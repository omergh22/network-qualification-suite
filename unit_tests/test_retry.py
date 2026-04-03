"""Unit tests for retry helper (stdlib only in test runner)."""

import unittest

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from utils.retry import run_with_retry  # noqa: E402


class TestRetry(unittest.TestCase):
    def test_succeeds_first_try(self) -> None:
        n = {"c": 0}

        def fn():
            n["c"] += 1
            return 42

        val, attempts, err = run_with_retry(fn, max_attempts=3)
        self.assertEqual(val, 42)
        self.assertEqual(attempts, 1)
        self.assertIsNone(err)

    def test_retries_then_success(self) -> None:
        n = {"c": 0}

        def fn():
            n["c"] += 1
            if n["c"] < 2:
                raise RuntimeError("transient")
            return "ok"

        val, attempts, err = run_with_retry(fn, max_attempts=5, base_delay_s=0.01)
        self.assertEqual(val, "ok")
        self.assertEqual(attempts, 2)
        self.assertIsNone(err)

    def test_exhausts_attempts(self) -> None:
        def fn():
            raise ValueError("always")

        val, attempts, err = run_with_retry(fn, max_attempts=2, base_delay_s=0.01)
        self.assertIsNone(val)
        self.assertEqual(attempts, 2)
        self.assertIn("always", err or "")


if __name__ == "__main__":
    unittest.main()
