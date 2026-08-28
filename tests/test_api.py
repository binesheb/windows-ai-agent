from fastapi.testclient import TestClient

from agent.core.auth import get_or_create_token
from agent.main import app

client = TestClient(app)
AUTH_HEADERS = {"X-Agent-Token": get_or_create_token()}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_system_inventory():
    response = client.get("/system", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert "computer" in response.json()
    assert "cpu" in response.json()


def test_unknown_capability_is_denied():
    response = client.get(
        "/capabilities/arbitrary_command_execution", headers=AUTH_HEADERS
    )
    assert response.status_code == 200
    assert response.json()["allowed"] is False
