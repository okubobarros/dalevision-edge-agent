# ADR 0001-edge-agent-local-windows: Executar agente local Windows no cliente

Data: 2026-05-06T20:09:09.572994Z

## Status

Aceita retroativamente.

## Contexto

O sistema precisa acessar NVR/cameras locais e operar mesmo com redes privadas.

Evidencias: historico Git, code-analysis.md, domain.md e arquivos de runtime/backend/frontend.

## Decisao

Manter um executavel/servico Windows com setup API local, diagnosticos e auto-update.

## Alternativas consideradas

- Rodar tudo na cloud com acesso direto ao NVR
- App mobile como bridge
- Gateway appliance dedicado

## Consequencias

- Exige instalador, autostart e suporte remoto
- Permite RTSP/local network sem expor camera publicamente
- Cria contrato forte entre agente e backend

## Confianca

🟡 INFERIDO para motivacao historica; 🟢 CONFIRMADO para a decisao implementada no codigo.
