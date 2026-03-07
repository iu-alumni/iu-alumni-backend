"""Pytest configuration and shared fixtures for the test suite.

Environment variables must be set *before* any app module is imported because
``app/core/database.py`` calls ``create_engine`` and ``load_dotenv`` at import
time.  Patching ``dotenv.load_dotenv`` here ensures a local ``.env`` file cannot
override the in-memory SQLite URL used during testing.
"""

import os

# ---------------------------------------------------------------------------
# 1. Set required environment variables before any app imports
# ---------------------------------------------------------------------------
_TEST_ENV = {
    "SQLALCHEMY_DATABASE_URL": "sqlite:///:memory:",
    "SECRET_KEY": "test-secret-key-for-testing-purposes-only-32c",
    "EMAIL_HASH_SECRET": "test-email-hash-secret-for-tests-only!!!",
    "ADMIN_EMAIL": "admin@innopolis.university",
    "ADMIN_PASSWORD": "adminpassword123",
    "ENVIRONMENT": "TEST",
}
for _key, _val in _TEST_ENV.items():
    os.environ[_key] = _val

# ---------------------------------------------------------------------------
# 2. Prevent load_dotenv from overriding the test variables above.
#    database.py does ``from dotenv import load_dotenv`` at import time, so
#    replacing the function on the module object before that import is enough.
# ---------------------------------------------------------------------------
import dotenv  # noqa: E402

dotenv.load_dotenv = lambda *args, **kwargs: None  # type: ignore[assignment]
