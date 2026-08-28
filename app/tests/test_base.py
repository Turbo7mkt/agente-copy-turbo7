#!/usr/bin/env python3
"""Testes do núcleo do painel. Rode com: python3 app/tests/test_base.py"""

import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from app.core.base import (  # noqa: E402
    Angulo,
    _parse_briefing,
    _parse_requer,
    carregar_angulos,
    checar_frescor,
    filtrar_angulos,
)


def briefing_de(frontmatter: str, corpo: str = ""):
    return _parse_briefing("teste", f"---\n{frontmatter}\n---\n{corpo}")


COMPLETO = """slug: teste
nome: Loja Teste
unidades:
  - nome: Centro
    google_nota: 4.9
    google_avaliacoes: 120
usa_preco: false
prazo_entrega: 35 dias úteis
garantia: 5 anos
atualizado_em: 2026-08-01"""

MAGRO = """slug: magro
nome: Loja Magra
unidades: []
usa_preco: true
prazo_entrega: null
garantia: null
atualizado_em: 2026-08-01"""


class TestBriefing(unittest.TestCase):
    def test_le_frontmatter_e_corpo(self):
        b = briefing_de(COMPLETO, "## Provas disponíveis\n\n- Nota 4,9\n")
        self.assertEqual(b.nome, "Loja Teste")
        self.assertFalse(b.usa_preco)
        self.assertIn("Provas", b.corpo)

    def test_campo_confirmado(self):
        b = briefing_de(COMPLETO)
        self.assertTrue(b.campo_confirmado("prazo_entrega"))
        self.assertTrue(b.campo_confirmado("garantia"))

    def test_campo_null_nao_conta_como_confirmado(self):
        b = briefing_de(MAGRO)
        self.assertFalse(b.campo_confirmado("prazo_entrega"))
        self.assertFalse(b.campo_confirmado("garantia"))

    def test_detecta_prova_google_contestada(self):
        b = briefing_de(COMPLETO, "## Provas disponíveis\n\n> ⚠️ Nota do Google fora de uso.\n")
        self.assertTrue(b.prova_google_contestada)

    def test_prova_limpa_nao_e_contestada(self):
        b = briefing_de(COMPLETO, "## Provas disponíveis\n\n- Nota 4,9 com 120 avaliações\n")
        self.assertFalse(b.prova_google_contestada)

    def test_alerta_sem_relacao_com_google_nao_contesta_a_nota(self):
        b = briefing_de(COMPLETO, "## Restrições\n\n- ⚠️ Não citar concorrente pelo nome.\n")
        self.assertFalse(b.prova_google_contestada)

    def test_extrai_secao(self):
        corpo = "## Provas disponíveis\n\nnota alta\n\n## Restrições\n\nsem preço\n"
        b = briefing_de(COMPLETO, corpo)
        self.assertEqual(b.secao("Restrições"), "sem preço")

    def test_frontmatter_ausente_e_erro(self):
        with self.assertRaises(ValueError):
            _parse_briefing("x", "# sem frontmatter\n")


class TestParseRequer(unittest.TestCase):
    def test_travessao_significa_sem_requisito(self):
        self.assertEqual(_parse_requer("—"), ())

    def test_remove_crases(self):
        self.assertEqual(_parse_requer("`campo:garantia`"), ("campo:garantia",))

    def test_aceita_lista(self):
        self.assertEqual(
            _parse_requer("`preco`, `campo:garantia`"),
            ("preco", "campo:garantia"),
        )


class TestFiltroDeAngulos(unittest.TestCase):
    """O passo 3 do protocolo: o gestor só vê o que o briefing sustenta."""

    CATALOGO = [
        Angulo(1, "Livre", "Objeção", "todos", "eixo", ()),
        Angulo(6, "Dias úteis", "Racional", "obra", "prazo", ("campo:prazo_entrega",)),
        Angulo(10, "Prova social", "Racional", "cético", "nota", ("prova:google",)),
        Angulo(13, "Cinco anos", "Racional", "durabilidade", "garantia", ("campo:garantia",)),
        Angulo(15, "Valor fechado", "Racional", "preço", "preço", ("preco",)),
    ]

    def test_briefing_completo_libera_o_que_tem_prova(self):
        b = briefing_de(COMPLETO, "## Provas\n\n- Nota 4,9\n")
        disp, bloq = filtrar_angulos(self.CATALOGO, b)
        numeros = {a["numero"] for a in disp}
        self.assertEqual(numeros, {1, 6, 10, 13})
        self.assertEqual([a["numero"] for a in bloq], [15])

    def test_usa_preco_false_bloqueia_angulo_de_preco(self):
        b = briefing_de(COMPLETO)
        _, bloq = filtrar_angulos(self.CATALOGO, b)
        motivo = next(a["motivo"] for a in bloq if a["numero"] == 15)
        self.assertIn("usa_preco", motivo)

    def test_campo_null_bloqueia_angulo_dependente(self):
        b = briefing_de(MAGRO)
        _, bloq = filtrar_angulos(self.CATALOGO, b)
        bloqueados = {a["numero"] for a in bloq}
        self.assertIn(6, bloqueados)   # prazo null
        self.assertIn(13, bloqueados)  # garantia null

    def test_usa_preco_true_libera_angulo_de_preco(self):
        b = briefing_de(MAGRO)
        disp, _ = filtrar_angulos(self.CATALOGO, b)
        self.assertIn(15, {a["numero"] for a in disp})

    def test_prova_contestada_bloqueia_prova_social(self):
        b = briefing_de(COMPLETO, "> ⚠️ nota do Google fora de uso até unificar perfis\n")
        _, bloq = filtrar_angulos(self.CATALOGO, b)
        motivo = next(a["motivo"] for a in bloq if a["numero"] == 10)
        self.assertIn("⚠️", motivo)

    def test_sem_nota_nenhuma_bloqueia_prova_social(self):
        b = briefing_de(MAGRO)
        _, bloq = filtrar_angulos(self.CATALOGO, b)
        motivo = next(a["motivo"] for a in bloq if a["numero"] == 10)
        self.assertIn("nota do Google", motivo)

    def test_marca_angulo_ja_usado_sem_bloquear(self):
        b = briefing_de(COMPLETO, "- Nota 4,9\n")
        disp, _ = filtrar_angulos(self.CATALOGO, b, ja_usados={1})
        primeiro = next(a for a in disp if a["numero"] == 1)
        self.assertTrue(primeiro["ja_usado"])

    def test_todo_angulo_cai_em_exatamente_um_lado(self):
        b = briefing_de(MAGRO)
        disp, bloq = filtrar_angulos(self.CATALOGO, b)
        self.assertEqual(len(disp) + len(bloq), len(self.CATALOGO))


class TestCatalogoReal(unittest.TestCase):
    def test_le_a_biblioteca_versionada(self):
        angulos = carregar_angulos()
        self.assertGreaterEqual(len(angulos), 14)
        self.assertTrue(all(a.nome for a in angulos))

    def test_tokens_do_catalogo_sao_conhecidos(self):
        validos = {"prova:google", "campo:prazo_entrega", "campo:garantia", "preco"}
        for a in carregar_angulos():
            for token in a.requer:
                self.assertIn(token, validos, f"ângulo {a.numero} usa token desconhecido")

    def test_preemier_nao_recebe_angulo_de_prova_social(self):
        """Regressão: a loja tem os perfis do Google divididos."""
        from app.core.base import carregar_briefing

        b = carregar_briefing("preemier-decore-italinea")
        _, bloq = filtrar_angulos(carregar_angulos(), b)
        self.assertIn(10, {a["numero"] for a in bloq})


class TestFrescor(unittest.TestCase):
    def _manifest(self, conteudo):
        f = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8")
        f.write(conteudo)
        f.close()
        self.addCleanup(lambda: Path(f.name).unlink(missing_ok=True))
        return Path(f.name)

    def test_base_recente_e_ok(self):
        hoje = date.today()
        f = checar_frescor(self._manifest(f"ultima_sincronizacao: {hoje}\n"))
        self.assertEqual(f.status, "ok")
        self.assertEqual(f.dias, 0)

    def test_base_com_mais_de_sete_dias_e_velha(self):
        antiga = date.today() - timedelta(days=8)
        f = checar_frescor(self._manifest(f"ultima_sincronizacao: {antiga}\n"))
        self.assertEqual(f.status, "velha")
        self.assertIn("sync-drive", f.mensagem)

    def test_exatamente_sete_dias_ainda_e_ok(self):
        limite = date.today() - timedelta(days=7)
        f = checar_frescor(self._manifest(f"ultima_sincronizacao: {limite}\n"))
        self.assertEqual(f.status, "ok")

    def test_manifest_sem_data_e_desconhecida(self):
        f = checar_frescor(self._manifest("arquivos: []\n"))
        self.assertEqual(f.status, "desconhecida")

    def test_manifest_ausente_e_desconhecida(self):
        f = checar_frescor(Path("/nao/existe/MANIFEST.yaml"))
        self.assertEqual(f.status, "desconhecida")


if __name__ == "__main__":
    unittest.main(verbosity=2)
