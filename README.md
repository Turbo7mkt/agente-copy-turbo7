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

## Duas formas de operar

**Painel web** — o gestor escolhe cliente e ângulo pela tela, sem abrir o Claude
Code. Ver [`app/README.md`](app/README.md).

```bash
pip install -r app/requirements.txt
export APP_SENHA=uma-senha
uvicorn app.main:app --port 8000
```

Não precisa de chave de API: o painel monta o prompt e você cola no Claude que
já assina. Com `ANTHROPIC_API_KEY` no ambiente, ele também gera sozinho.

Em produção roda na Vercel — passo a passo e as diferenças do serverless em
[`docs/deploy-vercel.md`](docs/deploy-vercel.md).

**Claude Code** — mesma base, mesmas regras, mesmo linter:

```
/sync-drive          puxa material novo do Drive para a base
/briefing Decoralle  converte o diagnóstico do cliente em briefing
/copy Decoralle      gera as copies a partir do briefing
```

### O que acontece quando você chama `/copy`

O agente não sai escrevendo. Ele cumpre 4 passos bloqueantes antes:

1. **Consulta a base** — briefing do cliente, as 7 regras, biblioteca de ângulos,
   formatos, exemplos aprovados e a skill de marca `italinea-identidade-visual`.
2. **Verifica o Drive** — se `ultima_sincronizacao` tem mais de 7 dias, roda
   `sync-drive` antes, sem perguntar. Base velha é o risco, não a sincronização.
3. **Pergunta qual ângulo você quer** — 3 ou 4 opções já filtradas pelo briefing,
   com o recomendado em primeiro e o motivo ancorado nas provas da loja. Ângulo
   que depende de prova ⚠️ ou de campo `null` nem aparece na lista.
4. **Confirma o formato** — 10 completas ou estrutura reduzida.

Já sabe o ângulo? Diga no pedido (`/copy Decoralle ângulo de pós-venda`) e ele
confirma em uma linha em vez de perguntar.

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

E as regras da identidade Italínea, quando o preço é permitido:

| Código | O que pega |
| --- | --- |
| `MARCA-preco-formato` | preço fora do padrão `R$ 34.900` |
| `MARCA-a-partir-de` | "a partir de" grudado no número |
| `MARCA-cta` | CTA fora dos aprovados pela marca |
| `MARCA-rodape` | peça com preço sem rodapé legal |

O linter lê `usa_preco` do briefing irmão automaticamente. Passar nele **não é
aprovação** — o checklist manual (`base-conhecimento/regras/checklist-qa.md`)
cobre o que padrão de texto não alcança.

```bash
python3 scripts/tests/test_lint_copy.py   # 30 testes do linter
python3 app/tests/test_base.py            # 27 do filtro de ângulos
python3 app/tests/test_prompt.py          # 22 da montagem do prompt
```

## Skills que o agente usa

Além das skills deste repo, o agente depende de **`italinea-identidade-visual`**
(skill da conta) como autoridade da marca. O mapa completo — o que é obrigatório,
o que é útil, e o que foi avaliado e descartado — está em
[`docs/skills.md`](docs/skills.md).

## Rotina automática

Uma rotina agendada (`trig_01Max61MfWCS5raH2j7gRfWG`) varre o Drive nos dias
úteis às 8h e ingere o que é novo.

⚠️ Ela ainda precisa do conector do Google Drive habilitado em claude.ai →
Routines. Detalhes e comandos de gestão em
[`docs/rotina-sync.md`](docs/rotina-sync.md).

## Clientes com briefing pronto

| Cliente | `usa_preco` | Ângulos liberados | Estratégia |
| --- | --- | --- | --- |
| DiCasa Italínea | `false` | 14 | Reputação, pós-venda, prazo em dias úteis |
| Mobile Prime Italínea | `true` | 14 | Equipe própria, garantia 5 anos, 60 dias úteis |
| Planeta Italínea | `true` | 13 | Condição de pagamento longa, foco em público B |
| Mhavi Planejados | `true` | 12 | Showroom de arquiteto, custo-benefício |
| Decoralle Planejados | `true` | 12 | Preço por ambiente, showroom em Guarulhos, 5 anos |
| Preemier Decore Italínea | `true` | 11 | Preço por metragem + ser Italínea de fábrica |
| Casa & Cozinha Italínea | `false` | 10 | Marca Italínea; sem prova própria ainda |

O número de ângulos liberados não é arbitrário: sai do filtro determinístico
cruzando a biblioteca com o que cada briefing sustenta. Casa & Cozinha tem 10
porque não existe perfil no Google da unidade, o pós-venda tem reputação ruim e
não há tabela de preço confirmada — o sistema esconde o que a loja não pode
provar, em vez de deixar a copy prometer.

Os playbooks de mídia seguem em `base-conhecimento/MANIFEST.yaml` sob
`pendentes`.
