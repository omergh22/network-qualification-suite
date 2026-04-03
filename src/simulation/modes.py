"""Failure / stress modes for local echo targets (qualification debugging demos)."""

from __future__ import annotations

from enum import Enum


class SimulationMode(str, Enum):
    NORMAL = "normal"
    DELAYED = "delayed"
    PACKET_LOSS = "packet_loss"
    PARTIAL = "partial"
    INTERMITTENT = "intermittent"
    WRONG_ECHO = "wrong_echo"
    CONNECTION_REFUSED = "connection_refused"  # informational: no TCP listen


_MODE_HELP: dict[str, str] = {
    SimulationMode.NORMAL.value: "Standard echo behavior (baseline).",
    SimulationMode.DELAYED.value: "Adds latency before responding (timeout / perf stress).",
    SimulationMode.PACKET_LOSS.value: "Randomly drops UDP replies (loss / reliability).",
    SimulationMode.PARTIAL.value: "TCP sends truncated reply (partial response bug).",
    SimulationMode.INTERMITTENT.value: "Random failures / flakiness (intermittent bug).",
    SimulationMode.WRONG_ECHO.value: "Echo corrupted payload (protocol validation).",
    SimulationMode.CONNECTION_REFUSED.value: "Do not bind TCP (client sees connection refused on that port).",
}


def describe_mode(mode: str) -> str:
    return _MODE_HELP.get(mode, "Custom or unknown mode.")


def list_modes() -> list[str]:
    return [m.value for m in SimulationMode]
