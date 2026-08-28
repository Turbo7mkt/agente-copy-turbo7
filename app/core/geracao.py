"""Geração de copy: monta o prompt a partir da base e chama a Claude.

O protocolo dos 4 passos é cumprido *fora* do modelo — o briefing, as regras e
os ângulos permitidos já chegam resolvidos. O modelo escreve, não decide.

A geração é streaming por dois motivos: a saída de 10 copies passa do timeout
de request sem stream, e em serverless (Vercel) a conexão precisa receber bytes
para não ser cortada no meio.
"""

from __future__ import annotations

import os
import sys
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterator

import anthropic

from .base import RAIZ, REGRAS, Briefing, Frescor

sys.path.insert(0, str(RAIZ / "scripts"))
from lint_copy import verificar  # noqa: E402

MODELO = "claude-opus-5"
MAX_TOKENS = 64_000

SKILLS_DA_CONTA = Path("/root/.claude/skills/synced")


class CredencialAusente(RuntimeError):
    """Nenhuma credencial da Anthropic pôde ser resolvida no ambiente."""


def escrita_permitida() -> bool:
    """Serverless roda com filesystem só-leitura (exceto /tmp)."""
    return not os.environ.get("VERCEL")


# --------------------------------------------------------------------------
# Prompt
# --------------------------------------------------------------------------

def _ler(caminho: Path) -> str:
    return caminho.read_text(encoding="utf-8") if caminho.is_file() else ""


def _regras_da_marca() -> str:
    """Regras de oferta da skill `italinea-identidade-visual`, se instalada.

    A skill é da conta, não do repo — em produção ela não existe. As regras
    equivalentes já vivem em `regras-copy.md`, então o prompt segue válido;
    perde só o detalhamento de formato.
    """
    for c in SKILLS_DA_CONTA.glob("*/italinea-identidade-visual/references/ofertas-e-copy.md"):
        return c.read_text(encoding="utf-8")
    return _ler(REGRAS / "identidade-italinea.md")


def montar_system(briefing: Briefing) -> str:
    """Prompt estável — vai inteiro para o cache."""
    import yaml

    partes = [
        "Você é o copywriter sênior da Turbo7, agência de marketing para lojas de "
        "móveis planejados da rede Italínea. Escreve resposta direta para Meta Ads, "
        "fundo de funil, público de alta intenção de compra.",
        "",
        "Você NUNCA inventa prova. Nota do Google, prazo, garantia e depoimento só "
        "entram se estiverem no briefing abaixo. Campo ausente significa que a loja "
        "não confirmou — não herde de outro cliente.",
        "",
        "## Regras de copy",
        _ler(REGRAS / "regras-copy.md"),
        "",
        "## Formatos de entrega",
        _ler(REGRAS / "formatos-entrega.md"),
        "",
        "## Copies aprovadas — calibragem de tom (nunca copiar frase)",
        _ler(RAIZ / "base-conhecimento" / "exemplos" / "copies-aprovadas.md"),
    ]

    marca = _regras_da_marca()
    if marca:
        partes += ["", "## Identidade Italínea — autoridade da marca sobre forma", marca]

    frontmatter = yaml.safe_dump(briefing.dados, allow_unicode=True, sort_keys=False).strip()
    partes += ["", "## Briefing do cliente", f"```yaml\n{frontmatter}\n```", briefing.corpo]
    return "\n".join(partes)


def montar_pedido(angulos: list[dict], formato: str, observacao: str = "") -> str:
    lista = "\n".join(
        f"- **{a['nome']}** · gatilho {a['gatilho']} · fala com: {a['fala_com']} "
        f"· eixo: {a['eixo']}"
        for a in angulos
    )
    partes = [
        "Escreva as copies usando **exatamente** os ângulos abaixo, escolhidos pelo "
        "gestor. Não substitua nenhum, não acrescente ângulo por conta própria.",
        "",
        lista,
        "",
        f"Formato de entrega: {formato}",
        "",
        "Feche com uma seção `## Nota de conformidade` declarando: o ângulo usado e "
        "que foi escolhido pelo gestor; qual prova do briefing ficou de fora e por "
        "quê; que promessas foram evitadas por causa das restrições; e a recomendação "
        "de segmentação, quando o briefing tiver.",
        "",
        "Responda apenas com o markdown da entrega, sem preâmbulo.",
    ]
    if observacao.strip():
        partes += ["", f"Observação do gestor: {observacao.strip()}"]
    return "\n".join(partes)


# --------------------------------------------------------------------------
# Geração
# --------------------------------------------------------------------------

@dataclass
class Resultado:
    markdown: str
    arquivo: str | None
    achados: list[dict]
    tokens_entrada: int
    tokens_saida: int
    cache_lido: int


def gerar_eventos(briefing: Briefing, angulos: list[dict], formato: str,
                  frescor: Frescor, observacao: str = "", tema: str = "fundo-funil",
                  salvar: bool = True,
                  client: anthropic.Anthropic | None = None) -> Iterator[tuple[str, object]]:
    """Gera em streaming. Emite ('delta', texto) e termina com ('fim', Resultado)."""
    client = client or anthropic.Anthropic()

    pedacos: list[str] = []
    try:
        with client.messages.stream(
            model=MODELO,
            max_tokens=MAX_TOKENS,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            cache_control={"type": "ephemeral"},
            system=montar_system(briefing),
            messages=[{"role": "user", "content": montar_pedido(angulos, formato, observacao)}],
        ) as stream:
            for texto in stream.text_stream:
                pedacos.append(texto)
                yield ("delta", texto)
            resposta = stream.get_final_message()
    except TypeError as e:
        # A SDK só resolve a credencial na hora do request. Sem api_key,
        # auth_token nem perfil do `ant auth login`, ela levanta TypeError.
        if "authentication" not in str(e).lower():
            raise
        raise CredencialAusente(
            "Nenhuma credencial da Anthropic encontrada. Defina ANTHROPIC_API_KEY."
        ) from e

    if resposta.stop_reason == "refusal":
        detalhe = getattr(resposta, "stop_details", None)
        motivo = getattr(detalhe, "explanation", None) or "sem detalhe"
        raise RuntimeError(f"O modelo recusou a geração: {motivo}")

    markdown = "".join(pedacos).strip()
    if not markdown:
        raise RuntimeError("A resposta veio vazia.")

    conteudo = f"{_cabecalho(briefing, angulos, frescor)}\n\n{markdown}\n"

    caminho = None
    if salvar and escrita_permitida():
        pasta = RAIZ / "clientes" / briefing.slug / "copies"
        pasta.mkdir(parents=True, exist_ok=True)
        caminho = pasta / f"{date.today():%Y-%m-%d}-{tema}.md"
        caminho.write_text(conteudo, encoding="utf-8")

    uso = resposta.usage
    yield ("fim", Resultado(
        markdown=conteudo,
        arquivo=caminho.name if caminho else None,
        achados=lintar(conteudo, briefing.usa_preco),
        tokens_entrada=uso.input_tokens,
        tokens_saida=uso.output_tokens,
        cache_lido=getattr(uso, "cache_read_input_tokens", 0) or 0,
    ))


def gerar(**kwargs) -> Resultado:
    """Versão não-streaming, para testes e uso em script."""
    for tipo, carga in gerar_eventos(**kwargs):
        if tipo == "fim":
            return carga
    raise RuntimeError("stream terminou sem resultado")


def _cabecalho(briefing: Briefing, angulos: list[dict], frescor: Frescor) -> str:
    nomes = ", ".join(a["nome"] for a in angulos)
    sync = frescor.ultima_sincronizacao or "desconhecida"
    return (
        f"# {briefing.nome} — {date.today():%d/%m/%Y}\n\n"
        f"> Ângulo escolhido pelo gestor: {nomes}\n"
        f"> Base sincronizada com o Drive em: {sync}\n"
        f"> Gerado pelo painel do agente de copy."
    )


def lintar(conteudo: str, usa_preco: bool) -> list[dict]:
    """Roda o mesmo linter da linha de comando, sem duplicar as regras.

    O linter trabalha sobre arquivo; em serverless só /tmp é gravável.
    """
    arquivo = tempfile.NamedTemporaryFile(
        "w", suffix=".md", delete=False, encoding="utf-8", dir=tempfile.gettempdir()
    )
    arquivo.write(conteudo)
    arquivo.close()
    try:
        return [
            {"linha": a.linha, "codigo": a.codigo, "descricao": a.descricao, "trecho": a.trecho}
            for a in verificar(Path(arquivo.name), usa_preco)
        ]
    finally:
        Path(arquivo.name).unlink(missing_ok=True)
