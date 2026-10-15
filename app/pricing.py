# USD per 1M tokens: (input, output). Verify at groq.com/pricing.
PRICES: dict[str, tuple[float, float]] = {
    "openai/gpt-oss-20b": (0.075, 0.30),
    "openai/gpt-oss-120b": (0.15, 0.60),
}


def _normalize(model: str) -> str:
    model = model.lower()
    return model[len("groq/"):] if model.startswith("groq/") else model


def get_price(model: str) -> tuple[float, float] | None:
    return PRICES.get(_normalize(model))


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float | None:
    """Return cost in USD, or None if the model has no price entry."""
    price = get_price(model)
    if price is None:
        return None
    in_price, out_price = price
    return (prompt_tokens * in_price + completion_tokens * out_price) / 1_000_000