#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
look-through-portafoglio.py — cosa possiedi davvero sommando gli ETF: settori, paesi e primi titoli aggregati
su tutte le posizioni, pesati per controvalore.

Perché esiste: composizione.csv (scritto da importa-composizione-etf.py) descrive ogni ETF per settore GICS,
paese e primi titoli, ma nessuno script risponde alla domanda «messi insieme, cosa contengono i miei ETF?».
Questo script legge quel CSV e le posizioni (il --json di importa-estratto-broker.py, o il --dati del capitale
umano), confronta ogni posizione con la composizione per ISIN e poi per nome, e aggrega. Tutto offline: niente
rete, nessun dato lascia la cartella di lavoro. Non è consulenza finanziaria.

Regole applicate (references/composizione-etf.md, «Il look-through del portafoglio»):
- per ogni dimensione (settori, paesi, titoli) contano solo le posizioni che la hanno nel CSV; i pesi si
  rinormalizzano sulla PARTE COPERTA e la copertura (quota del controvalore totale) sta sempre accanto;
- le regioni (Nord America, America Latina e Caraibi, Europa, Asia, Oceania, Africa, Antartide) non si leggono dal
  CSV: derivano dai paesi con la classificazione ONU M49, hanno la stessa copertura dei paesi e sommano a 1;
- i titoli sono i primi N di ogni ETF, quindi la concentrazione che ne risulta è un MINIMO, non il totale;
- lo stesso titolo scritto da due emittenti in modi diversi («Apple Inc.», «APPLE INC») si somma con una chiave
  normalizzata del nome (senza punteggiatura, suffissi societari e classi di azioni); «da» elenca gli ETF che
  contribuiscono, per accorgersi di quelli rimasti separati;
- la stessa posizione su due broker (stesso ISIN) è un'unica esposizione e si somma;
- una posizione senza composizione resta fuori e viene nominata: si importa il file delle posizioni con l'ISIN
  come --strumento, oppure si compilano le righe a mano (una singola azione o un BTP: il paese, il titolo);
- nessun «altro» inventato: ciò che non si sa non entra nei pesi.

Limiti dichiarati: ogni ETF ha la data del suo file, qui non allineata; il fondo pensione non entra; il paese
di una posizione diretta non si deduce dall'ISIN (un ISIN IE può essere un ETF irlandese di titoli americani).

Uso:
    python look-through-portafoglio.py --composizione composizione.csv --posizioni broker.json [--posizioni ...]
                                       [--json FILE|-] [--set N_TITOLI_REPORT=10]
"""
import csv
import importlib.util
import json
import os
import re

from motore_bootstrap import cli, errore, euro, numero, pct, scrivi_json

# ── Costanti sovrascrivibili con --set ───────────────────────────────────────
N_TITOLI_REPORT = 10   # i primi titoli aggregati nel report e nel JSON del cruscotto
N_PAESI_REPORT = 10    # i primi paesi nel report; gli altri in una riga «altri N paesi»
# Parole in coda al nome di un titolo che non distinguono la società: si tolgono prima di sommare
SUFFISSI_SOCIETARI = ("inc", "corp", "corporation", "co", "ltd", "limited", "plc", "sa", "spa", "ag", "se", "nv",
                      "ab", "asa", "oyj", "kk", "holdings", "holding", "group")
# Classi di azioni e forme di quotazione: due classi della stessa società sono la stessa esposizione
CLASSI_AZIONI = ("class a", "class b", "class c", "cl a", "cl b", "cl c", "ord", "adr", "reit")
# Sigle societarie che normalizza() spezza in lettere («S.A.» → «s a»): si tolgono in coda, prima dei suffissi
_SIGLE_SPEZZATE = (("s", "p", "a"), ("s", "a"), ("n", "v"), ("a", "g"))

# ── Tabelle condivise con l'importatore della composizione (stessa cartella) ─
_IMPORTATORE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "importa-composizione-etf.py")


def _importatore():
    """Il modulo importa-composizione-etf.py, per SETTORI_GICS, PAESI e normalizza(): una sola copia delle tabelle."""
    spec = importlib.util.spec_from_file_location("importa_composizione_etf", _IMPORTATORE)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


_imp = _importatore()
SETTORI_GICS, PAESI, normalizza = _imp.SETTORI_GICS, _imp.PAESI, _imp.normalizza
DIMENSIONI = ("settori", "paesi", "titoli")
ISIN_TITOLO = re.compile(r"[A-Z]{2}[A-Z0-9]{9}[0-9]")

# Le regioni geografiche derivano dai paesi, non si leggono dai file degli emittenti. Fonte: «Standard country or area
# codes for statistical use (M49)», Divisione di statistica dell'ONU, vista «Geographic Regions»,
# https://unstats.un.org/unsd/methodology/m49/overview/, letta il 14/11/2026. Le Americhe si dividono nelle
# sottoregioni «Northern America» e «Latin America and the Caribbean»; Europa, Asia, Oceania e Africa sono le regioni M49.
# Due scelte fuori dallo standard (spec §7.3): Taiwan (TW), che M49 non elenca, sta in «asia»; l'Antartide (AQ), che
# M49 lascia senza regione, ha la voce «antartide». Ogni codice di PAESI sta in una sola regione (lo verifica un test).
REGIONI = {
    "nord_america": ("Nord America", tuple("""
    BM CA GL PM US
    """.split())),
    "america_latina": ("America Latina e Caraibi", tuple("""
    AG AI AR AW BB BL BO BQ BR BS BV BZ CL CO CR CU CW DM DO EC FK GD GF GP GS GT GY HN HT JM KN KY LC
    MF MQ MS MX NI PA PE PR PY SR SV SX TC TT UY VC VE VG VI
    """.split())),
    "europa": ("Europa", tuple("""
    AD AL AT AX BA BE BG BY CH CZ DE DK EE ES FI FO FR GB GG GI GR HR HU IE IM IS IT JE LI LT LU LV MC
    MD ME MK MT NL NO PL PT RO RS RU SE SI SJ SK SM UA VA
    """.split())),
    "asia": ("Asia", tuple("""
    AE AF AM AZ BD BH BN BT CN CY GE HK ID IL IN IQ IR JO JP KG KH KP KR KW KZ LA LB LK MM MN MO MV MY
    NP OM PH PK PS QA SA SG SY TH TJ TL TM TR TW UZ VN YE
    """.split())),
    "oceania": ("Oceania", tuple("""
    AS AU CC CK CX FJ FM GU HM KI MH MP NC NF NR NU NZ PF PG PN PW SB TK TO TV UM VU WF WS
    """.split())),
    "africa": ("Africa", tuple("""
    AO BF BI BJ BW CD CF CG CI CM CV DJ DZ EG EH ER ET GA GH GM GN GQ GW IO KE KM LR LS LY MA MG ML MR
    MU MW MZ NA NE NG RE RW SC SD SH SL SN SO SS ST SZ TD TF TG TN TZ UG YT ZA ZM ZW
    """.split())),
    "antartide": ("Antartide", tuple("""
    AQ
    """.split())),
}


def regione_di(codice):
    """La chiave della regione (una di REGIONI) di un codice ISO di PAESI."""
    for chiave, (_, codici) in REGIONI.items():
        if codice in codici:
            return chiave
    raise KeyError(codice)


# ── Chiave dei titoli ────────────────────────────────────────────────────────

def _tabella(nome):
    """Una tabella in testa allo script, letta al momento dell'uso (--set ha effetto) e normalizzata. Una stringa
    al posto della tupla è il refuso più comune (--set "NOME=('spa')" senza la virgola finale)."""
    valore = globals()[nome]
    if isinstance(valore, str) or not isinstance(valore, (tuple, list, set, frozenset)):
        errore(f"--set {nome}: serve una tupla di nomi, per esempio ('{valore}',) con la virgola finale")
    return tuple(normalizza(v) for v in valore)


def chiave_titolo(nome):
    """La chiave con cui lo stesso titolo si somma tra ETF diversi: maiuscole, senza accenti né punteggiatura,
    senza le classi di azioni (ovunque) e i suffissi societari (in coda, ripetutamente). «Apple Inc.» e «APPLE INC»
    danno APPLE; «ALPHABET INC CLASS A» e «Alphabet Inc Class C» danno ALPHABET. Stringa vuota se non resta nulla."""
    suffissi, classi = _tabella("SUFFISSI_SOCIETARI"), _tabella("CLASSI_AZIONI")
    parole = normalizza(nome).split()
    cambiato = True
    while cambiato and parole:
        cambiato = False
        for sigla in _SIGLE_SPEZZATE:
            if len(parole) >= len(sigla) and tuple(parole[-len(sigla):]) == sigla:
                parole = parole[:-len(sigla)]
                cambiato = True
        for classe in classi:
            seq = classe.split()
            i = 0
            while i <= len(parole) - len(seq):
                if parole[i:i + len(seq)] == seq:
                    del parole[i:i + len(seq)]
                    cambiato = True
                else:
                    i += 1
        if parole and parole[-1] in suffissi:
            parole = parole[:-1]
            cambiato = True
    return " ".join(parole).upper()


# ── composizione.csv ─────────────────────────────────────────────────────────

def _numero_csv(testo):
    return float(testo.strip().rstrip("%").replace(",", "."))


def leggi_composizione(path, avvisi=None):
    """{chiave: {"settori": {GICS: frazione}, "paesi": {ISO: frazione}, "titoli": {nome: frazione},
    "isin": {nome del titolo: ISIN}}} dal CSV dell'importatore (strumento;dimensione;voce;peso;isin, o senza l'ultima
    colonna) o dal vecchio strumento;settore;peso (solo settori). L'ISIN è del solo titolo, non è una dimensione;
    le righe «valuta» si saltano (le legge un'altra parte dello script).
    Pesi in percento o in frazione, per strumento e dimensione: settori e paesi come in capitale-umano.py (somma
    sopra 1,5 → percento); i titoli seguono la scala delle altre dimensioni dello strumento, o sono percento se
    uno supera 1; nei casi in cui la scala dei titoli è un'inferenza (pesi tutti fino a 1) un avviso lo dice.
    Colonne, dimensioni, settori, paesi o pesi non riconosciuti fermano lo script."""
    avvisi = [] if avvisi is None else avvisi
    if not os.path.exists(path):
        errore(f"--composizione: file non trovato: {path}")
    with open(path, "rb") as f:
        grezzo = f.read()
    try:
        testo = grezzo.decode("utf-8-sig")
    except UnicodeDecodeError:
        testo = grezzo.decode("cp1252", errors="replace")
    righe = [r for r in testo.splitlines() if r.strip(" ;\t") and not r.lstrip().startswith("#")]
    lettore = csv.DictReader(righe, delimiter=";")
    colonne = [c.strip().lower() for c in lettore.fieldnames or () if c.strip()]
    if colonne in (["strumento", "dimensione", "voce", "peso"], ["strumento", "dimensione", "voce", "peso", "isin"]):
        vecchio = False
    elif colonne == ["strumento", "settore", "peso"]:
        vecchio = True
    else:
        errore(f"--composizione {path}: colonne non riconosciute ({';'.join(colonne)}): servono "
               "strumento;dimensione;voce;peso;isin (da importa-composizione-etf.py), la stessa senza isin o strumento;settore;peso")
    comp, percento = {}, {}
    for r in lettore:
        r = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k is not None}
        if not any(r.values()):
            continue
        strumento = r["strumento"]
        if vecchio:
            dim, voce = "settori", r["settore"]
        else:
            dim = {"settore": "settori", "paese": "paesi", "titolo": "titoli", "valuta": None}.get(r["dimensione"], "?")
            if dim == "?":
                errore(f"--composizione: dimensione {r['dimensione']!r} sconosciuta ({strumento}): "
                       "attese «settore», «paese», «valuta» o «titolo»")
            if dim is None:                         # «valuta»: riconosciuta, per ora saltata
                continue
            voce = r["voce"]
        if dim == "settori" and voce not in SETTORI_GICS:
            errore(f"--composizione: settore {voce!r} non GICS ({strumento}): usa uno di {', '.join(SETTORI_GICS)}")
        if dim == "paesi" and voce not in PAESI:
            errore(f"--composizione: paese {voce!r} non è un codice ISO 3166-1 alpha-2 ({strumento})")
        if dim == "titoli" and not voce:
            errore(f"--composizione: riga «titolo» senza nome ({strumento})")
        try:
            peso = _numero_csv(r["peso"])
        except ValueError:
            errore(f"--composizione: peso {r['peso']!r} non numerico ({strumento})")
        if r["peso"].endswith("%"):
            percento[(strumento, dim)] = True
        scheda = comp.setdefault(strumento, {d: {} for d in DIMENSIONI + ("isin",)})
        voci = scheda[dim]
        voci[voce] = voci.get(voce, 0.0) + peso
        isin = r.get("isin", "").strip().upper()
        if dim == "titoli" and isin:
            if not ISIN_TITOLO.fullmatch(isin):
                errore(f"--composizione: ISIN {r['isin']!r} malformato per il titolo {voce!r} ({strumento})")
            scheda["isin"][voce] = isin
    for strumento, dims in comp.items():
        scala_nota = None
        for dim in ("settori", "paesi"):
            voci = dims[dim]
            if not voci:
                continue
            in_percento = percento.get((strumento, dim)) or sum(voci.values()) > 1.5
            scala_nota = in_percento if scala_nota is None else scala_nota
            if in_percento:
                for k in voci:
                    voci[k] /= 100
            totale = sum(voci.values())
            if abs(totale - 1) > 0.02:
                errore(f"--composizione: i pesi dei {dim} di {strumento!r} sommano a {pct(totale)}, non a 100%")
        titoli = dims["titoli"]
        if titoli:
            esplicito = percento.get((strumento, "titoli"))
            in_percento = esplicito or (scala_nota if scala_nota is not None else max(titoli.values()) > 1)
            if not esplicito and max(titoli.values()) <= 1:
                if scala_nota:
                    avvisi.append(f"{strumento}: i pesi dei titoli non superano 1 e sono letti in percento come i settori e i "
                                  "paesi dello strumento (0,05 = 0,05%): se li hai scritti in frazione, scrivili in percento")
                elif scala_nota is None:
                    avvisi.append(f"{strumento}: sole righe «titolo» con pesi fino a 1, letti come frazione (0,8 = 80%): "
                                  "se intendevi il percento, scrivi «0,8%» o usa valori sopra 1")
            if in_percento:
                for k in titoli:
                    titoli[k] /= 100
            if any(v > 1 or v < 0 for v in titoli.values()):
                errore(f"--composizione: un titolo di {strumento!r} pesa più del 100% del fondo o meno di zero")
    return comp


# ── Posizioni ────────────────────────────────────────────────────────────────

def leggi_posizioni(percorsi):
    """Le posizioni dai JSON (il --json di importa-estratto-broker.py o il --dati del capitale umano), unite per
    ISIN, o per nome se l'ISIN manca: [{"isin", "nome", "valore"}] e gli avvisi (posizioni a valore zero)."""
    unite, ordine, avvisi = {}, [], []
    for percorso in percorsi:
        nome_file = os.path.basename(percorso)
        if not os.path.exists(percorso):
            errore(f"--posizioni: file non trovato: {percorso}")
        try:
            with open(percorso, encoding="utf-8-sig") as f:
                dati = json.load(f)
        except (OSError, ValueError) as e:
            errore(f"--posizioni {nome_file}: non è un JSON leggibile ({e})")
        if not isinstance(dati, dict) or not isinstance(dati.get("posizioni"), list):
            errore(f"--posizioni {nome_file}: manca la lista posizioni: serve il --json di importa-estratto-broker.py "
                   "o il --dati del capitale umano")
        for i, p in enumerate(dati["posizioni"]):
            if not isinstance(p, dict):
                errore(f"--posizioni {nome_file}: posizioni[{i}] non è un oggetto")
            valore = p.get("valore")
            if isinstance(valore, bool) or not isinstance(valore, (int, float)) or valore < 0:
                errore(f"--posizioni {nome_file}: posizioni[{i}].valore = {valore!r}: serve il controvalore in euro, "
                       "un numero non negativo")
            isin = (p.get("isin") or "").strip() or None
            nome = (p.get("descrizione") or p.get("strumento") or "").strip() or isin or f"posizioni[{i}] di {nome_file}"
            if valore == 0:
                avvisi.append(f"posizione a valore zero ignorata: {nome}" + (f" ({isin})" if isin and isin != nome else ""))
                continue
            chiave = ("isin", isin) if isin else ("nome", nome)
            if chiave not in unite:
                unite[chiave] = {"isin": isin, "nome": nome, "valore": 0.0}
                ordine.append(chiave)
            unite[chiave]["valore"] += float(valore)
    return [unite[k] for k in ordine], avvisi


# ── Aggregazione ─────────────────────────────────────────────────────────────

def _chiave(pos, composizione):
    for candidato in (pos["isin"], pos["nome"]):
        if candidato and candidato in composizione:
            return candidato
    return None


def aggrega(posizioni, composizione, csv_path, avvisi):
    """Il look-through: posizioni con la loro chiave, copertura per dimensione, pesi sulla parte coperta,
    titoli sommati per chiave normalizzata (spec §3.2)."""
    totale = sum(p["valore"] for p in posizioni)
    if not posizioni or totale <= 0:
        errore("controvalore totale zero: nessuna posizione con un valore positivo nei file di --posizioni")
    n_report = globals()["N_TITOLI_REPORT"]
    if isinstance(n_report, bool) or not isinstance(n_report, int) or n_report < 1:
        errore(f"N_TITOLI_REPORT = {n_report!r}: serve un intero positivo")

    con, senza = [], []
    for p in posizioni:
        chiave = _chiave(p, composizione)
        voce = {"chiave": chiave or p["isin"] or p["nome"], "nome": p["nome"], "valore": p["valore"],
                "quota": p["valore"] / totale}
        if chiave is None:
            senza.append(voce)
            continue
        c = composizione[chiave]
        voce.update({d: bool(c[d]) for d in DIMENSIONI})
        con.append((voce, c))
    if not con:
        errore(f"nessuna posizione ha una composizione in {csv_path}: importa i file delle posizioni con l'ISIN "
               "come --strumento (--isin di importa-composizione-etf.py), o compila le righe a mano con l'ISIN "
               "della posizione come chiave")

    # una posizione diretta descritta a mano: una sola riga «titolo» al 100% (è la posizione stessa, non un titolo
    # di un ETF): nel JSON «diretto», così il cruscotto non la mostra
    diretti = {chiave for chiave, c in composizione.items() if len(c["titoli"]) == 1 and max(c["titoli"].values()) >= 0.999}
    usate = {v["chiave"] for v, _ in con}
    senza_posizione = sorted(k for k in composizione if k not in usate)

    copertura, pesi = {}, {}
    for d in DIMENSIONI:
        coperte = [(v, c) for v, c in con if v[d]]
        V_d = sum(v["valore"] for v, _ in coperte)
        copertura[d] = V_d / totale
        pesi[d] = {}
        if d == "titoli":
            continue
        for v, c in coperte:
            for voce, peso in c[d].items():
                pesi[d][voce] = pesi[d].get(voce, 0.0) + v["valore"] * peso / V_d
    settori = [{"voce": k, "nome": SETTORI_GICS[k], "peso": w}
               for k, w in sorted(pesi["settori"].items(), key=lambda kv: -kv[1])]
    paesi = [{"voce": k, "nome": PAESI[k][0], "peso": w} for k, w in sorted(pesi["paesi"].items(), key=lambda kv: -kv[1])]
    # le regioni sono i paesi già pesati, sommati per regione: stessa copertura dei paesi
    pesi_regioni = {}
    for k, w in pesi["paesi"].items():
        r_k = regione_di(k)
        pesi_regioni[r_k] = pesi_regioni.get(r_k, 0.0) + w
    regioni = [{"voce": k, "nome": REGIONI[k][0], "peso": w} for k, w in sorted(pesi_regioni.items(), key=lambda kv: -kv[1])]
    copertura["regioni"] = copertura["paesi"]

    # titoli: due righe sono lo stesso titolo se hanno lo stesso ISIN o la stessa chiave del nome (componenti
    # connesse, con una union-find sui nodi «ISIN» e «nome»); il nome viene dallo strumento che contribuisce di più
    padre = {}
    def radice(x):
        padre.setdefault(x, x)
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x
    righe_titoli = []
    V_t = sum(v["valore"] for v, _ in con if v["titoli"])
    for v, c in con:
        for nome, peso in c["titoli"].items():
            k = chiave_titolo(nome)
            if not k:
                avvisi.append(f"titolo «{nome}» di {v['chiave']} ignorato: dopo la pulizia del nome non resta nulla")
                continue
            isin = c["isin"].get(nome)
            radice(("nome", k))
            if isin:
                padre[radice(("isin", isin))] = radice(("nome", k))
            righe_titoli.append((v, nome, k, isin, v["valore"] * peso / V_t))
    titoli = {}
    for v, nome, k, isin, contributo in righe_titoli:
        t = titoli.setdefault(radice(("nome", k)), {"peso": 0.0, "nomi": {}, "da": {}, "isin": set()})
        t["peso"] += contributo
        t["nomi"][nome] = t["nomi"].get(nome, 0.0) + contributo
        t["da"][v["chiave"]] = t["da"].get(v["chiave"], 0.0) + contributo
        if isin:
            t["isin"].add(isin)
    lista_titoli = [{"nome": max(t["nomi"], key=t["nomi"].get), "peso": t["peso"],
                     "da": [s for s, _ in sorted(t["da"].items(), key=lambda kv: -kv[1])],
                     "diretto": all(s in diretti for s in t["da"]), "isin": sorted(t["isin"])}
                    for t in sorted(titoli.values(), key=lambda t: -t["peso"])]
    return {"controvalore_totale": totale, "posizioni": [v for v, _ in con], "senza_composizione": senza,
            "composizioni_senza_posizione": senza_posizione,
            "copertura": copertura, "settori": settori, "paesi": paesi, "regioni": regioni, "titoli": lista_titoli,
            "n_titoli_report": n_report, "quota_primi_titoli": sum(t["peso"] for t in lista_titoli[:n_report]),
            "n_titoli_aggregati": len(lista_titoli), "avvisi": avvisi}


# ── Report ───────────────────────────────────────────────────────────────────

def _nome_chiave(v):
    return v["nome"] if v["chiave"] == v["nome"] else f"{v['nome']} ({v['chiave']})"


def stampa(r):
    n_report = globals()["N_TITOLI_REPORT"]
    con = r["posizioni"]
    V_con = sum(v["valore"] for v in con)
    n_tot = len(con) + len(r["senza_composizione"])
    print("LOOK-THROUGH DEL PORTAFOGLIO — cosa possiedi sommando gli ETF (pesato per controvalore)")
    print(f"   Controvalore: {euro(r['controvalore_totale'])} su {n_tot} posizioni; con composizione: {len(con)} "
          f"({euro(V_con)}, {pct(V_con / r['controvalore_totale'])})")
    if r["senza_composizione"]:
        print("   Senza composizione (importa il file delle posizioni con l'ISIN, o compila le righe a mano): "
              + "; ".join(f"{_nome_chiave(v)} {euro(v['valore'])}, {pct(v['quota'])}" for v in r["senza_composizione"]))
    if r["composizioni_senza_posizione"]:
        print("   Composizioni senza posizione: " + ", ".join(r["composizioni_senza_posizione"])
              + " (chiavi del CSV che nessuna posizione usa, né per ISIN né per nome)")
    for a in r["avvisi"]:
        print(f"   ⚠️  {a}")

    print(f"\n1. SETTORI (copertura {pct(r['copertura']['settori'])} del controvalore)")
    print("   " + (" · ".join(f"{s['nome']} {pct(s['peso'])}" for s in r["settori"])
                   if r["settori"] else "nessuna posizione con i settori"))
    print(f"\n2. PAESI (copertura {pct(r['copertura']['paesi'])})")
    primi, altri = r["paesi"][:N_PAESI_REPORT], r["paesi"][N_PAESI_REPORT:]
    riga = " · ".join(f"{p['nome']} {pct(p['peso'])}" for p in primi)
    if altri:
        riga += f" · altri {len(altri)} paesi {pct(sum(p['peso'] for p in altri))}"
    print("   " + (riga or "nessuna posizione con i paesi"))
    if r["regioni"]:
        print("   Per regione: " + " · ".join(f"{x['nome']} {pct(x['peso'])}" for x in r["regioni"]))
    print(f"\n3. PRIMI TITOLI (copertura {pct(r['copertura']['titoli'])}; i primi di ogni ETF, quindi un minimo della "
          "concentrazione)")
    if r["titoli"]:
        print("   " + " · ".join(f"{t['nome']} {pct(t['peso'])}" + (f" (da {', '.join(t['da'])})" if len(t["da"]) > 1 else "")
                                 for t in r["titoli"][:n_report]))
        print(f"   I primi {min(n_report, len(r['titoli']))} titoli pesano il {pct(r['quota_primi_titoli'])} della parte "
              f"coperta ({numero(r['n_titoli_aggregati'])} titoli distinti in tutto).")
    else:
        print("   nessuna posizione con i titoli")
    print("\nNon è consulenza: è la fotografia delle composizioni alla data dei file degli emittenti, da riguardare "
          "a ogni revisione.")


def main():
    args = cli(__doc__.strip().splitlines()[0].split("— ", 1)[1], spazio=globals(), json=True,
               argomenti=[(("--composizione",), {"required": True, "metavar": "FILE",
                                                 "help": "composizione.csv scritto da importa-composizione-etf.py (o a mano)"}),
                          (("--posizioni",), {"action": "append", "required": True, "metavar": "FILE",
                                              "help": "JSON con la lista posizioni: il --json di importa-estratto-broker.py "
                                                      "o il --dati del capitale umano (ripetibile, un file per broker)"})])
    avvisi = []
    composizione = leggi_composizione(args.composizione, avvisi)
    posizioni, avvisi_posizioni = leggi_posizioni(args.posizioni)
    r = aggrega(posizioni, composizione, args.composizione, avvisi + avvisi_posizioni)
    if args.json == "-":
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return
    stampa(r)
    if args.json:
        scrivi_json(args.json, r)


if __name__ == "__main__":
    main()
