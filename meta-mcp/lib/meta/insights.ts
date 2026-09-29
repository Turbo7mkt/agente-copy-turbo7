import { metaGetTodos } from "./client";

export type Nivel = "conta" | "campanha" | "conjunto" | "anuncio";

const LEVEL: Record<Nivel, string> = { conta: "account", campanha: "campaign", conjunto: "adset", anuncio: "ad" };

const CAMPOS_BASE = ["spend", "impressions", "reach", "frequency", "inline_link_clicks", "actions"];
const CAMPOS_NIVEL: Record<Nivel, string[]> = {
  conta: [],
  campanha: ["campaign_id", "campaign_name"],
  conjunto: ["campaign_name", "adset_id", "adset_name"],
  anuncio: ["campaign_name", "adset_name", "ad_id", "ad_name"],
};

export async function buscarInsights(contaId: string, nivel: Nivel, periodo: Record<string, string>) {
  return metaGetTodos(`${contaId}/insights`, {
    level: LEVEL[nivel],
    fields: [...CAMPOS_BASE, ...CAMPOS_NIVEL[nivel]].join(","),
    // Usa a configuração de atribuição de cada conjunto, igual ao Gerenciador de Anúncios.
    use_unified_attribution_setting: "true",
    limit: "200",
    ...periodo,
  });
}
