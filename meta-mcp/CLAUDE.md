# Plano do MCP Meta Ads da Turbo7

> Documento-mestre do projeto. O Claude Code lê este arquivo no início de cada sessão.
> Atualize a seção "Status" ao concluir cada etapa.

## 1. Contexto

A Turbo7 é uma agência de performance (Taubaté, SP) especializada em lojas de móveis planejados, principalmente franqueados Italínea. Tem cerca de 20 clientes ativos e todas as contas de anúncio chegam ao Business Manager (BM) da Turbo7 como parceiro.

**Objetivo:** um servidor MCP próprio que conecta o Claude às contas Meta Ads dos clientes, para analisar a carteira inteira por conversa, aplicar os benchmarks de funil da Turbo7 e, no futuro, operar campanhas com segurança.

**Por que próprio, e não o MCP oficial da Meta:** o oficial (lançado em abril de 2026) ainda está em beta, com liberação gradual, sem visão consolidada de carteira e sem as regras da Turbo7. Queremos algo consolidado e sob nosso controle.

## 2. Decisões tomadas

| Tema | Decisão |
|---|---|
| Linguagem e framework | TypeScript + Next.js (App Router) |
| Biblioteca MCP | `mcp-handler` 2.x + `@modelcontextprotocol/server` 2.x + Zod 4 |
| Hospedagem | Vercel (Node.js 20+, Fluid compute) |
| Acesso à Meta | Usuário do sistema do BM da Turbo7, token só `ads_read` na fase de leitura |
| Versão da API | Graph API fixada em `v25.0` (variável `META_API_VERSION`) |
| Dados de campanha | Não são armazenados; são buscados na Meta a cada consulta |
| Lead | Conversas iniciadas por mensagem + `lead` (formulário/site); nunca somar `offsite_conversion.fb_pixel_lead` junto com `lead` |
| Atribuição | `use_unified_attribution_setting=true` (igual ao Gerenciador de Anúncios) |
| Segurança fase privada | Chave secreta na URL (`/mcp/<MCP_ACCESS_KEY>`) |
| Segurança fase equipe | Login OAuth por usuário via `withMcpAuth` |
| Idioma | Código com nomes em português; mensagens de erro em português e acionáveis |

## 3. Arquitetura

```
Claude (claude.ai / Desktop / Code)
        │  MCP (Streamable HTTP)
        ▼
app/mcp/[chave]/route.ts   Porta de entrada: valida a chave e repassa ao handler
lib/mcp/server.ts          Ferramentas: validam parâmetros e orquestram (sem regra de negócio)
lib/regras/                Regras Turbo7: leads, CPL, semáforo, períodos (funções puras, testáveis)
lib/meta/                  Único ponto de contato com a Meta: auth, paginação, retry, erros
config/turbo7.ts           Regras editáveis: lead por conta, benchmarks, apelidos
        │
        ▼
Meta Graph API (v25.0)
```

Regra de dependência: cada camada só chama a de baixo. Se a Meta mudar a API, só `lib/meta/` muda.

## 4. Fases

### Fase 0 — Descoberta e decisões ✅ CONCLUÍDA
- Pesquisa do MCP oficial da Meta e de alternativas open source.
- Decisão de construir o MCP próprio, stack, arquitetura em camadas e riscos mapeados.

### Fase 1 — Pré-requisitos na Meta ⏳ EM ANDAMENTO (responsável: Erick)
Roda em paralelo ao desenvolvimento.
- [ ] Criar app do tipo Business no Meta for Developers e adicionar o produto Marketing API.
- [ ] No BM da Turbo7, criar o usuário do sistema "MCP Turbo7 (leitura)".
- [ ] Conferir se as ~20 contas estão em *Contas de anúncios* do BM da Turbo7 (como parceiro). Contas com acesso só por perfil pessoal devem ser solicitadas pelo BM.
- [ ] Atribuir o usuário do sistema a cada conta com permissão de ver desempenho.
- [ ] Gerar o token com `ads_read` (sem `ads_management`).
- [ ] Verificação da empresa na Central de Segurança do BM.
- [ ] Após volume mínimo de chamadas (exigência exibida no painel do app), pedir o **Full Access** do Marketing API Access Tier via App Review.

### Fase 2 — MVP somente leitura (v0.1) ✅ CÓDIGO PRONTO
- [x] Projeto Next.js + `mcp-handler`, compila e passa no teste de protocolo (initialize, tools/list, tools/call).
- [x] `listar_contas`: descobre as contas pelo token (`/me/adaccounts`), com status, moeda e fuso; cache de 10 min.
- [x] `desempenho_conta`: métricas por conta, campanha, conjunto ou anúncio; cliente chamado pelo nome.
- [x] `resumo_carteira`: todas as contas ativas, do pior para o melhor CPL, com totais, contas sem gasto e erros à parte.
- [x] Chave secreta na URL, erros traduzidos, retry com backoff, paginação, aviso de dados recentes.

### Fase 3 — Deploy privado e validação dos dados ⬅️ PRÓXIMA
- [ ] Repositório Git privado (GitHub) com o projeto.
- [ ] Projeto no Vercel ligado ao repositório.
- [ ] Variáveis de ambiente no painel do Vercel (feitas pelo Erick, nunca pelo chat): `META_ACCESS_TOKEN`, `META_API_VERSION`, `MCP_ACCESS_KEY`.
- [ ] Deployment Protection desligada neste projeto (a chave da URL faz a proteção).
- [ ] Adicionar como conector personalizado no Claude do Erick.
- [ ] **Validação:** em 3 clientes, comparar gasto, leads e CPL com o Gerenciador de Anúncios no mesmo período. Diferença aceitável: zero em gasto, até 2% em leads.
- [ ] Ajustar `leadActions` por conta onde a definição de lead for diferente.
- [ ] Conferir fuso e moeda de todas as contas.

**Pronto quando:** o Erick consegue perguntar "como está a carteira nos últimos 7 dias?" no claude.ai e os números batem com o Gerenciador.

### Fase 4 — Regras Turbo7 e ferramentas completas (v0.2 a v0.3)
- [ ] Benchmarks de CPL (padrão e por cliente) em `config/turbo7.ts`, ativando o semáforo.
- [ ] Config por cliente: apelidos, gestor responsável, orçamento mensal, lead actions.
- [ ] `diagnostico_cliente`: compara com o período anterior equivalente e aponta variações relevantes de CPL, CPM, CTR e frequência; anúncios com gasto e sem lead; conjuntos em aprendizado limitado.
- [ ] `top_anuncios`: melhores e piores anúncios por CPL ou gasto, com nome, texto e link de pré-visualização do criativo.
- [ ] `gasto_vs_orcamento`: gasto do mês por cliente e ritmo projetado até o fim do mês.
- [ ] `comparar_periodos`: dois períodos lado a lado para um cliente ou para a carteira.
- [ ] Testes automatizados (Vitest) com respostas simuladas da Meta, sem chamar a API.
- [ ] Relatórios assíncronos de insights para períodos longos.
- [ ] Respostas sempre enxutas (resumo + top N; detalhe só sob pedido).

### Fase 5 — Abertura para a equipe (v1.0)
- [ ] Trocar a chave na URL por login OAuth (`withMcpAuth`), um login por colaborador.
- [ ] Filtro de carteira por gestor (cada gestor vê primeiro os próprios clientes).
- [ ] Registro de consultas (quem, qual ferramenta, quando), sem token nem dados sensíveis.
- [ ] Monitoramento de erros e alerta quando o token expirar ou a Meta recusar chamadas.
- [ ] Manual curto de uso para o time de tráfego.

### Fase 6 — Funil completo
- [ ] Integrar CRM (TurboGO/WeSales) e a planilha consolidada para calcular CPQ, CPAG e CAC reais.
- [ ] Alinhar a regra de cálculo com o dashboard oficial para os dois nunca divergirem.

### Fase 7 — Ações de escrita (opcional)
- [ ] Usuário do sistema separado, com `ads_management`, e token separado.
- [ ] Ferramentas: pausar/ativar, ajustar orçamento, duplicar conjunto.
- [ ] Confirmação explícita antes de executar (elicitação do MCP), com simulação prévia do efeito.
- [ ] Limites de segurança (ex.: variação máxima de orçamento por ação) e auditoria de cada ação.

### Contínuo — Manutenção
- Um responsável pelo projeto no time de TI.
- Revisão trimestral do changelog da Meta; atualizar `META_API_VERSION` antes da versão atual expirar.
- Revalidar números com o Gerenciador após cada mudança relevante da Meta.

## 5. Riscos e cuidados

| Risco | Como tratamos |
|---|---|
| App sem Full Access | Operar no Limited Access até o volume mínimo; pedir revisão cedo |
| Números errados sem aviso (janelas de atribuição removidas em jan/2026 retornam vazio) | Usar só janelas válidas e validar com o Gerenciador |
| Dados recentes mudam (atribuição atrasada) | Aviso automático em períodos que incluem os últimos 3 dias |
| Limites de histórico (13 meses para breakdowns únicos/por hora, 6 para frequência) | Não oferecer comparativos além desses limites |
| Token é a chave de 20 contas | Só leitura agora; token só nas variáveis do Vercel; token de escrita separado na Fase 7 |
| Texto vindo da Meta usado para manipular o Claude | Instruções do servidor mandam tratar nomes e textos como dados |
| Dados pessoais (LGPD) | Nunca buscar conteúdo de formulários de lead; validar cláusula de uso de IA nos contratos com o jurídico |
| Respostas grandes demais | Resumo + top N em todas as ferramentas |
| Divergência com o dashboard | Definir o dashboard como número oficial para o cliente, ou alinhar a regra (Fase 6) |
| Versões da API aposentadas | Versão fixada e revisão trimestral |

## 6. Convenções de código

- TypeScript estrito; `npm run typecheck` e `npm run build` precisam passar antes de qualquer commit.
- Uma responsabilidade por arquivo; ferramentas novas seguem o padrão de `lib/mcp/server.ts` (considerar mover para `lib/mcp/tools/` quando passar de 5 ferramentas).
- Toda ferramenta: `annotations.readOnlyHint = true` enquanto for leitura; descrição clara em português; parâmetros com `.describe()`.
- Erros sempre via `MetaApiError` com mensagem em português que diga o que fazer.
- Nunca logar, imprimir ou commitar tokens. `.env*` fica no `.gitignore`.
- Nenhuma chamada POST/DELETE à Meta até a Fase 7.
- Ambiente do Erick: Windows. Comandos e instruções devem funcionar no PowerShell.

## 7. Status

- Versão atual: **0.1.0** (Fase 2 concluída; Fase 3 é a próxima)
- Pendências do Erick: itens da Fase 1; faixas de CPL para o semáforo.
