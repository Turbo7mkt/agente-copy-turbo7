"""Painel do agente de copy — Turbo7.

Local:
    export ANTHROPIC_API_KEY=...
    uvicorn app.main:app --reload --port 8000

Vercel: ver `docs/deploy-vercel.md`.

O protocolo dos 4 passos é servido pela API, não pelo modelo:
    /api/clientes            passo 1 — quem tem briefing
    /api/clientes/{slug}     passo 2 — frescor da base e do briefing
    .../angulos              passo 3 — o que o briefing sustenta
    /api/gerar               passo 4 — gera (SSE) com o ângulo escolhido, lintado
"""

from __future__ import annotations

import hmac
import json
import os
from pathlib import Path

import anthropic
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .core import base, geracao

ESTATICO = Path(__file__).parent / "static"
SENHA = os.environ.get("APP_SENHA", "")

app = FastAPI(title="Agente de Copy — Turbo7", version="1.1")


# --------------------------------------------------------------------------
# Acesso
# --------------------------------------------------------------------------

def exigir_senha(x_senha: str = Header(default="")) -> None:
    """Porta única do painel.

    Sem `APP_SENHA` definida, o painel fica aberto — aceitável em localhost,
    nunca em produção. O deploy na Vercel checa isso em /api/status e a tela
    avisa em vermelho.
    """
    if not SENHA:
        return
    if not hmac.compare_digest(x_senha, SENHA):
        raise HTTPException(401, "Senha incorreta.")


class PedidoGeracao(BaseModel):
    slug: str
    angulos: list[int] = Field(min_length=1)
    formato: str = "10 copies — 7 vídeo, 2 imagem, 1 carrossel"
    observacao: str = ""
    tema: str = "fundo-funil"
    salvar: bool = True


class PedidoValidacao(BaseModel):
    slug: str
    markdown: str = Field(min_length=1)


# --------------------------------------------------------------------------
# Passos 1 e 2
# --------------------------------------------------------------------------

@app.get("/api/status")
def status() -> dict:
    frescor = base.checar_frescor()
    return {
        "base": {
            "status": frescor.status,
            "dias": frescor.dias,
            "ultima_sincronizacao": (
                str(frescor.ultima_sincronizacao) if frescor.ultima_sincronizacao else None
            ),
            "mensagem": frescor.mensagem,
        },
        "credencial_no_ambiente": bool(
            os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
        ),
        "protegido_por_senha": bool(SENHA),
        "grava_no_repo": geracao.escrita_permitida(),
    }


@app.get("/api/clientes", dependencies=[Depends(exigir_senha)])
def clientes() -> list[dict]:
    return base.listar_clientes()


@app.get("/api/clientes/{slug}", dependencies=[Depends(exigir_senha)])
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
# Passo 3
# --------------------------------------------------------------------------

@app.get("/api/clientes/{slug}/angulos", dependencies=[Depends(exigir_senha)])
def angulos(slug: str) -> dict:
    disponiveis, bloqueados = base.filtrar_angulos(base.carregar_angulos(), _briefing(slug))
    return {"disponiveis": disponiveis, "bloqueados": bloqueados}


@app.get("/api/clientes/{slug}/copies/{arquivo}", dependencies=[Depends(exigir_senha)])
def copy(slug: str, arquivo: str) -> dict:
    if "/" in arquivo or ".." in arquivo:
        raise HTTPException(400, "nome de arquivo inválido")
    caminho = base.CLIENTES / slug / "copies" / arquivo
    if not caminho.is_file():
        raise HTTPException(404, "copy não encontrada")
    return {"arquivo": arquivo, "markdown": caminho.read_text(encoding="utf-8")}


# --------------------------------------------------------------------------
# Passo 4a — montar o prompt (sem API, sem custo)
# --------------------------------------------------------------------------

@app.post("/api/prompt", dependencies=[Depends(exigir_senha)])
def prompt(pedido: PedidoGeracao) -> dict:
    """Devolve o prompt pronto para colar no Claude.

    É o caminho padrão de quem não tem chave de API: o painel cumpre os passos
    1 a 3 do protocolo — lê a base, checa o frescor, filtra os ângulos — e
    entrega o prompt montado. Quem escreve é o Claude da assinatura.
    """
    b = _briefing(pedido.slug)
    escolhidos = _validar_angulos(b, pedido.angulos)
    frescor = base.checar_frescor()

    corpo = geracao.montar_pedido(escolhidos, pedido.formato, pedido.observacao)
    return {
        "prompt": f"{geracao.montar_system(b)}\n\n---\n\n{corpo}",
        "angulos": [a["nome"] for a in escolhidos],
        "base_sincronizada_em": (
            str(frescor.ultima_sincronizacao) if frescor.ultima_sincronizacao else None
        ),
        "base_status": frescor.status,
    }


@app.post("/api/validar", dependencies=[Depends(exigir_senha)])
def validar(pedido: PedidoValidacao) -> dict:
    """Roda o linter sobre a copy que voltou do Claude.

    É o passo que impede a volta manual de virar buraco no protocolo: a copy
    colada passa exatamente pelas mesmas regras da geração automática.
    """
    b = _briefing(pedido.slug)
    achados = geracao.lintar(pedido.markdown, b.usa_preco)
    return {
        "achados": achados,
        "aprovado_no_linter": not achados,
        "usa_preco": b.usa_preco,
    }


# --------------------------------------------------------------------------
# Passo 4b — gerar direto (só com credencial no ambiente)
# --------------------------------------------------------------------------

@app.post("/api/gerar", dependencies=[Depends(exigir_senha)])
def gerar(pedido: PedidoGeracao) -> StreamingResponse:
    b = _briefing(pedido.slug)
    frescor = base.checar_frescor()
    escolhidos = _validar_angulos(b, pedido.angulos)

    def eventos():
        try:
            for tipo, carga in geracao.gerar_eventos(
                briefing=b,
                angulos=escolhidos,
                formato=pedido.formato,
                frescor=frescor,
                observacao=pedido.observacao,
                tema=pedido.tema,
                salvar=pedido.salvar,
            ):
                if tipo == "delta":
                    yield _sse("delta", {"texto": carga})
                else:
                    yield _sse("fim", {
                        "markdown": carga.markdown,
                        "arquivo": carga.arquivo,
                        "achados": carga.achados,
                        "aprovado_no_linter": not carga.achados,
                        "base_sincronizada_em": (
                            str(frescor.ultima_sincronizacao)
                            if frescor.ultima_sincronizacao else None
                        ),
                        "uso": {
                            "entrada": carga.tokens_entrada,
                            "saida": carga.tokens_saida,
                            "cache_lido": carga.cache_lido,
                        },
                    })
        except geracao.CredencialAusente as e:
            yield _sse("erro", {"mensagem": str(e)})
        except anthropic.AuthenticationError:
            yield _sse("erro", {"mensagem": "Credencial da API inválida."})
        except anthropic.RateLimitError as e:
            espera = e.response.headers.get("retry-after", "60")
            yield _sse("erro", {"mensagem": f"Limite de uso atingido. Tente em {espera}s."})
        except anthropic.APIStatusError as e:
            yield _sse("erro", {"mensagem": f"Erro da API ({e.status_code}): {e.message}"})
        except anthropic.APIConnectionError:
            yield _sse("erro", {"mensagem": "Não consegui falar com a API. Verifique a rede."})
        except RuntimeError as e:
            yield _sse("erro", {"mensagem": str(e)})

    return StreamingResponse(
        eventos(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _sse(evento: str, dados: dict) -> str:
    return f"event: {evento}\ndata: {json.dumps(dados, ensure_ascii=False)}\n\n"


def _validar_angulos(b: base.Briefing, pedidos: list[int]) -> list[dict]:
    disponiveis, bloqueados = base.filtrar_angulos(base.carregar_angulos(), b)
    por_numero = {a["numero"]: a for a in disponiveis}
    bloqueados_por_numero = {a["numero"]: a for a in bloqueados}

    escolhidos = []
    for n in pedidos:
        if n in por_numero:
            escolhidos.append(por_numero[n])
        elif n in bloqueados_por_numero:
            motivo = bloqueados_por_numero[n]["motivo"]
            raise HTTPException(422, f"ângulo {n} não é permitido para este cliente: {motivo}")
        else:
            raise HTTPException(422, f"ângulo {n} não existe na biblioteca")
    return escolhidos


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
