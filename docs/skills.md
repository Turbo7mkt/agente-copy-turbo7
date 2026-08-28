# Skills do agente de copy — o que usa, o que falta, o que foi descartado

Levantamento feito em 28/08/2026 sobre o catálogo de skills e plugins da conta.

## Resumo

O ecossistema aberto **não tem** skill de copywriting publicitário em português
que sirva para esta operação. A busca por `copywriting`, `marketing`, `meta ads`,
`social media`, `branding` e `voz de marca` no catálogo de skills standalone
retornou zero resultados.

A capacidade que faltava não estava fora — estava desconectada dentro de casa: a
skill **`italinea-identidade-visual`** já estava habilitada na conta e não era
consumida pelo agente de copy. Ela é a autoridade da marca sobre preço, rodapé
legal, CTA e tom. Agora é dependência obrigatória da skill `copy`.

## Dependências do agente

### Obrigatórias

| Skill | Origem | Para quê |
| --- | --- | --- |
| `copy` | este repo | Gera as copies |
| `briefing` | este repo | Diagnóstico 360° → briefing estruturado |
| `sync-drive` | este repo | Mantém a base de conhecimento em dia |
| `italinea-identidade-visual` | conta (habilitada) | **Autoridade da marca.** Formato de preço, rodapé legal obrigatório, CTAs aprovados, tom da rede, gabaritos e fontes para a arte |

Precedência entre a skill de marca e o briefing do cliente:

- Divergência de **forma** (como escrever preço, que CTA usar) → **marca vence**.
- Divergência de **fato** (qual o prazo desta loja, qual a nota dela) →
  **briefing vence**. A marca não conhece a loja.

### Úteis, já habilitadas

| Skill | Para quê no fluxo |
| --- | --- |
| `pdf` | Briefing e diagnóstico chegam em PDF (o "PROMPT COPYS" original diz "enviado como pdf") |
| `docx` | Diagnósticos e planos exportados do Drive |
| `xlsx` | Planilhas de acompanhamento e métricas por cliente |
| `canva` (plugin) | Montagem e brand-check de peça no Canva |
| `skill-creator` | Criar e otimizar novas skills desta operação |
| `find-skills` | Descobrir skills do ecossistema (instalada manualmente neste repo) |

## Avaliados e não instalados

Nenhum é necessário para o agente funcionar. Ficam registrados com o motivo para
não serem reavaliados do zero.

| Candidato | Por que não |
| --- | --- |
| **`marketing`** (plugin) | Content marketing B2B genérico: SEO audit, sequência de e-mail, blog post. O que teria valor (`performance-report`, `competitive-brief`) já é coberto pelo diagnóstico e pelos conectores Supermetrics/Windsor que a conta tem. Traz junto MCPs que a operação não usa (Ahrefs, HubSpot, Klaviyo, Amplitude, Similarweb) |
| **`adspirer-ads-agent`** (plugin) | O mais relevante do catálogo — gestão de Meta/Google/TikTok Ads, 91 ferramentas, `performance-review` e `wasted-spend`. **Exige conta Adspirer** (custo e setup externos). O `write-ad-copy` dele competiria com a skill `copy`, que é específica da carteira. Vale considerar se a agência quiser gestão de campanha dentro do Claude, não só copy |
| `postiz` | Agendamento em 28+ plataformas. A operação publica direto no Meta |
| `zoominfo`, `twilio`, `carta`, `growthbook`, `airtable`, `small-business` | Fora do domínio |

## Lacuna real que sobrou

O que o sistema ainda **não** faz: fechar o loop entre o ângulo entregue e o
resultado dele. Hoje escrevemos 10 ângulos e não sabemos qual converteu.

A metodologia já aponta isso ("loop de atribuição": lead qualificado no CRM
devolve evento para Meta CAPI e Google offline). Os conectores para resolver
— **Supermetrics** e **Windsor.ai** — já estão disponíveis na conta.

Isso é skill nova a construir, não skill a instalar. Ver a proposta em
`docs/proximos-passos.md`.

## Reproduzir este levantamento

```
SearchSkills   keywords: copywriting, marketing, meta ads, social media, branding
ListSkills     (o que já está habilitado)
SearchPlugins  keywords: marketing, copywriting, ads, social media, analytics
```

O `npx skills find` da skill `find-skills` também serve — mas só rodando o Claude
Code local. Em sessão web o clone de repositórios de terceiros é bloqueado.
