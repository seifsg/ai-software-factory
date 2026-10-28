"""Read token and dollar figures a host already recorded. Never calls a model.

Claude Code appends a `cost-state` line to the session jsonl. That line is the
source. A rates file can price tokens only when every counted field has a rate.
Missing records stay unavailable. Nothing here estimates tokens from text.
"""

import json
import hashlib
import math

TOKEN_FIELDS = (
    ("inputTokens", "input"),
    ("outputTokens", "output"),
    ("thinkingTokens", "thinking"),
    ("cacheReadInputTokens", "cache_read"),
    ("cacheCreationInputTokens", "cache_write"),
)


def load(text):
    """Read one host's latest cumulative session record without retaining messages."""
    text = text.strip()
    if not text:
        raise ValueError("usage record is empty")
    try:
        single = json.loads(text)
    except ValueError:
        single = None
    if isinstance(single, dict) and (single.get("modelUsage") or single.get("type") == "cost-state"):
        return single
    found, session, models = None, None, set()
    for line in text.splitlines():
        line = line.strip()
        if not line or not any(marker in line for marker in ('"cost-state"', '"modelUsage"',
                                                             '"token_count"', '"session_meta"', '"turn_context"')):
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if not isinstance(row, dict):
            continue
        if row.get("type") == "session_meta":
            session = (row.get("payload") or {}).get("id") or session
        elif row.get("type") == "turn_context":
            model = (row.get("payload") or {}).get("model")
            if model:
                models.add(str(model))
        elif row.get("type") == "event_msg" and (row.get("payload") or {}).get("type") == "token_count":
            usage = ((row.get("payload") or {}).get("info") or {}).get("total_token_usage")
            if isinstance(usage, dict):
                found = {"type": "codex-usage", "sessionId": session,
                         "model": next(iter(models)) if len(models) == 1 else "mixed/unknown",
                         "total_token_usage": usage}
        elif row.get("type") == "cost-state" or row.get("modelUsage"):
            found = row
    if found is None:
        raise ValueError("no host usage record in this file")
    return found


def summarize(record, rates=None, source_id=None):
    """Tokens from the host. Dollars only from the host figure or a complete rate card."""
    if not isinstance(record, dict):
        raise ValueError("usage record must be an object")
    if record.get("type") == "codex-usage":
        counts = record.get("total_token_usage") or {}
        input_tokens = _count(counts.get("input_tokens"))
        cached = _count(counts.get("cached_input_tokens"))
        written = _count(counts.get("cache_write_input_tokens"))
        output = _count(counts.get("output_tokens"))
        if cached + written > input_tokens:
            raise ValueError("Codex cached input exceeds total input")
        if counts.get("total_tokens") is not None and _count(counts["total_tokens"]) != input_tokens + output:
            raise ValueError("Codex total tokens disagree with input plus output")
        usage = {record.get("model") or "unknown": {
            "inputTokens": input_tokens - cached - written, "cacheReadInputTokens": cached,
            "cacheCreationInputTokens": written,
            "outputTokens": output, "thinkingTokens": 0,
        }}
        provenance = "codex-token-count"
    else:
        usage = record.get("modelUsage")
        provenance = "host-cost-state"
    if not isinstance(usage, dict) or not usage:
        raise ValueError("usage record has no modelUsage")
    models = []
    for name, row in usage.items():
        if not isinstance(row, dict):
            continue
        counts = {label: _count(row.get(key)) for key, label in TOKEN_FIELDS}
        item = {"model": str(name), "counts": counts, "tokens": sum(counts.values())}
        model_cost = _money(row.get("costUSD"))
        if model_cost is not None and record.get("hasUnknownModelCost") is False:
            item["cost_usd"] = model_cost
            item["cost_kind"] = "host"
        models.append(item)
    if not models:
        raise ValueError("usage record has no model rows")
    tokens = sum(item["tokens"] for item in models)
    identity = record.get("sessionId") or record.get("session_id") or source_id
    session_id = hashlib.sha256(str(identity).encode("utf-8")).hexdigest()[:24] if identity else "unattributed"
    scope = "shared_session" if identity else "unattributed"
    host_total = _money(record.get("totalCostUSD"))
    if host_total is not None and record.get("hasUnknownModelCost") is False:
        return {
            "provenance": provenance, "session_id": session_id, "scope": scope,
            "tokens": tokens,
            "models": models,
            "cost_usd": host_total,
            "cost_kind": "host",
        }
    estimated = _estimate(models, rates)
    result = {"provenance": provenance, "session_id": session_id,
              "scope": scope, "tokens": tokens, "models": models}
    if estimated is None:
        result["cost_usd"] = None
        result["cost_kind"] = "unavailable"
    else:
        result["cost_usd"] = estimated
        result["cost_kind"] = "estimated"
    return result


def _count(value):
    """Reject malformed host counts before they enter an analytical report."""
    if value is None:
        return 0
    if type(value) is not int or value < 0:
        raise ValueError("host token count must be a nonnegative integer")
    return value


def _money(value):
    """Keep malformed host or rate-card dollars out of reports."""
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        return None
    return float(value)


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
            rate = _money(card[label])
            if rate is None:
                return None
            total += count * rate / 1_000_000
    return round(total, 6)


def detail(counts):
    return ", ".join(f"{label} {count}" for label, count in counts.items())
