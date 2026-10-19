#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pacchetto.py — costruisce lo zip del plugin per l'upload in Cowork
(Settings → Plugins → Add plugin → Upload a zip) e per la GitHub Release.

Uso (dalla radice del repository):
    python scripts/pacchetto.py                  → dist/wealth-management-it-vX.Y.Z.zip
    python scripts/pacchetto.py --out DIR        → DIR/wealth-management-it-vX.Y.Z.zip
    python scripts/pacchetto.py --tag vX.Y.Z     → fallisce se il tag ≠ versione del manifest

Nello zip entra solo ciò che serve al plugin installato: manifest, comandi,
skill e README, sotto la cartella wealth-management-it/. Restano fuori test,
workflow, script di build, cache e file di sistema.
"""

import argparse
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOME = "wealth-management-it"

# Cosa entra nello zip (relativo alla radice del repository).
INCLUDI = [".claude-plugin", "commands", "skills", "README.md"]
# Cosa resta fuori anche se dentro una cartella inclusa.
ESCLUDI_DIR = {"__pycache__", ".git", "ordini"}
ESCLUDI_FILE = {".DS_Store"}
ESCLUDI_EXT = (".pyc",)


def versione_manifest():
    with open(os.path.join(ROOT, ".claude-plugin", "plugin.json"), encoding="utf-8") as f:
        return json.load(f)["version"]


def file_da_includere():
    for voce in INCLUDI:
        percorso = os.path.join(ROOT, voce)
        if os.path.isfile(percorso):
            yield percorso
            continue
        for base, dirs, files in os.walk(percorso):
            dirs[:] = sorted(d for d in dirs if d not in ESCLUDI_DIR)
            for f in sorted(files):
                if f in ESCLUDI_FILE or f.endswith(ESCLUDI_EXT):
                    continue
                yield os.path.join(base, f)


def costruisci(out_dir, versione):
    os.makedirs(out_dir, exist_ok=True)
    zpath = os.path.join(out_dir, f"{NOME}-v{versione}.zip")
    n = 0
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for percorso in file_da_includere():
            arcname = os.path.join(NOME, os.path.relpath(percorso, ROOT))
            z.write(percorso, arcname)
            n += 1
    return zpath, n


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, "dist"), metavar="DIR",
                    help="cartella di destinazione (default: dist/)")
    ap.add_argument("--tag", metavar="vX.Y.Z",
                    help="tag di release: deve coincidere con la versione del manifest")
    args = ap.parse_args()

    versione = versione_manifest()
    if args.tag is not None and args.tag.lstrip("v") != versione:
        print(f"ERRORE: il tag {args.tag} non coincide con la versione del manifest "
              f"({versione}). Allineare plugin.json (e marketplace.json) prima di taggare.",
              file=sys.stderr)
        sys.exit(1)

    zpath, n = costruisci(args.out, versione)
    print(f"{zpath}: {n} file, {os.path.getsize(zpath) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
