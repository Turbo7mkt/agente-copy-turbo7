#!/usr/bin/env python3
"""Testes do linter de copy. Rode com: python3 scripts/tests/test_lint_copy.py"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lint_copy import (  # noqa: E402
    blocos_de_copy,
    briefing_permite_preco,
    linhas_de_copy,
    verificar,
)

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


class TestNotaDeConformidade(unittest.TestCase):
    """Regressão: a nota declara o que foi evitado, e isso não é violação."""

    def _achados(self, texto, usa_preco=False):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(texto)
            caminho = Path(f.name)
        self.addCleanup(lambda: caminho.unlink(missing_ok=True))
        return verificar(caminho, usa_preco)

    NOTA = (
        "\n## Nota de conformidade\n\n"
        "- **Preço, parcela ou desconto:** `usa_preco: false`, nada disso entrou.\n"
        "- **Promessas evitadas:** excelência de atendimento, o melhor da região.\n"
        "- Nenhuma urgência artificial: sem últimas vagas, sem corre.\n"
    )

    def test_nota_nao_gera_violacao(self):
        texto = "Entregamos em 35 dias úteis com garantia de 5 anos.\n" + self.NOTA
        self.assertEqual(self._achados(texto), [])

    def test_violacao_antes_da_nota_ainda_pega(self):
        texto = "Somos a melhor loja! Últimas vagas.\n" + self.NOTA
        codigos = {a.codigo for a in self._achados(texto)}
        self.assertIn("R2-superlativo", codigos)
        self.assertIn("R2-urgencia", codigos)

    def test_preco_na_nota_nao_reprova_cliente_sem_preco(self):
        """O caso real do Casa & Cozinha em 29/09."""
        texto = "A gaveta que continua firme depois de anos.\n" + self.NOTA
        self.assertEqual([a for a in self._achados(texto) if a.codigo == "PRECO"], [])

    def test_preco_so_na_nota_nao_exige_rodape(self):
        texto = ("Projeto sob medida para o seu espaço.\n"
                 "\n## Nota de conformidade\n\n"
                 "- A tabela de R$ 34.900 ficou de fora por decisão do diagnóstico.\n")
        self.assertEqual([a for a in self._achados(texto, True) if a.codigo == "MARCA-rodape"], [])

    def test_titulo_da_nota_em_qualquer_nivel(self):
        for nivel in ["#", "##", "###"]:
            texto = f"Copy limpa.\n\n{nivel} Nota de conformidade\n\nSem excelência aqui.\n"
            self.assertEqual(self._achados(texto), [], f"nível {nivel} não cortou")


class TestTamanho(unittest.TestCase):
    """O Meta trunca. Copy que estoura não fica completa — fica cortada."""

    def _achados(self, texto, usa_preco=True):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(texto)
            caminho = Path(f.name)
        self.addCleanup(lambda: caminho.unlink(missing_ok=True))
        return verificar(caminho, usa_preco)

    def _codigos(self, texto, usa_preco=True):
        return [a.codigo for a in self._achados(texto, usa_preco)]

    def test_titulo_curto_passa(self):
        self.assertNotIn("TAMANHO-titulo", self._codigos("**Título:** Comece por um ambiente\n"))

    def test_titulo_longo_reprova(self):
        # O caso real da Mhavi em 05/10: 55 caracteres, o Meta exibe 40.
        texto = "**Título:** Comece por um ambiente. A casa inteira agradece depois.\n"
        self.assertIn("TAMANHO-titulo", self._codigos(texto))

    def test_titulo_nao_conta_a_marcacao(self):
        # 38 caracteres de texto, 42 com os asteriscos. Quem lê não vê asterisco.
        texto = "**Título:** **Projeto que cabe no seu prazo**\n"
        self.assertNotIn("TAMANHO-titulo", self._codigos(texto))

    def test_descricao_longa_reprova(self):
        texto = "**Descrição:** Valor fechado por metragem · Showroom em São Paulo\n"
        self.assertIn("TAMANHO-descricao", self._codigos(texto))

    def test_descricao_curta_passa(self):
        self.assertNotIn("TAMANHO-descricao", self._codigos("**Descrição:** Showroom em SP\n"))

    def test_copy_curta_passa(self):
        texto = "A gaveta que continua firme depois de anos. Venha nos fazer uma visita.\n"
        self.assertNotIn("TAMANHO-copy", self._codigos(texto))

    def test_copy_longa_reprova(self):
        self.assertIn("TAMANHO-copy", self._codigos("palavra " * 70))

    def test_soma_de_paragrafos_reprova(self):
        """O caso da Mhavi: três parágrafos de ~300, nenhum gritante sozinho."""
        paragrafo = "Frase que ocupa espaço sem chamar atenção por si. " * 3
        texto = f"## ÂNGULO — teste\n\n{paragrafo}\n\n{paragrafo}\n\n{paragrafo}\n"
        self.assertIn("TAMANHO-copy", self._codigos(texto))

    def test_cada_cabecalho_tem_seu_proprio_orcamento(self):
        """Dez copies curtas não somam até reprovar — cada uma conta sozinha."""
        curta = "Uma dor, uma prova, um CTA. Venha nos fazer uma visita."
        texto = "".join(f"## ÂNGULO {n}\n\n{curta}\n\n" for n in range(1, 11))
        self.assertNotIn("TAMANHO-copy", self._codigos(texto))

    def test_nota_de_conformidade_nao_conta_no_tamanho(self):
        texto = "Copy curta e limpa.\n\n## Nota de conformidade\n\n" + ("explicação longa " * 60)
        self.assertNotIn("TAMANHO-copy", self._codigos(texto))


class TestBlocosDeCopy(unittest.TestCase):
    def _blocos(self, texto):
        return [t for _, t in blocos_de_copy(linhas_de_copy(texto))]

    def test_junta_paragrafos_do_mesmo_cabecalho(self):
        self.assertEqual(self._blocos("## A\n\num\n\ndois\n"), ["um dois"])

    def test_cabecalho_separa(self):
        self.assertEqual(self._blocos("## A\n\num\n\n## B\n\ndois\n"), ["um", "dois"])

    def test_tira_rotulo_de_bloco(self):
        self.assertEqual(self._blocos("**SOLUÇÃO**\n\nO texto.\n"), ["O texto."])

    def test_tira_metadado(self):
        texto = "**Gatilho:** Desejo\n**CTA do botão Meta Ads:** Cadastre-se\n\nO texto.\n"
        self.assertEqual(self._blocos(texto), ["O texto."])

    def test_tira_citacao_e_tabela(self):
        self.assertEqual(self._blocos("> procedência\n\n| a | b |\n\nO texto.\n"), ["O texto."])

    def test_tira_a_marcacao_do_texto(self):
        self.assertEqual(self._blocos("O **texto** com `marca`.\n"), ["O texto com marca."])


class TestLinhasDeCopy(unittest.TestCase):
    def test_remove_conteudo_entre_fences(self):
        texto = "a\n```\nb\n```\nc\n"
        self.assertEqual(linhas_de_copy(texto), [(1, "a"), (5, "c")])

    def test_corta_na_nota_de_conformidade(self):
        texto = "copy\n\n## Nota de conformidade\n\nexcelência\n"
        self.assertEqual([l for _, l in linhas_de_copy(texto)], ["copy", ""])


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
