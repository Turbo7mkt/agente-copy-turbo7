import { LEAD_ACTIONS_PADRAO, CPL_PADRAO, POR_CONTA, type Faixas } from "../../config/turbo7";

export type Metricas = {
  gasto: number;
  impressoes: number;
  alcance?: number;
  frequencia?: number;
  cliquesLink: number;
  ctrLink: number | null; // %
  cpm: number | null;
  conversas: number;
  leadsOutros: number;
  leads: number;
  cpl: number | null;
};

const n = (v: unknown) => (v === undefined || v === null || v === "" ? 0 : Number(v));
const r2 = (v: number) => Math.round(v * 100) / 100;

function acao(actions: any[] | undefined, tipo: string): number {
  return n(actions?.find((a) => a.action_type === tipo)?.value);
}

export function leadActionsDaConta(contaId: string): string[] {
  return POR_CONTA[contaId]?.leadActions ?? LEAD_ACTIONS_PADRAO;
}

export function calcular(linha: any, contaId: string): Metricas {
  const gasto = n(linha.spend);
  const impressoes = n(linha.impressions);
  const cliquesLink = n(linha.inline_link_clicks);
  const tipos = leadActionsDaConta(contaId);
  const leads = tipos.reduce((s, t) => s + acao(linha.actions, t), 0);
  const conversas = acao(linha.actions, "onsite_conversion.messaging_conversation_started_7d");
  return {
    gasto: r2(gasto),
    impressoes,
    alcance: linha.reach !== undefined ? n(linha.reach) : undefined,
    frequencia: linha.frequency !== undefined ? r2(n(linha.frequency)) : undefined,
    cliquesLink,
    ctrLink: impressoes ? r2((cliquesLink / impressoes) * 100) : null,
    cpm: impressoes ? r2((gasto / impressoes) * 1000) : null,
    conversas,
    leadsOutros: leads - (tipos.includes("onsite_conversion.messaging_conversation_started_7d") ? conversas : 0),
    leads,
    cpl: leads ? r2(gasto / leads) : null,
  };
}

export type Semaforo = "verde" | "amarelo" | "vermelho" | "sem_lead" | "sem_benchmark";

export function semaforoCpl(contaId: string, m: Metricas): Semaforo {
  const faixas: Faixas | null = POR_CONTA[contaId]?.cpl ?? CPL_PADRAO;
  if (m.gasto > 0 && m.leads === 0) return "sem_lead";
  if (!faixas || m.cpl === null) return "sem_benchmark";
  if (m.cpl <= faixas.verdeAte) return "verde";
  if (m.cpl <= faixas.amareloAte) return "amarelo";
  return "vermelho";
}
