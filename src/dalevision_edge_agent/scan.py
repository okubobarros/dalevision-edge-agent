from __future__ import annotations

import ipaddress
import logging
import socket
from typing import Any, Optional

from .diagnostics import _parse_ipconfig, _run_cmd

SCAN_PORTS = (80, 443, 554, 37777)
SCAN_TIMEOUT_SECONDS = 0.2
MAX_SCAN_WORKERS = 64


def _scan_range(ipv4: str, logger: logging.Logger) -> list[dict[str, Any]]:
    try:
        network = ipaddress.ip_network(f"{ipv4}/24", strict=False)
    except Exception:
        return []

    logger.info("NETSCAN scanning %s ports=%s", network, ",".join(str(p) for p in SCAN_PORTS))
    results: list[dict[str, Any]] = []

    def check_host(host: str) -> Optional[dict[str, Any]]:
        open_ports = []
        for port in SCAN_PORTS:
            try:
                with socket.create_connection((host, port), timeout=SCAN_TIMEOUT_SECONDS):
                    open_ports.append(port)
            except OSError:
                continue
        if open_ports:
            score = 0
            if 554 in open_ports:
                score += 3
            if 37777 in open_ports:
                score += 2
            if 80 in open_ports or 443 in open_ports:
                score += 1
            return {
                "ip": host,
                "ports": open_ports,
                "confidence": "high" if score >= 4 else "medium" if score >= 2 else "low",
            }
        return None

    from concurrent.futures import ThreadPoolExecutor, as_completed

    with ThreadPoolExecutor(max_workers=MAX_SCAN_WORKERS) as executor:
        futures = []
        for host in network.hosts():
            futures.append(executor.submit(check_host, str(host)))
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
    return sorted(results, key=lambda item: item["ip"])


def run_scan(*, logger: logging.Logger) -> list[dict[str, Any]]:
    ipconfig_text = _run_cmd("ipconfig /all")
    parsed = _parse_ipconfig(ipconfig_text)
    ipv4 = parsed.get("ipv4")
    if not ipv4:
        logger.warning("NET001 sem IP local detectado")
        return []
    results = _scan_range(ipv4, logger)
    if not results:
        logger.info("NETSCAN nenhum candidato encontrado")
    return results
