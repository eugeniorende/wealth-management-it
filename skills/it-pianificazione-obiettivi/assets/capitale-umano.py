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


def main():
    cli(__doc__.strip().splitlines()[0].split("— ", 1)[1], spazio=globals(), json=True)
    print("capitale-umano.py: in costruzione (€)")


if __name__ == "__main__":
    main()
