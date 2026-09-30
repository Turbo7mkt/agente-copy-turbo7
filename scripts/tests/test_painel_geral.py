"""Testa a soma do Painel Geral Consolidado (scripts/contrato/painel_geral.py).

Uso:  python3 scripts/tests/test_painel_geral.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "contrato"))
import painel_geral as p  # noqa: E402

STRACT = [("Date", "Account Name", "Spend (Cost, Amount Spent)", "Campaign Name", "Cliente")]
CRM = [("Cliente", "Plataforma", "Data/Hora", "Nome", "Telefone", "Origem", "Etapa")]


def st(dia, cliente, gasto):
    return (datetime.fromisoformat(dia), "conta", gasto, "camp", cliente)


def crm(quando, cliente, fone, etapa):
    return (cliente, "Meta Ads", quando, "Fulano de Tal", fone, "Meta Ads", etapa)


def test_lead_unico_no_mes_do_primeiro_registro():
    d = p.agregar(
        STRACT + [st("2026-09-02", "Atlantica", 300.0), st("2026-09-03", "Atlantica", 100.0)],
        CRM + [
            crm("2026/09/02 às 10:00:00", "Atlantica", 5511999990001.0, "Fez Contato"),
            crm("2026/09/05 às 10:00:00", "Atlantica", 5511999990001.0, "Qualificado"),  # mesma pessoa
            crm("2026/09/06 às 10:00:00", "Atlantica", 5511999990002.0, "Agendamento"),
            crm("2026/08/30 às 10:00:00", "Atlantica", 5511999990003.0, "Fez Contato"),  # agosto
            crm("2026/09/01 às 10:00:00", "Atlantica", 5511999990003.0, "Perdido"),
        ],
    )
    t = d["meses"]["2026-09"]["Tiago Vianna"]
    c = t["contas"][0]
    assert (c["gasto"], c["leads"], c["qualificados"], c["agendados"]) == (400.0, 2, 2, 1)
    assert c["cpl"] == 200.0 and c["dentro"] is False
    assert "Pinheiros" in t["sem_dados"]
    assert d["dados_ate"] == "2026-09-03"


def test_json_sem_dado_pessoal():
    d = p.agregar(STRACT + [st("2026-10-01", "Mabruk", 40.0)], CRM + [crm("2026/10/01 às 09:00:00", "Mabruk", 5511988887777.0, "Fez Contato")])
    texto = json.dumps(d, ensure_ascii=False)
    assert "Fulano" not in texto and "5511988887777" not in texto
    assert d["meses"]["2026-10"]["Micheli"]["contas"][0]["dentro"] is True


def test_cliente_sem_gestor():
    d = p.agregar(STRACT + [st("2026-09-10", "Mobile Prime", 90.0)], CRM)
    g = d["meses"]["2026-09"][p.SEM_GESTOR]
    assert g["cpl"] is None and g["contas"][0]["conta"] == "Mobile Prime"


if __name__ == "__main__":
    testes = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in testes:
        t()
    print(f"{len(testes)} testes ok")
