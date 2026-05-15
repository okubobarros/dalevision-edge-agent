# Diagnóstico de Erros Atuais

## 1. Fricção de setup e configuração [RESOLVIDO] 🟢
- **Sintoma:** usuário precisava editar `.env` manualmente.
- **Status:** Implementado sistema de ativação via token (`/ACTIVATION_TOKEN`). O instalador configura tudo automaticamente.
- **Fix Adicional:** Corrigido link de download no frontend que forçava v1.0.0 em caso de falha na API.

## 2. Ativação com ambiguidades de estado [RESOLVIDO] 🟢
- **Sintoma:** fluxo confuso sem feedback visual do progresso real.
- **Status:** `StoreActivationWizard` implementado com passos baseados em `technical_status` do backend.

## 3. Falso positivo no onboarding [RESOLVIDO] 🟢
- **Sintoma:** usuário avançava manualmente sem o agente estar realmente pronto.
- **Status:** Bloqueio de passos implementado. O sistema só avança quando detecta o heartbeat real do agente.

## 4. Erros técnicos sem tradução operacional [EM PROGRESSO] 🟡
- **Sintoma:** mensagens técnicas que não explicam como resolver o problema.
- **Status:** Catálogo de erros iniciado em `onboarding_error_codes.py`. O comando `doctor` já fornece orientações em linguagem simples.

## 5. Testes manuais longos e repetitivos [EM PROGRESSO] 🟡
- **Sintoma:** necessidade de validar todo o fluxo manualmente a cada release.
- **Status:** Criado script `release_windows.ps1` e testes de registry. Pendente: Automação E2E completa do download à primeira métrica.
