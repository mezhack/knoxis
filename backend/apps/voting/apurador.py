"""
Apuração de escrutínio — função pura.
Lê do BD, calcula, retorna estrutura. Não persiste nada.
"""
from dataclasses import dataclass, field


@dataclass
class CandidateResult:
    candidate_id: int
    candidate_name: str
    votes: int
    elected: bool
    tie_at_cutoff: bool


@dataclass
class PositionResult:
    position_id: int
    position_name: str
    vacancies: int
    threshold: int | None  # None em escrutínio final
    candidates: list[CandidateResult] = field(default_factory=list)
    remaining_vacancies: int = 0
    tie_pending: bool = False


@dataclass
class ResultadoApuracao:
    escrutinio_id: int
    total_voters: int
    is_final: bool
    positions: list[PositionResult] = field(default_factory=list)
    election_can_close: bool = False


def _calcular_limiar(n: int) -> int:
    """RN-1: floor(N/2) + 1"""
    return (n // 2) + 1


def apurar(escrutinio) -> ResultadoApuracao:
    """
    Calcula o resultado de um escrutínio encerrado.
    Parâmetro: instância de Escrutinio (com relações pré-carregáveis).
    Retorna ResultadoApuracao sem persistir nada.
    """
    from django.db.models import Count

    from .models import EscrutinioPosition, Vote, VoterAttendance

    total_voters = VoterAttendance.objects.filter(escrutinio=escrutinio).count()
    is_final = escrutinio.is_final

    if not is_final:
        threshold = _calcular_limiar(total_voters)
    else:
        threshold = None

    position_snapshots = EscrutinioPosition.objects.filter(escrutinio=escrutinio).select_related("position")

    vote_counts = (
        Vote.objects.filter(escrutinio=escrutinio)
        .values("candidate_id", "position_id")
        .annotate(total=Count("id"))
    )
    votes_by_candidate = {v["candidate_id"]: v["total"] for v in vote_counts}

    from .models import EscrutinioCandidate

    positions_result: list[PositionResult] = []
    all_filled = True

    for ep in position_snapshots:
        pos = ep.position
        vagas = ep.vacancies_remaining

        ec_qs = EscrutinioCandidate.objects.filter(
            escrutinio=escrutinio, position=pos
        ).select_related("candidate")

        cand_votes = []
        for ec in ec_qs:
            cand_votes.append((ec.candidate, votes_by_candidate.get(ec.candidate_id, 0)))

        cand_votes.sort(key=lambda x: (-x[1], x[0].name))

        if not is_final:
            qualificados = [(c, v) for c, v in cand_votes if v >= threshold]
            qualificados.sort(key=lambda x: (-x[1], x[0].name))

            eleitos: list[tuple] = []
            tie_pending = False

            if len(qualificados) <= vagas:
                eleitos = qualificados
            else:
                eleitos_core = qualificados[:vagas]
                corte_votos = eleitos_core[-1][1]
                candidatos_no_corte = [x for x in qualificados if x[1] == corte_votos]
                candidatos_eleitos_no_corte = [x for x in eleitos_core if x[1] == corte_votos]

                if len(candidatos_no_corte) > len(candidatos_eleitos_no_corte):
                    tie_pending = True
                    eleitos = qualificados[:vagas - len(candidatos_eleitos_no_corte)]
                else:
                    eleitos = eleitos_core

            eleitos_ids = {c.id for c, _ in eleitos}
            vagas_restantes = vagas - len(eleitos)

            candidates_result = []
            for c, v in cand_votes:
                is_elected = c.id in eleitos_ids and not tie_pending
                is_tie = tie_pending and (c.id in {x[0].id for x in qualificados[vagas - 1:vagas + 1]})
                candidates_result.append(
                    CandidateResult(
                        candidate_id=c.id,
                        candidate_name=c.name,
                        votes=v,
                        elected=is_elected,
                        tie_at_cutoff=is_tie,
                    )
                )

            positions_result.append(
                PositionResult(
                    position_id=pos.id,
                    position_name=pos.name,
                    vacancies=vagas,
                    threshold=threshold,
                    candidates=candidates_result,
                    remaining_vacancies=vagas_restantes if not tie_pending else vagas,
                    tie_pending=tie_pending,
                )
            )

            if vagas_restantes > 0 or tie_pending:
                all_filled = False

        else:
            # Escrutínio final: mais votados, sem limiar
            ordered = sorted(cand_votes, key=lambda x: (-x[1], x[0].name))
            eleitos_final: list[tuple] = []
            tie_pending = False

            if len(ordered) <= vagas:
                eleitos_final = ordered
            else:
                corte_votos = ordered[vagas - 1][1]
                proximo_votos = ordered[vagas][1] if len(ordered) > vagas else -1
                if corte_votos == proximo_votos:
                    tie_pending = True
                    eleitos_final = [x for x in ordered if x[1] > corte_votos]
                else:
                    eleitos_final = ordered[:vagas]

            eleitos_ids = {c.id for c, _ in eleitos_final}
            vagas_restantes = vagas - len(eleitos_final)

            candidates_result = []
            for c, v in cand_votes:
                is_elected = c.id in eleitos_ids
                is_tie = tie_pending and v == (ordered[vagas - 1][1] if len(ordered) > vagas - 1 else -1)
                candidates_result.append(
                    CandidateResult(
                        candidate_id=c.id,
                        candidate_name=c.name,
                        votes=v,
                        elected=is_elected,
                        tie_at_cutoff=is_tie,
                    )
                )

            positions_result.append(
                PositionResult(
                    position_id=pos.id,
                    position_name=pos.name,
                    vacancies=vagas,
                    threshold=None,
                    candidates=candidates_result,
                    remaining_vacancies=vagas_restantes if not tie_pending else vagas,
                    tie_pending=tie_pending,
                )
            )

            if vagas_restantes > 0 or tie_pending:
                all_filled = False

    return ResultadoApuracao(
        escrutinio_id=escrutinio.id,
        total_voters=total_voters,
        is_final=is_final,
        positions=positions_result,
        election_can_close=all_filled,
    )
