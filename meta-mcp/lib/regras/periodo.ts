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

export function avisoPeriodo(periodo: keyof typeof PERIODOS, fim?: string): string | undefined {
  const recente = fim
    ? Date.now() - new Date(fim).getTime() < 3 * 86400000
    : ["hoje", "ontem", "ultimos_7d", "ultimos_14d", "ultimos_30d", "mes_atual"].includes(periodo);
  return recente ? "Os últimos 1 a 3 dias ainda podem mudar (conversões atribuídas com atraso)." : undefined;
}
