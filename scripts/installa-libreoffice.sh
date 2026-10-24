#!/usr/bin/env bash
# installa-libreoffice.sh — installa LibreOffice Calc nella CI riusando i .deb in cache.
#
# Uso (nei workflow, dopo actions/cache/restore sulla stessa cartella):
#     bash scripts/installa-libreoffice.sh /tmp/apt-libreoffice
#
# Su alcuni runner di GitHub (westus3) azure.archive.ubuntu.com serve i .deb a
# ~70 KB/s: 20-30 minuti per i 94 MB di LibreOffice, mentre l'update degli indici
# resta veloce. Con i .deb dei run precedenti apt scarica solo quelli che mancano.
#
# apt riusa un .deb già scaricato se la dimensione coincide, senza controllarne
# l'hash: prima dell'installazione ogni file in cache si confronta con lo SHA256
# dell'indice firmato, e quelli diversi si cancellano (apt li riscarica).
# Alla fine restano solo .deb ancora pubblicati (autoclean), leggibili da
# actions/cache/save, e in $GITHUB_OUTPUT va la chiave della cache: cambia solo
# quando cambia l'elenco dei file. Il prefisso della chiave è lo stesso dei
# restore-keys nei workflow.
set -euo pipefail

DEB=${1:?uso: installa-libreoffice.sh CARTELLA_DEB}
OPZIONI=(-q --no-install-recommends)
TMP=$(mktemp -d)
trap 'sudo rm -rf "$TMP"' EXIT

mkdir -p "$DEB"
sudo apt-get update -q

# SHA256 di ogni .deb dell'installazione: con l'archivio vuoto nessuno risulta già scaricato.
sudo apt-get install "${OPZIONI[@]}" --print-uris -o Acquire::ForceHash=SHA256 \
        -o Dir::Cache::Archives="$TMP" libreoffice-calc \
    | sed -nE "s/^'[^']+' ([^ ]+) [0-9]+ SHA256:([0-9a-f]{64})$/\2  \1/p" > "$TMP/attesi"
while read -r hash nome; do
    if [ -f "$DEB/$nome" ] && ! echo "$hash  $DEB/$nome" | sha256sum -c --status; then
        echo "$nome: hash diverso dall'indice, si riscarica"
        sudo rm -f "$DEB/$nome"
    fi
done < "$TMP/attesi"

sudo apt-get install -y "${OPZIONI[@]}" -o Dir::Cache::Archives="$DEB" libreoffice-calc
sudo apt-get autoclean -q -o Dir::Cache::Archives="$DEB"
sudo rm -rf "$DEB/partial" "$DEB/lock"

if [ -n "${GITHUB_OUTPUT:-}" ]; then
    echo "chiave=apt-libreoffice-$RUNNER_OS-$RUNNER_ARCH-$(find "$DEB" -name '*.deb' -printf '%f\n' | sort | sha256sum | cut -c1-16)" >> "$GITHUB_OUTPUT"
fi
