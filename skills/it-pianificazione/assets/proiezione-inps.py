#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
proiezione-inps.py — proiezione parametrica della pensione INPS (metodo contributivo).

Prende il montante contributivo attuale (da importa-previdenza.py o da "La mia pensione futura"),
la RAL e le ipotesi di scenario, e calcola la pensione lorda annua e il tasso di sostituzione.

Tutto è in TERMINI REALI (moneta di oggi): la crescita della RAL è al netto dell'inflazione,
e la rivalutazione del montante usa il PIL REALE (il montante per legge cresce col PIL nominale,
cioè PIL reale + inflazione; deflazionando, resta il PIL reale).

Uso:
    python proiezione-inps.py [--set NOME=VALORE ...] [--json FILE]
    (--help elenca le costanti sovrascrivibili; senza --set valgono i default qui sotto)

ONESTÀ METODOLOGICA
- Una RAL crescente ABBASSA il tasso di sostituzione: la pensione contributiva si basa sulla
  media dei versamenti di tutta la carriera, quindi rimpiazza una frazione minore di uno
  stipendio finale più alto. Proiettare a RAL piatta gonfia il tasso (ottimismo mascherato).
- I due parametri fuori dal tuo controllo — PIL reale e coefficienti di trasformazione futuri —
  spostano il risultato di parecchi punti: per questo l'output include una tabella di sensibilità.
- Il risultato è LORDO. Il netto è relativamente migliore (in pensione non si versano contributi
  e l'IRPEF su un reddito minore è più leggera).
- Oltre il massimale contributivo (MASSIMALE_CONTRIBUTIVO) non si versano contributi: per le RAL
  alte la pensione pubblica smette di crescere col reddito.
"""

from motore_bootstrap import cli, errore, numero, pct, scrivi_json

# ============================== PARAMETRI ==============================

MONTANTE_ATTUALE = 85_000.0   # montante contributivo a oggi (€) — da importa-previdenza.py
                              # o, meglio, da "La mia pensione futura" sul portale INPS
RAL_ATTUALE      = 36_000.0   # retribuzione annua lorda attuale (€)
ALIQUOTA_COMPUTO = 0.33       # computo IVS dipendenti (artigiani e commercianti 0,24; gestione separata 0,25, sul 26,07% versato)

ETA_ATTUALE        = 37.0     # età attuale (anche frazionaria)
ETA_PENSIONAMENTO  = 69.0     # età di uscita ipotizzata (la vecchiaia è indicizzata alla
                              # speranza di vita: per chi è giovane oggi, ~68-70 è realistico)

CRESCITA_REALE_RAL = 0.015    # crescita REALE annua della RAL (0 = carriera piatta: gonfia
                              # il tasso di sostituzione, usalo solo consapevolmente)
PIL_REALE          = 0.005    # crescita REALE del PIL = rendimento reale del montante
                              # (media storica recente Italia ~0-1%; 0 = stagnazione)
MASSIMALE_CONTRIBUTIVO = 122_295.0  # retribuzione massima su cui si versano contributi (post-1995),
                              # tenuto costante in termini reali (Circ. INPS 6/2026; Verificato: 2026-10)

# Coefficiente di trasformazione (montante → rendita) all'età di pensionamento:
COEFF_ESPLICITO      = None   # se valorizzato (es. 0.048), vince su tabella e riduzione
RIDUZIONE_COEFF_ANNUA = 0.007 # riduzione RELATIVA annua attesa dei coefficienti per
                              # l'allungamento della speranza di vita (~-0,7%/anno, coerente
                              # con le revisioni biennali storiche ~-1,5/-2%; 0 = coefficienti
                              # vigenti congelati, scenario ottimistico)

# Tabella vigente (biennio 2025-2026, DM 436 del 20/11/2024; Verificato: 2026-06) — età: coefficiente
COEFF_2025_2026 = {
    57: 0.04204, 58: 0.04308, 59: 0.04419, 60: 0.04536, 61: 0.04661,
    62: 0.04795, 63: 0.04936, 64: 0.05088, 65: 0.05250, 66: 0.05423,
    67: 0.05608, 68: 0.05808, 69: 0.06024, 70: 0.06258, 71: 0.06510,
}

# =======================================================================


def coeff_vigente(eta):
    """Coefficiente della tabella vigente all'età data (interpolazione sui dodicesimi, come da norma)."""
    e_min, e_max = min(COEFF_2025_2026), max(COEFF_2025_2026)
    e = max(e_min, min(e_max, eta))
    lo = int(e)
    if lo >= e_max:
        return COEFF_2025_2026[e_max]
    frazione = e - lo
    return COEFF_2025_2026[lo] + frazione * (COEFF_2025_2026[lo + 1] - COEFF_2025_2026[lo])


def proietta(montante0, ral0, g_ral, pil, anni, coeff):
    """Montante e pensione a fine carriera, tutto in termini reali (moneta di oggi).

    Meccanica L.335/1995 rispettata: i contributi dell'anno t si rivalutano da t+1 in poi
    (l'ultimo anno non si rivaluta) e la retribuzione oltre il massimale non versa contributi.
    Ritorna (montante_finale, quota_attuale, quota_futuri, pensione).
    """
    fv_attuale = montante0 * (1 + pil) ** anni
    fv_futuri = 0.0
    for t in range(anni):
        contributo = min(ral0 * (1 + g_ral) ** t, MASSIMALE_CONTRIBUTIVO) * ALIQUOTA_COMPUTO
        fv_futuri += contributo * (1 + pil) ** (anni - 1 - t)
    montante_fin = fv_attuale + fv_futuri
    return montante_fin, fv_attuale, fv_futuri, montante_fin * coeff


def main():
    args = cli("Proiezione parametrica della pensione INPS in euro di oggi (metodo contributivo), con la "
               "sensibilità a PIL reale e coefficienti di trasformazione.", globals(), json=True,
               da_json={"montante_attuale": "MONTANTE_ATTUALE", "ral_attuale": "RAL_ATTUALE",
                        "eta_attuale": "ETA_ATTUALE"})   # il JSON di importa-previdenza.py
    json_out = args.json
    anni = ETA_PENSIONAMENTO - ETA_ATTUALE
    if anni <= 0:
        errore("ETA_PENSIONAMENTO deve superare ETA_ATTUALE.")
    n = round(anni)
    ral_fin = RAL_ATTUALE * (1 + CRESCITA_REALE_RAL) ** n

    c_vig = coeff_vigente(ETA_PENSIONAMENTO)
    if COEFF_ESPLICITO is not None:
        coeff, origine = COEFF_ESPLICITO, "esplicito (da parametro)"
    else:
        coeff = c_vig * (1 - RIDUZIONE_COEFF_ANNUA) ** n
        origine = (f"tabella 2025-26 a {ETA_PENSIONAMENTO:.0f} anni ({pct(c_vig, 3)}) "
                   f"ridotto del {pct(RIDUZIONE_COEFF_ANNUA)}/anno per {n} anni")

    m_fin, fv_att, fv_fut, pensione = proietta(
        MONTANTE_ATTUALE, RAL_ATTUALE, CRESCITA_REALE_RAL, PIL_REALE, n, coeff)

    print("=" * 72)
    print("PROIEZIONE PENSIONE INPS — metodo contributivo, valori reali (€ di oggi)")
    print("=" * 72)
    print(f"Orizzonte: {n} anni (da {ETA_ATTUALE:.0f} a {ETA_PENSIONAMENTO:.0f} anni)")
    print(f"RAL: € {numero(RAL_ATTUALE)} oggi → € {numero(ral_fin)} finale "
          f"(crescita reale {pct(CRESCITA_REALE_RAL, 1, segno=True)}/anno)")
    print(f"\nMontante contributivo a {ETA_PENSIONAMENTO:.0f} anni: € {numero(m_fin)}")
    print(f"  di cui montante attuale rivalutato:  € {numero(fv_att)}  (PIL reale {pct(PIL_REALE, 1, segno=True)})")
    print(f"  di cui contributi futuri rivalutati: € {numero(fv_fut)}")
    print(f"\nCoefficiente di trasformazione: {pct(coeff, 3)}")
    print(f"  origine: {origine}")
    print(f"\nPENSIONE LORDA ANNUA: ≈ € {numero(pensione)}   (≈ € {numero(pensione/13)} × 13 mensilità)")
    print(f"TASSO DI SOSTITUZIONE LORDO: {pct(pensione/ral_fin)} della RAL finale"
          f"   ({pct(pensione/RAL_ATTUALE)} della RAL di oggi)")

    # ------------------------- sensibilità -------------------------
    print("\n" + "-" * 72)
    print("SENSIBILITÀ del tasso di sostituzione (vs RAL finale)")
    print("ai due parametri fuori dal tuo controllo:")
    riduzioni = [0.0, 0.007, 0.010]
    pil_scenari = [0.0, 0.005, 0.010]
    intest = "".join(f"{'coeff. vigenti' if r == 0 else f'riduz. {pct(r)}/a':>18}" for r in riduzioni)
    print(f"  {'PIL reale':<12}{intest}")
    for p in pil_scenari:
        riga = f"  {pct(p):>9}   "
        for r in riduzioni:
            c = (COEFF_ESPLICITO if COEFF_ESPLICITO is not None
                 else coeff_vigente(ETA_PENSIONAMENTO) * (1 - r) ** n)
            _, _, _, pens = proietta(MONTANTE_ATTUALE, RAL_ATTUALE, CRESCITA_REALE_RAL, p, n, c)
            riga += f"{pct(pens/ral_fin):>18}"
        print(riga)
    if COEFF_ESPLICITO is not None:
        print("  (COEFF_ESPLICITO impostato: le colonne coincidono; azzeralo per la sensibilità piena)")

    print("\nAvvertenze:")
    print("  - risultato LORDO: il netto è relativamente migliore (niente contributi, IRPEF più bassa)")
    print("  - una RAL crescente abbassa il tasso: proiettare a RAL piatta lo gonfia")
    print("  - PIL e coefficienti futuri non dipendono da te: pianifica sulla riga prudente,")
    print("    non su quella che ti piace")
    print("\nQuesto strumento è educativo e non costituisce consulenza finanziaria o previdenziale.")

    if json_out:
        scrivi_json(json_out, {
            "pensione_inps_lorda_annua": round(pensione, 2),
            "montante_finale": round(m_fin, 2),
            "ral_finale": round(ral_fin, 2),
            "coefficiente_trasformazione": round(coeff, 5),
            "tasso_sostituzione_lordo_vs_ral_finale": round(pensione / ral_fin, 4),
            "anni_al_pensionamento": n,
            "eta_pensionamento": ETA_PENSIONAMENTO,
        })


if __name__ == "__main__":
    main()
