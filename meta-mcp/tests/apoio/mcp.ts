// Chama as ferramentas pelo protocolo MCP de verdade (JSON-RPC via handler), como o Claude faria.
import { vi } from "vitest";

let id = 0;

async function rpc(metodo: string, params?: unknown): Promise<any> {
  // Import dinâmico: cada teste recebe módulos novos (cache de contas zerado) após vi.resetModules().
  const { handler } = await import("../../lib/mcp/server");
  const res = await handler(
    new Request("http://localhost/mcp/teste", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        accept: "application/json, text/event-stream",
        "mcp-protocol-version": "2025-06-18",
      },
      body: JSON.stringify({ jsonrpc: "2.0", id: ++id, method: metodo, params }),
    }),
  );
  const texto = await res.text();
  const linha = texto.split("\n").find((l) => l.startsWith("data: "));
  const msg = JSON.parse(linha ? linha.slice(6) : texto);
  if (msg.error) throw new Error(`JSON-RPC ${msg.error.code}: ${msg.error.message}`);
  return msg.result;
}

export async function listarFerramentas() {
  return (await rpc("tools/list")).tools as any[];
}

/** Chama a ferramenta e devolve o JSON da resposta (ou o texto, se for erro). */
export async function chamar(nome: string, args: Record<string, unknown> = {}) {
  const r = await rpc("tools/call", { name: nome, arguments: args });
  const texto = r.content?.[0]?.text ?? "";
  return { erro: r.isError === true, texto, dados: r.isError ? undefined : JSON.parse(texto) };
}

export function novosModulos() {
  vi.resetModules();
}
