from fastapi.testclient import TestClient

from hello_api.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_hello() -> None:
    response = client.get("/api/hello")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello from FastAPI behind Caddy"}
