/* Testa o corte da entrega em peças — o que decide quantas linhas entram na
 * `BASE_CRIATIVOS`.
 *
 * Como em test_lint_painel.mjs, o código vem do HTML que o painel PUBLICA,
 * não de uma cópia: implementação duplicada diverge em silêncio.
 *
 * Uso:  node scripts/tests/test_fatiar_entrega.mjs
 */
import { readFileSync, writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";

const RAIZ = fileURLToPath(new URL("../..", import.meta.url));
const html = readFileSync(join(RAIZ, "docs/painel-artifact.html"), "utf8");

function recortar(inicio, fim) {
  const i = html.indexOf(inicio);
  const f = html.indexOf(fim, i + 1);
  assert.ok(i !== -1 && f > i, `não achei o bloco ${inicio.slice(0, 40)}`);
  return html.slice(i, f);
}

// `fatiarEntrega` usa `corpoDaCopy`, que mora no bloco do linter.
const bloco =
  recortar('const B = "(?<![\\\\wÀ-ÿ])"', "/* ---------- Render ---------- */") +
  recortar("/* ---------- Fatiar a entrega em peças ---------- */", "/* ---------- Gravação na planilha ---------- */");

const modulo = join(mkdtempSync(join(tmpdir(), "fatiar-")), "fatiar.mjs");
writeFileSync(modulo, bloco + "\nexport { fatiarEntrega, tipoDaPeca };\n", "utf8");
const { fatiarEntrega, tipoDaPeca } = await import("file://" + modulo);

let ok = 0;
const falhas = [];
const t = (nome, fn) => { try { fn(); ok++; } catch (e) { falhas.push(`${nome} → ${e.message}`); } };
const tipos = (md, padrao = "Vídeo") => fatiarEntrega(md).map((p) => tipoDaPeca(p, padrao));

/* --- Quantas peças --- */

t("entrega de uma copy só vira uma peça", () => {
  const md = "# Mhavi — 2026-10-05\n\n## ÂNGULO — Começa por um ambiente\n\nO texto da copy.\n";
  assert.equal(fatiarEntrega(md).length, 1);
});

t("sem cabeçalho nenhum, a entrega inteira é uma peça", () =>
  assert.equal(fatiarEntrega("Só o texto corrido, sem título.\n").length, 1));

t("dez ângulos viram dez peças", () => {
  let md = "# Loja — 2026-10-05\n\n";
  for (let n = 1; n <= 10; n++) md += `## ÂNGULO ${n} — tema ${n}\n\nTexto da peça ${n}.\n\n`;
  assert.equal(fatiarEntrega(md).length, 10);
});

t("corta no nível mais fundo: 4 vídeos dentro de 1 ângulo são 4 peças", () => {
  const md = "# Loja\n\n## ÂNGULO 1 — tema\n\n### Vídeo 1\n\na\n\n### Vídeo 2\n\nb\n\n### Vídeo 3\n\nc\n\n### Vídeo 4\n\nd\n";
  assert.equal(fatiarEntrega(md).length, 4);
});

t("a nota de conformidade não vira peça", () => {
  const md = "# Loja\n\n## ÂNGULO 1\n\na\n\n## ÂNGULO 2\n\nb\n\n## Nota de conformidade\n\n- bala\n";
  const pecas = fatiarEntrega(md);
  assert.equal(pecas.length, 2);
  assert.ok(!pecas.some((p) => /conformidade/i.test(p.titulo)));
});

t("o título do documento não vira peça", () => {
  const md = "# Loja — 2026-10-05\n\n> procedência\n\n## ÂNGULO 1\n\na\n";
  assert.deepEqual(fatiarEntrega(md).map((p) => p.titulo), ["ÂNGULO 1"]);
});

t("cada peça leva o próprio texto, com o cabeçalho", () => {
  const pecas = fatiarEntrega("# L\n\n## A\n\nprimeiro\n\n## B\n\nsegundo\n");
  assert.ok(pecas[0].texto.includes("primeiro") && !pecas[0].texto.includes("segundo"));
  assert.ok(pecas[1].texto.startsWith("## B"));
});

/* --- Que tipo de criativo --- */

t("carrossel é reconhecido", () =>
  assert.deepEqual(tipos("## Carrossel — 5 cards\n\nCard 1: abre.\n"), ["Carrossel"]));

t("carrossel vence vídeo quando os dois aparecem", () =>
  assert.deepEqual(tipos("## Carrossel\n\nCard 1 com roteiro de vídeo.\n"), ["Carrossel"]));

t("roteiro de vídeo é reconhecido", () =>
  assert.deepEqual(tipos("## ÂNGULO 1\n\n✦ GANCHO FORTE: para o scroll.\n"), ["Vídeo"]));

t("imagem estática é reconhecida", () =>
  assert.deepEqual(tipos("## ÂNGULO 8 — imagem\n\nHEADLINE: frase curta.\n"), ["Foto"]));

t("sem pista, usa o padrão da configuração", () =>
  assert.deepEqual(tipos("## ÂNGULO 1\n\nTexto neutro sem pista alguma.\n", "Foto"), ["Foto"]));

t("a distribuição de 10 copies sai como 7 vídeo, 2 foto, 1 carrossel", () => {
  let md = "# Loja\n\n";
  for (let n = 1; n <= 7; n++) md += `## ÂNGULO ${n}\n\n✦ GANCHO FORTE: abre o vídeo.\n\n`;
  for (let n = 8; n <= 9; n++) md += `## ÂNGULO ${n}\n\nHEADLINE: frase curta.\n\n`;
  md += "## ÂNGULO 10\n\nCarrossel em 5 cards.\n";
  const conta = tipos(md).reduce((a, t) => ({ ...a, [t]: (a[t] || 0) + 1 }), {});
  assert.deepEqual(conta, { "Vídeo": 7, "Foto": 2, "Carrossel": 1 });
});

console.log(`${ok} passaram, ${falhas.length} falharam`);
for (const f of falhas) console.log("  ✗ " + f);
process.exit(falhas.length ? 1 : 0);
