#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
capitale-umano.py — il portafoglio dentro la ricchezza totale: capitale finanziario, capitale umano
(i redditi da lavoro futuri) e capitale pensionistico (la pensione INPS futura), con cinque diagnosi.

Il capitale umano è il valore attuale dei redditi da lavoro futuri (Ibbotson, Milevsky, Chen e Zhu,
«Lifetime Financial Advice», CFA Institute Research Foundation 2007, eq. 2.1):

    HC = Σ_{t=1..N} E[h_t] / (1 + r_f + ν)^t,   h_t = (netto + TFR + contributo del datore) × (1 + g)^t
    E[h_t] = h_t × (1 − p_u × durata × (1 − sostituzione NASpI))

Una parte del capitale umano si comporta come un'azione, il resto come un'obbligazione: la quota
azionaria è un parametro esplicito del profilo di lavoro (profili-capitale-umano.csv), non una stima
personale. La pensione INPS è un blocco a sé, tutto obbligazionario.

Le cinque diagnosi: 1) bilancio patrimoniale totale; 2) esposizione azionaria del portafoglio contro
quella della ricchezza totale, con la riga di equivalenza facoltativa; 3) proiezione fino alla pensione
con una fascia Monte Carlo; 4) sovrapposizione tra il settore del proprio lavoro e il portafoglio;
5) sensibilità ai parametri.

È una LENTE, non un target: non modifica l'allocazione degli obiettivi né quella di it-rebalance.
Non è consulenza finanziaria. Metodo, fonti e limiti: references/capitale-umano.md.

Uso:
    python capitale-umano.py [--dati FILE] [--composizione FILE] [--from FILE ...] [--set NOME=VALORE ...]
                             [--json FILE]
    (senza --dati gira sull'esempio esempio-capitale-umano.json e lo dichiara; --from legge i JSON di
     proiezione-inps.py, netto-pensione.py e glidepath-obiettivi.py; precedenza --set > --dati > --from)

ONESTÀ METODOLOGICA
- Euro di oggi, termini reali, redditi netti: i contributi tornano come pensione, valutata a parte.
- La quota azionaria del capitale umano è una stima per categoria di lavoro: la sensibilità mostra
  quanto pesa.
- Il capitale umano non si vende né si frazione: l'esposizione totale serve a ragionare, non è un
  portafoglio da replicare.
"""
import csv
import os

from motore_bootstrap import cli, errore, numero, euro, pct, scrivi_json

# ── Costanti di scenario (sovrascrivibili con --set) ────────────────────────
R_F = 0.01               # tasso reale privo di rischio
NU_PENSIONE = 0.0075     # premio per il rischio normativo sulla pensione INPS
ETA_FINE = 90            # età fino a cui si conta la pensione
ETA_PENSIONE = None      # da --dati, --from (proiezione-inps.py) o --set
PENSIONE_NETTA = None    # annua, euro di oggi: da --dati, --from (netto-pensione.py) o --set
REND_AZ_REALE = 0.03     # rendimento reale annualizzato, netto di costi e imposte (mercati-e-correlazione.md)
REND_OBB_REALE = 0.005
SIGMA_AZ = 0.18          # volatilità azionaria del Monte Carlo
N_SIM = 2000
SEED = 42
QUOTE_GLIDE = None       # quota azionaria per anno, da --from del JSON di glidepath-obiettivi.py
SOGLIA_SOVRAPPESO = 2.0  # avviso se il settore pesa nel portafoglio più di N volte il mercato mondiale

PROFILI_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profili-capitale-umano.csv")
CAMPI_NUMERICI = ("quota_azionaria_hc", "nu", "rho", "sigma_h", "p_u", "durata_anni", "sostituzione_naspi")

# I settori GICS con il nome inglese degli emittenti di ETF e quello italiano del report
SETTORI_GICS = {
    "Information Technology": "Tecnologia dell'informazione",
    "Financials": "Finanza",
    "Health Care": "Sanità",
    "Consumer Discretionary": "Beni voluttuari",
    "Communication Services": "Servizi di comunicazione",
    "Industrials": "Industria",
    "Consumer Staples": "Beni di prima necessità",
    "Energy": "Energia",
    "Materials": "Materiali",
    "Utilities": "Servizi di pubblica utilità",
    "Real Estate": "Immobiliare",
}


def _numero_csv(testo):
    """Numero da CSV italiano o anglosassone: «0,30», «0.30», «23,4»."""
    return float(testo.strip().replace(",", "."))


def carica_profili(path=None):
    """I profili di lavoro dal CSV (righe «#» saltate, «;» come separatore, virgola decimale)."""
    path = path or PROFILI_CSV
    if not os.path.exists(path):
        errore(f"profili non trovati: {path}")
    with open(path, encoding="utf-8-sig") as f:
        righe = [r for r in f if r.strip() and not r.lstrip().startswith("#")]
    profili = {}
    for r in csv.DictReader(righe, delimiter=";"):
        p = {k: _numero_csv(r[k]) for k in CAMPI_NUMERICI}
        p["settore_default"] = r["settore_default"].strip() or None
        p["fonte"], p["natura"] = r["fonte"], r["natura"]
        profili[r["profilo"].strip()] = p
    return profili


def profilo_effettivo(persona, profili):
    """Il profilo della persona con i suoi override applicati (la tabella non cambia)."""
    nome = persona.get("profilo")
    if nome not in profili:
        errore(f"profilo {nome!r} sconosciuto: usa uno di {', '.join(profili)}")
    p = dict(profili[nome], nome=nome)
    for k, v in (persona.get("override") or {}).items():
        if k not in CAMPI_NUMERICI and k != "settore_default":
            errore(f"override {k!r} sconosciuto: ammessi {', '.join(CAMPI_NUMERICI)}")
        p[k] = v
    return p


def frazione_lavorata(p_u, durata_anni, sostituzione_naspi):
    """Quota del reddito attesa al netto dei periodi senza lavoro, attenuati dalla NASpI."""
    return 1 - p_u * durata_anni * (1 - sostituzione_naspi)


def valore_capitale_umano(reddito0, g, anni, r_f, nu, frazione):
    """Valore attuale dei redditi da lavoro dei prossimi `anni` anni (fine anno, crescita reale g)."""
    return sum(reddito0 * (1 + g) ** t * frazione / (1 + r_f + nu) ** t for t in range(1, int(anni) + 1))


def valore_pensione(pensione, anni_a_pensione, anni_a_fine, r_f, nu_pens):
    """Valore attuale della pensione annua dall'anno dopo la pensione fino all'età finale."""
    inizio = max(int(anni_a_pensione), 0) + 1
    return sum(pensione / (1 + r_f + nu_pens) ** t for t in range(inizio, int(anni_a_fine) + 1))


def quota_azionaria_effettiva(s, quota_azioni_datore):
    """La parte pagata in azioni del datore conta tutta come azione; il resto con la quota del profilo."""
    return quota_azioni_datore + (1 - quota_azioni_datore) * s


ESEMPIO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "esempio-capitale-umano.json")
CLASSI_NOTE = ("azionario", "obbligazionario", "monetario")
ETICHETTA_EQUIVALENZA = ("calcolo, non target: non modifica l'allocazione degli obiettivi "
                         "né quella di it-rebalance")
# chiavi lette con --from dai JSON degli altri script
DA_JSON = {
    "eta_pensionamento": ("ETA_PENSIONE", int),      # proiezione-inps.py
    "netto_pensione_inps": "PENSIONE_NETTA",         # netto-pensione.py
    "portafoglio": "QUOTE_GLIDE",                    # glidepath-obiettivi.py: quota azionaria aggregata per anno
}


def _non_negativo(nome, valore):
    if not isinstance(valore, (int, float)) or isinstance(valore, bool):
        errore(f"{nome} = {valore!r}: serve un numero")
    if valore < 0:
        errore(f"{nome} = {valore}: valore negativo")


def _quota(nome, valore):
    _non_negativo(nome, valore)
    if valore > 1:
        errore(f"{nome} = {valore}: quota fuori da [0, 1] (le quote sono frazioni: 0.6 per il 60%)")


def leggi_dati(path):
    """Il JSON della persona e del patrimonio (schema in references/capitale-umano.md), validato."""
    import json
    if not os.path.exists(path):
        errore(f"--dati: file non trovato: {path}")
    try:
        with open(path, encoding="utf-8-sig") as f:
            d = json.load(f)
    except ValueError as e:
        errore(f"--dati: {path} non è un JSON valido ({e})")
    if "persone" in d:
        errore('un solo reddito per ora: usa "persona" (un oggetto), non "persone"')
    persona = d.get("persona")
    if not isinstance(persona, dict):
        errore('--dati: manca "persona", l\'oggetto con profilo, età e reddito')
    for k in ("profilo", "eta"):
        if k not in persona:
            errore(f'--dati: manca "persona.{k}"')
    _non_negativo("persona.eta", persona["eta"])
    for k in ("netto_annuo", "tfr_annuo", "contributo_datore_fp"):
        _non_negativo(f"persona.{k}", persona.get(k, 0))
    if "eta_pensione" in persona:
        _non_negativo("persona.eta_pensione", persona["eta_pensione"])
    _quota("persona.quota_reddito_azioni_datore", persona.get("quota_reddito_azioni_datore", 0))
    for k, v in (persona.get("override") or {}).items():
        if k in ("quota_azionaria_hc", "p_u", "sostituzione_naspi"):
            _quota(f"persona.override.{k}", v)
        elif k in ("nu", "sigma_h", "durata_anni"):
            _non_negativo(f"persona.override.{k}", v)
    pensione = d.get("pensione") or {}
    for k in ("netta_annua", "eta_fine"):
        if k in pensione:
            _non_negativo(f"pensione.{k}", pensione[k])
    for i, pos in enumerate(d.get("posizioni") or []):
        if "asset_class" not in pos or "valore" not in pos:
            errore(f"posizioni[{i}]: servono asset_class e valore")
        _non_negativo(f"posizioni[{i}].valore", pos["valore"])
    fp = d.get("fondo_pensione") or {}
    _non_negativo("fondo_pensione.valore", fp.get("valore", 0))
    _quota("fondo_pensione.quota_azionaria", fp.get("quota_azionaria", 0))
    for k in ("tfr_maturato_azienda", "liquidita", "risparmio_annuo", "altri_attivi"):
        _non_negativo(k, d.get(k, 0))
    if d.get("esposizione_totale_desiderata") is not None:
        _quota("esposizione_totale_desiderata", d["esposizione_totale_desiderata"])
    return d


def verifica_eta(persona, c):
    """Età coerenti tra loro: chi ha ancora un reddito da lavoro non può essere oltre l'età di pensione."""
    eta, ep, ef = persona["eta"], c["ETA_PENSIONE"], c["ETA_FINE"]
    if eta >= ef:
        errore(f"eta ({eta}) non è minore di eta_fine ({ef}): non resta nulla da valutare")
    reddito = persona.get("netto_annuo", 0) + persona.get("tfr_annuo", 0) + persona.get("contributo_datore_fp", 0)
    if ep < eta and reddito > 0:
        errore(f"eta_pensione ({ep}) è prima di eta ({eta}) ma il reddito da lavoro non è zero: "
               "chi è già in pensione mette netto_annuo e tfr_annuo a 0")


def bilancio(dati, profilo, c):
    """Diagnosi 1 e 2: le voci della ricchezza totale e le due esposizioni azionarie.
    `c`: le costanti risolte R_F, NU_PENSIONE, ETA_FINE, ETA_PENSIONE, PENSIONE_NETTA."""
    persona = dati["persona"]
    eta = persona["eta"]
    anni_lavoro = max(int(c["ETA_PENSIONE"] - eta), 0)
    reddito0 = persona.get("netto_annuo", 0) + persona.get("tfr_annuo", 0) + persona.get("contributo_datore_fp", 0)
    frazione = frazione_lavorata(profilo["p_u"], profilo["durata_anni"], profilo["sostituzione_naspi"])
    HC = valore_capitale_umano(reddito0, persona.get("crescita_reale", 0.01), anni_lavoro, c["R_F"], profilo["nu"], frazione)
    s = quota_azionaria_effettiva(profilo["quota_azionaria_hc"], persona.get("quota_reddito_azioni_datore", 0))
    PP = valore_pensione(c["PENSIONE_NETTA"], int(c["ETA_PENSIONE"] - eta), int(c["ETA_FINE"] - eta), c["R_F"], c["NU_PENSIONE"])

    avvisi = []
    posizioni = dati.get("posizioni") or []
    pos_tot = sum(p["valore"] for p in posizioni)
    pos_az = sum(p["valore"] for p in posizioni if p["asset_class"] == "azionario")
    ignote = sorted({p["asset_class"] for p in posizioni if p["asset_class"] not in CLASSI_NOTE})
    if ignote:
        avvisi.append(f"asset_class fuori da {', '.join(CLASSI_NOTE)} contate come non azionarie: {', '.join(ignote)}")
    liquidita = dati.get("liquidita", 0)
    fp = dati.get("fondo_pensione") or {}
    fp_valore, fp_az = fp.get("valore", 0), fp.get("valore", 0) * fp.get("quota_azionaria", 0)
    tfr = dati.get("tfr_maturato_azienda", 0)

    F_portafoglio = pos_tot + liquidita
    F = F_portafoglio + fp_valore + tfr
    F_az = pos_az + fp_az
    HC_az = s * HC
    W = F + HC + PP
    if W <= 0:
        errore("ricchezza totale nulla: nessun patrimonio, reddito o pensione da valutare")
    voci = [
        ("Portafoglio", pos_tot, pos_az / pos_tot if pos_tot else 0),
        ("Fondo pensione", fp_valore, fp.get("quota_azionaria", 0)),
        ("TFR maturato in azienda", tfr, 0),
        ("Liquidità", liquidita, 0),
        ("Capitale umano, parte azionaria", HC_az, 1),
        ("Capitale umano, parte obbligazionaria", HC - HC_az, 0),
        ("Capitale pensionistico (INPS)", PP, 0),
    ]
    return {
        "voci": [{"nome": n, "valore": v, "peso": v / W, "quota_azionaria": q} for n, v, q in voci],
        "F": F, "F_az": F_az, "F_portafoglio": F_portafoglio, "F_az_fondo": fp_az,
        "HC": HC, "HC_az": HC_az, "s": s, "PP": PP, "W": W,
        "esposizione_finanziaria": F_az / F if F > 0 else None,
        "esposizione_totale": (F_az + HC_az) / W,
        "altri_attivi": dati.get("altri_attivi", 0),
        "avvisi": avvisi,
    }


def equivalenza(T, b):
    """La quota azionaria del portafoglio (posizioni e liquidità) che darebbe un'esposizione totale T,
    con fondo pensione e capitale umano fermi; limitata a [0, 1]. Calcolo, non target."""
    if b["F_portafoglio"] <= 0:
        return {"x": None, "limite": None,
                "messaggio": f"nessun portafoglio su cui calcolarla (posizioni e liquidità a zero); {ETICHETTA_EQUIVALENZA}"}
    fermo = b["HC_az"] + b["F_az_fondo"]
    x = (T * b["W"] - fermo) / b["F_portafoglio"]
    if x > 1:
        massimo = (b["F_portafoglio"] + fermo) / b["W"]
        return {"x": 1, "limite": "max",
                "messaggio": f"anche con il portafoglio al 100% in azioni l'esposizione totale resta al {pct(massimo)}, "
                             f"sotto il {pct(T)} desiderato; {ETICHETTA_EQUIVALENZA}"}
    if x < 0:
        minimo = fermo / b["W"]
        return {"x": 0, "limite": "min",
                "messaggio": f"anche con il portafoglio senza azioni l'esposizione totale è già al {pct(minimo)}, "
                             f"sopra il {pct(T)} desiderato; {ETICHETTA_EQUIVALENZA}"}
    return {"x": x, "limite": None,
            "messaggio": f"per un'esposizione totale del {pct(T)} il portafoglio dovrebbe stare al {pct(x)} in azioni; "
                         f"{ETICHETTA_EQUIVALENZA}"}


def risolvi_costanti(dati, nomi_set):
    """Età di pensione, pensione netta ed età finale con la precedenza --set > --dati > --from > default."""
    global ETA_PENSIONE, PENSIONE_NETTA, ETA_FINE
    persona, pensione = dati["persona"], dati.get("pensione") or {}
    origine = {}
    for nome, valore_dati, default in (("ETA_PENSIONE", persona.get("eta_pensione"), None),
                                       ("PENSIONE_NETTA", pensione.get("netta_annua"), None),
                                       ("ETA_FINE", pensione.get("eta_fine"), 90)):
        if nome in nomi_set:
            origine[nome] = "set"
        elif valore_dati is not None:
            globals()[nome] = valore_dati
            origine[nome] = "dati"
        elif globals()[nome] is not None and globals()[nome] != default:
            origine[nome] = "from"
        else:
            origine[nome] = "default"
    if ETA_PENSIONE is None:
        errore("manca l'età di pensione: indicala in --dati (persona.eta_pensione), con --from del JSON di "
               "proiezione-inps.py o con --set ETA_PENSIONE=67")
    if PENSIONE_NETTA is None:
        errore("manca la pensione netta annua: indicala in --dati (pensione.netta_annua), con --from del JSON di "
               "netto-pensione.py o con --set PENSIONE_NETTA=18000")
    _non_negativo("PENSIONE_NETTA", PENSIONE_NETTA)
    c = {"R_F": R_F, "NU_PENSIONE": NU_PENSIONE, "ETA_FINE": ETA_FINE, "ETA_PENSIONE": ETA_PENSIONE,
         "PENSIONE_NETTA": PENSIONE_NETTA}
    return c, origine


def stampa_bilancio(b, eq):
    print("\n1. BILANCIO PATRIMONIALE TOTALE (euro di oggi)")
    print(f"   {'Voce':<40}{'Valore':>14}{'Peso':>9}{'Azioni':>9}")
    for v in b["voci"]:
        print(f"   {v['nome']:<40}{euro(v['valore']):>14}{pct(v['peso']):>9}{pct(v['quota_azionaria'], 0):>9}")
    print(f"   {'Ricchezza totale':<40}{euro(b['W']):>14}{pct(1, 0):>9}")
    if b["altri_attivi"]:
        print(f"   Altri attivi (casa e simili, fuori dall'esposizione): {euro(b['altri_attivi'])}")
    for a in b["avvisi"]:
        print(f"   ⚠️  {a}")

    print("\n2. ESPOSIZIONE AZIONARIA")
    ef = b["esposizione_finanziaria"]
    print(f"   Patrimonio finanziario: {pct(ef) if ef is not None else 'n/d'} in azioni")
    print(f"   Ricchezza totale:       {pct(b['esposizione_totale'])} in azioni")
    peso_hc = b["HC"] / b["W"]
    print(f"   Il capitale umano pesa il {pct(peso_hc)} della ricchezza totale ed è per il {pct(b['s'], 0)} "
          f"un'azione: " + ("conta più del portafoglio, quindi l'esposizione totale dipende soprattutto da lui."
                             if peso_hc > 0.5 else "il portafoglio pesa di più, e l'esposizione totale gli somiglia."))
    if eq is not None:
        print(f"   Equivalenza: {eq['messaggio']}")


def main():
    args = cli(__doc__.strip().splitlines()[0].split("— ", 1)[1], spazio=globals(), json=True, da_json=DA_JSON,
               argomenti=[(("--dati",), {"metavar": "FILE", "help": "JSON di persona e patrimonio (default: l'esempio)"}),
                          (("--composizione",), {"metavar": "FILE",
                                                 "help": "CSV strumento;settore;peso per la sovrapposizione settoriale"})])
    esempio = args.dati is None
    dati = leggi_dati(ESEMPIO if esempio else args.dati)
    nomi_set = {e.split("=", 1)[0].strip() for e in args.set}
    c, origine = risolvi_costanti(dati, nomi_set)
    profilo = profilo_effettivo(dati["persona"], carica_profili())
    verifica_eta(dati["persona"], c)
    b = bilancio(dati, profilo, c)
    T = dati.get("esposizione_totale_desiderata")
    eq = equivalenza(T, b) if T is not None else None

    print("=" * 74)
    print("CAPITALE UMANO — il portafoglio dentro la ricchezza totale")
    print("=" * 74)
    print("⚠️  Lente diagnostica, non consulenza: non modifica i target degli obiettivi né di it-rebalance.")
    if esempio:
        print("   (dati d'esempio: passa i tuoi con --dati FILE)")
    persona = dati["persona"]
    print(f"   Profilo {profilo['nome']}, {persona['eta']} anni, pensione a {c['ETA_PENSIONE']}, "
          f"netto {euro(persona.get('netto_annuo', 0))} l'anno")
    stampa_bilancio(b, eq)

    if args.json:
        scrivi_json(args.json, {
            "bilancio": {k: v for k, v in b.items()},
            "esposizione_finanziaria": b["esposizione_finanziaria"],
            "esposizione_totale": b["esposizione_totale"],
            "equivalenza": eq,
            "proiezione": None,
            "eta_sorpasso": None,
            "settore": None,
            "sensibilita": None,
            "profilo_usato": {**{k: v for k, v in profilo.items() if k not in ("fonte", "natura")},
                              "eta_pensione": c["ETA_PENSIONE"], "pensione_netta": c["PENSIONE_NETTA"],
                              "eta_fine": c["ETA_FINE"], "origine": origine},
        })


if __name__ == "__main__":
    main()
