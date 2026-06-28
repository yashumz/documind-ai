# observability/cost_calculator.py
# ─────────────────────────────────────────────────────────────
# Converts raw token counts into USD and INR cost
# for every LLM call made by DocuMind AI.
#
# Why track costs?
#   → Resume: "reduced LLM costs by X% by optimizing prompts"
#   → Dashboard: show cost per query to users
#   → Alerts: notify if a single query costs too much
# ─────────────────────────────────────────────────────────────

# Anthropic pricing — USD per 1 million tokens (June 2026)
# Source: https://anthropic.com/pricing
MODEL_PRICING = {
    "claude-sonnet-4-6": {"input": 3.00,  "output": 15.00},
    "claude-opus-4-6":   {"input": 15.00, "output": 75.00},
    "claude-haiku-4-5":  {"input": 0.80,  "output": 4.00},
    "default":           {"input": 3.00,  "output": 15.00},
}

# Conversion rate — update periodically
USD_TO_INR = 83.5


def calculate_cost(
    model:         str,
    input_tokens:  int,
    output_tokens: int,
) -> dict:
    """
    WHAT:  Calculates cost for one LLM API call
    WHY:   Track spend per query for the dashboard

    Real life: Like a taxi meter that calculates
               the fare based on distance travelled
               (tokens used)

    Args:
        model:         Model name string
                       e.g. "claude-sonnet-4-6"
        input_tokens:  Number of tokens in the prompt
        output_tokens: Number of tokens in the response

    Returns:
        {
            "model":         "claude-sonnet-4-6",
            "input_tokens":  512,
            "output_tokens": 128,
            "cost_usd":      0.003456,
            "cost_inr":      0.2886
        }

    Example:
        cost = calculate_cost("claude-sonnet-4-6", 512, 128)
        print(f"This query cost ₹{cost['cost_inr']}")
    """
    # Match model by prefix — handles version suffixes
    # e.g. "claude-sonnet-4-6-20250514" matches "claude-sonnet-4-6"
    pricing = MODEL_PRICING["default"]
    for key in MODEL_PRICING:
        if key in model:
            pricing = MODEL_PRICING[key]
            break

    # Cost = (tokens / 1,000,000) × price per million tokens
    input_cost  = (input_tokens  / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    total_usd   = input_cost + output_cost

    return {
        "model":         model,
        "input_tokens":  input_tokens,
        "output_tokens": output_tokens,
        "cost_usd":      round(total_usd, 6),
        "cost_inr":      round(total_usd * USD_TO_INR, 4),
    }