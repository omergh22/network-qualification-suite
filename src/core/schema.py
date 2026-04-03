"""Validate test case dictionaries from YAML/JSON."""

from __future__ import annotations

from typing import Any

REQUIRED = (
    "test_id",
    "name",
    "protocol",
    "target_host",
    "target_port",
    "timeout",
    "expected_result",
    "enabled",
)


def validate_test_case(raw: dict[str, Any], path: str) -> str | None:
    """Return error message or None if valid."""
    for key in REQUIRED:
        if key not in raw:
            return f"{path}: missing required field '{key}'"
    proto = str(raw["protocol"]).upper()
    if proto not in ("TCP", "UDP"):
        return f"{path}: unsupported protocol '{raw['protocol']}'"
    try:
        port = int(raw["target_port"])
        if not (1 <= port <= 65535):
            return f"{path}: target_port out of range"
    except (TypeError, ValueError):
        return f"{path}: target_port must be an integer"
    try:
        float(raw["timeout"])
    except (TypeError, ValueError):
        return f"{path}: timeout must be a number"
    exp = str(raw["expected_result"]).lower()
    if exp not in ("success", "failure"):
        return f"{path}: expected_result must be 'success' or 'failure'"
    if "retry_count" in raw:
        try:
            rc = int(raw["retry_count"])
            if rc < 0:
                return f"{path}: retry_count must be >= 0"
        except (TypeError, ValueError):
            return f"{path}: retry_count must be an integer"
    return None


def normalize_test_case(raw: dict[str, Any]) -> dict[str, Any]:
    """Apply defaults for optional fields."""
    out = dict(raw)
    out["protocol"] = str(out["protocol"]).upper()
    out["timeout"] = float(out["timeout"])
    out["retry_count"] = int(out.get("retry_count", 0))
    out["packet_count"] = int(out.get("packet_count", 1))
    out["payload_size"] = int(out.get("payload_size", 64))
    out["enabled"] = bool(out["enabled"])
    out["description"] = str(out.get("description", ""))
    out["test_type"] = str(out.get("test_type", "auto")).lower()
    return out
