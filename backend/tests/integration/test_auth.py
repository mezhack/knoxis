import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_signup(client):
    resp = client.post(
        "/api/v1/admin/auth/signup",
        {
            "name": "João",
            "email": "joao@test.com",
            "password": "senha-super-segura-123",
            "organization": {"name": "Igreja A", "slug": "igreja-a"},
        },
        content_type="application/json",
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["email"] == "joao@test.com"
    assert data["organization"]["slug"] == "igreja-a"


@pytest.mark.django_db
def test_login(client, user):
    resp = client.post(
        "/api/v1/admin/auth/login",
        {"email": "admin@test.com", "password": "senha-segura-123"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert "user" in resp.json()


@pytest.mark.django_db
def test_login_wrong_password(client, user):
    resp = client.post(
        "/api/v1/admin/auth/login",
        {"email": "admin@test.com", "password": "senha-errada"},
        content_type="application/json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_me_authenticated(auth_client):
    resp = auth_client.get("/api/v1/admin/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["email"] == "admin@test.com"


@pytest.mark.django_db
def test_me_unauthenticated(client):
    resp = client.get("/api/v1/admin/me")
    assert resp.status_code == 401


@pytest.mark.django_db
def test_cross_tenant(auth_client, auth_client2, org, org2, election):
    """User de org2 não consegue ver eleições de org."""
    resp = auth_client2.get(f"/api/v1/admin/elections/{election.id}")
    assert resp.status_code == 404
