import { beforeEach, describe, expect, it } from "vitest";
import { contaMeta, erroMeta, linhaInsights, simularMeta } from "./apoio/metaSimulada";
import { chamar, listarFerramentas, novosModulos } from "./apoio/mcp";

beforeEach(novosModulos);

const CONTAS = {
  "me/adaccounts": () => ({
    data: [
      contaMeta("act_1", "BS Grajaú Italínea"),
      contaMeta("act_2", "DiCasa Italínea"),
      contaMeta("act_3", "Preemier Decore Italínea"),
      contaMeta("act_4", "Loja Sem Verba"),
      contaMeta("act_9", "Loja Encerrada", 101),
    ],
  }),
};

describe("protocolo", () => {
  it("toda ferramenta é somente leitura e tem descrição", async () => {
    const ferramentas = await listarFerramentas();
    expect(ferramentas.length).toBeGreaterThanOrEqual(3);
    for (const f of ferramentas) {
      expect(f.annotations?.readOnlyHint, f.name).toBe(true);
      expect(f.description, f.name).toBeTruthy();
    }
  });
});

describe("listar_contas", () => {
  it("filtra por parte do nome", async () => {
    simularMeta(CONTAS);
    const r = await chamar("listar_contas", { filtro: "italínea" });
    expect(r.dados.total).toBe(3);
  });
});

describe("desempenho_conta", () => {
  it("pede o nível certo, ordena por gasto e respeita o limite", async () => {
    const meta = simularMeta({
      ...CONTAS,
      "act_2/insights": () => ({
        data: [
          linhaInsights({ gasto: 100, leads: 5, extra: { campaign_id: "c1", campaign_name: "Leads" } }),
          linhaInsights({ gasto: 400, conversas: 10, extra: { campaign_id: "c2", campaign_name: "Mensagens" } }),
          linhaInsights({ gasto: 50, extra: { campaign_id: "c3", campaign_name: "Alcance" } }),
        ],
      }),
    });
    const r = await chamar("desempenho_conta", { conta: "dicasa", periodo: "mes_passado", limite: 2 });
    expect(r.erro).toBe(false);
    expect(r.dados.itens.map((i: any) => i.campanha)).toEqual(["Mensagens", "Leads"]);
    expect(r.dados.linhas_total).toBe(3);
    const insights = meta.chamadas.find((c) => c.caminho === "act_2/insights")!;
    expect(insights.params).toMatchObject({ level: "campaign", date_preset: "last_month", use_unified_attribution_setting: "true" });
  });

  it("conta desconhecida devolve erro acionável", async () => {
    simularMeta(CONTAS);
    const r = await chamar("desempenho_conta", { conta: "inexistente" });
    expect(r.erro).toBe(true);
    expect(r.texto).toMatch(/listar_contas/);
  });
});

describe("resumo_carteira", () => {
  it("ordena do pior CPL ao melhor, separa sem gasto e erros, ignora encerradas", async () => {
    const meta = simularMeta({
      ...CONTAS,
      "act_1/insights": () => ({ data: [linhaInsights({ gasto: 300, leads: 10 })] }), // CPL 30
      "act_2/insights": () => ({ data: [linhaInsights({ gasto: 200, conversas: 2 })] }), // CPL 100
      "act_3/insights": () => erroMeta(10, "sem permissão"),
      "act_4/insights": () => ({ data: [] }),
    });
    const r = await chamar("resumo_carteira", { periodo: "ultimos_7d" });
    expect(r.dados.contas.map((c: any) => c.conta)).toEqual(["DiCasa Italínea", "BS Grajaú Italínea"]);
    expect(r.dados.totais).toEqual({ contas_com_gasto: 2, gasto: 500, leads: 12, cpl_medio: 41.67 });
    expect(r.dados.sem_gasto).toEqual(["Loja Sem Verba"]);
    expect(r.dados.erros).toHaveLength(1);
    expect(r.dados.erros[0].erro).toMatch(/usuário do sistema/);
    expect(r.dados.aviso).toBeDefined();
    expect(meta.chamadas.some((c) => c.caminho === "act_9/insights")).toBe(false);
  });
});

describe("segurança", () => {
  it("nenhuma ferramenta faz chamada que não seja GET", async () => {
    const meta = simularMeta({
      ...CONTAS,
      "act_1/insights": () => ({ data: [linhaInsights({ gasto: 10, leads: 1 })] }),
      "act_2/insights": () => ({ data: [] }),
      "act_3/insights": () => ({ data: [] }),
      "act_4/insights": () => ({ data: [] }),
    });
    await chamar("listar_contas");
    await chamar("desempenho_conta", { conta: "act_1" });
    await chamar("resumo_carteira");
    expect(meta.chamadas.length).toBeGreaterThan(0);
    expect(meta.chamadas.every((c) => c.metodo === "GET")).toBe(true);
  });
});
