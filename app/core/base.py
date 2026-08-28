"""Leitura da base de conhecimento: briefings, ângulos e frescor do Drive.

Tudo aqui é determinístico e testável. O modelo não participa de nenhuma
decisão deste módulo — ele só recebe o resultado.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
CLIENTES = RAIZ / "clientes"
REGRAS = RAIZ / "base-conhecimento" / "regras"
MANIFEST = RAIZ / "base-conhecimento" / "MANIFEST.yaml"

DIAS_ATE_BASE_VELHA = 7
DIAS_ATE_BRIEFING_VELHO = 60

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)


# --------------------------------------------------------------------------
# Briefing
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Briefing:
    slug: str
    dados: dict
    corpo: str

    @property
    def nome(self) -> str:
        return self.dados.get("nome") or self.slug

    @property
    def usa_preco(self) -> bool:
        return self.dados.get("usa_preco") is True

    @property
    def atualizado_em(self) -> date | None:
        return _como_data(self.dados.get("atualizado_em"))

    @property
    def dias_desde_atualizacao(self) -> int | None:
        d = self.atualizado_em
        return None if d is None else (date.today() - d).days

    @property
    def prova_google_contestada(self) -> bool:
        """A seção de provas marcou a nota do Google com ⚠️?

        O briefing usa ⚠️ para prova que existe mas não pode virar anúncio —
        loja em rebranding, perfil duplicado, avaliação ruim em destaque.
        """
        for linha in self.corpo.splitlines():
            if "⚠️" in linha and re.search(r"google|nota|avalia", linha, re.IGNORECASE):
                return True
        return False

    def campo_confirmado(self, campo: str) -> bool:
        valor = self.dados.get(campo)
        return valor is not None and str(valor).strip().lower() not in {"", "null", "none"}

    def secao(self, titulo: str) -> str:
        """Extrai uma seção `## Titulo` do corpo do briefing."""
        padrao = re.compile(
            rf"^##\s+{re.escape(titulo)}\s*$(.*?)(?=^##\s|\Z)",
            re.MULTILINE | re.DOTALL,
        )
        achado = padrao.search(self.corpo)
        return achado.group(1).strip() if achado else ""


def carregar_briefing(slug: str) -> Briefing:
    caminho = CLIENTES / slug / "briefing.md"
    if not caminho.is_file():
        raise FileNotFoundError(f"briefing não encontrado para '{slug}'")
    return _parse_briefing(slug, caminho.read_text(encoding="utf-8"))


def _parse_briefing(slug: str, texto: str) -> Briefing:
    achado = FRONTMATTER_RE.match(texto)
    if not achado:
        raise ValueError(f"briefing de '{slug}' sem frontmatter YAML")
    dados = yaml.safe_load(achado.group(1)) or {}
    return Briefing(slug=slug, dados=dados, corpo=achado.group(2))


def listar_clientes() -> list[dict]:
    """Clientes com briefing, exceto o template."""
    saida = []
    if not CLIENTES.is_dir():
        return saida
    for pasta in sorted(CLIENTES.iterdir()):
        if not pasta.is_dir() or pasta.name.startswith("_"):
            continue
        if not (pasta / "briefing.md").is_file():
            continue
        try:
            b = carregar_briefing(pasta.name)
        except (ValueError, FileNotFoundError):
            continue
        saida.append({
            "slug": b.slug,
            "nome": b.nome,
            "praca": b.dados.get("praca"),
            "usa_preco": b.usa_preco,
            "atualizado_em": str(b.atualizado_em) if b.atualizado_em else None,
            "copies": len(listar_copies(b.slug)),
        })
    return saida


def listar_copies(slug: str) -> list[dict]:
    pasta = CLIENTES / slug / "copies"
    if not pasta.is_dir():
        return []
    arquivos = sorted(pasta.glob("*.md"), reverse=True)
    return [{"arquivo": a.name, "bytes": a.stat().st_size} for a in arquivos]


# --------------------------------------------------------------------------
# Ângulos
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Angulo:
    numero: int
    nome: str
    gatilho: str
    fala_com: str
    eixo: str
    requer: tuple[str, ...] = field(default=())


LINHA_ANGULO_RE = re.compile(r"^\|\s*(\d+)\s*\|(.+)\|\s*$")


def carregar_angulos(caminho: Path | None = None) -> list[Angulo]:
    """Lê a tabela de ângulos de `base-conhecimento/regras/angulos.md`."""
    texto = (caminho or (REGRAS / "angulos.md")).read_text(encoding="utf-8")
    angulos: list[Angulo] = []
    for linha in texto.splitlines():
        achado = LINHA_ANGULO_RE.match(linha)
        if not achado:
            continue
        campos = [c.strip() for c in achado.group(2).split("|")]
        # nome | gatilho | fala_com | eixo | requer
        if len(campos) < 5:
            continue
        requer = _parse_requer(campos[4])
        angulos.append(Angulo(
            numero=int(achado.group(1)),
            nome=campos[0],
            gatilho=campos[1],
            fala_com=campos[2],
            eixo=campos[3],
            requer=requer,
        ))
    return angulos


def _parse_requer(bruto: str) -> tuple[str, ...]:
    limpo = bruto.replace("`", "").strip()
    if not limpo or limpo in {"—", "-", "–"}:
        return ()
    return tuple(t.strip() for t in limpo.split(",") if t.strip())


def filtrar_angulos(angulos: list[Angulo], briefing: Briefing,
                    ja_usados: set[int] | None = None) -> tuple[list[dict], list[dict]]:
    """Separa os ângulos em (disponíveis, bloqueados-com-motivo).

    Esta é a regra do passo 3 do protocolo. O gestor só vê o que o briefing
    sustenta — o que falta prova nem chega a ser oferecido.
    """
    ja_usados = ja_usados or set()
    disponiveis: list[dict] = []
    bloqueados: list[dict] = []

    for a in angulos:
        motivo = _motivo_bloqueio(a, briefing)
        registro = {
            "numero": a.numero,
            "nome": a.nome,
            "gatilho": a.gatilho,
            "fala_com": a.fala_com,
            "eixo": a.eixo,
        }
        if motivo:
            bloqueados.append({**registro, "motivo": motivo})
        else:
            disponiveis.append({**registro, "ja_usado": a.numero in ja_usados})
    return disponiveis, bloqueados


def _motivo_bloqueio(a: Angulo, b: Briefing) -> str | None:
    for token in a.requer:
        if token == "prova:google":
            if b.prova_google_contestada:
                return "a nota do Google está marcada com ⚠️ no briefing"
            if not _tem_nota(b):
                return "nenhuma unidade tem nota do Google no briefing"
        elif token.startswith("campo:"):
            campo = token.split(":", 1)[1]
            if not b.campo_confirmado(campo):
                return f"`{campo}` não está confirmado no briefing"
        elif token == "preco":
            if not b.usa_preco:
                return "este cliente é `usa_preco: false`"
    return None


def _tem_nota(b: Briefing) -> bool:
    for unidade in b.dados.get("unidades") or []:
        if isinstance(unidade, dict) and unidade.get("google_nota") is not None:
            return True
    return False


# --------------------------------------------------------------------------
# Frescor da base (passo 2 do protocolo)
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Frescor:
    ultima_sincronizacao: date | None
    dias: int | None
    status: str          # "ok" | "velha" | "desconhecida"
    mensagem: str


def checar_frescor(caminho: Path | None = None) -> Frescor:
    arquivo = caminho or MANIFEST
    if not arquivo.is_file():
        return Frescor(None, None, "desconhecida",
                       "MANIFEST.yaml não encontrado — não dá para saber a idade da base.")
    dados = yaml.safe_load(arquivo.read_text(encoding="utf-8")) or {}
    quando = _como_data(dados.get("ultima_sincronizacao"))
    if quando is None:
        return Frescor(None, None, "desconhecida",
                       "MANIFEST.yaml sem `ultima_sincronizacao`.")
    dias = (date.today() - quando).days
    if dias > DIAS_ATE_BASE_VELHA:
        return Frescor(quando, dias, "velha",
                       f"Base sincronizada há {dias} dias. Rode `/sync-drive` antes de gerar.")
    return Frescor(quando, dias, "ok",
                   f"Base sincronizada há {dias} dia(s), em {quando}.")


def _como_data(valor) -> date | None:
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        try:
            return datetime.strptime(valor.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None
    return None
