// Regras do diagnóstico de um cliente: o que mudou contra o período anterior e onde a verba vaza.
import { DIAGNOSTICO } from "../../config/turbo7";
import type { Metricas } from "./metricas";

type MetricaComparada = "cpl" | "cpm" | "ctrLink" | "frequencia";

/** Para cada métrica, qual direção é ruim. CTR que cai é ruim; o resto, subir é ruim. */
const PIORA_QUANDO: Record<MetricaComparada, "sobe" | "cai"> = { cpl: "sobe", cpm: "sobe", ctrLink: "cai", frequencia: "sobe" };

const LEITURA: Record<MetricaComparada, { piora: string; melhora: string }> = {
  cpl: { piora: "Cada lead ficou mais caro.", melhora: "Cada lead ficou mais barato." },
  cpm: { piora: "Mil impressões ficaram mais caras (leilão ou público mais disputado).", melhora: "Mil impressões ficaram mais baratas." },
  ctrLink: { piora: "Menos gente clica: sinal de criativo cansado ou desalinhado ao público.", melhora: "Mais gente clica no anúncio." },
  frequencia: { piora: "O mesmo público está vendo o anúncio mais vezes: risco de saturação.", melhora: "O anúncio está chegando a gente nova." },
};

export type Alerta = {
  metrica: MetricaComparada;
  sentido: "piora" | "melhora";
  atual: number | null;
  anterior: number | null;
  variacao_pct: number | null;
  leitura: string;
};

const r1 = (v: number) => Math.round(v * 10) / 10;

export function variacaoPct(atual: number | null | undefined, anterior: number | null | undefined): number | null {
  if (atual == null || anterior == null || anterior === 0) return null;
  return r1(((atual - anterior) / anterior) * 100);
}

/**
 * Compara as métricas do período atual com o anterior e devolve só as variações relevantes,
 * pioras primeiro e as maiores antes. Abaixo do gasto mínimo em qualquer período, não há alerta.
 */
export function compararMetricas(atual: Metricas, anterior: Metricas, regras = DIAGNOSTICO): Alerta[] {
  if (atual.gasto < regras.gastoMinimo || anterior.gasto < regras.gastoMinimo) return [];

  const alertas: Alerta[] = [];
  for (const metrica of Object.keys(PIORA_QUANDO) as MetricaComparada[]) {
    const a = atual[metrica] ?? null;
    const b = anterior[metrica] ?? null;

    // CPL: o caso sem lead não tem variação numérica, mas é o alerta mais importante.
    if (metrica === "cpl" && a === null && b !== null) {
      alertas.push({ metrica, sentido: "piora", atual: a, anterior: b, variacao_pct: null, leitura: "Houve gasto e nenhum lead no período." });
      continue;
    }
    if (metrica === "cpl" && a !== null && b === null) {
      alertas.push({ metrica, sentido: "melhora", atual: a, anterior: b, variacao_pct: null, leitura: "Voltou a gerar leads; no período anterior não houve nenhum." });
      continue;
    }

    const pct = variacaoPct(a, b);
    if (pct === null || Math.abs(pct) < regras.variacaoMinimaPct[metrica]) continue;
    const subiu = pct > 0;
    const sentido = subiu === (PIORA_QUANDO[metrica] === "sobe") ? "piora" : "melhora";
    alertas.push({ metrica, sentido, atual: a, anterior: b, variacao_pct: pct, leitura: LEITURA[metrica][sentido] });
  }

  const peso = (x: Alerta) => (x.sentido === "piora" ? 0 : 1);
  return alertas.sort((x, y) => peso(x) - peso(y) || Math.abs(y.variacao_pct ?? Infinity) - Math.abs(x.variacao_pct ?? Infinity));
}

/** Gasto a partir do qual um anúncio sem lead entra na lista: max(piso, CPL da conta). */
export function limiteSemLead(cplConta: number | null, regras = DIAGNOSTICO): number {
  return Math.max(regras.semLeadGastoMinimo, cplConta ?? 0);
}

export function avisoGastoBaixo(atual: Metricas, anterior: Metricas, regras = DIAGNOSTICO): string | undefined {
  if (atual.gasto >= regras.gastoMinimo && anterior.gasto >= regras.gastoMinimo) return undefined;
  return `Gasto abaixo de R$ ${regras.gastoMinimo} em um dos períodos: variações não geram alerta.`;
}
