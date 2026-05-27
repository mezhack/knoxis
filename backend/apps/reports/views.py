from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsOrganizationMember
from apps.elections.models import Election
from apps.voting.models import ElectionResult, Escrutinio, VoterAttendance


class RelatorioListView(APIView):
    permission_classes = [IsOrganizationMember]

    def get(self, request, election_pk):
        org = request.current_organization
        election = Election.objects.get(pk=election_pk, organization=org)
        escrutinios = Escrutinio.objects.filter(election=election, status="encerrado").order_by("number")

        data = []
        prev_voters = None
        for esc in escrutinios:
            voters = esc.total_voters or 0
            abstencao = max(0, prev_voters - voters) if prev_voters is not None else None
            eleitos = ElectionResult.objects.filter(escrutinio=esc, was_elected=True).count()
            data.append(
                {
                    "id": esc.id,
                    "number": esc.number,
                    "is_final": esc.is_final,
                    "opened_at": esc.opened_at,
                    "closed_at": esc.closed_at,
                    "total_voters": voters,
                    "abstencao": abstencao,
                    "eleitos_count": eleitos,
                }
            )
            prev_voters = voters

        return Response(data)


class RelatorioDetailView(APIView):
    permission_classes = [IsOrganizationMember]

    def get(self, request, pk):
        org = request.current_organization
        esc = Escrutinio.objects.select_related("election", "election__organization").get(
            pk=pk, organization=org
        )
        election = esc.election

        prev_esc = Escrutinio.objects.filter(
            election=election, number=esc.number - 1, status="encerrado"
        ).first()
        prev_voters = prev_esc.total_voters if prev_esc else None
        voters = esc.total_voters or 0
        abstencao = max(0, prev_voters - voters) if prev_voters is not None else None

        results = (
            ElectionResult.objects.filter(escrutinio=esc)
            .select_related("position", "candidate")
            .order_by("position__display_order", "position__name", "-votes_count", "candidate__name")
        )

        positions_map: dict = {}
        from apps.voting.models import EscrutinioPosition
        pos_snapshots = {ep.position_id: ep.vacancies_remaining for ep in EscrutinioPosition.objects.filter(escrutinio=esc)}

        for r in results:
            pid = r.position_id
            if pid not in positions_map:
                threshold = (voters // 2 + 1) if not esc.is_final else None
                positions_map[pid] = {
                    "position": {"id": pid, "name": r.position.name},
                    "vacancies_in_round": pos_snapshots.get(pid, 0),
                    "threshold": threshold,
                    "candidates": [],
                }
            positions_map[pid]["candidates"].append(
                {"id": r.candidate_id, "name": r.candidate.name, "votes": r.votes_count, "elected": r.was_elected}
            )

        return Response(
            {
                "election": {
                    "id": election.id,
                    "name": election.name,
                    "organization": {
                        "name": election.organization.name,
                        "city": election.organization.city,
                        "state": election.organization.state,
                    },
                },
                "escrutinio": {
                    "id": esc.id,
                    "number": esc.number,
                    "is_final": esc.is_final,
                    "opened_at": esc.opened_at,
                    "closed_at": esc.closed_at,
                },
                "totals": {
                    "voters": voters,
                    "previous_voters": prev_voters,
                    "abstention": abstencao,
                },
                "positions": list(positions_map.values()),
            }
        )
