// Único ponto de contato com a Meta: autenticação, paginação, retentativas e erros.

const API_VERSION = process.env.META_API_VERSION || "v25.0";
const BASE = `https://graph.facebook.com/${API_VERSION}`;

export class MetaApiError extends Error {
  constructor(message: string, public code?: number, public subcode?: number) {
    super(message);
    this.name = "MetaApiError";
  }
}

const RETENTAVEIS = new Set([1, 2, 4, 17, 32, 613, 80000, 80003, 80004, 80014]);

function token(): string {
  const t = process.env.META_ACCESS_TOKEN;
  if (!t) throw new MetaApiError("META_ACCESS_TOKEN não está configurado nas variáveis de ambiente do Vercel.");
  return t;
}

function traduzirErro(code: number | undefined, mensagem: string): string {
  if (code === 190) return "Token da Meta inválido ou expirado. Gere um novo token do usuário do sistema.";
  if (code === 10 || code === 200 || code === 283)
    return `Sem permissão para este recurso. Confirme se o usuário do sistema foi atribuído à conta. (Meta: ${mensagem})`;
  if (code === 17 || code === 80004 || code === 613) return "Limite de chamadas da Meta atingido para esta conta. Tente de novo em alguns minutos.";
  if (code === 100) return `Parâmetro inválido na chamada à Meta: ${mensagem}`;
  return `Erro da Meta${code ? ` (${code})` : ""}: ${mensagem}`;
}

const esperar = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function requisitar(url: string, tentativa = 0): Promise<any> {
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token()}` },
    cache: "no-store",
  });
  const corpo: any = await res.json().catch(() => ({}));
  if (res.ok && !corpo?.error) return corpo;

  const erro = corpo?.error ?? {};
  const code: number | undefined = erro.code;
  const retentavel = (code !== undefined && RETENTAVEIS.has(code)) || res.status >= 500;
  if (retentavel && tentativa < 3) {
    await esperar(1000 * 2 ** tentativa + Math.random() * 300);
    return requisitar(url, tentativa + 1);
  }
  throw new MetaApiError(traduzirErro(code, erro.message ?? `HTTP ${res.status}`), code, erro.error_subcode);
}

function montarUrl(caminho: string, params: Record<string, string | undefined>): string {
  const url = new URL(`${BASE}/${caminho.replace(/^\//, "")}`);
  for (const [k, v] of Object.entries(params)) if (v !== undefined) url.searchParams.set(k, v);
  return url.toString();
}

export async function metaGet(caminho: string, params: Record<string, string | undefined> = {}): Promise<any> {
  return requisitar(montarUrl(caminho, params));
}

/** Busca todas as páginas de uma lista (com teto de segurança). */
export async function metaGetTodos<T = any>(
  caminho: string,
  params: Record<string, string | undefined> = {},
  maxPaginas = 20,
): Promise<T[]> {
  const itens: T[] = [];
  let resposta = await metaGet(caminho, params);
  itens.push(...(resposta.data ?? []));
  let paginas = 1;
  while (resposta.paging?.next && paginas < maxPaginas) {
    resposta = await requisitar(resposta.paging.next);
    itens.push(...(resposta.data ?? []));
    paginas++;
  }
  return itens;
}
