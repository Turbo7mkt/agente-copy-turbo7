// Regras da Turbo7. Edite aqui: definição de lead e benchmarks.

/**
 * O que conta como lead por padrão (somados).
 * - conversas iniciadas por mensagem (WhatsApp/Direct/Messenger)
 * - "lead": total de leads (formulário nativo + pixel), já consolidado pela Meta
 * Não incluir offsite_conversion.fb_pixel_lead junto com "lead" (conta em dobro).
 */
export const LEAD_ACTIONS_PADRAO = [
  "onsite_conversion.messaging_conversation_started_7d",
  "lead",
];

export type Faixas = { verdeAte: number; amareloAte: number }; // acima de amareloAte = vermelho

/** Benchmark padrão de CPL em R$. null = sem semáforo até definirmos. */
export const CPL_PADRAO: Faixas | null = null;

/**
 * Regras do diagnostico_cliente. Valores iniciais, a calibrar com o time de tráfego.
 * - variacaoMinimaPct: variação (em %) contra o período anterior para virar alerta.
 * - gastoMinimo: abaixo disso (R$) em qualquer um dos períodos, a comparação é ruído e não gera alerta.
 * - semLeadGastoMinimo: piso (R$) para um anúncio sem lead entrar na lista. O critério real é
 *   max(piso, CPL da conta no período): o anúncio gastou um lead inteiro e não trouxe nenhum.
 */
export const DIAGNOSTICO = {
  variacaoMinimaPct: { cpl: 20, cpm: 20, ctrLink: 20, frequencia: 15 },
  gastoMinimo: 100,
  semLeadGastoMinimo: 30,
};

/** Exceções por conta (chave = act_...). */
export const POR_CONTA: Record<string, { leadActions?: string[]; cpl?: Faixas }> = {
  // "act_000000000": { cpl: { verdeAte: 25, amareloAte: 40 } },
};
