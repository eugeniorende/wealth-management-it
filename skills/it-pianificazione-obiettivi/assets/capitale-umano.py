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
import math
import os

import numpy as np

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

# Pesi dei settori nell'indice MSCI ACWI (USD), dalla scheda ufficiale MSCI «Index Factsheet» del 30/09/2026,
# sezione Sector Weights: https://www.msci.com/documents/10199/255599/msci-acwi-net.pdf
# Da riverificare a ogni release: il peso della tecnologia cambia di qualche punto in pochi mesi.
PESI_MONDO = {
    "Information Technology": 0.3321, "Financials": 0.1617, "Industrials": 0.1027, "Health Care": 0.0842,
    "Consumer Discretionary": 0.0824, "Communication Services": 0.0801, "Consumer Staples": 0.0451,
    "Energy": 0.0396, "Materials": 0.0351, "Utilities": 0.0225, "Real Estate": 0.0145,
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
    if not isinstance(persona.get("tfr_nel_fondo", False), bool):
        errore(f"persona.tfr_nel_fondo = {persona['tfr_nel_fondo']!r}: serve true o false")
    for k, v in (persona.get("override") or {}).items():
        if k in ("quota_azionaria_hc", "p_u", "sostituzione_naspi"):
            _quota(f"persona.override.{k}", v)
        elif k in ("nu", "sigma_h", "durata_anni"):
            _non_negativo(f"persona.override.{k}", v)
        elif k == "rho" and (not isinstance(v, (int, float)) or isinstance(v, bool) or not -1 <= v <= 1):
            errore(f"persona.override.rho = {v!r}: la correlazione sta tra -1 e 1")
    g = persona.get("crescita_reale", 0.01)
    if not isinstance(g, (int, float)) or isinstance(g, bool) or g <= -1:
        errore(f"persona.crescita_reale = {g!r}: serve un numero come frazione (0.01 per l'1%)")
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


CHIAVI_NOTE = {
    "": {"persona", "pensione", "posizioni", "fondo_pensione", "tfr_maturato_azienda", "liquidita", "risparmio_annuo",
         "esposizione_totale_desiderata", "altri_attivi"},
    "persona": {"profilo", "settore", "eta", "eta_pensione", "netto_annuo", "crescita_reale", "tfr_annuo", "tfr_nel_fondo",
                "contributo_datore_fp", "quota_reddito_azioni_datore", "override"},
    "pensione": {"netta_annua", "eta_fine"},
    "fondo_pensione": {"valore", "quota_azionaria"},
}


def chiavi_sconosciute(dati):
    """Le chiavi del JSON che lo script non legge (un refuso vale zero in silenzio). Le chiavi che iniziano con
    «_» sono note libere; le posizioni non si controllano, perché si copiano dal JSON di it-rebalance con
    campi in più (broker, categoria fiscale, plus)."""
    ignote = []
    for sezione, note in CHIAVI_NOTE.items():
        blocco = dati if not sezione else dati.get(sezione)
        if not isinstance(blocco, dict):
            continue
        for k in blocco:
            if k not in note and not k.startswith("_"):
                ignote.append(f"{sezione}.{k}" if sezione else k)
    return ignote


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


def proiezione(dati, profilo, c, quote_glide, n_sim, seed):
    """Diagnosi 3: anno per anno fino a 5 anni dopo la pensione (o dopo l'età attuale, se è più alta), senza
    superare l'età finale. Percorso atteso (rendimenti e crescita ai valori centrali) e fascia P10-P50-P90
    dell'esposizione totale da un Monte Carlo con shock di borsa e di reddito correlati (Ibbotson et al.
    2007, eq. A.6-A.9).
    Il patrimonio è in tre contenitori: portafoglio (posizioni e liquidità, con la quota azionaria di oggi o
    quella del glide path dall'anno 1), fondo pensione (con la sua quota) e TFR in azienda (obbligazionario).
    Ogni anno di lavoro il risparmio entra nel portafoglio, il contributo del datore nel fondo pensione e il
    TFR nel contenitore TFR, o nel fondo con persona.tfr_nel_fondo: quello che esce dal capitale umano entra
    nel patrimonio. L'anno 0 è la fotografia di oggi e coincide con la diagnosi 2."""
    persona = dati["persona"]
    eta0, ep = persona["eta"], c["ETA_PENSIONE"]
    g = persona.get("crescita_reale", 0.01)
    tfr_annuo, contributo = persona.get("tfr_annuo", 0), persona.get("contributo_datore_fp", 0)
    nel_fondo = bool(persona.get("tfr_nel_fondo", False))
    reddito0 = persona.get("netto_annuo", 0) + tfr_annuo + contributo
    frazione = frazione_lavorata(profilo["p_u"], profilo["durata_anni"], profilo["sostituzione_naspi"])
    s = quota_azionaria_effettiva(profilo["quota_azionaria_hc"], persona.get("quota_reddito_azioni_datore", 0))
    b0 = bilancio(dati, profilo, c)
    fp = dati.get("fondo_pensione") or {}
    q_fondo = fp.get("quota_azionaria", 0)
    P0, FP0, TFR0 = b0["F_portafoglio"], fp.get("valore", 0), dati.get("tfr_maturato_azienda", 0)
    q0 = (b0["F_az"] - b0["F_az_fondo"]) / P0 if P0 > 0 else 0.0
    risparmio = dati.get("risparmio_annuo", 0)
    ultimo = max(min(max(int(ep), eta0) + 5, int(c["ETA_FINE"]) - 1), eta0)
    anni = ultimo - eta0 + 1
    avvisi = []
    if quote_glide is not None and len(quote_glide) < anni:
        avvisi.append(f"glide path più corto della proiezione ({len(quote_glide)} anni su {anni}): "
                      "tenuta l'ultima quota per gli anni successivi")

    def quota(t):
        if t == 0 or quote_glide is None or not len(quote_glide):
            return q0
        return quote_glide[min(t, len(quote_glide) - 1)]

    rng = np.random.default_rng(seed)
    rho, sigma_h = profilo["rho"], profilo["sigma_h"]
    P, FP, TFR = float(P0), float(FP0), float(TFR0)
    h_sim = np.full(n_sim, float(reddito0))
    P_sim, FP_sim, TFR_sim = np.full(n_sim, P), np.full(n_sim, FP), np.full(n_sim, TFR)
    righe, sorpasso, sopra_prima = [], None, None
    for t in range(anni):
        eta = eta0 + t
        anni_lavoro = max(int(ep - eta), 0)
        fattore_hc = valore_capitale_umano(1.0, g, anni_lavoro, c["R_F"], profilo["nu"], frazione)
        HC = reddito0 * (1 + g) ** t * fattore_hc if anni_lavoro > 0 else 0.0
        PP = valore_pensione(c["PENSIONE_NETTA"], int(ep - eta), int(c["ETA_FINE"] - eta), c["R_F"], c["NU_PENSIONE"])
        q = quota(t)
        F = P + FP + TFR
        W = F + HC + PP
        esposizione = (q * P + q_fondo * FP + s * HC) / W
        HC_sim = h_sim * fattore_hc if anni_lavoro > 0 else np.zeros(n_sim)
        esp_sim = (q * P_sim + q_fondo * FP_sim + s * HC_sim) / (P_sim + FP_sim + TFR_sim + HC_sim + PP)
        righe.append({"eta": eta, "F": F, "portafoglio": P, "fondo": FP, "tfr": TFR,
                      "az_portafoglio": q * P, "az_fondo": q_fondo * FP, "HC": float(HC), "PP": float(PP),
                      "quota_hc": float(HC / W), "esposizione": float(esposizione),
                      "p10": float(np.percentile(esp_sim, 10)), "p50": float(np.percentile(esp_sim, 50)),
                      "p90": float(np.percentile(esp_sim, 90))})
        sopra = F > HC
        if sopra_prima is False and sopra and sorpasso is None:
            sorpasso = eta
        sopra_prima = sopra
        # anno successivo: rendimenti, poi i flussi di chi lavora ancora
        lavora = eta < ep and reddito0 > 0
        crescita = (1 + g) ** t
        P = P * (1 + q * REND_AZ_REALE + (1 - q) * REND_OBB_REALE)
        FP = FP * (1 + q_fondo * REND_AZ_REALE + (1 - q_fondo) * REND_OBB_REALE)
        TFR = TFR * (1 + REND_OBB_REALE)
        if lavora:
            P += risparmio * crescita
            FP += (contributo + (tfr_annuo if nel_fondo else 0)) * crescita
            TFR += (0 if nel_fondo else tfr_annuo) * crescita
        z_s, z = rng.standard_normal(n_sim), rng.standard_normal(n_sim)
        z_h = rho * z_s + math.sqrt(1 - rho ** 2) * z
        r_az = np.exp(math.log(1 + REND_AZ_REALE) + SIGMA_AZ * z_s) - 1
        P_sim = P_sim * (1 + q * r_az + (1 - q) * REND_OBB_REALE)
        FP_sim = FP_sim * (1 + q_fondo * r_az + (1 - q_fondo) * REND_OBB_REALE)
        TFR_sim = TFR_sim * (1 + REND_OBB_REALE)
        if lavora:
            k = h_sim / reddito0
            P_sim = P_sim + risparmio * k
            FP_sim = FP_sim + (contributo + (tfr_annuo if nel_fondo else 0)) * k
            TFR_sim = TFR_sim + (0 if nel_fondo else tfr_annuo) * k
        h_sim = h_sim * np.exp(math.log(1 + g) + sigma_h * z_h)
    if righe and righe[0]["F"] > righe[0]["HC"]:
        stato = "gia_superato"
    elif sorpasso is not None:
        stato = "entro_la_proiezione"
    else:
        stato = "non_prima_della_fine"
    return {"anni": righe, "eta_sorpasso": sorpasso, "stato_sorpasso": stato, "avvisi": avvisi}


def stampa_proiezione(p):
    print("\n3. PROIEZIONE (euro di oggi; esposizione totale attesa e percentili del Monte Carlo)")
    print(f"   {'Età':>4}{'Finanziario':>14}{'Cap. umano':>14}{'Pensione':>13}{'Peso c.u.':>11}{'Esposizione':>13}"
          f"{'P10 · P50 · P90':>24}")
    anni = p["anni"]
    for i, r in enumerate(anni):
        if i % 5 and i != len(anni) - 1:
            continue
        print(f"   {r['eta']:>4}{euro(r['F']):>14}{euro(r['HC']):>14}{euro(r['PP']):>13}{pct(r['quota_hc']):>11}"
              f"{pct(r['esposizione']):>13}{pct(r['p10']) + ' · ' + pct(r['p50']) + ' · ' + pct(r['p90']):>24}")
    if p["stato_sorpasso"] == "entro_la_proiezione":
        print(f"   Il patrimonio finanziario supera il capitale umano a {p['eta_sorpasso']} anni.")
    elif p["stato_sorpasso"] == "gia_superato":
        print("   Il patrimonio finanziario supera già il capitale umano.")
    else:
        print("   Il patrimonio finanziario non supera il capitale umano prima della fine della proiezione.")
    print("   La mediana P50 sta di solito un po' sopra l'esposizione attesa: un portafoglio misto ribilanciato ogni "
          "anno cresce, in mediana, più della media dei suoi pezzi.")
    for a in p["avvisi"]:
        print(f"   ⚠️  {a}")


def leggi_composizione(path):
    """Composizione settoriale degli strumenti, da un CSV in uno dei due formati (righe «#» saltate, BOM ammesso):
    strumento;dimensione;voce;peso scritto da importa-composizione-etf.py, di cui contano le righe «settore»
    (le righe «paese» servono ad altro), oppure strumento;settore;peso compilato a mano.
    Pesi in frazione o in percento (se quelli di uno strumento sommano più di 1,5), virgola o punto."""
    if not os.path.exists(path):
        errore(f"--composizione: file non trovato: {path}")
    with open(path, "rb") as f:
        grezzo = f.read()
    try:
        testo = grezzo.decode("utf-8-sig")
    except UnicodeDecodeError:
        testo = grezzo.decode("cp1252", errors="replace")   # «CSV» semplice di Excel italiano
    righe = [r for r in testo.splitlines() if r.strip(" ;\t") and not r.lstrip().startswith("#")]
    lettore = csv.DictReader(righe, delimiter=";")
    colonne = {c.strip() for c in lettore.fieldnames or ()}
    importato = {"strumento", "dimensione", "voce", "peso"} <= colonne
    if not importato and not {"strumento", "settore", "peso"} <= colonne:
        errore("--composizione: servono le colonne strumento;dimensione;voce;peso (da importa-composizione-etf.py) "
               "o strumento;settore;peso")
    comp = {}
    for r in lettore:
        r = {k.strip(): (v or "").strip() for k, v in r.items() if k is not None}   # «;» in fondo alle righe
        if not any(r.values()):
            continue
        if importato:
            if r["dimensione"] not in ("settore", "paese"):
                errore(f"--composizione: dimensione {r['dimensione']!r} sconosciuta ({r['strumento']}): "
                       "attese «settore» o «paese»")
            if r["dimensione"] != "settore":
                continue
            r["settore"] = r["voce"]
        if r["settore"] not in SETTORI_GICS:
            errore(f"--composizione: settore {r['settore']!r} non GICS: usa uno di {', '.join(SETTORI_GICS)}")
        try:
            peso = _numero_csv(r["peso"].rstrip("%"))
        except ValueError:
            errore(f"--composizione: peso {r['peso']!r} non numerico ({r['strumento']})")
        if r["peso"].endswith("%"):
            peso /= 100
        settori = comp.setdefault(r["strumento"], {})
        settori[r["settore"]] = settori.get(r["settore"], 0) + peso
    for strumento, settori in comp.items():
        totale = sum(settori.values())
        if totale > 1.5:
            for k in settori:
                settori[k] /= 100
            totale /= 100
        if abs(totale - 1) > 0.02:
            errore(f"--composizione: i pesi di {strumento!r} sommano a {pct(totale)}, non a 100%")
    return comp


def sovrapposizione(posizioni, composizione, settore, F_az, HC_az, pesi_mondo):
    """Diagnosi 4: quanto della parte azionaria del portafoglio sta nel settore del proprio lavoro, contro il
    mercato mondiale, e l'esposizione combinata se la parte azionaria del capitale umano sta tutta lì.
    Contano solo le posizioni azionarie con una composizione; le altre sono elencate in «mancanti»."""
    con, num, mancanti = 0.0, 0.0, []
    for p in posizioni:
        if p["asset_class"] != "azionario":
            continue
        nome = (p.get("strumento") or "(senza strumento)").strip()
        if nome not in composizione:
            mancanti.append(nome)
            continue
        con += p["valore"]
        num += p["valore"] * composizione[nome].get(settore, 0)
    quota = num / con if con else None
    peso_mondo = pesi_mondo[settore]
    rapporto = quota / peso_mondo if quota is not None else None
    combinata = (F_az * quota + HC_az) / (F_az + HC_az) if quota is not None and F_az + HC_az > 0 else None
    return {"settore": settore, "quota_settore_fin": quota, "peso_mondo": peso_mondo, "rapporto": rapporto,
            "esposizione_combinata": combinata, "sovrappeso": bool(rapporto is not None and rapporto > SOGLIA_SOVRAPPESO),
            "mancanti": mancanti}


def stampa_settore(z):
    nome = f"{SETTORI_GICS[z['settore']]} ({z['settore']})"
    print(f"\n4. SOVRAPPOSIZIONE SETTORIALE: {nome}")
    if z["quota_settore_fin"] is None:
        print("   Nessuna posizione azionaria con una composizione: aggiungi le righe nel CSV di --composizione.")
    else:
        print(f"   Nel portafoglio azionario: {pct(z['quota_settore_fin'])}; nel mercato mondiale (MSCI ACWI): "
              f"{pct(z['peso_mondo'])}, cioè {numero(z['rapporto'], 1)} volte.")
    if z["esposizione_combinata"] is not None:
        print(f"   Azioni del portafoglio più parte azionaria del capitale umano, quota in questo settore: "
              f"{pct(z['esposizione_combinata'])} (si assume che il capitale umano azionario sia tutto qui).")
    if z["sovrappeso"]:
        print(f"   ⚠️  Il settore pesa più di {numero(SOGLIA_SOVRAPPESO, 0)} volte il mercato: reddito e portafoglio "
              "dipendono dalla stessa parte dell'economia.")
    if z["mancanti"]:
        print(f"   Senza composizione, esclusi dal calcolo: {', '.join(z['mancanti'])}.")
    print("   Il fondo pensione non entra nel calcolo: la sua composizione non è disponibile.")


NOMI_PARAMETRI = {"s": "quota azionaria del capitale umano", "nu": "premio ν del profilo", "g": "crescita reale del reddito",
                  "p_u": "probabilità di perdere il lavoro", "r_f": "tasso reale privo di rischio"}


def punti(frazione):
    """Differenza di esposizione in punti percentuali, con un decimale; zero senza segno («0,0 punti»)."""
    v = round(frazione * 100, 1)
    return "0,0 punti" if v == 0 else f"{numero(v, 1, segno=True)} punti"


def etichetta_punti(frazione):
    """Variazione di un parametro in punti: «+10 punti», «+1,5 punti», «-1 punto»."""
    v = round(frazione * 100, 6)
    testo = numero(v, 0 if v == int(v) else 1, segno=True)
    return f"{testo} {'punto' if abs(v) == 1 else 'punti'}"


def sensibilita(dati, profilo, c):
    """Diagnosi 5: un parametro alla volta, capitale umano ed esposizione totale rispetto al caso base.
    Ordinate per l'effetto più ampio sull'esposizione totale, con le varianti dello stesso parametro vicine."""
    import copy
    base = bilancio(dati, profilo, c)["esposizione_totale"]

    def con_g(g):
        d = copy.deepcopy(dati)
        d["persona"]["crescita_reale"] = g
        return d

    varianti = [
        ("s", etichetta_punti(0.10), dati, dict(profilo, quota_azionaria_hc=min(profilo["quota_azionaria_hc"] + 0.10, 1)), c),
        ("s", etichetta_punti(-0.10), dati, dict(profilo, quota_azionaria_hc=max(profilo["quota_azionaria_hc"] - 0.10, 0)), c),
        ("nu", etichetta_punti(0.015), dati, dict(profilo, nu=profilo["nu"] + 0.015), c),
        ("nu", etichetta_punti(-0.015), dati, dict(profilo, nu=max(profilo["nu"] - 0.015, 0)), c),
        ("g", pct(0, 0), con_g(0.0), profilo, c),
        ("g", pct(0.02, 0), con_g(0.02), profilo, c),
        ("p_u", "× 2", dati, dict(profilo, p_u=min(profilo["p_u"] * 2, 1)), c),
        ("r_f", etichetta_punti(0.01), dati, profilo, dict(c, R_F=c["R_F"] + 0.01)),
        ("r_f", etichetta_punti(-0.01), dati, profilo, dict(c, R_F=c["R_F"] - 0.01)),
    ]
    righe = []
    for parametro, variante, d, prof, cc in varianti:
        b = bilancio(d, prof, cc)
        righe.append({"parametro": parametro, "variante": variante, "HC": b["HC"],
                      "esposizione_totale": b["esposizione_totale"], "delta": b["esposizione_totale"] - base})
    ampiezza = {}
    for r in righe:
        ampiezza[r["parametro"]] = max(ampiezza.get(r["parametro"], 0), abs(r["delta"]))
    ordine = sorted(ampiezza, key=lambda k: -ampiezza[k])
    return sorted(righe, key=lambda r: ordine.index(r["parametro"]))


def stampa_sensibilita(righe):
    print("\n5. SENSIBILITÀ (un parametro alla volta, dal più influente)")
    print(f"   {'Parametro':<38}{'Variante':>12}{'Cap. umano':>14}{'Esposizione':>13}{'Differenza':>14}")
    for r in righe:
        print(f"   {NOMI_PARAMETRI[r['parametro']]:<38}{r['variante']:>12}{euro(r['HC']):>14}"
              f"{pct(r['esposizione_totale']):>13}{punti(r['delta']):>14}")


def eta_intera(valore, nome, note):
    """Il modello lavora ad anni interi: un'età frazionaria (proiezione-inps.py le accetta) si arrotonda per
    difetto, dicendolo."""
    if valore != int(valore):
        note.append(f"{nome} {numero(valore, 1)} arrotondata per difetto a {int(valore)}: il modello lavora ad anni interi")
    return int(valore)


def risolvi_costanti(dati, nomi_set, note):
    """Età di pensione, pensione netta ed età finale con la precedenza --set > --dati > --from > default.
    Le età diventano intere; quando --dati scavalca un valore letto con --from lo aggiunge alle note."""
    global ETA_PENSIONE, PENSIONE_NETTA, ETA_FINE
    persona, pensione = dati["persona"], dati.get("pensione") or {}
    origine = {}
    for nome, valore_dati, default in (("ETA_PENSIONE", persona.get("eta_pensione"), None),
                                       ("PENSIONE_NETTA", pensione.get("netta_annua"), None),
                                       ("ETA_FINE", pensione.get("eta_fine"), 90)):
        if nome in nomi_set:
            origine[nome] = "set"
        elif valore_dati is not None:
            letto = globals()[nome]
            if letto is not None and letto != default and letto != valore_dati:
                note.append(f"{nome}: uso {valore_dati} da --dati, non {letto} letto con --from "
                            "(per usare il valore di --from, togli la chiave da --dati)")
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
    _non_negativo("ETA_PENSIONE", ETA_PENSIONE)
    ETA_PENSIONE = eta_intera(ETA_PENSIONE, "età di pensione", note)
    ETA_FINE = eta_intera(ETA_FINE, "età finale", note)
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
    blocchi = {"il capitale umano": b["HC"], "il capitale pensionistico": b["PP"], "il patrimonio finanziario": b["F"]}
    maggiore = max(blocchi, key=blocchi.get)
    print(f"   Peso del capitale umano sulla ricchezza totale: {pct(peso_hc)}; sua quota azionaria: {pct(b['s'], 0)}.")
    if maggiore == "il patrimonio finanziario":
        print(f"   Il blocco più grande è il patrimonio finanziario ({pct(b['F'] / b['W'])}): "
              "l'esposizione totale gli somiglia.")
    else:
        print(f"   Il blocco più grande è {maggiore} ({pct(blocchi[maggiore] / b['W'])}): l'esposizione totale "
              "dipende soprattutto da lui, non dal portafoglio.")
    if eq is not None:
        print(f"   Equivalenza: {eq['messaggio']}")


def main():
    args = cli(__doc__.strip().splitlines()[0].split("— ", 1)[1], spazio=globals(), json=True, da_json=DA_JSON,
               argomenti=[(("--dati",), {"metavar": "FILE", "help": "JSON di persona e patrimonio (default: l'esempio)"}),
                          (("--composizione",), {"metavar": "FILE",
                                                 "help": "CSV della composizione per la sovrapposizione settoriale (strumento;dimensione;voce;peso da "
                                                         "importa-composizione-etf.py, o strumento;settore;peso compilato a mano)"})])
    esempio = args.dati is None
    dati = leggi_dati(ESEMPIO if esempio else args.dati)
    persona = dati["persona"]
    note = []
    persona["eta"] = eta_intera(persona["eta"], "età", note)
    ignote = chiavi_sconosciute(dati)
    if ignote:
        note.append(f"chiavi non riconosciute, ignorate (refusi?): {', '.join(ignote)}")
    nomi_set = {e.split("=", 1)[0].strip() for e in args.set}
    c, origine = risolvi_costanti(dati, nomi_set, note)
    profilo = profilo_effettivo(persona, carica_profili())
    verifica_eta(persona, c)
    if QUOTE_GLIDE is not None:
        if not isinstance(QUOTE_GLIDE, list) or not all(isinstance(x, (int, float)) and 0 <= x <= 1 for x in QUOTE_GLIDE):
            errore("QUOTE_GLIDE: serve una lista di quote tra 0 e 1 (il campo «portafoglio» del JSON del glide path)")
    comp = settore = None
    if args.composizione:
        comp = leggi_composizione(args.composizione)
        settore = persona.get("settore") or profilo.get("settore_default")
        if not settore:
            errore('--composizione: manca "persona.settore", il settore GICS del tuo lavoro')
        if settore not in SETTORI_GICS:
            errore(f"persona.settore {settore!r} non GICS: usa uno di {', '.join(SETTORI_GICS)}")

    # tutti i calcoli prima di stampare: un errore non lascia mezzo report
    b = bilancio(dati, profilo, c)
    T = dati.get("esposizione_totale_desiderata")
    eq = equivalenza(T, b) if T is not None else None
    p = proiezione(dati, profilo, c, QUOTE_GLIDE, N_SIM, SEED)
    z = None
    if comp is not None:
        posizioni = dati.get("posizioni") or []
        F_az_comp = sum(q["valore"] for q in posizioni
                        if q["asset_class"] == "azionario" and (q.get("strumento") or "").strip() in comp)
        z = sovrapposizione(posizioni, comp, settore, F_az_comp, b["HC_az"], PESI_MONDO)
    sens = sensibilita(dati, profilo, c)

    print("=" * 74)
    print("CAPITALE UMANO — il portafoglio dentro la ricchezza totale")
    print("=" * 74)
    print("⚠️  Lente diagnostica, non consulenza: non modifica i target degli obiettivi né di it-rebalance.")
    if esempio:
        print("   (dati d'esempio: passa i tuoi con --dati FILE)")
    print(f"   Profilo {profilo['nome']}, {persona['eta']} anni, pensione a {c['ETA_PENSIONE']}, "
          f"netto {euro(persona.get('netto_annuo', 0))} l'anno")
    for n in note:
        print(f"   ℹ️  {n}")
    stampa_bilancio(b, eq)
    stampa_proiezione(p)
    if z is not None:
        stampa_settore(z)
    stampa_sensibilita(sens)
    print("\nNon è consulenza: è una lente per ragionare sul rischio complessivo, non un'allocazione da adottare.")

    if args.json:
        scrivi_json(args.json, {
            "bilancio": {k: v for k, v in b.items()},
            "esposizione_finanziaria": b["esposizione_finanziaria"],
            "esposizione_totale": b["esposizione_totale"],
            "equivalenza": eq,
            "proiezione": p["anni"],
            "eta_sorpasso": p["eta_sorpasso"],
            "stato_sorpasso": p["stato_sorpasso"],
            "settore": z,
            "sensibilita": sens,
            "profilo_usato": {**{k: v for k, v in profilo.items() if k not in ("fonte", "natura")},
                              "eta_pensione": c["ETA_PENSIONE"], "pensione_netta": c["PENSIONE_NETTA"],
                              "eta_fine": c["ETA_FINE"], "origine": origine},
        })


if __name__ == "__main__":
    main()
