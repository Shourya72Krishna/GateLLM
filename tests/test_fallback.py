import litellm

from app.config import settings
from tests.test_api import BODY, fake_response, rows


def test_fallback_to_strong_when_cheap_fails(client, auth, monkeypatch):
    calls = []

    async def fake(**kwargs):
        calls.append(kwargs["model"])
        if kwargs["model"] == settings.cheap_model:
            raise RuntimeError("cheap down")
        return fake_response()

    monkeypatch.setattr(litellm, "acompletion", fake)
    monkeypatch.setattr(litellm, "completion_cost", lambda **kw: 0.0)

    r = client.post("/v1/chat/completions", json=BODY, headers=auth)
    assert r.status_code == 200
    assert calls == [settings.cheap_model, settings.strong_model]

    data = rows()
    assert data[0][0] == settings.cheap_model and data[0][3] == "error"
    assert data[1][0] == settings.strong_model and data[1][3] == "ok"


def test_all_models_fail_502_and_both_logged(client, auth, monkeypatch):
    async def boom(**kwargs):
        raise RuntimeError("down")

    monkeypatch.setattr(litellm, "acompletion", boom)

    r = client.post("/v1/chat/completions", json=BODY, headers=auth)
    assert r.status_code == 502
    assert [row[3] for row in rows()] == ["error", "error"]


def test_no_fallback_needed(client, auth, monkeypatch):
    calls = []

    async def fake(**kwargs):
        calls.append(kwargs["model"])
        return fake_response()

    monkeypatch.setattr(litellm, "acompletion", fake)
    monkeypatch.setattr(litellm, "completion_cost", lambda **kw: 0.0)

    client.post("/v1/chat/completions", json=BODY, headers=auth)
    assert calls == [settings.cheap_model]