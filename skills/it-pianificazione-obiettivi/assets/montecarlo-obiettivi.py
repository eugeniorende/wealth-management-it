#!/usr/bin/env python3
"""
Monte Carlo per il pianificatore obiettivi.

Legge gli obiettivi e i parametri da pianificatore-obiettivi.xlsx e, per ciascun
obiettivo, simula migliaia di percorsi di accumulo con rendimenti annui casuali
(media = rendimento del profilo, deviazione standard = volatilità del profilo).
Restituisce, per ogni obiettivo:
  - la probabilità di raggiungere il target con il versamento deterministico
  - la distribuzione del capitale finale (10°, 50°, 90° percentile)
  - il versamento mensile che servirebbe per una confidenza-obiettivo (default 85%)

Il punto: il versamento "deterministico" del foglio Excel centra la MEDIA, quindi
dà tipicamente ~50% di probabilità di successo. Per avere più confidenza serve
versare di più (o ridurre il rischio, o allungare l'orizzonte). Il Monte Carlo
rende esplicito questo che il calcolo deterministico nasconde.

Dipendenze: numpy, openpyxl  (pip install numpy openpyxl)
Uso:        python montecarlo-obiettivi.py [percorso/pianificatore-obiettivi.xlsx]

NON è consulenza di investimento. I rendimenti e le volatilità sono ipotesi con
ampia variabilità; il modello assume rendimenti normali i.i.d. (vedi monte-carlo.md
per i limiti). I risultati sono ordini di grandezza per ragionare sul rischio, non
garanzie.

Nota: se il capitale già accantonato sovra-finanzia un obiettivo alla media (il
versamento deterministico risulterebbe negativo), lo script NON simula prelievi:
azzera il versamento e riporta la probabilità con €0/mese (la domanda giusta è
"il capitale esistente basta da solo?", non "quanto posso prelevare?").
"""

import sys
import os
import numpy as np
from openpyxl import load_workbook

from motore_bootstrap import applica_override, carica_storico, indici_bootstrap, blocchi_bootstrap, verifica_intestazioni_obiettivi

# ---- Parametri della simulazione ----
N_SIM = 20000              # numero di percorsi simulati
CONFIDENZA_TARGET = 0.85   # livello di confidenza per il calcolo del versamento "robusto"
SEED = 42                  # per risultati riproducibili (rimuovere per casualità piena)

# Leva di rischio: a versamento BLOCCATO, alzare la quota azionaria può alzare la probabilità?
# È la "seconda strada" quando non si può versare di più. NON è un pasto gratis: più rischio
# alza la mediana ma allarga la distribuzione, e il caso brutto (10°pct) può PEGGIORARE. Per
# questo si mostra la distribuzione intera, non solo la probabilità, e si segnala quando la leva
# è controproducente (obiettivo già in linea) o inadatta: obiettivo non desiderabile (essenziale o
# importante) oppure dentro la finestra di de-risking, dove il glide path abbassa la quota azionaria.
LEVA_RISCHIO    = True
SOGLIA_ONTRACK  = 0.75     # prob col profilo attuale ≥ questa ⇒ alzare il rischio è controproducente
FINESTRA_DERISK = 7        # come glidepath-obiettivi.py: entro questi anni dalla scadenza il rischio scende

# ---- Modello dei rendimenti ----
MODELLO = "normale"        # "normale" (Normale i.i.d.) | "bootstrap" (ricampiona da serie storica reale)
FILE_STORICO = "rendimenti-storici.csv"  # serie annuale azionario/obbligazionario (stessa cartella)
BLOCCO_BOOTSTRAP = 5       # lunghezza blocco (anni consecutivi) nel bootstrap: preserva la sequenza
RICENTRA_MEDIA = True      # ricentra la media storica sul rendimento atteso del profilo
                           # (calibra la MEDIA sull'ipotesi del profilo, mantiene FORMA/volatilità/code reali)

_AZ_HIST = None            # caricati a runtime se MODELLO == "bootstrap"
_OB_HIST = None

# Posizioni note nel foglio (coerenti con build_obiettivi.py)
CAP_ROW = 5                # Parametri!B5 = capacità di risparmio mensile
INFL_ROW = 6               # Parametri!B6 = inflazione
PROF_START = 10            # Parametri!A10:C14 = profili (nome, rendimento, volatilità)
PROF_N = 6
GOAL_START = 5             # Obiettivi: prima riga dati
GOAL_N = 10


def leggi_excel(path):
    wb = load_workbook(path, data_only=True)
    verifica_intestazioni_obiettivi(wb["Obiettivi"])
    par = wb["Parametri"]
    obj = wb["Obiettivi"]

    capacita = par.cell(row=CAP_ROW, column=2).value or 0
    inflazione = par.cell(row=INFL_ROW, column=2).value or 0

    profili = {}
    for i in range(PROF_N):
        r = PROF_START + i
        nome = par.cell(row=r, column=1).value
        rend = par.cell(row=r, column=2).value
        vol = par.cell(row=r, column=3).value
        peso = par.cell(row=r, column=4).value   # % azionario (per il bootstrap)
        if nome:
            profili[nome] = (float(rend), float(vol), float(peso) if peso is not None else 0.0)

    obiettivi = []
    for i in range(GOAL_N):
        r = GOAL_START + i
        nome = obj.cell(row=r, column=1).value
        imp = obj.cell(row=r, column=2).value
        oriz = obj.cell(row=r, column=3).value
        prof = obj.cell(row=r, column=4).value
        gia = obj.cell(row=r, column=6).value
        prio = obj.cell(row=r, column=7).value
        if nome and imp and oriz and prof:
            obiettivi.append({
                "nome": nome,
                "target_oggi": float(imp),
                "orizzonte": int(oriz),
                "profilo": prof,
                "gia": float(gia) if gia else 0.0,
                "priorita": prio or "",
            })
    return capacita, inflazione, profili, obiettivi


def pmt_deterministico(target_nom, gia, rend_ann, anni):
    """Versamento mensile del foglio Excel (valore futuro di una rendita, ramo per r=0)."""
    n = anni
    if rend_ann == 0:
        return (target_nom - gia) / (n * 12)
    fattore = (((1 + rend_ann) ** n) - 1) / ((1 + rend_ann) ** (1 / 12) - 1)
    return (target_nom - gia * (1 + rend_ann) ** n) / fattore


def simula_bootstrap(gia, pmt_mensile, rend_ann, peso_az, anni, n_sim=N_SIM):
    """Percorsi annuali via block bootstrap dalla serie storica reale, per il peso azionario dato.
    Se RICENTRA_MEDIA, la media storica è riportata al rendimento atteso del profilo
    (si calibra la media, si mantengono volatilità, asimmetria e code reali)."""
    port = peso_az * _AZ_HIST + (1.0 - peso_az) * _OB_HIST     # serie storica del portafoglio
    if RICENTRA_MEDIA:
        port = port - port.mean() + rend_ann
    rendimenti = blocchi_bootstrap(port, n_sim, anni, BLOCCO_BOOTSTRAP)
    saldi = np.full(n_sim, gia, dtype=float)
    for y in range(anni):
        R = rendimenti[:, y]
        # contributi mensili approssimati a metà anno (≈ mezzo anno di rendimento medio)
        saldi = saldi * (1 + R) + 12 * pmt_mensile * np.sqrt(np.maximum(1 + R, 1e-4))
    return saldi


def simula(target_nom, gia, pmt_mensile, rend_ann, vol_ann, anni, peso_az=0.0, n_sim=N_SIM):
    """Simula n_sim percorsi. Restituisce array dei capitali finali.
    MODELLO='normale': passi mensili, rendimenti Normali i.i.d.
    MODELLO='bootstrap': passi annuali, ricampionati dalla serie storica reale."""
    if MODELLO == "bootstrap" and _AZ_HIST is not None:
        return simula_bootstrap(gia, pmt_mensile, rend_ann, peso_az, anni, n_sim)
    mesi = anni * 12
    mu_m = (1 + rend_ann) ** (1 / 12) - 1          # media mensile (geometrica)
    sigma_m = vol_ann / np.sqrt(12)                 # volatilità mensile (scaling sqrt-tempo)
    saldi = np.full(n_sim, gia, dtype=float)
    for _ in range(mesi):
        r = np.random.normal(mu_m, sigma_m, n_sim)
        saldi = saldi * (1 + r) + pmt_mensile
    return saldi


def prob_successo(target_nom, gia, pmt_mensile, rend_ann, vol_ann, anni, peso_az=0.0, n_sim=N_SIM):
    finali = simula(target_nom, gia, pmt_mensile, rend_ann, vol_ann, anni, peso_az, n_sim)
    return float(np.mean(finali >= target_nom)), finali


def pmt_per_confidenza(target_nom, gia, rend_ann, vol_ann, anni, conf, pmt_det, peso_az=0.0):
    """Cerca (bisezione) il versamento mensile che dà la probabilità di successo = conf."""
    lo, hi = 0.0, max(pmt_det * 4, 50.0)
    # garantisci che hi sia sufficiente
    for _ in range(20):
        p_hi, _ = prob_successo(target_nom, gia, hi, rend_ann, vol_ann, anni, peso_az, n_sim=4000)
        if p_hi >= conf:
            break
        hi *= 1.5
    for _ in range(22):
        mid = (lo + hi) / 2
        p, _ = prob_successo(target_nom, gia, mid, rend_ann, vol_ann, anni, peso_az, n_sim=4000)
        if p < conf:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def interp_profilo(w, profili):
    """Interpola (rendimento, volatilità) per una quota azionaria arbitraria w dai profili.
    Lineare tra i profili; oltre il più aggressivo, estrapola con la pendenza dell'ultimo segmento."""
    pts = sorted(profili.values(), key=lambda p: p[2])    # (rend, vol, peso_az) per peso crescente
    pesi = [p[2] for p in pts]; rends = [p[0] for p in pts]; vols = [p[1] for p in pts]
    if w <= pesi[0]:
        return rends[0], vols[0]
    if w >= pesi[-1]:
        if pesi[-1] == pesi[-2]:
            return rends[-1], vols[-1]
        fr = (rends[-1] - rends[-2]) / (pesi[-1] - pesi[-2])
        fv = (vols[-1] - vols[-2]) / (pesi[-1] - pesi[-2])
        return rends[-1] + fr * (w - pesi[-1]), max(0.0, vols[-1] + fv * (w - pesi[-1]))
    for i in range(1, len(pesi)):
        if w <= pesi[i]:
            t = (w - pesi[i-1]) / (pesi[i] - pesi[i-1])
            return rends[i-1] + t*(rends[i]-rends[i-1]), vols[i-1] + t*(vols[i]-vols[i-1])
    return rends[-1], vols[-1]


def nome_profilo_vicino(w, profili):
    return min(profili.items(), key=lambda kv: abs(kv[1][2] - w))[0]


def leva_di_rischio(target_nom, gia, pmt_fisso, anni, peso_attuale, profili, n_sim=6000):
    """A versamento BLOCCATO, fa lo sweep della quota azionaria dalla attuale verso l'alto.
    Per ogni livello calcola probabilità e distribuzione (P10/P50/P90). Ritorna la lista dei
    risultati e l'indice del massimo di probabilità — così si vede sia se la prob sale, sia il
    prezzo sul caso brutto (volutamente NON si guarda solo la probabilità)."""
    pesi_max = max(p[2] for p in profili.values())
    hi = min(1.0, max(pesi_max, peso_attuale))
    griglia = sorted({round(peso_attuale + k * 0.05, 2) for k in range(0, 21)} | {round(pesi_max, 2)})
    griglia = [w for w in griglia if peso_attuale - 1e-9 <= w <= hi + 1e-9]
    if not griglia:
        griglia = [peso_attuale]
    ris = []
    for w in griglia:
        rend, vol = interp_profilo(w, profili)
        p, finali = prob_successo(target_nom, gia, pmt_fisso, rend, vol, anni, w, n_sim)
        p10, p50, p90 = np.percentile(finali, [10, 50, 90])
        ris.append((w, rend, vol, p, p10, p50, p90))
    i_best = max(range(len(ris)), key=lambda i: ris[i][3])
    return ris, i_best


def simula_congiunta(obiettivi_def, n_sim=N_SIM):
    """Simula TUTTI gli obiettivi con un UNICO percorso di mercato per simulazione (fattore
    condiviso): un crollo li colpisce insieme. Gli obiettivi con orizzonti diversi condividono
    gli anni iniziali del percorso. Ritorna le maschere di successo (n_sim,) per obiettivo, da
    cui calcolare le probabilità CONGIUNTE. Richiede il modello bootstrap."""
    max_anni = max(o["anni"] for o in obiettivi_def)
    # matrice CONDIVISA di indici storici (n_sim, max_anni): stessa estrazione di anni
    # per tutti gli obiettivi → shock di mercato comuni (vedi motore_bootstrap)
    idx = indici_bootstrap(len(_AZ_HIST), n_sim, max_anni, BLOCCO_BOOTSTRAP)
    maschere = {}
    for o in obiettivi_def:
        peso, rend, anni = o["peso_az"], o["rend"], o["anni"]
        port_full = peso * _AZ_HIST + (1.0 - peso) * _OB_HIST
        shift = (-port_full.mean() + rend) if RICENTRA_MEDIA else 0.0
        saldi = np.full(n_sim, o["gia"], dtype=float)
        for y in range(anni):
            R = port_full[idx[:, y]] + shift     # stesso anno storico per tutti → correlazione
            saldi = saldi * (1 + R) + 12 * o["pmt"] * np.sqrt(np.maximum(1 + R, 1e-4))
        maschere[o["nome"]] = saldi >= o["target_nom"]
    return maschere


def euro(x):
    return f"€{x:,.0f}".replace(",", ".")


def main():
    applica_override(globals())
    if SEED is not None:
        np.random.seed(SEED)

    # percorso xlsx
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, "pianificatore-obiettivi.xlsx")
    if not os.path.exists(path):
        print(f"File non trovato: {path}")
        print("Uso: python montecarlo-obiettivi.py [percorso/pianificatore-obiettivi.xlsx]")
        sys.exit(1)

    capacita, inflazione, profili, obiettivi = leggi_excel(path)

    # carica la serie storica se il modello è bootstrap
    global _AZ_HIST, _OB_HIST
    if MODELLO == "bootstrap":
        here = os.path.dirname(os.path.abspath(__file__))
        csv_path = FILE_STORICO if os.path.isabs(FILE_STORICO) else os.path.join(here, FILE_STORICO)
        if not os.path.exists(csv_path):
            print(f"⚠️  MODELLO='bootstrap' ma serie storica non trovata: {csv_path}")
            print("    Reimposto MODELLO='normale'.")
            globals()["MODELLO"] = "normale"
        else:
            _AZ_HIST, _OB_HIST = carica_storico(csv_path)

    print("=" * 78)
    print("MONTE CARLO — PIANIFICATORE OBIETTIVI")
    print("=" * 78)
    print(f"Simulazioni per obiettivo: {N_SIM:,}".replace(",", "."))
    print(f"Capacità di risparmio: {euro(capacita)}/mese  |  Inflazione: {inflazione*100:.1f}%")
    print(f"Confidenza-obiettivo per il versamento robusto: {CONFIDENZA_TARGET*100:.0f}%")
    if MODELLO == "bootstrap":
        ric = "media ricentrata sul profilo" if RICENTRA_MEDIA else "media storica grezza"
        print(f"Modello rendimenti: BOOTSTRAP storico ({len(_AZ_HIST)} anni, blocchi da {BLOCCO_BOOTSTRAP}, {ric})")
    else:
        print(f"Modello rendimenti: Normale i.i.d.")
    print("-" * 78)

    totale_pmt_det = 0.0
    totale_pmt_conf = 0.0
    obiettivi_def = []   # raccolti per la simulazione congiunta (rischio sistemico)

    for g in obiettivi:
        if g["profilo"] not in profili:
            print(f"\n⚠️  {g['nome']}: profilo '{g['profilo']}' non in tabella. Salto.")
            continue
        rend, vol, peso_az = profili[g["profilo"]]
        target_nom = g["target_oggi"] * (1 + inflazione) ** g["orizzonte"]
        pmt_det_raw = pmt_deterministico(target_nom, g["gia"], rend, g["orizzonte"])
        # Un versamento negativo significa che il capitale esistente sovra-finanzia
        # l'obiettivo ALLA MEDIA: non si "preleva" per raggiungere un obiettivo, si versa 0.
        sovra_finanziato = pmt_det_raw < 0
        pmt_det = max(0.0, pmt_det_raw)
        p_succ, finali = prob_successo(target_nom, g["gia"], pmt_det, rend, vol, g["orizzonte"], peso_az)
        p10, p50, p90 = np.percentile(finali, [10, 50, 90])
        pmt_conf = pmt_per_confidenza(target_nom, g["gia"], rend, vol, g["orizzonte"], CONFIDENZA_TARGET, max(pmt_det, 50.0), peso_az)

        totale_pmt_det += pmt_det
        totale_pmt_conf += pmt_conf
        obiettivi_def.append({
            "nome": g["nome"], "gia": g["gia"], "pmt": pmt_det, "target_nom": target_nom,
            "anni": g["orizzonte"], "peso_az": peso_az, "rend": rend, "priorita": g["priorita"],
        })

        print(f"\n▸ {g['nome']}  [{g['profilo']}, {g['orizzonte']} anni, priorità: {g['priorita']}]")
        print(f"    Target nominale (con inflazione):   {euro(target_nom)}")
        print(f"    Rendimento {rend*100:.1f}% · volatilità {vol*100:.1f}%")
        if sovra_finanziato:
            print(f"    Versamento necessario:              €0/mese  (capitale esistente già sufficiente ALLA MEDIA)")
        else:
            print(f"    Versamento deterministico:          {euro(pmt_det)}/mese")
        print(f"    → Probabilità di successo con questo versamento: {p_succ*100:.0f}%")
        print(f"    Capitale finale simulato:")
        print(f"        pessimistico (10°pct):          {euro(p10)}")
        print(f"        mediano      (50°pct):          {euro(p50)}")
        print(f"        ottimistico  (90°pct):          {euro(p90)}")
        print(f"    Versamento per {CONFIDENZA_TARGET*100:.0f}% di confidenza:    {euro(pmt_conf)}/mese"
              f"  ({'+' if pmt_conf>=pmt_det else ''}{euro(pmt_conf - pmt_det)} vs sopra)")

        # ── Seconda strada: alzare il rischio invece del versamento (a versamento bloccato) ──
        if LEVA_RISCHIO:
            essenziale = "essenz" in g["priorita"].lower()
            desiderabile = any(k in g["priorita"].lower() for k in ("desider", "discrez"))
            breve = g["orizzonte"] <= FINESTRA_DERISK
            ontrack = p_succ >= SOGLIA_ONTRACK
            print(f"    — Seconda strada: alzare il rischio invece di versare di più (versamento fermo a {euro(pmt_det)}/mese) —")
            if essenziale:
                print(f"        INADATTA per un obiettivo essenziale: più rischio allarga proprio la coda")
                print(f"        sinistra, e mancare un essenziale non è un'opzione. Meglio versare di più o ridurre il target.")
            elif not desiderabile:
                print(f"        INADATTA per un obiettivo «{g['priorita']}»: la leva di rischio è un'opzione solo per")
                print(f"        gli obiettivi desiderabili. Meglio versare di più, allungare l'orizzonte o ridurre il target.")
            elif breve:
                print(f"        INADATTA su orizzonte di {g['orizzonte']} anni: entro la finestra di de-risking")
                print(f"        ({FINESTRA_DERISK} anni) la quota azionaria deve scendere verso la scadenza, non salire.")
            elif ontrack:
                print(f"        CONTROPRODUCENTE: sei già in linea (prob {p_succ*100:.0f}%). Alzare il rischio")
                print(f"        aggiunge un downside che non ti serve — quando hai (quasi) vinto, non rilanci.")
            else:
                ris, ib = leva_di_rischio(target_nom, g["gia"], pmt_det, g["orizzonte"], peso_az, profili)
                wb, rb, vb, pb, p10b, p50b, p90b = ris[ib]
                if wb > peso_az + 1e-6 and pb > p_succ + 0.03:
                    peggiora = p10b < p10 - 1
                    print(f"        OPZIONE: portando la quota azionaria a ~{wb*100:.0f}% (≈ {nome_profilo_vicino(wb, profili)}),")
                    print(f"        la probabilità sale dal {p_succ*100:.0f}% al {pb*100:.0f}% SENZA versare di più.")
                    print(f"        Ma il prezzo è sul caso brutto: il 10°pct va da {euro(p10)} a {euro(p10b)} "
                          f"({'PEGGIORA' if peggiora else 'tiene'}).")
                    print(f"        È un rilancio: più probabilità di centrare il target, worst case "
                          f"{'più severo' if peggiora else 'simile'}. Ha senso solo se reggi quel downside.")
                else:
                    print(f"        Non aiuta: anche alzando il rischio la probabilità non sale in modo")
                    print(f"        significativo (oltre una certa quota il volatility drag la riabbassa).")

    print("\n" + "=" * 78)
    print("RIEPILOGO")
    print("-" * 78)
    print(f"Totale versamenti deterministici (~50% confidenza ciascuno): {euro(totale_pmt_det)}/mese")
    print(f"Totale versamenti per {CONFIDENZA_TARGET*100:.0f}% di confidenza ciascuno:        {euro(totale_pmt_conf)}/mese")
    print(f"Capacità di risparmio disponibile:                          {euro(capacita)}/mese")
    if totale_pmt_conf > capacita:
        print(f"\n⚠️  Per avere {CONFIDENZA_TARGET*100:.0f}% di confidenza su TUTTI gli obiettivi servirebbero "
              f"{euro(totale_pmt_conf - capacita)}/mese in più della capacità.")
        print("    Leve: dare priorità (alta confidenza solo sugli essenziali), allungare gli orizzonti,")
        print("    ridurre i target discrezionali, o accettare confidenza più bassa sugli obiettivi non critici.")
    else:
        print(f"\n✓  La capacità copre anche i versamenti per {CONFIDENZA_TARGET*100:.0f}% di confidenza su tutti.")

    print("\n" + "-" * 78)
    print("Nota: il versamento deterministico centra la MEDIA → ~50% di probabilità.")
    print("Per gli obiettivi essenziali (es. fondo emergenza) si vuole confidenza alta,")
    print("quindi un versamento più alto del deterministico. Vedi monte-carlo.md.")
    print("NON è consulenza di investimento.")
    if MODELLO == "bootstrap":
        print("Modello: BOOTSTRAP a blocchi da serie storica reale (code grasse e correlazioni")
        print("azionario/obbligazionario reali). Media calibrata sul profilo; il passato non")
        print("predice il futuro. Limiti e metodologia in monte-carlo.md.")
    else:
        print("Modello a rendimenti normali i.i.d., con i limiti descritti in monte-carlo.md")
        print("(no code grasse, no correlazioni). Per code più realistiche: MODELLO='bootstrap'.")

    # ---- Rischio sistemico: gli obiettivi NON sono indipendenti ----
    if len(obiettivi_def) >= 2:
        if MODELLO != "bootstrap":
            print("\n" + "-" * 78)
            print("RISCHIO SISTEMICO: l'analisi congiunta richiede MODELLO='bootstrap' (un unico")
            print("percorso di mercato condiviso tra obiettivi). Imposta il bootstrap per vederla.")
        else:
            essenziali = [o for o in obiettivi_def if "essenz" in o["priorita"].lower()]
            if len(essenziali) >= 2:
                usati, etichetta = essenziali, "essenziali"
            else:
                usati = obiettivi_def
                etichetta = "tutti gli obiettivi" + (" (un solo essenziale)" if essenziali else "")
            maschere = simula_congiunta(usati)
            M = np.array([maschere[o["nome"]] for o in usati])    # (k, n_sim) bool
            margin = M.mean(axis=1)
            all_succ_ind = float(np.prod(margin))
            all_succ_cor = float(np.all(M, axis=0).mean())
            all_fail_ind = float(np.prod(1 - margin))
            all_fail_cor = float(np.all(~M, axis=0).mean())
            print("\n" + "=" * 78)
            print("RISCHIO SISTEMICO — gli obiettivi condividono lo stesso mercato")
            print("-" * 78)
            print(f"Obiettivi considerati ({etichetta}): {', '.join(o['nome'] for o in usati)}")
            print("Un crollo li colpisce INSIEME: trattarli come indipendenti falsa le code congiunte.")
            print(f"\n  P(TUTTI falliscono nello STESSO scenario) — la coda che conta per la resilienza:")
            print(f"      indipendenti (prodotto):           {all_fail_ind*100:5.1f}%   ← ipotesi ingenua")
            print(f"      mercato condiviso (congiunta):     {all_fail_cor*100:5.1f}%   ← realistico")
            direzione = "SOTTOSTIMA" if all_fail_cor > all_fail_ind else "sovrastima"
            print(f"      → l'indipendenza {direzione} di {abs(all_fail_cor-all_fail_ind)*100:.1f} punti il rischio che salti tutto insieme.")
            print(f"\n  P(TUTTI riescono insieme):")
            print(f"      indipendenti (prodotto):           {all_succ_ind*100:5.1f}%")
            print(f"      mercato condiviso (congiunta):     {all_succ_cor*100:5.1f}%")
            print("\n  Le probabilità SINGOLE non cambiano; ma non ci si diversifica TRA obiettivi che")
            print("  condividono il mercato (l'effetto cresce se condividono esposizione azionaria).")
            print("  Per questo il fondo emergenza e gli essenziali vanno coperti per primi.")
            print("  Dettagli in mercati-e-correlazione.md.")


if __name__ == "__main__":
    main()
