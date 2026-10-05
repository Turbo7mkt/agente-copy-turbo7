/* Testa o linter que o PAINEL publica — não uma cópia dele.
 *
 * O painel (`docs/painel-artifact.html`) carrega uma porta em JavaScript do
 * `scripts/lint_copy.py`, porque no Artifact não roda Python. Duas
 * implementações da mesma regra divergem em silêncio: foi assim que a nota de
 * conformidade virou violação no painel depois de já estar corrigida no Python.
 *
 * Por isso este arquivo extrai o bloco do HTML e roda contra ele. Se alguém
 * editar o painel e quebrar uma regra, o teste cai.
 *
 * Uso:  node scripts/tests/test_lint_painel.mjs
 */
import { readFileSync, writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";

const RAIZ = fileURLToPath(new URL("../..", import.meta.url));
const html = readFileSync(join(RAIZ, "docs/painel-artifact.html"), "utf8");

const INICIO = 'const B = "(?<![\\\\wÀ-ÿ])"';
const FIM = "/* ---------- Render ---------- */";
const i = html.indexOf(INICIO), f = html.indexOf(FIM);
assert.ok(i !== -1 && f > i, "não achei o bloco do linter em docs/painel-artifact.html");

const modulo = join(mkdtempSync(join(tmpdir(), "lintpainel-")), "linter.mjs");
writeFileSync(modulo, html.slice(i, f) + "\nexport { lintar, corpoDaCopy, blocosDeCopy, linhasDeCopy };\n", "utf8");
const { lintar, corpoDaCopy, blocosDeCopy, linhasDeCopy } = await import("file://" + modulo);

let ok = 0;
const falhas = [];
const t = (nome, fn) => { try { fn(); ok++; } catch (e) { falhas.push(`${nome} → ${e.message}`); } };
const codigos = (txt, preco = false) => lintar(txt, preco).map((a) => a.codigo);

const NOTA = [
  "", "## Nota de conformidade", "",
  "- **Preço, parcela ou desconto:** `usa_preco: false`, nada disso entrou.",
  "- **Promessas evitadas:** excelência de atendimento, o melhor da região.",
  "- Nenhuma urgência artificial: sem últimas vagas, sem corre.", "",
].join("\n");

t("copy limpa não gera achado", () =>
  assert.deepEqual(codigos("Entregamos em 35 dias úteis com garantia de 5 anos.\n"), []));
t("pega urgência artificial", () =>
  assert.ok(codigos("Últimas vagas hoje.").includes("R2-urgencia")));
t("pega superlativo vazio", () =>
  assert.ok(codigos("Somos a melhor loja.").includes("R2-superlativo")));
t("pega clichê de mercado", () =>
  assert.ok(codigos("Realize o sonho da casa própria.").includes("R7-cliche")));
t("pega preço com usa_preco: false", () =>
  assert.ok(codigos("Cozinha por R$ 19.900.").includes("PRECO")));
t("preço liberado não vira PRECO", () =>
  assert.ok(!codigos("Cozinha por R$ 19.900.", true).includes("PRECO")));
t("ignora bloco de código", () =>
  assert.deepEqual(codigos("Copy limpa.\n\n```\nÚltimas vagas! R$ 19.900\n```\n\nFim limpo.\n"), []));
t("exige rodapé legal quando há preço", () =>
  assert.ok(codigos("Projeto completo por R$ 34.900.", true).includes("MARCA-rodape")));

/* --- Regressão: a nota declara o que foi evitado, e isso não é violação. --- */
t("nota de conformidade não gera violação", () =>
  assert.deepEqual(codigos("A gaveta que continua firme depois de anos.\n" + NOTA), []));
t("caso real Casa & Cozinha 29/09 — PRECO não dispara na nota", () =>
  assert.ok(!codigos("A gaveta que continua firme.\n" + NOTA).includes("PRECO")));
t("caso real Casa & Cozinha 29/09 — superlativo não dispara na nota", () =>
  assert.ok(!codigos("A gaveta que continua firme.\n" + NOTA).includes("R2-superlativo")));
t("violação ANTES da nota ainda pega", () => {
  const c = codigos("Somos a melhor loja! Últimas vagas.\n" + NOTA);
  assert.ok(c.includes("R2-superlativo") && c.includes("R2-urgencia"));
});
t("preço citado só na nota não exige rodapé", () =>
  assert.ok(!codigos(
    "Projeto sob medida.\n\n## Nota de conformidade\n\n- A tabela de R$ 34.900 ficou fora.\n",
    true).includes("MARCA-rodape")));
t("título da nota em qualquer nível", () => {
  for (const n of ["#", "##", "###"])
    assert.deepEqual(codigos(`Copy limpa.\n\n${n} Nota de conformidade\n\nSem excelência aqui.\n`), [], n);
});
t("número da linha continua certo com nota no fim", () =>
  assert.equal(lintar("um\ndois\nÚltimas vagas hoje\n" + NOTA, false)[0].linha, 3));
t("corpoDaCopy corta na nota", () =>
  assert.equal(corpoDaCopy("copy\n\n## Nota de conformidade\n\nexcelência\n"), "copy\n"));

/* --- Limites de tamanho: o Meta trunca, e copy cortada não vende. --- */
t("título curto passa", () =>
  assert.ok(!codigos("**Título:** Comece por um ambiente", true).includes("TAMANHO-titulo")));
t("caso real Mhavi 05/10 — título de 55 caracteres reprova", () =>
  assert.ok(codigos("**Título:** Comece por um ambiente. A casa inteira agradece depois.", true).includes("TAMANHO-titulo")));
t("título não conta a marcação", () =>
  assert.ok(!codigos("**Título:** **Projeto que cabe no seu prazo**", true).includes("TAMANHO-titulo")));
t("caso real Mhavi 05/10 — descrição de 50 caracteres reprova", () =>
  assert.ok(codigos("**Descrição:** Valor fechado por metragem · Showroom em São Paulo", true).includes("TAMANHO-descricao")));
t("descrição curta passa", () =>
  assert.ok(!codigos("**Descrição:** Showroom em SP", true).includes("TAMANHO-descricao")));
t("copy curta passa", () =>
  assert.ok(!codigos("A gaveta que continua firme depois de anos.").includes("TAMANHO-copy")));
t("caso real Mhavi 05/10 — três parágrafos de ~300 somam e reprovam", () => {
  const par = "Frase que ocupa espaço sem chamar atenção por si. ".repeat(3);
  assert.ok(codigos(`## ÂNGULO — teste\n\n${par}\n\n${par}\n\n${par}\n`).includes("TAMANHO-copy"));
});
t("cada cabeçalho tem seu próprio orçamento", () => {
  const curta = "Uma dor, uma prova, um CTA. Venha nos fazer uma visita.";
  let texto = "";
  for (let n = 1; n <= 10; n++) texto += `## ÂNGULO ${n}\n\n${curta}\n\n`;
  assert.ok(!codigos(texto).includes("TAMANHO-copy"));
});
t("a nota de conformidade não conta no tamanho", () =>
  assert.ok(!codigos("Copy curta e limpa.\n\n## Nota de conformidade\n\n" + "explicação longa ".repeat(60)).includes("TAMANHO-copy")));
t("blocosDeCopy tira rótulo e metadado", () =>
  assert.deepEqual(
    blocosDeCopy(linhasDeCopy("**SOLUÇÃO**\n\n**Gatilho:** Desejo\n\nO texto.\n")).map((b) => b[1]),
    ["O texto."]));
t("blocosDeCopy junta parágrafos do mesmo cabeçalho", () =>
  assert.deepEqual(
    blocosDeCopy(linhasDeCopy("## A\n\num\n\ndois\n")).map((b) => b[1]), ["um dois"]));

console.log(`${ok} passaram, ${falhas.length} falharam`);
for (const f of falhas) console.log("  ✗ " + f);
process.exit(falhas.length ? 1 : 0);
