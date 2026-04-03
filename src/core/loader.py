"""Load test plans from YAML or JSON."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .schema import normalize_test_case, validate_test_case

log = logging.getLogger("nqs.loader")

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def load_test_plans(paths: list[Path]) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Load and merge tests from multiple files.
    Returns (tests, errors).
    """
    tests: list[dict[str, Any]] = []
    errors: list[str] = []

    for p in paths:
        if not p.exists():
            errors.append(f"File not found: {p}")
            continue
        try:
            raw_text = p.read_text(encoding="utf-8")
        except OSError as e:
            errors.append(f"Cannot read {p}: {e}")
            continue

        data: Any
        try:
            if p.suffix.lower() in (".yaml", ".yml"):
                if yaml is None:
                    errors.append("PyYAML is required for .yaml/.yml plans")
                    continue
                data = yaml.safe_load(raw_text)
            elif p.suffix.lower() == ".json":
                data = json.loads(raw_text)
            else:
                errors.append(f"Unsupported extension: {p}")
                continue
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON {p}: {e}")
            continue
        except ValueError as e:
            errors.append(f"Invalid config {p}: {e}")
            continue
        except Exception as e:
            if yaml and isinstance(e, yaml.YAMLError):
                errors.append(f"Invalid YAML {p}: {e}")
                continue
            errors.append(f"Parse error {p}: {e}")
            continue

        if not isinstance(data, dict) or "tests" not in data:
            errors.append(f"{p}: root must be an object with 'tests' array")
            continue

        if not isinstance(data["tests"], list):
            errors.append(f"{p}: 'tests' must be a list")
            continue

        for i, item in enumerate(data["tests"]):
            sub = f"{p} tests[{i}]"
            if not isinstance(item, dict):
                errors.append(f"{sub}: must be an object")
                continue
            err = validate_test_case(item, sub)
            if err:
                errors.append(err)
                continue
            tests.append(normalize_test_case(item))

    return tests, errors
