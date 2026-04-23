import socket
import logging
import uuid
from typing import Any, List

logger = logging.getLogger(__name__)

def discover_onvif_cameras(timeout: int = 2) -> List[dict[str, Any]]:
    """
    Realiza o broadcast UDP (WS-Discovery) na rede local para descobrir câmeras ONVIF.
    Retorna a lista de dispositivos encontrados com sugestões de paths RTSP.
    """
    WS_DISCOVERY_IP = '239.255.255.250'
    WS_DISCOVERY_PORT = 3702
    
    msg_id = uuid.uuid4().urn
    payload = f"""<?xml version="1.0" encoding="utf-8"?>
    <Envelope xmlns:dn="http://www.onvif.org/ver10/network/wsdl" xmlns="http://www.w3.org/2003/05/soap-envelope">
      <Header>
        <wsa:MessageID xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">{msg_id}</wsa:MessageID>
        <wsa:To xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>
        <wsa:Action xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>
      </Header>
      <Body>
        <Probe xmlns="http://schemas.xmlsoap.org/ws/2005/04/discovery" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
          <Types>dn:NetworkVideoTransmitter</Types>
          <Scopes />
        </Probe>
      </Body>
    </Envelope>"""

    cam_results = []
    seen_ips = set()
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.settimeout(timeout)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 4)
        
        logger.info(f"Broadcast WS-Discovery ONVIF enviado (Timeout: {timeout}s)...")
        sock.sendto(payload.encode('utf-8'), (WS_DISCOVERY_IP, WS_DISCOVERY_PORT))

        while True:
            try:
                data, addr = sock.recvfrom(65536)
                ip = addr[0]
                if ip in seen_ips:
                    continue
                
                response = data.decode('utf-8', errors='ignore')
                
                if "XAddrs" in response or "onvif" in response.lower():
                    logger.info(f"Câmera ONVIF detectada em: {ip}")
                    seen_ips.add(ip)
                    
                    # Extração rudimentar de informações dos Scopes do ONVIF
                    # Scopes geralmente contêm strings como 'onvif://www.onvif.org/name/Camera_Entrance'
                    name_hint = ""
                    if "<Scopes>" in response:
                        try:
                            scopes_content = response.split("<Scopes>")[1].split("</Scopes>")[0]
                            for scope in scopes_content.split():
                                if "/name/" in scope:
                                    name_hint = scope.split("/name/")[1].replace("_", " ").strip()
                                    break
                                if "/location/" in scope:
                                    name_hint = scope.split("/location/")[1].replace("_", " ").strip()
                                    break
                        except:
                            pass

                    # Sugestões de RTSP baseadas no IP e marcas comuns (Hikvision, Intelbras, Dahua)
                    paths = [
                        "/cam/realmonitor?channel=1&subtype=0", # Intelbras/Dahua
                        "/h264/ch1/main/av_stream",            # Hikvision
                        "/live/main",                          # Genérica
                        "/onvif1"                              # Genérica ONVIF
                    ]
                    
                    cam_results.append({
                        "ip": ip,
                        "name": name_hint or f"Câmera {ip.split('.')[-1]}",
                        "brand_hint": "Intelbras/Hikvision/Dahua" if "XAddrs" in response else "Generic",
                        "model": "ONVIF Camera",
                        "ports": [80, 554, 8000, 8999], 
                        "rtsp_suggestions": [f"rtsp://admin:admin@{ip}{p}" for p in paths],
                        "confidence": "high",
                        "status": "ok",
                        "reason_code": "onvif_ws_discovery_match"
                    })
            except socket.timeout:
                break
    except Exception as e:
        logger.error(f"Erro no scan UDP ONVIF: {e}")
    finally:
        sock.close()
        
    return cam_results
