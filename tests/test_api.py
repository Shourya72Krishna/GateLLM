import sqlite3
from types import SimpleNamespace

import litellm

from app.config import settings

BODY = {"model": "auto", "messages": [{"role": "user", "content": "hi"}]}


def fake_response():
    return SimpleNamespace(
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=20),
        model_dump=lambda: {
            "choices": [{"message": {"role": "assistant", "content": "hello"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        },
    )


def mock_ok(monkeypatch):
    async def fake(**kwargs):
        return fake_response()

    monkeypatch.setattr(litellm, "acompletion", fake)
    monkeypatch.setattr(litellm, "completion_cost", lambda **kw: 0.001)


def rows():
    with sqlite3.connect(settings.db_path) as c:
        return c.execute(
            "select model, prompt_tokens, completion_tokens, status from requests"
        ).fetchall()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_missing_key_401(client):
    assert client.post("/v1/chat/completions", json=BODY).status_code == 401


def test_wrong_key_401(client):
    r = client.post(
        "/v1/chat/completions", json=BODY, headers={"Authorization": "Bearer nope"}
    )
    assert r.status_code == 401


def test_success_and_logged(client, auth, monkeypatch):
    mock_ok(monkeypatch)
    r = client.post("/v1/chat/completions", json=BODY, headers=auth)
    assert r.status_code == 200
    assert r.json()["choices"][0]["message"]["content"] == "hello"
    assert rows() == [(settings.cheap_model, 10, 20, "ok")]


def test_auto_uses_cheap_model(client, auth, monkeypatch):
    seen = {}

    async def fake(**kwargs):
        seen.update(kwargs)
        return fake_response()

    monkeypatch.setattr(litellm, "acompletion", fake)
    monkeypatch.setattr(litellm, "completion_cost", lambda **kw: 0.0)
    client.post("/v1/chat/completions", json=BODY, headers=auth)
    assert seen["model"] == settings.cheap_model


def test_provider_error_502_and_logged(client, auth, monkeypatch):
    async def boom(**kwargs):
        raise RuntimeError("provider down")

    monkeypatch.setattr(litellm, "acompletion", boom)
    r = client.post("/v1/chat/completions", json=BODY, headers=auth)
    assert r.status_code == 502
    assert rows()[0][3] == "error"


def test_rate_limit_429(client, auth, monkeypatch):
    mock_ok(monkeypatch)
    codes = [
        client.post("/v1/chat/completions", json=BODY, headers=auth).status_code
        for _ in range(5)
    ]
    assert codes == [200, 200, 200, 429, 429]