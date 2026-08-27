# Checklist final — antes de entregar

> Fonte: Google Drive · "PROMPT COPYS". Se algum item falhar, **reescreva antes
> de entregar**. Não entregue com ressalva.

## Diferenciação

- [ ] Os 10 ângulos são de fato diferentes entre si? (sem repetir gatilho + perfil)
- [ ] Os blocos Gancho, Clareza e Emoção variam genuinamente entre os 7 vídeos?
- [ ] Os blocos Prova e CTA estão escritos uma única vez e mantidos idênticos?

## Qualidade da copy

- [ ] Cada hook funcionaria como primeira frase parando o scroll?
- [ ] Nenhum CTA cria pressão artificial?
- [ ] O tom está alinhado ao estilo da marca informado no briefing?
- [ ] Cada copy tem alguém específico em mente, não "o público em geral"?
- [ ] Está em português natural, sem cara de anúncio traduzido?

## Conformidade com o briefing

- [ ] Nenhuma copy cita preço/parcela/desconto (salvo `usa_preco: true`)?
- [ ] Toda prova usada (nota, nº de avaliações, prazo, garantia) consta do
      briefing? Nada inventado?
- [ ] O prazo está declarado em **dias úteis** quando o briefing diz dias úteis?
- [ ] O nome da loja/unidade está grafado como no briefing?

## Verificação automática

Rode o linter antes de fechar a entrega:

```bash
python3 scripts/lint_copy.py clientes/<slug>/copies/<arquivo>.md
```

Ele pega urgência artificial, superlativos vazios, preço, excesso de emoji e
exclamação em série. Passar no linter **não** substitui o checklist acima —
ele só cobre o que dá para checar por padrão de texto.
