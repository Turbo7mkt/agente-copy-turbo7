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


class TestRegrasDaMarca(unittest.TestCase):
    """Regras da skill italinea-identidade-visual, só valem com preço liberado."""

    def setUp(self):
        import tempfile

        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = self._tmpdir.name

    def tearDown(self):
        self._tmpdir.cleanup()

    def _achados(self, texto, permitir_preco=True):
        arquivo = Path(self.tmp) / "copy.md"
        arquivo.write_text(texto, encoding="utf-8")
        return verificar(arquivo, permitir_preco)

    RODAPE = "Condições válidas para projetos de até 50 m². Consulte a loja.\n"

    def _codigos(self, texto):
        return {a.codigo for a in self._achados(texto + self.RODAPE)}

    def test_preco_canonico_passa(self):
        self.assertNotIn("MARCA-preco-formato", self._codigos("Projeto completo por R$ 34.900.\n"))

    def test_pega_preco_sem_cifrao(self):
        self.assertIn("MARCA-preco-formato", self._codigos("Projeto completo por 34.900.\n"))

    def test_pega_preco_sem_espaco_apos_cifrao(self):
        self.assertIn("MARCA-preco-formato", self._codigos("Projeto completo por R$34.900.\n"))

    def test_pega_preco_com_centavos(self):
        self.assertIn("MARCA-preco-formato", self._codigos("Projeto completo por R$ 34.900,00.\n"))

    def test_pega_a_partir_de_grudado_no_numero(self):
        self.assertIn("MARCA-a-partir-de", self._codigos("Cozinha a partir de R$ 12.900.\n"))

    def test_pega_cta_fora_do_tom(self):
        self.assertIn("MARCA-cta", self._codigos("R$ 34.900. Clique aqui.\n"))

    def test_cta_aprovado_passa(self):
        self.assertNotIn("MARCA-cta", self._codigos("R$ 34.900. Venha nos fazer uma visita.\n"))

    def test_exige_rodape_legal_quando_ha_preco(self):
        achados = self._achados("Projeto completo por R$ 34.900.\n")
        self.assertTrue(any(a.codigo == "MARCA-rodape" for a in achados))

    def test_rodape_presente_satisfaz(self):
        achados = self._achados("Projeto completo por R$ 34.900.\n" + self.RODAPE)
        self.assertEqual([a for a in achados if a.codigo == "MARCA-rodape"], [])

    def test_sem_preco_nao_exige_rodape(self):
        achados = self._achados("Entrega em 35 dias úteis, garantia de 5 anos.\n")
        self.assertEqual([a for a in achados if a.codigo == "MARCA-rodape"], [])

    def test_regras_da_marca_nao_valem_sem_preco_liberado(self):
        # Cliente com usa_preco: false cai na regra PRECO, não nas de formatação
        achados = self._achados("Cozinha por 34.900.\n", permitir_preco=False)
        codigos = {a.codigo for a in achados}
        self.assertNotIn("MARCA-preco-formato", codigos)
        self.assertNotIn("MARCA-rodape", codigos)

    def test_nao_confunde_metragem_com_preco(self):
        self.assertNotIn("MARCA-preco-formato", self._codigos("Casa completa até 40m².\n"))


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
