# Formatos de entrega — 10 copies

> Fonte: Google Drive · "PROMPT COPYS"

## Distribuição obrigatória

| Nº | Formato | Quantidade |
| --- | --- | --- |
| 1–7 | Vídeo | 7 |
| 8–9 | Imagem estática | 2 |
| 10 | Carrossel | 1 |

Cada uma das 10 é um **ângulo psicológico diferente**, com gatilho claro
(Dor / Desejo / Objeção / Emocional / Racional — pode combinar) e um perfil
específico de comprador.

## Arquitetura dos 7 vídeos — 5 blocos

Os blocos 1–3 **variam** por ângulo. Os blocos 4–5 são **idênticos** nos 7 vídeos,
escritos uma única vez no topo da seção e referenciados nos demais.

| Bloco | Tempo | Varia? | Conteúdo |
| --- | --- | --- | --- |
| ✦ GANCHO FORTE | 0–3s | Sim | Frase única que para o scroll. Pergunta, afirmação reconhecível ou provocação. Nunca clichê. |
| ✦ CLAREZA | 5–10s | Sim | 2 frases definindo cenário, dor ou desejo. O espectador entende do que se trata e por que diz respeito a ele. |
| ✦ EMOÇÃO | 10–15s | Sim | 2–3 frases conectando à vida real. Cena cotidiana, sensação reconhecível, projeção de futuro. O bloco do "isso é comigo". |
| ✦ PROVA | 5–10s | **Não** | Credibilidade da marca, a partir das provas do briefing. |
| ✦ CTA | últimos 5s | **Não** | Chamada de baixa fricção, a partir do CTA preferido + benefício de entrada. |

### Formato de saída dos vídeos

```
═══════════════════════════════════════
BLOCOS PADRONIZADOS DOS 7 VÍDEOS
═══════════════════════════════════════

✦ PROVA (igual nos 7 vídeos):
[texto do bloco de prova, baseado nas credenciais do briefing]

✦ CTA (igual nos 7 vídeos):
[texto do bloco de CTA, baseado no CTA preferido + benefício de entrada]

═══════════════════════════════════════

ÂNGULO [Nº] — [NOME DO ÂNGULO]
Gatilho: [Dor / Desejo / Objeção / Emocional / Racional]
Para quem fala: [descrição em 1 linha do perfil específico]

✦ GANCHO FORTE:
[frase de parada de scroll, exclusiva deste ângulo]

✦ CLAREZA:
[2 frases definindo cenário/dor/desejo, exclusivas deste ângulo]

✦ EMOÇÃO:
[2-3 frases conectando à vida real do espectador, exclusivas deste ângulo]

✦ PROVA: [usar bloco padrão acima]

✦ CTA: [usar bloco padrão acima]

LEGENDA DO POST (3-5 linhas, prontas para colar):
[texto pronto]

CTA do botão Meta Ads: [Saiba Mais / Enviar Mensagem / Cadastre-se / etc.]
```

## Formato das copies de IMAGEM (8 e 9)

```
ÂNGULO [Nº] — [NOME DO ÂNGULO]
Gatilho: [tipo]
Para quem fala: [perfil]

HEADLINE (texto principal sobre a imagem, máx 8 palavras):
[frase impactante]

SUBHEADLINE (apoio, máx 12 palavras):
[frase de reforço]

LEGENDA DO POST (3-5 linhas):
[texto pronto]

SUGESTÃO VISUAL (1 linha): [tipo de imagem que combina com a copy]

CTA do botão: [opção]
```

## Formato da copy de CARROSSEL (10)

```
ÂNGULO 10 — [NOME DO ÂNGULO]
Gatilho: [tipo]
Para quem fala: [perfil]

CARD 1 (capa) — Headline + Subheadline:
[texto]

CARD 2 — [tema do card]:
[texto]

CARD 3 — [tema do card]:
[texto]

CARD 4 — [tema do card]:
[texto]

CARD 5 (CTA) — Headline + chamada:
[texto]

LEGENDA DO POST (3-5 linhas):
[texto pronto]

CTA do botão: [opção]
```

---

# Limites de tamanho — o que o Meta realmente exibe

> Acrescentado em 05/10/2026, depois de uma copy sair com 1.127 caracteres de
> texto principal. O Meta corta em ~125: o leitor via a primeira frase e um
> "Ver mais", sem chegar na loja nem na oferta. Longo demais não é "caprichado",
> é anúncio que não foi lido.

| Peça | Limite | Por quê |
| --- | --- | --- |
| **Texto principal** | **400 caracteres**, com dor + marca nos **primeiros 125** | 125 é onde o Meta trunca no feed. O que vem depois só é lido por quem clicou em "Ver mais" |
| **Título** | **40 caracteres** | Acima disso o Meta corta no meio da frase |
| **Descrição** | **30 caracteres** | Idem, e em vários posicionamentos nem aparece |
| **Nota de conformidade** | **6 linhas** | É recado para o gestor, não entrega. Nota maior que a copy é sinal de que a copy encolheu |

A régua dos 400 não é arbitrária: as copies **aprovadas** desta base têm
mediana entre 126 e 317 caracteres por bloco. 400 já é o teto generoso.

## O corte, na prática

Escrever curto não é cortar argumento — é escolher **um**. A copy de 1.127
caracteres tentava entregar, de uma vez: a dor da reforma por etapas, a
continuidade do projeto, a tabela inteira de preço, o showroom, o arquiteto e a
nota do Google. Seis argumentos brigando por 125 caracteres de atenção.

Regra prática: **uma dor, uma prova, um CTA.** O resto é material para o próximo
criativo, não para o mesmo.

`scripts/lint_copy.py` reprova com `TAMANHO-titulo`, `TAMANHO-descricao` e
`TAMANHO-paragrafo` quando o limite estoura.
