#!/usr/bin/env python3
"""Testes do linter de copy. Rode com: python3 scripts/tests/test_lint_copy.py"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lint_copy import briefing_permite_preco, linhas_de_copy, verificar  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]


class TestVerificar(unittest.TestCase):
    def _achados(self, texto, permitir_preco=False, tmp_name="copy.md"):
        arquivo = Path(self.tmp) / tmp_name
        arquivo.write_text(texto, encoding="utf-8")
        return verificar(arquivo, permitir_preco)

    def setUp(self):
        import tempfile

        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = self._tmpdir.name

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_copy_limpa_nao_gera_achado(self):
        texto = (
            "Tem uma parte do projeto que só aparece quando a montagem termina.\n"
            "Entregamos em 35 dias úteis com garantia de 5 anos.\n"
        )
        self.assertEqual(self._achados(texto), [])

    def test_pega_urgencia_artificial(self):
        achados = self._achados("Últimas vagas para agendar seu projeto.\n")
        self.assertEqual([a.codigo for a in achados], ["R2-urgencia"])

    def test_pega_superlativo_vazio(self):
        achados = self._achados("Somos a melhor loja de planejados da cidade.\n")
        self.assertEqual([a.codigo for a in achados], ["R2-superlativo"])

    def test_pega_cliche(self):
        achados = self._achados("Realize o sonho da casa própria com a gente.\n")
        self.assertTrue(any(a.codigo == "R7-cliche" for a in achados))

    def test_pega_preco_em_reais(self):
        achados = self._achados("Cozinha completa por R$ 19.900.\n")
        self.assertTrue(any(a.codigo == "PRECO" for a in achados))

    def test_pega_parcelamento(self):
        achados = self._achados("Sua casa em 24x de R$ 980,00 sem juros.\n")
        codigos = {a.codigo for a in achados}
        self.assertIn("PRECO", codigos)

    def test_pega_desconto_percentual(self):
        achados = self._achados("São 40% de desconto à vista.\n")
        self.assertTrue(any(a.codigo == "PRECO" for a in achados))

    def test_preco_liberado_quando_permitido(self):
        achados = self._achados("Cozinha por R$ 19.900.\n", permitir_preco=True)
        self.assertEqual([a for a in achados if a.codigo == "PRECO"], [])

    def test_pega_exclamacao_em_serie(self):
        achados = self._achados("Agende agora!!\n")
        self.assertTrue(any(a.codigo == "R2-exclamacao" for a in achados))

    def test_exclamacao_unica_passa(self):
        achados = self._achados("Vamos desenhar a sua primeira etapa!\n")
        self.assertEqual([a for a in achados if a.codigo == "R2-exclamacao"], [])

    def test_pega_emoji_em_excesso(self):
        achados = self._achados("Sua cozinha nova 🔥🔥🔥 agora\n")
        self.assertTrue(any(a.codigo == "R2-emoji" for a in achados))

    def test_um_emoji_passa(self):
        achados = self._achados("Sua cozinha nova 🚀 agora\n")
        self.assertEqual([a for a in achados if a.codigo == "R2-emoji"], [])

    def test_ignora_bloco_de_codigo(self):
        texto = "Copy limpa aqui.\n\n```\nÚltimas vagas! R$ 19.900\n```\n\nMais copy limpa.\n"
        self.assertEqual(self._achados(texto), [])

    def test_reporta_numero_de_linha_correto(self):
        texto = "linha um\nlinha dois\nÚltimas vagas hoje\n"
        achados = self._achados(texto)
        self.assertEqual(achados[0].linha, 3)

    def test_nao_confunde_palavra_dentro_de_outra(self):
        # "correr" contém "corre", mas não deve disparar a regra de urgência
        achados = self._achados("O projeto vai correr dentro do cronograma.\n")
        self.assertEqual([a for a in achados if a.codigo == "R2-urgencia"], [])


class TestLinhasDeCopy(unittest.TestCase):
    def test_remove_conteudo_entre_fences(self):
        texto = "a\n```\nb\n```\nc\n"
        self.assertEqual(linhas_de_copy(texto), [(1, "a"), (5, "c")])


class TestBriefingPermitePreco(unittest.TestCase):
    def test_le_usa_preco_do_briefing_irmao(self):
        alvo = RAIZ / "clientes" / "dicasa-italinea" / "copies" / "qualquer.md"
        # DiCasa está com usa_preco: false no briefing versionado
        self.assertFalse(briefing_permite_preco(alvo))

    def test_sem_briefing_assume_falso(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(briefing_permite_preco(Path(tmp) / "x.md"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
