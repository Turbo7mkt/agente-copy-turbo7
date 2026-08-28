#!/usr/bin/env python3
"""Testes da montagem do prompt — o caminho sem chave de API.

Nada aqui chama a rede: o prompt é montado a partir dos arquivos do repo.
Rode com: python3 app/tests/test_prompt.py
"""

import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from app.core.base import carregar_angulos, carregar_briefing, filtrar_angulos  # noqa: E402
from app.core.geracao import lintar, montar_pedido, montar_system  # noqa: E402


class TestMontarSystem(unittest.TestCase):
    def setUp(self):
        self.b = carregar_briefing("preemier-decore-italinea")
        self.prompt = montar_system(self.b)

    def test_carrega_as_regras(self):
        self.assertIn("Regras de copy", self.prompt)
        self.assertIn("urgência artificial", self.prompt)

    def test_carrega_os_formatos(self):
        self.assertIn("Formatos de entrega", self.prompt)

    def test_carrega_os_exemplos_de_tom(self):
        self.assertIn("Copies aprovadas", self.prompt)

    def test_embute_o_briefing_do_cliente(self):
        self.assertIn("Briefing do cliente", self.prompt)
        self.assertIn("preemier-decore-italinea", self.prompt)

    def test_leva_o_usa_preco_do_cliente(self):
        self.assertIn("usa_preco: true", self.prompt)

    def test_leva_as_restricoes(self):
        self.assertIn("Restrições", self.prompt)

    def test_proibe_inventar_prova(self):
        self.assertIn("NUNCA inventa prova", self.prompt)

    def test_briefing_sem_preco_vai_como_false(self):
        prompt = montar_system(carregar_briefing("dicasa-italinea"))
        self.assertIn("usa_preco: false", prompt)


class TestMontarPedido(unittest.TestCase):
    def _angulos(self, slug, numeros):
        b = carregar_briefing(slug)
        disponiveis, _ = filtrar_angulos(carregar_angulos(), b)
        return [a for a in disponiveis if a["numero"] in numeros]

    def test_nomeia_os_angulos_escolhidos(self):
        escolhidos = self._angulos("dicasa-italinea", {2})
        pedido = montar_pedido(escolhidos, "3 vídeos curtos")
        self.assertIn("Ninguém pergunta sobre o depois", pedido)

    def test_proibe_o_modelo_de_trocar_de_angulo(self):
        pedido = montar_pedido(self._angulos("dicasa-italinea", {2}), "3 vídeos")
        self.assertIn("Não substitua nenhum", pedido)
        self.assertIn("escolhidos pelo gestor", pedido)

    def test_leva_o_formato_pedido(self):
        pedido = montar_pedido(self._angulos("dicasa-italinea", {2}), "4 vídeos + 1 imagem")
        self.assertIn("4 vídeos + 1 imagem", pedido)

    def test_exige_nota_de_conformidade(self):
        pedido = montar_pedido(self._angulos("dicasa-italinea", {2}), "3 vídeos")
        self.assertIn("Nota de conformidade", pedido)

    def test_inclui_observacao_do_gestor(self):
        pedido = montar_pedido(self._angulos("dicasa-italinea", {2}), "3 vídeos", "priorizar Moinhos")
        self.assertIn("priorizar Moinhos", pedido)

    def test_observacao_vazia_nao_polui(self):
        pedido = montar_pedido(self._angulos("dicasa-italinea", {2}), "3 vídeos", "   ")
        self.assertNotIn("Observação do gestor", pedido)

    def test_varios_angulos_entram_todos(self):
        escolhidos = self._angulos("dicasa-italinea", {2, 3, 5})
        pedido = montar_pedido(escolhidos, "3 vídeos")
        self.assertEqual(pedido.count("gatilho"), 3)


class TestValidarCopyColada(unittest.TestCase):
    """A volta manual passa pelas mesmas regras da geração automática."""

    def test_reprova_urgencia_e_superlativo(self):
        achados = lintar("Últimas vagas! Somos a melhor loja.", usa_preco=False)
        codigos = {a["codigo"] for a in achados}
        self.assertIn("R2-urgencia", codigos)
        self.assertIn("R2-superlativo", codigos)

    def test_reprova_preco_em_cliente_sem_preco(self):
        achados = lintar("Cozinha por R$ 19.900.", usa_preco=False)
        self.assertIn("PRECO", {a["codigo"] for a in achados})

    def test_mesmo_texto_passa_em_cliente_com_preco_e_rodape(self):
        texto = "Cozinha completa por R$ 19.900. Condições válidas. Consulte a loja."
        self.assertEqual(lintar(texto, usa_preco=True), [])

    def test_copy_limpa_passa(self):
        texto = ("Tem uma parte do projeto que só aparece quando a montagem termina. "
                 "Entregamos em 35 dias úteis com garantia de 5 anos.")
        self.assertEqual(lintar(texto, usa_preco=False), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
