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
import datetime
import io
import os
import re
import unicodedata
import warnings

from motore_bootstrap import cli, errore, numero, pct

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
SOGLIA_AVVISO = 0.05      # avviso se le righe non classificate, o liquidità e derivati, superano il 5% del fondo

# ── Settori GICS ────────────────────────────────────────────────────────────
# Gli 11 settori con il nome inglese degli emittenti e quello italiano del report: gli stessi di SETTORI_GICS in
# capitale-umano.py (un test lo vincola), perché composizione.csv è il suo input.
SETTORI_GICS = {
    "Information Technology": "Tecnologia dell'informazione",
    "Financials": "Finanza",
    "Health Care": "Sanità",
    "Consumer Discretionary": "Beni voluttuari",
    "Communication Services": "Servizi di comunicazione",
    "Industrials": "Industria",
    "Consumer Staples": "Beni di prima necessità",
    "Energy": "Energia",
    "Materials": "Materiali",
    "Utilities": "Servizi di pubblica utilità",
    "Real Estate": "Immobiliare",
}
# Nomi italiani e varianti inglesi dei file, verso il nome GICS (confronto con normalizza())
_VARIANTI_SETTORI = {
    "Information Technology": ("informatica", "tecnologia dell'informazione", "tecnologie dell'informazione",
                               "tecnologie informatiche", "it"),
    "Financials": ("finanza", "finanziari", "finanziario", "financial"),
    "Health Care": ("sanità", "salute", "healthcare", "assistenza sanitaria", "sanitario"),
    "Consumer Discretionary": ("beni voluttuari", "beni di consumo discrezionali", "consumi discrezionali",
                               "beni di consumo voluttuari", "beni di consumo ciclici"),
    "Communication Services": ("servizi di comunicazione", "comunicazioni", "servizi per le comunicazioni",
                               "communication"),
    "Industrials": ("industriali", "industria", "industriale", "beni industriali"),
    "Consumer Staples": ("beni di prima necessità", "beni di consumo di base", "consumi di base",
                         "beni di consumo primari", "beni di consumo non ciclici"),
    "Energy": ("energia", "energetico"),
    "Materials": ("materiali", "materie prime"),
    "Utilities": ("servizi di pubblica utilità", "pubblica utilità", "utility", "servizi pubblici"),
    "Real Estate": ("immobiliare", "immobili", "settore immobiliare"),
}
# GICS prima del 2018: il settore è diventato Communication Services, con un perimetro diverso (avviso)
SETTORI_GICS_VECCHI = {"telecommunication services": "Communication Services",
                       "servizi di telecomunicazione": "Communication Services"}
# Nomi che esistono in un solo sistema: decidono tra GICS e ICB (molti altri sono uguali nei due)
NOMI_ICB_ESCLUSIVI = {"technology", "telecommunications", "basic materials"}
NOMI_GICS_ESCLUSIVI = {"information technology", "communication services", "materials"}

# ── Paesi ───────────────────────────────────────────────────────────────────
# ISO 3166-1 alpha-2 → (nome italiano, nome inglese e varianti dei file). Il codice e il nome italiano valgono
# anch'essi come sinonimi. Copre MSCI ACWI IMI e FTSE All-World, i domicili frequenti e qualche frontiera.
PAESI = {
    "AU": ("Australia", ("Australia",)), "AT": ("Austria", ("Austria",)), "BE": ("Belgio", ("Belgium",)),
    "CA": ("Canada", ("Canada",)), "DK": ("Danimarca", ("Denmark",)), "FI": ("Finlandia", ("Finland",)),
    "FR": ("Francia", ("France",)), "DE": ("Germania", ("Germany",)),
    "HK": ("Hong Kong", ("Hong Kong", "Hong Kong SAR", "Hong Kong SAR, China")),
    "IE": ("Irlanda", ("Ireland",)), "IL": ("Israele", ("Israel",)), "IT": ("Italia", ("Italy",)),
    "JP": ("Giappone", ("Japan",)), "NL": ("Paesi Bassi", ("Netherlands", "The Netherlands", "Holland", "Olanda")),
    "NZ": ("Nuova Zelanda", ("New Zealand",)), "NO": ("Norvegia", ("Norway",)), "PT": ("Portogallo", ("Portugal",)),
    "SG": ("Singapore", ("Singapore",)), "ES": ("Spagna", ("Spain",)), "SE": ("Svezia", ("Sweden",)),
    "CH": ("Svizzera", ("Switzerland",)),
    "GB": ("Regno Unito", ("United Kingdom", "UK", "Great Britain", "Gran Bretagna", "England", "Inghilterra")),
    "US": ("Stati Uniti", ("United States", "USA", "United States of America", "Stati Uniti d'America", "U.S.")),
    "BR": ("Brasile", ("Brazil",)), "CL": ("Cile", ("Chile",)),
    "CN": ("Cina", ("China", "People's Republic of China", "China (Mainland)", "Repubblica popolare cinese")),
    "CO": ("Colombia", ("Colombia",)), "CZ": ("Repubblica Ceca", ("Czech Republic", "Czechia", "Cechia")),
    "EG": ("Egitto", ("Egypt",)), "GR": ("Grecia", ("Greece",)), "HU": ("Ungheria", ("Hungary",)),
    "IN": ("India", ("India",)), "ID": ("Indonesia", ("Indonesia",)),
    "KR": ("Corea del Sud", ("Korea (South)", "Korea, Republic of", "South Korea", "Republic of Korea", "Korea",
                             "Corea", "Repubblica di Corea")),
    "KW": ("Kuwait", ("Kuwait",)), "MY": ("Malesia", ("Malaysia",)), "MX": ("Messico", ("Mexico",)),
    "PE": ("Perù", ("Peru",)), "PH": ("Filippine", ("Philippines",)), "PL": ("Polonia", ("Poland",)),
    "QA": ("Qatar", ("Qatar",)), "SA": ("Arabia Saudita", ("Saudi Arabia",)),
    "ZA": ("Sudafrica", ("South Africa", "Sud Africa")),
    "TW": ("Taiwan", ("Taiwan", "Taiwan, Province of China", "Chinese Taipei")),
    "TH": ("Thailandia", ("Thailand",)), "TR": ("Turchia", ("Turkey", "Türkiye")),
    "AE": ("Emirati Arabi Uniti", ("United Arab Emirates", "UAE")),
    "LU": ("Lussemburgo", ("Luxembourg",)), "BM": ("Bermuda", ("Bermuda",)),
    "KY": ("Isole Cayman", ("Cayman Islands",)), "JE": ("Jersey", ("Jersey",)), "GG": ("Guernsey", ("Guernsey",)),
    "CW": ("Curaçao", ("Curacao",)), "PA": ("Panama", ("Panama",)), "LR": ("Liberia", ("Liberia",)),
    "IM": ("Isola di Man", ("Isle of Man",)), "MO": ("Macao", ("Macau", "Macao SAR")),
    "AR": ("Argentina", ("Argentina",)), "RU": ("Russia", ("Russian Federation", "Federazione Russa")),
    "PK": ("Pakistan", ("Pakistan",)), "VN": ("Vietnam", ("Viet Nam",)), "NG": ("Nigeria", ("Nigeria",)),
    "KZ": ("Kazakistan", ("Kazakhstan",)), "IS": ("Islanda", ("Iceland",)), "MT": ("Malta", ("Malta",)),
    "CY": ("Cipro", ("Cyprus",)), "RO": ("Romania", ("Romania",)), "EE": ("Estonia", ("Estonia",)),
    "LT": ("Lituania", ("Lithuania",)), "LV": ("Lettonia", ("Latvia",)),
    "SK": ("Slovacchia", ("Slovakia", "Slovak Republic")), "SI": ("Slovenia", ("Slovenia",)),
    "HR": ("Croazia", ("Croatia",)), "BG": ("Bulgaria", ("Bulgaria",)), "UY": ("Uruguay", ("Uruguay",)),
    "MA": ("Marocco", ("Morocco",)), "KE": ("Kenya", ("Kenya",)),
}

# ── Righe da escludere ──────────────────────────────────────────────────────
# Asset class o settore che indicano liquidità e derivati: esclusi da tutte e due le dimensioni
VALORI_LIQUIDITA = ("cash", "cash and/or derivatives", "cash and derivatives", "cash collateral and margins",
                    "money market", "fx", "futures", "future", "forward", "forwards", "swap", "swaps",
                    "liquidità", "liquidità e/o derivati", "derivati", "contanti")
# Settore o paese assente: la riga resta nell'altra dimensione
VALORI_NON_CLASSIFICATI = ("unknown", "unassigned", "other", "-", "n/a", "non classificato", "altro", "",
                           "not classified")

# ── Schede degli emittenti ──────────────────────────────────────────────────
# Solo quello che il motore non deduce. «verificato»: mese e fonte della verifica del layout su un file reale.
ETICHETTE_DATA = ("fund holdings as of", "holdings as of", "as of", "posizioni al", "dati al")
SCHEDE = {
    "ishares": {"nome": "iShares", "riconosci": ("ishares", "blackrock"), "classificazione": "GICS",
                "etichette_data": ETICHETTE_DATA, "data_nel_foglio": False, "liquidita": (),
                "verificato": "da confermare"},
    "xtrackers": {"nome": "Xtrackers", "riconosci": ("xtrackers", "dws"), "classificazione": "GICS",
                  "etichette_data": ETICHETTE_DATA, "data_nel_foglio": True, "liquidita": ("warrants",),
                  "verificato": "2026-10, file reale (sito britannico, XLSX)"},
    # Vanguard: GICS o ICB secondo l'indice (FTSE usa ICB); finché un file reale non lo conferma, dai nomi
    "vanguard": {"nome": "Vanguard", "riconosci": ("vanguard",), "classificazione": None,
                 "etichette_data": ETICHETTE_DATA + ("as at",), "data_nel_foglio": False, "liquidita": (),
                 "verificato": "da confermare"},
    "amundi": {"nome": "Amundi", "riconosci": ("amundi", "lyxor"), "classificazione": "GICS",
               "etichette_data": ETICHETTE_DATA, "data_nel_foglio": False, "liquidita": (),
               "verificato": "da confermare"},
    "spdr": {"nome": "SPDR", "riconosci": ("spdr", "state street", "ssga"), "classificazione": "GICS",
             "etichette_data": ETICHETTE_DATA, "data_nel_foglio": False, "liquidita": (),
             "verificato": "2026-10, file reale (sito EMEA, XLSX)"},
}


def normalizza(testo):
    """Confronto tollerante: minuscole, senza accenti, punteggiatura (tranne «%») e spazi compressi."""
    testo = unicodedata.normalize("NFKD", str(testo if testo is not None else ""))
    testo = "".join(c for c in testo if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^\w%]+", " ", testo).split())


_SINONIMI_NORM = {ruolo: tuple(normalizza(s) for s in nomi) for ruolo, nomi in SINONIMI_COLONNE.items()}
_SEGNAPOSTO_NORM = {normalizza(s) for s in SEGNAPOSTO}
# Tabelle di confronto: nome normalizzato → settore GICS, → codice ISO
SINONIMI_SETTORI = {normalizza(n): g for g in SETTORI_GICS for n in (g,) + _VARIANTI_SETTORI[g]}
SINONIMI_PAESI = {normalizza(n): codice for codice, (it, varianti) in PAESI.items() for n in (codice, it) + varianti}
_LIQUIDITA_NORM = {normalizza(v) for v in VALORI_LIQUIDITA}
_NON_CLASSIFICATI_NORM = {normalizza(v) for v in VALORI_NON_CLASSIFICATI}


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
    alla prima riga che è un disclaimer (peso né numerico né segnaposto, al più due celle piene). Una riga con i
    dati di un titolo e un peso non numerico resta: componi() la respinge con il numero di riga."""
    dati = []
    for riga in righe[i_intestazione + 1:]:
        if all(_vuota(c) for c in riga):
            if dati:
                break
            continue
        peso = riga[col_peso] if col_peso < len(riga) else None
        if not (_sembra_numero(peso) or _segnaposto(peso)) and sum(not _vuota(c) for c in riga) <= 2:
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


# ── Emittente e data delle posizioni ────────────────────────────────────────

def _testo_cercabile(testo):
    return " " + normalizza(testo).replace("_", " ") + " "


def riconosci_emittente(preambolo, nome_file, forzato=None):
    """(chiave della scheda o None, come): da --emittente, dalle parole del preambolo, dal nome del file."""
    if forzato:
        return forzato, "--emittente"
    for fonte, testo in (("preambolo", " ".join(str(c) for r in preambolo for c in r if not _vuota(c))),
                         ("nome del file", nome_file)):
        testo = _testo_cercabile(testo)
        for chiave, scheda in SCHEDE.items():
            if any(f" {parola} " in testo for parola in scheda["riconosci"]):
                return chiave, fonte
    return None, "nessuno"


MESI = {"jan": 1, "gen": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "mag": 5, "jun": 6, "giu": 6, "jul": 7,
        "lug": 7, "aug": 8, "ago": 8, "sep": 9, "set": 9, "oct": 10, "ott": 10, "nov": 11, "dec": 12, "dic": 12}


def _data(valore):
    """Una data da una cella: datetime di openpyxl, «2026-09-30», «30/09/2026», «30/set/2026», «22-Oct-2026»,
    «30 Sep 2026», «Sep 30, 2026». None se la cella non ne contiene una."""
    if isinstance(valore, (datetime.datetime, datetime.date)):
        return valore.strftime("%Y-%m-%d")
    testo = str(valore or "")
    tentativi = []
    m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", testo)
    if m:
        tentativi.append((int(m[1]), int(m[2]), int(m[3])))
    m = re.search(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\b", testo)
    if m:
        tentativi.append((int(m[3]), int(m[2]), int(m[1])))
    m = re.search(r"\b(\d{1,2})[\s/.-]+([A-Za-z]{3})[A-Za-z]*\.?[\s/.,-]+(\d{4})\b", testo)
    if m and m[2].lower() in MESI:
        tentativi.append((int(m[3]), MESI[m[2].lower()], int(m[1])))
    m = re.search(r"\b([A-Za-z]{3})[A-Za-z]*\.?\s+(\d{1,2}),?\s+(\d{4})\b", testo)
    if m and m[1].lower() in MESI:
        tentativi.append((int(m[3]), MESI[m[1].lower()], int(m[2])))
    for anno, mese, giorno in tentativi:
        try:
            return datetime.date(anno, mese, giorno).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def data_posizioni(preambolo, titolo_foglio, scheda):
    """La data delle posizioni in ISO, se il file la riporta: nel titolo del foglio (Xtrackers) o accanto a
    un'etichetta del preambolo («Fund Holdings as of», «Posizioni al»…), nella stessa cella o nella successiva."""
    if scheda and scheda["data_nel_foglio"] and _data(titolo_foglio):
        return _data(titolo_foglio)
    etichette = scheda["etichette_data"] if scheda else ETICHETTE_DATA
    for riga in preambolo:
        for j, cella in enumerate(riga):
            n = normalizza(cella)
            if any(n == e or n.startswith(e + " ") for e in etichette):
                for candidata in [cella] + [c for c in riga[j + 1:] if not _vuota(c)][:1]:
                    if _data(candidata):
                        return _data(candidata)
    return None


# ── Composizione di un file ─────────────────────────────────────────────────

DIMENSIONI = (("settore", "settori"), ("paese", "paesi"))


def componi(path, strumento, forzato=None):
    """La composizione di un file delle posizioni: la voce di «strumenti» del JSON (spec §3.4), pesi in frazione
    rinormalizzati a 1 per dimensione e ordinati per peso decrescente. Un errore nei dati ferma lo script."""
    file = os.path.basename(path)
    righe, foglio = leggi_righe(path)
    i, col, testi = trova_intestazione(righe)
    dati = righe_dati(righe, i, col["peso"])
    chiave, riconosciuto_da = riconosci_emittente(righe[:i], file, forzato)
    scheda = SCHEDE.get(chiave)
    avvisi = []
    if scheda is None:
        avvisi.append("emittente non riconosciuto: regole generiche, controlla le esclusioni")
    cella = lambda r, ruolo: r[col[ruolo]] if ruolo in col and col[ruolo] < len(r) else None  # noqa: E731
    virgola = virgola_decimale([cella(r, "peso") for r in dati])

    # pesi numerici; le righe con un segnaposto («N/A») non contano, nemmeno per settore e paese
    titoli = []
    for r in dati:
        try:
            peso = peso_numerico(cella(r, "peso"), virgola)
        except ValueError:
            n = next(k for k, x in enumerate(righe) if x is r) + 1
            errore(f"{file}: peso {cella(r, 'peso')!r} non numerico alla riga {n} ({cella(r, 'nome') or 'senza nome'})")
        if peso is not None:
            titoli.append((r, peso))
    if not titoli:
        errore(f"{file}: nessuna riga con un peso numerico sotto l'intestazione")
    totale = sum(p for _, p in titoli)
    if 0.9 <= totale <= 1.1:
        scala = 1.0
    elif 90 <= totale <= 110:
        scala = 100.0
    else:
        errore(f"{file}: i pesi sommano a {numero(totale, 2)}, né circa 1 né circa 100: file troncato o colonna sbagliata?")

    liquidita_extra = {normalizza(v) for v in (scheda["liquidita"] if scheda else ())}
    esclusi = {"liquidita_derivati": 0.0, "settore_non_classificato": 0.0, "paese_non_classificato": 0.0}
    grezzi = {"settore": [], "paese": []}            # (nome normalizzato, nome originale, peso) per dimensione
    n_titoli = 0
    for r, peso in titoli:
        peso /= scala
        classe, settore = normalizza(cella(r, "asset_class")), normalizza(cella(r, "settore"))
        if peso < 0 or classe in _LIQUIDITA_NORM | liquidita_extra or settore in _LIQUIDITA_NORM:
            esclusi["liquidita_derivati"] += abs(peso)
            continue
        n_titoli += 1
        for dim, _ in DIMENSIONI:
            if dim not in col:
                continue
            valore = cella(r, dim)
            if normalizza(valore) in _NON_CLASSIFICATI_NORM:
                esclusi[f"{dim}_non_classificato"] += peso
            else:
                grezzi[dim].append((normalizza(valore), str(valore).strip(), peso))

    # classificazione: dalla scheda, o dai nomi esclusivi dei due sistemi
    nomi_settori = {n for n, _, _ in grezzi["settore"]}
    classificazione = scheda["classificazione"] if scheda and scheda["classificazione"] else None
    if classificazione is None:
        icb, gics = nomi_settori & NOMI_ICB_ESCLUSIVI, nomi_settori & NOMI_GICS_ESCLUSIVI
        if icb and gics:
            errore(f"{file}: classificazione mista GICS e ICB nei settori ({', '.join(sorted(icb | gics))}): "
                   "controlla di aver scaricato un solo fondo")
        classificazione = "ICB" if icb else "GICS"

    ignoti = {"settore": {}, "paese": {}}
    pesi = {"settore": {}, "paese": {}}
    vecchi = set()
    for dim, _ in DIMENSIONI:
        if dim == "settore" and classificazione == "ICB":
            continue
        for n, originale, peso in grezzi[dim]:
            if dim == "settore":
                voce = SINONIMI_SETTORI.get(n) or SETTORI_GICS_VECCHI.get(n)
                if n in SETTORI_GICS_VECCHI:
                    vecchi.add(originale)
            else:
                voce = SINONIMI_PAESI.get(n)
            if voce is None:
                ignoti[dim][originale] = ignoti[dim].get(originale, 0) + peso
            else:
                pesi[dim][voce] = pesi[dim].get(voce, 0) + peso
    if ignoti["settore"] or ignoti["paese"]:
        parti = [f"{etichetta} non riconosciuti: " + ", ".join(f"{k} ({pct(v, 2)})" for k, v in ignoti[dim].items())
                 for dim, etichetta in (("settore", "settori"), ("paese", "paesi")) if ignoti[dim]]
        errore(f"{file}: {'; '.join(parti)}. Lo script non li indovina: segnalali per aggiungerli ai sinonimi "
               "(references/composizione-etf.md)")

    # rinormalizzazione per dimensione, peso decrescente
    risultato = {}
    for dim, plurale in DIMENSIONI:
        totale_dim = sum(pesi[dim].values())
        risultato[plurale] = {k: v / totale_dim for k, v in sorted(pesi[dim].items(), key=lambda kv: -kv[1])} \
            if totale_dim > 0 else {}
    if not risultato["settori"] and not risultato["paesi"]:
        errore(f"{file}: nessuna riga di titoli con settore o paese dopo le esclusioni (liquidità, derivati, "
               "righe non classificate)")

    if classificazione == "ICB":
        avvisi.append("classificazione ICB, non convertibile in GICS senza errore: settori non scritti, il capitale "
                      "umano tratterà lo strumento come senza composizione settoriale")
    for vecchio in sorted(vecchi):
        avvisi.append(f"«{vecchio}» (GICS prima del 2018) letto come Communication Services: il perimetro non è identico")
    for dim, plurale in DIMENSIONI:
        if dim not in col:
            avvisi.append(f"il file non ha la colonna del {dim}: {plurale} non scritti")
        elif not risultato[plurale] and not (dim == "settore" and classificazione == "ICB"):
            avvisi.append(f"nessun titolo con il {dim}: {plurale} non scritti")
        if esclusi[f"{dim}_non_classificato"] > SOGLIA_AVVISO:
            avvisi.append(f"{dim} non classificato per {pct(esclusi[f'{dim}_non_classificato'], 2)} del fondo, sopra "
                          f"la soglia del 5%: i pesi per {dim} descrivono solo il resto")
    if esclusi["liquidita_derivati"] > SOGLIA_AVVISO:
        avvisi.append(f"liquidità e derivati pesano {pct(esclusi['liquidita_derivati'], 2)}, sopra il 5%: per un ETF "
                      "sintetico il file può contenere il paniere di collaterale, non l'esposizione")

    return {"strumento": strumento, "emittente": chiave, "riconosciuto_da": riconosciuto_da, "file": file,
            "data_posizioni": data_posizioni(righe[:i], foglio, scheda), "classificazione": classificazione,
            "colonne": {k: v for k, v in testi.items() if k != "nome"}, "titoli": n_titoli, "esclusi": esclusi,
            "settori": risultato["settori"], "paesi": risultato["paesi"], "avvisi": avvisi}


def main():
    args = cli(__doc__.strip().splitlines()[0].split("— ", 1)[1],
               argomenti=[(("--file",), {"action": "append", "required": True, "metavar": "FILE",
                                         "help": "file delle posizioni dell'emittente, CSV o XLSX (ripetibile)"}),
                          (("--strumento",), {"action": "append", "required": True, "metavar": "NOME",
                                              "help": "nome dello strumento, come nelle posizioni (uno per --file)"}),
                          (("--emittente",), {"choices": sorted(SCHEDE),
                                              "help": "forza la scheda dell'emittente per tutti i file"}),
                          (("--out",), {"default": "composizione.csv", "metavar": "FILE",
                                        "help": "composizione.csv da scrivere o aggiornare (default nella cartella corrente)"})])
    for path, strumento in zip(args.file, args.strumento):
        c = componi(path, strumento, args.emittente)
        print(f"{strumento}: {len(c['settori'])} settori, {len(c['paesi'])} paesi")


if __name__ == "__main__":
    main()
