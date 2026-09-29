# Turbo7 Meta Ads MCP

Servidor MCP da Turbo7 para Meta Ads. **Versão 0.2: somente leitura.**

## Ferramentas
| Ferramenta | O que faz |
|---|---|
| `listar_contas` | Contas de anúncio acessíveis pelo BM da Turbo7, com status, moeda e fuso |
| `desempenho_conta` | Métricas de um cliente por conta, campanha, conjunto ou anúncio |
| `resumo_carteira` | Todas as contas ativas no período, do pior CPL para o melhor, com semáforo |
| `diagnostico_cliente` | O que mudou contra o período anterior (CPL, CPM, CTR, frequência), anúncios que gastaram sem lead e conjuntos em aprendizado limitado |

As contas são descobertas automaticamente pelo token (`/me/adaccounts`). O cliente pode ser chamado pelo nome ("bs grajau"), sem acento e sem ID.

## Estrutura
```
app/mcp/[chave]/route.ts   Porta de entrada: valida a chave secreta da URL
lib/mcp/server.ts          Ferramentas (orquestração, sem regra de negócio)
lib/regras/                Cálculo de leads, CPL, semáforo e períodos
lib/meta/                  Único ponto de contato com a Meta (paginação, retry, erros)
config/turbo7.ts           Regras editáveis: definição de lead, benchmarks e limiares do diagnóstico
tests/                     Vitest com a Meta simulada
```

## Variáveis de ambiente (Vercel → Settings → Environment Variables)
- `META_ACCESS_TOKEN`: token do usuário do sistema "MCP Turbo7 (leitura)", só `ads_read`
- `META_API_VERSION`: `v25.0`
- `MCP_ACCESS_KEY`: chave aleatória com 32+ caracteres (gere em um gerador de senhas)

## Conectar no Claude
URL do conector personalizado: `https://<projeto>.vercel.app/mcp/<MCP_ACCESS_KEY>`

A URL é a senha: não compartilhe. Na Fase 2 (time), troca-se por login OAuth.

## Regras importantes
- Leads = conversas iniciadas por mensagem + `lead` (formulário/site). Ajuste por conta em `config/turbo7.ts`.
- Atribuição: `use_unified_attribution_setting=true`, igual ao Gerenciador de Anúncios.
- Dados dos últimos 1 a 3 dias ainda podem mudar.
- Nenhuma ferramenta escreve na Meta nem lê dados pessoais de leads.

## Desenvolvimento
`npm install` → `npm run typecheck` → `npm test` → `npm run build`

Os testes nunca chamam a Meta: `tests/apoio/metaSimulada.ts` troca o `fetch` por respostas no formato da Graph API, e `tests/apoio/mcp.ts` chama as ferramentas pelo protocolo MCP, como o Claude faria.
