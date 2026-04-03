"""Orchestrates loading plans, optional local targets, execution, and reporting."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reporting.generator import write_reports
from simulation.echo_server import EchoServerManager
from simulation.modes import SimulationMode
from utils.env_info import collect_environment_snapshot
from utils.logging_config import setup_run_logging, utc_run_id

from .loader import load_test_plans
from .runner import ExecutedTest, run_single_test

log = logging.getLogger("nqs.engine")


@dataclass
class RunSummary:
    run_id: str
    tests: list[ExecutedTest]
    environment: dict[str, Any]
    log_path: Path | None
    report_paths: dict[str, Path]
    load_errors: list[str]
    duration_sec: float


class QualificationEngine:
    def __init__(self, project_root: Path) -> None:
        self.root = project_root.resolve()
        self.logs_dir = self.root / "logs"
        self.reports_dir = self.root / "reports"
        self.default_tcp_port = 9000
        self.default_udp_port = 9001
        self.default_host = "127.0.0.1"

    def run(
        self,
        plan_paths: list[Path],
        protocol_filter: str | None = None,
        simulation_mode: SimulationMode | None = None,
        auto_local_target: bool = False,
    ) -> RunSummary:
        import time

        run_id = utc_run_id()
        logger, log_path = setup_run_logging(self.logs_dir, run_id)
        env = collect_environment_snapshot()
        logger.info("Environment snapshot: %s", env)

        t0 = time.perf_counter()
        tests_raw, load_errors = load_test_plans([p.resolve() for p in plan_paths])

        if load_errors and not tests_raw:
            for e in load_errors:
                logger.error("%s", e)
            write_reports(
                self.reports_dir,
                run_id,
                [],
                env,
                load_errors,
                time.perf_counter() - t0,
            )
            return RunSummary(
                run_id=run_id,
                tests=[],
                environment=env,
                log_path=log_path,
                report_paths={},
                load_errors=load_errors,
                duration_sec=time.perf_counter() - t0,
            )

        for e in load_errors:
            logger.warning("Plan warning: %s", e)

        mgr: EchoServerManager | None = None
        if auto_local_target and simulation_mode is not None:
            mgr = EchoServerManager(
                host=self.default_host,
                tcp_port=self.default_tcp_port,
                udp_port=self.default_udp_port,
                mode=simulation_mode,
            )
            mgr.start(tcp=True, udp=True)
            logger.info(
                "Started local echo targets mode=%s tcp=%s udp=%s",
                simulation_mode.value,
                self.default_tcp_port,
                self.default_udp_port,
            )

        executed: list[ExecutedTest] = []
        try:
            for tc in tests_raw:
                if protocol_filter:
                    if tc["protocol"].upper() != protocol_filter.upper():
                        executed.append(
                            ExecutedTest(
                                test_id=tc["test_id"],
                                name=tc["name"],
                                protocol=tc["protocol"],
                                status="skipped",
                                duration_ms=0.0,
                                message=f"Skipped (--protocol {protocol_filter})",
                                retries_used=0,
                            )
                        )
                        continue
                logger.info("Running %s — %s", tc["test_id"], tc["name"])
                et = run_single_test(tc)
                executed.append(et)
                logger.info(
                    "Result %s: %s (%s ms)",
                    et.test_id,
                    et.status,
                    et.duration_ms,
                )
        finally:
            if mgr is not None:
                mgr.stop()
                logger.info("Stopped local echo targets")

        duration = time.perf_counter() - t0
        paths = write_reports(
            self.reports_dir,
            run_id,
            executed,
            env,
            load_errors,
            duration,
        )
        logger.info("Run complete in %.2fs", duration)

        return RunSummary(
            run_id=run_id,
            tests=executed,
            environment=env,
            log_path=log_path,
            report_paths=paths,
            load_errors=load_errors,
            duration_sec=duration,
        )
