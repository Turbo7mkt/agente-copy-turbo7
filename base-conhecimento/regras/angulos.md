# Biblioteca de ângulos — fundo de funil, planejados B+

Catálogo de ângulos já validados na carteira. O agente escolhe **10 distintos**
por entrega (sem repetir a combinação gatilho + perfil) e pode criar novos —
desde que passem no checklist.

> Os ângulos 1–6 saíram das copies aprovadas de DiCasa Italínea (ago/2026).
> Os demais são variações do mesmo eixo: disputar por confiança, não por preço.

A coluna **Requer** é lida por máquina: o painel usa ela para esconder, na hora de
perguntar o ângulo, tudo que o briefing do cliente não sustenta. Tokens válidos:

| Token | Significa |
| --- | --- |
| `prova:google` | Depende da nota/volume de avaliações. Some se a prova estiver marcada com ⚠️ |
| `campo:prazo_entrega` | Depende do prazo confirmado. Some se o campo for `null` |
| `campo:garantia` | Depende da garantia confirmada. Some se o campo for `null` |
| `preco` | Só faz sentido com `usa_preco: true` |
| `—` | Não depende de nada além do briefing existir |

| # | Ângulo | Gatilho | Fala com | Eixo | Requer |
| --- | --- | --- | --- | --- | --- |
| 1 | O que só aparece depois da montagem | Racional + Emocional | Quem já se decepcionou com acabamento | Acabamento / encaixe / gaveta que continua deslizando | — |
| 2 | Ninguém pergunta sobre o depois | Objeção | Quem tem medo de ficar na mão pós-entrega | Pós-venda como parte do projeto | — |
| 3 | Nada no escuro | Objeção | Quem teme surpresa no projeto | Medição, 3D, acabamentos ao vivo, aprovação antes de produzir | — |
| 4 | Começa por um ambiente | Desejo | Quem vai reformar por etapas | Coerência entre ambientes do mesmo projeto | — |
| 5 | Se você já tem arquiteto | Objeção | Cliente com arquiteto contratado | Trabalho conjunto, sem retrabalho nem disputa de autoria | — |
| 6 | Dias úteis ou dias corridos? | Racional | Quem está com obra e mudança marcada | Transparência de prazo antes de assinar | `campo:prazo_entrega` |
| 7 | A visita que decide | Desejo | Quem já pesquisou muito e não decidiu | Showroom, ver e tocar o acabamento | — |
| 8 | O orçamento mais barato | Objeção | Quem está comparando propostas | Custo do retrabalho vs custo do projeto bem-feito | — |
| 9 | A casa que recebe | Emocional | Quem vai receber família/amigos | Projeção de uso, não de produto | — |
| 10 | Quem já passou por isso | Racional | Cético, quer prova social | Volume e nota das avaliações no Google | `prova:google` |
| 11 | Espaço que não sobra | Dor | Apartamento compacto, ticket alto | Milímetro aproveitado, marcenaria sob medida | — |
| 12 | O prazo que não atrasa a mudança | Dor | Quem tem data de entrega de obra | Cronograma casado com a obra | `campo:prazo_entrega` |
| 13 | Cinco anos depois | Racional | Quem pensa em durabilidade | Garantia como consequência do processo | `campo:garantia` |
| 14 | A decisão que trava | Emocional | Casal que não fecha a escolha | Projetista conduzindo a decisão a dois | — |
| 15 | O valor que já está fechado | Racional | Quem decide por preço e odeia orçamento vago | Preço por metragem, com escopo, sem "a partir de" | `preco` |

## Como escolher os 10

- Cubra pelo menos **3 gatilhos diferentes** entre os 10.
- Não repita **perfil**: se o ângulo 2 fala com "quem teme ficar na mão", nenhum
  outro dos 10 pode falar com o mesmo perfil.
- Os 2 de imagem (8 e 9) pedem ângulos que cabem em **8 palavras de headline** —
  prefira racionais e objeções curtas (ângulos 6, 10, 13).
- O carrossel (10) pede ângulo com **progressão** — algo que se explica em 5
  cards (ângulos 3, 5, 8 funcionam bem).

## Ângulos queimados (não usar sem instrução)

- "Realize o sonho da casa própria" — clichê de mercado.
- "Qualidade e excelência que você merece" — superlativo vazio, regra 2.
- "Últimas unidades / condição só até sexta" — urgência artificial, regra 2.
- Qualquer ângulo cujo argumento central seja **preço ou parcela**, salvo
  `usa_preco: true` no briefing.
