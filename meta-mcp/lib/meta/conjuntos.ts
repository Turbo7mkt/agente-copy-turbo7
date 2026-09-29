import { metaGetTodos } from "./client";

export type FaseAprendizado = "aprendendo" | "aprendizado_limitado" | "concluido" | "desconhecida";

export type Conjunto = {
  id: string;
  nome: string;
  campanha?: string;
  fase: FaseAprendizado;
};

// learning_stage_info.status da Meta: LEARNING, SUCCESS ou FAIL ("Aprendizado limitado" no Gerenciador).
const FASE: Record<string, FaseAprendizado> = { LEARNING: "aprendendo", FAIL: "aprendizado_limitado", SUCCESS: "concluido" };

/** Conjuntos em veiculação agora, com a fase de aprendizado. */
export async function buscarConjuntosAtivos(contaId: string): Promise<Conjunto[]> {
  const brutos = await metaGetTodos(`${contaId}/adsets`, {
    fields: "id,name,campaign{name},learning_stage_info",
    effective_status: JSON.stringify(["ACTIVE"]),
    limit: "200",
  });
  return brutos.map((c: any) => ({
    id: c.id,
    nome: c.name,
    campanha: c.campaign?.name,
    fase: FASE[c.learning_stage_info?.status] ?? "desconhecida",
  }));
}
