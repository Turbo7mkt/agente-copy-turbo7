# Deploy do painel na Vercel

## Passo a passo

1. **Importe o repositório** em [vercel.com/new](https://vercel.com/new).
   O `vercel.json` já está no repo — não mexa em Build Command nem Output
   Directory, deixe a Vercel detectar.

2. **Defina as variáveis de ambiente** (Settings → Environment Variables):

   | Variável | Valor | Obrigatória |
   | --- | --- | --- |
   | `APP_SENHA` | a senha do painel | **sim, em produção** |
   | `ANTHROPIC_API_KEY` | `sk-ant-...` | **não** — só para geração direta |

   Sem `ANTHROPIC_API_KEY` o painel roda no modo entrega de prompt: monta o
   prompt, você cola no Claude da sua assinatura, e volta para validar. É o modo
   padrão e não custa nada além da hospedagem.

   Sem `APP_SENHA` o painel fica **aberto para qualquer pessoa com a URL**, e
   cada geração é uma chamada paga na sua conta. A tela mostra um alerta
   vermelho enquanto ela não estiver definida.

3. **Deploy.** A URL sai em `https://<projeto>.vercel.app`.

## As três coisas que a Vercel muda no comportamento

### 1. O painel não grava no repositório

Serverless roda com filesystem só-leitura. Localmente, cada geração é salva em
`clientes/<slug>/copies/AAAA-MM-DD-tema.md`; na Vercel, não.

O app detecta isso (`grava_no_repo: false` em `/api/status`) e troca o rótulo
por **Baixar .md**. O gestor baixa e você commita no repo quando quiser manter o
histórico.

Se o histórico versionado for importante no fluxo, a saída é gerar pelo Claude
Code — que grava e commita — e usar o painel só para as entregas avulsas.

### 2. Timeout de função — só afeta a geração direta

No modo entrega de prompt não existe timeout: montar o prompt é leitura de
arquivo, responde em milissegundos. O que segue vale só se você configurar
`ANTHROPIC_API_KEY`.

Uma geração de 10 copies com `claude-opus-5` em `effort: high` leva de 1 a 2
minutos.

| Plano | Teto de `maxDuration` | Serve? |
| --- | --- | --- |
| Hobby | 60 s | **Não** para 10 copies. Serve para formatos curtos (3 vídeos, Dor/Solução/CTA com 1-2 ângulos) |
| Pro | 300 s | Sim |

O `vercel.json` já pede `maxDuration: 300`. **No plano Hobby a Vercel reduz para
60 s em silêncio** — a função é cortada no meio e o painel mostra a saída
parcial. Se você está no Hobby e precisa das 10 copies, gere pelo Claude Code.

A geração é **streaming** justamente por isso: o texto aparece na tela conforme é
escrito, então mesmo um corte deixa o que já saiu aproveitável, e a conexão não
morre por inatividade.

### 3. A skill de identidade da marca não existe em produção

`italinea-identidade-visual` é uma skill da sua conta Claude, instalada na
máquina — ela não é deployada. O prompt cai para as regras equivalentes que estão
versionadas em `base-conhecimento/regras/regras-copy.md`, que já cobrem preço,
rodapé legal e CTA.

O que se perde é o detalhamento de formato do arquivo `ofertas-e-copy.md`. O
linter continua reprovando `MARCA-preco-formato`, `MARCA-rodape` e companhia,
porque essas regras estão no código, não na skill.

Para eliminar a diferença, copie o conteúdo relevante da skill para
`base-conhecimento/regras/identidade-italinea.md` — o código já procura por esse
arquivo como alternativa.

## Custo

Cada clique em "Gerar" é uma chamada paga. Ordem de grandeza por geração de 10
copies, com `claude-opus-5` ($5 entrada / $25 saída por milhão):

- entrada: ~15-20 mil tokens (regras + exemplos + briefing) → ~US$ 0,10
- saída: ~8-12 mil tokens → ~US$ 0,25

Cerca de **US$ 0,35 por geração**, caindo na segunda em diante para o mesmo
cliente: o prompt estável vai com `cache_control: ephemeral` e a leitura de cache
custa ~10% da entrada. A resposta traz `uso.cache_lido` para conferir.

Isso é estimativa por contagem de tokens, não medição — acompanhe o consumo real
no console da Anthropic nos primeiros dias.

## Segurança

`APP_SENHA` é uma senha única compartilhada, verificada com `hmac.compare_digest`
e guardada no `sessionStorage` do navegador. É uma porta, não um sistema de
contas: não dá para revogar acesso de uma pessoa só, nem saber quem gerou o quê.

Para uma equipe maior, troque por Vercel Authentication (Settings → Deployment
Protection), que põe o SSO da Vercel na frente de tudo sem mexer no código.

**O repositório é público.** Como os briefings vão no deploy, qualquer pessoa com
a URL do painel — se `APP_SENHA` não estiver definida — lê análise de
concorrência e posicionamento de preço dos seus clientes.

## Rodando local

```bash
pip install -r app/requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
export APP_SENHA=opcional-em-local
uvicorn app.main:app --reload --port 8000
```

Sem `VERCEL` no ambiente, o app volta a gravar em `clientes/<slug>/copies/`.
