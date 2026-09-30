"""Testa a soma do Stract por conta, gestor e mês (scripts/contrato/meta_stract.py).

Uso:  python3 scripts/tests/test_meta_stract.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "contrato"))
import meta_stract as m  # noqa: E402

CONV = m.COLUNAS_LEAD[0]


def linha(data, conta, gasto, conversas, campanha="CAMPANHA I WPP"):
    return {m.COL_DATA: data, m.COL_CONTA: conta, m.COL_GASTO: gasto, m.COL_CAMPANHA: campanha, CONV: conversas}


def test_numero_brasileiro():
    assert m.numero("1.234,56") == 1234.56
    assert m.numero("0,3") == 0.3
    assert m.numero("") == 0.0


def test_soma_por_gestor_e_cpl():
    d = m.agregar([
        linha("2026-09-01", "Diana Prime - T7 NOVA", "400,00", "20"),
        linha("2026-09-02", "Diana Prime - T7 NOVA", "200,00", "10"),
        linha("2026-09-02", "Atlantica Italínea [NOVA T7]", "900,00", "10", "ATLANTICA I FORMS I 09/06"),
        linha("2026-08-31", "Diana Prime - T7 NOVA", "999,00", "1"),  # fora do contrato
    ])
    set_ = d["meses"]["2026-09"]
    assert "2026-08" not in d["meses"]
    assert set_["Micheli"]["gasto"] == 600.0 and set_["Micheli"]["leads"] == 30.0
    assert set_["Micheli"]["cpl"] == 20.0 and set_["Micheli"]["contas"][0]["dentro"] is True
    tiago = set_["Tiago Vianna"]
    assert tiago["cpl"] == 90.0 and tiago["contas"][0]["dentro"] is False
    assert tiago["gasto_form"] == 900.0
    assert d["dados_ate"] == "2026-09-02"


def test_conta_sem_gestor_e_sem_lead():
    d = m.agregar([linha("2026-10-05", "Conta Nova X", "100,00", "0")])
    g = d["meses"]["2026-10"][m.SEM_GESTOR]
    assert g["cpl"] is None and g["contas"][0]["dentro"] is False


if __name__ == "__main__":
    testes = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in testes:
        t()
    print(f"{len(testes)} testes ok")
