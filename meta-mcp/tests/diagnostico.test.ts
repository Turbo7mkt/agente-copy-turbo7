import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { hojeNoFuso, intervaloDoPeriodo, periodoAnterior } from "../lib/regras/periodo";
import { compararMetricas, limiteSemLead } from "../lib/regras/diagnostico";
import { calcular } from "../lib/regras/metricas";
import { contaMeta, erroMeta, linhaInsights, simularMeta } from "./apoio/metaSimulada";
import { chamar, novosModulos } from "./apoio/mcp";

describe("datas do período", () => {
  it("o dia vira no fuso da conta, não no UTC", () => {
    // 29/09 às 01h UTC ainda é 28/09 em São Paulo.
    expect(hojeNoFuso("America/Sao_Paulo", new Date("2026-09-29T01:00:00Z"))).toBe("2026-09-28");
  });

  it("segue a semântica dos presets da Meta (últimos N dias não incluem hoje)", () => {
    const hoje = "2026-09-29";
    expect(intervaloDoPeriodo("ultimos_7d", hoje)).toEqual({ inicio: "2026-09-22", fim: "2026-09-28" });
    expect(intervaloDoPeriodo("ontem", hoje)).toEqual({ inicio: "2026-09-28", fim: "2026-09-28" });
    expect(intervaloDoPeriodo("mes_atual", hoje)).toEqual({ inicio: "2026-09-01", fim: "2026-09-29" });
    expect(intervaloDoPeriodo("mes_passado", "2026-01-15")).toEqual({ inicio: "2025-12-01", fim: "2025-12-31" });
  });

  it("anterior equivalente: mesmo tamanho, logo antes", () => {
    expect(periodoAnterior({ inicio: "2026-09-22", fim: "2026-09-28" })).toEqual({ inicio: "2026-09-15", fim: "2026-09-21" });
    expect(periodoAnterior({ inicio: "2026-03-01", fim: "2026-03-01" })).toEqual({ inicio: "2026-02-28", fim: "2026-02-28" });
  });

  it("mês atual compara com os mesmos dias do mês anterior, limitado ao fim do mês", () => {
    expect(periodoAnterior({ inicio: "2026-09-01", fim: "2026-09-29" }, "mes_atual")).toEqual({ inicio: "2026-08-01", fim: "2026-08-29" });
    expect(periodoAnterior({ inicio: "2026-03-01", fim: "2026-03-31" }, "mes_atual")).toEqual({ inicio: "2026-02-01", fim: "2026-02-28" });
  });

  it("mês passado compara com o mês inteiro antes dele, mesmo de tamanhos diferentes", () => {
    expect(periodoAnterior({ inicio: "2026-03-01", fim: "2026-03-31" }, "mes_passado")).toEqual({ inicio: "2026-02-01", fim: "2026-02-28" });
    expect(periodoAnterior({ inicio: "2026-01-01", fim: "2026-01-31" }, "mes_passado")).toEqual({ inicio: "2025-12-01", fim: "2025-12-31" });
  });
});

describe("compararMetricas", () => {
  const m = (p: Parameters<typeof linhaInsights>[0]) => calcular(linhaInsights(p), "act_1");

  it("CPL subindo além do limiar é piora; oscilação pequena é silêncio", () => {
    const anterior = m({ gasto: 1000, impressoes: 50000, cliques: 500, frequencia: 2, leads: 50 }); // CPL 20
    const atual = m({ gasto: 1000, impressoes: 52000, cliques: 520, frequencia: 2.1, leads: 40 }); // CPL 25
    const alertas = compararMetricas(atual, anterior);
    expect(alertas).toHaveLength(1);
    expect(alertas[0]).toMatchObject({ metrica: "cpl", sentido: "piora", variacao_pct: 25 });
  });

  it("CTR caindo é piora, CPM caindo é melhora; pioras vêm primeiro", () => {
    const anterior = m({ gasto: 1000, impressoes: 50000, cliques: 1000, leads: 50 });
    const atual = m({ gasto: 1000, impressoes: 80000, cliques: 800, leads: 50 });
    const alertas = compararMetricas(atual, anterior);
    expect(alertas.map((a) => `${a.metrica}:${a.sentido}`)).toEqual(["ctrLink:piora", "cpm:melhora"]);
  });

  it("gasto sem nenhum lead no período atual é alerta, mesmo sem variação numérica", () => {
    const alertas = compararMetricas(m({ gasto: 500, impressoes: 1000 }), m({ gasto: 500, impressoes: 1000, leads: 10 }));
    expect(alertas[0]).toMatchObject({ metrica: "cpl", sentido: "piora", atual: null, anterior: 50 });
  });

  it("gasto abaixo do mínimo não gera alerta", () => {
    expect(compararMetricas(m({ gasto: 50, leads: 1 }), m({ gasto: 50, leads: 5 }))).toEqual([]);
  });

  it("corte de anúncio sem lead: o maior entre o piso e o CPL da conta", () => {
    expect(limiteSemLead(null)).toBe(30);
    expect(limiteSemLead(12)).toBe(30);
    expect(limiteSemLead(45.5)).toBe(45.5);
  });
});

describe("diagnostico_cliente (ferramenta)", () => {
  beforeEach(() => {
    novosModulos();
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-09-29T15:00:00Z")); // 12h em São Paulo
  });
  afterEach(() => vi.useRealTimers());

  const periodoDe = (params: Record<string, string>) => JSON.parse(params.time_range).since as string;

  function cenario(conjuntos: () => unknown = () => ({ data: [] })) {
    return simularMeta({
      "me/adaccounts": () => ({ data: [contaMeta("act_2", "DiCasa Italínea")] }),
      "act_2/insights": (p) => {
        if (p.level === "ad")
          return {
            data: [
              linhaInsights({ gasto: 120, impressoes: 8000, cliques: 40, extra: { ad_id: "a1", ad_name: "Vídeo antigo", campaign_name: "C", adset_name: "S" } }),
              linhaInsights({ gasto: 20, impressoes: 900, extra: { ad_id: "a2", ad_name: "Pouco gasto", campaign_name: "C", adset_name: "S" } }),
              linhaInsights({ gasto: 860, impressoes: 60000, cliques: 500, leads: 20, extra: { ad_id: "a3", ad_name: "Carrossel", campaign_name: "C", adset_name: "S" } }),
            ],
          };
        // Semana atual (22 a 28/09): CPL 50. Semana anterior (15 a 21/09): CPL 25.
        return periodoDe(p) === "2026-09-22"
          ? { data: [linhaInsights({ gasto: 1000, impressoes: 68900, cliques: 540, frequencia: 2.4, leads: 20 })] }
          : { data: [linhaInsights({ gasto: 1000, impressoes: 70000, cliques: 700, frequencia: 1.8, leads: 40 })] };
      },
      "act_2/adsets": conjuntos,
    });
  }

  it("compara as semanas certas no fuso da conta e aponta pioras e vazamentos", async () => {
    const meta = cenario(() => ({
      data: [
        { id: "s1", name: "Aberto", campaign: { name: "C" }, learning_stage_info: { status: "FAIL" } },
        { id: "s2", name: "Lookalike", learning_stage_info: { status: "LEARNING" } },
        { id: "s3", name: "Remarketing", learning_stage_info: { status: "SUCCESS" } },
      ],
    }));
    const r = await chamar("diagnostico_cliente", { conta: "dicasa" });
    expect(r.erro).toBe(false);
    const d = r.dados;

    expect(d.periodo).toEqual({
      atual: { inicio: "2026-09-22", fim: "2026-09-28" },
      anterior: { inicio: "2026-09-15", fim: "2026-09-21" },
    });
    expect(d.comparativo.cpl).toEqual({ atual: 50, anterior: 25, variacao_pct: 100 });
    expect(d.alertas.map((a: any) => a.metrica)).toEqual(["cpl", "frequencia", "ctrLink"]);
    expect(d.alertas.every((a: any) => a.sentido === "piora")).toBe(true);

    // Corte = CPL da conta (R$ 50): o de R$ 20 fica de fora; o que trouxe lead também.
    expect(d.anuncios_sem_lead.total).toBe(1);
    expect(d.anuncios_sem_lead.itens[0]).toMatchObject({ anuncio: "Vídeo antigo", gasto: 120 });

    expect(d.conjuntos).toMatchObject({ ativos: 3, em_aprendizado: 1, aprendizado_limitado: { total: 1 } });
    expect(d.conjuntos.aprendizado_limitado.itens[0]).toMatchObject({ nome: "Aberto", campanha: "C" });

    const adsets = meta.chamadas.find((c) => c.caminho === "act_2/adsets")!;
    expect(adsets.params.effective_status).toBe('["ACTIVE"]');
    expect(meta.chamadas.every((c) => c.metodo === "GET")).toBe(true);
  });

  it("se a Meta recusar os conjuntos, o resto do diagnóstico sai mesmo assim", async () => {
    cenario(() => erroMeta(100, "campo inválido"));
    const r = await chamar("diagnostico_cliente", { conta: "dicasa" });
    expect(r.erro).toBe(false);
    expect(r.dados.conjuntos.erro).toMatch(/Parâmetro inválido/);
    expect(r.dados.alertas.length).toBeGreaterThan(0);
  });

  it("período personalizado compara com o intervalo de mesmo tamanho logo antes", async () => {
    const meta = cenario();
    const r = await chamar("diagnostico_cliente", { conta: "act_2", inicio: "2026-08-01", fim: "2026-08-10" });
    expect(r.dados.periodo.anterior).toEqual({ inicio: "2026-07-22", fim: "2026-07-31" });
    const desdes = meta.chamadas.filter((c) => c.params.level === "account").map((c) => periodoDe(c.params));
    expect(desdes.sort()).toEqual(["2026-07-22", "2026-08-01"]);
  });

  it("recusa datas incompletas ou invertidas com mensagem clara", async () => {
    cenario();
    expect((await chamar("diagnostico_cliente", { conta: "dicasa", inicio: "2026-08-01" })).texto).toMatch(/juntos/);
    expect((await chamar("diagnostico_cliente", { conta: "dicasa", inicio: "2026-08-10", fim: "2026-08-01" })).texto).toMatch(/depois da final/);
  });
});
