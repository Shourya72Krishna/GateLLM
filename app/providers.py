import time
from typing import Any

import litellm

from app.config import settings
from app.db import log_request


class AllProvidersFailed(Exception):
    pass


def build_chain(model: str) -> list[str]:
    """Requested model first, then the other configured models as fallbacks."""
    chain = [model]
    for m in (settings.strong_model, settings.cheap_model):
        if m not in chain:
            chain.append(m)
    return chain


async def call_with_fallback(kwargs: dict[str, Any], chain: list[str]):
    """Try each model in order. Returns (response, model_used, latency_ms)."""
    errors: list[str] = []
    for model in chain:
        start = time.perf_counter()
        try:
            resp = await litellm.acompletion(
                model=model, timeout=settings.request_timeout, **kwargs
            )
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            log_request(model, 0, 0, latency_ms, 0.0, status="error", error=str(e)[:500])
            errors.append(f"{model}: {e}")
            continue
        latency_ms = (time.perf_counter() - start) * 1000
        return resp, model, latency_ms
    raise AllProvidersFailed("; ".join(errors))