"""Central logging setup: console + timestamped file under logs/."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path


def setup_run_logging(logs_dir: Path, run_id: str) -> tuple[logging.Logger, Path]:
    """
    Configure root logger: INFO to console, DEBUG to file.
    Returns the application logger and the log file path.
    """
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / f"nqs_{run_id}.log"

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    root.addHandler(fh)
    root.addHandler(ch)

    log = logging.getLogger("nqs")
    log.info("Run started: %s", run_id)
    log.debug("Log file: %s", log_path.resolve())
    return log, log_path


def utc_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
