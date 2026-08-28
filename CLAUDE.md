# agente-copy-turbo7

Sistema de agentes de copy da **Turbo7** — agência de marketing para lojas de
móveis planejados da rede Italínea.

## O que este repo é

A base de conhecimento da agência, versionada, mais as skills que a consomem.
O fluxo é sempre o mesmo:

```
Google Drive  →  base-conhecimento/  →  clientes/<slug>/briefing.md  →  copies
  (fonte)         sync-drive              briefing                       copy
```

## Regra número um

**Nenhuma copy sai sem briefing.** O briefing é o que impede o agente de inventar
nota do Google, prazo de entrega ou garantia. Se `clientes/<slug>/briefing.md`
não existe, rode a skill `briefing` antes de escrever qualquer linha.

Prova sem origem rastreável não entra em anúncio.

## As outras duas regras que bloqueiam

**Consultar a base e o Drive antes de gerar — sempre.** Ler o briefing, as regras
e os exemplos não é opcional, mesmo que o agente ache que já sabe o conteúdo.
E a base local é retrato do Drive: se `ultima_sincronizacao` no
`base-conhecimento/MANIFEST.yaml` tem mais de 7 dias, rode `sync-drive` **antes**
de escrever. Não pergunte se pode — a base velha é o risco, não a sincronização.

**Perguntar o ângulo antes de escrever — sempre.** O agente não escolhe o ângulo
sozinho. Quem sabe qual é a campanha, a data e o que já está no ar é o gestor.
A pergunta oferece 3 ou 4 ângulos **já filtrados pelo briefing** (fora os que
dependem de prova ⚠️, de campo `null` ou que violam uma restrição), com o
recomendado em primeiro e o motivo ancorado no briefing. Se o usuário já disse o
ângulo no pedido, confirme em uma linha e siga.

O protocolo completo, com os 4 passos bloqueantes, está em
`.claude/skills/copy/SKILL.md`.

## Skills

| Skill | Quando usar |
| --- | --- |
| `sync-drive` | Puxar material novo/atualizado do Google Drive para a base |
| `briefing` | Converter um Diagnóstico 360° em briefing estruturado de cliente |
| `copy` | Gerar as copies a partir do briefing + regras |
| `find-skills` | Descobrir e instalar skills do ecossistema aberto |

Subagente `revisor-copy`: auditoria adversarial antes de entregar ao cliente.

### Dependência externa obrigatória

**`italinea-identidade-visual`** (skill da conta, não deste repo) é a autoridade
da marca: formato de preço, rodapé legal, CTAs aprovados, tom da rede, gabaritos
e fontes. A skill `copy` a invoca sempre.

Precedência: divergiu em **forma** (como escrever preço, que CTA usar), a marca
vence; divergiu em **fato** (prazo desta loja, nota dela), o briefing vence — a
marca não conhece a loja.

Mapa completo de skills, incluindo o que foi avaliado e descartado:
[`docs/skills.md`](docs/skills.md).

## Estrutura

```
base-conhecimento/
  MANIFEST.yaml          mapa do que veio do Drive, o que falta, o que ignorar
  regras/                as 7 regras, ângulos, formatos de entrega, checklist QA
  metodologia/           os 7 pilares da Turbo7
  templates/             diagnóstico 360°, briefing de cliente
  exemplos/              copies aprovadas — calibragem de tom
  playbooks/             playbooks de mídia (pendentes de ingestão)
clientes/
  _TEMPLATE/             briefing em branco
  <slug>/briefing.md     o contrato entre diagnóstico e copy
  <slug>/copies/         entregas, uma por data
scripts/
  lint_copy.py           verificação determinística das regras
  tests/                 18 testes do linter
```

## Comandos

```bash
# validar uma copy
python3 scripts/lint_copy.py clientes/<slug>/copies/<arquivo>.md

# validar tudo
python3 scripts/lint_copy.py clientes/*/copies/*.md

# testes do linter
python3 scripts/tests/test_lint_copy.py
```

## Convenções

- **Português brasileiro** em tudo: código, comentários, documentação e commits.
- `slug` de cliente: minúsculas, sem acento, hífen. `Preemier Decore Italínea` →
  `preemier-decore-italinea`.
- Arquivo de copy: `clientes/<slug>/copies/AAAA-MM-DD-<tema>.md`.
- Todo arquivo vindo do Drive carrega a linha de procedência no topo:
  `> Fonte: Google Drive · "<título>" (\`<fileId>\`) · sincronizado em AAAA-MM-DD`
- **Nunca versionar credencial.** Documentos de acesso do Drive ficam de fora,
  por triagem explícita no `MANIFEST.yaml`.

## O detalhe que muda tudo: `usa_preco`

Cada cliente decide se a copy fala de preço, e isso vem do diagnóstico:

- `usa_preco: false` — padrão da carteira. Disputa por pós-venda, reputação,
  prazo e garantia. Ex.: DiCasa Italínea.
- `usa_preco: true` — praça de ticket menor onde o público decide por valor.
  Ex.: Preemier Decore Italínea (Itaquera).

O linter lê esse campo do briefing irmão e ajusta o que reprova.
