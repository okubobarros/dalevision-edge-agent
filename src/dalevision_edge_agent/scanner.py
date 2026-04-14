from __future__ import annotations

import asyncio
import ipaddress
import socket
from typing import Any

from .diagnostics import _parse_ipconfig, _run_cmd

SCAN_PORTS = (80, 554, 8000, 37777, 8999)
SCAN_TIMEOUT_SECONDS = 0.35
SCAN_CONCURRENCY = 128
MAX_HOSTS_PER_NETWORK = 256


def _is_private_ipv4(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    return isinstance(ip, ipaddress.IPv4Address) and ip.is_private and not ip.is_loopback


def _normalize_network(ipv4: str, mask: str | None) -> ipaddress.IPv4Network | None:
    try:
        if mask:
            network = ipaddress.ip_network(f"{ipv4}/{mask}", strict=False)
        else:
            network = ipaddress.ip_network(f"{ipv4}/24", strict=False)
    except ValueError:
        return None
    if not isinstance(network, ipaddress.IPv4Network):
        return None
    # Keep scans lightweight for store LANs; avoid traversing large enterprise ranges.
    if network.num_addresses > MAX_HOSTS_PER_NETWORK:
        return ipaddress.ip_network(f"{ipv4}/24", strict=False)
    return network


def detect_local_networks() -> list[ipaddress.IPv4Network]:
    ipconfig_text = _run_cmd("ipconfig /all")
    parsed = _parse_ipconfig(ipconfig_text)

    candidates: list[tuple[str, str | None]] = []
    ipv4 = str(parsed.get("ipv4") or "").strip()
    mask = str(parsed.get("mask") or "").strip() or None
    gateway = str(parsed.get("gateway") or "").strip()

    if ipv4 and _is_private_ipv4(ipv4):
        candidates.append((ipv4, mask))
    if gateway and _is_private_ipv4(gateway):
        candidates.append((gateway, mask))

    networks: list[ipaddress.IPv4Network] = []
    seen: set[str] = set()
    for host, netmask in candidates:
        network = _normalize_network(host, netmask)
        if network is None:
            continue
        key = str(network)
        if key in seen:
            continue
        seen.add(key)
        networks.append(network)
    return networks


async def _probe_port(host: str, port: int, timeout_seconds: float) -> bool:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host=host, port=port),
            timeout=timeout_seconds,
        )
    except Exception:
        return False
    try:
        writer.close()
        await writer.wait_closed()
    except Exception:
        pass
    return True


def _brand_hint_from_ports(ports: list[int]) -> str:
    port_set = set(ports)
    if 37777 in port_set:
        return "Intelbras/Dahua"
    if 8000 in port_set:
        return "Hikvision"
    if 8999 in port_set:
        return "ONVIF/Generic"
    if 554 in port_set:
        return "RTSP Device"
    return "Generic"


def _rtsp_suggestions(ip: str, ports: list[int]) -> list[str]:
    auth = "usuario:senha@"
    port_set = set(ports)
    suggestions: list[str] = []

    def add(path: str) -> None:
        value = f"rtsp://{auth}{ip}:554{path}"
        if value not in suggestions:
            suggestions.append(value)

    if 37777 in port_set:
        add("/cam/realmonitor?channel=1&subtype=0")
        add("/cam/realmonitor?channel=1&subtype=1")
    if 8000 in port_set:
        add("/Streaming/Channels/101")
        add("/Streaming/Channels/102")
        add("/h264/ch1/main/av_stream")
    if 8999 in port_set:
        add("/onvif1")
        add("/live/main")
    if 554 in port_set and not suggestions:
        add("/stream")
    return suggestions


def _confidence_from_ports(ports: list[int]) -> str:
    port_set = set(ports)
    score = 0
    if 554 in port_set:
        score += 3
    if 37777 in port_set or 8000 in port_set:
        score += 2
    if 8999 in port_set:
        score += 1
    if 80 in port_set:
        score += 1
    if score >= 5:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


async def _scan_host(
    host: str,
    *,
    ports: tuple[int, ...],
    timeout_seconds: float,
    semaphore: asyncio.Semaphore,
) -> dict[str, Any] | None:
    async with semaphore:
        checks = await asyncio.gather(
            *(_probe_port(host, port, timeout_seconds) for port in ports)
        )
    open_ports = [port for port, is_open in zip(ports, checks) if is_open]
    if not open_ports:
        return None
    return {
        "ip": host,
        "ports": open_ports,
        "brand_hint": _brand_hint_from_ports(open_ports),
        "rtsp_suggestions": _rtsp_suggestions(host, open_ports),
        "confidence": _confidence_from_ports(open_ports),
    }


async def scan_network_async(
    *,
    ports: tuple[int, ...] = SCAN_PORTS,
    timeout_seconds: float = SCAN_TIMEOUT_SECONDS,
    concurrency: int = SCAN_CONCURRENCY,
) -> list[dict[str, Any]]:
    networks = detect_local_networks()
    if not networks:
        return []

    hosts: list[str] = []
    for network in networks:
        for host in network.hosts():
            host_str = str(host)
            if host_str not in hosts:
                hosts.append(host_str)

    semaphore = asyncio.Semaphore(max(1, concurrency))
    rows = await asyncio.gather(
        *(
            _scan_host(
                host,
                ports=ports,
                timeout_seconds=timeout_seconds,
                semaphore=semaphore,
            )
            for host in hosts
        )
    )
    results = [row for row in rows if row]
    return sorted(results, key=lambda item: str(item.get("ip") or ""))


def scan_network(
    *,
    ports: tuple[int, ...] = SCAN_PORTS,
    timeout_seconds: float = SCAN_TIMEOUT_SECONDS,
    concurrency: int = SCAN_CONCURRENCY,
) -> list[dict[str, Any]]:
    try:
        return asyncio.run(
            scan_network_async(
                ports=ports,
                timeout_seconds=timeout_seconds,
                concurrency=concurrency,
            )
        )
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                scan_network_async(
                    ports=ports,
                    timeout_seconds=timeout_seconds,
                    concurrency=concurrency,
                )
            )
        finally:
            loop.close()
