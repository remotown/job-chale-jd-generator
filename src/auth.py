from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import settings


@dataclass
class User:
    id: str
    email: str | None
    role: str | None


supabase_url = settings.SUPABASE_URL.rstrip("/")
if not supabase_url:
    raise RuntimeError("SUPABASE_URL environment variable is required")

# Job Chale's access tokens are issued by Supabase Auth and signed with the project's
# asymmetric signing key. We verify them with the PUBLIC keys Supabase publishes, so this
# service holds no secret that could mint tokens. PyJWKClient caches the keys and refetches
# when a token names a key it hasn't seen (i.e. after a rotation in the dashboard).
issuer = f"{supabase_url}/auth/v1"
jwks_client = jwt.PyJWKClient(f"{issuer}/.well-known/jwks.json", cache_keys=True)

# Asymmetric only. Never accept HS256 here: with a public key in hand, allowing a symmetric
# algorithm would let anyone sign a token using that public key as the "secret".
ALGORITHMS = ["ES256", "RS256"]

bearer = HTTPBearer(auto_error=False)


def unauthorized(*, expired: bool = False) -> HTTPException:
    headers = {"WWW-Authenticate": "Bearer"}
    if expired:
        headers["X-Token-Expired"] = "true"

    return HTTPException(
        status_code=401,
        detail={
            "message": (
                "Your token has expired."
                if expired
                else "Invalid or missing access token."
            ),
            "isTokenExpired": expired,
        },
        headers=headers,
    )


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer),
    ],
) -> User:
    if credentials is None:
        raise unauthorized()

    token = credentials.credentials
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token).key
    except jwt.PyJWKClientConnectionError:
        # Supabase's key endpoint is unreachable: our outage, not a bad token.
        raise HTTPException(status_code=503, detail="Token verification is unavailable.") from None
    except (jwt.PyJWKClientError, jwt.InvalidTokenError):
        # Unknown key id, or a token too malformed to name a key.
        raise unauthorized() from None

    try:
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=ALGORITHMS,
            audience="authenticated",
            issuer=issuer,
            leeway=30,
            options={"require": ["exp", "sub", "aud", "iss"]},
        )
    except jwt.ExpiredSignatureError:
        raise unauthorized(expired=True) from None
    except jwt.InvalidTokenError:
        raise unauthorized() from None

    # `role` is Supabase's database role ("authenticated"), not the Job Chale role. The
    # employer check happens in the Job Chale app before it calls us; user_metadata is
    # user-editable and must never be trusted for that.
    return User(id=claims["sub"], email=claims.get("email"), role=claims.get("role"))
