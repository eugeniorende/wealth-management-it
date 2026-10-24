#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
motore_bootstrap.py — motore comune dei Monte Carlo del plugin (block bootstrap).

⚠ COPIA SINCRONIZZATA: questo file esiste identico in
    skills/it-pianificazione/assets/  e  skills/it-pianificazione-obiettivi/assets/
  perché ogni skill resta autosufficiente (script + motore + rendimenti-storici.csv
  si copiano insieme). Se lo modifichi, replica la modifica nell'altra skill:
  tests/run_tests.py verifica l'identità delle due copie e fallisce se divergono.

Contenuto:
  - carica_storico(path_csv): serie annuali NOMINALI in dollari USA (azionario,
    obbligazionario); un percorso relativo si risolve rispetto a questa cartella, non alla cwd
  - carica_inflazione(path_csv) / deflaziona(rendimenti, inflazione): inflazione USA
    storica (CPI-U dicembre su dicembre) e rendimenti reali anno per anno
  - indici_bootstrap(n_hist, n_sim, anni, blocco): campionamento a blocchi circolari
  - blocchi_bootstrap(port, n_sim, anni, blocco): rendimenti di portafoglio campionati
  - pctl(a, p): percentile come float
  - cli(descrizione, spazio, argomenti, json): riga di comando comune (--help, argomenti dichiarati,
    --set, --json, codici d'uscita 0/1/2), UTF-8 su stdout; errore(msg, codice) per uscire pulito
  - numero / euro / pct: numeri in formato italiano (punto per le migliaia, virgola per i decimali)
  - applica_override(spazio): override '--set NOME=VALORE' delle costanti da riga di comando
  - scrivi_json: i risultati chiave su file JSON (il flag --json lo dà cli())
  - verifica_intestazioni_obiettivi(ws): guardia sul layout del pianificatore Excel
  - leggi_pianificatore(path): l'unico lettore del pianificatore compilato (parametri, profili,
    obiettivi), con le stesse regole per i quattro script degli obiettivi
  - quota_glide / frazioni_glide / pmt_glide / crescita_glide / leggi_finestra_derisk /
    finestra_nel_foglio / scarti_dal_foglio: il glide path del pianificatore obiettivi, unica
    definizione per foglio, Monte Carlo, glide path e allocatore

Natura della serie (rendimenti-storici.csv): rendimenti NOMINALI in dollari USA di un
investitore USA (S&P 500 con dividendi, T-Bond decennale), senza componente di cambio. Chi
ricentra la media su un rendimento atteso (Monte Carlo obiettivi e pensione) ne usa solo la
forma; chi usa la serie grezza contro spese o target in euro di oggi deve deflazionarla anno
per anno con la colonna inflazione (carica_inflazione + deflaziona), non con un'inflazione
costante che cancellerebbe gli anni '70 (lo fa decumulo-obiettivi.py).

Il campionamento usa np.random (generatore legacy): il seed fissato dagli script
con np.random.seed(...) governa anche il motore. La sequenza di chiamate random è
UNA randint per blocco — invariante da preservare nei refactor (i risultati con seed
devono restare riproducibili).

Nota di perimetro: decumulo-obiettivi.py usa da qui il caricamento e la deflazione della
serie, ma una variante propria del campionamento (Generator con blocchi non circolari);
unificarla cambierebbe i suoi percorsi simulati, quindi resta deliberatamente fuori.
Le funzioni del glide path non usano numeri casuali: non toccano l'invariante sopra.
"""

import argparse
import ast
import os
import sys

import numpy as np


# ── Riga di comando comune ──────────────────────────────────────────────────
# Convenzione dei codici d'uscita di tutti gli script del plugin:
#   0  riuscito
#   1  errore nei dati o nei parametri: file mancante o illeggibile, valori incoerenti,
#      costante --set sconosciuta (il messaggio inizia con «ERRORE:» su stderr)
#   2  riga di comando non riconosciuta: flag ignoto, argomento obbligatorio mancante (argparse)

def configura_stdout():
    """UTF-8 su stdout e stderr qualunque sia la console: su Windows con cp1252 i simboli €, →, ≈
    farebbero crashare la stampa; i caratteri che la console non sa mostrare diventano «?»."""
    for flusso in (sys.stdout, sys.stderr):
        try:
            flusso.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):   # flusso sostituito (test, pipe chiusa): si lascia com'è
            pass


def errore(messaggio, codice=1):
    """Stampa «ERRORE: …» su stderr ed esce con il codice indicato (1 = dati, 2 = riga di comando)."""
    print(f"ERRORE: {messaggio}", file=sys.stderr)
    raise SystemExit(codice)


def costanti_sovrascrivibili(spazio):
    """Le costanti in testa allo script che --set può sovrascrivere: nomi MAIUSCOLI non callable, escluse le
    coordinate del foglio Excel (…_ROW, …_START, …_N) e le tabelle (dict), che non sono parametri di scenario."""
    return [k for k, v in spazio.items()
            if k.isupper() and not k.startswith("_") and not callable(v) and not hasattr(v, "__file__")
            and not k.endswith(("_ROW", "_START", "_N")) and not isinstance(v, dict)]


def cli(descrizione, spazio=None, argomenti=(), json=False, argv=None, epilogo=None):
    """Riga di comando comune degli script del plugin.

    - `--help` con descrizione, argomenti e, se `spazio` è dato, l'elenco delle costanti sovrascrivibili
    - `argomenti`: sequenza di (nomi, opzioni) passati a ArgumentParser.add_argument, per esempio
      (("excel",), {"nargs": "?", "help": "pianificatore compilato"})
    - `spazio` (di norma globals()): abilita `--set NOME=VALORE`, ripetibile, applicato con applica_override
      (refuso → rc 1); gli override applicati vengono stampati
    - `json=True`: aggiunge `--json FILE`; il percorso è in `.json` (None se assente)
    - argomento o flag non riconosciuto → usage su stderr e rc 2 (argparse)
    Ritorna il Namespace di argparse, con `.parser` per segnalare errori d'uso (`args.parser.error(...)`).
    Chiama configura_stdout(), quindi va invocata prima di qualsiasi stampa.
    """
    configura_stdout()
    if spazio is not None and epilogo is None:
        epilogo = ("costanti sovrascrivibili con --set NOME=VALORE (valori Python: 0.02, 10_000, None, "
                   "'bootstrap'):\n  " + ", ".join(costanti_sovrascrivibili(spazio)))
    ap = argparse.ArgumentParser(description=descrizione, epilog=epilogo, allow_abbrev=False,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    for nomi, opzioni in argomenti:
        ap.add_argument(*nomi, **opzioni)
    if spazio is not None:
        ap.add_argument("--set", action="append", default=[], metavar="NOME=VALORE",
                        help="sovrascrive una costante in testa allo script (ripetibile, vedi in fondo)")
    if json:
        ap.add_argument("--json", metavar="FILE", help="scrive i risultati chiave anche in un file JSON")
    args = ap.parse_args(argv)
    args.parser = ap
    if spazio is not None:
        finti_argv = [ap.prog]
        for espr in args.set:
            finti_argv += ["--set", espr]
        applica_override(spazio, finti_argv)
    return args


# ── Formati italiani ────────────────────────────────────────────────────────

def numero(x, decimali=0, segno=False):
    """Numero in formato italiano: punto per le migliaia, virgola per i decimali (1.234,5).
    Con segno=True il «+» compare anche sui positivi."""
    testo = f"{x:{'+' if segno else ''},.{decimali}f}"
    return testo.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def euro(x, decimali=0):
    """Importo in euro in formato italiano, col segno davanti al simbolo: €1.234 oppure -€1.234."""
    testo = numero(abs(x), decimali)
    return f"-€{testo}" if x < 0 and testo.strip("0.,") else f"€{testo}"


def pct(frazione, decimali=1, segno=False):
    """Percentuale in formato italiano da una frazione: pct(0.125) → «12,5%»."""
    return numero(frazione * 100, decimali, segno) + "%"


def _righe_storico(path_csv):
    """Righe di dati del CSV (commenti e intestazione esclusi), già divise sulle virgole.

    Un percorso relativo si risolve rispetto alla cartella del motore, dove stanno anche gli
    script e rendimenti-storici.csv: così gli script funzionano lanciati dalla cartella di
    lavoro dell'utente. Per una serie propria, passare un percorso assoluto.
    """
    if not os.path.isabs(path_csv):
        path_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)), path_csv)
    righe = []
    with open(path_csv, encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()
            if not riga or riga.startswith("#") or riga.lower().startswith("anno"):
                continue
            righe.append(riga.split(","))
    return righe


def carica_storico(path_csv):
    """Carica la serie annuale (azionario, obbligazionario) dal CSV. Valori in % → frazioni.

    Sono rendimenti NOMINALI in dollari USA (vedi l'intestazione del CSV): per ragionare in
    termini reali usare carica_inflazione + deflaziona.
    """
    righe = _righe_storico(path_csv)
    return (np.array([float(p[1]) / 100.0 for p in righe]),
            np.array([float(p[2]) / 100.0 for p in righe]))


def carica_inflazione(path_csv):
    """Colonna 'inflazione' del CSV (CPI USA dicembre su dicembre), in frazioni; None se la
    serie non la ha (una serie propria può fermarsi a due colonne)."""
    righe = _righe_storico(path_csv)
    if not righe or any(len(p) < 4 or not p[3].strip() for p in righe):
        return None
    return np.array([float(p[3]) / 100.0 for p in righe])


def deflaziona(rendimenti, inflazione):
    """Rendimenti reali anno per anno: (1 + nominale) / (1 + inflazione) − 1.
    `inflazione` è un array allineato alla serie (storica) o una costante."""
    return (1.0 + np.asarray(rendimenti)) / (1.0 + np.asarray(inflazione)) - 1.0


def indici_bootstrap(n_hist, n_sim, anni, blocco):
    """Matrice (n_sim, anni) di INDICI nella serie storica, a blocchi consecutivi circolari.

    Ogni blocco parte da un anno storico casuale e prosegue in sequenza (wrap sul fondo
    della serie): preserva l'autocorrelazione di breve periodo dei rendimenti storici.
    Restituire gli indici (e non i valori) permette di condividere la STESSA estrazione
    di anni tra più serie/obiettivi (shock di mercato comuni, per il rischio congiunto).
    """
    idx = np.empty((n_sim, anni), dtype=int)
    riempiti = 0
    while riempiti < anni:
        L = min(blocco, anni - riempiti)
        start = np.random.randint(0, n_hist, size=n_sim)
        for k in range(L):
            idx[:, riempiti + k] = (start + k) % n_hist
        riempiti += L
    return idx


def blocchi_bootstrap(port, n_sim, anni, blocco):
    """Matrice (n_sim, anni) di RENDIMENTI del portafoglio, campionati a blocchi dalla serie."""
    return port[indici_bootstrap(len(port), n_sim, anni, blocco)]


def pctl(a, p):
    return float(np.percentile(a, p))


def applica_override(spazio, argv=None):
    """Override '--set NOME=VALORE' delle costanti top-level, senza modificare il file.

    Mantiene il pattern "costanti in testa allo script" aggiungendo la via non
    distruttiva e riproducibile:
        python script.py --set N_SIM=2000 --set MODELLO=bootstrap [altri argomenti]
    - NOME deve già esistere nello script (protegge dai refusi)
    - VALORE è interpretato con ast.literal_eval (numeri, liste, None, True/False);
      se non interpretabile resta stringa (comodo per MODELLO=bootstrap), ma una
      costante numerica non accetta una stringa (RAL_ATTUALE=abc → ERRORE, rc 1)
    - dagli script si usa tramite cli(), che raccoglie i --set con argparse e li passa
      qui; chiamato da solo legge e RIMUOVE i --set da argv
    Gli override applicati vengono stampati: il run resta documentato e ripetibile.
    """
    if argv is None:
        argv = sys.argv
    applicati = []
    i = 1
    while i < len(argv):
        if argv[i] == "--set" and i + 1 < len(argv):
            espr = argv[i + 1]
            del argv[i:i + 2]
        elif argv[i].startswith("--set="):
            espr = argv[i][len("--set="):]
            del argv[i]
        else:
            i += 1
            continue
        nome, sep, val = espr.partition("=")
        nome = nome.strip()
        if not sep or nome not in spazio:
            raise SystemExit(f"ERRORE: --set: costante sconosciuta o malformata '{espr}' "
                             f"(i nomi validi sono le costanti in testa allo script)")
        try:
            nuovo = ast.literal_eval(val)
        except (ValueError, SyntaxError):
            nuovo = val
        vecchio = spazio[nome]
        if isinstance(vecchio, (int, float)) and not isinstance(vecchio, bool) and isinstance(nuovo, str):
            raise SystemExit(f"ERRORE: --set {nome}={val}: non è un numero (il default è {vecchio!r})")
        spazio[nome] = nuovo
        applicati.append(f"{nome}={spazio[nome]!r}")
    if applicati:
        print("[override] " + ", ".join(applicati))
    return applicati


def scrivi_json(path, dati):
    """Scrive i risultati chiave su file JSON (UTF-8, leggibile); percorso non scrivibile → ERRORE, rc 1."""
    import json
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(dati, f, ensure_ascii=False, indent=2)
    except OSError as e:
        errore(f"impossibile scrivere {path}: {e.strerror}")
    print(f"[json] risultati scritti in {path}")


# Il pianificatore Excel viene letto PER POSIZIONE (colonne A,B,C,D,F,G,N): se le
# colonne vengono spostate, senza guardia gli script leggerebbero dati sbagliati
# in silenzio. Questa mappa fissa le keyword attese nelle intestazioni (riga 4).
INTESTAZIONI_OBIETTIVI = {
    "A": "obiettivo", "B": "target", "C": "orizzonte",
    "D": "profilo", "F": "accantonato", "G": "priorit", "N": "tipo",
}


def verifica_intestazioni_obiettivi(ws, riga=4):
    """Guardia sul layout: errore ESPLICITO invece di dati sbagliati in silenzio."""
    for col, kw in INTESTAZIONI_OBIETTIVI.items():
        val = str(ws[f"{col}{riga}"].value or "").replace("\n", " ").lower()
        if kw not in val:
            raise SystemExit(
                f"Struttura del pianificatore NON riconosciuta: in colonna {col} (riga {riga}) "
                f"attendevo un'intestazione contenente '{kw}', trovato {val!r}. Gli script leggono "
                f"le colonne per posizione: se il layout è stato modificato, ripristinalo.")


# ── Lettore unico del pianificatore ─────────────────────────────────────────
# Layout del pianificatore-obiettivi.xlsx (letto per posizione, con la guardia sulle intestazioni):
#   Parametri!B5 capacità di risparmio mensile, B6 inflazione, A7:B7 finestra di de-risking,
#   A10:D15 profili (nome, rendimento, volatilità, % azionario); Obiettivi, righe 5-14:
#   A nome, B target in euro di oggi, C orizzonte in anni, D profilo, F già accantonato,
#   G priorità, N tipo (terminante / permanente).
RIGA_CAPACITA, RIGA_INFLAZIONE = 5, 6
PROFILI_PRIMA_RIGA, PROFILI_N = 10, 6
OBIETTIVI_PRIMA_RIGA, OBIETTIVI_N = 5, 10


def _numero_cella(valore, dove, cosa):
    """Numero da una cella del pianificatore; una cella di testo («40.000») è un errore esplicito."""
    if valore is None or valore == "":
        return None
    if isinstance(valore, bool) or not isinstance(valore, (int, float)):
        try:
            return float(str(valore).replace(".", "").replace(",", "."))
        except ValueError:
            errore(f"{cosa} non numerico in {dove}: {valore!r} (la cella è testo: riscrivila come numero)")
    return float(valore)


def leggi_pianificatore(path, avvisa=print):
    """Legge il pianificatore compilato e ritorna un dizionario con capacita, inflazione, finestra,
    finestra_nel_foglio, profili e obiettivi: l'unico lettore dei quattro script degli obiettivi, così
    gli errori di compilazione più comuni danno lo stesso esito ovunque.

    - foglio Parametri o Obiettivi mancante, importi scritti come testo, profilo che non è nella tabella,
      orizzonte non intero → ERRORE esplicito (rc 1), mai un KeyError o un numero sbagliato in silenzio
    - il profilo si confronta senza maiuscole e spazi, come il CERCA.VERT del foglio: «crescita» → «Crescita»
    - target vuoto → None, cioè «il più possibile»: ogni script decide se usarlo (il glide path sì,
      Monte Carlo e allocatore no, e lo dicono)
    - riga con il nome ma senza orizzonte o profilo → scartata con un avviso che dice il motivo
    - priorità e tipo in minuscolo; tipo mancante = terminante; coperto = il già accantonato copre il target
    - un avviso se il file è il modello dentro il plugin: i dati vanno in una copia nella cartella di lavoro
    profili: {nome: {"rendimento", "volatilita", "azionario"}}; obiettivi: lista di dizionari con nome,
    target_oggi, orizzonte, profilo (il nome canonico della tabella), gia, priorita, tipo, permanente, coperto.
    """
    from openpyxl import load_workbook
    if not os.path.exists(path):
        errore(f"file non trovato: {path}")
    if os.path.dirname(os.path.abspath(path)) == os.path.dirname(os.path.abspath(__file__)):
        avvisa("⚠️  Stai leggendo il pianificatore d'esempio dentro il plugin: copia il file nella tua cartella "
               "di lavoro, compilalo lì e passane il percorso allo script.")
    try:
        wb = load_workbook(path, data_only=True)
    except Exception as e:   # zipfile.BadZipFile, InvalidFileException, OSError: non è un xlsx leggibile
        errore(f"{path} non è un pianificatore xlsx leggibile ({type(e).__name__}: {e})")
    for foglio in ("Parametri", "Obiettivi"):
        if foglio not in wb.sheetnames:
            errore(f"foglio «{foglio}» mancante in {os.path.basename(path)} (fogli presenti: "
                   f"{', '.join(wb.sheetnames)}): non è un pianificatore-obiettivi.xlsx")
    par, obj = wb["Parametri"], wb["Obiettivi"]
    verifica_intestazioni_obiettivi(obj)

    profili = {}
    for r in range(PROFILI_PRIMA_RIGA, PROFILI_PRIMA_RIGA + PROFILI_N):
        nome = par.cell(row=r, column=1).value
        if nome is None or str(nome).strip() == "":
            continue
        nome = str(nome).strip()
        rend = _numero_cella(par.cell(row=r, column=2).value, f"Parametri!B{r}", f"rendimento del profilo «{nome}»")
        if rend is None:
            errore(f"profilo «{nome}» senza rendimento in Parametri!B{r}")
        profili[nome] = {
            "rendimento": rend,
            "volatilita": _numero_cella(par.cell(row=r, column=3).value, f"Parametri!C{r}", "volatilità") or 0.0,
            "azionario": _numero_cella(par.cell(row=r, column=4).value, f"Parametri!D{r}", "% azionario") or 0.0,
        }
    if not profili:
        errore(f"nessun profilo in Parametri!A{PROFILI_PRIMA_RIGA}:A{PROFILI_PRIMA_RIGA + PROFILI_N - 1}")
    canonici = {n.casefold(): n for n in profili}

    obiettivi = []
    for r in range(OBIETTIVI_PRIMA_RIGA, OBIETTIVI_PRIMA_RIGA + OBIETTIVI_N):
        celle = {col: obj.cell(row=r, column=c).value for col, c in
                 (("nome", 1), ("target", 2), ("orizzonte", 3), ("profilo", 4), ("gia", 6), ("priorita", 7), ("tipo", 14))}
        vuote = all(v is None or str(v).strip() == "" for v in celle.values())
        if vuote:
            continue
        nome = str(celle["nome"] or "").strip()
        if not nome:
            avvisa(f"⚠️  Obiettivi!riga {r}: riga senza nome scartata (compilata solo in parte)")
            continue
        mancanti = [c for c in ("orizzonte", "profilo") if celle[c] is None or str(celle[c]).strip() == ""]
        if mancanti:
            avvisa(f"⚠️  Obiettivi!riga {r}: «{nome}» scartato, manca {' e '.join(mancanti)}")
            continue
        oriz = _numero_cella(celle["orizzonte"], f"Obiettivi!C{r}", f"orizzonte di «{nome}»")
        if oriz is None or oriz <= 0 or not float(oriz).is_integer():
            errore(f"orizzonte di «{nome}» in Obiettivi!C{r} non valido: {celle['orizzonte']!r} "
                   f"(il pianificatore ragiona per anni interi, da 1 in su)")
        profilo = canonici.get(str(celle["profilo"]).strip().casefold())
        if profilo is None:
            errore(f"profilo «{celle['profilo']}» di «{nome}» (Obiettivi!D{r}) non è nella tabella dei profili: "
                   f"{', '.join(profili)}")
        target = _numero_cella(celle["target"], f"Obiettivi!B{r}", f"target di «{nome}»")
        gia = _numero_cella(celle["gia"], f"Obiettivi!F{r}", f"già accantonato di «{nome}»") or 0.0
        tipo = str(celle["tipo"] or "terminante").strip().casefold() or "terminante"
        obiettivi.append({
            "nome": nome, "target_oggi": target, "orizzonte": int(oriz), "profilo": profilo, "gia": gia,
            "priorita": str(celle["priorita"] or "").strip().casefold(), "tipo": tipo,
            "permanente": tipo.startswith("perman"),
            "coperto": target is not None and gia >= target - 1e-6,
        })

    return {
        "capacita": _numero_cella(par.cell(row=RIGA_CAPACITA, column=2).value, f"Parametri!B{RIGA_CAPACITA}",
                                  "capacità di risparmio") or 0.0,
        "inflazione": _numero_cella(par.cell(row=RIGA_INFLAZIONE, column=2).value, f"Parametri!B{RIGA_INFLAZIONE}",
                                    "inflazione") or 0.0,
        "finestra": leggi_finestra_derisk(par),
        "finestra_nel_foglio": finestra_nel_foglio(par),
        "profili": profili,
        "obiettivi": obiettivi,
    }


# ── Glide path del pianificatore obiettivi ──────────────────────────────────
# Un'unica definizione per il foglio Excel (Obiettivi, colonne O, P e I), il Monte Carlo, il
# calendario del glide path e l'allocatore. Gli obiettivi TERMINANTI tengono la quota del
# profilo finché mancano più di `finestra` anni alla scadenza, poi scendono fino alla quota di
# atterraggio. Il calendario è annuale: nell'anno y (da 0) vale la quota a inizio anno, con
# anni residui = anni − y, tenuta per tutto l'anno (it-rebalance riallinea i target una volta
# l'anno). Durante la rampa il secchiello è una miscela del portafoglio del profilo e di quello
# di atterraggio: rendimento atteso e volatilità sono lineari nella frazione trattenuta.

FINESTRA_DERISK_DEFAULT = 7


def quota_glide(anni_residui, quota_partenza, finestra, atterraggio=0.0, curvatura=1.0):
    """Quota azionaria target dato il tempo residuo all'obiettivo."""
    if quota_partenza <= atterraggio:
        return quota_partenza                  # già conservativo: niente da de-riskare
    if anni_residui <= 0:
        return atterraggio
    if anni_residui >= finestra:
        return quota_partenza                  # ancora lontano: tiene la quota piena
    frazione = (anni_residui / finestra) ** curvatura
    return atterraggio + (quota_partenza - atterraggio) * frazione


def frazioni_glide(anni, finestra, curvatura=1.0):
    """Per ogni anno y = 0..anni−1 la frazione trattenuta della distanza tra la quota del profilo
    e l'atterraggio (1 = quota piena, 0 = atterraggio), con finestra effettiva min(finestra, anni)."""
    w = min(finestra, anni)
    return np.array([quota_glide(anni - y, 1.0, w, 0.0, curvatura) for y in range(anni)])


def _fattore_versamenti(r, anni):
    """Valore a fine periodo di un versamento mensile unitario (fine mese) per `anni` anni."""
    if anni <= 0:
        return 0.0
    if r == 0:
        return 12.0 * anni
    return ((1 + r) ** anni - 1) / ((1 + r) ** (1 / 12) - 1)


def pmt_glide(target_nom, gia, rend, rend_atterraggio, anni, finestra, curvatura=1.0):
    """Versamento mensile per arrivare a target_nom lungo il glide path: la formula del foglio
    (Obiettivi!I). Due fasi: gli anni a quota piena al rendimento del profilo, poi gli anni di
    rampa al loro rendimento medio (con rampa lineare, la media tra profilo e atterraggio:
    Obiettivi!P). Con rend_atterraggio = rend (permanenti, profili senza azionario) è la formula
    classica del valore futuro di una rendita.

    Rispetto al calcolo anno per anno sbaglia per difetto, di più quanto più azionario ha il
    profilo e quanto più lunga è la finestra; il caso peggiore è un orizzonte pari alla finestra.
    Con la finestra di 7 anni l'errore resta sotto l'1% con Moderato e arriva all'1,4% con
    Crescita e all'1,8% con Azionario totale; con una finestra di 10 anni arriva al 2,8% con
    Crescita massima e al 3,0% con Azionario totale. È misurato sul versamento senza capitale già
    accantonato: se il già accantonato copre quasi tutto il target l'errore relativo sale, ma su un
    versamento piccolo."""
    f = frazioni_glide(anni, finestra, curvatura)
    m = int(np.sum(f < 1.0))               # anni di rampa
    k = anni - m                           # anni a quota piena
    r2 = (rend_atterraggio + (rend - rend_atterraggio) * float(np.mean(f[k:]))) if m else rend
    crescita_rampa = (1 + r2) ** m
    return ((target_nom - gia * (1 + rend) ** k * crescita_rampa)
            / (_fattore_versamenti(rend, k) * crescita_rampa + _fattore_versamenti(r2, m)))


def crescita_glide(rend, rend_atterraggio, anni, finestra, curvatura=1.0):
    """Fattore di crescita lungo il glide path di un capitale investito oggi: Π(1 + r_y)."""
    f = frazioni_glide(anni, finestra, curvatura)
    return float(np.prod(1 + rend_atterraggio + (rend - rend_atterraggio) * f))


def finestra_nel_foglio(ws_parametri):
    """True se il foglio Parametri porta la finestra di de-risking (A7:B7): i pianificatori dalla
    0.10.0, la cui colonna I sconta il glide path."""
    etichetta = str(ws_parametri["A7"].value or "").lower()
    valore = ws_parametri["B7"].value
    return "finestra" in etichetta and isinstance(valore, (int, float)) and valore >= 0


def leggi_finestra_derisk(ws_parametri, default=FINESTRA_DERISK_DEFAULT):
    """Finestra di de-risking dal foglio Parametri del pianificatore (A7:B7). Un pianificatore
    compilato prima della 0.10.0 non la porta: si usa il default e lo si dice, perché la colonna I
    di quel foglio è a quota fissa, più bassa del versamento col glide path degli script."""
    if finestra_nel_foglio(ws_parametri):
        return int(ws_parametri["B7"].value)
    print(f"⚠️  Pianificatore senza la finestra di de-risking (Parametri!A7:B7), compilato prima della "
          f"0.10.0: uso {default} anni. La sua colonna I è a quota fissa e non sconta il glide path, "
          f"quindi è più bassa dei versamenti calcolati qui. Ricopia gli obiettivi nel "
          f"pianificatore-obiettivi.xlsx aggiornato.")
    return default


def scarti_dal_foglio(finestra, finestra_foglio, atterraggio, quota_minima, curvatura):
    """Dove il glide path di uno script si discosta da quello del foglio (Obiettivi, colonne I, O, P:
    finestra di Parametri!B7, rampa lineare, atterraggio sul profilo a quota azionaria minima).
    finestra_foglio = None se il foglio non la porta. Lista vuota = il versamento dello script è
    quello della colonna I."""
    scarti = []
    if finestra_foglio is None:
        scarti.append("pianificatore precedente alla 0.10.0, colonna I a quota fissa")
    elif finestra != finestra_foglio:
        scarti.append(f"finestra {finestra} anni invece dei {finestra_foglio} di Parametri!B7")
    if abs(atterraggio - quota_minima) > 1e-9:
        scarti.append(f"atterraggio al {atterraggio * 100:.0f}% invece del {quota_minima * 100:.0f}% azionario")
    if curvatura != 1:
        scarti.append(f"curvatura {curvatura} invece della rampa lineare")
    return scarti
