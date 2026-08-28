# Painel do agente de copy

Front end web onde o gestor escolhe o cliente, escolhe o ângulo e recebe as
copies — sem abrir o Claude Code.

## Dois modos, e o padrão não custa nada

O painel funciona **sem chave de API**. Esse é o modo padrão.

**Modo entrega de prompt (sem chave).** O painel cumpre os passos 1 a 3 — lê a
base, checa o frescor do Drive, filtra os ângulos pelo briefing — e monta o
prompt completo. Você copia, cola no Claude que já assina (app, claude.ai ou
Claude Code), e traz a resposta de volta para o campo de validação, onde ela
passa pelo mesmo linter da geração automática.

**Modo geração direta (com chave).** Se `ANTHROPIC_API_KEY` existir no ambiente,
aparece também o botão "Gerar aqui mesmo" e o painel escreve sozinho, em
streaming. Sem a chave, esse botão nem é renderizado.

A diferença é só quem executa a escrita. O protocolo, o filtro e a validação são
idênticos nos dois.

## Subir local

```bash
pip install -r app/requirements.txt
export APP_SENHA=opcional-em-local
export ANTHROPIC_API_KEY=sk-ant-...        # opcional — libera a geração direta
uvicorn app.main:app --reload --port 8000
```

Abra <http://localhost:8000>.

## Deploy

Vercel, com `vercel.json` e `api/index.py` já no repo. Três diferenças de
comportamento em serverless — filesystem só-leitura, timeout de função e a skill
de marca ausente — estão em [`../docs/deploy-vercel.md`](../docs/deploy-vercel.md).

**`APP_SENHA` é obrigatória em produção.** Sem ela o painel fica aberto a quem
tiver a URL, e cada geração é uma chamada paga.

## A decisão de arquitetura que importa

**O protocolo dos 4 passos é cumprido em código, não pelo modelo.**

Se o app apenas mandasse "escreva copies para o cliente X" para a Claude, todo o
sistema viraria decoração: o modelo escolheria o ângulo sozinho e a prova
contestada voltaria para dentro do anúncio. Então a divisão é:

| Passo | Quem executa | Onde |
| --- | --- | --- |
| 1. Consultar a base | Código | `core/base.py` lê briefing, regras, exemplos |
| 2. Verificar o Drive | Código | `checar_frescor()` compara `MANIFEST.yaml` com hoje |
| 3. Filtrar e perguntar o ângulo | Código + gestor | `filtrar_angulos()` decide o que pode ser oferecido; o gestor clica |
| 4. Escrever | Modelo | recebe briefing, regras e **os ângulos já escolhidos** |
| 5. Validar | Código | o mesmo `scripts/lint_copy.py` da linha de comando |

O modelo escreve. Ele não decide o que é prova válida nem qual ângulo usar.

## O filtro de ângulos

`base-conhecimento/regras/angulos.md` tem uma coluna **Requer** legível por
máquina. O servidor cruza esses tokens com o briefing:

| Token | Some quando |
| --- | --- |
| `prova:google` | a nota está marcada com ⚠️ no briefing, ou nenhuma unidade tem nota |
| `campo:prazo_entrega` | o campo é `null` |
| `campo:garantia` | o campo é `null` |
| `preco` | o cliente é `usa_preco: false` |

Efeito real na carteira hoje:

- **DiCasa** — 14 ângulos disponíveis, 1 bloqueado (preço).
- **Preemier** — 11 disponíveis, 4 bloqueados: prova social (perfis do Google
  divididos), dois de prazo e um de garantia (campos não confirmados).

O painel mostra os bloqueados numa seção recolhida, **com o motivo**. O gestor vê
o que falta no briefing em vez de descobrir depois que a copy prometeu algo que
a loja não sustenta. E a trava é do servidor, não da tela: um POST direto em
`/api/gerar` com ângulo bloqueado recebe 422.

## Endpoints

| Método | Rota | Para quê |
| --- | --- | --- |
| GET | `/api/status` | frescor da base + se há credencial no ambiente |
| GET | `/api/clientes` | lojas com briefing |
| GET | `/api/clientes/{slug}` | resumo do briefing, restrições, alertas |
| GET | `/api/clientes/{slug}/angulos` | disponíveis + bloqueados com motivo |
| GET | `/api/clientes/{slug}/copies/{arquivo}` | histórico de entregas |
| POST | `/api/gerar` | gera, valida no linter e grava em `clientes/<slug>/copies/` |

## Modelo e custo

`claude-opus-5`, thinking adaptativo, `effort: high`, streaming (a saída de 10
copies é longa e passaria do timeout sem stream).

O prompt estável — regras, formatos, exemplos e briefing — vai com
`cache_control: ephemeral`. Da segunda geração em diante para o mesmo cliente, a
maior parte da entrada é lida do cache. A resposta traz `uso.cache_lido` para
você conferir que o cache está sendo aproveitado.

Cada geração é uma chamada paga. O painel não tem autenticação: **não exponha na
internet aberta** sem colocar login na frente.

## Testes

```bash
python3 app/tests/test_base.py     # 27 testes do filtro, briefing e frescor
```

Cobrem o que quebra silenciosamente: campo `null` tratado como confirmado, ⚠️
não detectado, ângulo de preço vazando para cliente sem preço, e a regressão do
Preemier (a prova social precisa continuar bloqueada).
