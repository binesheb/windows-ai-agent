from fastapi.testclient import TestClient

from agent.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_system_inventory():
    response = client.get("/system")
    assert response.status_code == 200
    assert "computer" in response.json()
    assert "cpu" in response.json()


def test_unknown_capability_is_denied():
    response = client.get("/capabilities/arbitrary_command_execution")
    assert response.status_code == 200
    assert response.json()["allowed"] is False
