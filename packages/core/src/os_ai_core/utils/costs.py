from typing import Tuple

from os_ai_core.config import (
    COST_INPUT_PER_MTOKENS_USD,
    COST_OUTPUT_PER_MTOKENS_USD,
    LONG_CONTEXT_INPUT_TOKENS_THRESHOLD,
    COST_INPUT_PER_MTOKENS_USD_LONG_CONTEXT,
    COST_OUTPUT_PER_MTOKENS_USD_LONG_CONTEXT,
)


def _is_sonnet4_model(model: str) -> bool:
    try:
        m = (model or "").lower().strip()
        # Примеры: "claude-sonnet-4-20250514", "claude-4-sonnet-latest" и т.п.
        return "sonnet" in m and "4" in m
    except Exception:
        return False


def get_rates_for_model(model: str, input_tokens: int) -> Tuple[float, float, str]:
    """Возвращает (input_rate, output_rate, tier_label).

    Для Sonnet 4 при длинном контексте (>= LONG_CONTEXT_INPUT_TOKENS_THRESHOLD входных токенов)
    применяет повышенные ставки.
    """
    if _is_sonnet4_model(model) and int(input_tokens) >= int(LONG_CONTEXT_INPUT_TOKENS_THRESHOLD):
        return (
            float(COST_INPUT_PER_MTOKENS_USD_LONG_CONTEXT),
            float(COST_OUTPUT_PER_MTOKENS_USD_LONG_CONTEXT),
            "sonnet4-long-context",
        )
    return (
        float(COST_INPUT_PER_MTOKENS_USD),
        float(COST_OUTPUT_PER_MTOKENS_USD),
        "base",
    )


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> Tuple[float, float, float, str]:
    """Оценивает стоимость вызова в долларах.

    Возвращает (input_cost, output_cost, total_cost, pricing_tier).
    """
    in_rate, out_rate, tier = get_rates_for_model(model, input_tokens)
    input_cost = (float(input_tokens) / 1_000_000.0) * in_rate
    output_cost = (float(output_tokens) / 1_000_000.0) * out_rate
    return input_cost, output_cost, (input_cost + output_cost), tier


