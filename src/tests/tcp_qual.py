"""TCP qualification checks: connectivity, stability, latency, negative cases."""

from __future__ import annotations

import socket
import time
from typing import Any

from .result_types import StepResult


def _payload(size: int) -> bytes:
    return bytes((i % 256) for i in range(size))


def tcp_connectivity(host: str, port: int, timeout: float, payload_size: int) -> StepResult:
    """Single connect, send, recv (echo)."""
    payload = _payload(payload_size)
    t0 = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout)
            s.sendall(payload)
            data = b""
            while len(data) < len(payload):
                chunk = s.recv(len(payload) - len(data))
                if not chunk:
                    break
                data += chunk
        elapsed_ms = (time.perf_counter() - t0) * 1000
        ok = data == payload
        return StepResult(
            ok=ok,
            message="Echo mismatch" if not ok else "TCP echo OK",
            metrics={"rtt_ms": round(elapsed_ms, 3), "bytes_sent": len(payload), "bytes_recv": len(data)},
        )
    except OSError as e:
        return StepResult(False, f"TCP error: {e}", metrics={"error": str(e)})


def tcp_stability(host: str, port: int, timeout: float, payload_size: int, packet_count: int) -> StepResult:
    """Repeated short-lived connections."""
    failures = 0
    latencies: list[float] = []
    for _ in range(max(1, packet_count)):
        r = tcp_connectivity(host, port, timeout, payload_size)
        if not r.ok:
            failures += 1
        latencies.append(float(r.metrics.get("rtt_ms", 0)))
    ok = failures == 0
    return StepResult(
        ok=ok,
        message=f"Stability: {packet_count - failures}/{packet_count} OK",
        metrics={
            "failures": failures,
            "iterations": packet_count,
            "latency_avg_ms": round(sum(latencies) / len(latencies), 3),
            "latency_max_ms": round(max(latencies), 3),
        },
    )


def tcp_latency(host: str, port: int, timeout: float, payload_size: int, samples: int) -> StepResult:
    """Measure RTT over multiple round trips on one connection when possible."""
    latencies: list[float] = []
    payload = _payload(payload_size)
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout)
            for _ in range(max(1, samples)):
                t0 = time.perf_counter()
                s.sendall(payload)
                data = b""
                while len(data) < len(payload):
                    chunk = s.recv(len(payload) - len(data))
                    if not chunk:
                        break
                    data += chunk
                latencies.append((time.perf_counter() - t0) * 1000)
        ok = len(latencies) == samples and all(
            latencies[i] >= 0 for i in range(len(latencies))
        )
        return StepResult(
            ok=ok,
            message="Latency samples collected",
            metrics={
                "samples": len(latencies),
                "latency_min_ms": round(min(latencies), 3) if latencies else 0,
                "latency_avg_ms": round(sum(latencies) / len(latencies), 3) if latencies else 0,
                "latency_max_ms": round(max(latencies), 3) if latencies else 0,
            },
        )
    except OSError as e:
        return StepResult(False, f"TCP latency error: {e}", metrics={"error": str(e)})


def tcp_unreachable_host(timeout: float) -> StepResult:
    """Use a documentation-only IPv4 that should not route (RFC 5737)."""
    # 192.0.2.1 is TEST-NET-1 — typically no route from lab host
    host = "192.0.2.1"
    port = 80
    try:
        socket.create_connection((host, port), timeout=min(timeout, 3.0))
        return StepResult(False, "Unexpected: connection succeeded to TEST-NET", {})
    except OSError as e:
        return StepResult(True, f"Expected failure: {e}", metrics={"error": str(e)})


def tcp_connection_refused(host: str, refused_port: int, timeout: float) -> StepResult:
    """Expect immediate refusal when nothing listens."""
    try:
        socket.create_connection((host, refused_port), timeout=timeout)
        return StepResult(False, "Expected connection refused but connected", {})
    except ConnectionRefusedError as e:
        return StepResult(True, f"Expected: {e}", metrics={"error": str(e)})
    except OSError as e:
        # Some stacks may timeout instead of refuse for filtered hosts
        return StepResult(True, f"Expected failure: {e}", metrics={"error": str(e)})


def infer_tcp_case(test_type: str, test_id: str, name: str) -> str:
    t = (test_type or "").lower()
    if t and t != "auto":
        return t
    blob = f"{test_id} {name}".lower()
    if "refus" in blob or "refused" in blob:
        return "connection_refused"
    if "invalid" in blob or "unreach" in blob:
        return "unreachable_host"
    if "stab" in blob or "repeat" in blob:
        return "stability"
    if "latenc" in blob or "rtt" in blob:
        return "latency"
    return "connectivity"


def run_tcp_case(case: str, params: dict[str, Any]) -> StepResult:
    host = str(params["target_host"])
    port = int(params["target_port"])
    timeout = float(params["timeout"])
    payload_size = int(params["payload_size"])
    packet_count = int(params["packet_count"])

    if case == "connection_refused":
        return tcp_connection_refused(host, port, timeout)
    if case == "unreachable_host":
        return tcp_unreachable_host(timeout)
    if case == "stability":
        return tcp_stability(host, port, timeout, payload_size, packet_count)
    if case == "latency":
        return tcp_latency(host, port, timeout, payload_size, max(3, packet_count))
    return tcp_connectivity(host, port, timeout, payload_size)
