from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import settings


@dataclass
class User:
    id: str
    is_platform_admin: bool
    email: str | None
    role: str | None
    partner_id: str | None


secret = settings.JWT_TOKEN_SECRET
if not secret:
    raise RuntimeError("JWT_TOKEN_SECRET environment variable is required")

# Matches the existing backend for an ASCII-only SECRET.
# Fail at startup if the secret requires special encoding handling.
signing_key = secret.encode("ascii")

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

    try:
        claims = jwt.decode(
            credentials.credentials,
            signing_key,
            algorithms=["HS256"],
            leeway=30,
            options={
                "require": ["exp"],
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iss": False,
                "verify_aud": False,
                "verify_iat": False,
            },
        )
    except jwt.ExpiredSignatureError:
        raise unauthorized(expired=True) from None
    except jwt.InvalidTokenError:
        raise unauthorized() from None

    user_id = claims.get("nameid")
    if not user_id:
        raise unauthorized()

    return User(
        user_id,
        email=claims.get("email"),
        role=claims.get("role"),
        is_platform_admin=claims.get("is_platform_admin") == "true",
        partner_id=claims.get("partner_id"),
    )
