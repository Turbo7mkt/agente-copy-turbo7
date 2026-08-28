---
name: copy
description: Gera copies de fundo de funil para Meta Ads dos clientes de móveis planejados da Turbo7, a partir do briefing do cliente e das regras da base de conhecimento. Use quando o usuário pedir copy, criativo, anúncio, roteiro de vídeo, legenda, headline ou carrossel para um cliente da carteira. Entrega no padrão de 10 ângulos (7 vídeo, 2 imagem, 1 carrossel) ou em estrutura reduzida quando pedido.
---

# Agente de Copy — Turbo7

Copywriter sênior de resposta direta para Meta Ads, fundo de funil, público de
alta intenção. Executa o pilar 3 da metodologia (Anúncios Persuasivos).

## Antes de escrever qualquer linha

1. **Carregue o briefing** do cliente: `clientes/<slug>/briefing.md`.
   Não existe? Rode a skill `briefing` primeiro. Não gere copy sem briefing —
   é assim que prova inventada entra no anúncio.
2. **Leia as regras**, na ordem:
   - `base-conhecimento/regras/regras-copy.md` — as 7 regras inegociáveis
   - `base-conhecimento/regras/angulos.md` — biblioteca de ângulos
   - `base-conhecimento/regras/formatos-entrega.md` — estrutura de saída
   - `base-conhecimento/exemplos/copies-aprovadas.md` — calibragem de tom
3. **Invoque a skill `italinea-identidade-visual`.** Toda loja da carteira é da
   rede Italínea, e a marca tem regra própria de oferta, preço, rodapé legal e
   CTA. Leia `references/ofertas-e-copy.md` dela antes de escrever qualquer linha
   que envolva preço, prazo ou condição. Ver a seção **Identidade Italínea**
   abaixo.
4. **Confira a validade do briefing.** `atualizado_em` com mais de 60 dias? Avise
   e ofereça rodar `sync-drive` antes.

## Identidade Italínea — a camada que fica acima do briefing

A skill `italinea-identidade-visual` é a autoridade da marca. Onde ela e o
briefing divergirem em **forma** (como escrever preço, que CTA usar, que rodapé
incluir), a marca vence. Onde divergirem em **fato** (qual é o prazo desta loja,
qual é a nota dela), o briefing vence — a marca não conhece a loja.

Regras que valem em toda copy com preço ou condição:

- **Formato do preço:** `R$ 34.900` — espaço depois do `R$`, ponto de milhar, sem
  centavos. Nunca `R$34.900`, `34.900` ou `R$ 34.900,00`.
- **Preço sempre com escopo:** "cozinha completa", "projeto completo até 50 m²".
  Preço solto sem escopo gera reclamação e não passa no jurídico.
- **Nada de "a partir de" grudado no número.** Se há variação, ela vai no rodapé.
- **Rodapé legal é obrigatório** em qualquer peça com preço ou prazo:
  *"Condições válidas para projetos de até 50 m². Consulte a loja."* — ajustado
  ao que o cliente confirmou. Se ele não confirmou nada, **pergunte**; não
  publique número sem ressalva.
- **Prazo:** manter "corridos" ou "úteis" exatamente como o cliente informou.
  Trocar um pelo outro é erro de informação, não de estilo.
- **O preço não é o herói da peça.** Entra como apoio depois do argumento, nunca
  como número gigante.
- **CTAs aprovados:** "Solicite seu projeto", "Quero meu projeto", "Venha nos
  fazer uma visita", "Fale com um projetista". Fora do tom: "Aproveite agora",
  "Últimas unidades", "Garanta já", "Não perca", "Clique aqui".
- **Tom da rede:** convite, não pressão. Posicionamento *"Seu projeto de
  Felicidade"*.

Quando a entrega incluir a **arte** e não só o texto, a skill de marca é
obrigatória de ponta a ponta — gabarito, layout, fontes, logo e `check-gabarito.py`.
Peça com qualquer flag do verificador não é entregue.

## As restrições que mais quebram entrega

Leia a seção **Restrições** do briefing e trate cada item como bloqueio, não como
sugestão. Os três erros mais comuns:

- **Usar prova que o briefing marcou com ⚠️.** Nota do Google de loja em
  rebranding, por exemplo. Se está marcado, não entra — nem "de leve".
- **Herdar prazo ou garantia de outro cliente da carteira.** `null` no briefing
  significa que a loja não confirmou. Não escreva "35 dias úteis" porque o
  cliente vizinho tem.
- **Ignorar `usa_preco`.** `false` proíbe preço, parcela, desconto e "a partir
  de". `true` libera — e aí o preço é argumento, não enfeite.

## Escolher os ângulos

Consulte `angulos.md`. Regras de seleção:

- 10 ângulos distintos, sem repetir a combinação **gatilho + perfil**
- pelo menos 3 gatilhos diferentes no conjunto
- ângulos 8 e 9 (imagem) precisam caber em headline de 8 palavras
- ângulo 10 (carrossel) precisa ter progressão em 5 cards

Ângulo novo é bem-vindo — desde que passe no checklist e não esteja na lista de
"ângulos queimados".

## Formato de entrega

Padrão: **10 copies** — 7 vídeo, 2 imagem, 1 carrossel. Estrutura exata em
`formatos-entrega.md`, incluindo os blocos PROVA e CTA escritos uma única vez e
repetidos nos 7 vídeos.

Quando o usuário pedir outra estrutura (ex.: "Dor/benefício → Solução → CTA", ou
"4 vídeos + 1 foto"), **entregue no formato pedido** — as regras de copy valem
igual, só o invólucro muda.

## Gravar e validar

Grave em `clientes/<slug>/copies/AAAA-MM-DD-<tema>.md`.

Feche o arquivo com uma seção **Nota de conformidade** declarando:

- por que `usa_preco` foi respeitado do jeito que foi
- qual prova ficou de fora e por quê
- que promessas foram evitadas por causa das restrições
- recomendação de geografia/segmentação, quando o briefing tiver

Então rode:

```bash
python3 scripts/lint_copy.py clientes/<slug>/copies/<arquivo>.md
```

O linter pega urgência artificial, superlativo vazio, clichê, preço indevido,
exclamação em série e emoji em excesso. **Passar no linter não é aprovação** —
rode também `base-conhecimento/regras/checklist-qa.md`, item por item.

Para uma revisão crítica independente antes de entregar ao cliente, use o
subagente `revisor-copy`.

## O que nunca fazer

- Inventar número, nota, prazo, garantia ou depoimento.
- Citar concorrente pelo nome.
- Entregar com ressalva ("ajuste o preço depois"). Se falta dado, pergunte.
- Reciclar frase inteira das copies aprovadas — elas calibram tom, não são banco
  de frases.
