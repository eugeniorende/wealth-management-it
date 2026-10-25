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
import json
import os
import re
import unicodedata
import warnings

from motore_bootstrap import cli, errore, numero, pct, scrivi_json

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
SOGLIA_CLASSIFICATI = 0.5  # sotto questa quota dei titoli classificati la dimensione non si scrive: il 3% del fondo
                           # rinormalizzato a 100 descriverebbe un fondo che non esiste

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
# Tutti i codici ISO 3166-1 alpha-2, una riga per paese: codice;nome italiano;nome inglese|varianti dei file.
# Il codice e il nome italiano valgono anch'essi come sinonimi. L'elenco è completo perché i file reali
# contengono anche paesi minori (in un MSCI World di Xtrackers c'era un titolo dello Zambia allo 0,02%).
_ELENCO_PAESI = """
AD;Andorra;Andorra
AE;Emirati Arabi Uniti;United Arab Emirates|UAE
AF;Afghanistan;Afghanistan
AG;Antigua e Barbuda;Antigua and Barbuda
AI;Anguilla;Anguilla
AL;Albania;Albania
AM;Armenia;Armenia
AO;Angola;Angola
AQ;Antartide;Antarctica
AR;Argentina;Argentina
AS;Samoa Americane;American Samoa
AT;Austria;Austria
AU;Australia;Australia
AW;Aruba;Aruba
AX;Isole Åland;Aland Islands|Åland Islands
AZ;Azerbaigian;Azerbaijan
BA;Bosnia ed Erzegovina;Bosnia and Herzegovina|Bosnia-Herzegovina
BB;Barbados;Barbados
BD;Bangladesh;Bangladesh
BE;Belgio;Belgium
BF;Burkina Faso;Burkina Faso
BG;Bulgaria;Bulgaria
BH;Bahrein;Bahrain|Bahrein
BI;Burundi;Burundi
BJ;Benin;Benin
BL;Saint-Barthélemy;Saint Barthelemy
BM;Bermuda;Bermuda|Bermude
BN;Brunei;Brunei|Brunei Darussalam
BO;Bolivia;Bolivia|Bolivia, Plurinational State of
BQ;Caraibi olandesi;Bonaire, Sint Eustatius and Saba|Caribbean Netherlands
BR;Brasile;Brazil
BS;Bahamas;Bahamas|The Bahamas
BT;Bhutan;Bhutan
BV;Isola Bouvet;Bouvet Island
BW;Botswana;Botswana
BY;Bielorussia;Belarus
BZ;Belize;Belize
CA;Canada;Canada
CC;Isole Cocos;Cocos (Keeling) Islands
CD;Repubblica Democratica del Congo;Congo, Democratic Republic of the|Democratic Republic of the Congo|Congo (Kinshasa)|DR Congo
CF;Repubblica Centrafricana;Central African Republic
CG;Repubblica del Congo;Congo|Republic of the Congo|Congo (Brazzaville)
CH;Svizzera;Switzerland
CI;Costa d'Avorio;Cote d'Ivoire|Côte d'Ivoire|Ivory Coast
CK;Isole Cook;Cook Islands
CL;Cile;Chile
CM;Camerun;Cameroon
CN;Cina;China|People's Republic of China|China (Mainland)|Repubblica popolare cinese|Repubblica Popolare Cinese
CO;Colombia;Colombia
CR;Costa Rica;Costa Rica
CU;Cuba;Cuba
CV;Capo Verde;Cabo Verde|Cape Verde
CW;Curaçao;Curacao|Curaçao
CX;Isola di Natale;Christmas Island
CY;Cipro;Cyprus
CZ;Repubblica Ceca;Czech Republic|Czechia|Cechia
DE;Germania;Germany
DJ;Gibuti;Djibouti
DK;Danimarca;Denmark
DM;Dominica;Dominica
DO;Repubblica Dominicana;Dominican Republic
DZ;Algeria;Algeria
EC;Ecuador;Ecuador
EE;Estonia;Estonia
EG;Egitto;Egypt
EH;Sahara Occidentale;Western Sahara
ER;Eritrea;Eritrea
ES;Spagna;Spain
ET;Etiopia;Ethiopia
FI;Finlandia;Finland
FJ;Figi;Fiji
FK;Isole Falkland;Falkland Islands|Falkland Islands (Malvinas)
FM;Micronesia;Micronesia|Micronesia, Federated States of
FO;Isole Fær Øer;Faroe Islands|Isole Faroe
FR;Francia;France
GA;Gabon;Gabon
GB;Regno Unito;United Kingdom|UK|Great Britain|Gran Bretagna|England|Inghilterra|United Kingdom of Great Britain and Northern Ireland
GD;Grenada;Grenada
GE;Georgia;Georgia
GF;Guyana francese;French Guiana
GG;Guernsey;Guernsey
GH;Ghana;Ghana
GI;Gibilterra;Gibraltar
GL;Groenlandia;Greenland
GM;Gambia;Gambia|The Gambia
GN;Guinea;Guinea
GP;Guadalupa;Guadeloupe
GQ;Guinea Equatoriale;Equatorial Guinea
GR;Grecia;Greece
GS;Georgia del Sud e isole Sandwich australi;South Georgia and the South Sandwich Islands
GT;Guatemala;Guatemala
GU;Guam;Guam
GW;Guinea-Bissau;Guinea-Bissau
GY;Guyana;Guyana
HK;Hong Kong;Hong Kong|Hong Kong SAR|Hong Kong SAR, China|Hong Kong, China
HM;Isole Heard e McDonald;Heard Island and McDonald Islands
HN;Honduras;Honduras
HR;Croazia;Croatia
HT;Haiti;Haiti
HU;Ungheria;Hungary
ID;Indonesia;Indonesia
IE;Irlanda;Ireland
IL;Israele;Israel
IM;Isola di Man;Isle of Man
IN;India;India
IO;Territorio britannico dell'Oceano Indiano;British Indian Ocean Territory
IQ;Iraq;Iraq
IR;Iran;Iran|Iran, Islamic Republic of
IS;Islanda;Iceland
IT;Italia;Italy
JE;Jersey;Jersey
JM;Giamaica;Jamaica
JO;Giordania;Jordan
JP;Giappone;Japan
KE;Kenya;Kenya
KG;Kirghizistan;Kyrgyzstan
KH;Cambogia;Cambodia
KI;Kiribati;Kiribati
KM;Comore;Comoros
KN;Saint Kitts e Nevis;Saint Kitts and Nevis
KP;Corea del Nord;North Korea|Korea (North)|Korea, Democratic People's Republic of
KR;Corea del Sud;Korea (South)|Korea, Republic of|South Korea|Republic of Korea|Korea|Corea|Repubblica di Corea
KW;Kuwait;Kuwait
KY;Isole Cayman;Cayman Islands
KZ;Kazakistan;Kazakhstan
LA;Laos;Laos|Lao People's Democratic Republic
LB;Libano;Lebanon
LC;Santa Lucia;Saint Lucia
LI;Liechtenstein;Liechtenstein
LK;Sri Lanka;Sri Lanka
LR;Liberia;Liberia
LS;Lesotho;Lesotho
LT;Lituania;Lithuania
LU;Lussemburgo;Luxembourg
LV;Lettonia;Latvia
LY;Libia;Libya
MA;Marocco;Morocco
MC;Monaco;Monaco|Principato di Monaco
MD;Moldavia;Moldova|Moldova, Republic of
ME;Montenegro;Montenegro
MF;Saint-Martin;Saint Martin (French part)
MG;Madagascar;Madagascar
MH;Isole Marshall;Marshall Islands
MK;Macedonia del Nord;North Macedonia|Macedonia
ML;Mali;Mali
MM;Myanmar;Myanmar|Burma|Birmania
MN;Mongolia;Mongolia
MO;Macao;Macau|Macao SAR|Macao, China
MP;Isole Marianne Settentrionali;Northern Mariana Islands
MQ;Martinica;Martinique
MR;Mauritania;Mauritania
MS;Montserrat;Montserrat
MT;Malta;Malta
MU;Mauritius;Mauritius
MV;Maldive;Maldives
MW;Malawi;Malawi
MX;Messico;Mexico
MY;Malesia;Malaysia
MZ;Mozambico;Mozambique
NA;Namibia;Namibia
NC;Nuova Caledonia;New Caledonia
NE;Niger;Niger
NF;Isola Norfolk;Norfolk Island
NG;Nigeria;Nigeria
NI;Nicaragua;Nicaragua
NL;Paesi Bassi;Netherlands|The Netherlands|Holland|Olanda
NO;Norvegia;Norway
NP;Nepal;Nepal
NR;Nauru;Nauru
NU;Niue;Niue
NZ;Nuova Zelanda;New Zealand
OM;Oman;Oman
PA;Panama;Panama
PE;Perù;Peru
PF;Polinesia francese;French Polynesia
PG;Papua Nuova Guinea;Papua New Guinea
PH;Filippine;Philippines
PK;Pakistan;Pakistan
PL;Polonia;Poland
PM;Saint-Pierre e Miquelon;Saint Pierre and Miquelon
PN;Isole Pitcairn;Pitcairn
PR;Porto Rico;Puerto Rico
PS;Palestina;Palestine|Palestine, State of
PT;Portogallo;Portugal
PW;Palau;Palau
PY;Paraguay;Paraguay
QA;Qatar;Qatar
RE;Riunione;Reunion|Réunion
RO;Romania;Romania
RS;Serbia;Serbia
RU;Russia;Russian Federation|Federazione Russa
RW;Ruanda;Rwanda
SA;Arabia Saudita;Saudi Arabia
SB;Isole Salomone;Solomon Islands
SC;Seychelles;Seychelles
SD;Sudan;Sudan
SE;Svezia;Sweden
SG;Singapore;Singapore
SH;Sant'Elena;Saint Helena|Saint Helena, Ascension and Tristan da Cunha
SI;Slovenia;Slovenia
SJ;Svalbard e Jan Mayen;Svalbard and Jan Mayen
SK;Slovacchia;Slovakia|Slovak Republic
SL;Sierra Leone;Sierra Leone
SM;San Marino;San Marino
SN;Senegal;Senegal
SO;Somalia;Somalia
SR;Suriname;Suriname
SS;Sudan del Sud;South Sudan
ST;São Tomé e Príncipe;Sao Tome and Principe
SV;El Salvador;El Salvador
SX;Sint Maarten;Sint Maarten (Dutch part)
SY;Siria;Syria|Syrian Arab Republic
SZ;Eswatini;Eswatini|Swaziland
TC;Isole Turks e Caicos;Turks and Caicos Islands
TD;Ciad;Chad
TF;Terre australi e antartiche francesi;French Southern Territories
TG;Togo;Togo
TH;Thailandia;Thailand
TJ;Tagikistan;Tajikistan
TK;Tokelau;Tokelau
TL;Timor Est;Timor-Leste|East Timor
TM;Turkmenistan;Turkmenistan
TN;Tunisia;Tunisia
TO;Tonga;Tonga
TR;Turchia;Turkey|Türkiye|Turkiye
TT;Trinidad e Tobago;Trinidad and Tobago
TV;Tuvalu;Tuvalu
TW;Taiwan;Taiwan|Taiwan, Province of China|Chinese Taipei
TZ;Tanzania;Tanzania|Tanzania, United Republic of
UA;Ucraina;Ukraine
UG;Uganda;Uganda
UM;Isole minori esterne degli Stati Uniti;United States Minor Outlying Islands
US;Stati Uniti;United States|USA|United States of America|Stati Uniti d'America|U.S.
UY;Uruguay;Uruguay
UZ;Uzbekistan;Uzbekistan
VA;Città del Vaticano;Holy See|Vatican City|Vaticano
VC;Saint Vincent e Grenadine;Saint Vincent and the Grenadines
VE;Venezuela;Venezuela|Venezuela, Bolivarian Republic of
VG;Isole Vergini britanniche;Virgin Islands, British|British Virgin Islands
VI;Isole Vergini americane;Virgin Islands, U.S.|US Virgin Islands
VN;Vietnam;Vietnam|Viet Nam
VU;Vanuatu;Vanuatu
WF;Wallis e Futuna;Wallis and Futuna
WS;Samoa;Samoa
YE;Yemen;Yemen
YT;Mayotte;Mayotte
ZA;Sudafrica;South Africa|Sud Africa
ZM;Zambia;Zambia
ZW;Zimbabwe;Zimbabwe
"""
PAESI = {codice: (italiano, tuple(varianti.split("|")))
         for codice, italiano, varianti in (r.split(";") for r in _ELENCO_PAESI.strip().splitlines())}

# ── Righe da escludere ──────────────────────────────────────────────────────
# Asset class o settore che indicano liquidità e derivati: esclusi da tutte e due le dimensioni
VALORI_LIQUIDITA = ("cash", "cash and/or derivatives", "cash and derivatives", "cash collateral and margins",
                    "money market", "fx", "futures", "future", "forward", "forwards", "swap", "swaps",
                    "liquidità", "liquidità e/o derivati", "derivati", "contanti")
# Settore o paese assente: la riga resta nell'altra dimensione
# («European Union», «Supranational»: emittenti sovranazionali o liquidità in euro, nessun paese ISO; «NA» qui è
# un segnaposto, non la Namibia, come nei pesi)
VALORI_NON_CLASSIFICATI = ("unknown", "unassigned", "other", "-", "n/a", "na", "n.d.", "non classificato", "altro",
                           "", "not classified", "european union", "unione europea", "supranational",
                           "sovranazionale", "multinational", "multinazionale")

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
# Tabelle di confronto: nome normalizzato → settore GICS, → codice ISO
SINONIMI_SETTORI = {normalizza(n): g for g in SETTORI_GICS for n in (g,) + _VARIANTI_SETTORI[g]}
SINONIMI_PAESI = {normalizza(n): codice for codice, (it, varianti) in PAESI.items() for n in (codice, it) + varianti}


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
    # Il separatore è quello con cui si trova la riga d'intestazione: in un file italiano ogni riga ha lo stesso
    # numero di virgole decimali, quindi a guardare le sole righe di dati «,» sembrerebbe coerente quanto «;».
    for separatore in (";", ",", "\t"):
        righe = list(csv.reader(linee, delimiter=separatore))
        if _cerca_intestazione(righe) is not None:
            return righe
    return list(csv.reader(linee, delimiter=max(",;\t", key=testo.count)))   # trova_intestazione dirà cosa ha visto


def _cerca_intestazione(righe):
    """Come trova_intestazione, ma None se la riga non c'è (serve anche a scegliere il separatore del CSV)."""
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
    return None


def trova_intestazione(righe):
    """(indice della riga, ruolo → colonna, ruolo → testo dell'intestazione): la prima riga, tra le prime
    RIGHE_INTESTAZIONE, con una colonna di peso e almeno una tra settore e paese."""
    trovata = _cerca_intestazione(righe)
    if trovata is not None:
        return trovata
    viste = []
    for riga in righe[:15]:
        for c in riga:
            if not _vuota(c) and str(c).strip() not in viste:
                viste.append(str(c).strip())
    errore("nessuna intestazione delle posizioni riconosciuta (servono una colonna del peso e una del settore o "
           f"del paese). Celle viste: {', '.join(v[:40] for v in viste[:30]) or 'nessuna'}. Scarica il file delle "
           "posizioni (holdings), non la scheda prodotto né il KID")


def _segnaposto(cella):
    return normalizza(cella) in {normalizza(s) for s in SEGNAPOSTO}


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

_DIMENSIONI = (("settore", "settori"), ("paese", "paesi"))


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

    # le tabelle si leggono qui e non all'import: --set VALORI_LIQUIDITA=… ha effetto
    liquidita = {normalizza(v) for v in tuple(VALORI_LIQUIDITA) + (scheda["liquidita"] if scheda else ())}
    non_classificati = {normalizza(v) for v in VALORI_NON_CLASSIFICATI}
    esclusi = {"liquidita_derivati": 0.0, "settore_non_classificato": 0.0, "paese_non_classificato": 0.0}
    grezzi = {"settore": [], "paese": []}            # (nome normalizzato, nome originale, peso) per dimensione
    n_titoli = 0
    for r, peso in titoli:
        peso /= scala
        classe, settore = normalizza(cella(r, "asset_class")), normalizza(cella(r, "settore"))
        if peso < 0 or classe in liquidita or settore in liquidita:
            esclusi["liquidita_derivati"] += abs(peso)
            continue
        n_titoli += 1
        for dim, _ in _DIMENSIONI:
            if dim not in col:
                continue
            valore = cella(r, dim)
            if normalizza(valore) in non_classificati:
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
    for dim, _ in _DIMENSIONI:
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

    # rinormalizzazione per dimensione, peso decrescente; una dimensione con pochi titoli classificati non si scrive
    risultato, scartate = {}, {}
    for dim, plurale in _DIMENSIONI:
        totale_dim = sum(pesi[dim].values())
        con_dim = totale_dim + esclusi[f"{dim}_non_classificato"]
        if totale_dim > 0 and totale_dim / con_dim < SOGLIA_CLASSIFICATI:
            scartate[dim] = totale_dim / con_dim
            totale_dim = 0
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
    for dim, plurale in _DIMENSIONI:
        if dim not in col:
            avvisi.append(f"il file non ha la colonna del {dim}: {plurale} non scritti")
        elif dim in scartate:
            avvisi.append(f"solo {pct(scartate[dim], 2)} dei titoli ha il {dim}, meno del "
                          f"{numero(SOGLIA_CLASSIFICATI * 100)}%: {plurale} non scritti, quella quota non descrive il fondo")
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


# ── composizione.csv ────────────────────────────────────────────────────────

_INTESTAZIONE_OUT = "strumento;dimensione;voce;peso"


def _linea(campi):
    """Una riga del CSV con «;» (le virgolette solo se un campo contiene «;» o virgolette)."""
    buffer = io.StringIO()
    csv.writer(buffer, delimiter=";", lineterminator="").writerow(campi)
    return buffer.getvalue()


def _peso_vecchio(testo, path, strumento):
    try:
        valore = float(testo.strip().rstrip("%").replace(",", "."))
    except ValueError:
        errore(f"--out {path}: peso {testo!r} non numerico ({strumento}): non lo sovrascrivo")
    return valore, testo.strip().endswith("%")


def leggi_out(path):
    """Il composizione.csv esistente: (commenti in testa, blocchi, vecchio formato?). Un blocco è (strumento,
    righe di testo), con il suo commento «# <strumento>: …» scritto dall'importatore; ogni altro commento è
    libero e forma un blocco senza strumento, che resta al suo posto a ogni reimport.
    Il vecchio formato strumento;settore;peso si converte nel nuovo, con i pesi in percento. Colonne
    sconosciute: ERRORE, perché un file che non si capisce non si sovrascrive."""
    if not os.path.exists(path):
        return [], [], False
    with open(path, "rb") as f:
        grezzo = f.read()
    try:
        testo = grezzo.decode("utf-8-sig")
    except UnicodeDecodeError:
        testo = grezzo.decode("cp1252", errors="replace")
    testa, blocchi, in_sospeso, colonne = [], [], [], None
    vecchi = {}                                     # vecchio formato: strumento → [(settore, peso, in percento?)]
    for linea in testo.splitlines():
        if not linea.strip(" ;\t"):
            continue
        if linea.lstrip().startswith("#"):
            (testa if colonne is None else in_sospeso).append(linea)
            continue
        campi = [c.strip() for c in next(csv.reader([linea], delimiter=";"))]
        if colonne is None:
            colonne = [c.lower() for c in campi if c]
            if colonne not in (["strumento", "settore", "peso"], ["strumento", "dimensione", "voce", "peso"]):
                errore(f"--out {path}: colonne non riconosciute ({';'.join(campi)}): non lo sovrascrivo, scegli "
                       f"un altro --out o usa le colonne {_INTESTAZIONE_OUT}")
            continue
        riga = dict(zip(colonne, campi))
        strumento = riga.get("strumento", "")
        propri = [c for c in in_sospeso if c.startswith(f"# {strumento}:")]
        liberi = [c for c in in_sospeso if c not in propri]
        if liberi:
            blocchi.append((None, liberi))
        if blocchi and blocchi[-1][0] == strumento:
            blocchi[-1][1].extend(propri)
        else:
            blocchi.append((strumento, propri))
        in_sospeso = []
        if colonne[1] == "settore":
            vecchi.setdefault(strumento, []).append((riga.get("settore", ""),) + _peso_vecchio(riga.get("peso", ""), path, strumento))
        else:
            blocchi[-1][1].append(linea)
    if in_sospeso:
        blocchi.append((None, in_sospeso))
    vecchio = colonne is not None and colonne[1] == "settore"
    if vecchio:                                     # pesi in frazione o in percento per strumento, come leggi_composizione
        for strumento, righe in blocchi:
            if strumento is None:
                continue
            voci = vecchi.pop(strumento, [])
            percento = sum(p for _, p, _ in voci) > 1.5
            for settore, peso, con_segno in voci:
                peso = peso if (percento or con_segno) else peso * 100
                righe.append(_linea([strumento, "settore", settore, numero(peso, 2)]))
    return testa, blocchi, vecchio


def _data_italiana(iso):
    return datetime.date.fromisoformat(iso).strftime("%d/%m/%Y")


def _esclusi(c):
    """Le quote escluse, per il commento del CSV e il report; quelle sotto lo 0,005% si scrivono «< 0,01%»
    (un file reale ne ha spesso: righe di diritti o di valuta allo 0,0001%)."""
    quota = lambda x: pct(x, 2) if x >= 0.00005 else "< 0,01%"  # noqa: E731
    return [f"{etichetta} {quota(c['esclusi'][k])}" for k, etichetta in (
        ("liquidita_derivati", "liquidità e derivati"), ("settore_non_classificato", "settore non classificato"),
        ("paese_non_classificato", "paese non classificato")) if c["esclusi"][k] > 0]


def righe_strumento(c, oggi):
    """Il commento e le righe di uno strumento importato, pesi in percento con due decimali."""
    nome = SCHEDE[c["emittente"]]["nome"] if c["emittente"] else "emittente non riconosciuto"
    commento = f"# {c['strumento']}: {nome}, {c['file']}"
    if c["data_posizioni"]:
        commento += f", posizioni al {_data_italiana(c['data_posizioni'])}"
    commento += f", importato il {oggi}"
    esclusi = _esclusi(c)
    if esclusi:
        commento += "; esclusi " + ", ".join(esclusi)
    righe = [commento]
    for dim, plurale in _DIMENSIONI:
        righe += [_linea([c["strumento"], dim, voce, numero(peso * 100, 2)]) for voce, peso in c[plurale].items()]
    return righe


def scrivi_out(path, testa, blocchi, nuovi, oggi):
    """Riscrive composizione.csv: i blocchi degli strumenti importati si tolgono, i nuovi vanno in fondo
    nell'ordine della riga di comando. UTF-8 con BOM e «;»: si apre in Excel italiano."""
    importati = {c["strumento"] for c in nuovi}
    linee = testa + [_INTESTAZIONE_OUT]
    for strumento, righe in blocchi:
        if strumento not in importati:
            linee += righe
    for c in nuovi:
        linee += righe_strumento(c, oggi)
    try:
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            f.write("\n".join(linee) + "\n")
    except OSError as e:
        errore(f"impossibile scrivere {path}: {e.strerror}")


# ── Report ──────────────────────────────────────────────────────────────────

def stampa(composizioni, out, conservati, vecchio):
    print("IMPORTAZIONE DELLA COMPOSIZIONE DEGLI ETF (settori GICS, paesi ISO; pesi rinormalizzati a 100 dopo "
          "liquidità, derivati e righe non classificate)")
    for c in composizioni:
        nome = SCHEDE[c["emittente"]]["nome"] if c["emittente"] else "emittente non riconosciuto"
        come = {"preambolo": "dal preambolo", "nome del file": "dal nome del file", "--emittente": "da --emittente",
                "nessuno": "regole generiche"}[c["riconosciuto_da"]]
        print(f"\n{c['strumento']} — {nome} ({come}), {c['file']}")
        data = f"posizioni al {_data_italiana(c['data_posizioni'])}" if c["data_posizioni"] else "data delle posizioni non indicata nel file"
        colonne = ", ".join(f"{r} «{t}»" for r, t in c["colonne"].items())
        print(f"   {data}; {c['titoli']} titoli; classificazione {c['classificazione']}; colonne lette: {colonne}")
        print(f"   Esclusi: {', '.join(_esclusi(c)) or 'nessuno'}")
        if c["settori"]:
            print("   Settori: " + " · ".join(f"{SETTORI_GICS[k]} {pct(v, 2)}" for k, v in list(c["settori"].items())[:5]))
        if c["paesi"]:
            print("   Paesi: " + " · ".join(f"{PAESI[k][0]} {pct(v, 2)}" for k, v in list(c["paesi"].items())[:5]))
        for a in c["avvisi"]:
            print(f"   ⚠️  {a}")
    print(f"\nScritto {out}: {len(composizioni)} strumenti importati"
          + (f"; conservati senza modifiche: {', '.join(conservati)}" if conservati else ""))
    if vecchio:
        print("   Il file esistente era nel vecchio formato strumento;settore;peso: convertito nel nuovo, stessi pesi.")
    print("Non è consulenza: è la composizione dichiarata dall'emittente alla data del file, da riguardare a ogni revisione.")


def main():
    args = cli(__doc__.strip().splitlines()[0].split("— ", 1)[1], spazio=globals(), json=True,
               argomenti=[(("--file",), {"action": "append", "required": True, "metavar": "FILE",
                                         "help": "file delle posizioni dell'emittente, CSV o XLSX (ripetibile)"}),
                          (("--strumento",), {"action": "append", "required": True, "metavar": "NOME",
                                              "help": "nome dello strumento, come nelle posizioni (uno per --file)"}),
                          (("--emittente",), {"choices": sorted(SCHEDE),
                                              "help": "forza la scheda dell'emittente per tutti i file"}),
                          (("--out",), {"default": "composizione.csv", "metavar": "FILE",
                                        "help": "composizione.csv da scrivere o aggiornare (default nella cartella corrente)"})])
    # il nome si confronta senza spazi ai bordi, come fanno leggi_out() e capitale-umano.py: «ETF World » è «ETF World»
    args.strumento = [n.strip() for n in args.strumento]
    if not all(args.strumento):
        args.parser.error("--strumento vuoto: scrivi il nome dello strumento come nelle posizioni")
    if len(args.file) != len(args.strumento):
        args.parser.error(f"--file e --strumento vanno in coppia: {len(args.file)} file e {len(args.strumento)} strumenti")
    doppi = sorted({s for s in args.strumento if args.strumento.count(s) > 1})
    if doppi:
        args.parser.error(f"--strumento ripetuto: {', '.join(doppi)}")

    # tutto letto e validato prima di scrivere: un errore lascia composizione.csv com'era
    testa, blocchi, vecchio = leggi_out(args.out)
    composizioni = [componi(path, strumento, args.emittente) for path, strumento in zip(args.file, args.strumento)]
    scrivi_out(args.out, testa, blocchi, composizioni, datetime.date.today().strftime("%d/%m/%Y"))
    risultato = {"strumenti": composizioni, "out": args.out}
    if args.json == "-":
        print(json.dumps(risultato, ensure_ascii=False, indent=2))
        return
    conservati = [s for s, _ in blocchi if s is not None and s not in set(args.strumento)]
    stampa(composizioni, args.out, conservati, vecchio)
    if args.json:
        scrivi_json(args.json, risultato)


if __name__ == "__main__":
    main()
