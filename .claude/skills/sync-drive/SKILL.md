---
name: sync-drive
description: Extrai conhecimento novo e atualizado do Google Drive da Turbo7 e salva na base de conhecimento do repo. Use quando o usuário pedir para sincronizar, atualizar ou puxar materiais do Drive, quando mencionar que subiu documentos novos, ou quando uma rotina agendada disparar a varredura. Também usar antes de gerar copy se a base estiver desatualizada há mais de 7 dias.
---

# Sincronizar base de conhecimento com o Google Drive

Varre o Drive, identifica o que é **novo ou mudou desde a última sincronização**,
e materializa o conteúdo relevante em `base-conhecimento/` e `clientes/`.

Requer as ferramentas MCP do Google Drive (`mcp__Google_Drive__*`). Se não
estiverem disponíveis nesta sessão, pare e avise — não invente conteúdo.

## Passo 1 — Ler o estado atual

Leia `base-conhecimento/MANIFEST.yaml`. Ele guarda:

- `ultima_sincronizacao` — data da última varredura
- `arquivos[]` — cada doc já ingerido, com `drive_id`, `modificado_em` no momento
  da ingestão e o `destino` no repo
- `ignorar[]` — IDs que já foram avaliados e descartados (com motivo), para não
  reavaliar toda vez

## Passo 2 — Varrer o que mudou

Use `mcp__Google_Drive__search_files` com filtro de data a partir de
`ultima_sincronizacao`:

```
modifiedTime > 'AAAA-MM-DDT00:00:00Z' and (
  mimeType = 'application/vnd.google-apps.document' or
  mimeType = 'application/vnd.google-apps.spreadsheet' or
  mimeType = 'application/pdf'
)
```

Pagine com `pageToken` até esgotar. Use `excludeContentSnippets: true` na
varredura — o conteúdo vem depois, só para o que interessa.

Se `ultima_sincronizacao` for nula (primeira execução), varra sem filtro de data
e use `mcp__Google_Drive__list_recent_files` como complemento.

## Passo 3 — Triar

Para cada arquivo retornado, classifique pelo título e pela pasta:

| Sinal no título | Destino | Ação |
| --- | --- | --- |
| `Diagnóstico - <Cliente>` | `clientes/<slug>/briefing.md` | Converter em briefing (ver skill `briefing`) |
| `Copys <Cliente>`, `COPYS <Cliente>` | `base-conhecimento/exemplos/` + `clientes/<slug>/copies/` | Ingerir como referência de tom |
| `Playbook`, `Manual`, `Metodologia`, `Prompt` | `base-conhecimento/metodologia/` ou `playbooks/` | Ingerir integral |
| `Plano_Marketing_<Cliente>`, `Plano de Marketing` | `clientes/<slug>/plano.md` | Ingerir integral |
| Planilha de cliente (`<Cliente> 🚀 Turbo7`) | — | **Ignorar.** São dashboards de métrica, não conhecimento de copy |
| Métricas, Stract, Painel, Central de dados, Leads | — | **Ignorar.** Mesma razão |
| Contrato, Acessos, senhas | — | **Ignorar.** Nunca versionar credencial no repo |
| `Documento sem título` | — | Ignorar, registrando em `ignorar[]` |

Na dúvida sobre um arquivo, **pergunte** antes de ingerir. É melhor deixar de
fora do que poluir a base.

## Passo 4 — Ingerir

Para cada arquivo aprovado na triagem:

1. `mcp__Google_Drive__read_file_content` com o `fileId`.
2. Converta para markdown limpo: remova o escape de colchetes (`\[ \]` → `[ ]`),
   normalize os separadores `═══`, transforme listas de checklist em tabela
   quando fizer sentido.
3. **Sempre** inclua no topo do arquivo gerado a linha de procedência:
   ```
   > Fonte: Google Drive · "<título>" (`<fileId>`) · sincronizado em AAAA-MM-DD
   ```
4. Escreva no destino da tabela acima.

Se o arquivo já existe no repo e mudou no Drive: **não sobrescreva edições
locais em silêncio.** Mostre o diff do que mudou e confirme antes de aplicar.
Arquivos em `clientes/*/briefing.md` costumam ter curadoria manual — esses
sempre pedem confirmação.

## Passo 5 — Atualizar o manifesto

Reescreva `base-conhecimento/MANIFEST.yaml` com:

- `ultima_sincronizacao` = data de hoje
- entrada nova/atualizada para cada arquivo ingerido
- entrada em `ignorar[]` para cada descarte, com o motivo

## Passo 6 — Relatar

Feche com um resumo curto:

```
Sincronizado em AAAA-MM-DD
  novos:        N arquivos → [lista]
  atualizados:  N arquivos → [lista]
  ignorados:    N (motivo agrupado)
  pendências:   [o que precisou de decisão humana]
```

Se nada mudou, diga só isso — não gere ruído.

## Rodando como rotina agendada

A varredura pode rodar sozinha. Ver `docs/rotina-sync.md` para o agendamento
configurado e como alterar a frequência.
