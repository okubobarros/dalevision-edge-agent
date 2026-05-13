# frontend-copilot-reports-admin, Casos de Borda e Cenários de Exceção

> Especificação de situações excepcionais, fallbacks e tratamentos de erro do módulo.

## 1. Copilot Hub

| Caso de Borda (Edge Case) | Comportamento Atual / Fallback | Confiança |
|---------------------------|--------------------------------|-----------|
| **Navegação com `storeId` nulo (Rede)** | Copilot não aciona a API externa e responde localmente com texto estático de fallback, poupando tokens. | 🟢 |
| **Falha na conexão com a API ao enviar mensagem** | Renderiza `role: "assistant"` estático informando erro claro de conectividade na UI. | 🟢 |
| **Múltiplos `?prompt=` enviados na URL em re-renders** | Protegido pelo `useRef(consumedContextRef)`; contexto injetado apenas uma única vez na sessão ativa. | 🟢 |
| **`localStorage` desabilitado ou com JSON corrompido** | O parser do Kanban e de Assets falha silenciosamente e retorna os defaults (arrays vazios) ao invés de quebrar a tela inteira. | 🟢 |
| **Upload de asset sem seleção de loja (storeId=null)** | O arquivo recebe o source `"local"` e status imediato `"ready"`, ficando guardado apenas em cache sem fazer POST na API. | 🟢 |

## 2. Reports (Painel de KPI & Ledger)

| Caso de Borda (Edge Case) | Comportamento Atual / Fallback | Confiança |
|---------------------------|--------------------------------|-----------|
| **Janela de Funcionamento (OpeningHours) não preenchida** | O app aciona o `fallbackOperationalWindow(bars)`, procurando automaticamente picos de "footfall > 0" no dia para deduzir as horas. | 🟢 |
| **MoM / YoY sem base histórica no Ledger** | A fórmula `deltaPct` retorna explícitamente `null` (ao invés de dar Infinity/NaN ou crashar), renderizando "N/A" nos labels. | 🟢 |
| **Fila excessiva estourando o cálculo do Score** | O redutor de pontos por fila possui clamp/truncamento em máximo de -24 pontos, e o score final é truncado com max() impedindo scores < 0. | 🟢 |
| **Endpoint de Ranking inoperante ou indisponível** | O frontend faz o fallback usando dados da query `networkQ`, ordenando a lista localmente usando um peso simples (`conversão × 5`). | 🟢 |
| **Falha de rede ao disparar Intervenção (Copilot Trigger)** | O erro é silenciado internamente e gravado em background como ActionOutcome `"failed"`. A UI mostra um Toast de erro mas não trava. | 🟢 |

## 3. Admin Control Tower

| Caso de Borda (Edge Case) | Comportamento Atual / Fallback | Confiança |
|---------------------------|--------------------------------|-----------|
| **`payload_missing_rate` incompleto ou nulo no Funil** | O cálculo de `dataQuality` suspende as médias e devolve score geral `null` imediatamente se o sub-score da métrica falhar. | 🟢 |
| **Latência alta na API de checagem de permissão** | A tela pausa num estado gracefull "Validando permissões..." (`waitingStatusValidation`), evitando expulsão abrupta de usuários válidos. | 🟢 |
| **Acesso negado localmente pela API mas usuário é Funcionario** | Fallback permissivo de segurança: o domínio `@dalevision.com` no email do auth libera a view (client-side) caso a API perca conexão temporalmente. | 🟢 |
| **Assets da Calibração duplicados ou race conditions** | A função do frontend assume mutações rápidas, limitadas ao hardcode de payload `{ max_actions: 40 }` prevenindo timeout do request. | 🟡 |
