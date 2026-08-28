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

    if (s.credencial_no_ambiente) $("gerar").classList.remove("oculto");

    const alertas = [];
    if (s.bloqueado_sem_senha) {
      alertas.push("APP_SENHA não está definida nas variáveis de ambiente. " +
        "O painel está bloqueado até que ela seja configurada — nenhum dado de " +
        "cliente é servido sem senha em produção.");
    } else if (!s.protegido_por_senha) {
      alertas.push("Painel sem senha — não deixe assim em produção.");
    }
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
  const pronto = Boolean(estado.slug) && estado.angulos.size > 0;
  const m = $("montar");
  m.disabled = !pronto;
  m.textContent = estado.angulos.size > 1
    ? `Montar prompt com ${estado.angulos.size} ângulos`
    : "Montar prompt";
  $("gerar").disabled = !pronto;
}

/* ---------- Passo 5 — monta o prompt, sem chamar a API ---------- */

function pedidoAtual() {
  return {
    slug: estado.slug,
    angulos: [...estado.angulos],
    formato: $("formato").value,
    observacao: $("observacao").value,
    tema: $("tema").value.trim() || "fundo-funil",
  };
}

async function montarPrompt() {
  const b = $("montar");
  b.disabled = true;
  texto($("aviso"), "");
  try {
    const r = await api("/api/prompt", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(pedidoAtual()),
    });
    $("prompt").textContent = r.prompt;
    texto($("prompt-meta"),
      `${r.angulos.join(" · ")} — base de ${r.base_sincronizada_em ?? "data desconhecida"}`);
    $("p5").classList.remove("oculto");
    $("p6").classList.remove("oculto");
    $("p5").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (e) {
    texto($("aviso"), e.message);
  } finally {
    b.disabled = false;
    atualizarBotao();
  }
}

/* ---------- Passo 6 — valida a copy que voltou ---------- */

async function validarColada() {
  const markdown = $("colada").value.trim();
  texto($("aviso-validar"), "");
  if (!markdown) {
    texto($("aviso-validar"), "Cole a copy antes de validar.");
    return;
  }

  const b = $("validar");
  b.disabled = true;
  try {
    const r = await api("/api/validar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ slug: estado.slug, markdown }),
    });

    const v = $("veredito-colada");
    if (r.aprovado_no_linter) {
      v.className = "veredito aprovado";
      v.innerHTML = `<span class="titulo">Passou no linter</span>
        <span>Falta o checklist manual antes de entregar ao cliente.</span>`;
    } else {
      v.className = "veredito reprovado";
      const itens = r.achados
        .map((a) => `<li>linha ${a.linha} · [${escapar(a.codigo)}] ${escapar(a.descricao)}</li>`)
        .join("");
      v.innerHTML = `<span class="titulo">${r.achados.length} violação(ões) — não entregue assim</span>
        <ul>${itens}</ul>`;
    }

    const link = $("baixar-colada");
    link.href = URL.createObjectURL(new Blob([markdown], { type: "text/markdown" }));
    link.download = `${new Date().toISOString().slice(0, 10)}-${estado.slug}.md`;
    link.classList.remove("oculto");
  } catch (e) {
    texto($("aviso-validar"), e.message);
  } finally {
    b.disabled = false;
  }
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

$("montar").addEventListener("click", montarPrompt);
$("gerar").addEventListener("click", gerar);
$("validar").addEventListener("click", validarColada);
$("copiar-prompt").addEventListener("click", async () => {
  await navigator.clipboard.writeText($("prompt").textContent);
  const b = $("copiar-prompt");
  b.textContent = "Copiado";
  setTimeout(() => (b.textContent = "Copiar prompt"), 1600);
});
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
