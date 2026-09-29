// Meta simulada: substitui o fetch global e responde como a Graph API, sem rede.
import { vi } from "vitest";

export type Chamada = { metodo: string; caminho: string; params: Record<string, string> };
type Resposta = { status?: number; corpo: unknown };
type Rota = (params: Record<string, string>) => Resposta | unknown;

/**
 * Registra respostas por caminho (sem a versão), ex.: "me/adaccounts" ou "act_1/insights".
 * A rota recebe os parâmetros da URL e devolve o corpo (ou { status, corpo }).
 * Uma lista de rotas é consumida em ordem, uma por chamada (útil para retry e paginação).
 */
export function simularMeta(rotas: Record<string, Rota | Rota[]>) {
  const chamadas: Chamada[] = [];
  const filas = new Map(Object.entries(rotas).map(([k, v]) => [k, Array.isArray(v) ? [...v] : v]));

  const fetchFalso = vi.fn(async (entrada: string | URL, init?: RequestInit) => {
    const url = new URL(String(entrada));
    const caminho = url.pathname.replace(/^\/v\d+\.\d+\//, "");
    const params = Object.fromEntries(url.searchParams);
    chamadas.push({ metodo: init?.method ?? "GET", caminho, params });

    const rota = filas.get(caminho);
    if (!rota) return json(404, { error: { message: `Rota não simulada: ${caminho}`, code: 803 } });
    const fn = Array.isArray(rota) ? rota.shift() : rota;
    if (!fn) return json(500, { error: { message: `Fila esgotada para ${caminho}`, code: 1 } });

    const r = fn(params) as Resposta;
    const temEnvelope = r && typeof r === "object" && "corpo" in r;
    return json(temEnvelope ? r.status ?? 200 : 200, temEnvelope ? r.corpo : r);
  });

  vi.stubGlobal("fetch", fetchFalso);
  return { chamadas, fetch: fetchFalso };
}

function json(status: number, corpo: unknown): Response {
  return new Response(JSON.stringify(corpo), { status, headers: { "content-type": "application/json" } });
}

export const erroMeta = (code: number, message = "erro simulado", status = 400) => ({
  status,
  corpo: { error: { message, code, type: "OAuthException" } },
});

/** Linha de insights no formato da Meta (números como string, ações em lista). */
export function linhaInsights(p: {
  gasto: number;
  impressoes?: number;
  cliques?: number;
  alcance?: number;
  frequencia?: number;
  conversas?: number;
  leads?: number;
  pixelLead?: number;
  extra?: Record<string, unknown>;
}) {
  const actions = [
    p.conversas !== undefined && { action_type: "onsite_conversion.messaging_conversation_started_7d", value: String(p.conversas) },
    p.leads !== undefined && { action_type: "lead", value: String(p.leads) },
    p.pixelLead !== undefined && { action_type: "offsite_conversion.fb_pixel_lead", value: String(p.pixelLead) },
  ].filter(Boolean);
  return {
    spend: String(p.gasto),
    impressions: String(p.impressoes ?? 0),
    reach: p.alcance !== undefined ? String(p.alcance) : undefined,
    frequency: p.frequencia !== undefined ? String(p.frequencia) : undefined,
    inline_link_clicks: String(p.cliques ?? 0),
    ...(actions.length ? { actions } : {}),
    ...p.extra,
  };
}

export const contaMeta = (id: string, nome: string, status = 1) => ({
  id,
  name: nome,
  account_status: status,
  currency: "BRL",
  timezone_name: "America/Sao_Paulo",
});
