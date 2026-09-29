# Gravar a copy no Google — o que dá, o que não dá, e o que vale mais

> Investigação de 29/09/2026, a partir do pedido "gerou a copy mas não salvou na
> planilha". Nenhum dado de lead (nome, e-mail, telefone) entra neste arquivo.

## 1. Qual é "a planilha"

**`Criativos Turbo7`** — `1fO-y_2wk8CpledUoRde6KEU2AeUvP32-fl3xj_Zype0`

É o pipeline de produção de criativo da agência, não um dashboard. A aba que
importa é **`BASE_CRIATIVOS`** (A1:N9923):

```
Cliente · Gestor · Data Solicitação · Para ser Entregue Em · Responsável ·
Tipo de Criativo · Copy · Status · Entregue Em · Dias em Aberto ·
Dias Em Atraso · ID do Criativo · Quem Gravou o audio · Observações
```

A copy vai na **coluna G**. O `Status` percorre
`A Fazer → Em Produção → Em Revisão → Copy em Aprovação → Aprovado → Entregue`.
O `ID do Criativo` é prefixo do cliente + sequência: `AI0001` (Atlântica),
`CI0001` (Camminare), `MEI0001` (Maison Ettuali), `DP0013`, `ND0012`.

Outras abas: `ANÁLISE PENDÊNCIAS` (8 criativos em "Copy em Aprovação" hoje),
`CONTEÚDOS` (pasta de material bruto por cliente), `HISTÓRICO_CLIENTES`
(ativos × encerrados), `PAINEL_CONTROLE`, `BASE_CRIATIVOS_MODELO`,
`BASE_CRIATIVOS_(antiga)`.

## 2. 🔴 Nenhuma ferramenta desta sessão consegue escrever nessa planilha

Foi verificado, não suposto:

| Ferramenta | O que faz | Serve? |
| --- | --- | --- |
| `mcp__Google_Drive__create_file` | Cria arquivo novo (Doc, Planilha, Pasta) com conteúdo | Só para arquivo **novo** |
| `mcp__Google_Drive__update_file` | **Só `title` e `parentId`** | Não escreve conteúdo |
| `mcp__Google_Drive__copy_file` / `share_file` / `trash_file` | Metadados e cópia | Não |
| Windsor.ai `execute_action` | Escrita só em Meta/Google/TikTok/LinkedIn/Bing Ads, Instagram, GBP, Klaviyo, Amazon | Não |
| Windsor.ai destinos | Google Sheets recebe **export agendado de conector**, não linha avulsa | Não |
| Supermetrics | Consulta e push de dados de mídia | Não |

O conector do Drive é **create-only para conteúdo**. Não existe append, não
existe escrita de célula. Qualquer promessa de "salva direto na planilha" sem
resolver isso é falsa.

## 3. As possibilidades, da mais barata à mais robusta

### A. Botão "copiar linha" no painel — funciona hoje, zero setup

O painel monta as 14 colunas de `BASE_CRIATIVOS` separadas por TAB e joga no
clipboard. O gestor clica numa célula vazia da planilha e dá `Ctrl+V` — o
Sheets distribui pelas colunas sozinho.

~20 linhas de JS. Nenhuma credencial, nenhum conector, nenhum risco. Resolve a
dor real (redigitar) sem prometer automação que não existe.

### B. Apps Script Web App na própria planilha — a automática de verdade

Script de ~30 linhas em *Extensões → Apps Script* da `Criativos Turbo7`,
publicado como Web App. O painel faz `POST` e a linha entra sozinha, com
`Status: Copy em Aprovação` e `ID do Criativo` gerado pelo prefixo do cliente.

Setup do gestor: uma vez, ~5 minutos.

⚠️ **O risco que vem junto:** o painel é "qualquer pessoa com o link". Se a URL
do Web App ficar no HTML publicado, qualquer um que abra o painel pode escrever
na planilha de produção da agência. Só vale com o Web App restrito a
*"Somente eu"* (e o gestor logado no Google ao usar o painel), nunca com token
embutido no HTML.

### C. Doc novo por entrega — funciona hoje, zero setup

`create_file` cria `Copys dos Criativos - <Cliente> - Turbo7`, que é
exatamente a convenção de setembro (Movel Max, BS Design Grajaú). Bom para
entregar ao cliente, **não** resolve o pipeline: a linha continua fora da
`BASE_CRIATIVOS`.

### D. Planilha-ponte com IMPORTRANGE — descartada

`create_file` cria, não acrescenta. Cada gravação viraria um arquivo novo.
Não serve.

## 4. O achado que vale mais que os quatro: o loop está quebrado no nome

Nenhuma dessas opções fecha o loop entre ângulo e resultado, porque as duas
pontas não têm chave comum.

| Onde | Como o anúncio se chama |
| --- | --- |
| `Criativos Turbo7` → `ID do Criativo` | `AI0001`, `CI0001`, `MEI0001`, `DP0013` |
| `<Cliente> 🚀 Turbo7` → `ad_name` | `AD 01 PIC`, `AD 02`, `AD 04 PIC`, `DINAMICO - TESTES` |

Não cruzam. E tem pior: na `Casa & Cozinha 🚀 Turbo7`, as abas `Leads CRM` e
`Dashboard Internoo` trazem `Anuncio = "."` em **toda** a leva da campanha
`Casa e Cozinha | Forms | 18/09`. A aba `Leads Forms`, que vem direto do Meta,
tem o `ad_name` certo. Ou seja: o caminho do CRM está perdendo a atribuição no
meio.

**A correção é de nomenclatura, não de software.** Se o anúncio no Meta passar
a carregar o `ID do Criativo` — por exemplo `CC0042 | fundo-funil | video` —
então `ad_name` vira chave estrangeira e o cruzamento entre `copies/` e
`desempenho.md` sai sozinho, sem conector novo nenhum.

Enquanto isso não acontecer, gravar a copy na planilha organiza a produção e
**não** ensina nada sobre o que converte.

## 5. De quebra: a copy que já está na planilha não passa nas regras

Passando pelo linter quatro copies que estão em `BASE_CRIATIVOS` com
`Status: Entregue`, com preço liberado (ou seja, só as regras de tom e de
marca):

| Criativo | Reprovou por |
| --- | --- |
| `AI0001` Atlântica | `R2-superlativo` "o melhor custo benefício" · `MARCA-rodape` preço sem rodapé legal |
| `CI0001` Camminare | `MARCA-a-partir-de` "a partir de 19990" — e o valor está sem `R$` e sem ponto de milhar |
| `MEI0004` Maison | `MARCA-a-partir-de` · `MARCA-rodape` |
| `MEI0001` Maison | passou no linter, mas traz "lar dos sonhos" e "alto padrão" — clichê e superlativo que as listas de regra ainda não cobrem |

Três de quatro reprovam pelas regras que já existem, e o quarto mostra que as
listas de `R7-cliche` e `R2-superlativo` estão curtas demais. O linter ainda
não pega valor sem separador de milhar (`19990`), o que também é falha dele.

## 6. Recomendação

1. **Agora:** botão "copiar linha" (opção A). Barato, honesto, sem risco.
2. **Junto:** ampliar as listas do linter com o que a auditoria acima expôs, e
   fazer `MARCA-preco-formato` pegar `19990`.
3. **Decisão do gestor:** padronizar o nome do anúncio no Meta com o
   `ID do Criativo`. É o que transforma o sistema de "escreve copy" em
   "aprende qual copy converte".
4. **Só depois, se valer:** Apps Script (opção B), com o Web App restrito.
