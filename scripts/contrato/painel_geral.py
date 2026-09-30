"""Soma o "Painel Geral Consolidado" por cliente, gestor e mês para o contrato.

Fonte: Google Drive · "Painel Geral Consolidado"
       (fileId 1A5u5lf4a3kzphmpstXp9AV3eVXJMFUAMRbOb8puToAU), exportado em .xlsx.
  - aba STRACT: investimento por dia, já com a coluna Cliente;
  - aba CRM: um registro por mudança de etapa de cada lead.
Saída: docs/contrato-dados.json, que o painel docs/contrato-resultados.html lê.

Regras do contrato:
  - lead = pessoa única (cliente + telefone) que entrou no CRM, venha de
    formulário ou de conversa no WhatsApp; conta no mês do primeiro registro;
  - qualificado = lead que chegou a Qualificado, Agendamento ou Comprou;
  - CPL = investido ÷ leads, meta de R$ 40 em todas as contas.

Só somas saem daqui: nome e telefone dos leads nunca vão para o JSON.

Uso:
    python3 scripts/contrato/painel_geral.py <painel.xlsx> [saida.json]
"""
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SAIDA_PADRAO = RAIZ / "docs" / "contrato-dados.json"
FONTE = 'Google Drive · "Painel Geral Consolidado" (1A5u5lf4a3kzphmpstXp9AV3eVXJMFUAMRbOb8puToAU)'

MESES = ("2026-09", "2026-10", "2026-11", "2026-12")  # setembro é a base
CPL_META = 40.0
ETAPAS_QUALIFICADO = {"Qualificado", "Agendamento", "Comprou"}
ETAPAS_AGENDADO = {"Agendamento", "Comprou"}

# Carteira de cada gestor pelo nome do cliente no Painel Geral (coluna Cliente).
# Tirada das abas das planilhas "Controle dos Gestores" em 30/09/2026.
# Cliente que ainda não entrou no Painel Geral aparece como "sem dados".
CARTEIRA = {
    "Micheli": [
        "Diana GRU", "Diana Prime", "Camminare", "Casa Nova", "Fast", "Mabruk",
        "Tonol", "Maison", "Planeta", "EFGE", "Decoralle",
        "Di Casa Moinhos", "Di Casa Higienópolis",
    ],
    "Tiago Vianna": [
        "Atlantica", "Nova Design", "Pinheiros", "Formobili", "Casa & Cozinha",
        "Preemier", "Mhavi", "Móvel Max", "BS Grajaú",
    ],
}
SEM_GESTOR = "Sem gestor"


def gestor_do_cliente(cliente):
    for gestor, clientes in CARTEIRA.items():
        if cliente in clientes:
            return gestor
    return SEM_GESTOR


def mes_de(valor):
    if hasattr(valor, "strftime"):
        return valor.strftime("%Y-%m")
    texto = str(valor or "")
    return texto[:7].replace("/", "-")  # "2026/07/30 às 08:08" → "2026-07"


def telefone(valor):
    if isinstance(valor, float):
        return str(int(valor))
    return str(valor or "").strip()


def indices(cabecalho, nomes):
    cab = [str(c).strip() if c is not None else "" for c in cabecalho]
    return {n: cab.index(n) for n in nomes}


def agregar(linhas_stract, linhas_crm):
    """Recebe as abas como listas de linhas (a primeira é o cabeçalho)."""
    ist = indices(linhas_stract[0], ("Date", "Spend (Cost, Amount Spent)", "Cliente"))
    icr = indices(linhas_crm[0], ("Cliente", "Data/Hora", "Telefone", "Etapa"))

    gasto = defaultdict(float)  # (mes, cliente) → investido
    ultima = ""
    for r in linhas_stract[1:]:
        mes, cliente = mes_de(r[ist["Date"]]), r[ist["Cliente"]]
        if mes not in MESES or not cliente:
            continue
        valor = r[ist["Spend (Cost, Amount Spent)"]]
        gasto[(mes, cliente)] += float(valor or 0) if not isinstance(valor, str) else float(valor.replace(".", "").replace(",", ".") or 0)
        dia = r[ist["Date"]].strftime("%Y-%m-%d") if hasattr(r[ist["Date"]], "strftime") else str(r[ist["Date"]])[:10]
        ultima = max(ultima, dia)

    primeiro, etapas = {}, defaultdict(set)
    for r in linhas_crm[1:]:
        cliente, fone = r[icr["Cliente"]], telefone(r[icr["Telefone"]])
        if not cliente or not fone:
            continue
        chave = (cliente, fone)
        mes = mes_de(r[icr["Data/Hora"]])
        if len(mes) == 7 and (chave not in primeiro or mes < primeiro[chave]):
            primeiro[chave] = mes
        etapas[chave].add(r[icr["Etapa"]])

    leads, qualif, agend = defaultdict(int), defaultdict(int), defaultdict(int)
    for (cliente, fone), mes in primeiro.items():
        if mes not in MESES:
            continue
        e = etapas[(cliente, fone)]
        leads[(mes, cliente)] += 1
        qualif[(mes, cliente)] += bool(e & ETAPAS_QUALIFICADO)
        agend[(mes, cliente)] += bool(e & ETAPAS_AGENDADO)

    meses = {}
    for mes in MESES:
        clientes = {c for (m, c) in list(gasto) + list(leads) if m == mes}
        if not clientes:
            continue
        gestores = {}
        for g in list(CARTEIRA) + [SEM_GESTOR]:
            da_carteira = [c for c in clientes if gestor_do_cliente(c) == g]
            sem_dados = [c for c in CARTEIRA.get(g, []) if c not in clientes]
            if not da_carteira and not sem_dados:
                continue
            contas = []
            for c in da_carteira:
                v = {"conta": c, "gasto": round(gasto[(mes, c)], 2), "leads": leads[(mes, c)],
                     "qualificados": qualif[(mes, c)], "agendados": agend[(mes, c)]}
                v["cpl"] = round(v["gasto"] / v["leads"], 2) if v["leads"] else None
                v["dentro"] = v["cpl"] is not None and v["cpl"] <= CPL_META
                contas.append(v)
            contas.sort(key=lambda v: -v["gasto"])
            tot = {k: round(sum(v[k] for v in contas), 2) for k in ("gasto", "leads", "qualificados", "agendados")}
            tot["cpl"] = round(tot["gasto"] / tot["leads"], 2) if tot["leads"] else None
            gestores[g] = {**tot, "contas": contas, "sem_dados": sorted(sem_dados)}
        meses[mes] = gestores

    return {
        "atualizado_em": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "dados_ate": ultima,
        "fonte": FONTE,
        "regra_lead": "pessoa única no CRM (formulário ou WhatsApp), no mês do primeiro registro",
        "leads_de_formulario_na_fonte": True,
        "cpl_meta": CPL_META,
        "carteira": CARTEIRA,
        "meses": meses,
    }


def ler_xlsx(caminho):
    try:
        import openpyxl
    except ImportError:
        sys.exit("Falta o openpyxl: pip install openpyxl")
    wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    abas = {ws.title.strip().upper(): [r for r in ws.iter_rows(values_only=True)] for ws in wb.worksheets}
    for nome in ("STRACT", "CRM"):
        if nome not in abas:
            sys.exit(f"A planilha não tem a aba {nome}. Abas: {', '.join(abas)}")
    return abas["STRACT"], abas["CRM"]


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    dados = agregar(*ler_xlsx(argv[1]))
    saida = Path(argv[2]) if len(argv) > 2 else SAIDA_PADRAO
    saida.write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for mes, gestores in sorted(dados["meses"].items()):
        for nome, g in gestores.items():
            print(f"{mes} {nome:14s} investido {g['gasto']:>11.2f}  leads {g['leads']:>5}  CPL {g['cpl']}  sem dados: {len(g['sem_dados'])}")
    print(f"→ {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
