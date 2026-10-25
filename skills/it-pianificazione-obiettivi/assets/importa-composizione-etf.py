#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
importa-composizione-etf.py — composizione per settore e paese degli ETF, dal file delle posizioni dell'emittente.

Perché esiste: la diagnosi 4 di capitale-umano.py (sovrapposizione tra il settore del proprio lavoro e il
portafoglio) ha bisogno dei pesi per settore di ogni ETF posseduto. Gli emittenti li pubblicano nel file delle
POSIZIONI (holdings) di ogni fondo, che scarichi tu dalla pagina dell'ETF (pulsante «Posizioni», «Holdings»,
«Portafoglio completo»): lo script lo legge dalla cartella di lavoro, senza rete, aggrega i titoli per settore
GICS e per paese e scrive composizione.csv, che capitale-umano.py legge con --composizione. Il file
dell'emittente resta tuo: il plugin non lo scarica e non lo ridistribuisce. Non è consulenza finanziaria.

Formati: CSV o XLSX di iShares, Xtrackers, Vanguard, Amundi e SPDR, in italiano o in inglese. Il motore è unico:
cerca la riga d'intestazione con tabelle di sinonimi (SINONIMI_COLONNE), quindi il preambolo sopra la tabella e
il disclaimer sotto non contano; una scheda per emittente (SCHEDE) dice solo quello che il motore non deduce
(classificazione dei settori, etichette della data, valori che indicano liquidità e derivati). Se il tuo file usa
nomi diversi, segnala i nomi da aggiungere: lo script si ferma e li elenca, non li indovina.

Regole applicate (references/composizione-etf.md):
- liquidità e derivati (asset class «Cash», «Futures», «FX»…, o peso negativo) si escludono da tutto;
- le righe senza settore o senza paese («unknown», «Unassigned», «-») si escludono solo da quella dimensione;
- i pesi rimasti si rinormalizzano a 100 per dimensione; la quota esclusa è nel report, nel CSV e nel JSON;
- settori: gli 11 GICS con il nome inglese, come in capitale-umano.py; paesi: codice ISO 3166-1 alpha-2;
- un file in classificazione ICB (FTSE) dà solo i paesi: ICB → GICS non si converte senza errore.

Limiti dichiarati: le posizioni sono quelle del fondo a una data (per un ETF sintetico il paniere di collaterale,
non l'esposizione); il paese è quello che l'emittente riporta (domicilio, rischio o negoziazione); niente PDF né
XLS del vecchio Excel; niente lingue diverse da italiano e inglese.

Uso:
    python importa-composizione-etf.py --file FILE --strumento NOME [--file FILE --strumento NOME ...]
                                       [--emittente NOME] [--out composizione.csv] [--json FILE|-]
    (--strumento va scritto come il campo «strumento» delle posizioni del capitale umano; se --out esiste,
     si sostituiscono solo le righe degli strumenti importati)
"""
import csv
import io
import os
import re
import unicodedata
import warnings

from motore_bootstrap import cli, errore

# ── Colonne riconosciute ────────────────────────────────────────────────────
# Per ruolo, i nomi delle intestazioni in italiano e in inglese. L'ordine conta: con due colonne candidate per lo
# stesso ruolo vince quella il cui sinonimo viene prima (in SPDR «Sector Classification» è il settore e
# «Industry Classification» il livello GICS sotto; in Xtrackers «Industry Classification» è il settore).
SINONIMI_COLONNE = {
    "peso": ("weight (%)", "weight", "weighting", "percent of fund", "% of net assets", "% of fund",
             "market value weight", "ponderazione (%)", "ponderazione", "peso (%)", "peso", "% del patrimonio"),
    "settore": ("sector", "gics sector", "sector classification", "industry classification", "settore",
                "settore gics"),
    "paese": ("location", "country", "trade country name", "country of risk", "domicile", "area geografica",
              "paese", "nazione"),
    "asset_class": ("asset class", "type of security", "security type", "asset type", "classe di attivo",
                    "tipo di strumento"),
    "nome": ("name", "security name", "holding name", "nome", "titolo", "emittente"),
}
RIGHE_INTESTAZIONE = 40   # la riga d'intestazione si cerca nelle prime N righe
SEGNAPOSTO = ("", "-", "n/a", "na", "n.d.", "nd")   # peso o nome assente


def normalizza(testo):
    """Confronto tollerante: minuscole, senza accenti, punteggiatura (tranne «%») e spazi compressi."""
    testo = unicodedata.normalize("NFKD", str(testo if testo is not None else ""))
    testo = "".join(c for c in testo if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^\w%]+", " ", testo).split())


_SINONIMI_NORM = {ruolo: tuple(normalizza(s) for s in nomi) for ruolo, nomi in SINONIMI_COLONNE.items()}
_SEGNAPOSTO_NORM = {normalizza(s) for s in SEGNAPOSTO}


def _vuota(cella):
    return cella is None or (isinstance(cella, str) and not cella.strip())


# ── Lettura del file ────────────────────────────────────────────────────────

def leggi_righe(path):
    """Tutte le righe del file come liste di celle, e il titolo del foglio (XLSX) o None.
    XLSX con openpyxl (i numeri arrivano già come numeri); CSV in UTF-8 con BOM o cp1252 (il «CSV» di Excel
    italiano), separatore riconosciuto tra «,», «;» e tab."""
    if not os.path.isfile(path):
        errore(f"--file: file non trovato: {path}")
    with open(path, "rb") as f:
        grezzo = f.read()
    inizio = grezzo[:512].lstrip().lower()
    if inizio.startswith((b"<!doctype", b"<html", b"\xef\xbb\xbf<!doctype", b"\xef\xbb\xbf<html")):
        errore(f"{os.path.basename(path)} è una pagina HTML, non il file delle posizioni: dalla pagina dell'ETF "
               "sul sito dell'emittente usa il pulsante di download delle posizioni (XLSX o CSV)")
    estensione = os.path.splitext(path)[1].lower()
    if estensione == ".xlsx":
        return _righe_xlsx(path, grezzo)
    if estensione in (".csv", ".txt"):
        return _righe_csv(grezzo), None
    errore(f"{os.path.basename(path)}: formato non supportato ({estensione or 'senza estensione'}): "
           "esporta le posizioni in XLSX o CSV")


def _righe_xlsx(path, grezzo):
    import openpyxl
    try:
        with warnings.catch_warnings():   # «Workbook contains no default style»: innocuo, negli export degli emittenti
            warnings.simplefilter("ignore")
            wb = openpyxl.load_workbook(io.BytesIO(grezzo), read_only=True, data_only=True)
    except Exception as e:  # noqa: BLE001 — zip rotto, xls rinominato: qualunque errore di openpyxl è un file illeggibile
        errore(f"{os.path.basename(path)}: XLSX illeggibile ({type(e).__name__}): riscaricalo o esportalo in CSV")
    for ws in wb.worksheets:
        righe = [list(r) for r in ws.iter_rows(values_only=True)]
        if any(not _vuota(c) for r in righe for c in r):
            return righe, ws.title
    errore(f"{os.path.basename(path)}: nessun foglio con dati")


def _righe_csv(grezzo):
    try:
        testo = grezzo.decode("utf-8-sig")
    except UnicodeDecodeError:
        testo = grezzo.decode("cp1252", errors="replace")
    linee = testo.splitlines()
    campione = "\n".join(linee[10:] if len(linee) > 10 else linee)
    try:
        separatore = csv.Sniffer().sniff(campione, delimiters=",;\t").delimiter
    except csv.Error:
        separatore = max(",;\t", key=testo.count)
    return [r for r in csv.reader(linee, delimiter=separatore)]


def trova_intestazione(righe):
    """(indice della riga, ruolo → colonna, ruolo → testo dell'intestazione): la prima riga, tra le prime
    RIGHE_INTESTAZIONE, con una colonna di peso e almeno una tra settore e paese."""
    for i, riga in enumerate(righe[:RIGHE_INTESTAZIONE]):
        celle = [normalizza(c) for c in riga]
        col = {}
        for ruolo, sinonimi in _SINONIMI_NORM.items():
            for s in sinonimi:
                if s in celle:
                    col[ruolo] = celle.index(s)
                    break
        if "peso" in col and ("settore" in col or "paese" in col):
            return i, col, {ruolo: str(riga[j]).strip() for ruolo, j in col.items()}
    viste = []
    for riga in righe[:15]:
        for c in riga:
            if not _vuota(c) and str(c).strip() not in viste:
                viste.append(str(c).strip())
    errore("nessuna intestazione delle posizioni riconosciuta (servono una colonna del peso e una del settore o "
           f"del paese). Celle viste: {', '.join(v[:40] for v in viste[:30]) or 'nessuna'}. Scarica il file delle "
           "posizioni (holdings), non la scheda prodotto né il KID")


def _segnaposto(cella):
    return normalizza(cella) in _SEGNAPOSTO_NORM


def _sembra_numero(cella):
    if isinstance(cella, bool):
        return False
    if isinstance(cella, (int, float)):
        return True
    return isinstance(cella, str) and re.fullmatch(r"\s*[-+]?[\d.,]*\d[\d.,]*\s*%?\s*", cella) is not None


def righe_dati(righe, i_intestazione, col_peso):
    """Le righe della tabella: dopo l'intestazione, fino alla prima riga vuota dopo almeno una riga di dati, o
    alla prima riga il cui peso non è né un numero né un segnaposto (il disclaimer, le note legali)."""
    dati = []
    for riga in righe[i_intestazione + 1:]:
        if all(_vuota(c) for c in riga):
            if dati:
                break
            continue
        peso = riga[col_peso] if col_peso < len(riga) else None
        if col_peso >= len(riga) or not (_sembra_numero(peso) or _segnaposto(peso)):
            break
        dati.append(riga)
    return dati


def virgola_decimale(valori):
    """True se i pesi testuali del file sono all'italiana: in almeno uno il separatore più a destra è la virgola
    («12,40», «1.234,5»). I pesi non arrivano mai alle migliaia, quindi «3,000» non è un caso da distinguere."""
    for v in valori:
        if isinstance(v, str) and "," in v:
            if v.rfind(",") > v.rfind("."):
                return True
    return False


def peso_numerico(valore, virgola):
    """Il peso come numero, nella scala del file (frazione o percento); None per un segnaposto («N/A», «-»).
    Un testo che non è un numero solleva ValueError."""
    if isinstance(valore, (int, float)) and not isinstance(valore, bool):
        return float(valore)
    if _segnaposto(valore):
        return None
    testo = str(valore).strip().rstrip("%").replace(" ", "").replace(" ", "")
    testo = testo.replace(".", "").replace(",", ".") if virgola else testo.replace(",", "")
    return float(testo)


def main():
    args = cli(__doc__.strip().splitlines()[0].split("— ", 1)[1],
               argomenti=[(("--file",), {"action": "append", "required": True, "metavar": "FILE",
                                         "help": "file delle posizioni dell'emittente, CSV o XLSX (ripetibile)"}),
                          (("--strumento",), {"action": "append", "required": True, "metavar": "NOME",
                                              "help": "nome dello strumento, come nelle posizioni (uno per --file)"})])
    for path in args.file:
        righe, _ = leggi_righe(path)
        i, col, testi = trova_intestazione(righe)
        print(f"{os.path.basename(path)}: intestazione alla riga {i + 1}, colonne {testi}")


if __name__ == "__main__":
    main()
