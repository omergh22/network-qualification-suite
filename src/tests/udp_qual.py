"""UDP qualification: round-trip, estimated loss, latency."""

from __future__ import annotations

import random
import socket
import time
from typing import Any

from .result_types import StepResult


def _payload(size: int) -> bytes:
    return bytes((random.randint(0, 255)) for _ in range(size))


def udp_roundtrip(
    host: str,
    port: int,
    timeout: float,
    packet_count: int,
    payload_size: int,
) -> StepResult:
    """Send UDP datagrams and expect echo."""
    recv_ok = 0
    latencies: list[float] = []
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Under loss, full `timeout` per packet makes long plans painfully slow; cap per datagram.
    recv_timeout = min(float(timeout), 0.5) if packet_count > 4 else float(timeout)
    udp.settimeout(recv_timeout)
    try:
        for _ in range(max(1, packet_count)):
            payload = _payload(payload_size)
            t0 = time.perf_counter()
            udp.sendto(payload, (host, port))
            try:
                data, _ = udp.recvfrom(65536)
            except TimeoutError:
                continue
            latencies.append((time.perf_counter() - t0) * 1000)
            if data == payload:
                recv_ok += 1
    finally:
        udp.close()

    loss_pct = 100.0 * (packet_count - recv_ok) / packet_count if packet_count else 0
    ok = recv_ok == packet_count
    return StepResult(
        ok=ok,
        message=f"UDP echo {recv_ok}/{packet_count} (est. loss {loss_pct:.1f}%)",
        metrics={
            "packets_sent": packet_count,
            "packets_matched": recv_ok,
            "estimated_loss_percent": round(loss_pct, 2),
            "latency_avg_ms": round(sum(latencies) / len(latencies), 3) if latencies else 0,
            "latency_max_ms": round(max(latencies), 3) if latencies else 0,
        },
    )


def udp_latency(host: str, port: int, timeout: float, payload_size: int, samples: int) -> StepResult:
    return udp_roundtrip(host, port, timeout, max(3, samples), payload_size)


def udp_invalid_port(host: str, bad_port: int, timeout: float) -> StepResult:
    """Send to a closed UDP port — ICMP unreachable may vary by OS; we accept timeout as 'failure observed'."""
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.settimeout(timeout)
    try:
        udp.sendto(b"ping", (host, bad_port))
        try:
            udp.recvfrom(1024)
        except TimeoutError:
            return StepResult(
                True,
                "No response on closed UDP port (expected for this check)",
                metrics={"note": "timeout waiting for reply"},
            )
        return StepResult(False, "Unexpected reply on assumed-closed port", {})
    except OSError as e:
        return StepResult(True, f"Expected failure path: {e}", metrics={"error": str(e)})
    finally:
        udp.close()


def infer_udp_case(test_type: str, test_id: str, name: str) -> str:
    t = (test_type or "").lower()
    if t and t != "auto":
        return t
    blob = f"{test_id} {name}".lower()
    if "invalid" in blob or "closed" in blob:
        return "invalid_port"
    if "latenc" in blob:
        return "latency"
    if "loss" in blob:
        return "roundtrip"
    return "roundtrip"


def run_udp_case(case: str, params: dict[str, Any]) -> StepResult:
    host = str(params["target_host"])
    port = int(params["target_port"])
    timeout = float(params["timeout"])
    payload_size = int(params["payload_size"])
    packet_count = int(params["packet_count"])

    if case == "invalid_port":
        return udp_invalid_port(host, port, timeout)
    if case == "latency":
        return udp_latency(host, port, timeout, payload_size, packet_count)
    return udp_roundtrip(host, port, timeout, packet_count, payload_size)
