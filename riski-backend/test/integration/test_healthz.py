from app.backend import backend
from app.core.settings import get_settings
from fastapi.testclient import TestClient


def test_healthz_returns_ok_and_version() -> None:
    client = TestClient(backend)
    response = client.get("/api/healthz")

    assert response.status_code == 200

    payload = response.json()
    settings = get_settings()

    assert payload == {"status": "ok", "version": settings.version}
