/* Testa a geração de `ID do Criativo` do Apps Script que grava na planilha.
 *
 * O script roda dentro do Google, onde não há como rodar teste. Então aqui ele
 * é carregado como texto, com as APIs do Sheets dubladas, e as funções puras
 * são exercitadas contra os IDs reais que existem hoje em BASE_CRIATIVOS.
 *
 * Uso:  node scripts/tests/test_gravar_copy.mjs
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";

const RAIZ = fileURLToPath(new URL("../..", import.meta.url));
const fonte = readFileSync(RAIZ + "scripts/planilha/gravar-copy.gs", "utf8");

// As APIs do Google só são tocadas dentro das funções, então basta existirem.
const escopo = { SpreadsheetApp: {}, PropertiesService: {}, LockService: {}, Utilities: {}, Logger: {}, ContentService: {} };
const fabricar = new Function(
  ...Object.keys(escopo),
  fonte + "\nreturn { proximoId, iniciais, normalizar, COL };"
);
const { proximoId, iniciais, normalizar, COL } = fabricar(...Object.values(escopo));

/** Dubla a aba: `linhas` é [[Cliente, …, ID do Criativo], …] a partir da linha 2. */
function abaFalsa(linhas) {
  const largura = COL.id - COL.cliente + 1;
  return {
    getLastRow: () => linhas.length + 1,
    getRange: () => ({
      getValues: () =>
        linhas.map((l) => {
          const cheia = new Array(largura).fill("");
          cheia[0] = l.cliente;
          cheia[COL.id - COL.cliente] = l.id;
          return cheia;
        }),
    }),
  };
}

let ok = 0;
const falhas = [];
const t = (nome, fn) => { try { fn(); ok++; } catch (e) { falhas.push(`${nome} → ${e.message}`); } };

/* --- iniciais: o prefixo de um cliente que ainda não tem linha --- */
t("iniciais ignoram & e preposições", () =>
  assert.equal(iniciais("CASA & COZINHA ITALÍNEA"), "CCI"));
t("iniciais de nome simples", () =>
  assert.equal(iniciais("DECORALLE"), "D"));
t("iniciais respeitam acento", () =>
  assert.equal(iniciais("ATLÂNTICA ITALÍNEA"), "AI"));
t("iniciais cortam em 4 letras", () =>
  assert.equal(iniciais("UM DOIS TRES QUATRO CINCO SEIS"), "UDTQ"));
t("iniciais nunca voltam vazias", () =>
  assert.equal(iniciais("123"), "XX"));

/* --- normalizar: o casamento de cliente tolera espaço duplo e caixa --- */
t("normalizar colapsa espaço duplo", () =>
  assert.equal(normalizar("DIANA PLANEJADOS  ITALÍNEA"), "DIANA PLANEJADOS ITALÍNEA"));

/* --- proximoId: os IDs reais da planilha em 29/09 --- */
t("continua a sequência do cliente", () =>
  assert.equal(proximoId(abaFalsa([
    { cliente: "ATLÂNTICA ITALÍNEA", id: "AI0001" },
    { cliente: "ATLÂNTICA ITALÍNEA", id: "AI0004" },
    { cliente: "CAMMINARE ITALÍNEA", id: "CI0001" },
  ]), "ATLÂNTICA ITALÍNEA"), "AI0005"));

t("não mistura a sequência de outro cliente", () =>
  assert.equal(proximoId(abaFalsa([
    { cliente: "ATLÂNTICA ITALÍNEA", id: "AI0009" },
    { cliente: "CAMMINARE ITALÍNEA", id: "CI0002" },
  ]), "CAMMINARE ITALÍNEA"), "CI0003"));

t("aceita ID com espaço, como DP 0013", () =>
  assert.equal(proximoId(abaFalsa([
    { cliente: "DIANA PLANEJADOS  ITALÍNEA", id: "DP 0013" },
    { cliente: "DIANA PLANEJADOS  ITALÍNEA", id: "DP 0016" },
  ]), "DIANA PLANEJADOS ITALÍNEA"), "DP0017"));

t("cliente sem linha nenhuma começa em 0001 com as iniciais", () =>
  assert.equal(proximoId(abaFalsa([
    { cliente: "ATLÂNTICA ITALÍNEA", id: "AI0001" },
  ]), "CASA & COZINHA ITALÍNEA"), "CCI0001"));

t("planilha vazia também começa em 0001", () =>
  assert.equal(proximoId(abaFalsa([]), "DECORALLE"), "D0001"));

t("preserva a largura quando o ID tem mais dígitos", () =>
  assert.equal(proximoId(abaFalsa([
    { cliente: "MOVEL MAX", id: "MM00042" },
  ]), "MOVEL MAX"), "MM00043"));

t("ignora linha do cliente sem ID preenchido", () =>
  assert.equal(proximoId(abaFalsa([
    { cliente: "NOVA DESIGN", id: "ND0012" },
    { cliente: "NOVA DESIGN", id: "" },
  ]), "NOVA DESIGN"), "ND0013"));

t("o maior vence, não o último", () =>
  assert.equal(proximoId(abaFalsa([
    { cliente: "QG ITALÍNEA", id: "QGI0020" },
    { cliente: "QG ITALÍNEA", id: "QGI0003" },
  ]), "QG ITALÍNEA"), "QGI0021"));

console.log(`${ok} passaram, ${falhas.length} falharam`);
for (const f of falhas) console.log("  ✗ " + f);
process.exit(falhas.length ? 1 : 0);
