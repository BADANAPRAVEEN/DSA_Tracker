import os
import uuid

import pytest
from fastapi.testclient import TestClient

# Safety: tests must run against a TEST database, never production
test_url = os.environ.get("TEST_DATABASE_URL")
if not test_url:
    raise RuntimeError("Set TEST_DATABASE_URL to your Neon test branch connection string.")
if test_url == os.environ.get("DATABASE_URL"):
    raise RuntimeError("TEST_DATABASE_URL must not be your production DATABASE_URL.")

os.environ["DATABASE_URL"] = test_url
os.environ["SECRET_KEY"] = "test-secret-key-only-for-pytest-0123456789-abcdefghij"


@pytest.fixture(scope="session")
def client():
    from main import app
    return TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_users():
    yield
    from database import get_db
    with get_db() as conn:
        conn.execute("DELETE FROM users WHERE email LIKE %s", ("test\\_%@example.com",))


@pytest.fixture
def unique_email():
    return lambda: f"test_{uuid.uuid4().hex[:10]}@example.com"


@pytest.fixture
def make_user(client, unique_email):
    def _make():
        email = unique_email()
        password = "TestPass123"
        res = client.post("/auth/signup", json={"email": email, "password": password})
        assert res.status_code == 201
        res = client.post("/auth/login", json={"email": email, "password": password})
        token = res.json()["access_token"]
        return {
            "email": email,
            "password": password,
            "headers": {"Authorization": f"Bearer {token}"},
        }
    return _make


@pytest.fixture
def user(make_user):
    return make_user()