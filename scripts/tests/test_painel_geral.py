"""Testa o agrupamento do Painel Geral Consolidado (scripts/contrato/painel_geral.py).

Uso:  python3 scripts/tests/test_painel_geral.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "contrato"))
import painel_geral as p  # noqa: E402

STRACT = [("Date", "Account Name", "Spend (Cost, Amount Spent)", "Campaign Name", "Cliente")]
CRM = [("Cliente", "Plataforma", "Data/Hora", "Nome", "Telefone", "Origem", "Etapa", "Campanha")]


def st(dia, cliente, gasto, campanha="CAMP A"):
    return (datetime.fromisoformat(dia), "conta", gasto, campanha, cliente)


def crm(quando, cliente, fone, etapa, origem="Meta Ads", campanha="CAMP A"):
    return (cliente, "Meta Ads", datetime.fromisoformat(quando), "Fulano de Tal", fone, origem, etapa, campanha)


def test_historico_vira_pessoa_unica_com_funil_e_etapa_atual():
    d = p.agregar(
        STRACT + [st("2026-09-02", "Atlantica", 300.0), st("2026-09-03", "Atlantica", 100.0)],
        CRM + [
            crm("2026-09-02T10:00:00", "Atlantica", 5511999990001.0, "Fez Contato"),
            crm("2026-09-02T10:00:00", "Atlantica", 5511999990001.0, "Qualificado"),
            crm("2026-09-02T10:00:00", "Atlantica", 5511999990001.0, "Perdido"),  # qualificou, hoje perdido
            crm("2026-09-02T10:00:00", "Atlantica", 5511999990001.0, "Perdido"),  # linha repetida
            crm("2026-09-06T10:00:00", "Atlantica", 5511999990002.0, "Agendamento"),
            crm("2026-08-30T10:00:00", "Atlantica", 5511999990003.0, "Fez Contato"),  # lead de agosto
        ],
    )
    c = d["meses"]["2026-09"]["Tiago"]["contas"][0]
    assert (c["gasto"], c["leads"], c["qualificados"], c["agendados"], c["perdidos"]) == (400.0, 2, 2, 1, 1)
    assert c["cpl"] == 200.0 and c["cpag"] == 400.0 and c["dentro"] is False
    assert d["meses"]["2026-08"]["Tiago"]["leads"] == 1
    assert "Pinheiros" in d["meses"]["2026-09"]["Tiago"]["sem_dados"]


def test_semanas_dias_e_campanhas():
    d = p.agregar(
        STRACT + [st("2026-09-14", "Mabruk", 50.0), st("2026-09-21", "Mabruk", 30.0, "CAMP B")],
        CRM + [crm("2026-09-15T09:00:00", "Mabruk", 5511911110000.0, "Fez Contato"),
               crm("2026-09-22T09:00:00", "Mabruk", 5511911110001.0, "Fez Contato", campanha="."),
               crm("2026-09-22T09:30:00", "Mabruk", 5511911110002.0, "Fez Contato", campanha="23294274719")],
    )
    c = d["clientes"]["Mabruk"]
    assert [w["semana"] for w in c["semanas"]] == ["2026-09-14", "2026-09-21"]
    assert c["semanas"][0]["cpl"] == 50.0 and c["semanas"][1]["leads"] == 2
    assert {k["campanha"] for k in c["campanhas"]["2026-09"]} == {"CAMP A", "CAMP B"}  # "." e ID saem
    assert [x["dia"] for x in c["dias"]] == ["2026-09-14", "2026-09-15", "2026-09-21", "2026-09-22"]


def test_google_fora_do_cpl_e_sem_dado_pessoal():
    d = p.agregar(
        STRACT + [st("2026-10-01", "EFGE", 80.0)],
        CRM + [crm("2026-10-01T09:00:00", "EFGE", 5511988887777.0, "Fez Contato"),
               crm("2026-10-01T10:00:00", "EFGE", 5511988887778.0, "Fez Contato", origem="Google Ads")],
    )
    c = d["meses"]["2026-10"]["Michele"]["contas"][0]
    assert c["leads"] == 2 and c["cpl"] == 80.0 and c["origens"] == {"Meta Ads": 1, "Google Ads": 1}
    texto = json.dumps(d, ensure_ascii=False)
    assert "Fulano" not in texto and "5511988887777" not in texto


if __name__ == "__main__":
    testes = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in testes:
        t()
    print(f"{len(testes)} testes ok")
