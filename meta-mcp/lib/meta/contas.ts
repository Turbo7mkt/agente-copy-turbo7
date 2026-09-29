import { metaGetTodos, MetaApiError } from "./client";

export type Conta = {
  id: string; // act_...
  nome: string;
  status: string;
  moeda: string;
  fuso: string;
  empresa?: string;
};

const STATUS: Record<number, string> = {
  1: "ativa",
  2: "desativada",
  3: "pagamento pendente",
  7: "em análise de risco",
  8: "acerto pendente",
  9: "período de carência",
  100: "encerramento pendente",
  101: "encerrada",
  201: "ativa (sem uso)",
  202: "encerrada",
};

let cache: { em: number; contas: Conta[] } | null = null;
const TTL = 10 * 60 * 1000;

export async function listarContas(forcar = false): Promise<Conta[]> {
  if (!forcar && cache && Date.now() - cache.em < TTL) return cache.contas;
  const brutas = await metaGetTodos("me/adaccounts", {
    fields: "id,name,account_status,currency,timezone_name,business{name}",
    limit: "100",
  });
  const contas: Conta[] = brutas.map((c: any) => ({
    id: c.id,
    nome: c.name,
    status: STATUS[c.account_status] ?? `status ${c.account_status}`,
    moeda: c.currency,
    fuso: c.timezone_name,
    empresa: c.business?.name,
  }));
  contas.sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
  cache = { em: Date.now(), contas };
  return contas;
}

const normalizar = (s: string) =>
  s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();

/** Aceita act_123, 123 ou parte do nome da conta ("bs grajau"). */
export async function resolverConta(termo: string): Promise<Conta> {
  const contas = await listarContas();
  const t = termo.trim();
  const id = t.startsWith("act_") ? t : /^\d+$/.test(t) ? `act_${t}` : null;
  if (id) {
    const c = contas.find((x) => x.id === id);
    if (!c) throw new MetaApiError(`A conta ${id} não está acessível pelo usuário do sistema.`);
    return c;
  }
  const alvo = normalizar(t);
  const achadas = contas.filter((c) => normalizar(c.nome).includes(alvo));
  if (achadas.length === 1) return achadas[0];
  if (achadas.length === 0)
    throw new MetaApiError(`Nenhuma conta encontrada para "${termo}". Use listar_contas para ver os nomes.`);
  const exatas = achadas.filter((c) => normalizar(c.nome) === alvo);
  if (exatas.length === 1) return exatas[0];
  throw new MetaApiError(
    `"${termo}" corresponde a mais de uma conta: ${achadas.map((c) => `${c.nome} (${c.id})`).join("; ")}. Seja mais específico.`,
  );
}
