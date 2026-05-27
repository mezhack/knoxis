import structlog
from django.db import transaction
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsOrganizationMember
from apps.elections.models import Candidate, Election, Position

from .apurador import apurar
from .models import (
    BallotSession,
    ElectionResult,
    Escrutinio,
    EscrutinioCandidate,
    EscrutinioPosition,
    Vote,
    VoterAttendance,
)

logger = structlog.get_logger()


def _build_result_response(resultado, election):
    positions_data = []
    for pr in resultado.positions:
        positions_data.append(
            {
                "position": {"id": pr.position_id, "name": pr.position_name},
                "vacancies": pr.vacancies,
                "threshold": pr.threshold,
                "candidates": [
                    {
                        "id": cr.candidate_id,
                        "name": cr.candidate_name,
                        "votes": cr.votes,
                        "elected": cr.elected,
                        "tie_at_cutoff": cr.tie_at_cutoff,
                    }
                    for cr in pr.candidates
                ],
                "remaining_vacancies": pr.remaining_vacancies,
                "tie_pending": pr.tie_pending,
            }
        )
    return {
        "escrutinio": {
            "id": resultado.escrutinio_id,
            "status": "encerrado",
            "total_voters": resultado.total_voters,
        },
        "results": positions_data,
        "election_status": election.status,
    }


class EscrutinioListView(APIView):
    permission_classes = [IsOrganizationMember]

    def get(self, request, election_pk):
        org = request.current_organization
        election = Election.objects.get(pk=election_pk, organization=org)
        escrutinios = Escrutinio.objects.filter(election=election).order_by("number")
        data = [
            {
                "id": e.id,
                "number": e.number,
                "status": e.status,
                "is_final": e.is_final,
                "opened_at": e.opened_at,
                "closed_at": e.closed_at,
                "total_voters": e.total_voters,
            }
            for e in escrutinios
        ]
        return Response(data)

    def post(self, request, election_pk):
        org = request.current_organization
        election = Election.objects.get(pk=election_pk, organization=org)

        if election.status not in ("em_andamento",):
            return Response({"detail": "Eleição não está em andamento."}, status=409)

        if Escrutinio.objects.filter(election=election, status="aberto").exists():
            return Response({"detail": "Há um escrutínio aberto. Encerre-o antes de criar outro."}, status=409)

        last_esc = Escrutinio.objects.filter(election=election).order_by("-number").first()
        if not last_esc or last_esc.status != "encerrado":
            return Response({"detail": "O último escrutínio deve estar encerrado."}, status=409)

        if ElectionResult.objects.filter(escrutinio=last_esc, tie_at_cutoff=True, tie_resolution__isnull=True).exists():
            return Response({"detail": "Há empate pendente de resolução no último escrutínio."}, status=409)

        next_number = last_esc.number + 1
        is_final = request.data.get("is_final", False)
        if election.final_rule == "max_count" and election.max_escrutinios and next_number >= election.max_escrutinios:
            is_final = True

        new_esc = Escrutinio.objects.create(
            organization=org,
            election=election,
            number=next_number,
            is_final=is_final,
        )
        return Response(
            {"id": new_esc.id, "number": new_esc.number, "is_final": new_esc.is_final, "status": new_esc.status},
            status=201,
        )


class EscrutinioDetailView(APIView):
    permission_classes = [IsOrganizationMember]

    def get(self, request, pk):
        org = request.current_organization
        esc = Escrutinio.objects.get(pk=pk, organization=org)
        positions = EscrutinioPosition.objects.filter(escrutinio=esc).select_related("position")
        candidates = EscrutinioCandidate.objects.filter(escrutinio=esc).select_related("candidate", "position")
        vote_count = Vote.objects.filter(escrutinio=esc).count()
        voter_count = VoterAttendance.objects.filter(escrutinio=esc).count()

        pos_data = []
        for ep in positions:
            cands = [ec.candidate for ec in candidates if ec.position_id == ep.position_id]
            pos_data.append(
                {
                    "position": {"id": ep.position_id, "name": ep.position.name},
                    "vacancies_remaining": ep.vacancies_remaining,
                    "candidates": [{"id": c.id, "name": c.name} for c in cands],
                }
            )

        return Response(
            {
                "id": esc.id,
                "election_id": esc.election_id,
                "number": esc.number,
                "status": esc.status,
                "is_final": esc.is_final,
                "opened_at": esc.opened_at,
                "closed_at": esc.closed_at,
                "total_voters": esc.total_voters,
                "voters_so_far": voter_count,
                "votes_so_far": vote_count,
                "positions": pos_data,
            }
        )

    def patch(self, request, pk):
        org = request.current_organization
        esc = Escrutinio.objects.get(pk=pk, organization=org)
        if esc.status != "preparando":
            return Response({"detail": "Só é possível editar escrutínio em preparando."}, status=409)
        if "is_final" in request.data:
            esc.is_final = request.data["is_final"]
            esc.save()
        return Response({"id": esc.id, "is_final": esc.is_final})


class EscrutinioOpenView(APIView):
    permission_classes = [IsOrganizationMember]

    def post(self, request, pk):
        org = request.current_organization
        esc = Escrutinio.objects.get(pk=pk, organization=org)

        if esc.status != "preparando":
            return Response({"detail": "Escrutínio não está em preparando."}, status=409)

        if Escrutinio.objects.filter(election=esc.election, status="aberto").exclude(pk=pk).exists():
            return Response({"detail": "Já existe um escrutínio aberto nesta eleição."}, status=409)

        with transaction.atomic():
            esc.status = "aberto"
            esc.opened_at = timezone.now()
            esc.save()

            # Snapshot de candidatos elegíveis e vagas remanescentes
            election = esc.election
            if esc.number == 1:
                for pos in election.positions.all():
                    EscrutinioPosition.objects.create(
                        organization=org,
                        escrutinio=esc,
                        position=pos,
                        vacancies_remaining=pos.vacancies,
                    )
                    for cand in pos.candidates.all():
                        EscrutinioCandidate.objects.create(
                            organization=org,
                            escrutinio=esc,
                            position=pos,
                            candidate=cand,
                        )
            else:
                prev_esc = Escrutinio.objects.get(election=election, number=esc.number - 1)
                prev_results = ElectionResult.objects.filter(escrutinio=prev_esc)
                elected_ids = set(prev_results.filter(was_elected=True).values_list("candidate_id", flat=True))

                for ep in EscrutinioPosition.objects.filter(escrutinio=prev_esc).select_related("position"):
                    vagas_eleitas = prev_results.filter(position=ep.position, was_elected=True).count()
                    vagas_restantes = ep.vacancies_remaining - vagas_eleitas
                    if vagas_restantes <= 0:
                        continue

                    EscrutinioPosition.objects.create(
                        organization=org,
                        escrutinio=esc,
                        position=ep.position,
                        vacancies_remaining=vagas_restantes,
                    )

                    for ec in EscrutinioCandidate.objects.filter(escrutinio=prev_esc, position=ep.position):
                        if ec.candidate_id not in elected_ids:
                            EscrutinioCandidate.objects.create(
                                organization=org,
                                escrutinio=esc,
                                position=ep.position,
                                candidate=ec.candidate,
                            )

            logger.info("escrutinio.opened", escrutinio_id=esc.id, election_id=esc.election_id, user_id=request.user.id)

        return Response({"id": esc.id, "status": esc.status, "opened_at": esc.opened_at})


class EscrutinioCloseView(APIView):
    permission_classes = [IsOrganizationMember]

    def post(self, request, pk):
        if not request.data.get("confirm"):
            return Response({"detail": "Confirmação necessária."}, status=400)

        org = request.current_organization
        esc = Escrutinio.objects.get(pk=pk, organization=org)

        if esc.status != "aberto":
            return Response({"detail": "Escrutínio não está aberto."}, status=409)

        resultado = apurar(esc)

        with transaction.atomic():
            esc.status = "encerrado"
            esc.closed_at = timezone.now()
            esc.total_voters = resultado.total_voters
            esc.save()

            ElectionResult.objects.filter(escrutinio=esc).delete()

            for pr in resultado.positions:
                for cr in pr.candidates:
                    ElectionResult.objects.create(
                        organization=org,
                        election=esc.election,
                        escrutinio=esc,
                        position_id=pr.position_id,
                        candidate_id=cr.candidate_id,
                        votes_count=cr.votes,
                        was_elected=cr.elected,
                        tie_at_cutoff=cr.tie_at_cutoff,
                    )

            if resultado.election_can_close:
                election = esc.election
                election.status = "encerrada"
                election.ended_at = timezone.now()
                election.save()

        logger.info("escrutinio.closed", escrutinio_id=esc.id, election_id=esc.election_id, user_id=request.user.id)
        return Response(_build_result_response(resultado, esc.election))


class EscrutinioParciaisView(APIView):
    permission_classes = [IsOrganizationMember]

    def get(self, request, pk):
        org = request.current_organization
        esc = Escrutinio.objects.get(pk=pk, organization=org)

        if esc.status != "aberto":
            return Response({"detail": "Escrutínio não está aberto."}, status=409)

        from django.db.models import Count

        voter_count = VoterAttendance.objects.filter(escrutinio=esc).count()
        vote_counts = (
            Vote.objects.filter(escrutinio=esc)
            .values("candidate_id", "position_id")
            .annotate(total=Count("id"))
        )
        counts_by_candidate = {v["candidate_id"]: v["total"] for v in vote_counts}

        etag_raw = f"{esc.updated_at.isoformat()}-{voter_count}"
        etag = str(hash(etag_raw))

        if request.headers.get("If-None-Match") == etag:
            return Response(status=304)

        positions = EscrutinioPosition.objects.filter(escrutinio=esc).select_related("position")
        candidates = EscrutinioCandidate.objects.filter(escrutinio=esc).select_related("candidate")

        positions_data = []
        for ep in positions:
            cands = [ec for ec in candidates if ec.position_id == ep.position_id]
            positions_data.append(
                {
                    "position": {
                        "id": ep.position_id,
                        "name": ep.position.name,
                        "vacancies_remaining": ep.vacancies_remaining,
                    },
                    "candidates": sorted(
                        [
                            {"id": ec.candidate_id, "name": ec.candidate.name, "votes": counts_by_candidate.get(ec.candidate_id, 0)}
                            for ec in cands
                        ],
                        key=lambda x: -x["votes"],
                    ),
                }
            )

        response = Response(
            {"etag": etag, "voters_so_far": voter_count, "positions": positions_data}
        )
        response["ETag"] = etag
        return response


class ResolveTieView(APIView):
    permission_classes = [IsOrganizationMember]

    def post(self, request, pk, position_pk):
        org = request.current_organization
        esc = Escrutinio.objects.get(pk=pk, organization=org)
        action = request.data.get("action")
        note = request.data.get("note", "")

        tie_results = ElectionResult.objects.filter(
            escrutinio=esc, position_id=position_pk, tie_at_cutoff=True, tie_resolution__isnull=True
        )
        if not tie_results.exists():
            return Response({"detail": "Nenhum empate pendente neste cargo."}, status=404)

        with transaction.atomic():
            if action == "elect_candidate":
                cand_id = request.data.get("candidate_id")
                if not cand_id:
                    return Response({"detail": "candidate_id obrigatório."}, status=400)
                for r in tie_results:
                    if r.candidate_id == cand_id:
                        r.was_elected = True
                        r.tie_resolution = note or "Eleito pelo organizador"
                    else:
                        r.was_elected = False
                        r.tie_resolution = note or "Não eleito na resolução de empate"
                    r.tie_at_cutoff = False
                    r.save()
            elif action == "defer_to_next":
                for r in tie_results:
                    r.was_elected = False
                    r.tie_at_cutoff = False
                    r.tie_resolution = note or "Adiado para próximo escrutínio"
                    r.save()
            elif action == "elect_both":
                for r in tie_results:
                    r.was_elected = True
                    r.tie_at_cutoff = False
                    r.tie_resolution = note or "Ambos eleitos por consenso"
                    r.save()
            else:
                return Response({"detail": "Ação inválida."}, status=400)

            if not ElectionResult.objects.filter(escrutinio=esc, tie_at_cutoff=True, tie_resolution__isnull=True).exists():
                all_elected = not EscrutinioPosition.objects.filter(
                    escrutinio=esc
                ).exclude(
                    position__in=ElectionResult.objects.filter(escrutinio=esc, was_elected=True).values("position")
                ).exists()

        return Response({"status": "resolvido"})
