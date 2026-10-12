import time
from contextlib import asynccontextmanager
from typing import Any

import litellm
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from app.auth import require_api_key
from app.config import settings
from app.db import init_db, log_request


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="GateLLM", lifespan=lifespan)


class ChatRequest(BaseModel):
    model: str | None = "auto"
    messages: list[dict[str, Any]]
    temperature: float | None = None
    max_tokens: int | None = None


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest, _key: str = Depends(require_api_key)):
    # "auto" -> cheap model for now (router comes in Week 2)
    model = settings.cheap_model if req.model in (None, "auto") else req.model

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": req.messages,
        "api_key": settings.groq_api_key,
    }
    if req.temperature is not None:
        kwargs["temperature"] = req.temperature
    if req.max_tokens is not None:
        kwargs["max_tokens"] = req.max_tokens

    start = time.perf_counter()
    try:
        resp = await litellm.acompletion(**kwargs)
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        log_request(model, 0, 0, latency_ms, 0.0, status="error", error=str(e)[:500])
        raise HTTPException(status_code=502, detail=f"Provider error: {e}")

    latency_ms = (time.perf_counter() - start) * 1000
    usage = resp.usage
    try:
        cost = litellm.completion_cost(completion_response=resp) or 0.0
    except Exception:
        cost = 0.0  # model missing from LiteLLM's price table

    log_request(
        model,
        usage.prompt_tokens,
        usage.completion_tokens,
        latency_ms,
        cost,
    )
    return resp.model_dump()