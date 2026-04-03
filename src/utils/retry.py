"""Retry helper with exponential backoff (bounded)."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def run_with_retry(
    fn: Callable[[], T],
    max_attempts: int,
    base_delay_s: float = 0.1,
    max_delay_s: float = 2.0,
) -> tuple[T | None, int, str | None]:
    """
    Call fn until success or max_attempts exhausted.
    Returns (result, attempts_used, last_error_message).
    """
    last_err: str | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn(), attempt, None
        except Exception as e:
            last_err = str(e)
            if attempt >= max_attempts:
                break
            # Exponential backoff with small jitter
            delay = min(max_delay_s, base_delay_s * (2 ** (attempt - 1)))
            delay = delay * (0.8 + 0.4 * random.random())
            time.sleep(delay)
    return None, max_attempts, last_err
