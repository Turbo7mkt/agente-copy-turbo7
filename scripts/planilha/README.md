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

## O que a linha carrega

Vai para a aba `BASE_CRIATIVOS`, no fim:

| Coluna | Vem de |
| --- | --- |
| `Cliente` | o nome que a planilha já usa (escolhido no passo 07, lembrado por cliente) |
| `Gestor`, `Responsável`, `Tipo de Criativo` | a configuração do passo 07 |
| `Data Solicitação` | hoje, no fuso da planilha |
| `Copy` | o markdown inteiro, com cabeçalho de ângulo e procedência |
| `Status` | `Copy em Aprovação` se passou no linter, `Em Revisão` se não |
| `ID do Criativo` | próximo da sequência **daquele cliente** (`AI0004` → `AI0005`) |
| `Observações` | que veio do painel e qual foi o veredito do linter |
| `Dias em Aberto`, `Dias Em Atraso` | fórmula herdada da linha de cima |

O `ID do Criativo` é gerado com trava (`LockService`), então duas abas do painel
gravando ao mesmo tempo não pegam o mesmo número.

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
node scripts/tests/test_gravar_copy.mjs
```

14 testes da geração de `ID do Criativo`, contra os IDs que existem hoje na
planilha — incluindo `DP 0013` com espaço e o nome `DIANA PLANEJADOS  ITALÍNEA`
com espaço duplo.

A ligação painel → script foi exercitada num Chromium de verdade contra um
dublê do Web App: configuração, *Testar conexão*, correção do nome do cliente,
POST, e a checagem de que o token **não** aparece no HTML da página.
