# Ligar o painel à planilha `Criativos Turbo7`

O painel roda no **navegador do gestor**, não no container do agente. Então ele
fala direto com o Google: não precisa de conector do Drive, não precisa de
rotina, e não depende de nenhuma sessão estar aberta.

O que falta é um endereço para onde mandar a linha. É isso que o
`gravar-copy.gs` cria.

## Instalação — uma vez, ~5 minutos

1. Abra a planilha **Criativos Turbo7** → *Extensões* → *Apps Script*.
2. Apague o `function myFunction() {}` que vem de fábrica e cole o conteúdo
   inteiro de [`gravar-copy.gs`](gravar-copy.gs).
3. Salve. Dê um nome ao projeto, por exemplo `Painel de Copy Turbo7`.
4. No seletor de função, escolha **`configurarToken`** e clique *Executar*.
   Na primeira vez o Google pede autorização — aceite.
   Abra *Registro de execução* e **copie o token** que aparece lá.
5. *Implantar* → *Nova implantação* → tipo **App da Web**:
   - *Executar como:* **Eu**
   - *Quem tem acesso:* **Qualquer pessoa**
6. Copie a **URL do app da Web** (termina em `/exec`).
7. No painel, passo **07 Planilha**: cole a URL e o token, preencha gestor e
   responsável, clique *Testar conexão*. O selo deve virar
   `ligada — N clientes na planilha`.

Pronto. Marque *"Gravar sozinho quando a copy passar no linter"* e a copy limpa
entra na planilha sem mais nenhum clique.

## Por que "Qualquer pessoa" não entrega a planilha a qualquer um

*Quem tem acesso: Qualquer pessoa* significa que o endereço aceita requisição
sem login do Google — é o que permite o painel falar com ele. A porta é o
**token**, e ele:

- não está neste repositório;
- não está no HTML do painel publicado;
- vive em *Propriedades do Script* do lado do Google e no `localStorage` do
  navegador de quem configurou do lado do painel.

Quem abrir o link do painel **não recebe o token junto**. Cada pessoa que for
usar configura o seu, uma vez, no próprio navegador.

Se um token vazar: rode `configurarToken` de novo. O antigo para de funcionar
na hora, e é só reconfigurar o painel.

## Uma linha por criativo, não por entrega

Uma entrega de 10 copies são **10 criativos**, e a `BASE_CRIATIVOS` é uma linha
por criativo, com um `ID do Criativo` cada. Gravar tudo numa linha só jogava
fora a unidade que a planilha usa para medir SLA e, mais tarde, atribuição.

O painel corta a entrega no **cabeçalho mais fundo que aparece**: dez
`## ÂNGULO 1..10` viram dez peças; um `## ÂNGULO` com quatro `### Vídeo 1..4`
vira as quatro peças de dentro. O tipo sai do que o texto diz ser — "carrossel"
e "cards" antes de "vídeo", porque um card pode citar vídeo e o contrário não
acontece.

Fatiar texto de modelo nunca acerta sempre. Por isso o resultado aparece numa
**prévia no passo 05**, com o tipo editável por linha e um ✕ para tirar o que
não é criativo. O gestor confere antes de gravar.

## O que cada coluna carrega

| Coluna | Vem de |
| --- | --- |
| `Cliente` | o nome que a planilha já usa (passo 07, lembrado por cliente) |
| `Gestor` | **o briefing da loja** — Mobile Prime é do Davi, as outras da Micheli. A configuração do painel só entra quando o briefing não diz |
| `Responsável` | a configuração do passo 07 |
| `Data Solicitação` | hoje, no fuso da planilha |
| `Para ser Entregue Em` | Data Solicitação + o SLA do passo 07, em **dias úteis** (padrão 3) |
| `Tipo de Criativo` | deduzido do texto da peça, corrigível na prévia |
| `Copy` | o texto daquela peça, não a entrega inteira |
| `Status` | `Copy em Aprovação` se passou no linter, `Em Revisão` se não |
| `ID do Criativo` | sequência **daquele cliente**, um por peça (`AI0005`, `AI0006`, …) |
| `Observações` | que veio do painel e qual foi o veredito do linter |
| `Dias em Aberto`, `Dias Em Atraso` | fórmula herdada da linha de cima |
| `Entregue Em`, `Quem Gravou o audio` | em branco — quem preenche é a produção |

Os IDs do lote inteiro saem sob uma trava só (`LockService`), então duas abas
do painel gravando ao mesmo tempo não colidem no meio da sequência.

Cliente que ainda não tem linha nenhuma ganha prefixo pelas iniciais
(`CASA & COZINHA ITALÍNEA` → `CCI0001`).

## O passo que vale mais e não é software

O `ID do Criativo` só fecha o loop se o **anúncio no Meta carregar esse ID**.
Hoje a planilha diz `AI0004` e o Meta diz `AD 04 PIC` — não cruzam, e por isso
ninguém sabe qual copy trouxe lead.

Nomeando o anúncio como `AI0005 | fundo-funil | video`, o `ad_name` das
planilhas `<Cliente> 🚀 Turbo7` vira chave estrangeira e o cruzamento entre
copy e resultado passa a sair sozinho. Ver
[`docs/gravar-no-drive.md`](../../docs/gravar-no-drive.md).

## Testes

```bash
node scripts/tests/test_gravar_copy.mjs    # 22 — IDs, lote, SLA em dias úteis
node scripts/tests/test_fatiar_entrega.mjs # 13 — corte em peças e tipo
```

Os IDs são testados contra os que existem hoje na planilha, incluindo
`DP 0013` com espaço e o nome `DIANA PLANEJADOS  ITALÍNEA` com espaço duplo.
O corte em peças é testado contra a distribuição de `formatos-entrega.md`:
10 copies saem como 7 vídeo, 2 foto e 1 carrossel.

A ligação painel → script foi exercitada num Chromium de verdade contra um
dublê do Web App: configuração, *Testar conexão*, correção do nome do cliente,
corte de uma entrega de 10 copies em 10 peças (7 vídeo · 2 foto · 1 carrossel),
POST do lote com 10 IDs sequenciais, e a checagem de que o token **não**
aparece no HTML da página.
