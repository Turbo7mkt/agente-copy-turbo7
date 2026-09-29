import { z } from "zod";

export const PERIODOS = {
  hoje: "today",
  ontem: "yesterday",
  ultimos_7d: "last_7d",
  ultimos_14d: "last_14d",
  ultimos_30d: "last_30d",
  mes_atual: "this_month",
  mes_passado: "last_month",
} as const;

export const periodoSchema = z
  .enum(Object.keys(PERIODOS) as [keyof typeof PERIODOS, ...(keyof typeof PERIODOS)[]])
  .default("ultimos_7d")
  .describe("Período pré-definido (no fuso de cada conta). Ignorado se inicio e fim forem informados.");

export const dataSchema = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, "Use AAAA-MM-DD")
  .optional();

export function paramsPeriodo(periodo: keyof typeof PERIODOS, inicio?: string, fim?: string): Record<string, string> {
  if (inicio && fim) return { time_range: JSON.stringify({ since: inicio, until: fim }) };
  return { date_preset: PERIODOS[periodo] };
}

export type Intervalo = { inicio: string; fim: string }; // AAAA-MM-DD, inclusivo

const DIA = 86400000;
const paraData = (iso: string) => new Date(`${iso}T00:00:00Z`);
const paraIso = (d: Date) => d.toISOString().slice(0, 10);
const somarDias = (iso: string, dias: number) => paraIso(new Date(paraData(iso).getTime() + dias * DIA));
const diasEntre = (a: string, b: string) => Math.round((paraData(b).getTime() - paraData(a).getTime()) / DIA);
const ultimoDiaDoMes = (ano: number, mes0: number) => new Date(Date.UTC(ano, mes0 + 1, 0)).getUTCDate();
const iso = (ano: number, mes0: number, dia: number) => paraIso(new Date(Date.UTC(ano, mes0, dia)));

/** Data de hoje (AAAA-MM-DD) no fuso da conta, que é o fuso em que a Meta fecha os dias. */
export function hojeNoFuso(fuso: string, agora = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: fuso, year: "numeric", month: "2-digit", day: "2-digit" }).format(agora);
}

/** Converte o período em datas concretas, com a mesma semântica dos date_preset da Meta. */
export function intervaloDoPeriodo(periodo: keyof typeof PERIODOS, hoje: string): Intervalo {
  const [ano, mes] = hoje.split("-").map(Number);
  switch (periodo) {
    case "hoje":
      return { inicio: hoje, fim: hoje };
    case "ontem":
      return { inicio: somarDias(hoje, -1), fim: somarDias(hoje, -1) };
    case "ultimos_7d":
      return { inicio: somarDias(hoje, -7), fim: somarDias(hoje, -1) };
    case "ultimos_14d":
      return { inicio: somarDias(hoje, -14), fim: somarDias(hoje, -1) };
    case "ultimos_30d":
      return { inicio: somarDias(hoje, -30), fim: somarDias(hoje, -1) };
    case "mes_atual":
      return { inicio: iso(ano, mes - 1, 1), fim: hoje };
    case "mes_passado":
      return { inicio: iso(ano, mes - 2, 1), fim: iso(ano, mes - 2, ultimoDiaDoMes(ano, mes - 2)) };
  }
}

/**
 * Período anterior equivalente, para comparação justa.
 * - mês atual (dia 1 a N): os mesmos dias 1 a N do mês anterior (limitado ao fim do mês);
 * - mês passado: o mês inteiro antes dele;
 * - demais: o mesmo número de dias, imediatamente antes.
 */
export function periodoAnterior(atual: Intervalo, periodo?: keyof typeof PERIODOS): Intervalo {
  const [ano, mes, dia] = atual.inicio.split("-").map(Number);
  if (periodo === "mes_atual") {
    const diaFim = Number(atual.fim.slice(8));
    return { inicio: iso(ano, mes - 2, 1), fim: iso(ano, mes - 2, Math.min(diaFim, ultimoDiaDoMes(ano, mes - 2))) };
  }
  if (periodo === "mes_passado" && dia === 1) {
    return { inicio: iso(ano, mes - 2, 1), fim: iso(ano, mes - 2, ultimoDiaDoMes(ano, mes - 2)) };
  }
  const dias = diasEntre(atual.inicio, atual.fim) + 1;
  return { inicio: somarDias(atual.inicio, -dias), fim: somarDias(atual.inicio, -1) };
}

export const paramsIntervalo = (i: Intervalo) => ({ time_range: JSON.stringify({ since: i.inicio, until: i.fim }) });

export function avisoPeriodo(periodo: keyof typeof PERIODOS, fim?: string): string | undefined {
  const recente = fim
    ? Date.now() - new Date(fim).getTime() < 3 * 86400000
    : ["hoje", "ontem", "ultimos_7d", "ultimos_14d", "ultimos_30d", "mes_atual"].includes(periodo);
  return recente ? "Os últimos 1 a 3 dias ainda podem mudar (conversões atribuídas com atraso)." : undefined;
}
