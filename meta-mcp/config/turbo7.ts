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

/** Exceções por conta (chave = act_...). */
export const POR_CONTA: Record<string, { leadActions?: string[]; cpl?: Faixas }> = {
  // "act_000000000": { cpl: { verdeAte: 25, amareloAte: 40 } },
};
