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
   paga imposta. Lo script stampa i due costi, a target e in banda. Con "target" anche la
   parte tassata va a target (sempre solo oltre la banda larga); con "banda" anche la parte
   a costo zero si ferma al punto di rientro.

4. ORDINE DELLE LEVE SU TUTTO IL PORTAFOGLIO. Prima le minus e le posizioni senza plus di
   tutte le classi (Leva 3), poi le quote coperte dallo zainetto, poi il resto per imposta per
   euro venduto, plus/valore × aliquota (Leva 4): in amministrato una minus compensa solo le
   plus realizzate dopo sullo stesso broker (art. 6 c. 5 D.Lgs. 461/97 → art. 306 c. 6 TU
   2027), quindi i CSV elencano le vendite in minus per prime. Una classe sottopesata fuori
   banda si riempie con la cassa e con vendite a costo zero dalle classi sopra il target,
   anche se in banda; con imposta solo se dopo la cassa il suo drift supera la banda larga.

Flussi: i versamenti e i flussi in entrata entrano nel totale prima di misurare il drift
(una classe sovrappesata oggi può essere sottopesata dopo un versamento) e vengono allocati
tutti; il PRELIEVO in decumulo esce dal totale, si finanzia con vendite (imposta compresa)
e non si reinveste. Le minus realizzate ricaricano lo zainetto del broker per le vendite
successive; ogni posizione ha la sua aliquota (26%, o 12,5% per titoli di Stato e
equiparati, che compensano lo zainetto al 48,08%; per ETF e fondi su titoli di Stato
un'aliquota mista, dalla quota di titoli di Stato e white list del fondo).

I valori qui sotto sono l'esempio di validazione (vedi il commento ATTESO in fondo): i dati
reali arrivano da --dati piano.json, le cui chiavi sostituiscono le costanti omonime, e lo
zainetto anche da --zainetto (il JSON dell'importatore). plus = plusvalenza/minusvalenza latente
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

import argparse
import csv
import os
import sys

# ─────────────────────────── INPUT (editabili) ───────────────────────────
# Per posizione: broker, asset_class (una delle chiavi di TARGET), tipo ("diverso" o
# "capitale"), valore e plus in euro, e se serve "aliquota" (0.26 di default; 0.125 per
# titoli di Stato italiani e white list, enti territoriali e organismi internazionali).
# ETF e fondi (tipo "capitale") su titoli di Stato: "quota_titoli_stato", la quota media
# dell'attivo in titoli di Stato e white list che l'emittente certifica ogni semestre (non è
# nel KID; vale quella del semestre della vendita), oppure direttamente l'"aliquota" effettiva
# tra 0.125 e 0.26. Aliquota = 12,5% × quota + 26% × (1 − quota), e le minus del fondo entrano
# nello zainetto per aliquota / 26% (DM 13/12/2011, art. 1; misura del 48,08% dalla circ. AdE
# 19/E/2014, par. 5.1).
POSITIONS = [
    {"broker": "Fineco",  "asset_class": "azionario",      "tipo": "capitale", "valore": 40000, "plus": 10000},
    {"broker": "Fineco",  "asset_class": "azionario",      "tipo": "diverso",  "valore": 10000, "plus":  4000},
    {"broker": "Fineco",  "asset_class": "obbligazionario","tipo": "capitale", "valore": 15000, "plus":  -500},
    {"broker": "Directa", "asset_class": "azionario",      "tipo": "capitale", "valore": 18000, "plus":  3000},
    {"broker": "Directa", "asset_class": "obbligazionario","tipo": "diverso",  "valore":  9000, "plus":     0},
    {"broker": "Directa", "asset_class": "monetario",      "tipo": "capitale", "valore":  8000, "plus":     0},
]
# minusvalenze compensabili disponibili per broker (lo zainetto è per-intermediario), in euro
# di minus al 26%: le minus al 12,5% valgono il 48,08% (l'importatore di it-tax-optimization
# dà l'importo 26%-equivalente). Quale quota scade quest'anno lo dice lo stesso importatore.
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
MARGINE_RIENTRO   = 0.5      # punto di rientro della parte tassata: target ± MARGINE × banda stretta (0,5 = metà)

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


# Vocabolario: i nomi e i valori canonici sono quelli del plugin (README, «Glossario»); lo script
# accetta i sinonimi dei nomi delle chiavi e li normalizza, così le posizioni del JSON
# dell'importatore si copiano così come sono, aggiungendo solo la classe. Internamente il tipo
# fiscale è «diverso» o «capitale»; l'aliquota è una frazione (0.26, 0.125), e quella in percento
# dell'importatore (26, 12.5) si converte dicendolo.
SINONIMI_CHIAVI = {"classe": "asset_class", "asset class": "asset_class", "asset_class": "asset_class",
                   "categoria_fiscale": "tipo", "tipo_fiscale": "tipo", "categoria": "tipo", "tipo": "tipo",
                   "plus_minus": "plus", "plusvalenza": "plus", "plus": "plus",
                   "controvalore": "valore", "valore": "valore", "intermediario": "broker", "broker": "broker"}
SINONIMI_TIPO = {"diverso": "diverso", "reddito_diverso": "diverso", "redditi_diversi": "diverso",
                 "capitale": "capitale", "reddito_capitale": "capitale", "reddito_di_capitale": "capitale",
                 "redditi_di_capitale": "capitale"}
TIPI_FUORI_PERIMETRO = {"reddito_capitale_irpef": "la plus va a IRPEF progressiva: fuori dal perimetro del "
                                                  "ribilanciamento, trattala a parte",
                        "da_classificare": "classifica prima la posizione (vedi it-tax-optimization)"}


def normalizza_posizione(p):
    """La posizione con le chiavi e i valori canonici dello script: accetta i sinonimi del vocabolario
    del plugin (categoria_fiscale o tipo_fiscale → tipo; reddito_diverso → diverso; classe → asset_class;
    plus_minus → plus; controvalore → valore). Le chiavi ignote restano com'erano."""
    q = {}
    for k, v in p.items():
        chiave = str(k).strip().lower().replace(" ", "_")
        q[SINONIMI_CHIAVI.get(chiave, str(k).strip())] = v
    if isinstance(q.get("tipo"), str):
        t = q["tipo"].strip().lower().replace(" ", "_")
        q["tipo"] = SINONIMI_TIPO.get(t, t)
    for k in ("asset_class", "broker"):
        if isinstance(q.get(k), str):
            q[k] = q[k].strip()
    return q


def _aliquota_da_percento(p, n):
    """L'aliquota in percento dell'importatore (26, 12.5) diventa la frazione dello script, con un avviso:
    le frazioni valide stanno tra 0,125 e 0,26, i percento tra 12,5 e 26, quindi non si confondono."""
    a = p.get("aliquota")
    if isinstance(a, (int, float)) and not isinstance(a, bool) and 1 < a <= 100:
        p["aliquota"] = a / 100
        print(f"ℹ posizione {n}: aliquota {numero(a, 1)} letta in percento → {numero(a / 100, 3)}")


# Chiavi del JSON di --dati (minuscole) → costanti dello script.
CHIAVI_DATI = {"posizioni": "POSITIONS", "zainetto": "ZAINETTO", "target": "TARGET",
               "nuovi_versamenti": "NUOVI_VERSAMENTI", "flussi_attesi": "FLUSSI_ATTESI", "prelievo": "PRELIEVO",
               "aliquota_default": "ALIQUOTA", "obiettivo_rientro": "OBIETTIVO_RIENTRO",
               "margine_rientro": "MARGINE_RIENTRO", "modula_volatilita": "MODULA_VOLATILITA",
               "genera_csv": "GENERA_CSV", "cartella_output": "CARTELLA_OUTPUT",
               "broker_versamenti": "BROKER_VERSAMENTI"}


def carica_dati(path):
    """Portafoglio, zainetto, target e opzioni dal JSON di --dati (schema in SKILL.md): sostituiscono le
    costanti in testa allo script. Chiavi ignote → errore, così un refuso non passa in silenzio."""
    import json
    try:
        with open(path, encoding="utf-8") as f:
            dati = json.load(f)
    except OSError as e:
        raise ErroreInput(f"--dati: impossibile leggere {path} ({e.strerror})")
    except ValueError as e:
        raise ErroreInput(f"--dati: {path} non è un JSON valido ({e})")
    if not isinstance(dati, dict):
        raise ErroreInput(f"--dati: {path} deve contenere un oggetto JSON con posizioni, zainetto e target")
    ignote = [k for k in dati if str(k).lower() not in CHIAVI_DATI]
    if ignote:
        raise ErroreInput(f"--dati: chiavi non riconosciute {ignote}; attese: {', '.join(CHIAVI_DATI)}")
    for k, v in dati.items():
        globals()[CHIAVI_DATI[str(k).lower()]] = v
    if not isinstance(POSITIONS, list) or not isinstance(ZAINETTO, dict) or not isinstance(TARGET, dict):
        raise ErroreInput("--dati: «posizioni» è una lista, «zainetto» e «target» sono oggetti broker → euro e classe → peso")
    globals()["DATI_ESEMPIO"] = False
    return dati


def carica_zainetto_importatore(path):
    """Lo zainetto per broker dal JSON di importa-estratto-broker.py --json: analisi.per_broker[b].
    zainetto_26_equivalente, cioè le minus valide in euro al 26% (quelle al 12,5% già al 48,08%)."""
    import json
    try:
        with open(path, encoding="utf-8") as f:
            dati = json.load(f)
        per_broker = dati["analisi"]["per_broker"]
        zainetto = {b: float(v["zainetto_26_equivalente"]) for b, v in per_broker.items()}
    except OSError as e:
        raise ErroreInput(f"--zainetto: impossibile leggere {path} ({e.strerror})")
    except (ValueError, KeyError, TypeError):
        raise ErroreInput(f"--zainetto: {path} non è il JSON di importa-estratto-broker.py --json "
                          f"(manca analisi.per_broker[].zainetto_26_equivalente)")
    globals()["ZAINETTO"] = zainetto
    return zainetto


class ErroreInput(Exception):
    """Parametri non validi: messaggio «ERRORE: …» su stderr e uscita con codice 1 (il 2 è di argparse)."""


def _numero_vero(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def allinea_zainetto(posizioni, zainetto):
    """Le chiavi dello zainetto con i nomi dei broker delle posizioni: «FINECO» o « fineco » diventano
    «Fineco» (sommando se due chiavi coincidono), con un avviso; uno zainetto di un broker senza
    posizioni resta inutilizzato, e lo si dice invece di perderlo in silenzio."""
    canonici = {}
    for p in posizioni:
        canonici.setdefault(str(p["broker"]).strip().casefold(), p["broker"])
    allineato = {}
    for chiave, importo in zainetto.items():
        nome = canonici.get(str(chiave).strip().casefold(), chiave)
        if nome != chiave:
            print(f"ℹ zainetto «{chiave}» → «{nome}», il nome del broker nelle posizioni")
        allineato[nome] = allineato.get(nome, 0.0) + importo
    for nome, importo in allineato.items():
        if importo > 0 and nome not in canonici.values():
            suggerimento = (" (l'estratto non aveva la colonna broker: rilancia l'importatore con --broker NOME)"
                            if nome == "(broker non indicato)" else "")
            print(f"⚠ zainetto «{nome}» di €{numero(importo)} non usato: nessuna posizione con quel broker "
                  f"(broker delle posizioni: {', '.join(sorted(set(canonici.values())))}){suggerimento}")
    return allineato


def valida():
    """Validazione dell'input, dopo la normalizzazione dei sinonimi del vocabolario: tipi (numeri veri,
    mai testo), aliquote, classi e broker; lo zainetto allineato ai broker delle posizioni."""
    globals()["POSITIONS"] = [normalizza_posizione(p) for p in POSITIONS]
    if not isinstance(TARGET, dict) or not TARGET:
        raise ErroreInput("TARGET vuoto: indicare le classi con il peso target (somma 1)")
    if not all(_numero_vero(v) for v in TARGET.values()):
        raise ErroreInput("TARGET: i pesi devono essere numeri (es. 0.6, non «60%» o «0.6» tra virgolette)")
    somma = sum(TARGET.values())
    if abs(somma - 1) > 1e-6:
        raise ErroreInput(f"TARGET somma a {numero(somma, 4)}, non a 1")
    if not isinstance(ZAINETTO, dict):
        raise ErroreInput("ZAINETTO: oggetto broker → euro di minus al 26% (es. {\"Fineco\": 5000})")
    for chiave, importo in ZAINETTO.items():
        if not _numero_vero(importo) or importo < 0:
            raise ErroreInput(f"ZAINETTO «{chiave}»: {importo!r} non è un importo in euro (es. 5000, non «5.000»)")
    for nome in ("NUOVI_VERSAMENTI", "FLUSSI_ATTESI", "PRELIEVO", "MARGINE_RIENTRO", "ALIQUOTA"):
        if not _numero_vero(globals()[nome]):
            raise ErroreInput(f"{nome.lower()}: {globals()[nome]!r} non è un numero (scriverlo senza virgolette)")
    for n, p in enumerate(POSITIONS, start=1):
        for campo in ("broker", "asset_class", "tipo", "valore", "plus"):
            if campo not in p:
                raise ErroreInput(f"posizione {n}: manca «{campo}» (chiavi: broker, asset_class, tipo, valore, plus)")
        if not isinstance(p.get("broker"), str) or not p["broker"]:
            raise ErroreInput(f"posizione {n}: broker vuoto o mancante (lo zainetto è per broker)")
        _aliquota_da_percento(p, n)
        if p.get("asset_class") not in TARGET:
            raise ErroreInput(f"posizione {n}: classe «{p.get('asset_class')}» assente da TARGET")
        if p.get("tipo") in TIPI_FUORI_PERIMETRO:
            raise ErroreInput(f"posizione {n}: {p['tipo']}: {TIPI_FUORI_PERIMETRO[p['tipo']]}")
        if p.get("tipo") not in ("diverso", "capitale"):
            raise ErroreInput(f"posizione {n}: tipo «{p.get('tipo')}» (attesi «diverso» o «capitale», "
                              f"anche come reddito_diverso o reddito_capitale)")
        for campo in ("valore", "plus"):
            if isinstance(p[campo], bool) or not isinstance(p[campo], (int, float)):
                raise ErroreInput(f"posizione {n}: {campo} {p[campo]!r} non numerico")
        for campo in ("aliquota", "quota_titoli_stato"):
            if campo in p and (isinstance(p[campo], bool) or not isinstance(p[campo], (int, float))):
                raise ErroreInput(f"posizione {n}: {campo} {p[campo]!r} non numerica (es. 0.125, non «12,5%»)")
        quota = p.get("quota_titoli_stato")
        if quota is not None:
            if p["tipo"] != "capitale":
                raise ErroreInput(f"posizione {n}: quota_titoli_stato vale solo per fondi ed ETF (tipo «capitale»)")
            if "aliquota" in p:
                raise ErroreInput(f"posizione {n}: indicare quota_titoli_stato oppure aliquota, non entrambe")
            if not 0 <= quota <= 1:
                raise ErroreInput(f"posizione {n}: quota_titoli_stato {quota} (attesa tra 0 e 1)")
        elif p["tipo"] == "diverso" and _aliquota(p) not in (0.26, 0.125):
            raise ErroreInput(f"posizione {n}: aliquota {_aliquota(p)} (attese 0.26 o 0.125 per un titolo "
                              f"detenuto direttamente)")
        elif not 0.125 <= _aliquota(p) <= 0.26:
            raise ErroreInput(f"posizione {n}: aliquota {_aliquota(p)} (per fondi ed ETF tra 0.125 e 0.26)")
        if p.get("valore", -1) < 0:
            raise ErroreInput(f"posizione {n}: valore negativo o mancante")
    if OBIETTIVO_RIENTRO not in ("misto", "target", "banda"):
        raise ErroreInput(f"OBIETTIVO_RIENTRO «{OBIETTIVO_RIENTRO}» (attesi misto, target, banda)")
    if min(PRELIEVO, NUOVI_VERSAMENTI, FLUSSI_ATTESI) < 0:
        raise ErroreInput("PRELIEVO, NUOVI_VERSAMENTI e FLUSSI_ATTESI vanno indicati come importi positivi")
    globals()["ZAINETTO"] = allinea_zainetto(POSITIONS, ZAINETTO)


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
    """Aliquota effettiva della posizione. Per fondi ed ETF con quota_titoli_stato è la media
    12,5% × quota + 26% × (1 − quota): la parte di proventi riferibile ai titoli di Stato e white
    list (DM 13/12/2011, art. 1) conta per il 48,08% (circ. AdE 19/E/2014, par. 5.1)."""
    if p.get("quota_titoli_stato") is not None:
        return 0.125 * p["quota_titoli_stato"] + 0.26 * (1 - p["quota_titoli_stato"])
    return p.get("aliquota", ALIQUOTA)


def _coeff(p):
    """Peso nello zainetto (in minus al 26%) di un euro di plus o minus della posizione: aliquota
    / 26%, cioè 48,08% al 12,5% (art. 6 c. 1 D.Lgs. 461/97 → art. 306 c. 1 TU 2027) e, per un
    fondo misto, 1 − 51,92% × quota (DM 13/12/2011, art. 1 c. 4; circ. AdE 19/E/2014, par. 5.1)."""
    return _aliquota(p) * 100 / 26     # non / 0.26: 0.125 / 0.26 differisce di un ulp da 12,5 / 26


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


def _etichetta_rientro():
    """Come si chiama il punto di rientro della parte tassata (target + MARGINE_RIENTRO × banda stretta)."""
    return "a metà banda" if MARGINE_RIENTRO == 0.5 else f"al {pct(MARGINE_RIENTRO, 0)} della banda stretta"


def piano_quote(quote, zain, residuo, totale=None, solo_costo_zero=False):
    """Vendite [(indice, euro)] che raccolgono fino a `quote[classe]` euro per classe (e al massimo
    `totale` in tutto) nell'ordine fiscale, su tutte le classi insieme: prima le minus e le posizioni
    senza plus (Leva 3, ricaricano lo zainetto), poi le quote coperte dallo zainetto del broker, poi
    il resto per imposta per euro venduto, plus/valore × aliquota (Leva 4). Aggiorna `zain` e
    `residuo` (passare copie per simulare) e ritorna anche l'imposta."""
    resto = {cl: q for cl, q in quote.items() if q > 0}
    budget = float("inf") if totale is None else totale
    vendite, tassa = [], 0.0

    def costo(i):
        p = POSITIONS[i]
        return (p["plus"] / p["valore"] * _aliquota(p) if p["valore"] else 0.0, i)

    def passata(ammessa, quanto, minimo):
        nonlocal budget, tassa
        idx = [i for i, p in enumerate(POSITIONS)
               if resto.get(p["asset_class"], 0) > 0.005 and residuo[i] > 0.005 and ammessa(p)]
        for i in sorted(idx, key=costo):
            p = POSITIONS[i]
            v = min(resto[p["asset_class"]], budget, quanto(i))
            if v < 0.005 or (v < minimo and v < min(resto[p["asset_class"]], budget) - 0.005):
                continue        # niente ordini sotto €1 per un risparmio d'imposta di centesimi
            _, _, t, dz = effetto_vendita(p, v, zain)
            zain[p["broker"]] = zain.get(p["broker"], 0.0) + dz
            residuo[i] -= v
            resto[p["asset_class"]] -= v
            budget -= v
            tassa += t
            vendite.append((i, v))

    passata(lambda p: p["plus"] <= 0, lambda i: residuo[i], 1.0)
    passata(lambda p: p["plus"] > 0 and p["tipo"] == "diverso",
            lambda i: quota_costo_zero(POSITIONS[i], zain, residuo[i]), 1.0)
    if not solo_costo_zero:
        passata(lambda p: True, lambda i: residuo[i], 0.0)
    return vendite, tassa


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
    zain = {b: float(v) for b, v in ZAINETTO.items()}   # zainetto per broker, nell'ordine delle decisioni
    residuo = [float(p["valore"]) for p in POSITIONS]   # controvalore non ancora venduto
    eventi = []             # (indice, euro, forzata, imposta, classe servita) in ordine di decisione
    buys = {cl: 0.0 for cl in TARGET}

    # 1) drift e decisione di banda, sul patrimonio dopo flussi e prelievo
    drift = {}
    for cl, tw in TARGET.items():
        w = classi.get(cl, 0) / total_post
        tight, wide = banda(tw, cl)
        drift[cl] = {"peso": w, "target": tw, "drift": w - tw, "gap_eur": (w - tw) * total_post,
                     "tight": tight, "wide": wide, "fuori_banda": abs(w - tw) > tight,
                     "residuo_non_corretto": 0.0, "motivo": "", "costo_a_target": 0.0, "costo_in_banda": 0.0,
                     "esito": "", "drift_decisione": w - tw}

    def gravita(cl):          # ordine deterministico, non quello delle chiavi di TARGET
        d = drift[cl]
        return (-abs(d["drift"]) / d["tight"] if d["tight"] else -float("inf"), cl)

    def venduto(cl):
        return sum(e[1] for e in eventi if POSITIONS[e[0]]["asset_class"] == cl)

    def valore(cl):
        return classi.get(cl, 0) - venduto(cl) + buys[cl]

    def cassa_libera():       # versamenti + vendite nette − prelievo − acquisti già assegnati
        return cassa_in + sum(e[1] - e[3] for e in eventi) - PRELIEVO - sum(buys.values())

    def esegui(vendite, forzata=False, serve=None):
        incasso = 0.0
        for i, v in vendite:
            p = POSITIONS[i]
            _, _, t, dz = effetto_vendita(p, v, zain)
            zain[p["broker"]] = zain.get(p["broker"], 0.0) + dz
            residuo[i] -= v
            eventi.append((i, v, forzata, t, serve or p["asset_class"]))
            incasso += v - t
        return incasso

    def lordo(netto, quote_di):
        """Lordo da vendere perché il netto d'imposta copra `netto` (le quote dipendono dal lordo)."""
        g = netto
        for _ in range(60):
            vend, t = piano_quote(quote_di(g), dict(zain), list(residuo), totale=g)
            if sum(v for _, v in vend) < g - 0.005 or abs(netto + t - g) < 0.0005:
                break
            g = netto + t
        return g

    def eccedenze(esclusa=None):  # quanto le altre classi sono sopra il target, sulla base delle decisioni
        return {c: max(0.0, valore(c) - TARGET[c] * total_post) for c in TARGET if c != esclusa}

    # 2) sovrappesate fuori banda. Prima tutto ciò che è a costo zero, su tutte le classi insieme
    #    (le minus di ogni classe prima delle plus, perché compensano solo le plus vendute dopo sullo
    #    stesso broker); poi, classe per classe, la parte che paga imposta, solo oltre la banda larga
    sopra = sorted((cl for cl, d in drift.items() if d["fuori_banda"] and d["gap_eur"] > 1e-6), key=gravita)
    eccesso = {cl: drift[cl]["gap_eur"] for cl in sopra}
    in_banda = {cl: classi.get(cl, 0) - (drift[cl]["target"] + drift[cl]["tight"] * MARGINE_RIENTRO) * total_post
                for cl in sopra}
    obiettivo_zero = {cl: in_banda[cl] if OBIETTIVO_RIENTRO == "banda" else eccesso[cl] for cl in sopra}
    esegui(piano_quote(obiettivo_zero, dict(zain), list(residuo), solo_costo_zero=True)[0])
    for cl in sopra:
        d = drift[cl]
        if eccesso[cl] - venduto(cl) <= 0.005:
            continue
        if OBIETTIVO_RIENTRO == "banda" and in_banda[cl] - venduto(cl) <= 0.005:
            d["esito"] = "scelta"
        elif abs(d["drift"]) <= d["wide"]:
            d["esito"] = "rinviata"
        else:
            quanto = eccesso[cl] if OBIETTIVO_RIENTRO == "target" else in_banda[cl]
            esegui(piano_quote({cl: quanto - venduto(cl)}, dict(zain), list(residuo))[0])
            d["esito"] = "rientro"

    # 3) prelievo: se la cassa non basta, vendite forzate ripartite per riportare i pesi verso il
    #    target (water-filling sulle classi più sopra il target), con lo stesso ordine fiscale; il
    #    lordo si calcola prima, così ogni posizione esce in una sola vendita
    mancante = -(cassa_in + sum(e[1] - e[3] for e in eventi) - PRELIEVO)
    if mancante > 0.005:
        def quote_prelievo(g):
            valori = {cl: sum(residuo[i] for i, p in enumerate(POSITIONS) if p["asset_class"] == cl) for cl in TARGET}
            q = _ripartisci(valori, g)
            grande = max(q, key=q.get)
            for cl in list(q):          # niente vendite sotto €1: le briciole vanno alla classe maggiore
                if cl != grande and 0 < q[cl] < 1 and q[grande] + q[cl] <= valori[grande]:
                    q[grande] += q[cl]
                    q[cl] = 0.0
            return q
        g = lordo(mancante, quote_prelievo)
        esegui(piano_quote(quote_prelievo(g), dict(zain), list(residuo), totale=g)[0], forzata=True)
        netto = cassa_in + sum(e[1] - e[3] for e in eventi) - PRELIEVO
        if netto < -0.01:
            raise ErroreInput(f"prelievo non finanziabile: il netto massimo dopo l'imposta è "
                              f"€{numero(netto + PRELIEVO)} (vendendo tutto)")

    # 4) sottopesate fuori banda: prima la cassa (pro-rata al fabbisogno), poi vendite a costo zero
    #    dalle classi sopra il target (anche in banda); con imposta solo se dopo cassa e costo zero il
    #    drift supera ancora la banda larga, e solo fino al punto di rientro
    sotto = sorted((cl for cl, d in drift.items() if d["fuori_banda"] and d["gap_eur"] < -1e-6), key=gravita)

    def obiettivo(cl):
        quota = TARGET[cl] - (drift[cl]["tight"] * MARGINE_RIENTRO if OBIETTIVO_RIENTRO == "banda" else 0.0)
        return quota * total_post

    bisogni = {cl: obiettivo(cl) - valore(cl) for cl in sotto if obiettivo(cl) - valore(cl) > 0.005}
    pool, tot = max(0.0, cassa_libera()), sum(bisogni.values())
    for cl, need in bisogni.items():
        buys[cl] += min(need, pool * need / tot)
    for cl in sotto:
        d = drift[cl]
        quota_target = TARGET[cl] * total_post
        rientro = (TARGET[cl] - d["tight"] * MARGINE_RIENTRO) * total_post
        manca = obiettivo(cl) - valore(cl)
        if manca > 0.005:
            buys[cl] += esegui(piano_quote(eccedenze(cl), dict(zain), list(residuo), totale=manca,
                                           solo_costo_zero=True)[0], serve=cl)
        if quota_target - valore(cl) <= 0.005:
            continue
        d["drift_decisione"] = (valore(cl) - quota_target) / total_post
        if OBIETTIVO_RIENTRO == "banda" and rientro - valore(cl) <= 0.005:
            d["esito"] = "scelta"
        elif abs(d["drift_decisione"]) <= d["wide"]:
            d["esito"] = "rinviata"
        else:
            netto = (quota_target if OBIETTIVO_RIENTRO == "target" else rientro) - valore(cl)
            if netto > 0.005:
                g = lordo(netto, lambda _g: eccedenze(cl))
                buys[cl] += esegui(piano_quote(eccedenze(cl), dict(zain), list(residuo), totale=g)[0], serve=cl)
            d["esito"] = "rientro"

    # 5) liquidazione: una riga per posizione, le minus prima delle plus (compensano solo le plus
    #    successive sullo stesso broker, art. 6 c. 5 D.Lgs. 461/97 → art. 306 c. 6 TU 2027);
    #    effetti fiscali ricalcolati in quest'ordine, che è quello di esecuzione
    righe = {}
    for i, v, forzata, _, _ in eventi:
        r = righe.setdefault(i, {"vendi": 0.0, "prelievo": 0.0})
        r["vendi"] += v
        r["prelievo"] += v if forzata else 0.0
    zain = {b: float(v) for b, v in ZAINETTO.items()}
    sells = []
    for i in sorted(righe, key=lambda i: POSITIONS[i]["plus"] > 0):      # stabile: poi l'ordine delle decisioni
        p, r = POSITIONS[i], righe[i]
        plus_real, comp, tassa, dz = effetto_vendita(p, r["vendi"], zain)
        zain[p["broker"]] = zain.get(p["broker"], 0.0) + dz
        sells.append({"broker": p["broker"], "classe": p["asset_class"], "tipo": p["tipo"],
                      "aliquota": _aliquota(p), "vendi": r["vendi"], "plus_real": plus_real, "comp": comp,
                      "tassa": tassa, "zainetto": dz, "prelievo": r["prelievo"],
                      "forzata": r["prelievo"] >= r["vendi"] - 0.005})
    tax_tot = sum(s["tassa"] for s in sells)

    # 6) cassa netta (versamenti + vendite − imposta − prelievo) verso le sottopesate:
    #    prima quelle fuori banda, poi le altre, fino al target; l'eventuale resto pro-rata al target
    cassa = max(0.0, cassa_in + sum(s["vendi"] - s["tassa"] for s in sells) - PRELIEVO - sum(buys.values()))
    total_finale = total + cassa_in - PRELIEVO - tax_tot

    def manca(cl):
        return TARGET[cl] * total_finale - valore(cl)
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

    # 7) residui dopo tutte le vendite (prelievo compreso), con il costo di completare la correzione
    #    dallo stato finale; i costi stampati comprendono l'imposta già pagata dalla classe. Una
    #    sovrappesata si misura sulla base delle decisioni (dopo flussi e prelievo); una sottopesata
    #    sul patrimonio finale, perché l'imposta pagata esce dal portafoglio e non è un sottopeso
    residuo_fin = [float(p["valore"]) for p in POSITIONS]
    for i, r in righe.items():
        residuo_fin[i] -= r["vendi"]
    for cl, d in drift.items():
        if not d["fuori_banda"]:
            continue
        if d["gap_eur"] > 0:
            scarto = valore(cl) - TARGET[cl] * total_post
            margine = d["tight"] * MARGINE_RIENTRO * total_post
            res, res_banda = max(0.0, scarto), max(0.0, scarto - margine)
            simula = lambda x: piano_quote({cl: x}, dict(zain), list(residuo_fin))[1]
        else:
            scarto = valore(cl) - TARGET[cl] * total_finale
            margine = d["tight"] * MARGINE_RIENTRO * total_finale
            res, res_banda = max(0.0, -scarto), max(0.0, -scarto - margine)
            simula = lambda x: piano_quote(eccedenze(cl), dict(zain), list(residuo_fin), totale=x)[1]
        # imposta delle vendite fatte per questa classe (le sue, o quelle che hanno riempito il suo sottopeso)
        pagata = sum(e[3] for e in eventi if e[4] == cl and not e[2])
        d["costo_a_target"] = pagata + (simula(res) if res > 0.5 else 0.0)
        d["costo_in_banda"] = pagata + (simula(res_banda) if res_banda > 0.5 else 0.0)
        if res <= 0.5:
            continue
        d["residuo_non_corretto"] = res
        etichetta, deriva = _etichetta_rientro(), d["drift_decisione"] * 100
        if d["esito"] == "scelta":
            d["motivo"] = (f"fermato {etichetta} per scelta (OBIETTIVO_RIENTRO «banda»): a target "
                           f"costerebbe altri €{numero(d['costo_a_target'] - pagata)}")
        elif d["esito"] == "rinviata":
            costo = d["costo_in_banda"] if OBIETTIVO_RIENTRO == "banda" else d["costo_a_target"]
            d["motivo"] = (f"vendita rinviata: imposta €{numero(costo - pagata)} con drift {numero(deriva, 1, segno=True)}% "
                           f"entro la banda larga {numero(d['wide']*100, 1)}%")
            if OBIETTIVO_RIENTRO == "banda":
                d["motivo"] += f"; tra il rientro {etichetta} e il target resta per scelta (OBIETTIVO_RIENTRO «banda»)"
        elif d["esito"] == "rientro" and OBIETTIVO_RIENTRO == "target":
            d["motivo"] = (f"rientro a target con imposta €{numero(pagata)} (drift {numero(deriva, 1, segno=True)}% oltre la banda "
                           f"larga {numero(d['wide']*100, 1)}%): lo scostamento che resta viene dall'imposta pagata, "
                           f"che esce dal portafoglio")
        elif d["esito"] == "rientro":
            d["motivo"] = (f"rientro {etichetta} (drift {numero(deriva, 1, segno=True)}% oltre la banda larga "
                           f"{numero(d['wide']*100, 1)}%): a target costerebbe €{numero(d['costo_a_target'])}, "
                           f"così €{numero(d['costo_in_banda'])}")
        else:
            d["motivo"] = "scostamento rimasto dopo il prelievo e l'imposta"
        per_prelievo = sum(s["prelievo"] for s in sells if s["classe"] == cl)
        if per_prelievo > 0.5:
            d["motivo"] += f"; €{numero(per_prelievo)} già venduti per il prelievo"

    liquidato = total_finale <= 0.005
    risultante = {cl: 0.0 if liquidato else valore(cl) / total_finale for cl in TARGET}
    return {"totale": total, "totale_post": total_post, "drift": drift, "acquisti": buys,
            "vendite": sells, "imposta": tax_tot, "zainetto": zain, "risultante": risultante,
            "prelievo": PRELIEVO, "entrate": cassa_in, "liquidato": liquidato}


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


CAMPI_CSV = ["broker", "operazione", "classe", "categoria_fiscale", "strumento_ISIN",
             "importo_eur", "plus_minus_eur", "imposta_eur", "compensazione_zainetto_eur", "nota"]
# Ultima riga di ogni CSV: chi apre il file vede il disclaimer, e l'intestazione resta la prima riga.
NOTA_CSV = ("Checklist educativa generata da ribilanciamento-multibroker.py: non costituisce consulenza "
            "di investimento né un ordine. Verificare saldi, prezzo medio di carico e zainetto "
            "sul portale del broker prima di operare.")
# Senza --dati il piano è quello dei dati d'esempio: lo dice anche il CSV, che può circolare da solo.
NOTA_CSV_ESEMPIO = "DATI DI ESEMPIO dello script, non un portafoglio reale. " + NOTA_CSV
DATI_ESEMPIO = True     # diventa False quando i dati arrivano da --dati
# Nel CSV la categoria fiscale ha i valori del vocabolario del plugin (README, «Glossario»).
CATEGORIA_CSV = {"diverso": "reddito_diverso", "capitale": "reddito_capitale"}


def numero(x, decimali=0, segno=False):
    """Numero in formato italiano: punto per le migliaia, virgola per i decimali (come
    motore_bootstrap.numero nelle skill previdenziali: questa skill non ha il motore)."""
    testo = f"{x:{'+' if segno else ''},.{decimali}f}"
    return testo.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def pct(frazione, decimali=1, segno=False):
    return numero(frazione * 100, decimali, segno) + "%"


def _percento(x, decimali=1):
    return pct(x, decimali)


def _mista(a):
    """Aliquota mista a un decimale, a due quando l'arrotondamento la farebbe sembrare 12,5% o 26%."""
    testo = _percento(a)
    return _percento(a, 2) if testo in ("12,5%", "26,0%") else testo


def _etichetta_aliquota(a):
    return "al 12,5%" if a == 0.125 else f"ad aliquota mista {_mista(a)}"


def effetto_fiscale(s):
    """Effetto fiscale di una vendita del piano, con il consumo reale dello zainetto (48,08% per
    le plus e minus al 12,5%, aliquota / 26% per un fondo misto) e l'avviso d'ordine per le minus."""
    ridotta = s["aliquota"] < 0.26
    computata = _percento(s["aliquota"] / 0.26, 2)
    if s["plus_real"] < 0:
        testo = f"minus €{numero(-s['plus_real'])} a zainetto {s['broker']}"
        if ridotta:
            testo += (f" (vale €{numero(s['zainetto'])} di zainetto: minus {_etichetta_aliquota(s['aliquota'])} "
                      f"computata al {computata})")
        return testo + ", da eseguire prima delle vendite in plus"
    if s["comp"] > 0:
        testo = f"plus €{numero(s['plus_real'])} compensata €{numero(s['comp'])} dallo zainetto {s['broker']}"
        if ridotta:
            testo += (f" (consuma €{numero(-s['zainetto'])} di zainetto: plus {_etichetta_aliquota(s['aliquota'])} "
                      f"computata al {computata})")
        if s["plus_real"] - s["comp"] > 0.005:
            testo += f", il resto €{numero(s['plus_real'] - s['comp'])} TASSATO"
        return testo
    aliquota = "" if s["aliquota"] == 0.26 else f" {_etichetta_aliquota(s['aliquota'])}"
    if s["tipo"] == "capitale":
        return f"plus €{numero(s['plus_real'])} TASSATA{aliquota} (reddito di capitale: non si compensa con lo zainetto)"
    return f"plus €{numero(s['plus_real'])} TASSATA{aliquota} (no zainetto compensabile qui)"


def genera_ordini(plan):
    """Trasforma il piano in una lista di ordini ESEGUIBILI per broker, instradando la cassa.
    Le vendite sono già specifiche per broker (con l'effetto fiscale). Gli acquisti e il prelievo
    vengono finanziati dalla liquidità presente su ciascun broker (le vendite lì realizzate, al
    netto dell'imposta che il broker trattiene, più eventuali versamenti che vi atterrano), così
    ogni broker resta a saldo e gli ordini sono eseguibili senza trasferimenti di cassa tra
    intermediari (che richiederebbero giorni)."""
    ordini = []

    # VENDITE — già per broker e nell'ordine di esecuzione (le minus prima delle plus), con l'effetto fiscale
    for s in plan["vendite"]:
        if s["forzata"]:
            motivo = "finanzia il prelievo"
        elif s["prelievo"] > 0.005:
            motivo = f"riduce sovrappeso {s['classe']}; €{numero(s['prelievo'])} finanziano il prelievo"
        else:
            motivo = f"riduce sovrappeso {s['classe']}"
        nota = f"{motivo}; {effetto_fiscale(s)}" if s["plus_real"] else motivo
        ordini.append({"broker": s["broker"], "operazione": "VENDITA", "classe": s["classe"],
                       "categoria_fiscale": CATEGORIA_CSV.get(s["tipo"], s["tipo"]), "importo_eur": round(s["vendi"], 2),
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
                           "categoria_fiscale": "", "importo_eur": round(quota, 2), "plus_minus_eur": "",
                           "imposta_eur": "", "compensazione_zainetto_eur": "", "nota": nota})
            cassa[broker] -= quota
            rimanente -= quota
        return rimanente

    # PRELIEVO prima degli acquisti: è il motivo delle vendite forzate
    if plan["prelievo"] > 0:
        rimanente = preleva(plan["prelievo"], "PRELIEVO", "", "bonifico del prelievo netto sul conto corrente")
        if rimanente > 0.005:   # difesa: pianifica() rifiuta i prelievi non finanziabili
            ordini.append({"broker": "(da finanziare)", "operazione": "PRELIEVO", "classe": "",
                           "categoria_fiscale": "", "importo_eur": round(rimanente, 2), "plus_minus_eur": "",
                           "imposta_eur": "", "compensazione_zainetto_eur": "",
                           "nota": "prelievo non coperto dalla cassa netta dei broker"})
    # ACQUISTI — instradati sui broker che hanno cassa
    for cl, amt in plan["acquisti"].items():
        if amt <= 1e-6:
            continue
        rimanente = preleva(amt, "ACQUISTO", cl, f"riempie sottopeso {cl}")
        if rimanente > 1e-6:   # cassa insufficiente ovunque: serve un versamento/trasferimento
            ordini.append({"broker": "(da finanziare)", "operazione": "ACQUISTO", "classe": cl,
                           "categoria_fiscale": "", "importo_eur": round(rimanente, 2), "plus_minus_eur": "",
                           "imposta_eur": "", "compensazione_zainetto_eur": "",
                           "nota": f"riempie sottopeso {cl} — cassa insufficiente, richiede versamento o trasferimento"})
    return ordini


DELIMITATORE_CSV = ";"


def _cella_csv(v):
    """Importi con due decimali e la virgola (8000,00); il resto com'è."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return v
    return f"{v:.2f}".replace(".", ",")


def scrivi_csv_per_broker(ordini, cartella=None):
    """Scrive un CSV per broker nella cartella indicata. Ritorna la lista (path, n_righe)."""
    cartella = cartella or CARTELLA_OUTPUT
    if not ordini:
        return []
    os.makedirs(cartella, exist_ok=True)
    scritti = []
    for b in sorted({o["broker"] for o in ordini}):
        righe = [o for o in ordini if o["broker"] == b]
        slug = "".join(c if c.isalnum() else "_" for c in b)
        path = os.path.join(cartella, f"ordini_{slug}.csv")
        # Apribile in Excel italiano con un doppio clic: «;» come separatore, virgola decimale,
        # UTF-8 con BOM (senza BOM Excel legge il file in cp1252 e sporca «€»).
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=CAMPI_CSV, extrasaction="ignore", delimiter=DELIMITATORE_CSV)
            w.writeheader()
            for o in righe:
                row = {k: _cella_csv(v) for k, v in o.items()}
                row.setdefault("strumento_ISIN", "")   # colonna da compilare a mano
                w.writerow(row)
            w.writerow({"broker": b, "operazione": "NOTA", "nota": NOTA_CSV_ESEMPIO if DATI_ESEMPIO else NOTA_CSV})
        scritti.append((path, len(righe)))
    return scritti


def stampa(plan):
    drift = plan["drift"]
    print(f"\n{'='*70}\nRIBILANCIAMENTO MULTI-BROKER  —  patrimonio €{numero(plan['totale'])}\n{'='*70}")
    if plan["entrate"] or plan["prelievo"]:
        print(f"   pesi e gap misurati su €{numero(plan['totale_post'])}: versamenti e flussi "
              f"+€{numero(plan['entrate'])}, prelievo −€{numero(plan['prelievo'])}")

    etichetta = _etichetta_rientro()
    regola = {"misto": f"a target se costa zero, {etichetta} se tassato", "target": "a target",
              "banda": etichetta}[OBIETTIVO_RIENTRO]
    print(f"\n1) DRIFT E BANDE DINAMICHE (regola 5/25, allargamento ×{WIDENING:g} se l'imposta morde; "
          f"rientro: {regola})")
    print(f"{'Classe':<18}{'Peso':>8}{'Target':>8}{'Drift':>8}{'B.stretta':>11}{'B.larga':>10}  Decisione")
    for cl, d in drift.items():
        dec = "in banda — non agire"
        if d["fuori_banda"]:
            dec = "FUORI banda — ribilanciare"
        print(f"{cl:<18}{numero(d['peso']*100, 1):>7}%{numero(d['target']*100):>7}%{numero(d['drift']*100, 1, segno=True):>7}%"
              f"{numero(d['tight']*100, 1):>10}%{numero(d['wide']*100, 1):>9}%  {dec}")

    print(f"\n2) PIANO — vendite (ottimizzate per broker e tipo fiscale; da eseguire nell'ordine "
          f"elencato, le minus prima delle plus)")
    rinviati = {cl: d for cl, d in drift.items() if d["residuo_non_corretto"] > 1e-6}
    if not plan["vendite"]:
        if rinviati:
            print("   nessuna vendita eseguita: le correzioni residue sono rinviate (vedi sotto)")
        elif any(d["fuori_banda"] for d in drift.values()):
            print("   nessuna vendita necessaria: le classi fuori banda si correggono con versamenti e flussi")
        else:
            print("   nessuna vendita necessaria: tutte le classi sono in banda")
    for s in plan["vendite"]:
        nota = f"  → {effetto_fiscale(s)}" if s["plus_real"] else ""
        aliq = "" if s["aliquota"] == 0.26 else (" (12,5%)" if s["aliquota"] == 0.125
                                                 else f" (aliquota mista {_mista(s['aliquota'])})")
        motivo = "  [prelievo]" if s["forzata"] else (f"  [€{numero(s['prelievo'])} per il prelievo]"
                                                       if s["prelievo"] > 0.005 else "")
        print(f"   VENDI €{numero(s['vendi'])} {s['classe']}/{s['tipo']}{aliq} @ {s['broker']}"
              f"  | imposta €{numero(s['tassa'])}{nota}{motivo}")
    for cl, d in rinviati.items():
        print(f"   {cl}: residuo non corretto €{numero(d['residuo_non_corretto'])} — {d['motivo']}")
    for cl, d in drift.items():
        if d["costo_a_target"] > 1e-6 or d["costo_in_banda"] > 1e-6:
            print(f"   {cl}: costo fiscale della parte tassata a target €{numero(d['costo_a_target'])}, "
                  f"{etichetta} €{numero(d['costo_in_banda'])}")

    print(f"\n   acquisti (riempimento sottopesate; broker a scelta, neutro ai fini fiscali)")
    if not any(q > 0.5 for q in plan["acquisti"].values()):
        print("   nessun acquisto")
    for cl, q in plan["acquisti"].items():
        if q > 1e-6:
            print(f"   COMPRA €{numero(q)} {cl}")

    print(f"\n3) COSTO FISCALE TOTALE: €{numero(plan['imposta'])}")
    print(f"   zainetto residuo per broker: " +
          ", ".join(f"{b} €{numero(v)}" for b, v in plan["zainetto"].items()))
    if plan["prelievo"]:
        lordo = sum(s["vendi"] for s in plan["vendite"])
        reinvestito = sum(plan["acquisti"].values())
        print(f"   vendite lorde €{numero(lordo)}, imposta €{numero(plan['imposta'])}, "
              f"netto prelevato €{numero(plan['prelievo'])}"
              + (f" (€{numero(reinvestito)} reinvestiti)" if reinvestito > 0.5 else ""))

    print(f"\n4) ALLOCAZIONE RISULTANTE vs TARGET")
    if plan["liquidato"]:
        print("   portafoglio interamente liquidato dal prelievo")
    for cl in TARGET:
        print(f"   {cl:<18}{numero(plan['risultante'][cl]*100, 1):>6}%  (target {numero(TARGET[cl]*100)}%)")
    print()


def _configura_stdout():
    """UTF-8 su stdout e stderr anche su Windows (cp1252), come motore_bootstrap.configura_stdout."""
    for flusso in (sys.stdout, sys.stderr):
        try:
            flusso.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def main(argv=None):
    _configura_stdout()
    ap = argparse.ArgumentParser(
        allow_abbrev=False,
        description="Ribilanciamento tax-aware multi-broker: drift e bande 5/25, piano di vendite per broker e "
                    "tipo fiscale nell'ordine di esecuzione, prelievo in decumulo, ordini in CSV per broker. "
                    "Portafoglio, zainetto, target, versamenti e prelievo arrivano dal JSON di --dati (schema in "
                    "SKILL.md), lo zainetto anche da --zainetto; senza --dati lo script gira sull'esempio di "
                    "validazione in testa al file. "
                    "Codici d'uscita: 0 riuscito, 1 parametri incoerenti, 2 riga di comando errata.")
    ap.add_argument("--dati", metavar="FILE",
                    help="JSON con posizioni, zainetto, target e opzioni (schema in SKILL.md); senza, i dati di "
                         "esempio in testa allo script")
    ap.add_argument("--zainetto", metavar="FILE",
                    help="JSON di importa-estratto-broker.py --json: lo zainetto per broker in euro 26%%-equivalenti "
                         "(analisi.per_broker), al posto di quello del JSON di --dati o dello script")
    ap.add_argument("--out", metavar="DIR", help="cartella dei CSV degli ordini (default: ./ordini nella cartella corrente)")
    args = ap.parse_args(argv)
    try:
        if args.dati:
            carica_dati(args.dati)
        else:
            print("⚠️  Dati di esempio: portafoglio, zainetto e target sono quelli in testa allo script. "
                  "Passa --dati piano.json con i tuoi (schema in SKILL.md).")
        if args.zainetto:
            carica_zainetto_importatore(args.zainetto)
        if args.out:
            globals()["CARTELLA_OUTPUT"] = args.out
        plan = pianifica()
    except ErroreInput as e:
        print(f"ERRORE: parametri: {e}", file=sys.stderr)
        raise SystemExit(1)
    stampa(plan)
    if GENERA_CSV:
        esporta_ordini(plan)
    print("   Questo strumento è educativo e non costituisce consulenza di investimento o fiscale:")
    print("   l'allocazione target è tua; saldi, prezzo medio di carico e zainetto vanno verificati")
    print("   sul portale del broker.")
    print()


def esporta_ordini(plan):
    ordini = genera_ordini(plan)
    if not ordini:
        print("5) NESSUN ORDINE DA ESPORTARE — le correzioni sono rinviate (vedi la sezione 2) o non "
              "necessarie; nessun CSV generato")
        print()
        return
    scritti = scrivi_csv_per_broker(ordini)
    print(f"5) ORDINI ESPORTATI — un CSV per broker in {os.path.join(CARTELLA_OUTPUT, '')}")
    for path, n in scritti:
        print(f"   {path}  ({n} ordini)")
    # anteprima leggibile
    print(f"\n   Anteprima:")
    print(f"   {'broker':<14}{'op.':<9}{'classe':<16}{'categoria':<17}{'importo':>10}  nota")
    for o in ordini:
        imp = f"€{numero(o['importo_eur'])}"
        print(f"   {o['broker']:<14}{o['operazione']:<9}{o['classe']:<16}{str(o['categoria_fiscale']):<17}{imp:>10}  {o['nota']}")
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
# zainetto 0 → nessuna vendita, residuo €8.000 rinviato e stampato, nessun CSV;
# OBIETTIVO_RIENTRO="banda" → vendita €5.500 a imposta zero, il resto fermo per scelta;
# TARGET 64/21/15 (solo il monetario fuori banda, sottopeso) → €3.000 di obbligazionario in
# minus e €4.000 di azionario «diverso» Fineco venduti a costo zero, monetario a target;
# PRELIEVO=10000 → vendite lorde = 10.000 + imposta + acquisti, una riga per posizione;
# PRELIEVO oltre il netto di liquidazione (€96.620) → errore nei parametri.
