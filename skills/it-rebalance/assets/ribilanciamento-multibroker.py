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

3. REGOLA DI RIENTRO MISTA (OBIETTIVO_RIENTRO = "misto"): a target se la correzione è a
   costo netto zero, fino a metà della banda stretta (MARGINE_RIENTRO) per la parte che
   paga imposta. Lo script stampa i due costi, a target e in banda.

Flussi: i versamenti e i flussi in entrata entrano nel totale prima di misurare il drift
(una classe sovrappesata oggi può essere sottopesata dopo un versamento) e vengono allocati
tutti; il PRELIEVO in decumulo esce dal totale, si finanzia con vendite (imposta compresa)
e non si reinveste. Le minus realizzate ricaricano lo zainetto del broker per le vendite
successive; ogni posizione ha la sua aliquota (26%, o 12,5% per titoli di Stato e
equiparati, che compensano lo zainetto al 48,08%).

Tutti i parametri sono editabili qui sotto. I valori di default sono un caso reale di
validazione (vedi il commento ATTESO in fondo). plus = plusvalenza/minusvalenza latente
in euro (negativo = minus). Realizzi parziali pro-rata: in amministrato è il calcolo esatto,
perché la plus si determina sul costo medio ponderato
(art. 6 c. 4 D.Lgs. 461/97 → art. 306 c. 5 TU 2027); il LIFO vale solo in dichiarativo,
fuori dallo scope (cfr. SKILL.md).

⚠️ Sui CSV: i broker italiani non hanno un formato standard di IMPORT ordini, quindi i file
generati sono una CHECKLIST DI ESECUZIONE e una traccia di audit (cosa vendere/comprare,
dove, con quale effetto fiscale), non ordini caricabili in un click. La colonna
`strumento_ISIN` è lasciata vuota da compilare: il piano ragiona per classe, sei tu a
scegliere lo strumento specifico (quale ETF/fondo) da movimentare.
"""

import csv
import os

# ─────────────────────────── INPUT (editabili) ───────────────────────────
# Per posizione: broker, asset_class (una delle chiavi di TARGET), tipo ("diverso" o
# "capitale"), valore e plus in euro, e se serve "aliquota" (0.26 di default; 0.125 per
# titoli di Stato italiani e white list, enti territoriali e organismi internazionali).
POSITIONS = [
    {"broker": "Fineco",  "asset_class": "azionario",      "tipo": "capitale", "valore": 40000, "plus": 10000},
    {"broker": "Fineco",  "asset_class": "azionario",      "tipo": "diverso",  "valore": 10000, "plus":  4000},
    {"broker": "Fineco",  "asset_class": "obbligazionario","tipo": "capitale", "valore": 15000, "plus":  -500},
    {"broker": "Directa", "asset_class": "azionario",      "tipo": "capitale", "valore": 18000, "plus":  3000},
    {"broker": "Directa", "asset_class": "obbligazionario","tipo": "diverso",  "valore":  9000, "plus":     0},
    {"broker": "Directa", "asset_class": "monetario",      "tipo": "capitale", "valore":  8000, "plus":     0},
]
# minusvalenze compensabili disponibili per broker (lo zainetto è per-intermediario), in euro
# di minus al 26%. Quale quota scade quest'anno lo dice it-tax-optimization (importatore).
ZAINETTO = {"Fineco": 5000, "Directa": 0}
# allocazione target (somma = 1) — INPUT dell'utente, non scelta dallo strumento
TARGET = {"azionario": 0.60, "obbligazionario": 0.30, "monetario": 0.10}

NUOVI_VERSAMENTI = 0      # liquidità in entrata per la Leva 1 (€)
FLUSSI_ATTESI    = 0      # dividendi/cedole per la Leva 2 (€)
PRELIEVO         = 0      # decumulo: euro netti da prelevare (le vendite coprono anche l'imposta)
ALIQUOTA         = 0.26   # aliquota di default delle posizioni senza campo "aliquota"
BANDA_ASSOLUTA   = 0.05   # 5 punti percentuali
BANDA_RELATIVA   = 0.25   # 25% del peso target
WIDENING         = 2.0    # fattore di allargamento della banda per correzioni con imposta netta
OBIETTIVO_RIENTRO = "misto"  # "misto": a target se costa zero, a metà banda se tassato; "target"; "banda"
MARGINE_RIENTRO   = 0.5      # quota della banda stretta lasciata come margine nel rientro «in banda»

# Modulazione della banda per la VOLATILITÀ della classe (rifinitura, vedi bande-dinamiche.md).
# Idea: una banda fissa rappresenta un "segnale vs rumore" diverso a seconda della volatilità —
# una classe volatile sfora una banda fissa più spesso solo per rumore. Scalare la banda con la
# volatilità rende la soglia un evento statisticamente più omogeneo (meno trade da rumore sulle
# classi volatili). ATTENZIONE alla tensione teorica: il controllo ottimo (Leland) dice l'opposto
# — una deviazione su un asset volatile è PIÙ rischiosa, quindi andrebbe tollerata MENO. Non è una
# legge: è un trade-off tra efficienza di trading e aderenza al target. Per questo i clamp sono
# stretti (effetto modesto) e la modulazione è spenta di default: la regola canonica è la pura
# 5/25, la stessa dei fogli (IPS, tracker, cruscotto). Accenderla è una scelta dell'utente.
MODULA_VOLATILITA = False
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


K_12_5 = 12.5 / 26     # coefficiente 48,08%: una plus o minus al 12,5% vale così nello zainetto


class ErroreInput(Exception):
    """Parametri in testa al file non validi: messaggio leggibile, uscita con codice 2."""


def valida():
    """Validazione minima dell'input (in attesa dell'interfaccia comune degli script)."""
    if abs(sum(TARGET.values()) - 1) > 1e-6:
        raise ErroreInput(f"TARGET somma a {sum(TARGET.values()):.4f}, non a 1")
    for n, p in enumerate(POSITIONS, start=1):
        if p.get("asset_class") not in TARGET:
            raise ErroreInput(f"posizione {n}: classe «{p.get('asset_class')}» assente da TARGET")
        if p.get("tipo") not in ("diverso", "capitale"):
            raise ErroreInput(f"posizione {n}: tipo «{p.get('tipo')}» (attesi «diverso» o «capitale»)")
        if p.get("aliquota", ALIQUOTA) not in (0.26, 0.125):
            raise ErroreInput(f"posizione {n}: aliquota {p.get('aliquota')} (attese 0.26 o 0.125)")
        if p.get("valore", -1) < 0:
            raise ErroreInput(f"posizione {n}: valore negativo o mancante")
    if OBIETTIVO_RIENTRO not in ("misto", "target", "banda"):
        raise ErroreInput(f"OBIETTIVO_RIENTRO «{OBIETTIVO_RIENTRO}» (attesi misto, target, banda)")
    if min(PRELIEVO, NUOVI_VERSAMENTI, FLUSSI_ATTESI) < 0:
        raise ErroreInput("PRELIEVO, NUOVI_VERSAMENTI e FLUSSI_ATTESI vanno indicati come importi positivi")


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


def _aliquota(p):
    return p.get("aliquota", ALIQUOTA)


def _coeff(p):
    """Peso nello zainetto (in minus al 26%) di un euro di plus o minus della posizione."""
    return K_12_5 if _aliquota(p) == 0.125 else 1.0


def effetto_vendita(p, vendi, zain):
    """(plus realizzata, compensazione in euro di plus, imposta, variazione dello zainetto) di una
    vendita di `vendi` euro della posizione, sul costo medio (pro-rata). Non modifica nulla."""
    plus_real = vendi * p["plus"] / p["valore"] if p["valore"] else 0.0
    if plus_real < 0:       # la minus (anche di un ETF) è reddito diverso: ricarica lo zainetto
        return plus_real, 0.0, 0.0, -plus_real * _coeff(p)
    comp = 0.0
    if plus_real > 0 and p["tipo"] == "diverso":
        comp = min(plus_real, zain.get(p["broker"], 0.0) / _coeff(p))
    return plus_real, comp, (plus_real - comp) * _aliquota(p), -comp * _coeff(p)


def quota_costo_zero(p, zain, residuo):
    """Euro vendibili della posizione senza pagare imposta: tutta se in minus o senza plus,
    la parte coperta dallo zainetto del broker se è reddito diverso in plus, zero altrimenti."""
    if p["plus"] <= 0:
        return residuo
    if p["tipo"] != "diverso":
        return 0.0
    rapporto = p["plus"] / p["valore"]
    return min(residuo, zain.get(p["broker"], 0.0) / (_coeff(p) * rapporto))


def pianifica():
    """Piano di ribilanciamento: dict con drift per classe, vendite, acquisti, imposta, zainetto
    residuo, allocazione risultante e prelievo. Vedi il docstring del modulo per le regole."""
    valida()
    total = sum(p["valore"] for p in POSITIONS)
    cassa_in = NUOVI_VERSAMENTI + FLUSSI_ATTESI
    total_post = total + cassa_in - PRELIEVO      # il patrimonio su cui misurare pesi e gap
    if total_post <= 0:
        raise ErroreInput("il prelievo supera il patrimonio più i versamenti")
    classi = aggrega(POSITIONS)
    zain = {b: float(v) for b, v in ZAINETTO.items()}   # zainetto mutabile per broker
    residuo = [float(p["valore"]) for p in POSITIONS]   # controvalore non ancora venduto
    sells = []

    # 1) drift e decisione di banda, sul patrimonio dopo flussi e prelievo
    drift = {}
    for cl, tw in TARGET.items():
        w = classi.get(cl, 0) / total_post
        tight, wide = banda(tw, cl)
        drift[cl] = {"peso": w, "target": tw, "drift": w - tw, "gap_eur": (w - tw) * total_post,
                     "tight": tight, "wide": wide, "fuori_banda": abs(w - tw) > tight,
                     "residuo_non_corretto": 0.0, "motivo": "", "costo_a_target": 0.0, "costo_in_banda": 0.0}

    def venduto(cl):
        return sum(s["vendi"] for s in sells if s["classe"] == cl)

    def esegui(i, vendi, forzata=False):
        p = POSITIONS[i]
        plus_real, comp, tassa, dz = effetto_vendita(p, vendi, zain)
        zain[p["broker"]] = zain.get(p["broker"], 0.0) + dz
        residuo[i] -= vendi
        sells.append({"broker": p["broker"], "classe": p["asset_class"], "tipo": p["tipo"],
                      "aliquota": _aliquota(p), "vendi": vendi, "plus_real": plus_real,
                      "comp": comp, "tassa": tassa, "forzata": forzata})
        return tassa

    def candidati(cl):
        """Indici delle posizioni della classe in ordine di costo fiscale: prima le minus,
        poi le quote a costo zero (diverso con zainetto), poi per imposta per euro venduto."""
        idx = [i for i, p in enumerate(POSITIONS) if p["asset_class"] == cl and residuo[i] > 1e-6]
        def costo(i):
            p = POSITIONS[i]
            if p["plus"] <= 0:
                return (0, p["plus"] / p["valore"] if p["valore"] else 0)
            if quota_costo_zero(p, zain, residuo[i]) > 1e-6:
                return (1, 0)
            return (2, p["plus"] / p["valore"] * _aliquota(p))
        return sorted(idx, key=costo)

    def costo_simulato(cl, importo):
        """Imposta di una vendita di `importo` dalla classe, senza eseguirla."""
        z, r, tassa = dict(zain), list(residuo), 0.0
        for i in candidati(cl):
            if importo <= 1e-6:
                break
            v = min(importo, r[i])
            _, _, t, dz = effetto_vendita(POSITIONS[i], v, z)
            z[POSITIONS[i]["broker"]] = z.get(POSITIONS[i]["broker"], 0.0) + dz
            tassa += t
            importo -= v
        return tassa

    # 2) vendite delle sovrappesate fuori banda (Leve 3 e 4), con la regola di rientro
    for cl, d in drift.items():
        eccesso = classi.get(cl, 0) - d["target"] * total_post     # euro sopra il target
        if eccesso <= 1e-6 or not d["fuori_banda"]:
            continue
        in_banda = classi.get(cl, 0) - (d["target"] + d["tight"] * MARGINE_RIENTRO) * total_post
        # prima tutto ciò che è a costo zero: minus e plus coperte dallo zainetto del broker
        obiettivo_zero = in_banda if OBIETTIVO_RIENTRO == "banda" else eccesso
        da_ridurre = obiettivo_zero
        for i in candidati(cl):
            if da_ridurre <= 1e-6:
                break
            v = min(da_ridurre, quota_costo_zero(POSITIONS[i], zain, residuo[i]))
            if v > 1e-6:
                esegui(i, v)
                da_ridurre -= v
        # poi la parte che paga imposta, solo oltre la banda larga
        mancante_target = eccesso - venduto(cl)
        if mancante_target <= 1e-6:
            continue
        d["costo_a_target"] = costo_simulato(cl, mancante_target)
        d["costo_in_banda"] = costo_simulato(cl, max(0.0, in_banda - venduto(cl)))
        if abs(d["drift"]) <= d["wide"]:
            d["residuo_non_corretto"] = mancante_target
            d["motivo"] = (f"vendita rinviata: imposta €{d['costo_a_target']:,.0f} con drift "
                           f"{d['drift']*100:+.1f}% entro la banda larga {d['wide']*100:.1f}%")
            continue
        da_ridurre = mancante_target if OBIETTIVO_RIENTRO == "target" else max(0.0, in_banda - venduto(cl))
        for i in candidati(cl):
            if da_ridurre <= 1e-6:
                break
            v = min(da_ridurre, residuo[i])
            esegui(i, v)
            da_ridurre -= v
        d["residuo_non_corretto"] = max(0.0, eccesso - venduto(cl))
        if d["residuo_non_corretto"] > 1e-6:
            d["motivo"] = (f"rientro a metà banda: a target costerebbe €{d['costo_a_target']:,.0f}, "
                           f"così €{d['costo_in_banda']:,.0f}")

    # 3) prelievo: se la cassa non basta, vendite forzate ripartite per riportare i pesi verso il
    #    target (water-filling sulle classi più sopra il target), finché il netto copre il prelievo
    for _ in range(20):
        cassa = cassa_in + sum(s["vendi"] - s["tassa"] for s in sells) - PRELIEVO
        if cassa >= -0.005:
            break
        valori = {cl: sum(residuo[i] for i, p in enumerate(POSITIONS) if p["asset_class"] == cl) for cl in TARGET}
        quote = _ripartisci(valori, -cassa)
        for cl, importo in quote.items():
            for i in candidati(cl):
                if importo <= 1e-6:
                    break
                v = min(importo, residuo[i])
                esegui(i, v, forzata=True)
                importo -= v
    tax_tot = sum(s["tassa"] for s in sells)

    # 4) cassa netta (versamenti + vendite − imposta − prelievo) verso le sottopesate:
    #    prima quelle fuori banda, poi le altre, fino al target; l'eventuale resto pro-rata al target
    cassa = max(0.0, cassa_in + sum(s["vendi"] - s["tassa"] for s in sells) - PRELIEVO)
    total_finale = total + cassa_in - PRELIEVO - tax_tot
    buys = {cl: 0.0 for cl in TARGET}

    def manca(cl):
        return TARGET[cl] * total_finale - (classi.get(cl, 0) - venduto(cl) + buys[cl])
    for gruppo in ([cl for cl in TARGET if drift[cl]["fuori_banda"]], list(TARGET)):
        bisogni = {cl: manca(cl) for cl in gruppo if manca(cl) > 1e-6}
        tot = sum(bisogni.values())
        if cassa <= 1e-6 or tot <= 0:
            continue
        for cl, need in bisogni.items():
            buys[cl] += min(need, cassa * need / tot)
        cassa = max(0.0, cassa - min(cassa, tot))
    if cassa > 1e-6:
        for cl, tw in TARGET.items():
            buys[cl] += cassa * tw

    risultante = {cl: (classi.get(cl, 0) - venduto(cl) + buys[cl]) / total_finale for cl in TARGET}
    return {"totale": total, "totale_post": total_post, "drift": drift, "acquisti": buys,
            "vendite": sells, "imposta": tax_tot, "zainetto": zain, "risultante": risultante,
            "prelievo": PRELIEVO, "entrate": cassa_in}


def _ripartisci(valori, importo):
    """Quanto vendere per classe per raccogliere `importo` lasciando i pesi il più vicino
    possibile al target: vendite = max(0, valore − target × λ), con λ trovato per bisezione."""
    disponibile = sum(valori.values())
    importo = min(importo, disponibile)
    lo, hi = 0.0, disponibile * 2 / max(min(t for t in TARGET.values() if t > 0), 1e-9)
    for _ in range(100):
        lam = (lo + hi) / 2
        tot = sum(max(0.0, v - TARGET[cl] * lam) for cl, v in valori.items())
        lo, hi = (lam, hi) if tot > importo else (lo, lam)
    return {cl: max(0.0, v - TARGET[cl] * hi) for cl, v in valori.items()}


CAMPI_CSV = ["broker", "operazione", "classe", "tipo_fiscale", "strumento_ISIN",
             "importo_eur", "plus_minus_eur", "imposta_eur", "compensazione_zainetto_eur", "nota"]
# Ultima riga di ogni CSV: chi apre il file vede il disclaimer, e l'intestazione resta la prima riga.
NOTA_CSV = ("Checklist educativa generata da ribilanciamento-multibroker.py: non costituisce consulenza "
            "di investimento né un ordine. Verificare saldi, prezzo medio di carico e zainetto "
            "sul portale del broker prima di operare.")


def genera_ordini(plan):
    """Trasforma il piano in una lista di ordini ESEGUIBILI per broker, instradando la cassa.
    Le vendite sono già specifiche per broker (con l'effetto fiscale). Gli acquisti e il prelievo
    vengono finanziati dalla liquidità presente su ciascun broker (le vendite lì realizzate, al
    netto dell'imposta che il broker trattiene, più eventuali versamenti che vi atterrano), così
    ogni broker resta a saldo e gli ordini sono eseguibili senza trasferimenti di cassa tra
    intermediari (che richiederebbero giorni)."""
    ordini = []

    # VENDITE — già per broker, con annotazione fiscale
    for s in plan["vendite"]:
        motivo = "finanzia il prelievo" if s["forzata"] else f"riduce sovrappeso {s['classe']}"
        if s["plus_real"] > 0 and s["comp"] > 0:
            nota = f"{motivo}; plus €{s['plus_real']:,.0f} compensata con zainetto {s['broker']}"
        elif s["plus_real"] > 0:
            nota = f"{motivo}; plus €{s['plus_real']:,.0f} TASSATA (no zainetto compensabile qui)"
        elif s["plus_real"] < 0:
            nota = f"{motivo}; minus €{-s['plus_real']:,.0f} a zainetto {s['broker']}"
        else:
            nota = motivo
        ordini.append({"broker": s["broker"], "operazione": "VENDITA", "classe": s["classe"],
                       "tipo_fiscale": s["tipo"], "importo_eur": round(s["vendi"], 2),
                       "plus_minus_eur": round(s["plus_real"], 2), "imposta_eur": round(s["tassa"], 2),
                       "compensazione_zainetto_eur": round(s["comp"], 2), "nota": nota})

    # cassa disponibile per broker = vendite nette realizzate lì (+ versamenti/flussi sul broker designato)
    cassa = {}
    for s in plan["vendite"]:
        cassa[s["broker"]] = cassa.get(s["broker"], 0.0) + s["vendi"] - s["tassa"]
    if plan["entrate"] > 0:
        cassa[BROKER_VERSAMENTI] = cassa.get(BROKER_VERSAMENTI, 0.0) + plan["entrate"]

    def preleva(importo, operazione, classe, nota):
        rimanente = importo
        for broker in sorted(cassa, key=lambda b: -cassa[b]):   # greedy: prima chi ha più cassa
            if rimanente <= 1e-6:
                break
            quota = min(rimanente, cassa[broker])
            if quota <= 1e-6:
                continue
            ordini.append({"broker": broker, "operazione": operazione, "classe": classe,
                           "tipo_fiscale": "", "importo_eur": round(quota, 2), "plus_minus_eur": "",
                           "imposta_eur": "", "compensazione_zainetto_eur": "", "nota": nota})
            cassa[broker] -= quota
            rimanente -= quota
        return rimanente

    # PRELIEVO prima degli acquisti: è il motivo delle vendite forzate
    if plan["prelievo"] > 0:
        preleva(plan["prelievo"], "PRELIEVO", "", "bonifico del prelievo netto sul conto corrente")
    # ACQUISTI — instradati sui broker che hanno cassa
    for cl, amt in plan["acquisti"].items():
        if amt <= 1e-6:
            continue
        rimanente = preleva(amt, "ACQUISTO", cl, f"riempie sottopeso {cl}")
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
    drift = plan["drift"]
    print(f"\n{'='*70}\nRIBILANCIAMENTO MULTI-BROKER  —  patrimonio €{plan['totale']:,.0f}\n{'='*70}")
    if plan["entrate"] or plan["prelievo"]:
        print(f"   pesi e gap misurati su €{plan['totale_post']:,.0f}: versamenti e flussi "
              f"+€{plan['entrate']:,.0f}, prelievo −€{plan['prelievo']:,.0f}")

    regola = {"misto": "a target se costa zero, a metà banda se tassato", "target": "a target",
              "banda": "a metà banda"}[OBIETTIVO_RIENTRO]
    print(f"\n1) DRIFT E BANDE DINAMICHE (regola 5/25, allargamento ×{WIDENING:g} se l'imposta morde; "
          f"rientro: {regola})")
    print(f"{'Classe':<18}{'Peso':>8}{'Target':>8}{'Drift':>8}{'B.stretta':>11}{'B.larga':>10}  Decisione")
    for cl, d in drift.items():
        dec = "in banda — non agire"
        if d["fuori_banda"]:
            dec = "FUORI banda — ribilanciare"
        print(f"{cl:<18}{d['peso']*100:>7.1f}%{d['target']*100:>7.0f}%{d['drift']*100:>+7.1f}%"
              f"{d['tight']*100:>10.1f}%{d['wide']*100:>9.1f}%  {dec}")

    print(f"\n2) PIANO — vendite (ottimizzate per broker e tipo fiscale)")
    rinviati = {cl: d for cl, d in drift.items() if d["residuo_non_corretto"] > 1e-6}
    if not plan["vendite"]:
        if rinviati:
            print("   nessuna vendita eseguita: le correzioni residue sono rinviate (vedi sotto)")
        else:
            print("   nessuna vendita necessaria (corretto con i soli flussi, o tutto in banda)")
    for s in plan["vendite"]:
        nota = ""
        if s["comp"] > 0:
            nota = f"  → plus €{s['plus_real']:,.0f} compensata €{s['comp']:,.0f} dallo zainetto {s['broker']}"
        elif s["plus_real"] > 0:
            nota = f"  → plus €{s['plus_real']:,.0f} TASSATA (no zainetto compensabile qui)"
        elif s["plus_real"] < 0:
            nota = f"  → minus €{-s['plus_real']:,.0f} a zainetto {s['broker']}"
        aliq = "" if s["aliquota"] == 0.26 else " (12,5%)"
        motivo = "  [prelievo]" if s["forzata"] else ""
        print(f"   VENDI €{s['vendi']:,.0f} {s['classe']}/{s['tipo']}{aliq} @ {s['broker']}"
              f"  | imposta €{s['tassa']:,.0f}{nota}{motivo}")
    for cl, d in rinviati.items():
        print(f"   {cl}: residuo non corretto €{d['residuo_non_corretto']:,.0f} — {d['motivo']}")
    for cl, d in drift.items():
        if d["costo_a_target"] > 1e-6 or d["costo_in_banda"] > 1e-6:
            print(f"   {cl}: costo fiscale della parte tassata a target €{d['costo_a_target']:,.0f}, "
                  f"a metà banda €{d['costo_in_banda']:,.0f}")

    print(f"\n   acquisti (riempimento sottopesate; broker a scelta, neutro ai fini fiscali)")
    for cl, q in plan["acquisti"].items():
        if q > 1e-6:
            print(f"   COMPRA €{q:,.0f} {cl}")

    print(f"\n3) COSTO FISCALE TOTALE: €{plan['imposta']:,.0f}")
    print(f"   zainetto residuo per broker: " +
          ", ".join(f"{b} €{v:,.0f}" for b, v in plan["zainetto"].items()))
    if plan["prelievo"]:
        lordo = sum(s["vendi"] for s in plan["vendite"])
        print(f"   vendite lorde €{lordo:,.0f}, imposta €{plan['imposta']:,.0f}, "
              f"netto prelevato €{plan['prelievo']:,.0f} (il resto è reinvestito)")

    print(f"\n4) ALLOCAZIONE RISULTANTE vs TARGET")
    for cl in TARGET:
        print(f"   {cl:<18}{plan['risultante'][cl]*100:>6.1f}%  (target {TARGET[cl]*100:.0f}%)")
    print()


def main():
    try:
        plan = pianifica()
    except ErroreInput as e:
        print(f"errore nei parametri: {e}")
        raise SystemExit(2)
    stampa(plan)
    if GENERA_CSV:
        esporta_ordini(plan)
    print("   Questo strumento è educativo e non costituisce consulenza di investimento o fiscale:")
    print("   l'allocazione target è tua; saldi, prezzo medio di carico e zainetto vanno verificati")
    print("   sul portale del broker.")
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
# Asserito da tests/run_tests.py (test «T7 ribilanciamento»), con MODULA_VOLATILITA spenta.
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
# Varianti asserite: NUOVI_VERSAMENTI=20000 → nessuna vendita, €20.000 allocati, 60/30/10;
# zainetto Fineco 2000 → vendita €5.000 a imposta zero, residuo €3.000 rinviato;
# PRELIEVO=10000 → vendite lorde = 10.000 + imposta + acquisti.
