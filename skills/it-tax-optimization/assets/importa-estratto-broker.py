#!/usr/bin/env python3
"""
importa-estratto-broker.py — pilota di import dei dati fiscali dai broker.

Perché esiste (e perché NON è un MCP "live"): i broker italiani non espongono via API
il dato che serve all'ottimizzazione fiscale — lo zainetto e le plus/minus. Quel dato vive
nei REPORT esportabili (sezione "Fiscalità"/certificazione, estratto del portafoglio). Questo
script ingerisce un estratto del portafoglio in CSV — che scarichi tu dal broker, quindi senza
dare credenziali a nessuno — calcola le plus/minus LATENTI per posizione, e le incrocia con lo
zainetto per evidenziare le occasioni di harvesting. Non è consulenza.

La sfida reale è che i tre broker (Directa, Fineco, Trade Republic) hanno formati DIVERSI e non
standard. Per questo il parser NON assume un layout fisso: riconosce i nomi-colonna tipici dei
dossier italiani con sinonimi e matching tollerante (maiuscole/accenti/spazi ignorati). Se il tuo
export usa nomi diversi, basta aggiungerli ai dizionari SINONIMI qui sotto.

Limiti dichiarati del pilota:
- Legge CSV (il formato più robusto). Il parsing dei PDF della certificazione è un passo successivo.
- Lo zainetto (minus realizzate per anno/aliquota) arriva da un secondo CSV opzionale, perché sta
  in un documento diverso (la certificazione) rispetto all'estratto delle posizioni.
- La classificazione reddito diverso/capitale: la plus/minus su VENDITA è reddito diverso
  (compensabile); il parser la tratta così. La trappola dei proventi degli ETF (reddito di
  capitale non compensabile) è un'altra cosa, vedi etf-trap-redditi-capitale.md.

Uso:
    python importa-estratto-broker.py estratto.csv [zainetto.csv]
Dipendenze: solo libreria standard.
"""

import csv
import io
import sys
import json
import unicodedata

# ───────────────────── mappatura colonne (sinonimi, estendibili) ─────────────────────
SINONIMI = {
    "isin":          ["isin", "codice isin", "cod isin"],
    "descrizione":   ["descrizione", "strumento", "titolo", "denominazione", "nome", "prodotto"],
    "quantita":      ["quantita", "quantità", "qta", "q.ta", "q.tà", "pezzi", "numero", "nominale", "quantita'"],
    "prezzo_carico": ["prezzo medio di carico", "prezzo di carico", "pmc", "prezzo carico",
                      "carico medio", "costo medio", "prezzo medio carico", "prz carico"],
    "valore_carico": ["valore di carico", "controvalore di carico", "costo", "valore carico",
                      "controvalore carico", "costo di carico"],
    "prezzo_attuale":["prezzo", "ultimo prezzo", "quotazione", "prezzo di mercato", "prezzo mercato",
                      "ultimo", "prz"],
    "valore_attuale":["controvalore", "valore di mercato", "valore attuale", "controvalore di mercato",
                      "valore mercato", "ctv", "controvalore mercato", "valore"],
    "tipo_fiscale":  ["tipo fiscale", "categoria fiscale", "natura", "natura fiscale"],
}

SINONIMI_ZAIN = {
    "anno":     ["anno", "anno formazione", "anno di formazione", "esercizio", "annualita", "annualità"],
    "importo":  ["importo", "minusvalenza", "minus", "residuo", "importo residuo", "valore", "ammontare"],
    "aliquota": ["aliquota", "aliquota fiscale", "%", "perc", "tipo"],
}


def _norm(s):
    """Normalizza un'intestazione: minuscolo, senza accenti, spazi compattati."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode("ascii")
    return " ".join(s.lower().replace("_", " ").split())


def _mappa_colonne(intestazioni, sinonimi):
    """Mappa ogni campo canonico alla colonna giusta. Strategia greedy: i match ESATTI vincono,
    poi l'alias più lungo che è sottostringa dell'intestazione (gestisce 'Prezzo di carico (EUR)').
    Ogni colonna è assegnata a un solo campo e ogni campo a una sola colonna, per evitare collisioni
    (es. 'Controvalore' non deve finire sia in valore_carico sia in valore_attuale)."""
    norm_head = [_norm(h) for h in intestazioni]
    candidati = []   # (campo, indice_colonna, punteggio)
    for campo, alias in sinonimi.items():
        for a in alias:
            an = _norm(a)
            for idx, h in enumerate(norm_head):
                if an == h:
                    candidati.append((campo, idx, 1000 + len(an)))   # match esatto: priorità alta
                elif an in h:                                         # alias contenuto nell'intestazione
                    candidati.append((campo, idx, len(an)))
    candidati.sort(key=lambda c: -c[2])
    mappa, colonne_usate = {}, set()
    for campo, idx, _ in candidati:
        if campo in mappa or idx in colonne_usate:
            continue
        mappa[campo] = idx
        colonne_usate.add(idx)
    return mappa


def _num(x):
    """Converte un numero in formato italiano o inglese in float (gestisce 1.234,56 e 1,234.56)."""
    if x is None:
        return None
    s = str(x).strip().replace("€", "").replace("EUR", "").replace(" ", "").replace("'", "")
    if not s or s in ("-", "n.d.", "nd", "na"):
        return None
    # se c'è sia '.' che ',' l'ultimo separatore è il decimale
    if "." in s and "," in s:
        if s.rfind(",") > s.rfind("."):      # formato italiano 1.234,56
            s = s.replace(".", "").replace(",", ".")
        else:                                 # formato inglese 1,234.56
            s = s.replace(",", "")
    elif "," in s:                            # solo virgola → decimale italiano
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _leggi_csv(path):
    """Legge un CSV rilevando il delimitatore (',' o ';') e ritorna (intestazioni, righe)."""
    with open(path, encoding="utf-8-sig") as f:
        testo = f.read()
    # sniff del delimitatore
    try:
        dialect = csv.Sniffer().sniff(testo.splitlines()[0], delimiters=";,\t")
        delim = dialect.delimiter
    except Exception:
        delim = ";" if testo.splitlines()[0].count(";") >= testo.splitlines()[0].count(",") else ","
    reader = csv.reader(io.StringIO(testo), delimiter=delim)
    righe = [r for r in reader if any(c.strip() for c in r)]
    return righe[0], righe[1:]


def parse_estratto(path):
    intest, righe = _leggi_csv(path)
    m = _mappa_colonne(intest, SINONIMI)
    if "isin" not in m and "descrizione" not in m:
        raise ValueError("Estratto non riconosciuto: manca sia ISIN sia Descrizione. "
                         "Controlla il file o aggiungi i nomi-colonna ai dizionari SINONIMI.")
    posizioni = []
    for r in righe:
        def get(campo):
            return r[m[campo]] if campo in m and m[campo] < len(r) else None
        qta = _num(get("quantita"))
        prezzo_c = _num(get("prezzo_carico"))
        val_c = _num(get("valore_carico"))
        prezzo_a = _num(get("prezzo_attuale"))
        val_a = _num(get("valore_attuale"))
        # costo: valore di carico se c'è, altrimenti quantità × prezzo di carico
        costo = val_c if val_c is not None else (qta * prezzo_c if qta is not None and prezzo_c is not None else None)
        # valore: controvalore se c'è, altrimenti quantità × prezzo attuale
        valore = val_a if val_a is not None else (qta * prezzo_a if qta is not None and prezzo_a is not None else None)
        if costo is None or valore is None:
            continue  # riga non valutabile (manca il necessario)
        plus_minus = valore - costo
        posizioni.append({
            "isin": (get("isin") or "").strip(),
            "descrizione": (get("descrizione") or "").strip(),
            "quantita": qta,
            "costo": round(costo, 2),
            "valore": round(valore, 2),
            "plus_minus": round(plus_minus, 2),
            "pct": round(plus_minus / costo * 100, 2) if costo else None,
            "tipo_fiscale": (get("tipo_fiscale") or "diverso").strip().lower(),
        })
    return posizioni


def parse_zainetto(path):
    intest, righe = _leggi_csv(path)
    m = _mappa_colonne(intest, SINONIMI_ZAIN)
    zain = []
    for r in righe:
        def get(campo):
            return r[m[campo]] if campo in m and m[campo] < len(r) else None
        imp = _num(get("importo"))
        if imp is None or imp == 0:
            continue
        anno = get("anno")
        zain.append({
            "anno": str(anno).strip() if anno else "?",
            "importo": round(abs(imp), 2),     # lo zainetto è un valore positivo di minus compensabili
            "aliquota": (get("aliquota") or "26%").strip(),
        })
    return zain


def analizza(posizioni, zainetto):
    tot_costo = sum(p["costo"] for p in posizioni)
    tot_valore = sum(p["valore"] for p in posizioni)
    minus_lat = [p for p in posizioni if p["plus_minus"] < 0]
    plus_lat = [p for p in posizioni if p["plus_minus"] > 0]
    tot_minus = sum(p["plus_minus"] for p in minus_lat)
    tot_plus = sum(p["plus_minus"] for p in plus_lat)
    # plus compensabili: solo reddito diverso (la plus su vendita è diverso)
    plus_diverso = sum(p["plus_minus"] for p in plus_lat if "capital" not in p["tipo_fiscale"])
    zain_tot = sum(z["importo"] for z in zainetto)
    return {
        "totale_costo": round(tot_costo, 2),
        "totale_valore": round(tot_valore, 2),
        "plus_minus_netta_latente": round(tot_valore - tot_costo, 2),
        "minus_latenti": sorted(minus_lat, key=lambda p: p["plus_minus"]),
        "plus_latenti": sorted(plus_lat, key=lambda p: -p["plus_minus"]),
        "totale_minus_latenti": round(tot_minus, 2),
        "totale_plus_latenti": round(tot_plus, 2),
        "plus_latenti_compensabili": round(plus_diverso, 2),
        "zainetto_totale": round(zain_tot, 2),
        "plus_realizzabili_a_costo_zero": round(min(plus_diverso, zain_tot), 2),
    }


def stampa(posizioni, zainetto, a):
    print(f"\n{'='*74}")
    print(f"IMPORT ESTRATTO BROKER — {len(posizioni)} posizioni valutate")
    print(f"{'='*74}")
    print(f"Costo totale di carico:  € {a['totale_costo']:>12,.2f}")
    print(f"Valore di mercato:       € {a['totale_valore']:>12,.2f}")
    print(f"Plus/minus netta latente:€ {a['plus_minus_netta_latente']:>12,.2f}")

    print(f"\n— MINUS LATENTI (candidate all'harvesting: vendere per caricare lo zainetto) —")
    if a["minus_latenti"]:
        for p in a["minus_latenti"]:
            nome = (p["descrizione"] or p["isin"])[:34]
            print(f"   {nome:<35}{p['plus_minus']:>12,.2f}  ({p['pct']:+.1f}%)")
        print(f"   {'TOTALE minus latenti':<35}{a['totale_minus_latenti']:>12,.2f}")
        print(f"   → l'Italia non ha la wash-sale rule: puoi vendere e ricomprare subito per")
        print(f"     ricaricare lo zainetto senza perdere la posizione (vedi SKILL.md).")
    else:
        print("   nessuna posizione in minus latente.")

    print(f"\n— PLUS LATENTI (vendere genera imposta, salvo compensazione) —")
    if a["plus_latenti"]:
        for p in a["plus_latenti"][:8]:
            nome = (p["descrizione"] or p["isin"])[:34]
            print(f"   {nome:<35}{p['plus_minus']:>12,.2f}  ({p['pct']:+.1f}%)")
        print(f"   {'TOTALE plus latenti':<35}{a['totale_plus_latenti']:>12,.2f}")
    else:
        print("   nessuna posizione in plus latente.")

    if zainetto:
        print(f"\n— ZAINETTO FISCALE (minus compensabili) —")
        for z in zainetto:
            print(f"   anno {z['anno']}: € {z['importo']:>10,.2f}  (aliquota {z['aliquota']})")
        print(f"   {'TOTALE zainetto':<20}€ {a['zainetto_totale']:>10,.2f}")
        print(f"\n   OCCASIONE: hai € {a['zainetto_totale']:,.2f} di zainetto e "
              f"€ {a['plus_latenti_compensabili']:,.2f} di plus latenti compensabili.")
        print(f"   Puoi realizzare fino a € {a['plus_realizzabili_a_costo_zero']:,.2f} di plus a imposta ZERO,")
        print(f"   compensandole con lo zainetto (occhio all'anno di scadenza delle minus).")
    else:
        print(f"\n   (nessun file zainetto fornito: passa la certificazione come secondo CSV per")
        print(f"    incrociare le plus latenti con le minus compensabili in scadenza.)")
    print()


def main():
    if len(sys.argv) < 2:
        print("Uso: python importa-estratto-broker.py estratto.csv [zainetto.csv]")
        sys.exit(1)
    posizioni = parse_estratto(sys.argv[1])
    zainetto = parse_zainetto(sys.argv[2]) if len(sys.argv) > 2 else []
    a = analizza(posizioni, zainetto)
    stampa(posizioni, zainetto, a)
    # output strutturato per usi a valle (es. la skill /minusvalenze)
    out = {"posizioni": posizioni, "zainetto": zainetto, "analisi": {k: v for k, v in a.items()
           if k not in ("minus_latenti", "plus_latenti")}}
    print("--- JSON strutturato (per /minusvalenze) ---")
    print(json.dumps(out, ensure_ascii=False, indent=2)[:1200] + "\n  [...]")


if __name__ == "__main__":
    main()
