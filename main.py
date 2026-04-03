#!/usr/bin/env python3
"""
network-qualification-suite — CLI entry point.
Adds ./src to sys.path so packages resolve as: core, tests, utils, simulation, reporting.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _cmd_run(args: argparse.Namespace) -> int:
    from rich.console import Console
    from rich.table import Table

    from core.engine import QualificationEngine
    from simulation.modes import SimulationMode

    console = Console()
    plans = args.plan or [ROOT / "testplans" / "basic_connectivity.yaml"]
    for p in plans:
        if not Path(p).exists():
            console.print(f"[red]Plan not found:[/red] {p}")
            return 2

    mode: SimulationMode | None = None
    if args.simulate:
        try:
            mode = SimulationMode(args.simulate)
        except ValueError:
            console.print(f"[red]Unknown simulation mode:[/red] {args.simulate}")
            return 2

    eng = QualificationEngine(ROOT)
    summary = eng.run(
        [Path(p) for p in plans],
        protocol_filter=args.protocol,
        simulation_mode=mode,
        auto_local_target=bool(args.simulate),
    )

    table = Table(title="Qualification Run Summary", show_lines=True)
    table.add_column("Test ID", style="cyan")
    table.add_column("Name", max_width=36)
    table.add_column("Proto")
    table.add_column("Status")
    table.add_column("ms", justify="right")
    for t in summary.tests:
        st = t.status
        style = "green" if st == "passed" else ("yellow" if st == "skipped" else "red")
        table.add_row(t.test_id, t.name, t.protocol, f"[{style}]{st}[/{style}]", f"{t.duration_ms:.1f}")
    console.print(table)
    console.print(
        f"\n[bold]Run[/bold] {summary.run_id} — "
        f"passed={sum(1 for x in summary.tests if x.status=='passed')} "
        f"failed={sum(1 for x in summary.tests if x.status=='failed')} "
        f"skipped={sum(1 for x in summary.tests if x.status=='skipped')} "
        f"in {summary.duration_sec:.2f}s"
    )
    if summary.log_path:
        console.print(f"Log: {summary.log_path.as_posix()}")
    for k, p in summary.report_paths.items():
        console.print(f"Report ({k}): {p.as_posix()}")

    return 1 if any(t.status == "failed" for t in summary.tests) else 0


def _cmd_simulate(args: argparse.Namespace) -> int:
    args.plan = [ROOT / "testplans" / "failure_reproduction.yaml"]
    args.simulate = args.mode
    return _cmd_run(args)


def _cmd_report(args: argparse.Namespace) -> int:
    from rich.console import Console
    from rich.markdown import Markdown

    console = Console()
    rep = ROOT / "reports"
    if not rep.is_dir():
        console.print("[red]No reports/ directory yet. Run a qualification first.[/red]")
        return 2

    if args.latest:
        json_files = sorted(rep.glob("nqs_report_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not json_files:
            console.print("[yellow]No JSON reports found.[/yellow]")
            return 1
        path = json_files[0]
        data = json.loads(path.read_text(encoding="utf-8"))
        md_path = path.with_suffix(".md")
        if md_path.exists():
            console.print(Markdown(md_path.read_text(encoding="utf-8")))
        else:
            console.print_json(data=data)
        console.print(f"\n[dim]Source: {path}[/dim]")
        return 0

    console.print("Use: python main.py report --latest")
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    from simulation.echo_server import run_standalone_serve
    from simulation.modes import SimulationMode

    def log_fn(msg: str) -> None:
        print(f"[serve] {msg}", flush=True)

    mode = SimulationMode(args.mode)
    tcp = bool(args.tcp)
    udp = bool(args.udp)
    if not tcp and not udp:
        tcp = udp = True
    run_standalone_serve(
        host=args.host,
        tcp_port=args.tcp_port,
        udp_port=args.udp_port,
        mode=mode,
        tcp=tcp,
        udp=udp,
        log_fn=log_fn,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="network-qualification-suite",
        description="Python system/network qualification framework (TCP/UDP lab-style validation).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    pr = sub.add_parser("run", help="Execute test plan(s)")
    pr.add_argument(
        "--plan",
        nargs="+",
        help="One or more YAML/JSON test plans (default: testplans/basic_connectivity.yaml)",
    )
    pr.add_argument("--protocol", choices=["tcp", "udp"], help="Run only TCP or UDP tests")
    pr.add_argument(
        "--simulate",
        metavar="MODE",
        help="Start local echo targets in MODE and run (see: simulate --help)",
    )
    pr.set_defaults(func=_cmd_run)

    ps = sub.add_parser("simulate", help="Run failure-reproduction plan with local simulated target")
    ps.add_argument(
        "--mode",
        required=True,
        choices=[
            "normal",
            "delayed",
            "packet_loss",
            "partial",
            "intermittent",
            "wrong_echo",
            "connection_refused",
        ],
        help="Echo server behavior for this run",
    )
    ps.add_argument("--protocol", choices=["tcp", "udp"], help="Limit to TCP or UDP tests")
    ps.set_defaults(func=_cmd_simulate)

    prp = sub.add_parser("report", help="Show latest human-readable report")
    prp.add_argument("--latest", action="store_true", help="Print latest Markdown report")
    prp.set_defaults(func=_cmd_report)

    pv = sub.add_parser("serve", help="Start local TCP/UDP echo servers for manual testing")
    pv.add_argument("--host", default="127.0.0.1")
    pv.add_argument("--tcp-port", type=int, default=9000)
    pv.add_argument("--udp-port", type=int, default=9001)
    pv.add_argument("--tcp", action="store_true", help="TCP only")
    pv.add_argument("--udp", action="store_true", help="UDP only")
    pv.add_argument(
        "--mode",
        default="normal",
        choices=[
            "normal",
            "delayed",
            "packet_loss",
            "partial",
            "intermittent",
            "wrong_echo",
            "connection_refused",
        ],
    )
    pv.set_defaults(func=_cmd_serve)

    return p


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
