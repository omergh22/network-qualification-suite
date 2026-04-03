"""Execute a single normalized test case."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from tests import tcp_qual, udp_qual

log = logging.getLogger("nqs.runner")


@dataclass
class ExecutedTest:
    test_id: str
    name: str
    protocol: str
    status: str  # passed | failed | skipped
    duration_ms: float
    message: str
    retries_used: int
    metrics: dict[str, Any] = field(default_factory=dict)
    error_detail: str | None = None


def _evaluate(expected: str, step_ok: bool) -> bool:
    exp = expected.lower()
    if exp == "success":
        return step_ok
    if exp == "failure":
        return not step_ok
    return False


def run_single_test(tc: dict[str, Any]) -> ExecutedTest:
    """Run one test with optional retries (only on unexpected exception paths — simplified)."""
    if not tc["enabled"]:
        return ExecutedTest(
            test_id=tc["test_id"],
            name=tc["name"],
            protocol=tc["protocol"],
            status="skipped",
            duration_ms=0.0,
            message="Disabled in plan",
            retries_used=0,
        )

    t0 = time.perf_counter()
    retries = max(1, int(tc["retry_count"]) + 1)
    attempts = 0
    last_msg = ""
    last_metrics: dict[str, Any] = {}
    last_ok_eval = False

    for attempt in range(retries):
        attempts = attempt + 1
        try:
            if tc["protocol"] == "TCP":
                case = tcp_qual.infer_tcp_case(tc["test_type"], tc["test_id"], tc["name"])
                step = tcp_qual.run_tcp_case(case, tc)
            else:
                case = udp_qual.infer_udp_case(tc["test_type"], tc["test_id"], tc["name"])
                step = udp_qual.run_udp_case(case, tc)

            last_msg = step.message
            last_metrics = dict(step.metrics)
            last_metrics["test_type_resolved"] = case
            last_ok_eval = _evaluate(tc["expected_result"], step.ok)

            if last_ok_eval:
                break
            log.warning(
                "Test attempt %s/%s failed eval for %s: %s",
                attempts,
                retries,
                tc["test_id"],
                last_msg,
            )
        except Exception as e:
            last_msg = f"Exception: {e}"
            last_metrics = {"error": str(e)}
            last_ok_eval = _evaluate(tc["expected_result"], False)
            log.exception("Test %s raised", tc["test_id"])
            if last_ok_eval:
                break

    duration_ms = (time.perf_counter() - t0) * 1000
    status = "passed" if last_ok_eval else "failed"
    err = None if status == "passed" else last_msg

    return ExecutedTest(
        test_id=tc["test_id"],
        name=tc["name"],
        protocol=tc["protocol"],
        status=status,
        duration_ms=round(duration_ms, 3),
        message=last_msg,
        retries_used=attempts,
        metrics=last_metrics,
        error_detail=err,
    )
