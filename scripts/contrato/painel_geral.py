"""Agrupa o "Painel Geral Consolidado" por cliente, gestor e período para o contrato.

Fonte: Google Drive · "Painel Geral Consolidado"
       (fileId 1A5u5lf4a3kzphmpstXp9AV3eVXJMFUAMRbOb8puToAU), exportado em .xlsx.
Saída: docs/contrato-dados.json, que o painel docs/contrato-resultados.html lê.

Como os dados se comportam (lido em 30/09/2026):
  - aba CRM é um HISTÓRICO: cada mudança de etapa acrescenta uma linha e repete
    a Data/Hora de criação do lead. Há sequências inteiras reapendadas e linhas
    idênticas. Por isso:
      lead          = pessoa única (cliente + telefone), no período da criação;
      etapa atual   = a última linha da pessoa na aba (ordem do arquivo);
      funil         = até onde a pessoa já chegou (Qualificado, Agendamento,
                      Comprou), mesmo que depois tenha virado Perdido;
  - aba STRACT é gasto do Meta por dia e por anúncio, já com a coluna Cliente.
    Anúncios com o mesmo nome no mesmo dia são anúncios diferentes: soma-se tudo;
  - Origem do lead: Meta Ads, Nao rastreada ou Google Ads. O investido é só Meta,
    então o CPL usa leads Meta + não rastreados; os do Google contam como lead
    mas ficam fora do CPL;
  - Campanha do CRM casa com a do STRACT em parte das campanhas; onde casa,
    sai o CPL por campanha.

Grupos gerados: mês (contrato), semana (segunda a domingo), dia (últimos 35),
etapa do funil, origem e campanha, por cliente e por carteira de gestor.
Só somas saem daqui: nome e telefone dos leads nunca vão para o JSON.

Uso:
    python3 scripts/contrato/painel_geral.py <painel.xlsx> [saida.json]
"""
import json
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SAIDA_PADRAO = RAIZ / "docs" / "contrato-dados.json"
FONTE = 'Google Drive · "Painel Geral Consolidado" (1A5u5lf4a3kzphmpstXp9AV3eVXJMFUAMRbOb8puToAU)'

CPL_META = 40.0
DIAS_SERIE = 35
QUALIFICADO = {"Qualificado", "Agendamento", "Comprou"}
AGENDADO = {"Agendamento", "Comprou"}
ORIGEM_FORA_DO_CPL = {"Google Ads"}

# Carteira de cada gestor pelo nome do cliente no Painel Geral (coluna Cliente).
# Tirada das abas das planilhas "Controle dos Gestores" em 30/09/2026.
# Cliente que ainda não entrou no Painel Geral aparece como "sem dados".
CARTEIRA = {
    "Michele": [
        "Diana GRU", "Diana Prime", "Camminare", "Casa Nova", "Fast", "Mabruk",
        "Tonol", "Maison", "Planeta", "EFGE", "Decoralle",
        "Di Casa Moinhos", "Di Casa Higienópolis",
    ],
    "Tiago": [
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


def para_data(valor):
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor or "").strip().replace("/", "-")[:10]  # "2026/07/30 às 08:08"
    try:
        return date.fromisoformat(texto)
    except ValueError:
        return None


def semana_de(d):
    inicio = d - timedelta(days=d.weekday())
    return inicio.isoformat()


def telefone(valor):
    if isinstance(valor, float):
        return str(int(valor))
    return str(valor or "").strip()


def numero(valor):
    if isinstance(valor, str):
        return float(valor.replace(".", "").replace(",", ".") or 0)
    return float(valor or 0)


def campanha_valida(texto):
    """O CRM às vezes grava ID numérico ou mensagem de erro do Meta no lugar do nome."""
    if not isinstance(texto, str) or not texto.strip():
        return None
    if "permission" in texto.lower() or texto.strip().isdigit():
        return None
    if not any(ch.isalpha() for ch in texto):  # ".", "-", "|"
        return None
    return texto.strip()


def indices(cabecalho, nomes):
    cab = [str(c).strip() if c is not None else "" for c in cabecalho]
    return {n: cab.index(n) for n in nomes}


def novo():
    return {"gasto": 0.0, "leads": 0, "leads_cpl": 0, "qualificados": 0, "agendados": 0,
            "compras": 0, "perdidos": 0, "em_aberto": 0}


def fechar(v):
    """Arredonda e calcula os custos e taxas de um grupo."""
    v = dict(v)
    v["gasto"] = round(v["gasto"], 2)
    v["cpl"] = round(v["gasto"] / v["leads_cpl"], 2) if v["leads_cpl"] else None
    v["cpq"] = round(v["gasto"] / v["qualificados"], 2) if v["qualificados"] else None
    v["cpag"] = round(v["gasto"] / v["agendados"], 2) if v["agendados"] else None
    v["tx_qualif"] = round(v["qualificados"] / v["leads"] * 100, 1) if v["leads"] else None
    v["tx_agend"] = round(v["agendados"] / v["leads"] * 100, 1) if v["leads"] else None
    return v


def somar(destino, origem):
    for k in novo():
        destino[k] += origem[k]


def agregar(linhas_stract, linhas_crm):
    """Recebe as abas como listas de linhas (a primeira é o cabeçalho)."""
    ist = indices(linhas_stract[0], ("Date", "Spend (Cost, Amount Spent)", "Campaign Name", "Cliente"))
    icr = indices(linhas_crm[0], ("Cliente", "Data/Hora", "Telefone", "Origem", "Etapa", "Campanha"))

    # grupos[(periodo_tipo, periodo, cliente)] → métricas
    grupos = defaultdict(novo)
    camp = defaultdict(lambda: {"gasto": 0.0, "leads": 0, "leads_cpl": 0})
    origens = defaultdict(lambda: defaultdict(int))
    ultima = None

    for r in linhas_stract[1:]:
        d, cliente = para_data(r[ist["Date"]]), r[ist["Cliente"]]
        if not d or not cliente:
            continue
        ultima = max(ultima, d) if ultima else d
        g = numero(r[ist["Spend (Cost, Amount Spent)"]])
        for chave in (("mes", d.strftime("%Y-%m")), ("semana", semana_de(d)), ("dia", d.isoformat())):
            grupos[(*chave, cliente)]["gasto"] += g
        c = campanha_valida(r[ist["Campaign Name"]])
        if c:
            camp[(d.strftime("%Y-%m"), cliente, c)]["gasto"] += g

    # CRM: uma entrada por pessoa, na ordem do arquivo
    pessoas = {}
    for r in linhas_crm[1:]:
        cliente, fone = r[icr["Cliente"]], telefone(r[icr["Telefone"]])
        d = para_data(r[icr["Data/Hora"]])
        if not cliente or not fone or not d:
            continue
        p = pessoas.setdefault((cliente, fone), {"criado": d, "etapas": set(), "atual": None,
                                                 "origem": r[icr["Origem"]], "campanha": None})
        p["criado"] = min(p["criado"], d)
        p["etapas"].add(r[icr["Etapa"]])
        p["atual"] = r[icr["Etapa"]]
        p["campanha"] = campanha_valida(r[icr["Campanha"]]) or p["campanha"]

    for (cliente, _), p in pessoas.items():
        d, e = p["criado"], p["etapas"]
        v = novo()
        v["leads"] = 1
        v["leads_cpl"] = int(p["origem"] not in ORIGEM_FORA_DO_CPL)
        v["qualificados"] = int(bool(e & QUALIFICADO))
        v["agendados"] = int(bool(e & AGENDADO))
        v["compras"] = int("Comprou" in e)
        v["perdidos"] = int(p["atual"] == "Perdido")
        v["em_aberto"] = int(p["atual"] not in ("Perdido", "Comprou"))
        for chave in (("mes", d.strftime("%Y-%m")), ("semana", semana_de(d)), ("dia", d.isoformat())):
            somar(grupos[(*chave, cliente)], v)
        origens[(d.strftime("%Y-%m"), cliente)][p["origem"] or "Sem origem"] += 1
        if p["campanha"]:
            k = camp[(d.strftime("%Y-%m"), cliente, p["campanha"])]
            k["leads"] += 1
            k["leads_cpl"] += v["leads_cpl"]

    clientes_com_dados = sorted({c for (_, _, c) in grupos})

    # contrato: mês → gestor → totais + clientes
    meses = {}
    for mes in sorted({p for (t, p, _) in grupos if t == "mes"}):
        gestores = {}
        for g in list(CARTEIRA) + [SEM_GESTOR]:
            da_carteira = [c for c in clientes_com_dados if gestor_do_cliente(c) == g and ("mes", mes, c) in grupos]
            sem_dados = sorted(c for c in CARTEIRA.get(g, []) if ("mes", mes, c) not in grupos)
            if not da_carteira and not sem_dados:
                continue
            total = novo()
            contas = []
            for c in da_carteira:
                somar(total, grupos[("mes", mes, c)])
                contas.append({"conta": c, **fechar(grupos[("mes", mes, c)]),
                               "origens": dict(origens[(mes, c)])})
            for conta in contas:
                conta["dentro"] = conta["cpl"] is not None and conta["cpl"] <= CPL_META
            contas.sort(key=lambda v: -v["gasto"])
            gestores[g] = {**fechar(total), "contas": contas, "sem_dados": sem_dados}
        meses[mes] = gestores

    # série por cliente: semanas, últimos dias e campanhas por mês
    hoje = ultima or date.today()
    clientes = {}
    for c in clientes_com_dados:
        semanas = [{"semana": p, **fechar(grupos[("semana", p, c)])}
                   for p in sorted({p for (t, p, cc) in grupos if t == "semana" and cc == c})]
        dias = [{"dia": p, "gasto": round(grupos[("dia", p, c)]["gasto"], 2), "leads": grupos[("dia", p, c)]["leads"],
                 "leads_cpl": grupos[("dia", p, c)]["leads_cpl"], "qualificados": grupos[("dia", p, c)]["qualificados"]}
                for p in sorted({p for (t, p, cc) in grupos if t == "dia" and cc == c})
                if date.fromisoformat(p) > hoje - timedelta(days=DIAS_SERIE)]
        campanhas = defaultdict(list)
        for (mes, cc, nome), v in camp.items():
            if cc != c:
                continue
            campanhas[mes].append({"campanha": nome, "gasto": round(v["gasto"], 2), "leads": v["leads"],
                                   "cpl": round(v["gasto"] / v["leads_cpl"], 2) if v["leads_cpl"] and v["gasto"] else None})
        for lista in campanhas.values():
            lista.sort(key=lambda v: (-v["gasto"], -v["leads"]))
        clientes[c] = {"gestor": gestor_do_cliente(c), "semanas": semanas, "dias": dias, "campanhas": dict(campanhas)}

    return {
        "atualizado_em": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "dados_ate": hoje.isoformat() if ultima else None,
        "fonte": FONTE,
        "regra_lead": "pessoa única no CRM (formulário ou WhatsApp), no período em que foi criada",
        "regra_cpl": "investido no Meta ÷ leads de origem Meta ou não rastreada",
        "leads_de_formulario_na_fonte": True,
        "cpl_meta": CPL_META,
        "carteira": CARTEIRA,
        "meses": meses,
        "clientes": clientes,
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
    saida.write_text(json.dumps(dados, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    for mes, gestores in sorted(dados["meses"].items()):
        for nome, g in gestores.items():
            print(f"{mes} {nome:14s} investido {g['gasto']:>10.2f}  leads {g['leads']:>5}  qualif {g['qualificados']:>4}"
                  f"  agend {g['agendados']:>3}  CPL {g['cpl']}  CPAG {g['cpag']}")
    print(f"{len(dados['clientes'])} clientes · dados até {dados['dados_ate']} → {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
