from __future__ import annotations

from datetime import datetime, timezone
import ipaddress
import json
import logging
import os
from pathlib import Path
import re
import socket
import subprocess
import shutil
import time
from typing import Any, Optional

import requests
from .cameras import detect_snapshot_support

NVR_PORTS = (80, 443, 554, 37777)

DIAGNOSTIC_TIMEOUT_SECONDS = 8


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run_cmd(command: str, timeout_seconds: int = DIAGNOSTIC_TIMEOUT_SECONDS) -> str:
    try:
        result = subprocess.run(
            ["cmd", "/c", command],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except Exception as exc:
        return f"[command_error] {command}: {exc}"
    output = result.stdout or ""
    if result.stderr:
        output = output + "\n" + result.stderr
    return output.strip()


def _first_ipv4_in_line(line: str) -> Optional[str]:
    match = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})", line)
    if not match:
        return None
    return match.group(1)


def _parse_ipconfig(ipconfig_text: str) -> dict[str, Optional[str]]:
    ipv4 = None
    mask = None
    gateway = None
    dns_servers: list[str] = []

    lines = ipconfig_text.splitlines()
    for idx, line in enumerate(lines):
        text = line.strip()
        lower = text.lower()
        if "ipv4" in lower or "endereço ipv4" in lower:
            value = _first_ipv4_in_line(text)
            if value and ipv4 is None:
                ipv4 = value
        if "subnet mask" in lower or "máscara de sub-rede" in lower:
            value = _first_ipv4_in_line(text)
            if value and mask is None:
                mask = value
        if "default gateway" in lower or "gateway padrão" in lower:
            value = _first_ipv4_in_line(text)
            if value:
                gateway = value
            else:
                if idx + 1 < len(lines):
                    gateway = _first_ipv4_in_line(lines[idx + 1].strip()) or gateway
        if "dns servers" in lower or "servidores dns" in lower:
            value = _first_ipv4_in_line(text)
            if value:
                dns_servers.append(value)
            j = idx + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if not next_line:
                    break
                next_ip = _first_ipv4_in_line(next_line)
                if next_ip:
                    dns_servers.append(next_ip)
                    j += 1
                    continue
                break

    dns_unique = []
    for item in dns_servers:
        if item not in dns_unique:
            dns_unique.append(item)

    return {
        "ipv4": ipv4,
        "mask": mask,
        "gateway": gateway,
        "dns_servers": ", ".join(dns_unique) if dns_unique else None,
    }


def _compute_cidr(ipv4: Optional[str], mask: Optional[str]) -> Optional[str]:
    if not ipv4 or not mask:
        return None
    try:
        network = ipaddress.ip_network(f"{ipv4}/{mask}", strict=False)
    except Exception:
        return None
    return str(network)


def _ping_gateway(gateway: Optional[str]) -> Optional[float]:
    if not gateway:
        return None
    output = _run_cmd(f"ping -n 1 -w 1000 {gateway}", timeout_seconds=3)
    match = re.search(r"tempo[=<](\d+)ms|time[=<](\d+)ms", output, re.IGNORECASE)
    if match:
        value = match.group(1) or match.group(2)
        try:
            return float(value)
        except Exception:
            return None
    return None


def _api_check(cloud_base_url: str, logger: logging.Logger) -> dict[str, Any]:
    if not cloud_base_url:
        return {"ok": False, "error": "missing_cloud_base_url"}
    try:
        response = requests.get(cloud_base_url, timeout=5)
        return {"ok": response.status_code < 500, "status": response.status_code}
    except requests.RequestException as exc:
        logger.info("NETAPI cloud_base_url=%s error=%s", cloud_base_url, exc)
        return {"ok": False, "error": str(exc)}


def _check_ports(ip: str, ports: tuple[int, ...]) -> list[int]:
    open_ports = []
    for port in ports:
        try:
            with socket.create_connection((ip, port), timeout=1):
                open_ports.append(port)
        except OSError:
            continue
    return open_ports


def _dns_check() -> dict[str, Any]:
    try:
        host = "google.com"
        resolved = socket.gethostbyname(host)
        return {"ok": True, "host": host, "resolved": resolved}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _internet_check() -> dict[str, Any]:
    target = ("1.1.1.1", 443)
    try:
        with socket.create_connection(target, timeout=2):
            return {"ok": True, "target": "1.1.1.1:443"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _disk_check(path: Path) -> dict[str, Any]:
    try:
        usage = shutil.disk_usage(path)
        return {
            "total_gb": round(usage.total / (1024**3), 2),
            "free_gb": round(usage.free / (1024**3), 2),
        }
    except Exception as exc:
        return {"error": str(exc)}


def _permissions_check(path: Path) -> dict[str, Any]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / f".permcheck-{int(time.time())}.tmp"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _summarize(
    *,
    ipv4: Optional[str],
    mask: Optional[str],
    gateway: Optional[str],
    dns_servers: Optional[str],
    local_cidr: Optional[str],
    cloud_base_url: str,
    nvr_ip: Optional[str],
    network_segmented: bool,
    ping_ms: Optional[float],
    api_ok: bool,
    dns_ok: bool,
    snapshot_ok: bool,
    permissions_ok: bool,
    internet_ok: bool,
) -> str:
    lines = []
    lines.append("DALE Vision Edge Agent - Diagnostics")
    lines.append(f"ts={_utc_timestamp()}")
    lines.append(f"cloud_base_url={cloud_base_url or 'N/A'}")
    lines.append(f"local_ip={ipv4 or 'N/A'}")
    lines.append(f"subnet_mask={mask or 'N/A'}")
    lines.append(f"local_cidr={local_cidr or 'N/A'}")
    lines.append(f"gateway={gateway or 'N/A'}")
    lines.append(f"dns_servers={dns_servers or 'N/A'}")
    lines.append(f"gateway_ping_ms={ping_ms if ping_ms is not None else 'N/A'}")
    lines.append(f"dns_ok={'sim' if dns_ok else 'nao'}")
    lines.append(f"api_ok={'sim' if api_ok else 'nao'}")
    lines.append(f"internet_ok={'sim' if internet_ok else 'nao'}")
    lines.append(f"snapshot_ok={'sim' if snapshot_ok else 'nao'}")
    lines.append(f"write_ok={'sim' if permissions_ok else 'nao'}")
    if not gateway:
        lines.append("NET001 sem gateway padrao")
    if nvr_ip:
        lines.append(f"nvr_ip={nvr_ip}")
        if network_segmented:
            lines.append("NET002 NVR fora do subnet local. Conecte o PC na mesma VLAN.")
    lines.append("")
    lines.append("Copie e cole este bloco para suporte.")
    return "\n".join(lines)


def run_doctor(
    *,
    cloud_base_url: str,
    logger: logging.Logger,
    nvr_ip: Optional[str] = None,
    share: bool = False,
) -> dict[str, Any]:
    ipconfig_text = _run_cmd("ipconfig /all")
    route_text = _run_cmd("route print")
    arp_text = _run_cmd("arp -a")
    wlan_text = _run_cmd("netsh wlan show interfaces")

    parsed = _parse_ipconfig(ipconfig_text)
    ipv4 = parsed.get("ipv4")
    mask = parsed.get("mask")
    gateway = parsed.get("gateway")
    dns_servers = parsed.get("dns_servers")
    local_cidr = _compute_cidr(ipv4, mask)
    ping_ms = _ping_gateway(gateway)
    api_check = _api_check(cloud_base_url, logger)
    dns_check = _dns_check()
    internet_check = _internet_check()
    snapshot_support = detect_snapshot_support(logger)

    log_dir = _log_dir()
    disk_check = _disk_check(log_dir)
    permissions_check = _permissions_check(log_dir)

    network_segmented = False
    if nvr_ip and local_cidr:
        try:
            network = ipaddress.ip_network(local_cidr, strict=False)
            network_segmented = ipaddress.ip_address(nvr_ip) not in network
        except Exception:
            network_segmented = False

    nvr_ports = _check_ports(nvr_ip, NVR_PORTS) if nvr_ip else []
    suggested_actions: list[str] = []
    if not gateway:
        suggested_actions.append("NET001 Verifique o cabo/rede. Sem gateway padrao.")
    if network_segmented:
        suggested_actions.append(
            "NET002 Conecte o PC na mesma rede/VLAN do NVR (ex.: 192.168.15.x)."
        )
    if nvr_ip and 554 not in nvr_ports:
        suggested_actions.append("RTSP554 Porta 554 fechada no NVR.")

    summary = _summarize(
        ipv4=ipv4,
        mask=mask,
        gateway=gateway,
        dns_servers=dns_servers,
        local_cidr=local_cidr,
        cloud_base_url=cloud_base_url,
        nvr_ip=nvr_ip,
        network_segmented=network_segmented,
        ping_ms=ping_ms,
        api_ok=bool(api_check.get("ok")),
        dns_ok=bool(dns_check.get("ok")),
        snapshot_ok=bool(snapshot_support.get("ffmpeg")) or snapshot_support.get("opencv") == "yes",
        permissions_ok=bool(permissions_check.get("ok")),
        internet_ok=bool(internet_check.get("ok")),
    )

    diagnostics_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    payload = {
        "ts": _utc_timestamp(),
        "id": diagnostics_id,
        "cloud_base_url": cloud_base_url,
        "network_info": {
            "local_ipv4": ipv4,
            "local_mask": mask,
            "local_cidr": local_cidr,
            "gateway": gateway,
            "dns_servers": dns_servers,
        },
        "gateway_ping_ms": ping_ms,
        "nvr_ip": nvr_ip,
        "network_segmented": network_segmented,
        "api_check": api_check,
        "dns_check": dns_check,
        "internet_check": internet_check,
        "snapshot_support": snapshot_support,
        "disk_check": disk_check,
        "permissions_check": permissions_check,
        "scan_results": [],
        "nvrs_found": [],
        "ports": {"nvr": nvr_ports},
        "rtsp_test_results": [],
        "suggested_actions": suggested_actions,
        "commands": {
            "ipconfig": ipconfig_text,
            "route_print": route_text,
            "arp": arp_text,
            "wlan": wlan_text,
        },
        "summary": summary,
    }

    log_dir.mkdir(parents=True, exist_ok=True)
    json_path = log_dir / f"diagnostics-{diagnostics_id}.json"
    txt_path = log_dir / f"diagnostics-{diagnostics_id}.txt"
    json_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    txt_path.write_text(summary, encoding="utf-8")

    print(summary)
    logger.info("Diagnostics saved: %s %s", json_path, txt_path)

    if share:
        share_zip = log_dir / f"diagnostics-share-{diagnostics_id}.zip"
        _build_share_zip(
            share_zip=share_zip,
            logger=logger,
            json_path=json_path,
            txt_path=txt_path,
        )
        logger.info("Diagnostics share ZIP: %s", share_zip)
    return payload


def _build_share_zip(
    *,
    share_zip: Path,
    logger: logging.Logger,
    json_path: Path,
    txt_path: Path,
) -> None:
    import zipfile

    log_dir = _log_dir()
    if share_zip.exists():
        share_zip.unlink()

    with zipfile.ZipFile(share_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if json_path.exists():
            zf.write(json_path, json_path.name)
        if txt_path.exists():
            zf.write(txt_path, txt_path.name)
        for log_file in log_dir.glob("*.log"):
            zf.write(log_file, log_file.name)
    logger.info("NETSHARE diagnostics package ready")
def _log_dir() -> Path:
    log_root = os.getenv("DALE_LOG_DIR")
    if log_root:
        return Path(log_root)
    program_data = os.getenv("PROGRAMDATA")
    if program_data:
        return Path(program_data) / "DaleVision" / "logs"
    return Path.cwd() / "logs"
