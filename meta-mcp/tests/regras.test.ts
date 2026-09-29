import { describe, expect, it } from "vitest";
import { calcular, semaforoCpl } from "../lib/regras/metricas";
import { avisoPeriodo, paramsPeriodo } from "../lib/regras/periodo";
import { linhaInsights } from "./apoio/metaSimulada";

describe("calcular", () => {
  it("soma conversas e lead, sem contar o pixel em dobro", () => {
    const m = calcular(linhaInsights({ gasto: 300, impressoes: 10000, cliques: 150, conversas: 8, leads: 2, pixelLead: 2 }), "act_1");
    expect(m.leads).toBe(10);
    expect(m.conversas).toBe(8);
    expect(m.leadsOutros).toBe(2);
    expect(m.cpl).toBe(30);
    expect(m.ctrLink).toBe(1.5);
    expect(m.cpm).toBe(30);
  });

  it("linha vazia (conta sem entrega) vira zeros e nulos, sem NaN", () => {
    const m = calcular({}, "act_1");
    expect(m).toMatchObject({ gasto: 0, impressoes: 0, leads: 0, cpl: null, ctrLink: null, cpm: null });
  });

  it("arredonda em centavos", () => {
    expect(calcular(linhaInsights({ gasto: 100, leads: 3 }), "act_1").cpl).toBe(33.33);
  });
});

describe("semaforoCpl", () => {
  it("gasto sem lead é sem_lead, mesmo sem benchmark", () => {
    expect(semaforoCpl("act_1", calcular(linhaInsights({ gasto: 50 }), "act_1"))).toBe("sem_lead");
  });

  it("sem benchmark configurado não pinta cor", () => {
    expect(semaforoCpl("act_1", calcular(linhaInsights({ gasto: 50, leads: 2 }), "act_1"))).toBe("sem_benchmark");
  });
});

describe("período", () => {
  it("usa date_preset por padrão e time_range quando há início e fim", () => {
    expect(paramsPeriodo("ultimos_7d")).toEqual({ date_preset: "last_7d" });
    expect(paramsPeriodo("ultimos_7d", "2026-09-01", "2026-09-10")).toEqual({
      time_range: JSON.stringify({ since: "2026-09-01", until: "2026-09-10" }),
    });
  });

  it("avisa sobre dados recentes só quando o período toca os últimos dias", () => {
    expect(avisoPeriodo("ultimos_7d")).toBeDefined();
    expect(avisoPeriodo("mes_passado")).toBeUndefined();
    expect(avisoPeriodo("ultimos_7d", "2020-01-31")).toBeUndefined();
  });
});
