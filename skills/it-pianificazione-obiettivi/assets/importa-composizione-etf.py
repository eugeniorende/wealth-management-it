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

Formati: CSV o XLSX di iShares, Xtrackers, Vanguard, Amundi e SPDR, in italiano, inglese, tedesco o francese (i siti
tedesco e francese di Xtrackers e Amundi). Il motore è unico:
cerca la riga d'intestazione con tabelle di sinonimi (SINONIMI_COLONNE), quindi il preambolo sopra la tabella e
il disclaimer sotto non contano; una scheda per emittente (SCHEDE) dice solo quello che il motore non deduce
(classificazione dei settori, etichette della data, valori che indicano liquidità e derivati). Se il tuo file usa
nomi diversi, segnala i nomi da aggiungere: lo script si ferma e li elenca, non li indovina.

Regole applicate (references/composizione-etf.md):
- liquidità e derivati (asset class «Cash», «Futures», «FX»…, o peso negativo) si escludono da tutto;
- le righe senza settore o senza paese («unknown», «Unassigned», «-») si escludono solo da quella dimensione;
- per le obbligazioni (asset class «Fixed Income», «Reddito fisso»…) il settore non è GICS: contano solo nei paesi;
- i pesi rimasti si rinormalizzano a 100 per dimensione; la quota esclusa è nel report, nel CSV e nel JSON;
- settori: gli 11 GICS con il nome inglese, come in capitale-umano.py; paesi: codice ISO 3166-1 alpha-2;
- un file in classificazione ICB (FTSE) dà solo i paesi: ICB → GICS non si converte senza errore;
- i primi N_TITOLI titoli per peso (liquidità e derivati esclusi) si scrivono come righe «titolo», con il peso
  nel fondo NON rinormalizzato, e l'ISIN del titolo quando il file lo ha: servono al look-through del portafoglio
  (look-through-portafoglio.py). composizione.csv ha cinque colonne: strumento;dimensione;voce;peso;isin.

Limiti dichiarati: le posizioni sono quelle del fondo a una data (per un ETF sintetico il paniere di collaterale,
non l'esposizione); il paese è quello che l'emittente riporta (domicilio, rischio o negoziazione); niente PDF né
XLS del vecchio Excel; niente lingue diverse da italiano, inglese, tedesco e francese.

Uso:
    python importa-composizione-etf.py --file FILE --strumento NOME|ISIN [--file FILE --isin ISIN ...]
                                       [--emittente NOME] [--out composizione.csv] [--json FILE|-]
    (--strumento, o il suo alias --isin, è la chiave con cui le posizioni trovano la composizione: l'ISIN
     quando le posizioni vengono dall'estratto del broker, altrimenti il campo «strumento» delle posizioni del
     capitale umano; se --out esiste, si sostituiscono solo le righe degli strumenti importati)
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
             "market value weight", "ponderazione (%)", "ponderazione", "peso (%)", "peso", "% del patrimonio",
             "% del valore di mercato",
             # tedesco e francese (siti di Xtrackers e Amundi)
             "gewichtung (%)", "gewichtung", "gewicht (%)", "gewicht", "anteil (%)", "anteil", "% des nettovermögens",
             "% des fondsvermögens", "pondération (%)", "pondération", "poids (%)", "poids", "% de l'actif net",
             "% de l'actif"),
    # l'ordine conta: «secteur» prima di «industrie» (il livello sotto), come «sector» prima di «industry classification»
    "settore": ("sector", "gics sector", "sector classification", "industry classification", "settore",
                "settore gics", "secteur", "secteur gics", "classification sectorielle", "branche", "sektor", "industrie"),
    "paese": ("location", "country", "trade country name", "country of risk", "domicile", "area geografica",
              "paese", "nazione", "regione", "land", "standort", "sitzland", "pays", "localisation", "pays de risque"),
    "asset_class": ("asset class", "type of security", "security type", "asset type", "classe di attivo",
                    "tipo di strumento", "anlageklasse", "wertpapierart", "wertpapiertyp", "classe d'actifs",
                    "type de titre", "type d'actif"),
    "nome": ("name", "security name", "holding name", "nome", "nome delle partecipazioni", "titolo", "emittente",
             "bezeichnung", "wertpapier", "nom", "libellé", "titre"),
    "isin": ("isin", "codice isin", "isin code", "code isin"),
}
RIGHE_INTESTAZIONE = 40   # la riga d'intestazione si cerca nelle prime N righe
SEGNAPOSTO = ("", "-", "n/a", "na", "n.d.", "nd")   # peso o nome assente
SOGLIA_AVVISO = 0.05      # avviso se le righe non classificate, o liquidità e derivati, superano il 5% del fondo
SOGLIA_CLASSIFICATI = 0.5  # sotto questa quota dei titoli classificati la dimensione non si scrive: il 3% del fondo
                           # rinormalizzato a 100 descriverebbe un fondo che non esiste
N_TITOLI = 10              # i primi titoli per peso scritti come righe «titolo» (per il look-through del portafoglio)

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
                               "tecnologie informatiche", "it", "informationstechnologie", "informationstechnik",
                               "technologies de l'information", "technologie de l'information"),
    "Financials": ("finanza", "finanziari", "finanziario", "financial", "finanzen", "finanzwesen", "finanzwerte",
                   "finanzdienstleistungen", "finance", "services financiers", "financières", "valeurs financières"),
    "Health Care": ("sanità", "salute", "healthcare", "assistenza sanitaria", "sanitario", "gesundheitswesen",
                    "gesundheit", "santé", "soins de santé"),
    "Consumer Discretionary": ("beni voluttuari", "beni di consumo discrezionali", "consumi discrezionali",
                               "beni di consumo voluttuari", "beni di consumo ciclici", "nicht-basiskonsumgüter",
                               "zyklische konsumgüter", "konsumgüter (zyklisch)", "zyklischer konsum",
                               "consommation discrétionnaire", "biens de consommation cycliques",
                               "biens de consommation discrétionnaire"),
    "Communication Services": ("servizi di comunicazione", "comunicazioni", "comunicazione", "servizi per le comunicazioni",
                               "communication", "kommunikationsdienste", "kommunikationsdienstleistungen",
                               "services de communication"),
    "Industrials": ("industriali", "industria", "industriale", "beni industriali", "industrie", "industriewerte",
                    "industriels", "industriegüter", "industrieunternehmen",
                    "industrali"),   # refuso nel file «Composizione dell'indice» di Amundi (sito italiano, 11/2026)
    "Consumer Staples": ("beni di prima necessità", "beni di consumo di base", "consumi di base",
                         "beni di consumo primari", "beni di consumo non ciclici", "generi di largo consumo",
                         "basiskonsumgüter",
                         "nichtzyklische konsumgüter", "nicht-zyklische konsumgüter", "konsumgüter (nicht-zyklisch)",
                         "nichtzyklischer konsum", "biens de consommation de base", "consommation de base",
                         "biens de consommation non cycliques", "consommation courante"),
    "Energy": ("energia", "energetico", "energie", "énergie"),
    "Materials": ("materiali", "materie prime", "roh-, hilfs- & betriebsstoffe", "roh-, hilfs- und betriebsstoffe",
                  "rohstoffe", "materialien", "material", "matériaux"),
    "Utilities": ("servizi di pubblica utilità", "pubblica utilità", "utility", "servizi pubblici",
                  "imprese di servizi di pubblica utilità", "versorger",
                  "versorgungsbetriebe", "versorgungsunternehmen", "services aux collectivités", "services publics",
                  "services collectifs"),
    "Real Estate": ("immobiliare", "immobili", "settore immobiliare", "immobilien", "immobilier"),
}
# GICS prima del 2018: il settore è diventato Communication Services, con un perimetro diverso (avviso)
SETTORI_GICS_VECCHI = {"telecommunication services": "Communication Services",
                       "servizi di telecomunicazione": "Communication Services",
                       "telekommunikationsdienste": "Communication Services",
                       "services de telecommunication": "Communication Services",
                       "services de telecommunications": "Communication Services"}
# Nomi che esistono in un solo sistema: decidono tra GICS e ICB (molti altri sono uguali nei due).
# In tedesco e francese «Technologie», «Telekommunikation»/«Télécommunications» e «Grundstoffe»/«Matériaux de base»
# sono i nomi ICB (FTSE); «Informationstechnologie»/«Technologies de l'information», «Kommunikationsdienste»/«Services
# de communication» e «Roh-, Hilfs- & Betriebsstoffe»/«Matériaux» quelli GICS (MSCI).
NOMI_ICB_ESCLUSIVI = {"technology", "telecommunications", "basic materials", "technologie", "telekommunikation",
                      "télécommunications", "grundstoffe", "matériaux de base"}
NOMI_GICS_ESCLUSIVI = {"information technology", "communication services", "materials", "informationstechnologie",
                       "kommunikationsdienste", "technologies de l'information", "services de communication",
                       "roh-, hilfs- & betriebsstoffe", "matériaux"}

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
KR;Corea del Sud;Korea (South)|Korea, Republic of|South Korea|Republic of Korea|Korea|Corea|Repubblica di Corea|Sud Corea
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
TH;Thailandia;Thailand|Tailandia
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
# Nomi tedeschi e francesi dei paesi che compaiono nei file reali (i siti tedesco e francese di Xtrackers e Amundi):
# codice;nomi separati da |. I paesi assenti qui si leggono comunque dal codice ISO o dal nome inglese o italiano.
_ELENCO_PAESI_DE_FR = """
AE;Vereinigte Arabische Emirate|Émirats arabes unis
AR;Argentinien|Argentine
AT;Österreich|Autriche
AU;Australien|Australie
BE;Belgien|Belgique
BR;Brasilien|Brésil
CA;Kanada
CH;Schweiz|Suisse
CL;Chile|Chili
CN;China|Chine|Volksrepublik China|Chine continentale
CO;Kolumbien|Colombie
CZ;Tschechien|Tschechische Republik|Tchéquie|République tchèque
DE;Deutschland|Allemagne
DK;Dänemark|Danemark
EG;Ägypten|Égypte
ES;Spanien|Espagne
FI;Finnland|Finlande
FR;Frankreich
GB;Vereinigtes Königreich|Großbritannien|Großbritannien (UK)|Grossbritannien|Royaume-Uni|Grande-Bretagne
GR;Griechenland|Grèce
HK;Hongkong
HU;Ungarn|Hongrie
ID;Indonesien|Indonésie
IE;Irland|Irlande
IL;Israel|Israël
IN;Indien|Inde
IT;Italien|Italie
JP;Japan|Japon
KR;Südkorea|Süd Korea|Korea|Korea, Republik|Republik Korea|Corée du Sud|Corée|Corée, République de|République de Corée
KW;Kuwait|Koweït
LU;Luxemburg
MX;Mexiko|Mexique
MY;Malaysia|Malaisie
NL;Niederlande|Pays-Bas
NO;Norwegen|Norvège
NZ;Neuseeland|Nouvelle-Zélande
PE;Peru|Pérou
PH;Philippinen
PL;Polen|Pologne
PT;Portugal
QA;Katar
RU;Russland|Russie
SA;Saudi-Arabien|Arabie saoudite
SE;Schweden|Suède
SG;Singapur|Singapour
TH;Thailand|Thaïlande
TR;Türkei|Turquie
TW;Taiwan|Taïwan
US;Vereinigte Staaten|Vereinigte Staaten von Amerika|USA|États-Unis|Etats-Unis|États-Unis d'Amérique
ZA;Südafrika|Afrique du Sud
ZM;Sambia|Zambie
KY;Kaimaninseln|Kaiman Inseln|Îles Caïmans|Iles Caimans
BM;Bermudas|Bermudes
VG;Britische Jungferninseln|Îles Vierges britanniques
CW;Curaçao
JE;Jersey
GG;Guernsey|Guernesey
IM;Isle of Man|Île de Man
LI;Liechtenstein
MC;Monaco
MT;Malta|Malte
CY;Zypern|Chypre
IS;Island|Islande
EE;Estland|Estonie
LV;Lettland|Lettonie
LT;Litauen|Lituanie
RO;Rumänien|Roumanie
HR;Kroatien|Croatie
SI;Slowenien|Slovénie
BG;Bulgarien|Bulgarie
RS;Serbien|Serbie
UA;Ukraine
KZ;Kasachstan|Kazakhstan
GE;Georgien|Géorgie
MA;Marokko|Maroc
TN;Tunesien|Tunisie
NG;Nigeria|Nigéria
KE;Kenia|Kenya
MU;Mauritius|Maurice
BH;Bahrain|Bahreïn
OM;Oman
JO;Jordanien|Jordanie
PK;Pakistan
LK;Sri Lanka
BD;Bangladesch|Bangladesh
VN;Vietnam|Viêt Nam|Viet Nam
MO;Macao|Macau
PR;Puerto Rico|Porto Rico
PA;Panama
UY;Uruguay
BS;Bahamas
CR;Costa Rica
EC;Ecuador|Équateur
BO;Bolivien|Bolivie
VE;Venezuela
JM;Jamaika|Jamaïque
DO;Dominikanische Republik|République dominicaine
TT;Trinidad und Tobago|Trinité-et-Tobago
PG;Papua-Neuguinea|Papouasie-Nouvelle-Guinée
"""
_PAESI_DE_FR = {codice: tuple(nomi.split("|")) for codice, nomi in
                (r.split(";") for r in _ELENCO_PAESI_DE_FR.strip().splitlines())}

# ── Righe da escludere ──────────────────────────────────────────────────────
# Asset class o settore che indicano liquidità e derivati: esclusi da tutte e due le dimensioni
VALORI_LIQUIDITA = ("cash", "cash and/or derivatives", "cash and derivatives", "cash collateral and margins",
                    "money market", "fx", "futures", "future", "forward", "forwards", "swap", "swaps",
                    "liquidità", "liquidità e/o derivati", "derivati", "contanti",
                    "barmittel", "kasse", "kassenbestand", "liquidität", "derivate", "devisentermingeschäft",
                    "devisentermingeschäfte", "termingeschäft", "geldmarkt",
                    "liquidités", "trésorerie", "dérivés", "produits dérivés", "contrat à terme", "contrats à terme",
                    "change à terme", "monétaire")
# Asset class a reddito fisso: il settore di un'obbligazione («Treasuries», «Banking», «Titoli di Stato») non è
# GICS e non entra nei settori; il paese sì. Così un ETF obbligazionario dà i paesi e uno misto i settori azionari.
VALORI_OBBLIGAZIONARI = ("fixed income", "bond", "bonds", "obbligazionario", "obbligazioni", "obbligazione",
                         "reddito fisso", "titoli a reddito fisso", "anleihen", "anleihe", "renten", "rentenpapiere",
                         "festverzinslich", "festverzinsliche wertpapiere", "obligations", "obligation", "taux",
                         "revenu fixe", "titres à revenu fixe")
# Settore o paese assente: la riga resta nell'altra dimensione
# («European Union», «Supranational»: emittenti sovranazionali o liquidità in euro, nessun paese ISO; «NA» qui è
# un segnaposto, non la Namibia, come nei pesi)
VALORI_NON_CLASSIFICATI = ("unknown", "unassigned", "other", "-", "n/a", "na", "n.d.", "non classificato", "altro",
                           "", "not classified", "european union", "unione europea", "supranational",
                           "sovranazionale", "multinational", "multinazionale",
                           "unbekannt", "nicht zugeordnet", "nicht klassifiziert", "sonstige", "andere", "k.a.",
                           "europäische union", "inconnu", "non classé", "non attribué", "autre", "autres",
                           "union européenne")

# ── Schede degli emittenti ──────────────────────────────────────────────────
# Solo quello che il motore non deduce. «verificato»: mese e fonte della verifica del layout su un file reale.
ETICHETTE_DATA = ("fund holdings as of", "holdings as of", "as of", "posizioni al", "dati al", "al",
                  "stand", "stand per", "stichtag", "positionen per", "bestände per", "daten per",
                  "positions au", "données au", "composition au", "portefeuille au", "date au")
SCHEDE = {
    # «ishare»: il sito italiano scarica «iShare_<ticker>_holdings.csv», e il CSV italiano non ha il marchio nel preambolo
    "ishares": {"nome": "iShares", "riconosci": ("ishares", "ishare", "blackrock"), "classificazione": "GICS",
                "etichette_extra": (), "data_nel_foglio": False, "liquidita": (),
                "verificato": "2026-11, file reale (sito italiano, CSV)"},
    "xtrackers": {"nome": "Xtrackers", "riconosci": ("xtrackers", "dws"), "classificazione": "GICS",
                  "etichette_extra": (), "data_nel_foglio": True, "liquidita": ("warrants",),
                  "verificato": "2026-10 sito britannico e 2026-11 sito tedesco (XLSX, intestazioni inglesi e valori tedeschi)"},
    # Vanguard: GICS o ICB secondo l'indice (FTSE usa ICB); finché un file reale non lo conferma, dai nomi
    "vanguard": {"nome": "Vanguard", "riconosci": ("vanguard",), "classificazione": None,
                 "etichette_extra": ("as at",), "data_nel_foglio": False, "liquidita": (),
                 "verificato": "2026-11, file reale (sito italiano, XLSX): FTSE All-World in ICB, solo paesi"},
    "amundi": {"nome": "Amundi", "riconosci": ("amundi", "lyxor"), "classificazione": "GICS",
               "etichette_extra": ("dati ritenuti esatti al", "data correct as at"), "data_nel_foglio": False, "liquidita": (),
               "giorno_prima": True,   # «04/11/2026» è il 4 novembre anche sotto «as at» (nome del file e sito lo confermano)
               "verificato": "2026-11, file reali (sito italiano): «Composizione dell'indice» (ripartizione) e «Fund Holdings» (ETF a swap)"},
    "spdr": {"nome": "SPDR", "riconosci": ("spdr", "state street", "ssga"), "classificazione": "GICS",
             "etichette_extra": (), "data_nel_foglio": False, "liquidita": (),
             "verificato": "2026-10, file reale (sito EMEA, XLSX)"},
}


# File di RIPARTIZIONE (Amundi, «Composizione dell'indice»): niente elenco dei titoli, ma un foglio con i pesi per
# settore e uno con i pesi per paese. Si riconoscono dal nome del foglio; la tabella è «nome;peso».
FOGLI_RIPARTIZIONE = {
    "settore": ("ripartizione settoriale", "ripartizione per settore", "sector breakdown", "sector allocation",
                "répartition sectorielle", "sektoraufteilung", "branchenaufteilung"),
    "paese": ("ripartizione geografica", "ripartizione per paese", "geographic breakdown", "country breakdown",
              "geographical breakdown", "répartition géographique", "länderaufteilung", "geografische aufteilung"),
}


def normalizza(testo):
    """Confronto tollerante: minuscole, senza accenti, punteggiatura (tranne «%») e spazi compressi."""
    testo = unicodedata.normalize("NFKD", str(testo if testo is not None else ""))
    testo = "".join(c for c in testo if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^\w%]+", " ", testo).split())


_SINONIMI_NORM = {ruolo: tuple(normalizza(s) for s in nomi) for ruolo, nomi in SINONIMI_COLONNE.items()}
# Tabelle di confronto: nome normalizzato → settore GICS, → codice ISO
SINONIMI_SETTORI = {normalizza(n): g for g in SETTORI_GICS for n in (g,) + _VARIANTI_SETTORI[g]}
SINONIMI_PAESI = {normalizza(n): codice for codice, (it, varianti) in PAESI.items()
                  for n in (codice, it) + varianti + _PAESI_DE_FR.get(codice, ())}


def _vuota(cella):
    return cella is None or (isinstance(cella, str) and not cella.strip())


# ── Lettura del file ────────────────────────────────────────────────────────

def leggi_righe(path, avvisi=None):
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
        return _righe_xlsx(path, grezzo, avvisi)
    if estensione in (".csv", ".txt"):
        return _righe_csv(grezzo), None
    errore(f"{os.path.basename(path)}: formato non supportato ({estensione or 'senza estensione'}): "
           "esporta le posizioni in XLSX o CSV")


def _stili_minimi():
    """Il foglio di stile di un workbook vuoto di openpyxl: valido per costruzione, con il minimo che il lettore esige."""
    import openpyxl
    import zipfile
    vuoto = io.BytesIO()
    openpyxl.Workbook().save(vuoto)
    with zipfile.ZipFile(io.BytesIO(vuoto.getvalue())) as z:
        return z.read("xl/styles.xml")


def _senza_stili(grezzo):
    """Lo stesso XLSX con un foglio di stile minimo al posto di xl/styles.xml: il file «Composizione dell'indice»
    di Amundi ha colori non esadecimali che openpyxl rifiuta, e gli stili non servono per leggere i valori."""
    import zipfile
    stili = _stili_minimi()
    uscita = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(grezzo)) as z, zipfile.ZipFile(uscita, "w", zipfile.ZIP_DEFLATED) as w:
        for nome in z.namelist():
            w.writestr(nome, stili if nome == "xl/styles.xml" else z.read(nome))
    return uscita.getvalue()


def _apri_xlsx(path, grezzo, avvisi):
    import openpyxl
    for tentativo, dati in enumerate((grezzo, None)):
        try:
            with warnings.catch_warnings():   # «Workbook contains no default style»: innocuo, negli export degli emittenti
                warnings.simplefilter("ignore")
                return openpyxl.load_workbook(io.BytesIO(dati if tentativo == 0 else _senza_stili(grezzo)),
                                              read_only=True, data_only=True)
        except ValueError as e:
            # stile non valido («Colors must be aRGB hex values», stylesheet illeggibile): si rilegge senza stili
            if tentativo == 0 and ("style" in str(e).lower() or "color" in str(e).lower()):
                avvisi.append("file letto senza gli stili Excel (il foglio di stile non è valido): una data in formato "
                              "numerico di Excel potrebbe non essere riconosciuta")
                continue
            errore(f"{os.path.basename(path)}: XLSX illeggibile ({type(e).__name__}): riscaricalo o esportalo in CSV")
        except Exception as e:  # noqa: BLE001 — zip rotto, xls rinominato: qualunque errore di openpyxl è un file illeggibile
            errore(f"{os.path.basename(path)}: XLSX illeggibile ({type(e).__name__}): riscaricalo o esportalo in CSV")


def _righe_xlsx(path, grezzo, avvisi=None):
    return _righe_da_wb(path, _apri_xlsx(path, grezzo, [] if avvisi is None else avvisi))


def _righe_da_wb(path, wb):
    for ws in wb.worksheets:
        righe = [list(r) for r in ws.iter_rows(values_only=True)]
        if any(not _vuota(c) for r in righe for c in r):
            return righe, ws.title
    errore(f"{os.path.basename(path)}: nessun foglio con dati")


def leggi_ripartizione(wb):
    """Le tabelle di un file di ripartizione: {"settore": [(nome, peso)], "paese": [...], "preambolo": righe sopra la
    tabella del primo foglio} o None se nessun foglio ha un nome di FOGLI_RIPARTIZIONE. In ogni foglio la tabella
    inizia alla riga che ha una cella di peso (sinonimi di «peso») e una cella di nome prima; finisce alla prima riga
    senza un peso numerico."""
    tabelle, preambolo = {}, None
    for ws in wb.worksheets:
        titolo = normalizza(ws.title)
        dim = next((d for d, nomi in FOGLI_RIPARTIZIONE.items() if any(titolo == normalizza(n) for n in nomi)), None)
        if dim is None:
            continue
        righe = [list(r) for r in ws.iter_rows(values_only=True)]
        for i, r in enumerate(righe):
            piene = [(j, c) for j, c in enumerate(r) if not _vuota(c)]
            j_peso = next((j for j, c in piene if isinstance(c, str) and normalizza(c) in _SINONIMI_NORM["peso"]), None)
            if j_peso is None or not any(j < j_peso for j, _ in piene):
                continue
            j_nome = max(j for j, _ in piene if j < j_peso)
            voci = []
            for r2 in righe[i + 1:]:
                peso = r2[j_peso] if j_peso < len(r2) else None
                if not _sembra_numero(peso):
                    break
                voci.append((str(r2[j_nome] if j_nome < len(r2) else "").strip(), peso))
            tabelle[dim] = {"voci": voci, "testo": str(r[j_nome]).strip(), "peso": str(r[j_peso]).strip()}
            if preambolo is None:
                preambolo = righe[:i]
            break
    return {**tabelle, "preambolo": preambolo or []} if tabelle else None


def leggi_file(path, avvisi):
    """(righe, titolo del foglio, ripartizione): come leggi_righe, ma un XLSX di ripartizione (Amundi) torna come
    tabelle per settore e paese al posto delle righe."""
    if not os.path.isfile(path):
        errore(f"--file: file non trovato: {path}")
    with open(path, "rb") as f:
        grezzo = f.read()
    if os.path.splitext(path)[1].lower() == ".xlsx":
        inizio = grezzo[:512].lstrip().lower()
        if not inizio.startswith((b"<!doctype", b"<html", b"\xef\xbb\xbf<!doctype", b"\xef\xbb\xbf<html")):
            wb = _apri_xlsx(path, grezzo, avvisi)
            ripartizione = leggi_ripartizione(wb)
            if ripartizione:
                return None, None, ripartizione
            righe, foglio = _righe_da_wb(path, wb)      # lo stesso workbook: l'avviso sugli stili una volta sola
            return righe, foglio, None
    righe, foglio = leggi_righe(path, avvisi)
    return righe, foglio, None


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


def _tabella(nome):
    """Una tabella in testa allo script (SEGNAPOSTO, VALORI_LIQUIDITA, NOMI_ICB_ESCLUSIVI…), letta al momento
    dell'uso così che --set abbia effetto, e normalizzata. Una stringa al posto della tupla è il refuso più
    comune: --set "NOME=('a')" senza la virgola finale darebbe le singole lettere."""
    valore = globals()[nome]
    if isinstance(valore, str) or not isinstance(valore, (tuple, list, set, frozenset)):
        errore(f"--set {nome}: serve una tupla di nomi, per esempio ('{valore}',) con la virgola finale")
    return {normalizza(v) for v in valore}


def _segnaposto(cella):
    return normalizza(cella) in _tabella("SEGNAPOSTO")


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
        "lug": 7, "aug": 8, "ago": 8, "sep": 9, "set": 9, "oct": 10, "ott": 10, "nov": 11, "dec": 12, "dic": 12,
        # tedesco e francese («30. Okt. 2026», «30 avr. 2026»); «jui» non si aggiunge: juin e juillet iniziano uguale
        "mrz": 3, "mai": 5, "okt": 10, "dez": 12, "fev": 2, "avr": 4, "aou": 8}


class DataAmbigua(Exception):
    """Una data numerica con giorno e mese entrambi fino a 12 sotto un'etichetta inglese: «03/04/2026» è il
    3 aprile nel Regno Unito e il 4 marzo negli Stati Uniti, e il file non dice quale dei due."""


def _data(valore, giorno_prima=True):
    """Una data da una cella: datetime di openpyxl, «2026-09-30», «30/09/2026», «30/set/2026», «22-Oct-2026»,
    «30 Sep 2026», «Sep 30, 2026». None se la cella non ne contiene una. Una data numerica si legge giorno/mese,
    o mese/giorno se il secondo numero supera 12 («10/24/2026»); con entrambi fino a 12 vale giorno_prima,
    e senza (etichetta inglese) solleva DataAmbigua."""
    if isinstance(valore, (datetime.datetime, datetime.date)):
        return valore.strftime("%Y-%m-%d")
    # senza accenti né dieresi, così «déc.», «août» e «März» entrano nelle regex dei mesi
    testo = unicodedata.normalize("NFKD", str(valore or ""))
    testo = "".join(c for c in testo if not unicodedata.combining(c))
    tentativi = []
    m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", testo)
    if m:
        tentativi.append((int(m[1]), int(m[2]), int(m[3])))
    m = re.search(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\b", testo)
    if m:
        primo, secondo, anno = int(m[1]), int(m[2]), int(m[3])
        if primo > 12 or (secondo <= 12 and giorno_prima):
            tentativi.append((anno, secondo, primo))
        elif secondo > 12:
            tentativi.append((anno, primo, secondo))
        elif not tentativi:
            raise DataAmbigua(m[0])
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
    """(data delle posizioni in ISO o None, avviso o None), se il file la riporta: nel titolo del foglio
    (Xtrackers) o accanto a un'etichetta del preambolo («Fund Holdings as of», «Posizioni al»…), nella stessa
    cella o nella successiva. Sotto un'etichetta inglese («… as of», «as at») una data come 03/04/2026 è ambigua:
    meglio nessuna data che una sbagliata."""
    if scheda and scheda["data_nel_foglio"] and _data(titolo_foglio):
        return _data(titolo_foglio), None
    extra = {normalizza(e) for e in (scheda["etichette_extra"] if scheda else ())}
    etichette = _tabella("ETICHETTE_DATA") | extra
    for riga in preambolo:
        for j, cella in enumerate(riga):
            n = normalizza(cella)
            # le etichette della scheda valgono anche dentro una frase («Please note … Data correct as at 04/11/2026»)
            etichetta = next((e for e in etichette if n == e or n.startswith(e + " ") or (e in extra and f" {e} " in f" {n} ")), None)
            if etichetta is None:
                continue
            inglese = etichetta.split()[-1] in ("of", "at", "on")
            if scheda and scheda.get("giorno_prima") is not None:
                inglese = not scheda["giorno_prima"]   # Amundi scrive gg/mm anche sotto un'etichetta inglese
            for candidata in [cella] + [c for c in riga[j + 1:] if not _vuota(c)][:1]:
                try:
                    data = _data(candidata, giorno_prima=not inglese)
                except DataAmbigua as e:
                    return None, (f"data delle posizioni ambigua («{e}»: giorno/mese o mese/giorno?), non scritta: "
                                  "controllala sul sito dell'emittente")
                if data:
                    return data, None
    return None, None


# ── Composizione di un file ─────────────────────────────────────────────────

_DIMENSIONI = (("settore", "settori"), ("paese", "paesi"))


def componi(path, strumento, forzato=None):
    """La composizione di un file delle posizioni: la voce di «strumenti» del JSON (spec §3.4), pesi in frazione
    rinormalizzati a 1 per dimensione e ordinati per peso decrescente. Un errore nei dati ferma lo script."""
    file = os.path.basename(path)
    avvisi = []
    righe, foglio, ripartizione = leggi_file(path, avvisi)
    if ripartizione is not None:
        return _componi_ripartizione(file, strumento, forzato, ripartizione, avvisi)
    i, col, testi = trova_intestazione(righe)
    dati = righe_dati(righe, i, col["peso"])
    chiave, riconosciuto_da = riconosci_emittente(righe[:i], file, forzato)
    scheda = SCHEDE.get(chiave)
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
    liquidita = _tabella("VALORI_LIQUIDITA") | {normalizza(v) for v in (scheda["liquidita"] if scheda else ())}
    non_classificati = _tabella("VALORI_NON_CLASSIFICATI")
    obbligazionari = _tabella("VALORI_OBBLIGAZIONARI")
    esclusi = {"liquidita_derivati": 0.0, "settore_obbligazionario": 0.0, "settore_non_classificato": 0.0,
               "paese_non_classificato": 0.0}
    grezzi = {"settore": [], "paese": []}            # (nome normalizzato, nome originale, peso) per dimensione
    n_titoli = 0
    candidati = []                                   # (nome, isin, peso) delle righe non escluse, per i primi titoli
    n_primi = globals()["N_TITOLI"]                  # letto qui: --set N_TITOLI=… ha effetto
    if isinstance(n_primi, bool) or not isinstance(n_primi, int) or n_primi < 1:
        errore(f"N_TITOLI = {n_primi!r}: serve un intero positivo (i primi titoli da scrivere)")
    for r, peso in titoli:
        peso /= scala
        classe, settore = normalizza(cella(r, "asset_class")), normalizza(cella(r, "settore"))
        if peso < 0 or classe in liquidita or settore in liquidita:
            esclusi["liquidita_derivati"] += abs(peso)
            continue
        n_titoli += 1
        nome_titolo = cella(r, "nome")
        if "nome" in col and not _vuota(nome_titolo) and not _segnaposto(nome_titolo):
            isin_titolo = cella(r, "isin")
            candidati.append((str(nome_titolo).strip(),
                              None if _vuota(isin_titolo) or _segnaposto(isin_titolo) else str(isin_titolo).strip(),
                              peso))
        for dim, _ in _DIMENSIONI:
            if dim not in col:
                continue
            if dim == "settore" and classe in obbligazionari:
                esclusi["settore_obbligazionario"] += peso
                continue
            valore = cella(r, dim)
            if normalizza(valore) in non_classificati:
                esclusi[f"{dim}_non_classificato"] += peso
            else:
                grezzi[dim].append((normalizza(valore), str(valore).strip(), peso))

    return _finalizza(file, strumento, chiave, riconosciuto_da, scheda, col, testi, grezzi, esclusi, n_titoli,
                      candidati, n_primi, avvisi, righe[:i], foglio)


def _componi_ripartizione(file, strumento, forzato, rip, avvisi):
    """La composizione da un file di ripartizione: i pesi per settore e per paese sono già aggregati; nessun titolo."""
    chiave, riconosciuto_da = riconosci_emittente(rip["preambolo"], file, forzato)
    scheda = SCHEDE.get(chiave)
    if scheda is None:
        avvisi.append("emittente non riconosciuto: regole generiche, controlla le esclusioni")
    non_classificati = _tabella("VALORI_NON_CLASSIFICATI")
    esclusi = {"liquidita_derivati": 0.0, "settore_obbligazionario": 0.0, "settore_non_classificato": 0.0,
               "paese_non_classificato": 0.0}
    grezzi, col, testi = {"settore": [], "paese": []}, {}, {}
    for dim in ("settore", "paese"):
        if dim not in rip:
            continue
        col[dim], testi[dim] = 1, rip[dim]["testo"]
        col["peso"], testi["peso"] = 2, rip[dim]["peso"]
        voci = rip[dim]["voci"]
        if not voci:
            errore(f"{file}: il foglio della ripartizione per {dim} non ha righe con un peso numerico")
        virgola = virgola_decimale([p for _, p in voci])
        pesi = []
        for nome, peso in voci:
            try:
                pesi.append((nome, peso_numerico(peso, virgola)))
            except ValueError:
                errore(f"{file}: peso {peso!r} non numerico nella ripartizione per {dim} ({nome})")
        totale = sum(p for _, p in pesi if p is not None)
        if 0.9 <= totale <= 1.1:
            scala = 1.0
        elif 90 <= totale <= 110:
            scala = 100.0
        else:
            errore(f"{file}: i pesi della ripartizione per {dim} sommano a {numero(totale, 2)}, né circa 1 né circa 100")
        for nome, peso in pesi:
            if peso is None:
                continue
            peso /= scala
            if normalizza(nome) in non_classificati:
                esclusi[f"{dim}_non_classificato"] += peso
            else:
                grezzi[dim].append((normalizza(nome), nome, peso))
    avvisi.append("file di ripartizione dell'indice per settore e paese, non elenco dei titoli: nessun titolo scritto "
                  "(per i primi titoli serve il file delle posizioni) e pesi dell'indice, non del fondo")
    return _finalizza(file, strumento, chiave, riconosciuto_da, scheda, col, testi, grezzi, esclusi, 0, [],
                      globals()["N_TITOLI"], avvisi, rip["preambolo"], None, ripartizione=True)


def _finalizza(file, strumento, chiave, riconosciuto_da, scheda, col, testi, grezzi, esclusi, n_titoli, candidati,
               n_primi, avvisi, preambolo, foglio, ripartizione=False):
    """La coda comune: classificazione, sinonimi, rinormalizzazione, avvisi, primi titoli e data."""
    # classificazione: dalla scheda, o dai nomi esclusivi dei due sistemi
    nomi_settori = {n for n, _, _ in grezzi["settore"]}
    classificazione = scheda["classificazione"] if scheda and scheda["classificazione"] else None
    if classificazione is None:
        icb, gics = nomi_settori & _tabella("NOMI_ICB_ESCLUSIVI"), nomi_settori & _tabella("NOMI_GICS_ESCLUSIVI")
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
        # una voce a peso zero (posizioni allo 0,00% nei file di Vanguard) non si scrive
        risultato[plurale] = {k: v / totale_dim for k, v in sorted(pesi[dim].items(), key=lambda kv: -kv[1]) if v > 0} \
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
        elif not risultato[plurale] and not (dim == "settore" and (classificazione == "ICB"
                                                                   or esclusi["settore_obbligazionario"] > 0)):
            avvisi.append(f"nessun titolo con il {dim}: {plurale} non scritti")
        if esclusi[f"{dim}_non_classificato"] > SOGLIA_AVVISO:
            avvisi.append(f"{dim} non classificato per {pct(esclusi[f'{dim}_non_classificato'], 2)} del fondo, sopra "
                          f"la soglia del 5%: i pesi per {dim} descrivono solo il resto")
    if esclusi["settore_obbligazionario"] > 0:
        avvisi.append(f"titoli obbligazionari per {pct(esclusi['settore_obbligazionario'], 2)} del fondo: il loro "
                      "settore non è GICS e non entra nei settori" + ("" if risultato["settori"] else
                                                                         ", quindi settori non scritti"))
    if esclusi["liquidita_derivati"] > SOGLIA_AVVISO:
        avvisi.append(f"liquidità e derivati pesano {pct(esclusi['liquidita_derivati'], 2)}, sopra il 5%: per un ETF "
                      "sintetico il file può contenere il paniere di collaterale, non l'esposizione")

    # i primi titoli per peso, con il peso nel fondo (non rinormalizzato): un minimo della concentrazione
    if "nome" not in col and not ripartizione:
        avvisi.append("il file non ha la colonna del nome: titoli non scritti")
    primi = [{"nome": n, "isin": isin_t, "peso": p}
             for n, isin_t, p in sorted(candidati, key=lambda t: -t[2])[:n_primi]]

    data, avviso_data = data_posizioni(preambolo, foglio, scheda)
    if avviso_data:
        avvisi.append(avviso_data)
    # replica sintetica dichiarata nel preambolo («Replication method: Synthetic»): le posizioni sono il paniere di
    # collaterale dello swap, non l'esposizione all'indice (un S&P 500 a swap può tenere titoli europei)
    testo_preambolo = " ".join(normalizza(c) for r in preambolo for c in r if not _vuota(c))
    sintetica = any(f" {parola}" in f" {testo_preambolo}" for parola in ("synthetic", "sintetic", "synthetisch", "synthetique"))
    if sintetica:
        avvisi.append("replica sintetica dichiarata nel file: le posizioni sono il paniere di collaterale dello swap, non "
                      "l'esposizione all'indice; settori, paesi e titoli descrivono il collaterale")
    return {"strumento": strumento, "emittente": chiave, "riconosciuto_da": riconosciuto_da, "file": file,
            "data_posizioni": data, "classificazione": classificazione,
            "colonne": {k: v for k, v in testi.items() if k != "nome"}, "titoli": n_titoli, "esclusi": esclusi,
            "settori": risultato["settori"], "paesi": risultato["paesi"], "primi_titoli": primi,
            "replica_sintetica": sintetica, "avvisi": avvisi}


# ── composizione.csv ────────────────────────────────────────────────────────

_INTESTAZIONE_OUT = "strumento;dimensione;voce;peso;isin"


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
    """Il composizione.csv esistente: (commenti in testa, blocchi, formato trovato). Un blocco è (strumento,
    righe di testo), con il suo commento «# <strumento>: …» scritto dall'importatore; ogni altro commento è
    libero e forma un blocco senza strumento, che resta al suo posto a ogni reimport.
    Il formato trovato è None (file assente), «settore» (strumento;settore;peso), «quattro»
    (strumento;dimensione;voce;peso) o «cinque» (con l'isin). I primi due si convertono nel formato a cinque
    colonne, con i pesi in percento e il quinto campo vuoto. Colonne sconosciute: ERRORE, perché un file che non
    si capisce non si sovrascrive."""
    if not os.path.exists(path):
        return [], [], None
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
            if colonne not in (["strumento", "settore", "peso"], ["strumento", "dimensione", "voce", "peso"],
                               ["strumento", "dimensione", "voce", "peso", "isin"]):
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
            if len(colonne) == 4:                   # quattro colonne: il quinto campo, vuoto, si aggiunge
                linea = _linea(campi[:4] + [""])
            blocchi[-1][1].append(linea)
    if in_sospeso:
        blocchi.append((None, in_sospeso))
    formato = None if colonne is None else {3: "settore", 4: "quattro", 5: "cinque"}[len(colonne)]
    if formato == "settore":                        # pesi in frazione o in percento per strumento, come leggi_composizione
        for strumento, righe in blocchi:
            if strumento is None:
                continue
            voci = vecchi.pop(strumento, [])
            percento = sum(p for _, p, _ in voci) > 1.5
            for settore, peso, con_segno in voci:
                peso = peso if (percento or con_segno) else peso * 100
                righe.append(_linea([strumento, "settore", settore, numero(peso, 2), ""]))
    return testa, blocchi, formato


def _data_italiana(iso):
    return datetime.date.fromisoformat(iso).strftime("%d/%m/%Y")


def _esclusi(c):
    """Le quote escluse, per il commento del CSV e il report; quelle sotto lo 0,005% si scrivono «< 0,01%»
    (un file reale ne ha spesso: righe di diritti o di valuta allo 0,0001%)."""
    quota = lambda x: pct(x, 2) if x >= 0.00005 else "< 0,01%"  # noqa: E731
    return [f"{etichetta} {quota(c['esclusi'][k])}" for k, etichetta in (
        ("liquidita_derivati", "liquidità e derivati"), ("settore_obbligazionario", "obbligazioni senza settore GICS"),
        ("settore_non_classificato", "settore non classificato"),
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
    if c["replica_sintetica"]:
        commento += "; replica sintetica: posizioni del collaterale, non esposizione all'indice"
    righe = [commento]
    for dim, plurale in _DIMENSIONI:
        righe += [_linea([c["strumento"], dim, voce, numero(peso * 100, 2), ""]) for voce, peso in c[plurale].items()]
    righe += [_linea([c["strumento"], "titolo", t["nome"], numero(t["peso"] * 100, 2), t["isin"] or ""])
              for t in c["primi_titoli"]]
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


def verifica_destinazione(path, opzione):
    """Prima di leggere o scrivere qualsiasi cosa: la destinazione è un file in una cartella che esiste ed è
    scrivibile. Così un --json sbagliato non lascia composizione.csv già riscritto, né un --out sbagliato il JSON."""
    if os.path.isdir(path):
        errore(f"{opzione} {path}: è una cartella, serve il percorso di un file")
    cartella = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(cartella):
        errore(f"impossibile scrivere {path}: la cartella {cartella} non esiste")
    if not os.access(path if os.path.exists(path) else cartella, os.W_OK):
        errore(f"impossibile scrivere {path}: permesso negato")


# ── Report ──────────────────────────────────────────────────────────────────

def stampa(composizioni, out, conservati, formato):
    print("IMPORTAZIONE DELLA COMPOSIZIONE DEGLI ETF (settori GICS, paesi ISO; pesi rinormalizzati a 100 dopo "
          "liquidità, derivati e righe non classificate)")
    for c in composizioni:
        nome = SCHEDE[c["emittente"]]["nome"] if c["emittente"] else "emittente non riconosciuto"
        come = {"preambolo": "dal preambolo", "nome del file": "dal nome del file", "--emittente": "da --emittente",
                "nessuno": "regole generiche"}[c["riconosciuto_da"]]
        print(f"\n{c['strumento']} — {nome} ({come}), {c['file']}")
        data = f"posizioni al {_data_italiana(c['data_posizioni'])}" if c["data_posizioni"] else "data delle posizioni non indicata nel file"
        colonne = ", ".join(f"{r.replace('_', ' ')} «{t}»" for r, t in c["colonne"].items())
        print(f"   {data}; {c['titoli']} titoli; classificazione {c['classificazione']}; colonne lette: {colonne}")
        print(f"   Esclusi: {', '.join(_esclusi(c)) or 'nessuno'}")
        if c["settori"]:
            print("   Settori: " + " · ".join(f"{SETTORI_GICS[k]} {pct(v, 2)}" for k, v in list(c["settori"].items())[:5]))
        if c["paesi"]:
            print("   Paesi: " + " · ".join(f"{PAESI[k][0]} {pct(v, 2)}" for k, v in list(c["paesi"].items())[:5]))
        if c["primi_titoli"]:
            print("   Primi titoli: " + " · ".join(f"{t['nome']} {pct(t['peso'], 2)}" for t in c["primi_titoli"][:5])
                  + " (peso nel fondo)")
        for a in c["avvisi"]:
            print(f"   ⚠️  {a}")
    importati = "1 strumento importato" if len(composizioni) == 1 else f"{len(composizioni)} strumenti importati"
    print(f"\nScritto {out}: {importati}"
          + (f"; conservati senza modifiche: {', '.join(conservati)}" if conservati else ""))
    if formato == "settore":
        print("   Il file esistente era nel vecchio formato strumento;settore;peso: convertito nel nuovo, stessi pesi.")
    elif formato == "quattro":
        print("   Il file esistente aveva quattro colonne: aggiunta la colonna isin, stesse righe.")
    print("Non è consulenza: è la composizione dichiarata dall'emittente alla data del file, da riguardare a ogni revisione.")


def main():
    args = cli(__doc__.strip().splitlines()[0].split("— ", 1)[1], spazio=globals(), json=True,
               argomenti=[(("--file",), {"action": "append", "required": True, "metavar": "FILE",
                                         "help": "file delle posizioni dell'emittente, CSV o XLSX (ripetibile)"}),
                          (("--strumento", "--isin"), {"action": "append", "required": True, "metavar": "NOME|ISIN",
                                                        "help": "nome o ISIN dello strumento, come nelle posizioni (uno per "
                                                                "--file); con le posizioni dell'estratto del broker usa l'ISIN"}),
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
    verifica_destinazione(args.out, "--out")
    if args.json and args.json != "-":
        verifica_destinazione(args.json, "--json")
    testa, blocchi, formato = leggi_out(args.out)
    composizioni = [componi(path, strumento, args.emittente) for path, strumento in zip(args.file, args.strumento)]
    scrivi_out(args.out, testa, blocchi, composizioni, datetime.date.today().strftime("%d/%m/%Y"))
    risultato = {"strumenti": composizioni, "out": args.out}
    if args.json == "-":
        print(json.dumps(risultato, ensure_ascii=False, indent=2))
        return
    conservati = [s for s, _ in blocchi if s is not None and s not in set(args.strumento)]
    stampa(composizioni, args.out, conservati, formato)
    if args.json:
        scrivi_json(args.json, risultato)


if __name__ == "__main__":
    main()
