import { timingSafeEqual } from "node:crypto";
import { handler } from "../../../lib/mcp/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

function autorizado(chave: string): boolean {
  const esperado = process.env.MCP_ACCESS_KEY;
  if (!esperado || esperado.length < 32) return false;
  const a = Buffer.from(chave);
  const b = Buffer.from(esperado);
  return a.length === b.length && timingSafeEqual(a, b);
}

async function rota(req: Request, ctx: { params: Promise<{ chave: string }> }) {
  const { chave } = await ctx.params;
  if (!autorizado(chave)) return new Response("Not found", { status: 404 });
  return handler(req);
}

export { rota as GET, rota as POST, rota as DELETE };
