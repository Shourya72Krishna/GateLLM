import pytest

from app.pricing import calculate_cost


def test_known_model_cost():
    # 1M input + 1M output on gpt-oss-20b
    assert calculate_cost("groq/openai/gpt-oss-20b", 1_000_000, 1_000_000) == pytest.approx(0.375)


def test_prefix_optional():
    a = calculate_cost("groq/openai/gpt-oss-120b", 1000, 1000)
    b = calculate_cost("openai/gpt-oss-120b", 1000, 1000)
    assert a == b


def test_unknown_model_returns_none():
    assert calculate_cost("groq/unknown-model", 10, 10) is None


def test_zero_tokens():
    assert calculate_cost("groq/openai/gpt-oss-20b", 0, 0) == 0.0