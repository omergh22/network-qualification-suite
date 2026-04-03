"""
Local TCP/UDP echo servers for qualification runs.
Supports injectable behaviors to reproduce common lab failures.
"""

from __future__ import annotations

import random
import socket
import threading
import time
from dataclasses import dataclass, field
from typing import Callable

from .modes import SimulationMode


@dataclass
class EchoServerManager:
    """Run TCP and/or UDP echo in background threads."""

    host: str = "127.0.0.1"
    tcp_port: int = 9000
    udp_port: int = 9001
    mode: SimulationMode = SimulationMode.NORMAL
    _threads: list[threading.Thread] = field(default_factory=list)
    _stop: threading.Event = field(default_factory=threading.Event)

    def start(self, tcp: bool = True, udp: bool = True) -> None:
        if tcp and self.mode != SimulationMode.CONNECTION_REFUSED:
            t = threading.Thread(target=self._tcp_loop, name="nqs-tcp-echo", daemon=True)
            t.start()
            self._threads.append(t)
        if udp:
            t = threading.Thread(target=self._udp_loop, name="nqs-udp-echo", daemon=True)
            t.start()
            self._threads.append(t)

    def stop(self, join_timeout: float = 2.0) -> None:
        self._stop.set()
        for t in self._threads:
            t.join(timeout=join_timeout)
        self._threads.clear()

    def _maybe_delay(self) -> None:
        if self.mode == SimulationMode.DELAYED:
            time.sleep(0.35)

    def _tcp_client_worker(self, conn: socket.socket, addr: tuple) -> None:
        try:
            conn.settimeout(30.0)
            data = conn.recv(65536)
            if not data:
                return
            self._maybe_delay()
            if self.mode == SimulationMode.INTERMITTENT and random.random() < 0.4:
                conn.close()
                return
            if self.mode == SimulationMode.PARTIAL:
                conn.sendall(data[: max(1, len(data) // 3)])
                return
            if self.mode == SimulationMode.WRONG_ECHO:
                conn.sendall(b"WRONG:" + data)
                return
            conn.sendall(data)
        except OSError:
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass

    def _tcp_loop(self) -> None:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            srv.bind((self.host, self.tcp_port))
            srv.listen(32)
            srv.settimeout(0.5)
            while not self._stop.is_set():
                try:
                    conn, addr = srv.accept()
                except TimeoutError:
                    continue
                except OSError:
                    break
                th = threading.Thread(
                    target=self._tcp_client_worker,
                    args=(conn, addr),
                    daemon=True,
                )
                th.start()
        finally:
            try:
                srv.close()
            except OSError:
                pass

    def _udp_loop(self) -> None:
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            udp.bind((self.host, self.udp_port))
            udp.settimeout(0.5)
            while not self._stop.is_set():
                try:
                    data, addr = udp.recvfrom(65536)
                except TimeoutError:
                    continue
                except OSError:
                    break
                self._maybe_delay()
                if self.mode == SimulationMode.PACKET_LOSS and random.random() < 0.35:
                    continue
                if self.mode == SimulationMode.INTERMITTENT and random.random() < 0.35:
                    continue
                if self.mode == SimulationMode.WRONG_ECHO:
                    udp.sendto(b"BAD:" + data, addr)
                else:
                    udp.sendto(data, addr)
        finally:
            try:
                udp.close()
            except OSError:
                pass


def run_standalone_serve(
    host: str,
    tcp_port: int,
    udp_port: int,
    mode: SimulationMode,
    tcp: bool,
    udp: bool,
    log_fn: Callable[[str], None],
) -> None:
    """Blocking: start servers and wait for KeyboardInterrupt."""
    mgr = EchoServerManager(host=host, tcp_port=tcp_port, udp_port=udp_port, mode=mode)
    mgr.start(tcp=tcp, udp=udp)
    log_fn(
        f"Echo servers — host={host} tcp={tcp_port if tcp else 'off'} "
        f"udp={udp_port if udp else 'off'} mode={mode.value}"
    )
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        log_fn("Stopping servers...")
        mgr.stop()
