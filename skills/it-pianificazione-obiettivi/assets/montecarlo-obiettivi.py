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

Convenzioni, le stesse del foglio:
  - il rendimento del profilo è NETTO di costi e imposte ed è la media ARITMETICA
    annua attesa: la crescita composta mediana è circa rendimento − volatilità²/2;
  - gli obiettivi TERMINANTI seguono il glide path (GLIDE = True): quota del profilo
    finché mancano più di FINESTRA_DERISK anni, poi discesa fino all'atterraggio, anno
    per anno come in glidepath-obiettivi.py. Il versamento deterministico è quello del
    foglio (colonna I), che tiene conto del de-risking, finché finestra, atterraggio e
    curvatura sono quelli del foglio (Parametri!B7, profilo a quota azionaria minima, rampa
    lineare): cambiandoli, o su un pianificatore precedente alla 0.10.0, diverge e lo script
    lo dice. I permanenti non de-riskano.

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

from motore_bootstrap import (blocchi_bootstrap, carica_storico, cli, euro, frazioni_glide, indici_bootstrap,
                              leggi_pianificatore, numero, pmt_glide, scarti_dal_foglio)

# ---- Parametri della simulazione ----
N_SIM = 20000              # numero di percorsi simulati
CONFIDENZA_TARGET = 0.85   # livello di confidenza per il calcolo del versamento "robusto"
SEED = 42                  # per risultati riproducibili (rimuovere per casualità piena)

# Glide path: gli obiettivi terminanti de-riskano verso la scadenza, come nel calendario di
# glidepath-obiettivi.py che it-rebalance esegue. Vale nel versamento e nella simulazione.
GLIDE           = True     # False: quota fissa del profilo fino alla scadenza (versamento e simulazione)
FINESTRA_DERISK = None     # None = dal foglio (Parametri!B7, 7 anni nell'esempio): entro questi anni
                           # dalla scadenza la quota azionaria scende
ATTERRAGGIO_AZ  = 0.00     # quota azionaria alla scadenza (0% = profilo Preservazione), come il glide path
CURVATURA       = 1.0      # forma della rampa (1 = lineare, come il foglio)

# Leva di rischio: a versamento BLOCCATO, alzare la quota azionaria può alzare la probabilità?
# È la "seconda strada" quando non si può versare di più. NON è un pasto gratis: più rischio
# alza la mediana ma allarga la distribuzione, e il caso brutto (10°pct) può PEGGIORARE. Per
# questo si mostra la distribuzione intera, non solo la probabilità, e si segnala quando la leva
# è controproducente (obiettivo già in linea) o inadatta: obiettivo non desiderabile (essenziale o
# importante) oppure dentro la finestra di de-risking, dove il glide path abbassa la quota azionaria.
# Accanto all'OPZIONE si mostrano sia il percorso glide sia la quota fissa fino alla scadenza.
LEVA_RISCHIO    = True
SOGLIA_ONTRACK  = 0.75     # prob col profilo attuale ≥ questa ⇒ alzare il rischio è controproducente

# ---- Modello dei rendimenti ----
MODELLO = "normale"        # "normale" (Normale i.i.d.) | "bootstrap" (ricampiona dalla serie storica)
FILE_STORICO = "rendimenti-storici.csv"  # S&P 500 e T-Bond USA, nominali in dollari (stessa cartella)
BLOCCO_BOOTSTRAP = 5       # lunghezza blocco (anni consecutivi) nel bootstrap: preserva la sequenza
RICENTRA_MEDIA = True      # ricentra la media storica sul rendimento atteso del profilo
                           # (calibra la MEDIA sull'ipotesi del profilo, mantiene FORMA/volatilità/code
                           # della storia: per questo una serie nominale in dollari va bene qui)

_AZ_HIST = None            # caricati a runtime se MODELLO == "bootstrap"
_OB_HIST = None

# Posizioni note nel foglio (coerenti con build_obiettivi.py)


def leggi_excel(path):
    """Parametri, profili (rendimento, volatilità, % azionario) e obiettivi dal lettore unico del motore.
    Il Monte Carlo ha bisogno di un importo: gli obiettivi senza target restano fuori, e lo dice."""
    d = leggi_pianificatore(path)
    profili = {n: (p["rendimento"], p["volatilita"], p["azionario"]) for n, p in d["profili"].items()}
    obiettivi = []
    for g in d["obiettivi"]:
        if g["target_oggi"] is None:
            print(f"⚠️  {g['nome']}: senza importo target («il più possibile») non si simula una probabilità "
                  f"di successo: escluso. Lo tratta glidepath-obiettivi.py.")
            continue
        obiettivi.append(g)
    return d["capacita"], d["inflazione"], d["finestra"], d["finestra_nel_foglio"], profili, obiettivi


def pmt_deterministico(target_nom, gia, rend_ann, anni):
    """Versamento mensile a quota fissa (valore futuro di una rendita, ramo per r=0): è la
    colonna I del foglio per gli obiettivi che non de-riskano; col glide path vale pmt_glide."""
    n = anni
    if rend_ann == 0:
        return (target_nom - gia) / (n * 12)
    fattore = (((1 + rend_ann) ** n) - 1) / ((1 + rend_ann) ** (1 / 12) - 1)
    return (target_nom - gia * (1 + rend_ann) ** n) / fattore


def percorso_glide(rend_ann, vol_ann, anni, glide):
    """Rendimento atteso e volatilità di ciascun anno. glide = (frazioni, rend_atterraggio,
    vol_atterraggio) oppure None (quota fissa). Durante la rampa il secchiello è una miscela
    del portafoglio del profilo e di quello di atterraggio: entrambi lineari nella frazione."""
    if glide is None:
        return np.full(anni, rend_ann), np.full(anni, vol_ann)
    frazioni, rend_l, vol_l = glide
    return rend_l + (rend_ann - rend_l) * frazioni, vol_l + (vol_ann - vol_l) * frazioni


def simula_bootstrap(gia, pmt_mensile, rend_ann, peso_az, anni, n_sim=N_SIM, glide=None):
    """Percorsi annuali via block bootstrap dalla serie storica, per il peso azionario dato.
    Se RICENTRA_MEDIA, la media storica è riportata al rendimento atteso del profilo
    (si calibra la media, si mantengono volatilità, asimmetria e code della storia).
    Col glide path la parte de-riskata rende il rendimento (certo) dell'atterraggio."""
    port = peso_az * _AZ_HIST + (1.0 - peso_az) * _OB_HIST     # serie storica del portafoglio
    if RICENTRA_MEDIA:
        port = port - port.mean() + rend_ann
    rendimenti = blocchi_bootstrap(port, n_sim, anni, BLOCCO_BOOTSTRAP)
    if glide is not None:
        frazioni, rend_l, _ = glide
        rendimenti = frazioni * rendimenti + (1.0 - frazioni) * rend_l
    saldi = np.full(n_sim, gia, dtype=float)
    for y in range(anni):
        R = rendimenti[:, y]
        # contributi mensili approssimati a metà anno (≈ mezzo anno di rendimento medio)
        saldi = saldi * (1 + R) + 12 * pmt_mensile * np.sqrt(np.maximum(1 + R, 1e-4))
    return saldi


def simula(target_nom, gia, pmt_mensile, rend_ann, vol_ann, anni, peso_az=0.0, n_sim=N_SIM, glide=None):
    """Simula n_sim percorsi. Restituisce array dei capitali finali.
    MODELLO='normale': passi mensili, rendimenti Normali i.i.d.
    MODELLO='bootstrap': passi annuali, ricampionati dalla serie storica.
    glide: vedi percorso_glide (None = quota fissa fino alla scadenza)."""
    if MODELLO == "bootstrap" and _AZ_HIST is not None:
        return simula_bootstrap(gia, pmt_mensile, rend_ann, peso_az, anni, n_sim, glide)
    medie, vols = percorso_glide(rend_ann, vol_ann, anni, glide)
    saldi = np.full(n_sim, gia, dtype=float)
    for y in range(anni):
        # media mensile tale che il rendimento annuo ATTESO (media aritmetica) sia quello
        # dell'anno: (1 + mu_m)^12 = 1 + rendimento. La mediana composta resta sotto (σ²/2).
        mu_m = (1 + medie[y]) ** (1 / 12) - 1
        sigma_m = vols[y] / np.sqrt(12)             # volatilità mensile (scaling sqrt-tempo)
        for _ in range(12):
            r = np.random.normal(mu_m, sigma_m, n_sim)
            saldi = saldi * (1 + r) + pmt_mensile
    return saldi


def prob_successo(target_nom, gia, pmt_mensile, rend_ann, vol_ann, anni, peso_az=0.0, n_sim=N_SIM,
                  glide=None):
    finali = simula(target_nom, gia, pmt_mensile, rend_ann, vol_ann, anni, peso_az, n_sim, glide)
    return float(np.mean(finali >= target_nom)), finali


def pmt_per_confidenza(target_nom, gia, rend_ann, vol_ann, anni, conf, pmt_det, peso_az=0.0, glide=None):
    """Cerca (bisezione) il versamento mensile che dà la probabilità di successo = conf."""
    lo, hi = 0.0, max(pmt_det * 4, 50.0)
    # garantisci che hi sia sufficiente
    for _ in range(20):
        p_hi, _ = prob_successo(target_nom, gia, hi, rend_ann, vol_ann, anni, peso_az, 4000, glide)
        if p_hi >= conf:
            break
        hi *= 1.5
    for _ in range(22):
        mid = (lo + hi) / 2
        p, _ = prob_successo(target_nom, gia, mid, rend_ann, vol_ann, anni, peso_az, 4000, glide)
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


def glide_per_quota(w, glide):
    """Il glide path vale solo per quote sopra l'atterraggio (come quota_glide del motore)."""
    return glide if glide is not None and w > ATTERRAGGIO_AZ + 1e-9 else None


def leva_di_rischio(target_nom, gia, pmt_fisso, anni, peso_attuale, profili, n_sim=6000, glide=None):
    """A versamento BLOCCATO, fa lo sweep della quota azionaria (di partenza, se c'è il glide
    path) dalla attuale verso l'alto. Per ogni livello calcola probabilità e distribuzione
    (P10/P50/P90). Ritorna la lista dei risultati e l'indice del massimo di probabilità — così
    si vede sia se la prob sale, sia il prezzo sul caso brutto (volutamente NON si guarda solo
    la probabilità)."""
    pesi_max = max(p[2] for p in profili.values())
    hi = min(1.0, max(pesi_max, peso_attuale))
    griglia = sorted({round(peso_attuale + k * 0.05, 2) for k in range(0, 21)} | {round(pesi_max, 2)})
    griglia = [w for w in griglia if peso_attuale - 1e-9 <= w <= hi + 1e-9]
    if not griglia:
        griglia = [peso_attuale]
    ris = []
    for w in griglia:
        rend, vol = interp_profilo(w, profili)
        p, finali = prob_successo(target_nom, gia, pmt_fisso, rend, vol, anni, w, n_sim,
                                  glide_per_quota(w, glide))
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
            if o["glide"] is not None:           # lo stesso glide path della simulazione singola
                frazioni, rend_l, _ = o["glide"]
                R = frazioni[y] * R + (1.0 - frazioni[y]) * rend_l
            saldi = saldi * (1 + R) + 12 * o["pmt"] * np.sqrt(np.maximum(1 + R, 1e-4))
        maschere[o["nome"]] = saldi >= o["target_nom"]
    return maschere


def main():
    args = cli("Monte Carlo degli obiettivi: probabilità di successo, percentili del capitale finale e versamento "
               "per la confidenza-obiettivo, dal pianificatore compilato.", globals(), argomenti=(
                   (("excel",), {"nargs": "?", "help": "pianificatore-obiettivi.xlsx compilato (default: il modello del plugin)"}),))
    if SEED is not None:
        np.random.seed(SEED)
    path = args.excel or os.path.join(os.path.dirname(os.path.abspath(__file__)), "pianificatore-obiettivi.xlsx")
    capacita, inflazione, finestra_foglio, nel_foglio, profili, obiettivi = leggi_excel(path)
    finestra = finestra_foglio if FINESTRA_DERISK is None else int(FINESTRA_DERISK)
    rend_l, vol_l = interp_profilo(ATTERRAGGIO_AZ, profili)    # il portafoglio di atterraggio
    scarti = scarti_dal_foglio(finestra, finestra_foglio if nel_foglio else None, ATTERRAGGIO_AZ,
                               min(p[2] for p in profili.values()), CURVATURA)

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
    print(f"Simulazioni per obiettivo: {numero(N_SIM)}")
    print(f"Capacità di risparmio: {euro(capacita)}/mese  |  Inflazione: {numero(inflazione*100, 1)}%")
    print(f"Confidenza-obiettivo per il versamento robusto: {numero(CONFIDENZA_TARGET*100)}%")
    if MODELLO == "bootstrap":
        ric = "media ricentrata sul profilo" if RICENTRA_MEDIA else "media storica grezza"
        print(f"Modello rendimenti: BOOTSTRAP storico ({len(_AZ_HIST)} anni, blocchi da {BLOCCO_BOOTSTRAP}, {ric})")
    else:
        print(f"Modello rendimenti: Normale i.i.d.")
    if GLIDE:
        print(f"Glide path: i terminanti de-riskano da {finestra} anni prima della scadenza fino a "
              f"{numero(ATTERRAGGIO_AZ*100)}% azionario (versamento e simulazione)")
        if scarti:
            print(f"⚠️  Glide path diverso da quello del foglio ({'; '.join(scarti)}): il versamento "
                  f"deterministico dei terminanti non è quello della colonna I.")
    else:
        print("Glide path: spento (GLIDE=False), quota fissa del profilo fino alla scadenza")
    print("-" * 78)

    totale_pmt_det = 0.0
    totale_pmt_conf = 0.0
    obiettivi_def = []   # raccolti per la simulazione congiunta (rischio sistemico)

    for g in obiettivi:
        rend, vol, peso_az = profili[g["profilo"]]     # il lettore ha già respinto i profili ignoti
        anni = g["orizzonte"]
        target_nom = g["target_oggi"] * (1 + inflazione) ** anni
        # il glide path del piano: solo per i terminanti con quota sopra l'atterraggio
        de_risk = not g["permanente"] and peso_az > ATTERRAGGIO_AZ + 1e-9
        glide_piano = (frazioni_glide(anni, finestra, CURVATURA), rend_l, vol_l) if de_risk else None
        glide = glide_piano if GLIDE else None
        if glide is not None:
            pmt_det_raw = pmt_glide(target_nom, g["gia"], rend, rend_l, anni, finestra, CURVATURA)
        else:
            pmt_det_raw = pmt_deterministico(target_nom, g["gia"], rend, anni)
        # Un versamento negativo significa che il capitale esistente sovra-finanzia
        # l'obiettivo ALLA MEDIA: non si "preleva" per raggiungere un obiettivo, si versa 0.
        sovra_finanziato = pmt_det_raw < 0
        pmt_det = max(0.0, pmt_det_raw)
        p_succ, finali = prob_successo(target_nom, g["gia"], pmt_det, rend, vol, anni, peso_az, N_SIM, glide)
        p10, p50, p90 = np.percentile(finali, [10, 50, 90])
        pmt_conf = pmt_per_confidenza(target_nom, g["gia"], rend, vol, anni, CONFIDENZA_TARGET,
                                      max(pmt_det, 50.0), peso_az, glide)

        totale_pmt_det += pmt_det
        totale_pmt_conf += pmt_conf
        obiettivi_def.append({
            "nome": g["nome"], "gia": g["gia"], "pmt": pmt_det, "target_nom": target_nom,
            "anni": anni, "peso_az": peso_az, "rend": rend, "priorita": g["priorita"],
            "glide": glide,
        })

        print(f"\n▸ {g['nome']}  [{g['profilo']}, {anni} anni, priorità: {g['priorita']}]")
        print(f"    Target nominale (con inflazione):   {euro(target_nom)}")
        print(f"    Rendimento {numero(rend*100, 1)}% · volatilità {numero(vol*100, 1)}%")
        if glide is not None:
            rampa = int(np.sum(glide[0] < 1.0))
            print(f"    Glide path: {numero(peso_az*100)}% azionario, ridotto ogni anno negli ultimi {rampa} anni "
                  f"fino a {numero(ATTERRAGGIO_AZ*100)}% alla scadenza")
        if sovra_finanziato:
            print(f"    Versamento necessario:              €0/mese  (capitale esistente già sufficiente ALLA MEDIA)")
        else:
            print(f"    Versamento deterministico:          {euro(pmt_det)}/mese")
        print(f"    → Probabilità di successo con questo versamento: {numero(p_succ*100)}%")
        print(f"    Capitale finale simulato:")
        print(f"        pessimistico (10°pct):          {euro(p10)}")
        print(f"        mediano      (50°pct):          {euro(p50)}")
        print(f"        ottimistico  (90°pct):          {euro(p90)}")
        print(f"    Versamento per {numero(CONFIDENZA_TARGET*100)}% di confidenza:    {euro(pmt_conf)}/mese"
              f"  ({'+' if pmt_conf>=pmt_det else ''}{euro(pmt_conf - pmt_det)} vs sopra)")

        # ── Seconda strada: alzare il rischio invece del versamento (a versamento bloccato) ──
        if LEVA_RISCHIO:
            essenziale = "essenz" in g["priorita"].lower()
            desiderabile = any(k in g["priorita"].lower() for k in ("desider", "discrez"))
            breve = anni <= finestra
            ontrack = p_succ >= SOGLIA_ONTRACK
            print(f"    — Seconda strada: alzare il rischio invece di versare di più (versamento fermo a {euro(pmt_det)}/mese) —")
            if essenziale:
                print(f"        INADATTA per un obiettivo essenziale: più rischio allarga proprio la coda")
                print(f"        sinistra, e mancare un essenziale non è un'opzione. Meglio versare di più o ridurre il target.")
            elif not desiderabile:
                print(f"        INADATTA per un obiettivo «{g['priorita']}»: la leva di rischio è un'opzione solo per")
                print(f"        gli obiettivi desiderabili. Meglio versare di più, allungare l'orizzonte o ridurre il target.")
            elif breve:
                print(f"        INADATTA su orizzonte di {anni} anni: entro la finestra di de-risking")
                print(f"        ({finestra} anni) la quota azionaria deve scendere verso la scadenza, non salire.")
            elif ontrack:
                print(f"        CONTROPRODUCENTE: sei già in linea (prob {numero(p_succ*100)}%). Alzare il rischio")
                print(f"        aggiunge un downside che non ti serve — quando hai (quasi) vinto, non rilanci.")
            else:
                ris, ib = leva_di_rischio(target_nom, g["gia"], pmt_det, anni, peso_az, profili, glide=glide)
                wb, rb, vb, pb, p10b, p50b, p90b = ris[ib]
                if wb > peso_az + 1e-6 and pb > p_succ + 0.03:
                    peggiora = p10b < p10 - 1
                    partenza = " di partenza" if de_risk else ""
                    print(f"        OPZIONE: portando la quota azionaria{partenza} a ~{numero(wb*100)}% "
                          f"(≈ {nome_profilo_vicino(wb, profili)}),")
                    if de_risk:
                        # F017: accanto all'OPZIONE i due percorsi, a parità di versamento. Conta il
                        # glide path, che è il piano che it-rebalance esegue.
                        altro = None if GLIDE else glide_piano
                        p_alt0, _ = prob_successo(target_nom, g["gia"], pmt_det, rend, vol, anni, peso_az,
                                                  6000, altro)
                        p_altb, _ = prob_successo(target_nom, g["gia"], pmt_det, rb, vb, anni, wb,
                                                  6000, glide_per_quota(wb, altro))
                        (pg0, pgb), (pf0, pfb) = (((p_succ, pb), (p_alt0, p_altb)) if GLIDE
                                                  else ((p_alt0, p_altb), (p_succ, pb)))
                        print(f"        la probabilità sale SENZA versare di più:")
                        print(f"          sul percorso glide (de-risking da {finestra} anni dalla scadenza): "
                              f"dal {numero(pg0*100)}% al {numero(pgb*100)}%")
                        print(f"          a quota fissa fino alla scadenza (senza de-risking):       "
                              f"dal {numero(pf0*100)}% al {numero(pfb*100)}%")
                        print(f"        Conta la prima riga: il glide path è il piano che it-rebalance esegue.")
                    else:
                        print(f"        la probabilità sale dal {numero(p_succ*100)}% al {numero(pb*100)}% SENZA versare di più.")
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
    print(f"Totale versamenti per {numero(CONFIDENZA_TARGET*100)}% di confidenza ciascuno:        {euro(totale_pmt_conf)}/mese")
    print(f"Capacità di risparmio disponibile:                          {euro(capacita)}/mese")
    if totale_pmt_conf > capacita:
        print(f"\n⚠️  Per avere {numero(CONFIDENZA_TARGET*100)}% di confidenza su TUTTI gli obiettivi servirebbero "
              f"{euro(totale_pmt_conf - capacita)}/mese in più della capacità.")
        print("    Leve: dare priorità (alta confidenza solo sugli essenziali), allungare gli orizzonti,")
        print("    ridurre i target discrezionali, o accettare confidenza più bassa sugli obiettivi non critici.")
    else:
        print(f"\n✓  La capacità copre anche i versamenti per {numero(CONFIDENZA_TARGET*100)}% di confidenza su tutti.")

    print("\n" + "-" * 78)
    print("Nota: il versamento deterministico centra la MEDIA del capitale finale → ~50% di probabilità.")
    print("Il rendimento del profilo è la media aritmetica annua attesa (netta di costi e imposte):")
    print("la crescita composta mediana è circa rendimento − volatilità²/2, per questo sugli orizzonti")
    print("lunghi e volatili la probabilità scende sotto il 50% (volatility drag).")
    print("Per gli obiettivi essenziali (es. fondo emergenza) si vuole confidenza alta,")
    print("quindi un versamento più alto del deterministico. Vedi monte-carlo.md.")
    print("NON è consulenza di investimento.")
    if MODELLO == "bootstrap":
        print("Modello: BOOTSTRAP a blocchi dalla serie storica USA (S&P 500 e T-Bond, nominali in")
        print("dollari): code grasse e correlazioni azionario/obbligazionario della storia. Media")
        print("calibrata sul profilo; il passato non predice il futuro. Limiti in monte-carlo.md.")
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
            print(f"      indipendenti (prodotto):           {numero(all_fail_ind*100, 1):>5}%   ← ipotesi ingenua")
            print(f"      mercato condiviso (congiunta):     {numero(all_fail_cor*100, 1):>5}%   ← realistico")
            direzione = "SOTTOSTIMA" if all_fail_cor > all_fail_ind else "sovrastima"
            print(f"      → l'indipendenza {direzione} di {abs(all_fail_cor-all_fail_ind)*100:.1f} punti il rischio che salti tutto insieme.")
            print(f"\n  P(TUTTI riescono insieme):")
            print(f"      indipendenti (prodotto):           {numero(all_succ_ind*100, 1):>5}%")
            print(f"      mercato condiviso (congiunta):     {numero(all_succ_cor*100, 1):>5}%")
            print("\n  Le probabilità SINGOLE non cambiano; ma non ci si diversifica TRA obiettivi che")
            print("  condividono il mercato (l'effetto cresce se condividono esposizione azionaria).")
            print("  Per questo il fondo emergenza e gli essenziali vanno coperti per primi.")
            print("  Dettagli in mercati-e-correlazione.md.")


if __name__ == "__main__":
    main()
