import pytest

from apps.accounts.models import Organization, OrganizationMember, User
from apps.core import cpf as cpf_utils
from apps.elections.models import Candidate, Election, Position, Voter


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Igreja Teste", slug="igreja-teste", city="SP", state="SP")


@pytest.fixture
def org2(db):
    return Organization.objects.create(name="Igreja B", slug="igreja-b")


@pytest.fixture
def user(db):
    u = User.objects.create_user(email="admin@test.com", name="Admin", password="senha-segura-123")
    return u


@pytest.fixture
def user2(db):
    u = User.objects.create_user(email="admin2@test.com", name="Admin2", password="senha-segura-123")
    return u


@pytest.fixture
def member(db, user, org):
    return OrganizationMember.objects.create(organization=org, user=user, role="owner")


@pytest.fixture
def member2(db, user2, org2):
    return OrganizationMember.objects.create(organization=org2, user=user2, role="owner")


@pytest.fixture
def election(db, org, user):
    e = Election.objects.create(
        organization=org,
        name="Eleição Teste",
        status="rascunho",
        final_rule="max_count",
        max_escrutinios=3,
        created_by=user,
    )
    return e


@pytest.fixture
def election_pronta(db, org, user):
    e = Election.objects.create(
        organization=org,
        name="Eleição Pronta",
        status="rascunho",
        final_rule="max_count",
        max_escrutinios=3,
        created_by=user,
    )
    pos = Position.objects.create(organization=org, election=e, name="Presbítero", vacancies=2)
    Candidate.objects.create(organization=org, election=e, position=pos, name="Candidato A")
    Candidate.objects.create(organization=org, election=e, position=pos, name="Candidato B")
    Candidate.objects.create(organization=org, election=e, position=pos, name="Candidato C")

    for i in range(5):
        cpf = _gen_cpf(i)
        Voter.objects.create(
            organization=org, election=e,
            name=f"Eleitor {i}",
            cpf_hash=cpf_utils.hash_cpf(cpf),
            cpf_last2=cpf_utils.last2(cpf),
        )
    return e


def _gen_cpf(seed: int) -> str:
    base = str(seed).zfill(9)
    nums = [int(c) for c in base]
    d1 = sum((10 - i) * v for i, v in enumerate(nums)) % 11
    d1 = 0 if d1 < 2 else 11 - d1
    nums.append(d1)
    d2 = sum((11 - i) * v for i, v in enumerate(nums)) % 11
    d2 = 0 if d2 < 2 else 11 - d2
    nums.append(d2)
    return "".join(str(n) for n in nums)


@pytest.fixture
def auth_client(client, user, member):
    client.force_login(user)
    session = client.session
    session["current_organization_id"] = member.organization_id
    session.save()
    return client


@pytest.fixture
def auth_client2(client, user2, member2):
    client.force_login(user2)
    session = client.session
    session["current_organization_id"] = member2.organization_id
    session.save()
    return client
