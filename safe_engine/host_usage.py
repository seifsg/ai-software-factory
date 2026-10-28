"""Read token and dollar figures a host already recorded. Never calls a model.

Claude Code appends a `cost-state` line to the session jsonl. That line is the
source. A rates file can price tokens only when every counted field has a rate.
Missing records stay unavailable. Nothing here estimates tokens from text.
"""

import json

TOKEN_FIELDS = (
    ("inputTokens", "input"),
    ("outputTokens", "output"),
    ("thinkingTokens", "thinking"),
    ("cacheReadInputTokens", "cache_read"),
    ("cacheCreationInputTokens", "cache_write"),
)


def load(text):
    """One JSON object, or the last cost-state line in a jsonl transcript."""
    text = text.strip()
    if not text:
        raise ValueError("usage record is empty")
    if text.startswith("{") and "\n" not in text:
        row = json.loads(text)
        return row if row.get("type") == "cost-state" or row.get("modelUsage") else _reject()
    found = None
    for line in text.splitlines():
        line = line.strip()
        if not line or ('"cost-state"' not in line and '"modelUsage"' not in line):
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict) and (row.get("type") == "cost-state" or row.get("modelUsage")):
            found = row
    if found is None:
        raise ValueError("no host usage record in this file")
    return found


def _reject():
    raise ValueError("usage record has no modelUsage")


def summarize(record, rates=None):
    """Tokens from the host. Dollars only from the host figure or a complete rate card."""
    usage = record.get("modelUsage")
    if not isinstance(usage, dict) or not usage:
        raise ValueError("usage record has no modelUsage")
    models = []
    for name, row in usage.items():
        if not isinstance(row, dict):
            continue
        counts = {label: int(row.get(key) or 0) for key, label in TOKEN_FIELDS}
        item = {"model": str(name), "counts": counts, "tokens": sum(counts.values())}
        if isinstance(row.get("costUSD"), (int, float)) and record.get("hasUnknownModelCost") is False:
            item["cost_usd"] = float(row["costUSD"])
            item["cost_kind"] = "host"
        models.append(item)
    if not models:
        raise ValueError("usage record has no model rows")
    tokens = sum(item["tokens"] for item in models)
    host_total = record.get("totalCostUSD")
    if isinstance(host_total, (int, float)) and record.get("hasUnknownModelCost") is False:
        return {
            "provenance": "host-cost-state",
            "tokens": tokens,
            "models": models,
            "cost_usd": float(host_total),
            "cost_kind": "host",
        }
    estimated = _estimate(models, rates)
    result = {"provenance": "host-cost-state", "tokens": tokens, "models": models}
    if estimated is None:
        result["cost_usd"] = None
        result["cost_kind"] = "unavailable"
    else:
        result["cost_usd"] = estimated
        result["cost_kind"] = "estimated"
    return result


def _estimate(models, rates):
    """USD from a caller-supplied card. None unless every model and every token field is priced."""
    if not isinstance(rates, dict):
        return None
    per = rates.get("per_million") if "per_million" in rates else rates
    if not isinstance(per, dict):
        return None
    total = 0.0
    for item in models:
        card = per.get(item["model"])
        if not isinstance(card, dict):
            return None
        for label, count in item["counts"].items():
            if label not in card:
                return None
            total += count * float(card[label]) / 1_000_000
    return round(total, 6)


def detail(counts):
    return ", ".join(f"{label} {count}" for label, count in counts.items())
