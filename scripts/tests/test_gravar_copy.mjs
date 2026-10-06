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
/* A planilha dublada: guarda o que foi escrito, para a asserção ser sobre a
   linha que realmente entraria em BASE_CRIATIVOS. */
const gravado = { linhas: [], primeira: 0 };

function montarEscopo(linhasExistentes) {
  const largura = 14;
  const aba = {
    getSheetId: () => 0,
    getLastRow: () => linhasExistentes.length + 1,
    getRange: (linha, coluna, nLinhas, nCols) => ({
      getValues: () =>
        linhasExistentes.map((l) => {
          const cheia = new Array(nCols || largura).fill("");
          cheia[0] = l.cliente;
          cheia[11] = l.id; // COL.id - COL.cliente
          return cheia;
        }),
      setValues: (m) => { gravado.primeira = linha; gravado.linhas = m; },
      getFormula: () => "",
      copyTo: () => {},
    }),
  };
  return {
    SpreadsheetApp: {
      getActiveSpreadsheet: () => ({
        getSheetByName: () => aba,
        getSpreadsheetTimeZone: () => "America/Sao_Paulo",
        getUrl: () => "https://exemplo/planilha",
      }),
    },
    PropertiesService: { getScriptProperties: () => ({ getProperty: () => "tok" }) },
    LockService: {},
    Utilities: { formatDate: (d) => `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}` },
    Logger: {},
    ContentService: {},
  };
}

function carregar(escopo) {
  return new Function(
    ...Object.keys(escopo),
    fonte + "\nreturn { proximoId, serieDoCliente, iniciais, normalizar, gravar, dataEmDiasUteis, COL };"
  )(...Object.values(escopo));
}

const { proximoId, iniciais, normalizar, COL } = carregar(montarEscopo([]));

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

/* --- Lote: uma entrega de N copies vira N linhas, não uma --- */

function gravarLote(linhasExistentes, corpo) {
  gravado.linhas = [];
  const api = carregar(montarEscopo(linhasExistentes));
  const r = api.gravar(corpo);
  return { r, escritas: gravado.linhas, primeira: gravado.primeira };
}

const BASE = [
  { cliente: "ATLÂNTICA ITALÍNEA", id: "AI0004" },
  { cliente: "CAMMINARE ITALÍNEA", id: "CI0002" },
];
const TRES = {
  cliente: "ATLÂNTICA ITALÍNEA", gestor: "Thiago", responsavel: "Gabriel", prazoDias: 3,
  linhas: [
    { tipo: "Vídeo", copy: "peça 1", status: "Copy em Aprovação" },
    { tipo: "Vídeo", copy: "peça 2", status: "Copy em Aprovação" },
    { tipo: "Carrossel", copy: "peça 3", status: "Copy em Aprovação" },
  ],
};

t("três peças viram três linhas", () =>
  assert.equal(gravarLote(BASE, TRES).escritas.length, 3));

t("os IDs do lote são sequenciais e continuam a série do cliente", () =>
  assert.deepEqual(gravarLote(BASE, TRES).r.ids, ["AI0005", "AI0006", "AI0007"]));

t("cada linha leva o seu próprio tipo de criativo", () =>
  assert.deepEqual(
    gravarLote(BASE, TRES).escritas.map((l) => l[COL.tipo - 1]),
    ["Vídeo", "Vídeo", "Carrossel"]));

t("gestor, responsável e cliente se repetem em todas", () => {
  const e = gravarLote(BASE, TRES).escritas;
  assert.ok(e.every((l) => l[COL.cliente - 1] === "ATLÂNTICA ITALÍNEA"
    && l[COL.gestor - 1] === "Thiago" && l[COL.responsavel - 1] === "Gabriel"));
});

t("`Para ser Entregue Em` deixa de sair em branco", () =>
  assert.ok(gravarLote(BASE, TRES).escritas.every((l) => /^\d{2}\/\d{2}\/\d{4}$/.test(l[COL.prazo - 1]))));

t("o SLA é contado em dias úteis, pulando o fim de semana", () => {
  const api = carregar(montarEscopo([]));
  const [d, m, a] = api.dataEmDiasUteis(3).split("/").map(Number);
  const alvo = new Date(a, m - 1, d);
  assert.ok(alvo.getDay() !== 0 && alvo.getDay() !== 6, "caiu no fim de semana");
  assert.ok(alvo > new Date(), "a data precisa estar no futuro");
});

t("o formato antigo de uma copy só continua gravando", () => {
  const r = gravarLote(BASE, { cliente: "ATLÂNTICA ITALÍNEA", linhas: [{ copy: "só uma" }] });
  assert.equal(r.escritas.length, 1);
  assert.equal(r.r.id, "AI0005");
});

t("cliente sem série ainda começa em 0001, mesmo em lote", () =>
  assert.deepEqual(
    gravarLote(BASE, { cliente: "CASA & COZINHA ITALÍNEA", linhas: [{ copy: "a" }, { copy: "b" }] }).r.ids,
    ["CCI0001", "CCI0002"]));

console.log(`${ok} passaram, ${falhas.length} falharam`);
for (const f of falhas) console.log("  ✗ " + f);
process.exit(falhas.length ? 1 : 0);
