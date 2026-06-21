"""Active network discovery agent."""

from __future__ import annotations

import socket
from typing import Any

from pydantic import BaseModel, ConfigDict


class NetworkProbeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    targets: list[dict[str, Any]]


class NetworkAgent:
    """Probe a small set of common ports for discovered IPs."""

    def __init__(self, ports: list[int] | None = None) -> None:
        self.ports = ports or [22, 80, 443, 8080, 8443]

    async def run(self, ip_addresses: list[str]) -> NetworkProbeResult:
        targets: list[dict[str, Any]] = []
        for ip in ip_addresses:
            open_ports: list[int] = []
            for port in self.ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.4)
                try:
                    sock.connect((ip, port))
                    open_ports.append(port)
                except OSError:
                    pass
                finally:
                    sock.close()
            targets.append({"ip": ip, "open_ports": open_ports})
        return NetworkProbeResult(targets=targets)
