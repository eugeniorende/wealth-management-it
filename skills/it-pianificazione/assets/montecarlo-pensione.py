#!/usr/bin/env python3
"""
montecarlo-pensione.py — la dimensione stocastica della proiezione pensionistica.

Il foglio Excel (proiezione-pensione.xlsx) fa una proiezione DETERMINISTICA: dato un rendimento
del fondo pensione, calcola un montante e un tasso di sostituzione. Ma il rendimento del fondo non
è noto: è soggetto al rischio di mercato. Questo script aggiunge la distribuzione degli esiti.

IL PUNTO METODOLOGICO (ed è una scelta di onestà): i due pilastri della pensione NON hanno lo
stesso rischio.
  • La pensione PUBBLICA (INPS contributivo) è rivalutata alla media quinquennale del PIL, NON ai
    mercati. Applicarle la volatilità azionaria sarebbe semplicemente sbagliato. Qui fa da ÀNCORA
    deterministica: il valore lordo annuo che hai stimato nel foglio Excel.
  • La pensione COMPLEMENTARE (fondo pensione) è investita in un comparto: il suo montante dipende
    dai rendimenti di mercato. È QUI che il Monte Carlo ha senso.
Conseguenza pratica e onesta: la dispersione del tasso di sostituzione viene quasi tutta dal
pilastro complementare; il pubblico la àncora. Lo script lo mostra esplicitamente.

Il motore è lo stesso block bootstrap di montecarlo-obiettivi.py: ricampiona blocchi di anni
consecutivi dalla serie storica reale (così code grasse, correlazioni e mean reversion sono quelle
vere), ricentrando la media sul rendimento atteso del comparto (si calibra il LIVELLO sull'ipotesi,
si mantiene la FORMA reale). Stessa serie Damodaran di obiettivi.

Termini: esprimi TUTTI i valori in modo coerente — consigliato in EURO DI OGGI (potere d'acquisto):
rendimento reale del comparto, pensione INPS e RAL in moneta di oggi. Il bootstrap trapianta la
volatilità storica (nominale) sul livello scelto; è un'approssimazione consapevole, come in obiettivi.

Dipendenze: numpy. Uso: python montecarlo-pensione.py
"""

import numpy as np

from motore_bootstrap import applica_override, carica_storico, blocchi_bootstrap, pctl, percorso_json, scrivi_json

# ─────────────── INPS — pilastro pubblico (ÀNCORA deterministica) ───────────────
PENSIONE_INPS_ANNUA = 21000.0      # pensione pubblica annua LORDA al pensionamento, dal foglio Excel
                                   # (rivalutata al PIL, non al mercato: nessun Monte Carlo qui)

# ─────────────── Fondo pensione — pilastro complementare (STOCASTICO) ───────────
FP_POT_ATTUALE = 25000.0           # montante attuale del fondo pensione (€)
FP_VERSAMENTO_ANNUO = 3000.0       # versamento annuo INIZIALE: contributo + TFR + quota datore (€)
CRESCITA_VERSAMENTO_REALE = 0.0    # crescita reale annua del versamento (se lo stipendio cresce, TFR e
                                   # contributi salgono; 0 = versamento costante in moneta di oggi)
ANNI = 30                          # anni al pensionamento
FP_RENDIMENTO_ATTESO_REALE = 0.025 # rendimento atteso REALE del comparto (bilanciato ~2,5%)
FP_PESO_AZIONARIO = 0.50           # quota azionaria del comparto (per volatilità/forma del bootstrap)
COEFF_RENDITA_FP = 0.050           # conversione del montante FP in rendita annua (~5%); dipende dai
                                   # coefficienti demografici al pensionamento → parametro

# ─────────────── Tasso di sostituzione ───────────────
RAL_FINALE = 45000.0               # RAL stimata all'ultimo anno, in moneta di oggi (denominatore)
TASSO_SOSTITUZIONE_TARGET = 0.70   # soglia per la probabilità di "successo"

# ─────────────── Monte Carlo ───────────────
N_SIM = 20000
BLOCCO = 5                         # lunghezza blocco (anni consecutivi): preserva la sequenza
RICENTRA_MEDIA = True              # ricentra la media storica sul rendimento atteso del comparto
SEED = 42                          # riproducibilità (rimuovere per casualità piena)
FILE_STORICO = "rendimenti-storici.csv"


def simula_fp(az_hist, ob_hist):
    """Distribuzione del montante del fondo pensione al pensionamento, via block bootstrap.
    Stessa logica di montecarlo-obiettivi.py, con versamenti ANNUI (contributi a metà anno)."""
    port = FP_PESO_AZIONARIO * az_hist + (1.0 - FP_PESO_AZIONARIO) * ob_hist
    if RICENTRA_MEDIA:
        port = port - port.mean() + FP_RENDIMENTO_ATTESO_REALE
    rendimenti = blocchi_bootstrap(port, N_SIM, ANNI, BLOCCO)
    saldi = np.full(N_SIM, FP_POT_ATTUALE, dtype=float)
    for y in range(ANNI):
        R = rendimenti[:, y]
        versamento_y = FP_VERSAMENTO_ANNUO * (1 + CRESCITA_VERSAMENTO_REALE) ** y
        saldi = saldi * (1 + R) + versamento_y * np.sqrt(np.maximum(1 + R, 1e-4))
    return saldi


def main():
    applica_override(globals())
    json_out = percorso_json()
    if SEED is not None:
        np.random.seed(SEED)
    az, ob = carica_storico(FILE_STORICO)

    pot = simula_fp(az, ob)                       # montante FP simulato
    fp_rendita = pot * COEFF_RENDITA_FP           # rendita annua complementare
    totale = PENSIONE_INPS_ANNUA + fp_rendita     # pensione totale lorda annua
    tasso = totale / RAL_FINALE                   # tasso di sostituzione

    # contributi al tasso di sostituzione
    ts_inps = PENSIONE_INPS_ANNUA / RAL_FINALE    # àncora (fisso)
    ts_fp_med = pctl(fp_rendita, 50) / RAL_FINALE

    print(f"\n{'='*70}")
    print(f"MONTE CARLO PENSIONE — {N_SIM:,} percorsi, {ANNI} anni, bootstrap a blocchi di {BLOCCO}")
    print(f"{'='*70}")
    print(f"Comparto fondo pensione: {FP_PESO_AZIONARIO*100:.0f}% azionario, "
          f"rendimento reale atteso {FP_RENDIMENTO_ATTESO_REALE*100:.1f}%")

    print(f"\n— PILASTRO COMPLEMENTARE (fondo pensione) — la parte a rischio di mercato —")
    print(f"   Montante al pensionamento:   P10 € {pctl(pot,10):>10,.0f}   "
          f"mediana € {pctl(pot,50):>10,.0f}   P90 € {pctl(pot,90):>10,.0f}")
    print(f"   Rendita annua (coeff {COEFF_RENDITA_FP*100:.1f}%): P10 € {pctl(fp_rendita,10):>10,.0f}   "
          f"mediana € {pctl(fp_rendita,50):>10,.0f}   P90 € {pctl(fp_rendita,90):>10,.0f}")

    print(f"\n— PILASTRO PUBBLICO (INPS) — l'àncora, non simulata —")
    print(f"   Pensione annua lorda:        € {PENSIONE_INPS_ANNUA:>10,.0f}   (fissa: rivalutata al PIL, non ai mercati)")

    print(f"\n— TOTALE: tasso di sostituzione lordo (pensione / RAL {RAL_FINALE:,.0f}) —")
    print(f"   P10  {pctl(tasso,10)*100:>5.1f}%      mediana  {pctl(tasso,50)*100:>5.1f}%      "
          f"P90  {pctl(tasso,90)*100:>5.1f}%")
    p_target = float(np.mean(tasso >= TASSO_SOSTITUZIONE_TARGET))
    print(f"   Probabilità di raggiungere il {TASSO_SOSTITUZIONE_TARGET*100:.0f}%: {p_target*100:.1f}%")

    print(f"\n— LA LETTURA ONESTA —")
    print(f"   Il pubblico àncora il tasso di sostituzione a {ts_inps*100:.1f}% (fisso).")
    print(f"   Il fondo pensione ci aggiunge una banda di mercato: dal +{pctl(fp_rendita,10)/RAL_FINALE*100:.1f}% (P10) "
          f"al +{pctl(fp_rendita,90)/RAL_FINALE*100:.1f}% (P90).")
    print(f"   Quindi il totale oscilla tra {pctl(tasso,10)*100:.1f}% e {pctl(tasso,90)*100:.1f}%, e tutta")
    print(f"   l'incertezza viene dal complementare: è lì che la scelta del comparto conta.")
    print(f"\n   Caveat: restano fuori dal Monte Carlo (perché non sono rischio di mercato) la discesa")
    print(f"   del coefficiente di trasformazione e la rivalutazione PIL dell'INPS — vanno trattate")
    print(f"   come scenari nel foglio Excel, non come volatilità.\n")

    # confronto col deterministico (atteso): la mediana deve stare vicino al montante deterministico
    det = FP_POT_ATTUALE * (1+FP_RENDIMENTO_ATTESO_REALE)**ANNI
    r, g = FP_RENDIMENTO_ATTESO_REALE, CRESCITA_VERSAMENTO_REALE
    if abs(r - g) < 1e-9:
        det += FP_VERSAMENTO_ANNUO * ANNI * (1 + r) ** (ANNI - 1)
    else:
        det += FP_VERSAMENTO_ANNUO * (((1+r)**ANNI - (1+g)**ANNI) / (r - g))
    print(f"[check] montante FP deterministico ≈ € {det:,.0f}; mediana simulata € {pctl(pot,50):,.0f} "
          f"(la mediana sta sotto per il volatility drag, atteso)")

    if json_out:
        scrivi_json(json_out, {
            "montante_fp": {"p10": round(pctl(pot, 10)), "mediana": round(pctl(pot, 50)), "p90": round(pctl(pot, 90))},
            "rendita_fp": {"p10": round(pctl(fp_rendita, 10)), "mediana": round(pctl(fp_rendita, 50)), "p90": round(pctl(fp_rendita, 90))},
            "pensione_inps_lorda": PENSIONE_INPS_ANNUA,
            "tasso_sostituzione_lordo": {"p10": round(pctl(tasso, 10), 4), "mediana": round(pctl(tasso, 50), 4), "p90": round(pctl(tasso, 90), 4)},
            "prob_target": round(p_target, 4),
            "target": TASSO_SOSTITUZIONE_TARGET,
        })


if __name__ == "__main__":
    main()
