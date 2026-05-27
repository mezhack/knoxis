"""
Testes unitários do apurador. Usam mocks para evitar dependência do BD.
"""
import pytest
from unittest.mock import MagicMock, patch


def _make_cand(id, name):
    c = MagicMock()
    c.id = id
    c.name = name
    c.display_order = 0
    return c


def _make_vote_counts(counts: dict):
    result = []
    for cand_id, total in counts.items():
        v = MagicMock()
        v.__getitem__ = lambda self, key: {"candidate_id": cand_id, "position_id": 10, "total": total}[key]
        result.append({"candidate_id": cand_id, "position_id": 10, "total": total})
    return result


def test_limiar_floor():
    from apps.voting.apurador import _calcular_limiar
    assert _calcular_limiar(30) == 16
    assert _calcular_limiar(31) == 16
    assert _calcular_limiar(50) == 26
    assert _calcular_limiar(51) == 26
    assert _calcular_limiar(100) == 51
    assert _calcular_limiar(101) == 51


@pytest.mark.django_db
def test_apuracao_nao_final(org, election_pronta):
    from apps.voting.models import (
        BallotSession, Escrutinio, EscrutinioCandidate, EscrutinioPosition,
        Vote, VoterAttendance
    )
    from apps.voting.apurador import apurar
    from apps.elections.models import Position, Candidate
    from django.utils import timezone

    election_pronta.status = "em_andamento"
    election_pronta.save()

    esc = Escrutinio.objects.create(
        organization=org,
        election=election_pronta,
        number=1,
        is_final=False,
        status="aberto",
        opened_at=timezone.now(),
    )

    pos = Position.objects.filter(election=election_pronta).first()
    cands = list(Candidate.objects.filter(position=pos))

    ep = EscrutinioPosition.objects.create(
        organization=org, escrutinio=esc, position=pos, vacancies_remaining=2
    )
    for c in cands:
        EscrutinioCandidate.objects.create(organization=org, escrutinio=esc, position=pos, candidate=c)

    voters = list(election_pronta.voters.all())
    for v in voters[:4]:
        VoterAttendance.objects.create(organization=org, escrutinio=esc, voter=v, voted_at=timezone.now())

    # 4 votantes, limiar = 3
    # cands[0] recebe 3 votos, cands[1] recebe 2, cands[2] recebe 1
    vote_data = {cands[0]: 3, cands[1]: 2, cands[2]: 1}
    for cand, count in vote_data.items():
        for _ in range(count):
            Vote.objects.create(
                organization=org, escrutinio=esc, position=pos, candidate=cand,
                created_at=timezone.now().replace(second=0, microsecond=0),
            )

    resultado = apurar(esc)
    assert resultado.total_voters == 4
    assert len(resultado.positions) == 1
    pr = resultado.positions[0]

    eleitos = [c for c in pr.candidates if c.elected]
    assert len(eleitos) == 1
    assert eleitos[0].candidate_id == cands[0].id
    assert not pr.tie_pending


@pytest.mark.django_db
def test_apuracao_final(org, election_pronta):
    from apps.voting.models import (
        Escrutinio, EscrutinioCandidate, EscrutinioPosition, Vote, VoterAttendance
    )
    from apps.voting.apurador import apurar
    from apps.elections.models import Position, Candidate
    from django.utils import timezone

    election_pronta.status = "em_andamento"
    election_pronta.save()

    esc = Escrutinio.objects.create(
        organization=org,
        election=election_pronta,
        number=1,
        is_final=True,
        status="aberto",
        opened_at=timezone.now(),
    )

    pos = Position.objects.filter(election=election_pronta).first()
    cands = list(Candidate.objects.filter(position=pos))

    EscrutinioPosition.objects.create(
        organization=org, escrutinio=esc, position=pos, vacancies_remaining=2
    )
    for c in cands:
        EscrutinioCandidate.objects.create(organization=org, escrutinio=esc, position=pos, candidate=c)

    voters = list(election_pronta.voters.all())
    for v in voters[:3]:
        VoterAttendance.objects.create(organization=org, escrutinio=esc, voter=v, voted_at=timezone.now())

    vote_data = {cands[0]: 2, cands[1]: 1, cands[2]: 0}
    for cand, count in vote_data.items():
        for _ in range(count):
            Vote.objects.create(
                organization=org, escrutinio=esc, position=pos, candidate=cand,
                created_at=timezone.now().replace(second=0, microsecond=0),
            )

    resultado = apurar(esc)
    assert resultado.is_final
    pr = resultado.positions[0]
    eleitos = [c for c in pr.candidates if c.elected]
    assert len(eleitos) == 2
    ids_eleitos = {c.candidate_id for c in eleitos}
    assert cands[0].id in ids_eleitos
    assert cands[1].id in ids_eleitos
