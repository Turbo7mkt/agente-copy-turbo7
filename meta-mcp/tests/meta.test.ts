import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { contaMeta, erroMeta, simularMeta } from "./apoio/metaSimulada";
import { novosModulos } from "./apoio/mcp";

beforeEach(novosModulos);
afterEach(() => vi.useRealTimers());

const client = () => import("../lib/meta/client");
const contas = () => import("../lib/meta/contas");

describe("client", () => {
  it("manda o token no cabeçalho, nunca na URL", async () => {
    const meta = simularMeta({ "me/adaccounts": () => ({ data: [] }) });
    await (await client()).metaGet("me/adaccounts");
    const [url, init] = meta.fetch.mock.calls[0];
    expect(String(url)).not.toContain("token-de-teste");
    expect((init!.headers as Record<string, string>).Authorization).toBe("Bearer token-de-teste");
  });

  it("segue a paginação até o fim", async () => {
    simularMeta({
      "act_1/ads": [
        () => ({ data: [{ id: "1" }], paging: { next: "https://graph.facebook.com/v25.0/act_1/ads?after=x" } }),
        () => ({ data: [{ id: "2" }] }),
      ],
    });
    expect(await (await client()).metaGetTodos("act_1/ads")).toEqual([{ id: "1" }, { id: "2" }]);
  });

  it("tenta de novo em limite de chamadas e depois funciona", async () => {
    vi.useFakeTimers();
    const meta = simularMeta({ "me/adaccounts": [() => erroMeta(17), () => ({ data: [{ id: "a" }] })] });
    const p = (await client()).metaGet("me/adaccounts");
    await vi.runAllTimersAsync();
    expect((await p).data).toHaveLength(1);
    expect(meta.chamadas).toHaveLength(2);
  });

  it("desiste após 3 retentativas com mensagem em português", async () => {
    vi.useFakeTimers();
    const meta = simularMeta({ "me/adaccounts": () => erroMeta(17) });
    const p = (await client()).metaGet("me/adaccounts");
    const verificacao = expect(p).rejects.toThrow(/Limite de chamadas/);
    await vi.runAllTimersAsync();
    await verificacao;
    expect(meta.chamadas).toHaveLength(4);
  });

  it("token expirado não é retentado e diz o que fazer", async () => {
    const meta = simularMeta({ "me/adaccounts": () => erroMeta(190) });
    await expect((await client()).metaGet("me/adaccounts")).rejects.toThrow(/Gere um novo token/);
    expect(meta.chamadas).toHaveLength(1);
  });
});

describe("contas", () => {
  const carteira = () =>
    simularMeta({
      "me/adaccounts": () => ({
        data: [
          contaMeta("act_1", "BS Grajaú Italínea"),
          contaMeta("act_2", "DiCasa Italínea"),
          contaMeta("act_3", "DiCasa Italínea Filial"),
          contaMeta("act_4", "Loja Encerrada", 101),
        ],
      }),
    });

  it("acha pelo nome sem acento e sem caixa", async () => {
    carteira();
    expect((await (await contas()).resolverConta("bs grajau")).id).toBe("act_1");
  });

  it("acha por ID numérico ou act_", async () => {
    carteira();
    const { resolverConta } = await contas();
    expect((await resolverConta("2")).nome).toBe("DiCasa Italínea");
    expect((await resolverConta("act_3")).nome).toBe("DiCasa Italínea Filial");
  });

  it("nome exato desempata; parcial ambíguo pede para ser específico", async () => {
    carteira();
    const { resolverConta } = await contas();
    expect((await resolverConta("dicasa italinea")).id).toBe("act_2");
    await expect(resolverConta("dicasa")).rejects.toThrow(/mais de uma conta/);
  });

  it("usa cache de 10 minutos", async () => {
    const meta = carteira();
    const { listarContas } = await contas();
    await listarContas();
    await listarContas();
    expect(meta.chamadas).toHaveLength(1);
    await listarContas(true);
    expect(meta.chamadas).toHaveLength(2);
  });
});
