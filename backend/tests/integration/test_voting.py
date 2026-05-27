import pytest
from django.utils import timezone


@pytest.mark.django_db
def test_election_check_ready(election_pronta):
    issues = election_pronta.check_ready()
    assert len(issues) == 0


@pytest.mark.django_db
def test_election_start(auth_client, election_pronta, org):
    election_pronta.status = "rascunho"
    election_pronta.save()
    resp = auth_client.post(f"/api/v1/admin/elections/{election_pronta.id}/start")
    assert resp.status_code == 200
    election_pronta.refresh_from_db()
    assert election_pronta.status == "em_andamento"


@pytest.mark.django_db
def test_election_start_sem_candidatos(auth_client, election, org):
    from apps.elections.models import Position
    Position.objects.create(organization=org, election=election, name="Presbítero", vacancies=2)
    resp = auth_client.post(f"/api/v1/admin/elections/{election.id}/start")
    assert resp.status_code == 422


@pytest.mark.django_db
def test_voto_basico(client, election_pronta, org):
    from apps.core import cpf as cpf_utils
    from apps.elections.models import Voter
    from apps.voting.models import Escrutinio, EscrutinioCandidate, EscrutinioPosition, VoterAttendance, Vote

    election_pronta.status = "em_andamento"
    election_pronta.save()

    esc = Escrutinio.objects.create(
        organization=org,
        election=election_pronta,
        number=1,
        status="aberto",
        opened_at=timezone.now(),
        is_final=False,
    )

    from apps.elections.models import Position, Candidate
    pos = Position.objects.filter(election=election_pronta).first()
    cands = list(Candidate.objects.filter(position=pos))

    EscrutinioPosition.objects.create(organization=org, escrutinio=esc, position=pos, vacancies_remaining=2)
    for c in cands:
        EscrutinioCandidate.objects.create(organization=org, escrutinio=esc, position=pos, candidate=c)

    voter = election_pronta.voters.first()

    valid_cpf = "529.982.247-25"
    voter.cpf_hash = cpf_utils.hash_cpf(valid_cpf)
    voter.cpf_last2 = cpf_utils.last2(valid_cpf)
    voter.save()

    slug = org.slug
    resp = client.post(
        f"/api/v1/public/elections/{slug}/identify",
        {"cpf": valid_cpf},
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert "ballot_session" in resp.cookies

    ballot = resp.json()["ballot"]
    pos_data = ballot["positions"][0]

    resp2 = client.post(
        "/api/v1/public/ballot/submit",
        {
            "choices": [
                {"position_id": pos_data["id"], "candidate_ids": [c["id"] for c in pos_data["candidates"][:2]]}
            ]
        },
        content_type="application/json",
    )
    assert resp2.status_code == 200
    assert resp2.json()["ok"] is True

    assert Vote.objects.filter(escrutinio=esc).count() == 2
    assert VoterAttendance.objects.filter(escrutinio=esc, voter=voter).exists()


@pytest.mark.django_db
def test_voto_duplicado_rejeitado(client, election_pronta, org):
    from apps.core import cpf as cpf_utils
    from apps.voting.models import Escrutinio, EscrutinioCandidate, EscrutinioPosition, VoterAttendance

    election_pronta.status = "em_andamento"
    election_pronta.save()

    esc = Escrutinio.objects.create(
        organization=org,
        election=election_pronta,
        number=1,
        status="aberto",
        opened_at=timezone.now(),
        is_final=False,
    )

    from apps.elections.models import Position, Candidate
    pos = Position.objects.filter(election=election_pronta).first()
    cands = list(Candidate.objects.filter(position=pos))

    EscrutinioPosition.objects.create(organization=org, escrutinio=esc, position=pos, vacancies_remaining=2)
    for c in cands:
        EscrutinioCandidate.objects.create(organization=org, escrutinio=esc, position=pos, candidate=c)

    voter = election_pronta.voters.first()
    VoterAttendance.objects.create(organization=org, escrutinio=esc, voter=voter, voted_at=timezone.now())

    valid_cpf = "529.982.247-25"
    voter.cpf_hash = cpf_utils.hash_cpf(valid_cpf)
    voter.cpf_last2 = cpf_utils.last2(valid_cpf)
    voter.save()

    slug = org.slug
    resp = client.post(
        f"/api/v1/public/elections/{slug}/identify",
        {"cpf": valid_cpf},
        content_type="application/json",
    )
    assert resp.status_code == 409
    assert "já votou" in resp.json().get("detail", "").lower()
