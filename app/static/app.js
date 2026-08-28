"use strict";

const $ = (id) => document.getElementById(id);
const estado = { slug: null, angulos: new Set(), cliente: null, gravaNoRepo: true };

const senha = () => sessionStorage.getItem("senha") || "";

async function api(caminho, opcoes = {}) {
  const r = await fetch(caminho, {
    ...opcoes,
    headers: { ...(opcoes.headers || {}), "X-Senha": senha() },
  });
  const corpo = await r.json().catch(() => ({}));
  if (r.status === 401) { pedirSenha(); throw new Error("Senha necessária."); }
  if (!r.ok) throw new Error(corpo.detail || `Erro ${r.status}`);
  return corpo;
}

const texto = (el, v) => { el.textContent = v; };

function escapar(s) {
  const d = document.createElement("div");
  d.textContent = String(s);
  return d.innerHTML;
}

/* ---------- Porta ---------- */

function pedirSenha() {
  $("porta").classList.remove("oculto");
  $("palco").classList.add("oculto");
}

$("entrar").addEventListener("click", async () => {
  sessionStorage.setItem("senha", $("senha").value);
  texto($("porta-aviso"), "");
  try {
    await api("/api/clientes");
    $("porta").classList.add("oculto");
    $("palco").classList.remove("oculto");
    iniciar();
  } catch (e) {
    texto($("porta-aviso"), e.message);
  }
});

$("senha").addEventListener("keydown", (e) => {
  if (e.key === "Enter") $("entrar").click();
});

/* ---------- Status ---------- */

async function carregarStatus() {
  try {
    const r = await fetch("/api/status");
    const s = await r.json();
    estado.gravaNoRepo = s.grava_no_repo;

    const el = $("frescor");
    el.className = `frescor ${s.base.status}`;
    texto(el, s.base.status === "velha"
      ? `⚠ base há ${s.base.dias} dias sem sincronizar`
      : `base sincronizada em ${s.base.ultima_sincronizacao ?? "—"}`);

    const alertas = [];
    if (!s.credencial_no_ambiente) alertas.push("ANTHROPIC_API_KEY não está definida no servidor.");
    if (!s.protegido_por_senha) alertas.push("Painel sem senha — não deixe assim em produção.");
    if (alertas.length) {
      const box = $("alerta-global");
      box.innerHTML = alertas.map((a) => `<div>${escapar(a)}</div>`).join("");
      box.classList.remove("oculto");
    }
    return s;
  } catch {
    texto($("frescor"), "status indisponível");
    return null;
  }
}

/* ---------- Passo 1 ---------- */

async function carregarClientes() {
  const alvo = $("clientes");
  try {
    const lista = await api("/api/clientes");
    if (!lista.length) {
      alvo.innerHTML = '<p class="carregando">Nenhum cliente com briefing. Rode a skill <code>briefing</code>.</p>';
      return;
    }
    alvo.innerHTML = "";
    for (const c of lista) {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "cartao";
      b.setAttribute("aria-pressed", "false");
      b.dataset.slug = c.slug;
      b.innerHTML = `<span class="nome"></span><span class="praca"></span><span class="meta"></span>`;
      b.querySelector(".nome").textContent = c.nome;
      b.querySelector(".praca").textContent = c.praca || "—";
      b.querySelector(".meta").textContent =
        `${c.usa_preco ? "com preço" : "sem preço"} · ${c.copies} entrega(s)`;
      b.addEventListener("click", () => escolherCliente(c.slug));
      alvo.appendChild(b);
    }
  } catch (e) {
    alvo.innerHTML = `<p class="carregando">${escapar(e.message)}</p>`;
  }
}

/* ---------- Passo 2 ---------- */

async function escolherCliente(slug) {
  estado.slug = slug;
  estado.angulos.clear();

  document.querySelectorAll(".cartao").forEach((el) =>
    el.setAttribute("aria-pressed", String(el.dataset.slug === slug)));

  const c = await api(`/api/clientes/${slug}`);
  estado.cliente = c;

  const dado = (rotulo, valor) => `
    <div class="dado">
      <dt>${rotulo}</dt>
      <dd class="${valor ? "" : "vazio"}">${valor ? escapar(valor) : "não confirmado"}</dd>
    </div>`;

  let html = `<div class="resumo">
    ${dado("Praça", c.praca)}
    ${dado("Público", c.publico)}
    ${dado("Ticket alvo", c.ticket_alvo)}
    ${dado("Prazo", c.prazo_entrega)}
    ${dado("Garantia", c.garantia)}
    <div class="dado">
      <dt>Preço na copy</dt>
      <dd><span class="selo ${c.usa_preco ? "preco-sim" : "preco-nao"}">${c.usa_preco ? "liberado" : "proibido"}</span></dd>
    </div>
  </div>`;

  if (c.prova_google_contestada) {
    html += `<div class="alerta">A nota do Google está marcada com ⚠️ no briefing —
      ângulos de prova social ficam indisponíveis para esta loja.</div>`;
  }
  if (c.briefing_velho) {
    html += `<div class="alerta">Briefing atualizado há ${c.dias_desde_atualizacao} dias.
      Confirme se ainda vale antes de gerar.</div>`;
  }

  $("briefing").innerHTML = html;
  $("p2").classList.remove("oculto");

  await carregarAngulos(slug);
  $("p4").classList.remove("oculto");
  $("resultado").classList.add("oculto");
  atualizarBotao();
}

/* ---------- Passo 3 ---------- */

async function carregarAngulos(slug) {
  const { disponiveis, bloqueados } = await api(`/api/clientes/${slug}/angulos`);

  const alvo = $("angulos");
  alvo.innerHTML = "";
  for (const a of disponiveis) {
    const l = document.createElement("label");
    l.className = "angulo";
    l.innerHTML = `
      <input type="checkbox" value="${a.numero}">
      <span class="corpo">
        <span class="gatilho"></span>
        <span class="nome"></span>
        <span class="detalhe"></span>
        <span class="usado"></span>
      </span>`;
    l.querySelector(".gatilho").textContent = a.gatilho;
    l.querySelector(".nome").textContent = a.nome;
    l.querySelector(".detalhe").textContent = `Fala com ${a.fala_com.toLowerCase()} · ${a.eixo}`;
    l.querySelector(".usado").textContent = a.ja_usado ? "já usado em entrega recente" : "";
    l.querySelector("input").addEventListener("change", (ev) => {
      const n = Number(ev.target.value);
      ev.target.checked ? estado.angulos.add(n) : estado.angulos.delete(n);
      atualizarBotao();
    });
    alvo.appendChild(l);
  }

  const box = $("bloqueados");
  box.innerHTML = "";
  texto($("bloqueados-n"), `(${bloqueados.length})`);
  $("bloqueados-box").style.display = bloqueados.length ? "" : "none";
  for (const a of bloqueados) {
    const d = document.createElement("div");
    d.className = "item";
    d.innerHTML = `<strong></strong> — <span></span>`;
    d.querySelector("strong").textContent = a.nome;
    d.querySelector("span").textContent = a.motivo;
    box.appendChild(d);
  }

  $("p3").classList.remove("oculto");
}

function atualizarBotao() {
  const b = $("gerar");
  b.disabled = !estado.slug || estado.angulos.size === 0;
  b.textContent = estado.angulos.size > 1
    ? `Gerar com ${estado.angulos.size} ângulos`
    : "Gerar copies";
}

/* ---------- Passo 4 — consome SSE ---------- */

async function gerar() {
  const botao = $("gerar");
  botao.disabled = true;
  botao.textContent = "Escrevendo…";
  texto($("aviso"), "");

  $("veredito").innerHTML = "";
  $("saida").textContent = "";
  texto($("arquivo-salvo"), "");
  $("resultado").classList.remove("oculto");
  $("resultado").scrollIntoView({ behavior: "smooth", block: "start" });

  try {
    const r = await fetch("/api/gerar", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Senha": senha() },
      body: JSON.stringify({
        slug: estado.slug,
        angulos: [...estado.angulos],
        formato: $("formato").value,
        observacao: $("observacao").value,
        tema: $("tema").value.trim() || "fundo-funil",
      }),
    });

    if (!r.ok) {
      const corpo = await r.json().catch(() => ({}));
      throw new Error(corpo.detail || `Erro ${r.status}`);
    }

    await consumirSSE(r);
  } catch (e) {
    texto($("aviso"), e.message);
  } finally {
    botao.disabled = false;
    atualizarBotao();
  }
}

async function consumirSSE(resposta) {
  const leitor = resposta.body.getReader();
  const decodificador = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await leitor.read();
    if (done) break;
    buffer += decodificador.decode(value, { stream: true });

    const blocos = buffer.split("\n\n");
    buffer = blocos.pop() ?? "";

    for (const bloco of blocos) {
      const evento = /^event: (.+)$/m.exec(bloco)?.[1];
      const dados = /^data: (.+)$/m.exec(bloco)?.[1];
      if (!evento || !dados) continue;
      const carga = JSON.parse(dados);

      if (evento === "delta") {
        $("saida").textContent += carga.texto;
        $("saida").scrollTop = $("saida").scrollHeight;
      } else if (evento === "fim") {
        mostrarResultado(carga);
      } else if (evento === "erro") {
        texto($("aviso"), carga.mensagem);
      }
    }
  }
}

function mostrarResultado(r) {
  const v = $("veredito");
  if (r.aprovado_no_linter) {
    v.className = "veredito aprovado";
    v.innerHTML = `<span class="titulo">Passou no linter</span>
      <span>Falta o checklist manual e a revisão do subagente antes de entregar ao cliente.</span>`;
  } else {
    v.className = "veredito reprovado";
    const itens = r.achados
      .map((a) => `<li>linha ${a.linha} · [${escapar(a.codigo)}] ${escapar(a.descricao)}</li>`)
      .join("");
    v.innerHTML = `<span class="titulo">${r.achados.length} violação(ões) — não entregue assim</span>
      <ul>${itens}</ul>`;
  }

  $("saida").textContent = r.markdown;
  texto($("arquivo-salvo"), r.arquivo
    ? `salvo em clientes/${estado.slug}/copies/${r.arquivo}`
    : (estado.gravaNoRepo ? "não salvo" : "servidor só-leitura — baixe o arquivo"));

  const nome = `${new Date().toISOString().slice(0, 10)}-${estado.slug}.md`;
  const link = $("baixar");
  link.href = URL.createObjectURL(new Blob([r.markdown], { type: "text/markdown" }));
  link.download = nome;
  link.classList.remove("oculto");
}

/* ---------- Ligações ---------- */

$("gerar").addEventListener("click", gerar);
$("copiar").addEventListener("click", async () => {
  await navigator.clipboard.writeText($("saida").textContent);
  const b = $("copiar");
  b.textContent = "Copiado";
  setTimeout(() => (b.textContent = "Copiar markdown"), 1600);
});

function iniciar() {
  carregarClientes();
}

(async () => {
  const s = await carregarStatus();
  if (s && s.protegido_por_senha && !senha()) {
    pedirSenha();
  } else {
    $("palco").classList.remove("oculto");
    iniciar();
  }
})();
