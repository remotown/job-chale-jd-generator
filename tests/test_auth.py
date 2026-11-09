"""Tests for JWT Bearer token authentication (AC-AUTH-001 through AC-AUTH-006)."""
import time

import jwt
import pytest
from fastapi.testclient import TestClient

from src.auth import get_current_user
from src.main import app
from tests.conftest import TEST_SECRET

client = TestClient(app)

PAYLOAD = {"job_title": "Developer"}


def make_token(secret=TEST_SECRET, expires_in=3600, **claims):
    payload = {
        "nameid": "user-1",
        "email": "user@example.com",
        "role": "user",
        "exp": int(time.time()) + expires_in,
        **claims,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture
def real_auth():
    """Remove the conftest auth bypass so the real dependency runs."""
    app.dependency_overrides.pop(get_current_user, None)
    yield
    app.dependency_overrides[get_current_user] = lambda: None


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_missing_token_returns_401(real_auth):
    response = client.post("/api/generate-jd", json=PAYLOAD)
    assert response.status_code == 401
    assert response.json()["detail"]["isTokenExpired"] is False


def test_malformed_token_returns_401(real_auth):
    response = client.post(
        "/api/generate-jd", json=PAYLOAD, headers={"Authorization": "Bearer not-a-jwt"}
    )
    assert response.status_code == 401


def test_non_bearer_scheme_returns_401(real_auth):
    response = client.post(
        "/api/generate-jd", json=PAYLOAD, headers={"Authorization": "Basic abc123"}
    )
    assert response.status_code == 401


def test_wrong_secret_returns_401(real_auth):
    token = make_token(secret="some-other-secret")
    response = client.post("/api/generate-jd", json=PAYLOAD, headers=auth_headers(token))
    assert response.status_code == 401


def test_expired_token_returns_401(real_auth):
    token = make_token(expires_in=-60)
    response = client.post("/api/generate-jd", json=PAYLOAD, headers=auth_headers(token))
    assert response.status_code == 401
    assert response.json()["detail"]["isTokenExpired"] is True
    assert response.headers.get("X-Token-Expired") == "true"


def test_valid_token_returns_200(real_auth):
    token = make_token()
    response = client.post("/api/generate-jd", json=PAYLOAD, headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["job_title"] == "Developer"


def test_public_endpoints_still_open(real_auth):
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200


def test_docs_disabled(real_auth):
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404
