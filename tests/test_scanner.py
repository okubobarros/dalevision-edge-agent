import ipaddress

from dalevision_edge_agent import scanner


def test_detect_local_networks_uses_mask_and_deduplicates(monkeypatch):
    sample = """
    Adaptador Ethernet:
       Endereço IPv4. . . . . . . . . . . . . . . . : 192.168.15.34
       Máscara de Sub-rede . . . . . . . . . . . . : 255.255.255.0
       Gateway Padrão. . . . . . . . . . . . . . . : 192.168.15.1
    """
    monkeypatch.setattr(scanner, "_run_cmd", lambda *_args, **_kwargs: sample)
    networks = scanner.detect_local_networks()
    assert networks == [ipaddress.ip_network("192.168.15.0/24")]


def test_normalize_network_caps_large_subnets():
    network = scanner._normalize_network("10.20.30.40", "255.255.0.0")
    assert network == ipaddress.ip_network("10.20.30.0/24")


def test_brand_hint_and_rtsp_suggestions():
    ports = [554, 37777]
    assert scanner._brand_hint_from_ports(ports) == "Intelbras/Dahua"
    suggestions = scanner._rtsp_suggestions("192.168.1.50", ports)
    assert "rtsp://usuario:senha@192.168.1.50:554/cam/realmonitor?channel=1&subtype=0" in suggestions
    assert "rtsp://usuario:senha@192.168.1.50:554/cam/realmonitor?channel=1&subtype=1" in suggestions


def test_confidence_from_ports():
    assert scanner._confidence_from_ports([554, 37777]) == "high"
    assert scanner._confidence_from_ports([8000]) == "medium"
    assert scanner._confidence_from_ports([80]) == "low"
