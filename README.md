# Agente de Copy — Turbo7

Sistema de agentes que escreve copy de Meta Ads para as lojas de móveis
planejados da carteira Italínea, usando a base de conhecimento da agência
(diagnósticos, playbooks e copies aprovadas) como fonte — não a memória do modelo.

## O problema que resolve

Copy de planejados quebra sempre pelos mesmos três motivos: prova inventada
("nota 5,0" numa loja que não tem), diferencial herdado do cliente vizinho
("35 dias úteis" numa loja que nunca prometeu isso) e ângulo genérico que fala
com todo mundo e converte ninguém.

O sistema fecha os três: **toda prova precisa estar no briefing, todo briefing
precisa vir de um diagnóstico, e todo ângulo precisa ser distinto dos outros nove.**

## Como funciona

```
┌─────────────┐   sync-drive   ┌───────────────────┐
│ Google Drive│ ─────────────► │ base-conhecimento │  regras, metodologia,
│  (fonte)    │                │                   │  templates, exemplos
└─────────────┘                └─────────┬─────────┘
                                         │
      Diagnóstico 360°   briefing        ▼
      do cliente     ──────────►  clientes/<slug>/briefing.md
                                         │
                                    copy │
                                         ▼
                              clientes/<slug>/copies/*.md
                                         │
                              lint_copy.py + revisor-copy
                                         ▼
                                    entrega ao cliente
```

## Uso

```
/sync-drive          puxa material novo do Drive para a base
/briefing Decoralle  converte o diagnóstico do cliente em briefing
/copy Decoralle      gera as 10 copies a partir do briefing
```

Depois de gerar, valide:

```bash
python3 scripts/lint_copy.py clientes/decoralle/copies/2026-08-27-fundo-funil.md
```

E peça a revisão adversarial ao subagente `revisor-copy` antes de entregar.

## Formato padrão de entrega

10 ângulos psicológicos distintos: **7 vídeo, 2 imagem estática, 1 carrossel**.
Os 7 vídeos seguem 5 blocos — Gancho, Clareza e Emoção variam por ângulo; Prova e
CTA são escritos uma vez e repetidos. Detalhe em
`base-conhecimento/regras/formatos-entrega.md`.

Outra estrutura serve também (`Dor/benefício → Solução → CTA`, "4 vídeos + 1
foto") — as regras de copy valem igual, só o invólucro muda.

## As regras que o linter cobre

`scripts/lint_copy.py` reprova por padrão de texto:

| Código | O que pega |
| --- | --- |
| `R2-urgencia` | "últimas vagas", "corre", "por tempo limitado" |
| `R2-superlativo` | "o melhor", "excelência", "qualidade incomparável" |
| `R2-exclamacao` | exclamação em série |
| `R2-emoji` | mais de um emoji por linha |
| `R7-cliche` | "realize o sonho", "a casa dos seus sonhos", "você merece" |
| `PRECO` | preço, parcela ou desconto em cliente com `usa_preco: false` |

O linter lê `usa_preco` do briefing irmão automaticamente. Passar nele **não é
aprovação** — o checklist manual (`base-conhecimento/regras/checklist-qa.md`)
cobre o que padrão de texto não alcança.

```bash
python3 scripts/tests/test_lint_copy.py   # 18 testes
```

## Rotina automática

Uma rotina agendada varre o Drive nos dias úteis e ingere o que é novo.
Configuração e como alterar: [`docs/rotina-sync.md`](docs/rotina-sync.md).

## Clientes com briefing pronto

| Cliente | Praça | `usa_preco` | Estratégia |
| --- | --- | --- | --- |
| DiCasa Italínea | Porto Alegre (Moinhos, Higienópolis) | `false` | Reputação, pós-venda, prazo em dias úteis |
| Preemier Decore Italínea | Itaquera / ZL São Paulo | `true` | Preço fechado por metragem + ser Italínea de fábrica |

Os demais diagnósticos do Drive estão mapeados em
`base-conhecimento/MANIFEST.yaml` sob `pendentes`.
