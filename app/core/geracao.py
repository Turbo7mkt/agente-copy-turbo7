"""Geração de copy: monta o prompt a partir da base e chama a Claude.

O protocolo dos 4 passos é cumprido *fora* do modelo — o briefing, as regras e
os ângulos permitidos já chegam resolvidos. O modelo escreve, não decide.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import anthropic

from .base import RAIZ, REGRAS, Briefing, Frescor

sys.path.insert(0, str(RAIZ / "scripts"))
from lint_copy import verificar  # noqa: E402

MODELO = "claude-opus-5"
MAX_TOKENS = 64_000


class CredencialAusente(RuntimeError):
    """Nenhuma credencial da Anthropic pôde ser resolvida no ambiente."""

MARCA = Path("/root/.claude/skills/synced")


def _ler(caminho: Path) -> str:
    return caminho.read_text(encoding="utf-8") if caminho.is_file() else ""


def _regras_da_marca() -> str:
    """Regras de oferta da skill `italinea-identidade-visual`, se instalada.

    A skill é da conta, não do repo. Quando ela não está no ambiente, as regras
    equivalentes já vivem em `regras-copy.md` e no checklist — o prompt segue
    válido, só perde o detalhamento de formato.
    """
    for candidato in MARCA.glob("*/italinea-identidade-visual/references/ofertas-e-copy.md"):
        return candidato.read_text(encoding="utf-8")
    return ""


def montar_system(briefing: Briefing) -> str:
    """Prompt estável — vai inteiro para o cache."""
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

    partes += [
        "",
        "## Briefing do cliente",
        f"```yaml\n{_dump_frontmatter(briefing)}\n```",
        briefing.corpo,
    ]
    return "\n".join(partes)


def _dump_frontmatter(briefing: Briefing) -> str:
    import yaml
    return yaml.safe_dump(briefing.dados, allow_unicode=True, sort_keys=False).strip()


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


@dataclass
class Resultado:
    markdown: str
    arquivo: str | None
    achados: list[dict]
    tokens_entrada: int
    tokens_saida: int
    cache_lido: int


def gerar(briefing: Briefing, angulos: list[dict], formato: str,
          frescor: Frescor, observacao: str = "", tema: str = "fundo-funil",
          salvar: bool = True, client: anthropic.Anthropic | None = None) -> Resultado:
    client = client or anthropic.Anthropic()

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
            resposta = stream.get_final_message()
    except TypeError as e:
        # A SDK só resolve a credencial na hora do request. Sem api_key,
        # auth_token nem perfil do `ant auth login`, ela levanta TypeError.
        if "authentication" not in str(e).lower():
            raise
        raise CredencialAusente(
            "Nenhuma credencial da Anthropic encontrada. Defina ANTHROPIC_API_KEY "
            "ou rode `ant auth login` no servidor."
        ) from e

    if resposta.stop_reason == "refusal":
        detalhe = getattr(resposta, "stop_details", None)
        motivo = getattr(detalhe, "explanation", None) or "sem detalhe"
        raise RuntimeError(f"O modelo recusou a geração: {motivo}")

    markdown = "".join(b.text for b in resposta.content if b.type == "text").strip()
    if not markdown:
        raise RuntimeError("A resposta veio vazia.")

    cabecalho = _cabecalho(briefing, angulos, frescor)
    conteudo = f"{cabecalho}\n\n{markdown}\n"

    caminho = None
    if salvar:
        pasta = RAIZ / "clientes" / briefing.slug / "copies"
        pasta.mkdir(parents=True, exist_ok=True)
        caminho = pasta / f"{date.today():%Y-%m-%d}-{tema}.md"
        caminho.write_text(conteudo, encoding="utf-8")

    achados = _lintar(conteudo, briefing, caminho)

    uso = resposta.usage
    return Resultado(
        markdown=conteudo,
        arquivo=caminho.name if caminho else None,
        achados=achados,
        tokens_entrada=uso.input_tokens,
        tokens_saida=uso.output_tokens,
        cache_lido=getattr(uso, "cache_read_input_tokens", 0) or 0,
    )


def _cabecalho(briefing: Briefing, angulos: list[dict], frescor: Frescor) -> str:
    nomes = ", ".join(a["nome"] for a in angulos)
    sync = frescor.ultima_sincronizacao or "desconhecida"
    return (
        f"# {briefing.nome} — {date.today():%d/%m/%Y}\n\n"
        f"> Ângulo escolhido pelo gestor: {nomes}\n"
        f"> Base sincronizada com o Drive em: {sync}\n"
        f"> Gerado pelo painel do agente de copy."
    )


def _lintar(conteudo: str, briefing: Briefing, caminho: Path | None) -> list[dict]:
    """Roda o mesmo linter da linha de comando, sem duplicar as regras."""
    import tempfile

    alvo = caminho
    temporario = None
    if alvo is None:
        temporario = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        temporario.write(conteudo)
        temporario.close()
        alvo = Path(temporario.name)

    try:
        achados = verificar(alvo, briefing.usa_preco)
        return [
            {"linha": a.linha, "codigo": a.codigo, "descricao": a.descricao, "trecho": a.trecho}
            for a in achados
        ]
    finally:
        if temporario is not None:
            Path(temporario.name).unlink(missing_ok=True)
