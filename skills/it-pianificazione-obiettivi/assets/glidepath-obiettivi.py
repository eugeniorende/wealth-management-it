#!/usr/bin/env python3
"""
Glide path automatico per il pianificatore obiettivi.

Genera il CALENDARIO DI DE-RISKING anno per anno: per ogni obiettivo, la quota
azionaria target che dovrebbe avere a ciascun anno fino alla scadenza, e
l'allocazione azionaria complessiva del portafoglio (aggregata, pesata per il
capitale proiettato). È il calendario che alimenta it-rebalance: gli dice come
spostare i target nel tempo, eseguendo il de-risking progressivo.

Logica del glide path (per ogni obiettivo):
  - tiene la quota azionaria di partenza (del profilo) finché mancano più anni
    della "finestra di de-risking"
  - poi scende LINEARMENTE fino alla quota di atterraggio entro la scadenza
  - la finestra effettiva è min(finestra, orizzonte): un obiettivo corto de-riska
    sull'intera vita, uno lungo solo negli ultimi anni

Aggregato di portafoglio:
  - per ogni anno, pesa la quota azionaria di ogni obiettivo ATTIVO per il suo
    capitale proiettato a quell'anno (crescita al rendimento atteso dell'anno lungo
    il glide path + versamenti); un obiettivo "esce" dal portafoglio quando raggiunge
    la scadenza
  - i versamenti sono quelli del foglio (colonna I), che tengono conto del de-risking:
    lo script li riepiloga in fondo. Il foglio fissa la finestra (Parametri!B7), la rampa
    lineare e l'atterraggio sul profilo a quota azionaria minima: con ATTERRAGGIO_AZ,
    CURVATURA o FINESTRA_DERISK diversi, o su un pianificatore precedente alla 0.10.0
    (colonna I a quota fissa), i versamenti divergono dalla colonna I e lo script lo dice

Dipendenze: openpyxl  (pip install openpyxl)
Uso:        python glidepath-obiettivi.py [percorso/pianificatore-obiettivi.xlsx]

NON è consulenza di investimento. Il glide path è una regola metodologica, le %
sono esempi; la proiezione del capitale usa il rendimento atteso anno per anno (non
modella la volatilità). Vedi glide-path.md per i limiti e l'interpretazione.
"""

import sys
import os

from motore_bootstrap import (cli, errore, euro, frazioni_glide, leggi_pianificatore, numero, pmt_glide, quota_glide,
                              scarti_dal_foglio, scrivi_json)

# ---- Parametri del glide path (editabili) ----
FINESTRA_DERISK = None   # anni prima della scadenza in cui inizia il de-risking;
                         #   None = dal foglio (Parametri!B7, 7 anni nell'esempio)
ATTERRAGGIO_AZ = 0.00    # quota azionaria target alla scadenza (0% = tutto liquido/sicuro)
CURVATURA = 1.0          # forma della rampa: 1.0 = lineare; <1 tiene la quota azionaria
                         #   più alta all'inizio della finestra e scende ripida vicino alla scadenza
                         #   (più crescita, de-risking tardivo); >1 de-riska prima e più dolce dopo

# Posizioni note nel foglio (coerenti con build_obiettivi.py)


def leggi_excel(path):
    """Parametri, profili (rendimento, % azionario) e obiettivi dal lettore unico del motore: qui entrano
    anche gli obiettivi senza target («il più possibile», marcati (max))."""
    d = leggi_pianificatore(path)
    profili = {n: (p["rendimento"], p["azionario"]) for n, p in d["profili"].items()}
    return d["inflazione"], d["finestra"], d["finestra_nel_foglio"], profili, d["obiettivi"]


def rendimento_a_quota(quota, profili):
    """Rendimento atteso per una quota azionaria, lineare tra i profili (quello di atterraggio)."""
    pts = sorted(profili.values(), key=lambda p: p[1])     # (rend, quota) per quota crescente
    if quota <= pts[0][1]:
        return pts[0][0]
    for (r0, q0), (r1, q1) in zip(pts, pts[1:]):
        if quota <= q1 and q1 > q0:
            return r0 + (r1 - r0) * (quota - q0) / (q1 - q0)
    return pts[-1][0]


def equity_glide(anni_residui, eq_start, finestra, atterraggio):
    """Quota azionaria target dato il tempo residuo all'obiettivo (definizione nel motore)."""
    return quota_glide(anni_residui, eq_start, finestra, atterraggio, CURVATURA)


def pct(x):
    return f"{numero(x*100)}%"


def main():
    args = cli("Calendario di de-risking anno per anno (glide path) per ogni obiettivo del pianificatore e per "
               "l'aggregato di portafoglio.", globals(), json=True, argomenti=(
                   (("excel",), {"nargs": "?", "help": "pianificatore-obiettivi.xlsx compilato (default: il modello del plugin)"}),))
    path = args.excel or os.path.join(os.path.dirname(os.path.abspath(__file__)), "pianificatore-obiettivi.xlsx")
    inflazione, finestra_foglio, nel_foglio, profili, obiettivi = leggi_excel(path)
    if not obiettivi:
        errore("nessun obiettivo nel foglio: compila il pianificatore prima.")
    finestra = finestra_foglio if FINESTRA_DERISK is None else int(FINESTRA_DERISK)
    rend_atterraggio = rendimento_a_quota(ATTERRAGGIO_AZ, profili)
    # i versamenti coincidono con la colonna I solo coi parametri del glide path del foglio
    scarti = scarti_dal_foglio(finestra, finestra_foglio if nel_foglio else None, ATTERRAGGIO_AZ,
                               min(eq for _, eq in profili.values()), CURVATURA)

    orizzonte_max = max(g["orizzonte"] for g in obiettivi)

    # pre-calcolo per ogni obiettivo: pmt, finestra, capitale proiettato anno per anno
    for g in obiettivi:
        rend, eq = profili[g["profilo"]]        # il lettore ha già respinto i profili ignoti
        g["rend"], g["eq_start"] = rend, eq
        g["finestra"] = min(finestra, g["orizzonte"])
        # i terminanti de-riskano: rendimento dell'anno lineare nella quota tra profilo e atterraggio
        de_risk = not g["permanente"] and eq > ATTERRAGGIO_AZ
        rend_l = rend_atterraggio if de_risk else rend
        frazioni = frazioni_glide(g["orizzonte"], finestra, CURVATURA)
        tassi = rend_l + (rend - rend_l) * frazioni
        if g["target_oggi"] is None:
            # "il più possibile": nessun versamento "necessario" da calcolare — si proietta
            # il solo capitale assegnato (eventuali versamenti liberi sono una scelta, non un obbligo)
            g["pmt"] = 0.0
        else:
            # lo stesso versamento del foglio (colonna I), col de-risking dei terminanti
            target_nom = g["target_oggi"] * (1 + inflazione) ** g["orizzonte"]
            g["pmt"] = max(0.0, pmt_glide(target_nom, g["gia"], rend, rend_l, g["orizzonte"], finestra, CURVATURA))
        # proiezione capitale fino a orizzonte_max:
        #  - fino alla scadenza: cresce al rendimento atteso dell'anno (glide path) + 12 versamenti
        #    mensili capitalizzati nell'anno
        #  - oltre la scadenza: TERMINANTE = irrilevante (esce); PERMANENTE = tenuto costante (riserva piena)
        cap = [g["gia"]]
        for t in range(1, orizzonte_max + 1):
            if t <= g["orizzonte"]:
                r = tassi[t - 1]
                versati = 12.0 if r == 0 else r / ((1 + r) ** (1 / 12) - 1)
                cap.append(cap[-1] * (1 + r) + g["pmt"] * versati)
            else:
                cap.append(cap[-1] if g["permanente"] else 0.0)
        g["cap"] = cap

    print("=" * 78)
    print("GLIDE PATH — CALENDARIO DI DE-RISKING")
    print("=" * 78)
    print(f"Finestra de-risking: {finestra} anni  |  Atterraggio: {pct(ATTERRAGGIO_AZ)} azionario alla scadenza")
    print(f"Inflazione: {numero(inflazione*100, 1)}%")
    print("-" * 78)

    # intestazione tabella per-obiettivo
    nomi = [g["nome"] + (" (P)" if g["permanente"] else "") + (" (max)" if g["target_oggi"] is None else "")
            for g in obiettivi]
    intest = "Anno  " + "  ".join(f"{n[:16]:>16}" for n in nomi) + "   |  PORTAFOGLIO"
    print("\nQUOTA AZIONARIA TARGET per obiettivo e aggregata (per anno).  (P) = permanente\n")
    print(intest)
    print("-" * len(intest))

    calendario = {g["nome"]: [] for g in obiettivi}   # quota azionaria per anno (None = concluso)
    aggregato = []
    for t in range(orizzonte_max + 1):
        celle = []
        num = 0.0   # capitale azionario aggregato
        den = 0.0   # capitale totale aggregato
        for g in obiettivi:
            attivo = (t <= g["orizzonte"]) or g["permanente"]
            if not attivo:
                celle.append(f"{'concl.':>16}")
                calendario[g["nome"]].append(None)
                continue
            if g["permanente"]:
                # nessun glide: una riserva permanente tiene la quota del profilo (non ha scadenza di spesa)
                eqt = g["eq_start"]
                etich = pct(eqt) + (" (piena)" if t == g["orizzonte"] else "")
            else:
                ar = g["orizzonte"] - t
                eqt = equity_glide(ar, g["eq_start"], g["finestra"], ATTERRAGGIO_AZ)
                etich = pct(eqt)
            celle.append(f"{etich:>16}")
            calendario[g["nome"]].append(round(eqt, 4))
            capt = g["cap"][t]
            num += capt * eqt
            den += capt
        agg = (num / den) if den > 0 else 0.0
        aggregato.append(round(agg, 4))
        riga = f"{t:>4}  " + "  ".join(celle) + f"   |  {pct(agg):>10}"
        print(riga)

    # i versamenti su cui poggia la proiezione: gli stessi del foglio e del Monte Carlo
    print("\n" + "-" * 78)
    if scarti:
        print(f"VERSAMENTI usati nella proiezione, DIVERSI dalla colonna I del foglio ({'; '.join(scarti)}):")
    else:
        print("VERSAMENTI usati nella proiezione (come la colonna I del foglio, de-risking compreso):")
    for g in obiettivi:
        quanto = "— (nessun target)" if g["target_oggi"] is None else f"{euro(g['pmt'])}/mese"
        print(f"  {g['nome']}: {quanto}")

    # transizioni chiave dell'aggregato
    print("\n" + "-" * 78)
    print("LETTURA:")
    print("- Ogni colonna obiettivo è il target che it-rebalance mantiene per QUEL secchiello.")
    print("- La colonna PORTAFOGLIO è l'allocazione azionaria complessiva attesa anno per anno,")
    print("  pesata per il capitale proiettato di ogni obiettivo ancora attivo.")
    print("- 'concl.' = obiettivo TERMINANTE arrivato a scadenza (si spende → esce dal portafoglio).")
    print("- (P) = obiettivo PERMANENTE: NON de-riska (tiene la quota del profilo) e NON esce a scadenza")
    print("  (è una riserva, es. fondo emergenza). '(piena)' = anno in cui è pienamente finanziato.")
    print("  Restando in portafoglio, smussa l'aggregato invece di farlo saltare.")
    print("- (max) = obiettivo SENZA target («il più possibile»): si proietta il solo capitale")
    print("  assegnato; nessun versamento 'necessario' viene calcolato. Se terminante, de-riska")
    print("  e a scadenza si spende come gli altri; se permanente, resta e non de-riska mai.")
    print("\nNON è consulenza di investimento. Proiezione al rendimento atteso di ogni anno lungo")
    print("il glide path (non modella la volatilità). Le % azionario per profilo e i parametri")
    print("del glide path sono editabili (la finestra anche nel foglio, Parametri!B7). Vedi glide-path.md.")

    if args.json:
        scrivi_json(args.json, {
            "finestra": finestra, "atterraggio": ATTERRAGGIO_AZ, "curvatura": CURVATURA,
            "inflazione": inflazione, "scarti_dal_foglio": scarti,
            "anni": list(range(orizzonte_max + 1)),
            "portafoglio": aggregato,          # quota azionaria aggregata per anno
            "obiettivi": [{"nome": g["nome"], "profilo": g["profilo"], "orizzonte": g["orizzonte"],
                           "permanente": g["permanente"], "target_oggi": g["target_oggi"],
                           "gia": g["gia"], "versamento_mensile": round(g["pmt"], 2),
                           "quota_azionaria": calendario[g["nome"]],
                           "capitale_proiettato": [round(c, 2) for c in g["cap"]]} for g in obiettivi],
        })


if __name__ == "__main__":
    main()
