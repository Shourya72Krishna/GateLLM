from contextlib import asynccontextmanager
from typing import Any

import litellm
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from app.auth import require_api_key
from app.config import settings
from app.db import init_db, log_request
from app.pricing import calculate_cost
from app.providers import AllProvidersFailed, build_chain, call_with_fallback


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


def compute_cost(model: str, resp: Any) -> float:
    usage = resp.usage
    cost = calculate_cost(model, usage.prompt_tokens, usage.completion_tokens)
    if cost is not None:
        return cost
    try:  # model not in our table: fall back to LiteLLM's price data
        return litellm.completion_cost(completion_response=resp) or 0.0
    except Exception:
        return 0.0


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest, _key: str = Depends(require_api_key)):
    # "auto" -> cheap model for now (router comes in Week 2)
    model = settings.cheap_model if req.model in (None, "auto") else req.model

    kwargs: dict[str, Any] = {
        "messages": req.messages,
        "api_key": settings.groq_api_key,
    }
    if req.temperature is not None:
        kwargs["temperature"] = req.temperature
    if req.max_tokens is not None:
        kwargs["max_tokens"] = req.max_tokens

    try:
        resp, used_model, latency_ms = await call_with_fallback(
            kwargs, build_chain(model)
        )
    except AllProvidersFailed as e:
        raise HTTPException(status_code=502, detail=f"All providers failed: {e}")

    usage = resp.usage
    log_request(
        used_model,
        usage.prompt_tokens,
        usage.completion_tokens,
        latency_ms,
        compute_cost(used_model, resp),
    )
    return resp.model_dump()