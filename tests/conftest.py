import pytest
from fastapi.testclient import TestClient

from app import ratelimit
from app.config import settings
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "db_path", str(tmp_path / "test.db"))
    monkeypatch.setattr(settings, "gateway_api_key", "test-key")
    monkeypatch.setattr(settings, "rate_limit_per_min", 3)
    ratelimit._hits.clear()
    with TestClient(app) as c:  # runs startup -> init_db
        yield c


@pytest.fixture
def auth():
    return {"Authorization": "Bearer test-key"}