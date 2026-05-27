import structlog
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core import cpf as cpf_utils
from apps.elections.models import Election, Voter

from .models import BallotSession, EscrutinioCandidate, EscrutinioPosition, Vote, VoterAttendance

logger = structlog.get_logger()


class ElectionPublicView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, slug):
        election = (
            Election.objects.select_related("organization")
            .filter(organization__slug=slug, status="em_andamento")
            .first()
        )
        if election is None:
            return Response(
                {"message": "Não há votação em andamento para esta organização."},
                status=200,
            )

        open_esc = election.escrutinios.filter(status="aberto").first()
        data = {
            "election": {
                "name": election.name,
                "organization_name": election.organization.name,
                "status": election.status,
            },
            "current_escrutinio": None,
        }

        if open_esc:
            data["current_escrutinio"] = {"number": open_esc.number, "status": open_esc.status}
        else:
            data["message"] = "Não há escrutínio aberto no momento."

        return Response(data)



class IdentifyView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, slug):
        # Rate limiting — 10/5min/IP
        from django_ratelimit.core import is_ratelimited
        is_limited = is_ratelimited(
            request,
            group="identify",
            key="ip",
            rate="10/5m",
            increment=True,
        )
        if is_limited:
            return Response(
                {"type": "rate_limit", "status": 429, "detail": "Muitas tentativas. Aguarde 5 minutos."},
                status=429,
            )

        raw_cpf = request.data.get("cpf", "")

        if not cpf_utils.is_valid(raw_cpf):
            return Response({"type": "validation_error", "status": 400, "detail": "CPF inválido."}, status=400)

        election = (
            Election.objects.select_related("organization")
            .filter(organization__slug=slug, status="em_andamento")
            .first()
        )
        if election is None:
            return Response({"detail": "Eleição não está em andamento."}, status=409)

        open_esc = election.escrutinios.filter(status="aberto").first()
        if not open_esc:
            return Response({"detail": "Nenhum escrutínio aberto."}, status=409)

        h = cpf_utils.hash_cpf(raw_cpf)
        try:
            voter = Voter.objects.get(election=election, cpf_hash=h)
        except Voter.DoesNotExist:
            return Response({"type": "not_found", "status": 404, "detail": "CPF não localizado na lista de membros desta eleição."}, status=404)

        if VoterAttendance.objects.filter(escrutinio=open_esc, voter=voter).exists():
            return Response({"type": "conflict", "status": 409, "detail": "Você já votou neste escrutínio."}, status=409)

        BallotSession.objects.filter(
            escrutinio=open_esc, voter=voter, used_at__isnull=True
        ).delete()

        session = BallotSession.create_for_voter(open_esc, voter)

        positions = EscrutinioPosition.objects.filter(escrutinio=open_esc).select_related("position")
        candidates = EscrutinioCandidate.objects.filter(escrutinio=open_esc).select_related("candidate")

        ballot_positions = []
        for ep in positions:
            cands = [ec.candidate for ec in candidates if ec.position_id == ep.position_id]
            ballot_positions.append(
                {
                    "id": ep.position_id,
                    "name": ep.position.name,
                    "vacancies": ep.vacancies_remaining,
                    "candidates": [{"id": c.id, "name": c.name} for c in sorted(cands, key=lambda c: (c.display_order, c.name))],
                }
            )

        response = Response(
            {"ballot": {"escrutinio_number": open_esc.number, "positions": ballot_positions}}
        )
        response.set_cookie(
            "ballot_session",
            session.token,
            max_age=600,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
            path="/api/v1/public/ballot",
        )
        return response


class SubmitBallotView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        token = request.COOKIES.get("ballot_session")
        if not token:
            return Response({"detail": "Sessão de cédula não encontrada."}, status=401)

        try:
            with transaction.atomic():
                try:
                    session = BallotSession.objects.select_for_update().get(token=token)
                except BallotSession.DoesNotExist:
                    return Response({"detail": "Sessão inválida."}, status=409)

                if not session.is_valid():
                    return Response({"detail": "Sessão expirada ou já utilizada."}, status=409)

                esc = session.escrutinio
                if esc.status != "aberto":
                    return Response({"detail": "Escrutínio encerrado. Tente novamente."}, status=409)

                choices = request.data.get("choices", [])
                positions_snapshot = {
                    ep.position_id: ep.vacancies_remaining
                    for ep in EscrutinioPosition.objects.filter(escrutinio=esc)
                }
                valid_candidates = {
                    ec.candidate_id: ec.position_id
                    for ec in EscrutinioCandidate.objects.filter(escrutinio=esc)
                }

                vote_rows = []
                for choice in choices:
                    pos_id = choice.get("position_id")
                    cand_ids = choice.get("candidate_ids", [])

                    if pos_id not in positions_snapshot:
                        return Response({"detail": f"Cargo {pos_id} inválido."}, status=400)

                    required = positions_snapshot[pos_id]
                    if len(cand_ids) != required:
                        return Response(
                            {"detail": f"Cargo {pos_id}: selecione exatamente {required} candidato(s). Recebido: {len(cand_ids)}."},
                            status=400,
                        )

                    for cid in cand_ids:
                        if valid_candidates.get(cid) != pos_id:
                            return Response({"detail": f"Candidato {cid} não elegível para cargo {pos_id}."}, status=400)
                        vote_rows.append(
                            Vote(
                                organization=esc.organization,
                                escrutinio=esc,
                                position_id=pos_id,
                                candidate_id=cid,
                                created_at=timezone.now().replace(second=0, microsecond=0),
                            )
                        )

                session.used_at = timezone.now()
                session.save()

                VoterAttendance.objects.create(
                    organization=esc.organization,
                    escrutinio=esc,
                    voter=session.voter,
                    voted_at=timezone.now(),
                )

                Vote.objects.bulk_create(vote_rows)

        except IntegrityError:
            return Response({"detail": "Voto duplo detectado."}, status=409)

        response = Response({"ok": True, "message": "Voto registrado com sucesso."})
        response.delete_cookie("ballot_session")
        return response
