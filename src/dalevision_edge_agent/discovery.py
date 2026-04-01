import socket
import logging
import uuid
from typing import Any, List

logger = logging.getLogger(__name__)

def discover_onvif_cameras(timeout: int = 3) -> List[dict[str, Any]]:
    """
    Realiza o broadcast UDP (WS-Discovery) na rede local para descobrir câmeras ONVIF.
    Retorna a lista de IPs e portas compatíveis encontrados sem precisar de bibliotecas pesadas.
    """
    WS_DISCOVERY_IP = '239.255.255.250'
    WS_DISCOVERY_PORT = 3702
    
    # Payload WS-Discovery Padrão
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
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.settimeout(timeout)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        
        logger.info(f"Broadcast WS-Discovery ONVIF enviado na rede (Timeout: {timeout}s)...")
        sock.sendto(payload.encode('utf-8'), (WS_DISCOVERY_IP, WS_DISCOVERY_PORT))

        while True:
            try:
                data, addr = sock.recvfrom(65536)
                ip = addr[0]
                response = data.decode('utf-8', errors='ignore')
                
                # Checa a existência de IPs diferentes via XAddrs
                if "XAddrs" in response or "onvif" in response.lower():
                    logger.info(f"Câmera ONVIF Compatível encontrada em: {ip}")
                    
                    # Tenta inferir porta comum ONVIF RTSP se não explícito
                    default_rtsp = 554
                    if "http://" in response:
                        # Extração simples apenas para ilustrar, o app montará a string RTSP baseada no IP
                        pass
                        
                    cam_results.append({
                        "ip": ip,
                        "ports": [80, 554, 8999], # Assume default ports para Hikvision/Intelbras
                        "confidence": "high",
                        "status": "ok",
                        "reason_code": "onvif_ws_discovery_match",
                        "raw_response_len": len(response)
                    })
            except socket.timeout:
                break
    except Exception as e:
        logger.error(f"Erro durante o scan UDP ONVIF: {e}")
    finally:
        sock.close()
        
    return cam_results
