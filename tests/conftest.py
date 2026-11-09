import os

os.environ.setdefault("JWT_TOKEN_SECRET", "test-jwt-secret-for-tests")

import pytest

from src.auth import User, get_current_user
from src.main import app

TEST_SECRET = os.environ["JWT_TOKEN_SECRET"]


@pytest.fixture(autouse=True)
def _authenticated_user():
    """Bypass JWT auth for existing tests; auth tests remove this override."""
    app.dependency_overrides[get_current_user] = lambda: User(
        "test-user", False, "test@example.com", "user", None
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)
