"""Painel do agente de copy — Turbo7.

Sobe com:
    export ANTHROPIC_API_KEY=...
    uvicorn app.main:app --reload --port 8000

O protocolo dos 4 passos é servido pela API, não pelo modelo:
    /api/clientes            passo 1 — quem tem briefing
    /api/clientes/{slug}     passo 2 — frescor da base e do briefing
    .../angulos              passo 3 — o que o briefing sustenta
    /api/gerar               passo 4 — gera com o ângulo escolhido, lintado
"""

from __future__ import annotations

import os
from pathlib import Path

import anthropic
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .core import base, geracao

ESTATICO = Path(__file__).parent / "static"

app = FastAPI(title="Agente de Copy — Turbo7", version="1.0")


# --------------------------------------------------------------------------
# Modelos de entrada
# --------------------------------------------------------------------------

class PedidoGeracao(BaseModel):
    slug: str
    angulos: list[int] = Field(min_length=1)
    formato: str = "10 copies — 7 vídeo, 2 imagem, 1 carrossel"
    observacao: str = ""
    tema: str = "fundo-funil"
    salvar: bool = True


# --------------------------------------------------------------------------
# Passo 1 e 2
# --------------------------------------------------------------------------

@app.get("/api/status")
def status() -> dict:
    frescor = base.checar_frescor()
    return {
        "base": {
            "status": frescor.status,
            "dias": frescor.dias,
            "ultima_sincronizacao": str(frescor.ultima_sincronizacao) if frescor.ultima_sincronizacao else None,
            "mensagem": frescor.mensagem,
        },
        "api_configurada": bool(
            os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
        ),
    }


@app.get("/api/clientes")
def clientes() -> list[dict]:
    return base.listar_clientes()


@app.get("/api/clientes/{slug}")
def cliente(slug: str) -> dict:
    b = _briefing(slug)
    dias = b.dias_desde_atualizacao
    return {
        "slug": b.slug,
        "nome": b.nome,
        "praca": b.dados.get("praca"),
        "usa_preco": b.usa_preco,
        "publico": b.dados.get("publico"),
        "ticket_alvo": b.dados.get("ticket_alvo"),
        "prazo_entrega": b.dados.get("prazo_entrega"),
        "garantia": b.dados.get("garantia"),
        "cta_preferido": b.dados.get("cta_preferido"),
        "atualizado_em": str(b.atualizado_em) if b.atualizado_em else None,
        "dias_desde_atualizacao": dias,
        "briefing_velho": dias is not None and dias > base.DIAS_ATE_BRIEFING_VELHO,
        "prova_google_contestada": b.prova_google_contestada,
        "restricoes": b.secao("Restrições"),
        "provas": b.secao("Provas disponíveis"),
        "copies": base.listar_copies(slug),
    }


# --------------------------------------------------------------------------
# Passo 3 — os ângulos que o briefing sustenta
# --------------------------------------------------------------------------

@app.get("/api/clientes/{slug}/angulos")
def angulos(slug: str) -> dict:
    b = _briefing(slug)
    disponiveis, bloqueados = base.filtrar_angulos(base.carregar_angulos(), b)
    return {"disponiveis": disponiveis, "bloqueados": bloqueados}


@app.get("/api/clientes/{slug}/copies/{arquivo}")
def copy(slug: str, arquivo: str) -> dict:
    if "/" in arquivo or ".." in arquivo:
        raise HTTPException(400, "nome de arquivo inválido")
    caminho = base.CLIENTES / slug / "copies" / arquivo
    if not caminho.is_file():
        raise HTTPException(404, "copy não encontrada")
    return {"arquivo": arquivo, "markdown": caminho.read_text(encoding="utf-8")}


# --------------------------------------------------------------------------
# Passo 4 — gerar
# --------------------------------------------------------------------------

@app.post("/api/gerar")
def gerar(pedido: PedidoGeracao) -> dict:
    b = _briefing(pedido.slug)
    frescor = base.checar_frescor()

    disponiveis, bloqueados = base.filtrar_angulos(base.carregar_angulos(), b)
    por_numero = {a["numero"]: a for a in disponiveis}
    bloqueados_por_numero = {a["numero"]: a for a in bloqueados}

    escolhidos = []
    for n in pedido.angulos:
        if n in por_numero:
            escolhidos.append(por_numero[n])
        elif n in bloqueados_por_numero:
            motivo = bloqueados_por_numero[n]["motivo"]
            raise HTTPException(422, f"ângulo {n} não é permitido para este cliente: {motivo}")
        else:
            raise HTTPException(422, f"ângulo {n} não existe na biblioteca")

    try:
        resultado = geracao.gerar(
            briefing=b,
            angulos=escolhidos,
            formato=pedido.formato,
            frescor=frescor,
            observacao=pedido.observacao,
            tema=pedido.tema,
            salvar=pedido.salvar,
        )
    except geracao.CredencialAusente as e:
        raise HTTPException(401, str(e))
    except anthropic.AuthenticationError:
        raise HTTPException(401, "Credencial da API inválida. Verifique ANTHROPIC_API_KEY.")
    except anthropic.RateLimitError as e:
        espera = e.response.headers.get("retry-after", "60")
        raise HTTPException(429, f"Limite de uso atingido. Tente de novo em {espera}s.")
    except anthropic.APIStatusError as e:
        raise HTTPException(502, f"Erro da API ({e.status_code}): {e.message}")
    except anthropic.APIConnectionError:
        raise HTTPException(504, "Não consegui falar com a API. Verifique a rede.")
    except RuntimeError as e:
        raise HTTPException(502, str(e))

    return {
        "markdown": resultado.markdown,
        "arquivo": resultado.arquivo,
        "achados": resultado.achados,
        "aprovado_no_linter": not resultado.achados,
        "base_sincronizada_em": str(frescor.ultima_sincronizacao) if frescor.ultima_sincronizacao else None,
        "uso": {
            "entrada": resultado.tokens_entrada,
            "saida": resultado.tokens_saida,
            "cache_lido": resultado.cache_lido,
        },
    }


# --------------------------------------------------------------------------

def _briefing(slug: str) -> base.Briefing:
    try:
        return base.carregar_briefing(slug)
    except FileNotFoundError:
        raise HTTPException(404, f"'{slug}' não tem briefing. Rode a skill `briefing` antes.")
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.get("/")
def index() -> FileResponse:
    return FileResponse(ESTATICO / "index.html")


app.mount("/static", StaticFiles(directory=ESTATICO), name="static")
