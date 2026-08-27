# Rotina de sincronização com o Google Drive

Varredura automática do Drive para manter a base de conhecimento em dia.

- **ID da rotina:** `trig_01Max61MfWCS5raH2j7gRfWG`
- **Nome:** Sync base de conhecimento — Google Drive
- **Agenda:** `0 11 * * 1-5` (dias úteis, 8h em Brasília)
- **Modo:** sessão nova a cada disparo, commitando em
  `claude/copy-agent-system-sttz3y`

> ## ⚠️ Pendência: conector do Google Drive
>
> A rotina foi criada, está ativa e vai disparar — mas **ainda não tem o conector
> do Google Drive anexado**, e sem ele a sessão disparada não enxerga as
> ferramentas `mcp__Google_Drive__*`. Ou seja: ela roda e não consegue ler o
> Drive.
>
> O motivo é uma limitação de propagação: uma rotina só herda os conectores que a
> sessão que a criou já carrega, e a sessão que a criou não tinha esse repasse
> disponível.
>
> **Como resolver (1 minuto, precisa ser você):**
>
> 1. Abra as rotinas em [claude.ai](https://claude.ai) → Routines
> 2. Encontre *Sync base de conhecimento — Google Drive*
> 3. Habilite o conector **Google Drive** nela e salve
>
> Enquanto isso não for feito, rode a sincronização manualmente com
> `/sync-drive` numa sessão que tenha o Drive conectado — a skill é a mesma.

## O que a rotina faz

A cada disparo, uma sessão nova executa a skill `sync-drive`:

1. Lê `ultima_sincronizacao` em `base-conhecimento/MANIFEST.yaml`
2. Busca no Drive tudo com `modifiedTime` posterior a essa data
3. Tria pelo título e pela pasta (ver tabela de triagem na skill)
4. Ingere o que passa, com linha de procedência no topo do arquivo
5. Atualiza o manifesto e commita na branch de trabalho
6. Relata: novos, atualizados, ignorados, pendências

Se nada mudou, encerra sem gerar ruído.

## O que ela nunca ingere

- **Credenciais.** Documentos de acesso do Drive são descartados por triagem
  explícita e registrados em `ignorar[]`.
- **Dashboards de métrica.** Planilhas Stract, Painel Consolidado, Central de
  dados, planilhas `<Cliente> 🚀 Turbo7`. São dado operacional, não conhecimento
  de copy.
- **Documentos sem título.**

## O que precisa de decisão humana

A rotina **não sobrescreve edições locais em silêncio**. Quando um arquivo já
existe no repo e mudou no Drive, ela mostra o diff e pede confirmação. Isso vale
sobretudo para `clientes/*/briefing.md`, que costumam ter curadoria manual do
gestor.

Arquivo de classificação duvidosa também para e pergunta — é melhor ficar de
fora do que poluir a base.

## Frequência

Dias úteis, 8h (horário de Brasília) — `0 11 * * 1-5` em UTC.

Foi escolhido dias úteis porque os diagnósticos são produzidos durante a semana,
em geral no onboarding de cliente novo. Fim de semana só geraria execução vazia.

## Alterar ou desligar

A rotina aparece em `/routines` no Claude Code, ou pelas ferramentas do
claude-code-remote:

```
list_triggers
update_trigger  trigger_id=trig_01Max61MfWCS5raH2j7gRfWG enabled=false
update_trigger  trigger_id=trig_01Max61MfWCS5raH2j7gRfWG cron_expression='0 11 * * 1'
delete_trigger  trigger_id=trig_01Max61MfWCS5raH2j7gRfWG
```

O segundo comando pausa; o terceiro passa para semanal, só às segundas; o quarto
remove de vez.

Para rodar fora de hora, sem esperar o agendamento:

```
fire_trigger  trigger_id=trig_01Max61MfWCS5raH2j7gRfWG
```

Ou simplesmente peça `/sync-drive` numa sessão aberta.

## Execução manual

```
/sync-drive
```

A skill funciona igual, agendada ou a pedido. A diferença é só quem dispara.
