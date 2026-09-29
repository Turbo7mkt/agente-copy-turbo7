# Identidade visual da Turbo7 — as ferramentas da agência

> Cores e tipografia derivadas do logotipo enviado pelo gestor em 29/09/2026.
> São **valores aproximados lidos da imagem**, não um manual de marca oficial.
> Se a agência tiver o manual com os HEX exatos, ele vence este arquivo — troque
> os valores aqui e o painel inteiro acompanha, porque tudo é token.

## A regra que separa as duas marcas

Existem duas identidades neste sistema e elas nunca se misturam:

| Onde | Identidade | Quem manda |
| --- | --- | --- |
| **Ferramenta interna** — painel, app, relatório para o gestor | **Turbo7** | este arquivo |
| **Peça que chega ao consumidor** — anúncio, arte, copy entregue | **Italínea** | skill `italinea-identidade-visual` |

O roxo da Turbo7 é a casca de quem opera. Ele **nunca** entra num anúncio de
loja: quem compra cozinha planejada não conhece a agência, conhece a rede. Uma
peça de cliente com roxo de agência é erro de marca, não escolha de design.

## Paleta

| Token | Claro | Escuro | Onde aparece |
| --- | --- | --- | --- |
| `--azul` *(primário)* | `#6D28D9` | `#C4A5F7` | Botões, links, foco, estado selecionado |
| `--azul-vivo` | `#7C3AED` | `#DCC4FF` | Hover e anel de foco |
| `--magenta` | `#A21CAF` | `#F0ABFC` | O `7` do logotipo, fim do gradiente |
| `--pessego` | `#F7D9FB` | `#F0ABFC` | Selo de destaque (era o pêssego Italínea) |
| `--ground` | `#F8F6FD` | `#110A1F` | Fundo da página |
| `--surface` | `#FFFFFF` | `#1B1230` | Cartões e campos |
| `--line` | `#E5DCF4` | `#38265C` | Divisórias |
| `--ink` | `#17102A` | `#F0E9FA` | Texto principal |

O token primário ainda se chama `--azul`. O nome ficou do tempo em que o painel
usava o azul Italínea. Renomear obrigaria a tocar todas as regras da folha sem
mudar um pixel — o comentário no topo do arquivo explica, e isso basta.

Neutros têm **viés violeta**, nunca cinza puro: um cinza neutro ao lado do roxo
parece sujo.

## Gradiente da assinatura

```css
linear-gradient(118deg, #4C1D95 0%, #6D28D9 42%, #A21CAF 100%)
```

É o fundo do logotipo. Usa-se **uma vez por tela**, no topo. Gradiente repetido
vira papel de parede e a marca some.

Dentro dele, tudo é branco — incluindo pílulas e selos de estado, que trocam
verde/vermelho por níveis de transparência branca. Verde sobre roxo não lê.

## Marca

```
TURBO7        — Poppins 700, letter-spacing .07em, "7" em #F5C2FF
Foguete       — SVG inline, branco, dentro de um selo 36×36 com fundo
                rgba(255,255,255,.15)
Assinatura    — "Marketing de planejados" ou o nome da ferramenta
```

O foguete é o único elemento figurativo. Não desenhe outro ícone com ele junto.

## Tipografia

Mantida do painel, porque já estava certa para as duas marcas:

| Papel | Fonte |
| --- | --- |
| Display (títulos, botões, marca) | **Poppins** 600/700 |
| Corpo | **Nunito Sans** 400/600 |
| Números, códigos de regra, metadados | **JetBrains Mono** |

## Onde isto está implementado

| Arquivo | O que carrega |
| --- | --- |
| `app/static/style.css` | Tokens e o topo do painel local |
| `app/static/index.html` | Marcação da marca (selo + foguete + wordmark) |
| Artifact `Painel de Copy Turbo7` | Mesma paleta, mesmo topo, publicado |

Mudou uma cor? Mude o token nos três e nada mais — nenhuma regra da folha tem
HEX solto fora do bloco `:root`, e essa é a condição para a troca ser barata.
