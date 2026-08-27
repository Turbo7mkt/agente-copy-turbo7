#!/usr/bin/env python3
"""Verifica copies da Turbo7 contra as regras inegociáveis.

Uso:
    python3 scripts/lint_copy.py clientes/dicasa-italinea/copies/2026-08-27.md
    python3 scripts/lint_copy.py clientes/**/copies/*.md
    python3 scripts/lint_copy.py --allow-price arquivo.md

Regras cobertas (base-conhecimento/regras/regras-copy.md):
    R2  urgência artificial, superlativos vazios, exclamação em série, emoji em excesso
    R7  clichês de mercado / português de anúncio traduzido
    PRECO  preço, parcela ou desconto quando o briefing tem usa_preco: false

Sai com código 1 se encontrar qualquer violação.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

MAX_EMOJI_POR_LINHA = 1

# Blocos de código e citações de referência não são copy entregável.
FENCE_RE = re.compile(r"^\s*```")

EMOJI_RE = re.compile(
    "["
    "\U0001f300-\U0001f5ff"
    "\U0001f600-\U0001f64f"
    "\U0001f680-\U0001f6ff"
    "\U0001f900-\U0001f9ff"
    "\U0001fa70-\U0001faff"
    "☀-⛿"
    "✀-➿"
    "]"
)

EXCLAMACAO_SERIE_RE = re.compile(r"!\s*!")


@dataclass(frozen=True)
class Regra:
    codigo: str
    descricao: str
    padrao: re.Pattern[str]


def _kw(*termos: str) -> re.Pattern[str]:
    """Compila termos como alternativas com fronteira de palavra, sem case."""
    corpo = "|".join(termos)
    return re.compile(rf"(?<!\w)(?:{corpo})(?!\w)", re.IGNORECASE)


REGRAS_BASE: tuple[Regra, ...] = (
    Regra(
        "R2-urgencia",
        "urgência artificial",
        _kw(
            r"últimas? vagas?",
            r"últimas? unidades?",
            r"corre\b",
            r"não perca",
            r"só até (?:hoje|amanhã|sexta|domingo|segunda)",
            r"por tempo limitado",
            r"imperdível",
            r"aproveite agora",
            r"vagas? limitadas?",
            r"acaba (?:hoje|amanhã)",
        ),
    ),
    Regra(
        "R2-superlativo",
        "superlativo vazio",
        _kw(
            r"o melhor",
            r"a melhor",
            r"os melhores",
            r"as melhores",
            r"qualidade incomparável",
            r"excelência",
            r"simplesmente perfeito",
            r"incrível",
            r"inigualável",
            r"insuperável",
            r"padrão de excelência",
            r"alto padrão de qualidade",
        ),
    ),
    Regra(
        "R7-cliche",
        "clichê de mercado",
        _kw(
            r"realize o sonho",
            r"o sonho da casa própria",
            r"transforme (?:o seu|seu) lar",
            r"do jeito que você sempre sonhou",
            r"a casa dos seus sonhos",
            r"você merece",
            r"venha (?:nos )?conhecer e se apaixonar",
        ),
    ),
)

REGRA_PRECO = Regra(
    "PRECO",
    "preço, parcela ou desconto com usa_preco: false",
    re.compile(
        r"(?<!\w)(?:"
        r"R\$"
        r"|\d+\s*x\s*(?:de\s*)?R?\$?\s*\d"          # 24x 980,00 / 24x de 980
        r"|a partir de\s+R?\$?\s*\d"
        r"|\d+\s*%\s*(?:de\s*)?(?:desconto|off)"
        r"|parcel(?:a|as|ado|amento)"
        r"|sem juros"
        r"|entrada de\s+R?\$?\s*\d"
        r")",
        re.IGNORECASE,
    ),
)


@dataclass(frozen=True)
class Achado:
    arquivo: Path
    linha: int
    codigo: str
    descricao: str
    trecho: str

    def __str__(self) -> str:
        return (
            f"{self.arquivo}:{self.linha}: [{self.codigo}] {self.descricao} "
            f"→ {self.trecho!r}"
        )


def briefing_permite_preco(arquivo: Path) -> bool:
    """Procura o briefing irmão (clientes/<slug>/briefing.md) e lê usa_preco."""
    for pai in arquivo.resolve().parents:
        candidato = pai / "briefing.md"
        if candidato.is_file():
            texto = candidato.read_text(encoding="utf-8")
            match = re.search(r"^usa_preco:\s*(\S+)", texto, re.MULTILINE)
            return bool(match) and match.group(1).strip().lower() == "true"
    return False


def linhas_de_copy(texto: str) -> list[tuple[int, str]]:
    """Devolve (nº da linha, conteúdo) ignorando blocos de código."""
    resultado: list[tuple[int, str]] = []
    dentro_de_fence = False
    for numero, linha in enumerate(texto.splitlines(), start=1):
        if FENCE_RE.match(linha):
            dentro_de_fence = not dentro_de_fence
            continue
        if dentro_de_fence:
            continue
        resultado.append((numero, linha))
    return resultado


def verificar(arquivo: Path, permitir_preco: bool) -> list[Achado]:
    texto = arquivo.read_text(encoding="utf-8")
    regras = list(REGRAS_BASE)
    if not permitir_preco:
        regras.append(REGRA_PRECO)

    achados: list[Achado] = []
    for numero, linha in linhas_de_copy(texto):
        for regra in regras:
            for match in regra.padrao.finditer(linha):
                achados.append(
                    Achado(arquivo, numero, regra.codigo, regra.descricao, match.group(0))
                )

        if EXCLAMACAO_SERIE_RE.search(linha):
            achados.append(
                Achado(arquivo, numero, "R2-exclamacao", "exclamação em série", linha.strip()[:60])
            )

        emojis = EMOJI_RE.findall(linha)
        if len(emojis) > MAX_EMOJI_POR_LINHA:
            achados.append(
                Achado(
                    arquivo,
                    numero,
                    "R2-emoji",
                    f"emoji em excesso ({len(emojis)} na linha, máx {MAX_EMOJI_POR_LINHA})",
                    "".join(emojis),
                )
            )

    return achados


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("arquivos", nargs="+", type=Path, help="arquivos de copy (.md)")
    parser.add_argument(
        "--allow-price",
        action="store_true",
        help="permite preço mesmo sem usa_preco: true no briefing",
    )
    args = parser.parse_args(argv)

    todos: list[Achado] = []
    for arquivo in args.arquivos:
        if not arquivo.is_file():
            print(f"aviso: {arquivo} não encontrado, ignorando", file=sys.stderr)
            continue
        permitir = args.allow_price or briefing_permite_preco(arquivo)
        todos.extend(verificar(arquivo, permitir))

    for achado in todos:
        print(achado)

    if todos:
        print(f"\n{len(todos)} violação(ões). Reescreva antes de entregar.", file=sys.stderr)
        return 1

    print("Sem violações de padrão. Falta rodar o checklist manual: base-conhecimento/regras/checklist-qa.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
