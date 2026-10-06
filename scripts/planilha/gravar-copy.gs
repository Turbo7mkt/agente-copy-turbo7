/**
 * Gravar copy do Painel Turbo7 na planilha `Criativos Turbo7`.
 *
 * Instalação: veja scripts/planilha/README.md.
 *
 * O painel roda no navegador do gestor, então ele fala direto com este Web App.
 * Nada passa pelo container do agente, e nenhum conector do Drive é necessário.
 *
 * O token NÃO fica neste arquivo. Ele vive em Propriedades do Script, e do lado
 * do painel vive no localStorage do navegador de quem usa — nunca no HTML
 * publicado. É isso que permite o painel ser aberto por link sem entregar a
 * chave de escrita da planilha junto.
 */

const ABA = 'BASE_CRIATIVOS';

/** Colunas de BASE_CRIATIVOS, 1-indexadas, na ordem real da planilha. */
const COL = {
  cliente: 1, gestor: 2, solicitacao: 3, prazo: 4, responsavel: 5,
  tipo: 6, copy: 7, status: 8, entregue: 9, diasAberto: 10,
  diasAtraso: 11, id: 12, audio: 13, obs: 14,
};
const TOTAL_COLUNAS = 14;

/** Colunas calculadas: a fórmula é herdada da linha de cima, não escrita à mão. */
const COLUNAS_DE_FORMULA = [COL.diasAberto, COL.diasAtraso];

/**
 * O painel chama isto ao abrir a configuração, para oferecer os valores que a
 * planilha JÁ usa em vez de deixar o gestor digitar. É o que evita criar
 * "DECORALLE PLANEJADOS" ao lado de "DECORALLE" e partir a sequência de IDs.
 */
function doGet(requisicao) {
  try {
    const esperado = PropertiesService.getScriptProperties().getProperty('TOKEN');
    if (!esperado) return responder({ ok: false, erro: 'Script sem TOKEN configurado.' });
    if (!requisicao.parameter || requisicao.parameter.token !== esperado) {
      return responder({ ok: false, erro: 'Token inválido.' });
    }

    const aba = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(ABA);
    if (!aba) return responder({ ok: false, erro: 'Aba ' + ABA + ' não encontrada.' });
    const ultima = aba.getLastRow();
    if (ultima < 2) return responder({ ok: true, clientes: [], gestores: [], responsaveis: [], tipos: [] });

    const dados = aba.getRange(2, COL.cliente, ultima - 1, COL.tipo - COL.cliente + 1).getValues();
    return responder({
      ok: true,
      clientes: distintos(dados, COL.cliente - COL.cliente),
      gestores: distintos(dados, COL.gestor - COL.cliente),
      responsaveis: distintos(dados, COL.responsavel - COL.cliente),
      tipos: distintos(dados, COL.tipo - COL.cliente),
    });
  } catch (e) {
    return responder({ ok: false, erro: String((e && e.message) || e) });
  }
}

function distintos(linhas, indice) {
  const vistos = Object.create(null);
  for (const linha of linhas) {
    const valor = String(linha[indice] || '').trim();
    if (valor) vistos[valor] = true;
  }
  return Object.keys(vistos).sort();
}

function doPost(requisicao) {
  try {
    const corpo = JSON.parse(requisicao.postData.contents);

    const esperado = PropertiesService.getScriptProperties().getProperty('TOKEN');
    if (!esperado) return responder({ ok: false, erro: 'Script sem TOKEN configurado.' });
    if (corpo.token !== esperado) return responder({ ok: false, erro: 'Token inválido.' });

    if (!corpo.cliente) return responder({ ok: false, erro: 'Falta o cliente.' });

    // Uma entrega de 10 copies são 10 criativos, e a planilha é uma linha por
    // criativo. O painel manda `linhas`; o formato antigo de uma copy só
    // continua aceito para não quebrar implantação já em uso.
    var linhas = corpo.linhas;
    if (!linhas && corpo.copy) {
      linhas = [{ tipo: corpo.tipo, copy: corpo.copy, status: corpo.status, observacoes: corpo.observacoes }];
    }
    if (!linhas || !linhas.length) return responder({ ok: false, erro: 'Nenhuma copy para gravar.' });
    for (var i = 0; i < linhas.length; i++) {
      if (!linhas[i].copy) return responder({ ok: false, erro: 'Copy vazia na peça ' + (i + 1) + '.' });
    }
    corpo.linhas = linhas;

    // Trava para duas abas do painel não pegarem o mesmo ID.
    const trava = LockService.getScriptLock();
    trava.waitLock(20000);
    try {
      return responder(gravar(corpo));
    } finally {
      trava.releaseLock();
    }
  } catch (e) {
    return responder({ ok: false, erro: String((e && e.message) || e) });
  }
}

function gravar(corpo) {
  const planilha = SpreadsheetApp.getActiveSpreadsheet();
  const aba = planilha.getSheetByName(ABA);
  if (!aba) return { ok: false, erro: 'Aba ' + ABA + ' não encontrada.' };

  const serie = serieDoCliente(aba, corpo.cliente);
  const solicitacao = hoje();
  // `Para ser Entregue Em` ficava em branco e quebrava `Dias Em Atraso`.
  // O painel manda o SLA em dias úteis; sem ele, o padrão da casa é 3.
  const prazo = corpo.prazo || dataEmDiasUteis(corpo.prazoDias == null ? 3 : corpo.prazoDias);

  const primeira = aba.getLastRow() + 1;
  const matriz = [];
  const ids = [];

  for (var i = 0; i < corpo.linhas.length; i++) {
    const peca = corpo.linhas[i];
    const id = serie.prefixo + String(serie.maior + 1 + i).padStart(serie.digitos, '0');
    ids.push(id);

    const valores = new Array(TOTAL_COLUNAS).fill('');
    valores[COL.cliente - 1] = corpo.cliente;
    valores[COL.gestor - 1] = corpo.gestor || '';
    valores[COL.solicitacao - 1] = solicitacao;
    valores[COL.prazo - 1] = prazo;
    valores[COL.responsavel - 1] = corpo.responsavel || '';
    valores[COL.tipo - 1] = peca.tipo || 'Vídeo';
    valores[COL.copy - 1] = peca.copy;
    valores[COL.status - 1] = peca.status || 'Copy em Aprovação';
    valores[COL.id - 1] = id;
    valores[COL.obs - 1] = peca.observacoes || '';
    matriz.push(valores);
  }

  aba.getRange(primeira, 1, matriz.length, TOTAL_COLUNAS).setValues(matriz);
  for (var j = 0; j < matriz.length; j++) herdarFormulas(aba, primeira + j);

  return {
    ok: true,
    ids: ids,
    id: ids[0],                       // compatibilidade com o formato antigo
    linha: primeira,
    linhas: matriz.length,
    prazo: prazo,
    url: planilha.getUrl() + '#gid=' + aba.getSheetId() + '&range=A' + primeira,
  };
}

/** Dia útil N dias à frente, pulando sábado e domingo. */
function dataEmDiasUteis(n) {
  const fuso = SpreadsheetApp.getActiveSpreadsheet().getSpreadsheetTimeZone();
  const d = new Date();
  var contados = 0;
  while (contados < n) {
    d.setDate(d.getDate() + 1);
    if (d.getDay() !== 0 && d.getDay() !== 6) contados++;
  }
  return Utilities.formatDate(d, fuso, 'dd/MM/yyyy');
}

/**
 * Próximo `ID do Criativo` do cliente: mesmo prefixo das linhas que ele já tem,
 * número seguinte, mesma quantidade de dígitos.
 *
 * Cliente novo, sem linha nenhuma: prefixo pelas iniciais, começando em 0001.
 */
function serieDoCliente(aba, cliente) {
  const ultima = aba.getLastRow();
  let prefixo = '';
  let maior = 0;
  let digitos = 4;

  if (ultima >= 2) {
    const dados = aba.getRange(2, COL.cliente, ultima - 1, COL.id - COL.cliente + 1).getValues();
    const alvo = normalizar(cliente);
    for (const linha of dados) {
      if (normalizar(linha[0]) !== alvo) continue;
      const bruto = String(linha[COL.id - COL.cliente] || '').trim();
      const partes = bruto.match(/^([A-Za-zÀ-ÿ]+)\s*(\d+)$/);
      if (!partes) continue;
      prefixo = partes[1].toUpperCase();
      digitos = Math.max(digitos, partes[2].length);
      maior = Math.max(maior, parseInt(partes[2], 10));
    }
  }

  if (!prefixo) prefixo = iniciais(cliente);
  return { prefixo: prefixo, maior: maior, digitos: digitos };
}

function proximoId(aba, cliente) {
  const s = serieDoCliente(aba, cliente);
  return s.prefixo + String(s.maior + 1).padStart(s.digitos, '0');
}

/** "CASA & COZINHA ITALÍNEA" → "CCI". Ignora "&", "DE", "DA" e afins. */
function iniciais(cliente) {
  const ignorar = ['DE', 'DA', 'DO', 'DAS', 'DOS', 'E', '&'];
  const letras = String(cliente)
    .toUpperCase()
    .replace(/[^A-ZÀ-Ÿ\s&]/g, ' ')
    .split(/\s+/)
    .filter((p) => p && ignorar.indexOf(p) === -1)
    .map((p) => p.charAt(0))
    .join('');
  return letras.slice(0, 4) || 'XX';
}

function normalizar(texto) {
  return String(texto || '').trim().replace(/\s+/g, ' ').toUpperCase();
}

/** Copia para a linha nova as fórmulas das colunas calculadas, se houver. */
function herdarFormulas(aba, linha) {
  if (linha < 3) return;
  for (const coluna of COLUNAS_DE_FORMULA) {
    const acima = aba.getRange(linha - 1, coluna);
    if (acima.getFormula()) acima.copyTo(aba.getRange(linha, coluna));
  }
}

function hoje() {
  const fuso = SpreadsheetApp.getActiveSpreadsheet().getSpreadsheetTimeZone();
  return Utilities.formatDate(new Date(), fuso, 'dd/MM/yyyy');
}

function responder(objeto) {
  return ContentService
    .createTextOutput(JSON.stringify(objeto))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Rode uma vez pelo editor (Executar → configurarToken) para criar um token
 * novo. Ele aparece no registro de execução — copie de lá para o painel.
 */
function configurarToken() {
  const token = Utilities.getUuid();
  PropertiesService.getScriptProperties().setProperty('TOKEN', token);
  Logger.log('TOKEN do painel: ' + token);
  return token;
}
