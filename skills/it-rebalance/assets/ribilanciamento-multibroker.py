#!/usr/bin/env python3
"""
ribilanciamento-multibroker.py — pianifica un ribilanciamento tax-aware quando il
portafoglio è diviso su PIÙ broker, dove ogni broker ha il proprio zainetto fiscale.

Due idee chiave, entrambe assenti nel ribilanciamento "ingenuo":

1. OTTIMIZZAZIONE GLOBALE DELLO ZAINETTO (multi-broker). In regime amministrato la
   compensazione minus/plus NON attraversa i broker: una minus al broker A compensa
   solo plus realizzate al broker A. Quindi NON conta solo COSA vendere (quale classe),
   ma DOVE venderlo: una plusvalenza va realizzata, quando possibile, presso il broker
   che ha zainetto capiente — e solo su strumenti "reddito diverso" (le plus su ETF
   armonizzati = reddito di capitale non sono mai compensabili).

2. BANDE DINAMICHE (alla Kitces). Non si ribilancia a calendario, ma quando il drift
   supera una soglia. La soglia segue la regola 5/25 (il minore tra 5 punti assoluti e
   25% relativi) e si ALLARGA quando correggere costa imposta netta: se la correzione
   è a costo netto zero (flussi, vendite di minus, o plus interamente compensate dallo
   zainetto) si agisce sulla banda stretta; se invece richiede di pagare imposta, si
   agisce solo oltre la banda allargata. Tradotto: non si paga imposta per correggere
   un drift troppo piccolo per contare.

Tutti i parametri sono editabili qui sotto. I valori di default sono un caso reale di
validazione (vedi il commento ATTESO in fondo). plus = plusvalenza/minusvalenza latente
in euro (negativo = minus). Approssimazione pro-rata sui realizzi parziali: il realizzo
effettivo dipende dalla stratificazione LIFO dei lotti (cfr. SKILL.md).

⚠️ Sui CSV: i broker italiani non hanno un formato standard di IMPORT ordini, quindi i file
generati sono una CHECKLIST DI ESECUZIONE e una traccia di audit (cosa vendere/comprare,
dove, con quale effetto fiscale), non ordini caricabili in un click. La colonna
`strumento_ISIN` è lasciata vuota da compilare: il piano ragiona per classe, sei tu a
scegliere lo strumento specifico (quale ETF/fondo) da movimentare.
"""

import csv
import os

# ─────────────────────────── INPUT (editabili) ───────────────────────────
POSITIONS = [
    {"broker": "Fineco",  "asset_class": "azionario",      "tipo": "capitale", "valore": 40000, "plus": 10000},
    {"broker": "Fineco",  "asset_class": "azionario",      "tipo": "diverso",  "valore": 10000, "plus":  4000},
    {"broker": "Fineco",  "asset_class": "obbligazionario","tipo": "capitale", "valore": 15000, "plus":  -500},
    {"broker": "Directa", "asset_class": "azionario",      "tipo": "capitale", "valore": 18000, "plus":  3000},
    {"broker": "Directa", "asset_class": "obbligazionario","tipo": "diverso",  "valore":  9000, "plus":     0},
    {"broker": "Directa", "asset_class": "monetario",      "tipo": "capitale", "valore":  8000, "plus":     0},
]
# minusvalenze compensabili disponibili per broker (lo zainetto è per-intermediario)
ZAINETTO = {"Fineco": 5000, "Directa": 0}
# allocazione target (somma = 1) — INPUT dell'utente, non scelta dallo strumento
TARGET = {"azionario": 0.60, "obbligazionario": 0.30, "monetario": 0.10}

NUOVI_VERSAMENTI = 0      # liquidità in entrata per la Leva 1 (€)
FLUSSI_ATTESI    = 0      # dividendi/cedole per la Leva 2 (€)
ALIQUOTA         = 0.26   # imposta sostitutiva sui redditi diversi (26%; cripto 33%)
BANDA_ASSOLUTA   = 0.05   # 5 punti percentuali
BANDA_RELATIVA   = 0.25   # 25% del peso target
WIDENING         = 2.0    # fattore di allargamento della banda per correzioni con imposta netta

# Modulazione della banda per la VOLATILITÀ della classe (rifinitura, vedi bande-dinamiche.md).
# Idea: una banda fissa rappresenta un "segnale vs rumore" diverso a seconda della volatilità —
# una classe volatile sfora una banda fissa più spesso solo per rumore. Scalare la banda con la
# volatilità rende la soglia un evento statisticamente più omogeneo (meno trade da rumore sulle
# classi volatili). ATTENZIONE alla tensione teorica: il controllo ottimo (Leland) dice l'opposto
# — una deviazione su un asset volatile è PIÙ rischiosa, quindi andrebbe tollerata MENO. Non è una
# legge: è un trade-off tra efficienza di trading e aderenza al target. Per questo i clamp sono
# stretti (effetto modesto) e MODULA_VOLATILITA si può spegnere per tornare alla pura 5/25.
MODULA_VOLATILITA = True
VOLATILITA = {            # volatilità annua REALE per classe (illustrativa: impostare sui propri comparti)
    "azionario": 0.16,
    "obbligazionario": 0.06,
    "monetario": 0.005,
}
VOL_RIFERIMENTO = 0.12    # volatilità di riferimento attorno cui la 5/25 è "calibrata"
BETA_VOL        = 1.0     # esponente: 1.0 = soglia statistica (banda ∝ deriva attesa ∝ σ)
VOL_FATTORE_MIN = 0.7     # clamp inferiore del fattore (le classi stabili non si stringono oltre)
VOL_FATTORE_MAX = 1.6     # clamp superiore del fattore (le classi volatili non si allargano oltre)

GENERA_CSV        = True       # genera i file CSV degli ordini, uno per broker
CARTELLA_OUTPUT   = "ordini"   # cartella dove scrivere i CSV (creata se assente)
BROKER_VERSAMENTI = "Fineco"   # broker su cui atterrano versamenti/flussi in entrata (per l'instradamento cassa)
# ──────────────────────────────────────────────────────────────────────────


def aggrega(positions):
    classi = {}
    for p in positions:
        classi.setdefault(p["asset_class"], 0)
        classi[p["asset_class"]] += p["valore"]
    return classi


def fattore_volatilita(asset_class):
    """Fattore di modulazione della banda per la volatilità della classe, clampato.
    1.0 se la modulazione è spenta o la volatilità non è nota (retro-compatibile con la pura 5/25)."""
    if not MODULA_VOLATILITA:
        return 1.0
    sigma = VOLATILITA.get(asset_class)
    if sigma is None or VOL_RIFERIMENTO <= 0:
        return 1.0
    f = (sigma / VOL_RIFERIMENTO) ** BETA_VOL
    return max(VOL_FATTORE_MIN, min(VOL_FATTORE_MAX, f))


def banda(target_w, asset_class=None):
    """Banda di tolleranza: 5/25 (minore tra 5pp e 25% del target), modulata per la volatilità
    della classe (clampata), poi la versione allargata cost-aware (× WIDENING)."""
    base = min(BANDA_ASSOLUTA, BANDA_RELATIVA * target_w)
    tight = base * fattore_volatilita(asset_class)
    return tight, tight * WIDENING


def pianifica():
    total = sum(p["valore"] for p in POSITIONS)
    classi = aggrega(POSITIONS)
    zain = dict(ZAINETTO)   # zainetto mutabile per broker (lo consumiamo man mano)

    # 1) drift e decisione di banda
    drift = {}
    for cl, tw in TARGET.items():
        w = classi.get(cl, 0) / total
        tight, wide = banda(tw, cl)
        drift[cl] = {"peso": w, "target": tw, "drift": w - tw,
                     "gap_eur": (w - tw) * total, "tight": tight, "wide": wide,
                     "fuori_banda": abs(w - tw) > tight}

    buys = {cl: 0.0 for cl in TARGET}   # acquisti per classe
    sells = []                          # vendite dettagliate
    tax_tot = 0.0

    # 2) LEVA 1 + 2 (costo zero): flussi verso le sottopesate fuori banda
    cassa_in = NUOVI_VERSAMENTI + FLUSSI_ATTESI
    sotto = {cl: -d["gap_eur"] for cl, d in drift.items() if d["gap_eur"] < 0 and d["fuori_banda"]}
    tot_sotto = sum(sotto.values())
    if cassa_in > 0 and tot_sotto > 0:
        for cl, need in sotto.items():
            quota = min(need, cassa_in * need / tot_sotto)
            buys[cl] += quota

    # ricalcolo dei gap residui dopo gli acquisti da flussi
    def gap_residuo(cl):
        nuovo_val = classi.get(cl, 0) + buys[cl]
        return nuovo_val - TARGET[cl] * total

    # 3) vendite per le SOVRAPPESATE fuori banda
    for cl, d in drift.items():
        if gap_residuo(cl) <= 0 or not d["fuori_banda"]:
            continue
        da_ridurre = gap_residuo(cl)  # porto a target

        # candidati alla vendita in questa classe
        pos = [p for p in POSITIONS if p["asset_class"] == cl]
        # LEVA 3: prima le posizioni in MINUS (costo zero/negativo)
        minus = sorted([p for p in pos if p["plus"] < 0], key=lambda x: x["plus"])
        # LEVA 4: posizioni in PLUS, ordinate per ottimizzazione fiscale:
        #   (a) compensabili (diverso) presso broker con zainetto, poi (b) plus latente minore
        plus = sorted([p for p in pos if p["plus"] > 0], key=lambda p: (
            0 if (p["tipo"] == "diverso" and zain.get(p["broker"], 0) > 0) else 1,
            p["plus"] / max(p["valore"], 1)))

        for p in minus + plus:
            if da_ridurre <= 1e-6:
                break
            vendi = min(da_ridurre, p["valore"])
            plus_real = vendi * (p["plus"] / p["valore"]) if p["valore"] else 0
            comp = 0.0
            tassa = 0.0
            if plus_real > 0:
                if p["tipo"] == "diverso":
                    comp = min(plus_real, zain.get(p["broker"], 0))
                tassabile = plus_real - comp
                tassa = tassabile * ALIQUOTA
                # BANDA DINAMICA: una vendita che genera imposta netta si fa solo
                # se il drift della classe supera la banda allargata
                if tassa > 1e-6 and abs(d["drift"]) <= d["wide"]:
                    continue  # drift insufficiente a giustificare l'imposta: salta
            # esegui la vendita
            if comp > 0:
                zain[p["broker"]] -= comp
            tax_tot += tassa
            da_ridurre -= vendi
            sells.append({"broker": p["broker"], "classe": cl, "tipo": p["tipo"],
                          "vendi": vendi, "plus_real": plus_real, "comp": comp, "tassa": tassa})

        # se resta da ridurre ma solo con vendite tassate sotto banda allargata, segnalo
        drift[cl]["residuo_non_corretto"] = max(0.0, da_ridurre)

    # 4) reimpiego della cassa generata dalle vendite verso le sottopesate (anche in banda)
    cassa_da_vendite = sum(s["vendi"] for s in sells)
    # prima le sottopesate fuori banda non ancora coperte, poi quelle in banda fino a target
    ordine = sorted(TARGET, key=lambda cl: gap_residuo(cl))  # più negative prima
    for cl in ordine:
        if cassa_da_vendite <= 1e-6:
            break
        manca = -gap_residuo(cl)
        if manca <= 0:
            continue
        q = min(manca, cassa_da_vendite)
        buys[cl] += q
        cassa_da_vendite -= q

    # allocazione risultante
    risultante = {}
    for cl in TARGET:
        venduto_cl = sum(s["vendi"] for s in sells if s["classe"] == cl)
        risultante[cl] = (classi.get(cl, 0) + buys[cl] - venduto_cl) / total

    return total, drift, buys, sells, tax_tot, zain, risultante


CAMPI_CSV = ["broker", "operazione", "classe", "tipo_fiscale", "strumento_ISIN",
             "importo_eur", "plus_minus_eur", "imposta_eur", "compensazione_zainetto_eur", "nota"]
# Ultima riga di ogni CSV: chi apre il file vede il disclaimer, e l'intestazione resta la prima riga.
NOTA_CSV = ("Checklist educativa generata da ribilanciamento-multibroker.py: non costituisce consulenza "
            "di investimento né un ordine. Verificare saldi, lotti e zainetto sul portale del broker "
            "prima di operare.")


def genera_ordini(plan):
    """Trasforma il piano in una lista di ordini ESEGUIBILI per broker, instradando la cassa.
    Le vendite sono già specifiche per broker (con l'effetto fiscale). Gli acquisti vengono
    finanziati dalla liquidità presente su ciascun broker (le vendite lì realizzate + eventuali
    versamenti che vi atterrano), così ogni broker resta a saldo e gli ordini sono eseguibili
    senza trasferimenti di cassa tra intermediari (che richiederebbero giorni)."""
    total, drift, buys, sells, tax_tot, zain, risultante = plan
    ordini = []

    # VENDITE — già per broker, con annotazione fiscale
    for s in sells:
        if s["plus_real"] > 0 and s["comp"] > 0:
            nota = f"riduce sovrappeso {s['classe']}; plus €{s['plus_real']:,.0f} compensata con zainetto {s['broker']}"
        elif s["plus_real"] > 0:
            nota = f"riduce sovrappeso {s['classe']}; plus €{s['plus_real']:,.0f} TASSATA (no zainetto compensabile qui)"
        elif s["plus_real"] < 0:
            nota = f"riduce sovrappeso {s['classe']}; minus €{-s['plus_real']:,.0f} a zainetto {s['broker']}"
        else:
            nota = f"riduce sovrappeso {s['classe']}"
        ordini.append({"broker": s["broker"], "operazione": "VENDITA", "classe": s["classe"],
                       "tipo_fiscale": s["tipo"], "importo_eur": round(s["vendi"], 2),
                       "plus_minus_eur": round(s["plus_real"], 2), "imposta_eur": round(s["tassa"], 2),
                       "compensazione_zainetto_eur": round(s["comp"], 2), "nota": nota})

    # cassa disponibile per broker = vendite realizzate lì (+ versamenti/flussi sul broker designato)
    cassa = {}
    for s in sells:
        cassa[s["broker"]] = cassa.get(s["broker"], 0.0) + s["vendi"]
    entrate = NUOVI_VERSAMENTI + FLUSSI_ATTESI
    if entrate > 0:
        cassa[BROKER_VERSAMENTI] = cassa.get(BROKER_VERSAMENTI, 0.0) + entrate

    # ACQUISTI — instradati sui broker che hanno cassa (greedy: prima chi ne ha di più)
    for cl, amt in buys.items():
        if amt <= 1e-6:
            continue
        rimanente = amt
        for broker in sorted(cassa, key=lambda b: -cassa[b]):
            if rimanente <= 1e-6:
                break
            quota = min(rimanente, cassa[broker])
            if quota <= 1e-6:
                continue
            ordini.append({"broker": broker, "operazione": "ACQUISTO", "classe": cl,
                           "tipo_fiscale": "", "importo_eur": round(quota, 2), "plus_minus_eur": "",
                           "imposta_eur": "", "compensazione_zainetto_eur": "",
                           "nota": f"riempie sottopeso {cl}"})
            cassa[broker] -= quota
            rimanente -= quota
        if rimanente > 1e-6:   # cassa insufficiente ovunque: serve un versamento/trasferimento
            ordini.append({"broker": "(da finanziare)", "operazione": "ACQUISTO", "classe": cl,
                           "tipo_fiscale": "", "importo_eur": round(rimanente, 2), "plus_minus_eur": "",
                           "imposta_eur": "", "compensazione_zainetto_eur": "",
                           "nota": f"riempie sottopeso {cl} — cassa insufficiente, richiede versamento o trasferimento"})
    return ordini


def scrivi_csv_per_broker(ordini, cartella=None):
    """Scrive un CSV per broker nella cartella indicata. Ritorna la lista (path, n_righe)."""
    cartella = cartella or CARTELLA_OUTPUT
    os.makedirs(cartella, exist_ok=True)
    scritti = []
    for b in sorted({o["broker"] for o in ordini}):
        righe = [o for o in ordini if o["broker"] == b]
        slug = "".join(c if c.isalnum() else "_" for c in b)
        path = os.path.join(cartella, f"ordini_{slug}.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CAMPI_CSV, extrasaction="ignore")
            w.writeheader()
            for o in righe:
                row = dict(o)
                row.setdefault("strumento_ISIN", "")   # colonna da compilare a mano
                w.writerow(row)
            w.writerow({"broker": b, "operazione": "NOTA", "nota": NOTA_CSV})
        scritti.append((path, len(righe)))
    return scritti


def stampa(plan):
    total, drift, buys, sells, tax_tot, zain, risultante = plan
    print(f"\n{'='*70}\nRIBILANCIAMENTO MULTI-BROKER  —  patrimonio €{total:,.0f}\n{'='*70}")

    print(f"\n1) DRIFT E BANDE DINAMICHE (regola 5/25, allargamento ×{WIDENING:g} se l'imposta morde)")
    print(f"{'Classe':<18}{'Peso':>8}{'Target':>8}{'Drift':>8}{'B.stretta':>11}{'B.larga':>10}  Decisione")
    for cl, d in drift.items():
        dec = "in banda — non agire"
        if d["fuori_banda"]:
            dec = "FUORI banda — ribilanciare"
        print(f"{cl:<18}{d['peso']*100:>7.1f}%{d['target']*100:>7.0f}%{d['drift']*100:>+7.1f}%"
              f"{d['tight']*100:>10.1f}%{d['wide']*100:>9.1f}%  {dec}")

    print(f"\n2) PIANO — vendite (ottimizzate per broker e tipo fiscale)")
    if not sells:
        print("   nessuna vendita necessaria (corretto con i soli flussi)")
    for s in sells:
        nota = ""
        if s["comp"] > 0:
            nota = f"  → plus €{s['plus_real']:,.0f} compensata €{s['comp']:,.0f} dallo zainetto {s['broker']}"
        elif s["plus_real"] > 0:
            nota = f"  → plus €{s['plus_real']:,.0f} TASSATA (no zainetto compensabile qui)"
        elif s["plus_real"] < 0:
            nota = f"  → minus €{-s['plus_real']:,.0f} a zainetto {s['broker']}"
        print(f"   VENDI €{s['vendi']:,.0f} {s['classe']}/{s['tipo']} @ {s['broker']}"
              f"  | imposta €{s['tassa']:,.0f}{nota}")

    print(f"\n   acquisti (riempimento sottopesate; broker a scelta, neutro ai fini fiscali)")
    for cl, q in buys.items():
        if q > 1e-6:
            print(f"   COMPRA €{q:,.0f} {cl}")

    print(f"\n3) COSTO FISCALE TOTALE: €{tax_tot:,.0f}")
    print(f"   zainetto residuo per broker: " +
          ", ".join(f"{b} €{v:,.0f}" for b, v in zain.items()))

    print(f"\n4) ALLOCAZIONE RISULTANTE vs TARGET")
    for cl in TARGET:
        print(f"   {cl:<18}{risultante[cl]*100:>6.1f}%  (target {TARGET[cl]*100:.0f}%)")
    print()


def main():
    plan = pianifica()
    stampa(plan)
    if GENERA_CSV:
        esporta_ordini(plan)
    print("   Questo strumento è educativo e non costituisce consulenza di investimento o fiscale:")
    print("   l'allocazione target è tua; saldi, lotti e zainetto vanno verificati sul portale del broker.")
    print()


def esporta_ordini(plan):
    ordini = genera_ordini(plan)
    scritti = scrivi_csv_per_broker(ordini)
    print(f"5) ORDINI ESPORTATI — un CSV per broker in ./{CARTELLA_OUTPUT}/")
    for path, n in scritti:
        print(f"   {path}  ({n} ordini)")
    # anteprima leggibile
    print(f"\n   Anteprima:")
    print(f"   {'broker':<14}{'op.':<9}{'classe':<16}{'tipo':<10}{'importo':>10}  nota")
    for o in ordini:
        imp = f"€{o['importo_eur']:,.0f}"
        print(f"   {o['broker']:<14}{o['operazione']:<9}{o['classe']:<16}{str(o['tipo_fiscale']):<10}{imp:>10}  {o['nota']}")
    print(f"\n   I broker italiani non importano ordini da CSV: questi file sono una checklist di")
    print(f"   esecuzione e una traccia. Compila la colonna strumento_ISIN con lo strumento scelto.")
    print()


if __name__ == "__main__":
    main()

# ─────────────────────────── ATTESO (validazione) ───────────────────────────
# Caso di default: azionario 68% (target 60%, FUORI banda), obblig 24% (target 30%,
# FUORI banda), monetario 8% (target 10%, drift -2% < banda stretta 2,5% → IN banda).
# La riduzione di €8k di azionario si fa al COSTO NETTO ZERO vendendo la posizione
# "diverso" presso Fineco (l'unica con plus compensabile, e Fineco ha €5k di zainetto):
#   vendi €8.000 azionario/diverso @ Fineco → plus pro-rata €3.200, compensata €3.200,
#   imposta €0; zainetto Fineco 5.000 → 1.800.
# Acquisti: €6.000 obbligazionario + €2.000 monetario (la cassa residua porta il
# monetario a target come effetto collaterale).
# COSTO FISCALE TOTALE atteso: €0.  Allocazione risultante: 60% / 30% / 10%.
# Nota: vendere invece l'ETF capitale (plus non compensabile) sarebbe costato imposta;
# è esattamente ciò che la doppia ottimizzazione (broker + tipo) evita.
