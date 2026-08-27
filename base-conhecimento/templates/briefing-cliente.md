# Template de briefing de cliente

Copie para `clientes/<slug>/briefing.md` e preencha. Os campos do frontmatter são
lidos pelas skills e pelo linter; os campos em prosa alimentam a copy.

Todo campo preenchido precisa ter **origem rastreável** (diagnóstico, reunião,
site do cliente). Campo sem origem fica `null` — o agente de copy nunca inventa
prova.

```markdown
---
slug: dicasa-italinea
nome: DiCasa Italínea
unidades:
  - nome: Moinhos
    google_nota: 5.0
    google_avaliacoes: 77
  - nome: Higienópolis
    google_nota: 4.8
    google_avaliacoes: 355
nicho: Móveis planejados
praca: Porto Alegre / RS
gestor: Micheli
ticket_alvo: acima de R$ 50 mil
publico: B+
usa_preco: false          # true libera preço/parcela na copy
prazo_entrega: 35 dias úteis
garantia: 5 anos
cta_preferido: Agendar visita ao showroom
cta_botao_meta: Enviar Mensagem
canais: [meta]
atualizado_em: 2026-08-24
fontes:
  - "Drive: Diagnóstico - DiCasa Italínea Moinhos & Higienópolis (1Opl6qW...)"
---

## Provas disponíveis
Lista do que pode virar bloco PROVA. Só o que é verificável.

## Diferenciais
O que a loja faz que o concorrente da praça não faz.

## Concorrência na praça
Quem roda anúncio, com que oferta, e o que isso implica para a nossa copy.

## Tom da marca
Como a marca fala. Duas ou três linhas.

## Restrições
O que não pode ser dito. Ex.: não divulgar preço, não citar o nome do concorrente.

## Insumos visuais disponíveis
Banco de fotos/vídeos de montagens executadas? Depoimentos? Showroom?
```
