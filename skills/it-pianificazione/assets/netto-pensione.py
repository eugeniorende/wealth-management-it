#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
netto-pensione.py — dal tasso di sostituzione LORDO a quello NETTO/NETTO.

Il lordo confronta due numeri tassati in modo molto diverso e sottostima
sistematicamente la copertura pensionistica:
  - lo STIPENDIO paga contributi IVS (9,19%) + IRPEF piena + addizionali;
  - la PENSIONE INPS non paga contributi e ha detrazioni dedicate;
  - la RENDITA del fondo pensione NON entra nell'IRPEF: paga un'imposta
    sostitutiva del 15%, ridotta dello 0,30% per ogni anno di partecipazione
    oltre il 15°, fino al minimo del 9%, sulla sola parte imponibile: TFR e
    contributi dedotti, non i rendimenti già tassati né i non dedotti comunicati
    (D.Lgs. 252/2005, art. 11 c. 6; dal 2027 art. 258 c. 4 D.Lgs. 117/2026).
    La quota imponibile è il parametro QUOTA_IMPONIBILE_FP: 1,0 (default) tassa
    tutta la rendita ed è una stima prudente, perché i rendimenti possono valere
    il 30-45% del montante. Il dato si ricava dal foglio Complementare
    dell'Excel (tassa in uscita / (aliquota × montante)) o dal fondo.
Questo script calcola il confronto giusto: pensione netta / ultimo stipendio netto.

Uso:
    python netto-pensione.py
    python netto-pensione.py --set PENSIONE_INPS_LORDA=27138 --set RAL_FINALE_LORDA=57972

Regole fiscali incorporate (Verificato: 2026-07; periodo d'imposta 2026):
  - IRPEF a tre scaglioni: 23% fino a 28.000; 33% da 28.000 a 50.000
    (ridotta dal 35% dalla L. 199/2025, art. 1 co. 3); 43% oltre 50.000
  - detrazione redditi da pensione (art. 13 TUIR, dal 2027 art. 13 D.Lgs. 117/2026): 1.955 € fino a 8.500 di
    reddito, poi decrescente, zero oltre 50.000 (no tax area 8.500 €)
  - detrazione lavoro dipendente (art. 13 c. 1 TUIR, stesso comma dal 2027): 1.955 € fino a 15.000, poi
    decrescente, zero oltre 50.000
  - contributi IVS a carico del dipendente: 9,19% della RAL, +1% sulla parte
    oltre la prima fascia di retribuzione pensionabile (€56.224), niente oltre
    il massimale (€122.295, iscritti dal 1996)
  - cuneo fiscale L. 207/2024 art. 1 c. 4-6 (solo lavoro dipendente, pensionati
    esclusi): fino a 20.000 € di reddito una somma esente pari al 7,1% / 5,3% /
    4,8% del reddito di lavoro (c. 4-5); tra 20.000 e 32.000 un'ulteriore
    detrazione di 1.000 €, che scende a zero tra 32.000 e 40.000 (c. 6)
    (Verificato: 2026-10: Normattiva L. 207/2024, Circ. AdE 4/E/2025, Circ. INPS 6/2026).
    Il c. 6 vale fino al 2026: dal 1/1/2027 lo abroga il D.Lgs. 117/2026, che
    riporta l'ulteriore detrazione nell'art. 13 del nuovo TUIR (comma da verificare)
  - addizionali regionale e comunale: parametriche (variano per territorio)

ONESTÀ METODOLOGICA
- Il calcolo proietta le regole fiscali DI OGGI su redditi in moneta di oggi:
  è lo standard della pianificazione, ma aliquote, scaglioni e detrazioni
  cambiano quasi ogni anno (questa stessa legge di bilancio ha toccato il
  secondo scaglione). Il numero è una fotografia coerente, non una promessa.
- Le addizionali locali sono medie parametriche: imposta i valori della tua
  regione/comune per il risultato puntuale.
- Semplificazioni dichiarate: nessun altro reddito IRPEF, nessuna detrazione
  per carichi di famiglia od oneri, niente trattamento integrativo.
- Rendita del fondo: la parte della rata che viene dai rendimenti maturati
  durante l'erogazione (art. 44 c. 1 lett. g-quinquies TUIR; dal 2027 art. 46 D.Lgs. 117/2026, lettera da verificare) è tassata a parte
  dall'erogatore al 26% (12,5% sui titoli di Stato) e non è modellata.
Questo strumento è educativo e non costituisce consulenza fiscale.
"""

from motore_bootstrap import applica_override, percorso_json, scrivi_json

# ============================== PARAMETRI ==============================

PENSIONE_INPS_LORDA = 27_000.0   # pensione pubblica lorda annua (da proiezione-inps.py)

# rendita lorda annua del fondo pensione: uno o più scenari (es. P10/P50/P90
# dal Monte Carlo). Etichetta libera; anche un solo scenario va bene.
RENDITE_FP = [
    ("P10", 9_500.0),
    ("mediana", 16_000.0),
    ("P90", 27_000.0),
]
ANNI_ISCRIZIONE_FP = 37          # anni di partecipazione al fondo alla decorrenza
                                 # (il TRASFERIMENTO tra fondi conserva l'anzianità)
QUOTA_IMPONIBILE_FP = 1.0        # parte della rendita fatta di TFR e contributi dedotti: la sola tassata
                                 # (1,0 = tutta, prudente; dall'Excel: tassa in uscita / (aliquota × montante))

RAL_FINALE_LORDA = 58_000.0      # ultimo stipendio lordo (per il confronto netto/netto)

ALIQ_CONTRIBUTI_DIP = 0.0919     # IVS a carico del dipendente (aliquota generalità)
PRIMA_FASCIA_PENSIONABILE = 56_224.0   # oltre questa retribuzione, +1% di IVS a carico del dipendente
ALIQ_AGGIUNTIVA_OLTRE_FASCIA = 0.01
MASSIMALE_CONTRIBUTIVO = 122_295.0     # oltre, niente contributi (iscritti dal 1996, Circ. INPS 6/2026)
CUNEO_L207 = True                # misure L. 207/2024 c. 4-6 sul netto dello stipendio (False = escluse)
CUNEO_SOMMA_ESENTE = [(8_500, 0.071), (15_000, 0.053), (20_000, 0.048)]  # (reddito fino a, % del reddito)
ADDIZIONALE_REGIONALE = 0.0173   # media nazionale indicativa; range reale ~1,23–3,33%
ADDIZIONALE_COMUNALE = 0.005     # media indicativa; range reale 0–0,9%

# Scaglioni IRPEF 2026 (limite superiore, aliquota) — L. 199/2025
SCAGLIONI = [(28_000, 0.23), (50_000, 0.33), (float("inf"), 0.43)]

# =======================================================================


def irpef_lorda(imponibile):
    imposta, prec = 0.0, 0.0
    for lim, aliq in SCAGLIONI:
        if imponibile > prec:
            imposta += (min(imponibile, lim) - prec) * aliq
        prec = lim
    return imposta


def detrazione_pensione(reddito):
    """Art. 13 co. 3 TUIR (redditi da pensione), struttura vigente 2026."""
    if reddito <= 8_500:
        return 1_955.0
    if reddito <= 28_000:
        return 700.0 + 1_255.0 * (28_000 - reddito) / 19_500
    if reddito <= 50_000:
        return 700.0 * (50_000 - reddito) / 22_000
    return 0.0


def detrazione_lavoro(reddito):
    """Art. 13 co. 1 TUIR (lavoro dipendente), struttura vigente 2026."""
    if reddito <= 15_000:
        return 1_955.0
    if reddito <= 28_000:
        return 1_910.0 + 1_190.0 * (28_000 - reddito) / 13_000
    if reddito <= 50_000:
        return 1_910.0 * (50_000 - reddito) / 22_000
    return 0.0


def aliquota_rendita_fp(anni_iscrizione):
    """15% − 0,30% per ogni anno oltre il 15°, floor 9% (D.Lgs. 252/2005 art. 11)."""
    return max(0.09, 0.15 - 0.003 * max(0, anni_iscrizione - 15))


def rendita_netta_fp(lorda, anni_iscrizione, quota_imponibile):
    """Rendita del fondo al netto della ritenuta 15→9%, applicata alla sola quota imponibile
    (TFR e contributi dedotti: art. 11 c. 6 D.Lgs. 252/2005, dal 2027 art. 258 c. 4 D.Lgs. 117/2026)."""
    return lorda * (1 - aliquota_rendita_fp(anni_iscrizione) * quota_imponibile)


def netto_pensionato(inps_lorda, add_reg, add_com):
    """Netto della sola pensione INPS (IRPEF + addizionali, detrazione pensione)."""
    irpef = max(0.0, irpef_lorda(inps_lorda) - detrazione_pensione(inps_lorda))
    addiz = inps_lorda * (add_reg + add_com) if irpef > 0 else 0.0
    return inps_lorda - irpef - addiz, irpef, addiz


def contributi_lavoratore(ral, aliq_contr):
    """IVS a carico del dipendente: aliquota base, +1% oltre la prima fascia, niente oltre il massimale."""
    base = min(ral, MASSIMALE_CONTRIBUTIVO)
    return base * aliq_contr + max(0.0, base - PRIMA_FASCIA_PENSIONABILE) * ALIQ_AGGIUNTIVA_OLTRE_FASCIA


def cuneo_l207(reddito):
    """L. 207/2024 art. 1 c. 4-6: (somma esente, ulteriore detrazione) per il lavoro dipendente.

    Il reddito di lavoro è anche il reddito complessivo (nessun altro reddito, come nel resto dello script)."""
    if not CUNEO_L207:
        return 0.0, 0.0
    if reddito <= 20_000:
        pct = next(p for lim, p in CUNEO_SOMMA_ESENTE if reddito <= lim)
        return reddito * pct, 0.0
    if reddito <= 32_000:
        return 0.0, 1_000.0
    if reddito <= 40_000:
        return 0.0, 1_000.0 * (40_000 - reddito) / 8_000
    return 0.0, 0.0


def netto_lavoratore(ral, aliq_contr, add_reg, add_com):
    """Netto dello stipendio: contributi IVS, IRPEF con detrazione lavoro e cuneo L. 207/2024, addizionali."""
    contributi = contributi_lavoratore(ral, aliq_contr)
    imponibile = ral - contributi
    somma_esente, ulteriore = cuneo_l207(imponibile)
    irpef = max(0.0, irpef_lorda(imponibile) - detrazione_lavoro(imponibile) - ulteriore)
    addiz = imponibile * (add_reg + add_com) if irpef > 0 else 0.0
    return ral - contributi - irpef - addiz + somma_esente, contributi, irpef, addiz


def main():
    applica_override(globals())
    json_out = percorso_json()

    print("=" * 74)
    print("TASSO DI SOSTITUZIONE NETTO — pensione netta / ultimo stipendio netto")
    print("=" * 74)

    # lato lavoro
    netto_lav, contr, irpef_lav, add_lav = netto_lavoratore(
        RAL_FINALE_LORDA, ALIQ_CONTRIBUTI_DIP, ADDIZIONALE_REGIONALE, ADDIZIONALE_COMUNALE)
    print(f"\nULTIMO STIPENDIO   lordo € {RAL_FINALE_LORDA:>10,.0f}")
    print(f"  − contributi IVS ({ALIQ_CONTRIBUTI_DIP:.2%})   € {contr:>9,.0f}")
    print(f"  − IRPEF (netto detrazione lavoro) € {irpef_lav:>9,.0f}")
    print(f"  − addizionali ({(ADDIZIONALE_REGIONALE+ADDIZIONALE_COMUNALE):.2%})"
          f"        € {add_lav:>9,.0f}")
    esente = cuneo_l207(RAL_FINALE_LORDA - contr)[0]
    if esente:
        print(f"  + somma esente L. 207/2024     € {esente:>9,.0f}")
    print(f"  = NETTO            € {netto_lav:>10,.0f}   (aliquota effettiva "
          f"{1-netto_lav/RAL_FINALE_LORDA:.1%})")

    # lato pensione INPS
    netto_inps, irpef_p, add_p = netto_pensionato(
        PENSIONE_INPS_LORDA, ADDIZIONALE_REGIONALE, ADDIZIONALE_COMUNALE)
    print(f"\nPENSIONE INPS      lorda € {PENSIONE_INPS_LORDA:>10,.0f}")
    print(f"  − IRPEF (netto detrazione pensione) € {irpef_p:>9,.0f}")
    print(f"  − addizionali      € {add_p:>9,.0f}")
    print(f"  = NETTA            € {netto_inps:>10,.0f}   (aliquota effettiva "
          f"{1-netto_inps/PENSIONE_INPS_LORDA:.1%})")

    # rendita complementare
    aliq_fp = aliquota_rendita_fp(ANNI_ISCRIZIONE_FP)
    print(f"\nRENDITA FONDO PENSIONE — imposta sostitutiva {aliq_fp:.1%} "
          f"({ANNI_ISCRIZIONE_FP} anni di partecipazione; fuori IRPEF) "
          f"sul {QUOTA_IMPONIBILE_FP:.0%} della rendita")
    if QUOTA_IMPONIBILE_FP >= 1:
        print("  stima prudente: tassa anche i rendimenti già tassati; imposta QUOTA_IMPONIBILE_FP "
              "con la quota di TFR e contributi dedotti")

    print(f"\n{'scenario':<10}{'rendita lorda':>14}{'rendita netta':>14}"
          f"{'pens. netta tot':>16}{'TASSO NETTO':>13}{'(lordo)':>9}")
    ral_lorda_tot = RAL_FINALE_LORDA
    for nome, lorda in RENDITE_FP:
        netta = rendita_netta_fp(lorda, ANNI_ISCRIZIONE_FP, QUOTA_IMPONIBILE_FP)
        tot = netto_inps + netta
        t_netto = tot / netto_lav
        t_lordo = (PENSIONE_INPS_LORDA + lorda) / ral_lorda_tot
        print(f"{nome:<10}{lorda:>14,.0f}{netta:>14,.0f}{tot:>16,.0f}"
              f"{t_netto:>12.1%}{t_lordo:>9.1%}")

    print("\nLettura: il tasso NETTO è il numero che descrive il tenore di vita —")
    print("confronta ciò che entra davvero in tasca nei due momenti della vita.")
    print("Il divario col lordo viene da tre asimmetrie: in pensione non si versano")
    print(f"contributi ({ALIQ_CONTRIBUTI_DIP:.2%}), la rendita complementare paga "
          f"{aliq_fp:.0%} secco fuori IRPEF,")
    print("e l'IRPEF su un reddito più basso sconta scaglioni e detrazioni migliori.")
    print("\nAvvertenze: regole fiscali di OGGI proiettate al futuro (cambiano quasi")
    print("ogni anno); addizionali medie indicative; nessun altro reddito o detrazione.")
    print("Questo strumento è educativo e non costituisce consulenza fiscale.")

    if json_out:
        scrivi_json(json_out, {
            "netto_ultimo_stipendio": round(netto_lav, 2),
            "netto_pensione_inps": round(netto_inps, 2),
            "aliquota_rendita_fp": aliq_fp,
            "quota_imponibile_fp": QUOTA_IMPONIBILE_FP,
            "scenari": [
                {"nome": nome, "rendita_lorda": lorda,
                 "rendita_netta": round(rendita_netta_fp(lorda, ANNI_ISCRIZIONE_FP, QUOTA_IMPONIBILE_FP), 2),
                 "pensione_netta_totale": round(
                     netto_inps + rendita_netta_fp(lorda, ANNI_ISCRIZIONE_FP, QUOTA_IMPONIBILE_FP), 2),
                 "tasso_sostituzione_netto": round(
                     (netto_inps + rendita_netta_fp(lorda, ANNI_ISCRIZIONE_FP, QUOTA_IMPONIBILE_FP)) / netto_lav, 4),
                 "tasso_sostituzione_lordo": round((PENSIONE_INPS_LORDA + lorda) / RAL_FINALE_LORDA, 4)}
                for nome, lorda in RENDITE_FP],
        })


if __name__ == "__main__":
    main()
