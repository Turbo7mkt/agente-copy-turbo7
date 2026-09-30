"""Soma o Meta Ads do Stract por conta, gestor e mês para o contrato de resultados.

Entrada: a aba "Stract Clientes" da planilha "Stract - Clientes Visão Geral"
(fileId 19UuY5so8bPyOPYvoMMMeh58Z7Wnr4WktvXhZJy_39hY), exportada como CSV.
Saída:   docs/contrato-dados.json, que o painel docs/contrato-resultados.html lê.

Regra do contrato: lead é conversa iniciada no WhatsApp OU lead de formulário.
A extração do Stract só traz conversas, então o gasto das campanhas de
formulário ("FORM" no nome) sai separado, para o painel avisar que ali faltam
leads. Quando a coluna de leads de formulário entrar no Stract, basta somá-la
em `leads` — o nome dela vai em COLUNAS_LEAD.

Uso:
    python3 scripts/contrato/meta_stract.py <stract.csv> [saida.json]
"""
import csv
import io
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SAIDA_PADRAO = RAIZ / "docs" / "contrato-dados.json"

MESES = ("2026-09", "2026-10", "2026-11", "2026-12")  # setembro é a base
CPL_META = 40.0

COL_DATA = "Date"
COL_CONTA = "Account Name"
COL_GASTO = "Spend (Cost, Amount Spent)"
COL_CAMPANHA = "Campaign Name"
COLUNAS_LEAD = ("Action Messaging Conversations Started (Onsite Conversion)",)

# Carteira de cada gestor, tirada das abas das planilhas "Controle dos Gestores"
# em 30/09/2026. Conta nova ou troca de gestor: mude aqui.
CARTEIRA = {
    "Micheli": [
        "DIANA PLANEJADOS NOVA", "Diana Prime - T7 NOVA", "Camminare Italinea - T7",
        "Casa Nova I TURBO 7 - NOVA", "Fast T7", "Mabruk Italínea - T7",
        "Tonol Planejados T7 NOVA", "Maison Ettuali T7 NOVA", "Planeta Móveis Sp",
        "EFGE - T7", "Decoralle - T7", "Moinhos - Turbo 7", "Turbo 7 - Higienópolis",
    ],
    "Tiago Vianna": [
        "Atlantica Italínea [NOVA T7]", "Pinheiro´s planejados 2", "Formobili - T7",
        "Casa e Cozinha - T7", "PREEMIER-TURBO 7", "Mhavi - T7",
        "CA01 - Mendes e Machado", "Nova Design T7",
        "CA - Italínea Móvel Max - Boleto/PIX",
    ],
    "Davi": [],
}
SEM_GESTOR = "Sem gestor"


def numero(texto):
    """Stract exporta no formato brasileiro: 1.234,56."""
    texto = (texto or "").strip()
    if not texto:
        return 0.0
    return float(texto.replace(".", "").replace(",", "."))


def gestor_da_conta(conta):
    for gestor, contas in CARTEIRA.items():
        if conta in contas:
            return gestor
    return SEM_GESTOR


def agregar(linhas):
    contas = defaultdict(lambda: defaultdict(lambda: {"gasto": 0.0, "leads": 0.0, "gasto_form": 0.0}))
    ultima = ""
    for r in linhas:
        mes = (r.get(COL_DATA) or "")[:7]
        if mes not in MESES:
            continue
        ultima = max(ultima, r[COL_DATA])
        gasto = numero(r.get(COL_GASTO))
        c = contas[mes][r[COL_CONTA]]
        c["gasto"] += gasto
        c["leads"] += sum(numero(r.get(col)) for col in COLUNAS_LEAD)
        if "FORM" in (r.get(COL_CAMPANHA) or "").upper():
            c["gasto_form"] += gasto

    meses = {}
    for mes, por_conta in contas.items():
        gestores = defaultdict(lambda: {"gasto": 0.0, "leads": 0.0, "gasto_form": 0.0, "contas": []})
        for conta, v in sorted(por_conta.items(), key=lambda kv: -kv[1]["gasto"]):
            v = {k: round(x, 2) for k, x in v.items()}
            v["cpl"] = round(v["gasto"] / v["leads"], 2) if v["leads"] else None
            v["dentro"] = v["cpl"] is not None and v["cpl"] <= CPL_META
            g = gestores[gestor_da_conta(conta)]
            g["contas"].append({"conta": conta, **v})
            for k in ("gasto", "leads", "gasto_form"):
                g[k] = round(g[k] + v[k], 2)
        for g in gestores.values():
            g["cpl"] = round(g["gasto"] / g["leads"], 2) if g["leads"] else None
        meses[mes] = dict(gestores)
    return {
        "atualizado_em": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "dados_ate": ultima,
        "fonte": 'Google Drive · "Stract - Clientes Visão Geral" (19UuY5so8bPyOPYvoMMMeh58Z7Wnr4WktvXhZJy_39hY)',
        "regra_lead": "conversa iniciada no WhatsApp ou lead de formulário",
        "leads_de_formulario_na_fonte": False,
        "cpl_meta": CPL_META,
        "carteira": CARTEIRA,
        "meses": meses,
    }


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    texto = Path(argv[1]).read_text(encoding="utf-8-sig")
    dados = agregar(csv.DictReader(io.StringIO(texto)))
    saida = Path(argv[2]) if len(argv) > 2 else SAIDA_PADRAO
    saida.write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for mes, gestores in sorted(dados["meses"].items()):
        for nome, g in gestores.items():
            print(f"{mes} {nome:14s} gasto {g['gasto']:>11.2f}  leads {g['leads']:>6.0f}  CPL {g['cpl']}")
    print(f"→ {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
