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
  - carica_storico(path_csv): serie annuali reali (azionario, obbligazionario); un
    percorso relativo si risolve rispetto a questa cartella, non alla cwd
  - indici_bootstrap(n_hist, n_sim, anni, blocco): campionamento a blocchi circolari
  - blocchi_bootstrap(port, n_sim, anni, blocco): rendimenti di portafoglio campionati
  - pctl(a, p): percentile come float
  - applica_override(spazio): override '--set NOME=VALORE' delle costanti da riga di comando
  - percorso_json / scrivi_json: flag '--json <file>' per l'output machine-readable (pipeline)
  - verifica_intestazioni_obiettivi(ws): guardia sul layout del pianificatore Excel

Il campionamento usa np.random (generatore legacy): il seed fissato dagli script
con np.random.seed(...) governa anche il motore. La sequenza di chiamate random è
UNA randint per blocco — invariante da preservare nei refactor (i risultati con seed
devono restare riproducibili).

Nota di perimetro: decumulo-obiettivi.py usa una variante propria (Generator con
blocchi non circolari); unificarla cambierebbe i suoi percorsi simulati, quindi
resta deliberatamente fuori da questo motore.
"""

import ast
import os
import sys

import numpy as np


def carica_storico(path_csv):
    """Carica la serie annuale (azionario, obbligazionario) dal CSV. Valori in % → frazioni.

    Un percorso relativo si risolve rispetto alla cartella del motore, dove stanno anche gli
    script e rendimenti-storici.csv: così gli script funzionano lanciati dalla cartella di
    lavoro dell'utente. Per una serie propria, passare un percorso assoluto.
    """
    if not os.path.isabs(path_csv):
        path_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)), path_csv)
    az, ob = [], []
    with open(path_csv) as f:
        for riga in f:
            riga = riga.strip()
            if not riga or riga.startswith("#") or riga.lower().startswith("anno"):
                continue
            parti = riga.split(",")
            az.append(float(parti[1]) / 100.0)
            ob.append(float(parti[2]) / 100.0)
    return np.array(az), np.array(ob)


def indici_bootstrap(n_hist, n_sim, anni, blocco):
    """Matrice (n_sim, anni) di INDICI nella serie storica, a blocchi consecutivi circolari.

    Ogni blocco parte da un anno storico casuale e prosegue in sequenza (wrap sul fondo
    della serie): preserva l'autocorrelazione di breve periodo dei rendimenti reali.
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
      se non interpretabile resta stringa (comodo per MODELLO=bootstrap)
    - gli argomenti --set vengono RIMOSSI da sys.argv: il resto del parsing
      (es. il path dell'Excel) non cambia
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
            raise SystemExit(f"--set: costante sconosciuta o malformata '{espr}' "
                             f"(i nomi validi sono le costanti in testa allo script)")
        try:
            spazio[nome] = ast.literal_eval(val)
        except (ValueError, SyntaxError):
            spazio[nome] = val
        applicati.append(f"{nome}={spazio[nome]!r}")
    if applicati:
        print("[override] " + ", ".join(applicati))
    return applicati


def percorso_json(argv=None):
    """Estrae '--json <file>' (o '--json=<file>') da argv; ritorna il path o None.

    Con questo flag gli script scrivono i risultati chiave anche in JSON, così i
    numeri passano da uno script all'altro (pipeline) senza travasi a mano."""
    if argv is None:
        argv = sys.argv
    i = 1
    while i < len(argv):
        if argv[i] == "--json" and i + 1 < len(argv):
            path = argv[i + 1]
            del argv[i:i + 2]
            return path
        if argv[i].startswith("--json="):
            path = argv[i][len("--json="):]
            del argv[i]
            return path
        i += 1
    return None


def scrivi_json(path, dati):
    """Scrive i risultati chiave su file JSON (UTF-8, leggibile)."""
    import json
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dati, f, ensure_ascii=False, indent=2)
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
