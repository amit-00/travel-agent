from fastapi.testclient import TestClient
from listings.main import app  # noqa: E402

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
