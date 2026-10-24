#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ricalcola-excel.py — ricalcola gli Excel del plugin con LibreOffice headless
e segnala le celle in errore.

Uso (dalla radice del repository):
    python scripts/ricalcola-excel.py --tutti                → controlla tutti gli xlsx sotto skills/
    python scripts/ricalcola-excel.py FILE.xlsx --outdir DIR → copie ricalcolate in DIR
    python scripts/ricalcola-excel.py FILE.xlsx --in-place   → aggiorna le cache del file

openpyxl legge solo i valori salvati nel file (la "cache" dell'ultimo
ricalcolo): dopo aver modificato formule o input, i valori restano quelli
vecchi finché un'applicazione non ricalcola. Questo script apre i file con
LibreOffice in un profilo temporaneo che forza il ricalcolo al caricamento
(OOXMLRecalcMode = 0, "ricalcola sempre") in locale it-IT, li salva e
controlla gli errori.
Esce con 1 se una cella contiene #REF!, #NAME?, #DIV/0!, #VALUE!, #N/A,
#NUM! o #NULL!; con 2 se LibreOffice non è installato.

LibreOffice si cerca in $SOFFICE, nel PATH (soffice, libreoffice) e nel
percorso standard di macOS.
"""

import argparse
import glob
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ERRORI = ("#REF!", "#NAME?", "#DIV/0!", "#VALUE!", "#N/A", "#NUM!", "#NULL!")
MACOS = "/Applications/LibreOffice.app/Contents/MacOS/soffice"

# Profilo LibreOffice minimo: ricalcola sempre i file OOXML e ODF al caricamento
# (il default è "mai", che lascerebbe le cache vecchie) e usa il locale it-IT,
# come un utente italiano: il punto è il separatore delle migliaia, quindi un
# numero salvato come testo ("0.022") o un TEXT(x;"0.0%") si comportano come
# nell'Excel o nel LibreOffice di chi usa il plugin, su qualunque macchina.
PROFILO = """<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry">
<item oor:path="/org.openoffice.Setup/L10N"><prop oor:name="ooSetupSystemLocale" oor:op="fuse"><value>it-IT</value></prop></item>
<item oor:path="/org.openoffice.Office.Calc/Formula/Load"><prop oor:name="OOXMLRecalcMode" oor:op="fuse"><value>0</value></prop></item>
<item oor:path="/org.openoffice.Office.Calc/Formula/Load"><prop oor:name="ODFRecalcMode" oor:op="fuse"><value>0</value></prop></item>
</oor:items>
"""


WINDOWS = [os.path.join(base, "LibreOffice", "program", "soffice.exe")
           for base in (os.environ.get("ProgramFiles", r"C:\Program Files"),
                        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))]


def trova_soffice():
    """Il binario di LibreOffice: $SOFFICE, poi il PATH, poi le installazioni standard di macOS e Windows."""
    for candidato in (os.environ.get("SOFFICE"), shutil.which("soffice"),
                      shutil.which("libreoffice"), MACOS, *WINDOWS):
        if candidato and os.path.exists(candidato):
            return candidato
    return None


def ricalcola(percorsi, outdir):
    """Salva in outdir le copie ricalcolate dei file; ritorna i percorsi prodotti."""
    soffice = trova_soffice()
    if not soffice:
        raise FileNotFoundError("LibreOffice non trovato: installarlo o impostare $SOFFICE")
    os.makedirs(outdir, exist_ok=True)
    nomi = [os.path.basename(p) for p in percorsi]
    if len(set(nomi)) != len(nomi):
        raise ValueError("due file con lo stesso nome finirebbero nella stessa outdir")
    with tempfile.TemporaryDirectory(prefix="lo-profilo-") as profilo:
        os.makedirs(os.path.join(profilo, "user"))
        with open(os.path.join(profilo, "user", "registrymodifications.xcu"), "w", encoding="utf-8") as f:
            f.write(PROFILO)
        r = subprocess.run(
            [soffice, f"-env:UserInstallation={pathlib.Path(profilo).as_uri()}",
             "--headless", "--norestore", "--convert-to", "xlsx", "--outdir", outdir, *percorsi],
            capture_output=True, text=True, timeout=600)
    prodotti = [os.path.join(outdir, n) for n in nomi]
    mancanti = [p for p in prodotti if not os.path.exists(p)]
    if r.returncode != 0 or mancanti:
        raise RuntimeError(f"LibreOffice non ha prodotto {mancanti or 'i file'}: {r.stderr.strip()[-400:]}")
    return prodotti


def errori(percorso):
    """Celle con un valore d'errore dopo il ricalcolo: [(foglio, cella, valore)]."""
    from openpyxl import load_workbook
    trovati = []
    for ws in load_workbook(percorso, data_only=True).worksheets:
        for riga in ws.iter_rows():
            for c in riga:
                if isinstance(c.value, str) and c.value.strip() in ERRORI:
                    trovati.append((ws.title, c.coordinate, c.value.strip()))
    return trovati


def tutti_gli_xlsx():
    return sorted(glob.glob(os.path.join(ROOT, "skills", "*", "assets", "*.xlsx")))


def main():
    for flusso in (sys.stdout, sys.stderr):   # UTF-8 anche su Windows (cp1252)
        try:
            flusso.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="Ricalcola gli Excel con LibreOffice headless e segnala gli errori.")
    ap.add_argument("file", nargs="*", help="file .xlsx da ricalcolare")
    ap.add_argument("--tutti", action="store_true", help="tutti gli xlsx sotto skills/*/assets/")
    dove = ap.add_mutually_exclusive_group()
    dove.add_argument("--outdir", help="cartella in cui salvare le copie ricalcolate")
    dove.add_argument("--in-place", action="store_true", help="sovrascrive i file con le cache aggiornate")
    args = ap.parse_args()

    percorsi = [os.path.abspath(p) for p in args.file] + (tutti_gli_xlsx() if args.tutti else [])
    if not percorsi:
        ap.error("indicare almeno un file oppure --tutti")
    if not trova_soffice():
        print("LibreOffice non trovato: installarlo o impostare $SOFFICE.", file=sys.stderr)
        sys.exit(2)
    with tempfile.TemporaryDirectory(prefix="ricalcolo-") as tmp:
        prodotti = ricalcola(percorsi, args.outdir or tmp)
        totale = 0
        for orig, nuovo in zip(percorsi, prodotti):
            trovati = errori(nuovo)
            totale += len(trovati)
            print(f"{os.path.relpath(orig, ROOT)}: {len(trovati)} celle in errore")
            for foglio, cella, valore in trovati[:20]:
                print(f"    {foglio}!{cella} = {valore}")
            if args.in_place:
                shutil.copyfile(nuovo, orig)
    if args.in_place:
        print("Cache aggiornate nei file originali.")
    sys.exit(1 if totale else 0)


if __name__ == "__main__":
    main()
