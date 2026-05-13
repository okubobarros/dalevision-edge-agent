# ADR 0004-snapshot-best-effort: Snapshot best-effort para onboarding e ROI

Data: 2026-05-06T20:09:09.572994Z

## Status

Aceita retroativamente.

## Contexto

UI precisa de imagem da camera para configurar ROI, mas OpenCV/ffmpeg podem faltar no cliente.

Evidencias: historico Git, code-analysis.md, domain.md e arquivos de runtime/backend/frontend.

## Decisao

Tentar OpenCV, depois ffmpeg; se ambos falharem, logar claramente e seguir sem snapshot.

## Alternativas consideradas

- Falhar instalacao se snapshot indisponivel
- Exigir ffmpeg empacotado sempre
- Tunnel de video ao vivo obrigatório

## Consequencias

- Onboarding continua em ambientes parciais
- Suporte recebe codigo claro de diagnostico
- Pode reduzir qualidade da configuracao se usuario nao tiver preview

## Confianca

🟡 INFERIDO para motivacao historica; 🟢 CONFIRMADO para a decisao implementada no codigo.
