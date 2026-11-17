"""Tests for Supabase JWT Bearer token authentication."""
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

import src.auth
from src.auth import get_current_user
from src.main import app

client = TestClient(app)

PAYLOAD = {"job_title": "Developer"}

# Stand-in for the Supabase project's signing key; the tests serve its public half
# in place of the real JWKS endpoint.
SIGNING_KEY = ec.generate_private_key(ec.SECP256R1())
OTHER_KEY = ec.generate_private_key(ec.SECP256R1())


class FakeJWKSClient:
    def __init__(self, public_key=None, error=None):
        self.public_key = public_key
        self.error = error

    def get_signing_key_from_jwt(self, token):
        if self.error:
            raise self.error
        jwt.get_unverified_header(token)  # malformed tokens fail here, as with the real client
        return type("SigningKey", (), {"key": self.public_key})()


def make_token(key=SIGNING_KEY, algorithm="ES256", expires_in=3600, **claims):
    payload = {
        "sub": "user-1",
        "email": "user@example.com",
        "role": "authenticated",
        "aud": "authenticated",
        "iss": src.auth.issuer,
        "exp": int(time.time()) + expires_in,
        **claims,
    }
    return jwt.encode(payload, key, algorithm=algorithm, headers={"kid": "test-kid"})


@pytest.fixture
def real_auth(monkeypatch):
    """Remove the conftest auth bypass and serve the test public key as the JWKS."""
    monkeypatch.setattr(src.auth, "jwks_client", FakeJWKSClient(SIGNING_KEY.public_key()))
    app.dependency_overrides.pop(get_current_user, None)
    yield
    app.dependency_overrides[get_current_user] = lambda: None


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def post(token):
    return client.post("/api/generate-jd", json=PAYLOAD, headers=auth_headers(token))


def test_missing_token_returns_401(real_auth):
    response = client.post("/api/generate-jd", json=PAYLOAD)
    assert response.status_code == 401
    assert response.json()["detail"]["isTokenExpired"] is False


def test_malformed_token_returns_401(real_auth):
    assert post("not-a-jwt").status_code == 401


def test_non_bearer_scheme_returns_401(real_auth):
    response = client.post(
        "/api/generate-jd", json=PAYLOAD, headers={"Authorization": "Basic abc123"}
    )
    assert response.status_code == 401


def test_token_signed_by_another_key_returns_401(real_auth):
    assert post(make_token(key=OTHER_KEY)).status_code == 401


def test_hs256_token_is_rejected(real_auth):
    # Algorithm-confusion guard: a symmetric token must never be accepted.
    assert post(make_token(key="any-shared-secret", algorithm="HS256")).status_code == 401


def test_wrong_audience_returns_401(real_auth):
    assert post(make_token(aud="anon")).status_code == 401


def test_wrong_issuer_returns_401(real_auth):
    assert post(make_token(iss="https://other-project.supabase.co/auth/v1")).status_code == 401


def test_missing_sub_returns_401(real_auth):
    token = make_token()
    claims = jwt.decode(token, options={"verify_signature": False})
    del claims["sub"]
    token = jwt.encode(claims, SIGNING_KEY, algorithm="ES256", headers={"kid": "test-kid"})
    assert post(token).status_code == 401


def test_expired_token_returns_401(real_auth):
    response = post(make_token(expires_in=-60))
    assert response.status_code == 401
    assert response.json()["detail"]["isTokenExpired"] is True
    assert response.headers.get("X-Token-Expired") == "true"


def test_unknown_key_id_returns_401(real_auth, monkeypatch):
    monkeypatch.setattr(
        src.auth, "jwks_client", FakeJWKSClient(error=jwt.PyJWKClientError("Unable to find a signing key"))
    )
    assert post(make_token()).status_code == 401


def test_jwks_unreachable_returns_503(real_auth, monkeypatch):
    monkeypatch.setattr(
        src.auth, "jwks_client", FakeJWKSClient(error=jwt.PyJWKClientConnectionError("down"))
    )
    assert post(make_token()).status_code == 503


def test_valid_token_returns_200(real_auth):
    response = post(make_token())
    assert response.status_code == 200
    assert response.json()["job_title"] == "Developer"


def test_user_comes_from_sub_claim(real_auth):
    user = get_current_user(
        type("Creds", (), {"credentials": make_token(sub="supabase-user-42")})()
    )
    assert user.id == "supabase-user-42"
    assert user.email == "user@example.com"


def test_public_endpoints_still_open(real_auth):
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200


def test_docs_disabled(real_auth):
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404
