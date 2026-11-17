import os

os.environ.setdefault("SUPABASE_URL", "https://test-project.supabase.co")

import pytest

from src.auth import User, get_current_user
from src.main import app


@pytest.fixture(autouse=True)
def _authenticated_user():
    """Bypass JWT auth for existing tests; auth tests remove this override."""
    app.dependency_overrides[get_current_user] = lambda: User(
        "test-user", "test@example.com", "authenticated"
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)
