#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ponte-pensione.py — "posso smettere a X anni?" Il calcolo del PONTE per l'uscita anticipata.

Chi è coperto dalla pensione (INPS + fondo) a partire dall'età di vecchiaia può comprarsi
l'uscita anticipata con un capitale-ponte che copre gli anni in mezzo. Questo script fa
il conto COMPLETO, che ha tre pezzi — e i calcoli ingenui ne mostrano solo uno:

  1. IL PONTE: un Monte Carlo sul capitale che finanzia la spesa dall'uscita alla
     vecchiaia → probabilità di arrivarci senza esaurirlo, e capitale necessario
     per una data confidenza.
  2. LA RITA (Rendita Integrativa Temporanea Anticipata, D.Lgs. 252/2005 art. 11
     co. 4, fonti COVIP/AdE; Verificato: 2026-07): da 5 anni prima della
     vecchiaia (10 se inoccupati >24 mesi) il montante del fondo pensione si può
     erogare come rendita-ponte tassata al 15%→9% — molto meglio che consumare
     capitale ordinario. Requisiti versione 5 anni: cessazione del lavoro, ≥20 anni
     di contributi obbligatori, ≥5 anni di previdenza complementare.
  3. I COSTI PERMANENTI: uscire prima significa contributi INPS in meno (pensione
     pubblica più bassa PER SEMPRE), versamenti al fondo in meno, e il montante
     usato in RITA che non c'è più a 69 → la pensione "da vecchiaia" si riduce.
     Ignorarlo significa comprare il ponte a un prezzo che non si è visto.

Uso:
    python ponte-pensione.py
    python ponte-pensione.py --set ETA_USCITA=60 --set SPESA_ANNUA_PONTE=22000

ONESTÀ METODOLOGICA
- Tutto in termini REALI (€ di oggi). La RITA è modellata a rate costanti
  (capitale destinato al comparto garantito, ~0% reale: prassi prudente) e con
  l'aliquota agevolata sull'INTERO importo (conservativo: la parte di
  rendimenti già tassati, che può valere il 30-45% del montante, sarebbe esente).
- I canali PUBBLICI di anticipo (pensione anticipata ordinaria, anticipata
  contributiva, APE…) NON sono modellati: se ne maturi i requisiti, il ponte
  si accorcia e questo calcolo diventa un limite superiore del fabbisogno.
  Per un contributivo puro il canale tipico è l'anticipata contributiva: 64 anni
  e 20 anni di contribuzione effettiva nel 2026; 64 anni e 1 mese e 20 anni e
  1 mese nel 2027; 64 anni e 3 mesi e 20 anni e 3 mesi dal 2028. Serve una
  prima rata ≥ 3 volte l'assegno sociale (2,8 e 2,6 per le madri, 3,2 dal
  2030), l'assegno è limitato a 5 volte il trattamento minimo fino alla
  vecchiaia e la pensione decorre tre mesi dopo la maturazione dei requisiti
  (art. 24 c. 11 DL 201/2011; Circ. INPS 19/2026 e 28/2026, Verificato:
  2026-10). Per stimarla: proiezione-inps.py --set ETA_PENSIONAMENTO=64 e
  confronto con la soglia. Per il ponte, ETA_PENSIONE_VECCHIAIA = 64.25 nel
  2026 (64.33 nel 2027, 64.5 dal 2028), cioè l'età più la finestra: accorcia
  il ponte INPS ma sposta anche la finestra della RITA, che per legge resta
  legata alla vecchiaia: in quel caso leggere la parte RITA con cautela (o
  RITA_ATTIVA=False).
- Il drag fiscale sui prelievi dal capitale ordinario (26% sui capital gain
  realizzati) è approssimato da un parametro annuo sul rendimento.
Questo strumento è educativo e non costituisce consulenza finanziaria o previdenziale.
"""

import numpy as np

from motore_bootstrap import applica_override, carica_storico, blocchi_bootstrap, pctl, percorso_json, scrivi_json

# ============================== PARAMETRI ==============================

ETA_USCITA = 62.0             # età in cui smetti di lavorare
ETA_PENSIONE_VECCHIAIA = 69.0 # età in cui INPS + fondo ti coprono (da proiezione-inps.py)

SPESA_ANNUA_PONTE = 25_000.0  # tenore di vita NETTO annuo nel ponte (€ reali di oggi)
CAPITALE_PONTE = 45_000.0     # capitale-ponte disponibile ALL'USCITA (€ reali) — tipicamente
                              # il secchiello "libertà finanziaria" proiettato a quella data
PESO_AZIONARIO_PONTE = 0.30   # quota azionaria durante il ponte (de-risked: il glide path
                              # della libertà finanziaria atterra proprio verso l'uscita)
DRAG_FISCALE_ANNUO = 0.004    # attrito fiscale sui prelievi (26% sui gain realizzati), approssimato

# RITA — rendita-ponte dal fondo pensione
RITA_ATTIVA = True
MONTANTE_FP_ALL_USCITA = 250_000.0  # montante del fondo pensione all'uscita (dal Monte Carlo pensione)
QUOTA_MONTANTE_IN_RITA = 1.0        # quota del montante destinata alla RITA (0–1)
ANNI_MAX_RITA = 5                   # 5 = ordinaria; 10 = con inoccupazione >24 mesi
ANNI_ISCRIZIONE_FP = 30             # anni di partecipazione alla complementare all'avvio RITA

# Costi permanenti (valori all'uscita, reali)
RAL_ALL_USCITA = 52_000.0     # ultima RAL (per i contributi INPS che NON verserai)
ALIQUOTA_COMPUTO = 0.33
PIL_REALE = 0.0               # rivalutazione reale del montante INPS nel ponte
COEFF_TRASFORMAZIONE = 0.048  # coefficiente a 69 (coerente con proiezione-inps.py)
VERSAMENTO_FP_ANNUO = 7_000.0 # versamenti al fondo che si fermano (TFR + personale + datore)
RENDIMENTO_FP_REALE = 0.030   # rendimento reale del fondo (per i versamenti persi)

N_SIM = 20_000
SEED = 42
BLOCCO = 5                    # block bootstrap (anni consecutivi)

# =======================================================================


def aliquota_rita(anni_iscrizione):
    """15% − 0,30%/anno oltre il 15°, riduzione max 6 punti → floor 9%."""
    return max(0.09, 0.15 - 0.003 * max(0, anni_iscrizione - 15))


def simula_ponte(capitale, rendimenti, prelievi):
    """Percorsi del capitale-ponte. Ritorna (successi bool, saldi finali)."""
    n_sim, anni = rendimenti.shape
    saldi = np.full(n_sim, float(capitale))
    vivi = np.ones(n_sim, dtype=bool)
    for y in range(anni):
        saldi = saldi * (1 + rendimenti[:, y] - DRAG_FISCALE_ANNUO) - prelievi[y]
        vivi &= saldi >= 0
        saldi = np.maximum(saldi, 0.0)
    return vivi, saldi


def capitale_per_confidenza(target, rendimenti, prelievi, lo=0.0, hi=3_000_000.0):
    """Bisezione: capitale iniziale minimo con P(successo) ≥ target (stessi percorsi)."""
    if simula_ponte(hi, rendimenti, prelievi)[0].mean() < target:
        return float("nan")
    for _ in range(60):
        mid = (lo + hi) / 2
        if simula_ponte(mid, rendimenti, prelievi)[0].mean() >= target:
            hi = mid
        else:
            lo = mid
    return hi


def main():
    applica_override(globals())
    json_out = percorso_json()
    if SEED is not None:
        np.random.seed(SEED)

    anni_ponte = int(round(ETA_PENSIONE_VECCHIAIA - ETA_USCITA))
    if anni_ponte <= 0:
        raise SystemExit("ETA_PENSIONE_VECCHIAIA deve superare ETA_USCITA.")

    # ── RITA ──
    if RITA_ATTIVA:
        eta_inizio_rita = max(ETA_USCITA, ETA_PENSIONE_VECCHIAIA - ANNI_MAX_RITA)
        anni_rita = int(round(ETA_PENSIONE_VECCHIAIA - eta_inizio_rita))
        montante_rita = MONTANTE_FP_ALL_USCITA * QUOTA_MONTANTE_IN_RITA
        aliq = aliquota_rita(ANNI_ISCRIZIONE_FP)
        rata_lorda = montante_rita / anni_rita if anni_rita > 0 else 0.0
        rata_netta = rata_lorda * (1 - aliq)
    else:
        eta_inizio_rita, anni_rita, montante_rita, aliq, rata_lorda, rata_netta = (
            ETA_PENSIONE_VECCHIAIA, 0, 0.0, 0.0, 0.0, 0.0)

    # prelievi annui dal capitale-ponte (la RITA copre gli anni in cui è attiva)
    prelievi = np.array([
        max(0.0, SPESA_ANNUA_PONTE - (rata_netta if (ETA_USCITA + y) >= eta_inizio_rita else 0.0))
        for y in range(anni_ponte)
    ])

    # ── Monte Carlo ──
    az, ob = carica_storico("rendimenti-storici.csv")
    port = PESO_AZIONARIO_PONTE * az + (1 - PESO_AZIONARIO_PONTE) * ob
    rendimenti = blocchi_bootstrap(port, N_SIM, anni_ponte, BLOCCO)
    vivi, saldi = simula_ponte(CAPITALE_PONTE, rendimenti, prelievi)
    prob = vivi.mean()

    print("=" * 74)
    print(f"PONTE PENSIONISTICO — uscita a {ETA_USCITA:.0f}, copertura da {ETA_PENSIONE_VECCHIAIA:.0f} "
          f"({anni_ponte} anni da finanziare)")
    print("=" * 74)
    print(f"Spesa annua nel ponte (netta, reale): € {SPESA_ANNUA_PONTE:,.0f}")
    if RITA_ATTIVA and anni_rita > 0:
        print(f"\nRITA: dal compimento dei {eta_inizio_rita:.0f} anni ({anni_rita} anni), "
              f"montante destinato € {montante_rita:,.0f}")
        print(f"  rata lorda € {rata_lorda:,.0f}/anno → netta € {rata_netta:,.0f} "
              f"(aliquota {aliq:.1%} con {ANNI_ISCRIZIONE_FP} anni di partecipazione)")
        print(f"  requisiti versione 5 anni: cessazione lavoro, ≥20 anni contributi INPS, "
              f"≥5 anni di complementare")
    print(f"\nFabbisogno dal capitale-ponte, per fase:")
    for y in range(anni_ponte):
        eta = ETA_USCITA + y
        print(f"  {eta:.0f} → {eta+1:.0f} anni: € {prelievi[y]:>8,.0f}"
              + ("   (RITA attiva)" if prelievi[y] < SPESA_ANNUA_PONTE - 0.01 else ""))
    print(f"  totale nominale: € {prelievi.sum():,.0f}")

    print(f"\nMONTE CARLO ({N_SIM:,} percorsi, {PESO_AZIONARIO_PONTE:.0%} azioni, "
          f"drag fiscale {DRAG_FISCALE_ANNUO:.1%}):")
    print(f"  capitale-ponte disponibile: € {CAPITALE_PONTE:,.0f}")
    print(f"  → PROBABILITÀ di coprire il ponte: {prob:.1%}")
    if prob > 0:
        ok = saldi[vivi]
        print(f"  residuo a {ETA_PENSIONE_VECCHIAIA:.0f} anni (nei percorsi riusciti): "
              f"P10 € {pctl(ok,10):,.0f} | mediana € {pctl(ok,50):,.0f} | P90 € {pctl(ok,90):,.0f}")

    print(f"\nCAPITALE NECESSARIO all'uscita:")
    necessari = {conf: capitale_per_confidenza(conf, rendimenti, prelievi) for conf in (0.85, 0.95)}
    for conf, c in necessari.items():
        print(f"  per {conf:.0%} di confidenza: € {c:,.0f}")

    # ── Costi permanenti ──
    d_montante_inps = anni_ponte * RAL_ALL_USCITA * ALIQUOTA_COMPUTO * \
        (((1 + PIL_REALE) ** anni_ponte - 1) / (PIL_REALE * anni_ponte) if PIL_REALE > 0 else 1.0)
    d_inps = d_montante_inps * COEFF_TRASFORMAZIONE
    r = RENDIMENTO_FP_REALE
    fattore = ((1 + r) ** anni_ponte - 1) / r if r else anni_ponte  # a r = 0 l'annuità è lineare
    d_fondo_vers = VERSAMENTO_FP_ANNUO * fattore * COEFF_TRASFORMAZIONE
    d_fondo_rita = montante_rita * COEFF_TRASFORMAZIONE  # il montante usato non genera rendita a 69

    print(f"\nCOSTI PERMANENTI dell'uscita a {ETA_USCITA:.0f} (lordi, sulla pensione da "
          f"{ETA_PENSIONE_VECCHIAIA:.0f} in poi, per sempre):")
    print(f"  INPS: −€ {d_inps:,.0f}/anno   ({anni_ponte} anni di contributi in meno "
          f"su RAL € {RAL_ALL_USCITA:,.0f})")
    print(f"  Rendita fondo: −€ {d_fondo_vers:,.0f}/anno per i versamenti mancati"
          + (f", −€ {d_fondo_rita:,.0f}/anno per il montante usato in RITA" if montante_rita else ""))
    tot = d_inps + d_fondo_vers + d_fondo_rita
    print(f"  TOTALE: ≈ −€ {tot:,.0f}/anno di pensione lorda, per sempre")
    print(f"  (al netto il divario si attenua — vedi netto-pensione.py; e in cambio hai avuto")
    print(f"   {anni_ponte} anni di libertà + l'eventuale RITA già incassata)")

    print("\nAvvertenze: canali pubblici di anticipo non modellati (se ne maturi i requisiti,")
    print("il ponte si accorcia); RITA a rate costanti su comparto garantito; regole di oggi.")
    print("Questo strumento è educativo e non costituisce consulenza finanziaria o previdenziale.")

    if json_out:
        scrivi_json(json_out, {
            "anni_ponte": anni_ponte,
            "probabilita_successo": round(float(prob), 4),
            "capitale_ponte": CAPITALE_PONTE,
            "capitale_necessario": {f"{c:.0%}": round(v, 0) for c, v in necessari.items()},
            "rita": {"attiva": bool(RITA_ATTIVA), "eta_inizio": eta_inizio_rita,
                     "rata_lorda": round(rata_lorda, 2), "rata_netta": round(rata_netta, 2),
                     "aliquota": aliq},
            "costo_permanente_lordo_annuo": round(tot, 2),
        })


if __name__ == "__main__":
    main()
