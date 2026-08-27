---
name: briefing
description: Converte um Diagnóstico Digital 360° do Google Drive em briefing estruturado de cliente, pronto para gerar copy. Use quando o usuário pedir para criar/atualizar o briefing de um cliente, quando mencionar um diagnóstico novo, ou antes de gerar copy para um cliente que ainda não tem briefing em clientes/<slug>/briefing.md.
---

# Diagnóstico → Briefing

O briefing é o contrato entre o diagnóstico (pilar 1 da metodologia) e a copy
(pilar 3). Ele existe para que o agente de copy **nunca precise inventar prova**.

## Passo 1 — Localizar o diagnóstico

Se o usuário não deu o `fileId`, busque no Drive:

```
title contains 'Diagnóstico' and title contains '<nome do cliente>'
```

Leia com `mcp__Google_Drive__read_file_content`. Se houver mais de um, use o de
`modifiedTime` mais recente e diga qual escolheu.

## Passo 2 — Extrair os campos

Mapeamento do diagnóstico para o frontmatter do briefing:

| Bloco do diagnóstico | Campo do briefing |
| --- | --- |
| Cabeçalho: Cliente, Gestor, Data, Praça | `nome`, `gestor`, `atualizado_em`, `praca` |
| 1. Anúncios · Anotações (ticket, região) | `ticket_alvo`, `publico` |
| 1. Anúncios · Ação (campanha de preço?) | `usa_preco` |
| 3. Site/LP · Diferenciais | `garantia`, `prazo_entrega`, seção **Diferenciais** |
| 4. Google Meu Negócio · Nota | `unidades[].google_nota`, `google_avaliacoes` |
| 8. Concorrência | seção **Concorrência na praça** |
| 8. Concorrência · Ação | seção **Restrições** e implicação para a copy |
| Resumo · Bloqueios | seção **Insumos visuais disponíveis** |

Preencha a partir de `clientes/_TEMPLATE/briefing.md`.

## Passo 3 — Decidir `usa_preco`

Este é o campo que mais muda a copy. Decida por evidência, não por hábito:

- `false` — quando o diagnóstico diz que a loja não divulga preço, ou quando a
  ação recomenda disputar por reputação/pós-venda. Padrão da carteira.
- `true` — quando a ação do diagnóstico pede explicitamente campanha de preço, ou
  quando existe tabela de valores por metragem no documento.

Registre o valor **e a frase do diagnóstico que o justifica**, na seção Oferta ou
Restrições.

## Passo 4 — Filtrar as provas

Regra dura: **prova só entra se for verificável e estiver limpa.**

Antes de registrar nota do Google como prova, cheque o bloco 8 e as anotações:

- Perfil duplicado, rebranding em curso, avaliação 1 estrela em destaque? →
  a nota **não** vira prova. Registre o motivo com `⚠️` na seção Provas.
- Reclamação recorrente sobre um tema (prazo, cor, montagem)? → vira
  **Restrição**: a copy não pode prometer perfeição naquele tema.

Prazo e garantia só entram se estiverem escritos no diagnóstico. Ausente = `null`.
Nunca herde de outro cliente da carteira.

## Passo 5 — Escrever e validar

Grave em `clientes/<slug>/briefing.md`. O `slug` é o nome em minúsculas, sem
acento, separado por hífen (`Preemier Decore Italínea` → `preemier-decore-italinea`).

Antes de fechar, confira:

- [ ] Todo campo do frontmatter está preenchido ou explicitamente `null`?
- [ ] Toda prova tem origem rastreável em `fontes`?
- [ ] `usa_preco` tem justificativa escrita?
- [ ] As restrições cobrem o que o diagnóstico marcou como sensível?
- [ ] Nada de credencial, senha ou acesso foi copiado para o repo?

Se um campo essencial (praça, público, diferencial, CTA) não existir no
diagnóstico, **liste as lacunas para o gestor** em vez de preencher por
suposição.
