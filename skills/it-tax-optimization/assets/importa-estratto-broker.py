#!/usr/bin/env python3
"""
importa-estratto-broker.py — import dei dati fiscali dai broker (regime amministrato).

Perché esiste (e perché NON è un MCP "live"): i broker italiani non espongono via API
il dato che serve all'ottimizzazione fiscale — lo zainetto e le plus/minus. Quel dato vive
nei REPORT esportabili (sezione "Fiscalità"/certificazione, estratto del portafoglio). Questo
script ingerisce un estratto del portafoglio in CSV — che scarichi tu dal broker, quindi senza
dare credenziali a nessuno — calcola le plus/minus LATENTI per posizione, e le incrocia con lo
zainetto per evidenziare le occasioni di harvesting. È uno strumento educativo e non
costituisce consulenza fiscale o finanziaria.

Formati: i broker (Directa, Fineco, Trade Republic...) esportano layout DIVERSI. Il parser
riconosce i nomi-colonna tipici con sinonimi e matching tollerante (maiuscole, accenti, spazi
ignorati); se il tuo export usa nomi diversi, aggiungili ai dizionari SINONIMI qui sotto. Il
formato dei numeri si decide per file: se compare una virgola decimale («12,40») il file è
all'italiana e «1.000» vale mille.

Regole fiscali applicate (vedi SKILL.md e le reference):
- La plus da vendita di ETF e fondi è reddito di CAPITALE, non compensabile con lo zainetto
  (art. 44 c. 1 lett. g TUIR); la minus è reddito diverso. Gli OICR non armonizzati fuori
  UE/SEE vanno a IRPEF progressiva (reddito_capitale_irpef). Azioni, obbligazioni ed ETC/ETN
  sono reddito diverso. Senza colonna "tipo fiscale" la categoria si deduce dalla DESCRIZIONE,
  non dal prefisso ISIN (DE/FR/IE/LU coprono anche azioni singole); se la descrizione non dà
  indizi la posizione resta «da classificare» e la sua plus non viene contata.
- BOT, CTZ e zero coupon: la plus latente è in gran parte scarto di emissione (reddito di
  capitale), quindi restano «da classificare».
- Titoli di Stato italiani (ISIN IT + BTP/BOT/CCT/CTZ in descrizione): aliquota 12,5%.
- Le minus scadono il 31/12 del quarto anno successivo al realizzo: quelle scadute rispetto
  a --anno sono escluse (con avviso).
- 12,5% e 26% si confrontano in «26%-equivalente» (coefficiente 48,08%, art. 6 c. 1 D.Lgs.
  461/97): una minus al 12,5% vale 0,48 € per euro, e 1 € di minus al 26% assorbe 2,08 € di
  plus al 12,5%.
- Lo zainetto è per intermediario: con più broker la compensazione si calcola broker per broker.

Limiti dichiarati: legge CSV, non i PDF della certificazione; lo zainetto è un secondo CSV;
per le obbligazioni con nominale e prezzo in percentuale serve la colonna del valore di carico
(altrimenti costo = quantità × prezzo); i numeri valgono solo per l'amministrato:
in dichiarativo (broker esteri) si applicano il LIFO e il cambio del giorno, non calcolati qui.

Uso:
    python importa-estratto-broker.py estratto.csv [zainetto.csv] [--anno AAAA]
                                     [--broker NOME] [--json PERCORSO|-]
Dipendenze: solo libreria standard.
"""

import argparse
import csv
import datetime
import io
import json
import re
import sys
import unicodedata

K_12_5 = 12.5 / 26          # coefficiente 48,08%: 12,5% espresso in «26%-equivalente»
ANNI_VALIDITA = 4           # minus utilizzabili fino al 31/12 del quarto anno successivo

# ───────────────────── mappatura colonne (sinonimi, estendibili) ─────────────────────
SINONIMI = {
    "broker":        ["broker", "intermediario"],
    "isin":          ["isin", "codice isin", "cod isin"],
    "descrizione":   ["descrizione", "strumento", "titolo", "denominazione", "nome", "prodotto"],
    "quantita":      ["quantita", "quantità", "qta", "q.ta", "q.tà", "pezzi", "numero", "nominale", "quantita'"],
    "prezzo_carico": ["prezzo medio di carico", "prezzo di carico", "pmc", "prezzo carico",
                      "carico medio", "costo medio", "prezzo medio carico", "prz carico"],
    "valore_carico": ["valore di carico", "controvalore di carico", "costo", "valore carico",
                      "controvalore carico", "costo di carico"],
    "prezzo_attuale":["prezzo", "ultimo prezzo", "quotazione", "prezzo di mercato", "prezzo mercato",
                      "prezzo corrente", "ultimo", "prz"],
    "valore_attuale":["controvalore", "valore di mercato", "valore attuale", "controvalore di mercato",
                      "valore mercato", "ctv", "controvalore mercato", "controvalore attuale", "valore"],
    "tipo_fiscale":  ["tipo fiscale", "categoria fiscale", "natura", "natura fiscale"],
    "aliquota":      ["aliquota", "aliquota fiscale"],
}

SINONIMI_ZAIN = {
    "broker":   ["broker", "intermediario"],
    "anno":     ["anno", "anno formazione", "anno di formazione", "anno realizzo", "esercizio",
                 "annualita", "annualità"],
    "importo":  ["importo", "minusvalenza", "minus", "residuo", "importo residuo", "valore", "ammontare"],
    "aliquota": ["aliquota", "aliquota fiscale", "%", "perc"],
}

COLONNE_NUMERICHE = ("quantita", "prezzo_carico", "valore_carico", "prezzo_attuale", "valore_attuale")

# Stati UE e SEE (ISIN): OICR istituiti qui sono armonizzati o, se non lo sono, possono avere
# un gestore vigilato; fuori da quest'area la plus va a IRPEF (art. 10-ter L. 77/1983).
UE_SEE = set("AT BE BG CY CZ DE DK EE ES FI FR GR HR HU IE IT LT LU LV MT NL PL PT RO SE SI SK "
             "IS LI NO".split())
EMITTENTI_OICR = ("ishares", "vanguard", "xtrackers", "amundi", "lyxor", "spdr", "invesco",
                  "vaneck", "wisdomtree")
CATEGORIE = ("reddito_diverso", "reddito_capitale", "reddito_capitale_irpef", "da_classificare")


class ErroreInput(Exception):
    """Errore sui file di input: messaggio leggibile, uscita con codice 2."""


def _norm(s):
    """Normalizza un'intestazione: minuscolo, senza accenti, spazi compattati."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode("ascii")
    return " ".join(s.lower().replace("_", " ").split())


def _mappa_colonne(intestazioni, sinonimi):
    """Mappa ogni campo canonico alla colonna giusta. I match ESATTI vincono, poi l'alias più
    lungo contenuto nell'intestazione (gestisce 'Prezzo di carico (EUR)'). Ogni colonna va a un
    solo campo e ogni campo a una sola colonna, per evitare collisioni."""
    norm_head = [_norm(h) for h in intestazioni]
    candidati = []   # (campo, indice_colonna, punteggio)
    for campo, alias in sinonimi.items():
        for a in alias:
            an = _norm(a)
            for idx, h in enumerate(norm_head):
                if an == h:
                    candidati.append((campo, idx, 1000 + len(an)))
                elif an in h:
                    candidati.append((campo, idx, len(an)))
    candidati.sort(key=lambda c: -c[2])
    mappa, colonne_usate = {}, set()
    for campo, idx, _ in candidati:
        if campo in mappa or idx in colonne_usate:
            continue
        mappa[campo] = idx
        colonne_usate.add(idx)
    return mappa


# ───────────────────────────── numeri IT/EN ─────────────────────────────
def _pulisci(x):
    s = str(x).strip().replace("€", "").replace("EUR", "").replace(" ", "")
    return s.replace(" ", "").replace("'", "")


def _indizio_locale(x):
    """'it' se la cella ha una virgola decimale, 'en' se ha un punto decimale, None se ambigua."""
    s = _pulisci(x).lstrip("+-(").rstrip(")")
    if not s or not any(c.isdigit() for c in s):
        return None
    if "," in s and "." in s:
        return "it" if s.rfind(",") > s.rfind(".") else "en"
    for sep, loc in ((",", "it"), (".", "en")):
        if sep in s and len(s.rsplit(sep, 1)[1]) != 3:
            return loc
    return None


def rileva_locale(valori):
    """Decide il formato dei numeri per l'intero file (maggioranza degli indizi)."""
    it = sum(1 for v in valori if _indizio_locale(v) == "it")
    en = sum(1 for v in valori if _indizio_locale(v) == "en")
    return "it" if it > en else "en" if en > it else None


def _num(x, locale, ambigui=None):
    """Converte un numero in formato italiano o inglese. `locale` è quello del file; senza
    indizi, «1.000» (punto e tre cifre) vale mille e la cella finisce in `ambigui`."""
    if x is None:
        return None
    s = _pulisci(x)
    if not s or s.lower() in ("-", "n.d.", "nd", "na", "n/a"):
        return None
    negativo = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    migliaia_punto = re.fullmatch(r"[+-]?\d{1,3}(\.\d{3})+", s)
    migliaia_virgola = re.fullmatch(r"[+-]?\d{1,3}(,\d{3})+", s)
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        if migliaia_virgola and (locale == "en" or s.count(",") > 1):
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    elif "." in s and migliaia_punto and (locale == "it" or s.count(".") > 1 or locale is None):
        if locale is None and s.count(".") == 1 and ambigui is not None:
            ambigui.append(str(x).strip())
        s = s.replace(".", "")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if negativo else v


def _aliquota(x):
    """'26%', '26', '12,5%', '12.50' → 26.0 o 12.5; None se vuota; ErroreInput se ignota."""
    if x is None or not str(x).strip():
        return None
    v = _num(str(x).replace("%", ""), "it")
    if v is not None and abs(v - 12.5) < 1e-9:
        return 12.5
    if v is not None and abs(v - 26) < 1e-9:
        return 26.0
    raise ErroreInput(f"aliquota non riconosciuta: «{x}» (attese 26 o 12,5)")


# ───────────────────────────── lettura file ─────────────────────────────
def _leggi_csv(path):
    """Legge un CSV rilevando il delimitatore (',' ';' o tab) e ritorna (intestazioni, righe)."""
    try:
        with open(path, encoding="utf-8-sig") as f:
            testo = f.read()
    except FileNotFoundError:
        raise ErroreInput(f"file non trovato: {path}")
    except UnicodeDecodeError:
        raise ErroreInput(f"{path}: il file non è in UTF-8 (riesportalo in UTF-8 o CSV standard)")
    righe_testo = [r for r in testo.splitlines() if r.strip()]
    if not righe_testo:
        raise ErroreInput(f"{path}: file vuoto")
    try:
        delim = csv.Sniffer().sniff(righe_testo[0], delimiters=";,\t").delimiter
    except csv.Error:
        delim = ";" if righe_testo[0].count(";") >= righe_testo[0].count(",") else ","
    righe = [r for r in csv.reader(io.StringIO(testo), delimiter=delim) if any(c.strip() for c in r)]
    if len(righe) < 2:
        raise ErroreInput(f"{path}: nessuna riga di dati sotto l'intestazione")
    return righe[0], righe[1:]


# ───────────────────────────── classificazione ─────────────────────────────
def _categoria_da_colonna(valore, avvisi, nome):
    v = _norm(valore)
    if not v:
        return None
    if "irpef" in v:
        return "reddito_capitale_irpef"
    if "capital" in v:
        return "reddito_capitale"
    if "divers" in v:
        return "reddito_diverso"
    if "classific" in v:
        return "da_classificare"
    avvisi.append(f"{nome}: tipo fiscale «{valore}» non riconosciuto, posizione da classificare")
    return "da_classificare"


def classifica(isin, descrizione):
    """(categoria, è_titolo_di_stato_IT, nota) dedotti dalla descrizione e, per gli OICR,
    dal paese dell'ISIN. In dubbio «da_classificare»: mai assumere reddito diverso."""
    d = descrizione or ""
    dl = d.lower()
    paese = (isin or "")[:2].upper()
    stato_it = paese == "IT" and re.search(r"\b(BTP\w*|BOT|CCT\w*|CTZ)\b", d, re.I) is not None
    if re.search(r"\b(ETC|ETN|ETP)\b", d, re.I) or "certificate" in dl:
        return "reddito_diverso", False, "ETC/ETN/certificate: reddito diverso"
    oicr = (re.search(r"\b(ETF|UCITS|SICAV|OICR|OICVM|fondo|fund)\b", d, re.I) is not None
            or (any(e in dl for e in EMITTENTI_OICR) and not _sembra_azione(d)))
    if oicr:
        if not isin:
            return "da_classificare", False, "OICR senza ISIN: domicilio ignoto"
        if paese not in UE_SEE:
            return ("reddito_capitale_irpef", False,
                    "OICR fuori UE/SEE: plus a IRPEF progressiva, quadro RL anche in amministrato")
        if re.search(r"non[ -]?(armonizzat|ucits)|\b(FIA|AIF)\b", d, re.I):
            return ("da_classificare", False,
                    "OICR non armonizzato UE/SEE: 26% solo con gestore vigilato, altrimenti IRPEF")
        return "reddito_capitale", False, "ETF/fondo: plus reddito di capitale, non compensabile"
    if _sembra_azione(d):
        return "reddito_diverso", False, "azione: reddito diverso"
    if re.search(r"\b(BOT|CTZ)\b", d, re.I) or "zero coupon" in dl:
        return ("da_classificare", stato_it,
                "zero coupon: la plus è in gran parte scarto di emissione (reddito di capitale)")
    if stato_it or re.search(r"obblig|\bbond\b|\d+([.,]\d+)?\s?%", d, re.I):
        return ("reddito_diverso", stato_it,
                "obbligazione: reddito diverso al netto di ratei e scarto di emissione maturati")
    return "da_classificare", False, "nessun indizio dalla descrizione"


def _sembra_azione(d):
    return re.search(r"\bazion|\bord\b|(\b(s\.?p\.?a|s\.?a|ag|se|n\.?v|plc|inc|corp|ltd)\.?)\s*$", d, re.I) is not None


# ───────────────────────────── parsing ─────────────────────────────
def parse_estratto(path, broker_default=None, avvisi=None):
    avvisi = [] if avvisi is None else avvisi
    intest, righe = _leggi_csv(path)
    m = _mappa_colonne(intest, SINONIMI)
    if "isin" not in m and "descrizione" not in m:
        raise ErroreInput(f"{path}: estratto non riconosciuto, manca sia ISIN sia Descrizione. "
                          "Controlla il file o aggiungi i nomi-colonna ai dizionari SINONIMI.")
    locale = rileva_locale(r[m[c]] for r in righe for c in COLONNE_NUMERICHE
                           if c in m and m[c] < len(r))
    ambigui, posizioni = [], []
    for n, r in enumerate(righe, start=2):
        def get(campo):
            return r[m[campo]].strip() if campo in m and m[campo] < len(r) else ""
        isin, descr = get("isin"), get("descrizione")
        nome = descr or isin or f"riga {n}"
        qta = _num(get("quantita"), locale, ambigui)
        prezzo_c = _num(get("prezzo_carico"), locale, ambigui)
        val_c = _num(get("valore_carico"), locale, ambigui)
        prezzo_a = _num(get("prezzo_attuale"), locale, ambigui)
        val_a = _num(get("valore_attuale"), locale, ambigui)
        costo = val_c if val_c is not None else (qta * prezzo_c if qta is not None and prezzo_c is not None else None)
        valore = val_a if val_a is not None else (qta * prezzo_a if qta is not None and prezzo_a is not None else None)
        if costo is None or valore is None:
            avvisi.append(f"riga {n} scartata ({nome}): mancano costo o valore leggibili")
            continue
        categoria, stato_it, nota = classifica(isin, descr)
        fonte = "descrizione" if nota != "nessun indizio dalla descrizione" else "nessun indizio"
        da_colonna = _categoria_da_colonna(get("tipo_fiscale"), avvisi, nome)
        if da_colonna:
            categoria, fonte, nota = da_colonna, "colonna", "categoria dalla colonna del file"
        aliquota = _aliquota(get("aliquota")) or (12.5 if stato_it else 26.0)
        plus_minus = valore - costo
        posizioni.append({
            "broker": get("broker") or broker_default,
            "isin": isin,
            "descrizione": descr,
            "quantita": qta,
            "costo": round(costo, 2),
            "valore": round(valore, 2),
            "plus_minus": round(plus_minus, 2),
            "pct": round(plus_minus / costo * 100, 2) if costo else None,
            "categoria_fiscale": categoria,
            "aliquota": aliquota,
            "fonte_categoria": fonte,
            "nota": nota,
        })
    if ambigui:
        avvisi.append(f"formato numeri: nessuna virgola decimale nel file, {', '.join(ambigui[:3])} "
                      "letti con il punto come separatore delle migliaia: verificare")
    return posizioni


def parse_zainetto(path, anno_rif, broker_default=None, avvisi=None):
    avvisi = [] if avvisi is None else avvisi
    intest, righe = _leggi_csv(path)
    m = _mappa_colonne(intest, SINONIMI_ZAIN)
    if "importo" not in m:
        raise ErroreInput(f"{path}: zainetto non riconosciuto, manca la colonna dell'importo")
    if "aliquota" not in m:
        avvisi.append("zainetto senza colonna aliquota: assunto il 26% per tutte le minus")
    locale = rileva_locale(r[m["importo"]] for r in righe if m["importo"] < len(r))
    zain = []
    for n, r in enumerate(righe, start=2):
        def get(campo):
            return r[m[campo]].strip() if campo in m and m[campo] < len(r) else ""
        imp = _num(get("importo"), locale)
        if imp is None and get("importo"):
            avvisi.append(f"zainetto riga {n} scartata: importo «{get('importo')}» non leggibile")
        if imp is None or imp == 0:
            continue
        trovato = re.search(r"(19|20)\d{2}", get("anno"))
        anno = int(trovato.group(0)) if trovato else None
        aliquota = _aliquota(get("aliquota")) or 26.0
        if anno is None:
            stato, scade = "anno_mancante", None
            avvisi.append(f"zainetto riga {n}: anno di realizzo mancante, minus esclusa (scadenza ignota)")
        else:
            scade = anno + ANNI_VALIDITA
            stato = "scaduta" if scade < anno_rif else "in_scadenza" if scade == anno_rif else "valida"
            if stato == "scaduta":
                avvisi.append(f"zainetto: minus {anno} scaduta il 31/12/{scade}, esclusa dal totale")
        importo = round(abs(imp), 2)
        zain.append({
            "broker": get("broker") or broker_default,
            "anno": anno,
            "importo": importo,
            "aliquota": aliquota,
            "scade_il": f"31/12/{scade}" if scade else None,
            "stato": stato,
            "importo_26_equivalente": round(importo * (K_12_5 if aliquota == 12.5 else 1), 2),
        })
    return zain


def allinea_broker(posizioni, zainetto, avvisi):
    """Assegna il broker dove un file non lo dice. Con un solo broker per parte i due file si
    riferiscono allo stesso intermediario; con più broker nell'estratto lo zainetto deve dirlo."""
    if not zainetto:
        return
    b_pos = {p["broker"] for p in posizioni}
    b_zain = {z["broker"] for z in zainetto} - {None}
    if len(b_pos) > 1 and any(z["broker"] is None for z in zainetto):
        raise ErroreInput("l'estratto contiene più broker ma lo zainetto non ha la colonna broker: "
                          "aggiungila (lo zainetto è per intermediario, non si compensa tra broker)")
    if b_pos == {None} and len(b_zain) > 1:
        raise ErroreInput("lo zainetto contiene più broker ma l'estratto non dice a quale appartiene: "
                          "usa --broker o aggiungi la colonna broker all'estratto")
    if b_pos == {None} and len(b_zain) == 1:
        for p in posizioni:
            p["broker"] = next(iter(b_zain))
        b_pos = b_zain
    if len(b_pos) == 1:
        for z in zainetto:
            if z["broker"] is None:
                z["broker"] = next(iter(b_pos))
    estranei = {z["broker"] for z in zainetto} - {p["broker"] for p in posizioni}
    if estranei:
        avvisi.append(f"zainetto di broker assenti dall'estratto ({', '.join(map(str, estranei))}): "
                      "quelle minus non compensano plus di altri broker")


# ───────────────────────────── analisi ─────────────────────────────
def _compensazione(posizioni, zainetto):
    """Compensazione dentro UN broker, in 26%-equivalente: si coprono prima le plus al 12,5%
    (1 € di minus al 26% ne assorbe 2,08 €), poi quelle al 26%. L'imposta risparmiata è la
    stessa in ogni ordine: 26% × min(zainetto, plus) in 26%-equivalente."""
    p26 = sum(p["plus_minus"] for p in posizioni
              if p["plus_minus"] > 0 and p["categoria_fiscale"] == "reddito_diverso" and p["aliquota"] == 26)
    p12 = sum(p["plus_minus"] for p in posizioni
              if p["plus_minus"] > 0 and p["categoria_fiscale"] == "reddito_diverso" and p["aliquota"] == 12.5)
    validi = [z for z in zainetto if z["stato"] in ("valida", "in_scadenza")]
    zeq = sum(z["importo"] * (K_12_5 if z["aliquota"] == 12.5 else 1) for z in validi)
    capienza = zeq
    c12 = min(p12 * K_12_5, capienza)
    capienza -= c12
    c26 = min(p26, capienza)
    return {
        "plus_latenti_compensabili": round(p26 + p12, 2),
        "plus_latenti_compensabili_26_equivalente": round(p26 + p12 * K_12_5, 2),
        "zainetto_totale": round(sum(z["importo"] for z in validi), 2),
        "zainetto_26_equivalente": round(zeq, 2),
        "zainetto_in_scadenza": round(sum(z["importo"] for z in zainetto if z["stato"] == "in_scadenza"), 2),
        "zainetto_scaduto": round(sum(z["importo"] for z in zainetto if z["stato"] == "scaduta"), 2),
        "plus_realizzabili_a_costo_zero": round(c12 / K_12_5 + c26, 2),
        "imposta_risparmiabile": round(0.26 * (c12 + c26), 2),
    }


def analizza(posizioni, zainetto):
    plus = [p for p in posizioni if p["plus_minus"] > 0]
    minus = [p for p in posizioni if p["plus_minus"] < 0]
    somma_plus = lambda cat: round(sum(p["plus_minus"] for p in plus if p["categoria_fiscale"] == cat), 2)
    broker = sorted({p["broker"] for p in posizioni} | {z["broker"] for z in zainetto}, key=str)
    per_broker = {(b or "(broker non indicato)"): _compensazione([p for p in posizioni if p["broker"] == b],
                                                                  [z for z in zainetto if z["broker"] == b])
                  for b in broker}
    totali = {k: round(sum(g[k] for g in per_broker.values()), 2) for k in _compensazione([], [])}
    tot_costo = sum(p["costo"] for p in posizioni)
    tot_valore = sum(p["valore"] for p in posizioni)
    a = {
        "totale_costo": round(tot_costo, 2),
        "totale_valore": round(tot_valore, 2),
        "plus_minus_netta_latente": round(tot_valore - tot_costo, 2),
        "totale_minus_latenti": round(sum(p["plus_minus"] for p in minus), 2),
        "totale_plus_latenti": round(sum(p["plus_minus"] for p in plus), 2),
        "plus_non_compensabili": somma_plus("reddito_capitale"),
        "plus_irpef": somma_plus("reddito_capitale_irpef"),
        "plus_da_classificare": somma_plus("da_classificare"),
    }
    a.update(totali)
    a["per_broker"] = per_broker
    return a


# ───────────────────────────── output ─────────────────────────────
def _eur(x):
    """Importo all'italiana: 1.234,56."""
    return f"{x:,.2f}".replace(",", "§").replace(".", ",").replace("§", ".")


def _pct(x):
    return f"{x:+.1f}%".replace(".", ",") if x is not None else "n.d."


ETICHETTA = {"reddito_diverso": "diverso", "reddito_capitale": "capitale",
             "reddito_capitale_irpef": "capitale a IRPEF", "da_classificare": "da classificare"}


def stampa(posizioni, zainetto, a, anno_rif, avvisi):
    w = 78
    print(f"\n{'=' * w}")
    print(f"IMPORT ESTRATTO BROKER — {len(posizioni)} posizioni valutate, anno di riferimento {anno_rif}")
    print(f"{'=' * w}")
    print(f"Costo totale di carico:   € {_eur(a['totale_costo']):>14}")
    print(f"Valore di mercato:        € {_eur(a['totale_valore']):>14}")
    print(f"Plus/minus netta latente: € {_eur(a['plus_minus_netta_latente']):>14}")

    print("\n— MINUS LATENTI (candidate all'harvesting: vendere per caricare lo zainetto) —")
    minus = sorted((p for p in posizioni if p["plus_minus"] < 0), key=lambda p: p["plus_minus"])
    for p in minus:
        print(f"   {(p['descrizione'] or p['isin'])[:36]:<37}{_eur(p['plus_minus']):>13}  ({_pct(p['pct'])})")
    if minus:
        print(f"   {'TOTALE minus latenti':<37}{_eur(a['totale_minus_latenti']):>13}")
        print("   → la minus su vendita è reddito diverso anche per gli ETF; l'Italia non ha la")
        print("     wash-sale rule, ma riacquistare un ETF crea plus future NON compensabili.")
    else:
        print("   nessuna posizione in minus latente.")

    print("\n— PLUS LATENTI (vendere genera imposta, salvo compensazione) —")
    plus = sorted((p for p in posizioni if p["plus_minus"] > 0), key=lambda p: -p["plus_minus"])
    for p in plus:
        if p["categoria_fiscale"] == "reddito_capitale_irpef":
            aliq = "aliquota marginale"
        else:
            aliq = "12,5%" if p["aliquota"] == 12.5 else "26%"
        print(f"   {(p['descrizione'] or p['isin'])[:36]:<37}{_eur(p['plus_minus']):>13}  ({_pct(p['pct'])})  "
              f"{ETICHETTA[p['categoria_fiscale']]}, {aliq}")
    if plus:
        print(f"   {'compensabili (reddito diverso)':<37}{_eur(a['plus_latenti_compensabili']):>13}")
        print(f"   {'NON compensabili (ETF e fondi)':<37}{_eur(a['plus_non_compensabili']):>13}")
        if a["plus_irpef"]:
            print(f"   {'a IRPEF (OICR fuori UE/SEE)':<37}{_eur(a['plus_irpef']):>13}  → quadro RL")
        if a["plus_da_classificare"]:
            print(f"   {'da classificare (non contate)':<37}{_eur(a['plus_da_classificare']):>13}")
    else:
        print("   nessuna posizione in plus latente.")

    dubbi = [p for p in posizioni if p["categoria_fiscale"] == "da_classificare"]
    if dubbi:
        print("\n— DA CLASSIFICARE (indica la categoria nella colonna «tipo fiscale» o chiedi) —")
        for p in dubbi:
            print(f"   {(p['descrizione'] or p['isin'])[:36]:<37} {p['nota']}")

    if zainetto:
        print("\n— ZAINETTO FISCALE PER SCADENZA —")
        print(f"   {'broker':<12}{'anno':>6}{'importo':>13}{'aliq.':>7}  {'scade il':<11}{'stato':<13}{'26%-eq.':>11}")
        for z in sorted(zainetto, key=lambda z: (z["anno"] or 0, str(z["broker"]))):
            aliq = "12,5%" if z["aliquota"] == 12.5 else "26%"
            stato = {"in_scadenza": "IN SCADENZA", "anno_mancante": "anno ignoto"}.get(z["stato"], z["stato"])
            print(f"   {str(z['broker'] or '-')[:11]:<12}{str(z['anno'] or '?'):>6}{_eur(z['importo']):>13}"
                  f"{aliq:>7}  {z['scade_il'] or '-':<11}{stato:<13}{_eur(z['importo_26_equivalente']):>11}")
        print(f"   valide: € {_eur(a['zainetto_totale'])} (26%-equivalente € {_eur(a['zainetto_26_equivalente'])}); "
              f"scadute: € {_eur(a['zainetto_scaduto'])}")
        print(f"\n   OCCASIONE: plus latenti compensabili € {_eur(a['plus_latenti_compensabili'])}, "
              f"zainetto valido € {_eur(a['zainetto_totale'])}.")
        print(f"   Plus realizzabili a imposta ZERO: fino a € {_eur(a['plus_realizzabili_a_costo_zero'])}"
              f" (imposta risparmiata € {_eur(a['imposta_risparmiabile'])}).")
        if len(a.get("per_broker", {})) > 1:
            print("   Lo zainetto è per intermediario, quindi il calcolo è broker per broker:")
            for b, g in a["per_broker"].items():
                print(f"     {str(b):<14} plus compensabili € {_eur(g['plus_latenti_compensabili'])}, "
                      f"zainetto € {_eur(g['zainetto_totale'])} → a imposta zero € {_eur(g['plus_realizzabili_a_costo_zero'])}")
        if a["zainetto_in_scadenza"]:
            print(f"   Priorità: € {_eur(a['zainetto_in_scadenza'])} di minus scadono il 31/12/{anno_rif}.")
    else:
        print("\n   (nessun file zainetto: passa la certificazione come secondo CSV per incrociare")
        print("    le plus latenti con le minus compensabili e le loro scadenze.)")

    if avvisi:
        print("\n— AVVISI —")
        for av in avvisi:
            print(f"   • {av}")
    print("\nStrumento educativo: non costituisce consulenza fiscale o finanziaria. Verifica PMC,")
    print("zainetto e scadenze sul portale del broker prima di operare.\n")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Plus/minus latenti da un estratto CSV del broker, incrociate con lo zainetto "
                    "(regime amministrato). Strumento educativo, non è consulenza fiscale.")
    ap.add_argument("estratto", help="CSV delle posizioni esportato dal broker")
    ap.add_argument("zainetto", nargs="?", help="CSV dello zainetto (anno, importo, aliquota[, broker])")
    ap.add_argument("--anno", type=int, default=datetime.date.today().year,
                    help="anno di riferimento per le scadenze delle minus (default: anno corrente)")
    ap.add_argument("--broker", help="nome del broker, se il CSV non ha la colonna broker")
    ap.add_argument("--json", metavar="PERCORSO",
                    help="scrive il JSON completo su file; con «-» stampa solo il JSON su stdout")
    args = ap.parse_args(argv)
    avvisi = []
    try:
        posizioni = parse_estratto(args.estratto, args.broker, avvisi)
        zainetto = parse_zainetto(args.zainetto, args.anno, args.broker, avvisi) if args.zainetto else []
        allinea_broker(posizioni, zainetto, avvisi)
        if not posizioni:
            raise ErroreInput(f"{args.estratto}: nessuna posizione valutabile (vedi gli avvisi: {avvisi[:2]})")
    except ErroreInput as e:
        print(f"errore: {e}", file=sys.stderr)
        sys.exit(2)
    a = analizza(posizioni, zainetto)
    out = {"anno_riferimento": args.anno, "broker": args.broker, "posizioni": posizioni,
           "zainetto": zainetto, "analisi": a, "avvisi": avvisi}
    if args.json == "-":
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    stampa(posizioni, zainetto, a, args.anno, avvisi)
    if args.json:
        try:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"errore: impossibile scrivere {args.json}: {e}", file=sys.stderr)
            sys.exit(2)
        print(f"JSON completo scritto in {args.json}")


if __name__ == "__main__":
    main()
