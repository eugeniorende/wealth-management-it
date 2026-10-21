#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
importa-previdenza.py — importa i dati previdenziali REALI e li trasforma in parametri di pianificazione.

Legge due file (il secondo è opzionale):
  1. l'estratto conto contributivo INPS in formato XML (scaricabile dal portale INPS)
  2. lo storico movimenti del fondo pensione complementare in CSV (export del fondo)

e produce:
  - anzianità contributiva (settimane/anni), retribuzioni imponibili per anno
  - la RICOSTRUZIONE del montante contributivo INPS (contributi × aliquota, rivalutati
    con i tassi di capitalizzazione ufficiali ISTAT — variazione media quinquennale del PIL nominale)
  - montante del fondo pensione per comparto (quote nette × ultimo NAV), stima del mix azionario,
    versamenti per anno e per fonte (iscritto / azienda / TFR)
  - un blocco di PARAMETRI PRONTI da incollare in proiezione-inps.py e montecarlo-pensione.py

Uso:
    python importa-previdenza.py estratto_inps.xml [storico_fondo.csv]

ONESTÀ METODOLOGICA
- La ricostruzione del montante è un'approssimazione (±qualche %): l'estratto conto elenca i
  contributi ma non li capitalizza. La tabella dei tassi copre 1996-2025; il tasso dell'anno in
  corso non è ancora pubblicato, quindi il montante al 31/12 dell'anno scorso non è ancora
  rivalutato per quest'anno (i contributi dell'anno, per legge, si rivalutano solo dall'anno dopo).
  Il valore ESATTO è nel servizio "La mia pensione futura" sul portale INPS: se lo hai, usa quello.
- Solo il sistema contributivo: le retribuzioni prima del 1996 appartengono alla quota retributiva
  (L. 335/1995 art. 1 c. 12-13), che lo script non calcola; restano fuori dal montante e un avviso
  lo dice.
- La stima del mix azionario del fondo è EURISTICA (dal nome del comparto): verificala sulla
  nota informativa del fondo.
"""

import csv
import sys
import datetime
import xml.etree.ElementTree as ET
from collections import defaultdict

# ============================== PARAMETRI ==============================

ALIQUOTA_COMPUTO = 0.33   # aliquota IVS dipendenti (autonomi ~0,24; gestione separata ~0,2607)

# Tassi di capitalizzazione del montante (L. 335/1995 art. 1 c. 8-9: variazione media quinquennale
# del PIL nominale calcolata dall'ISTAT, mai sotto 1 dal DL 65/2015 art. 5, con recupero sugli anni
# successivi, tranne per il 2014).
# Convenzione: TASSO[X] rivaluta al 31/12/X il montante accumulato fino al 31/12/(X-1); vale per le
# pensioni con decorrenza dall'anno X+1. Le tabelle INPS etichettano lo stesso valore col 31/12/(X-1).
# Tassi ISTAT 1996-2025 dalla nota ISTAT del 16/10/2025 (lavoro.gov.it), regola del minimo e del
# recupero dal DL 65/2015 — Verificato: 2026-10. I valori applicati da INPS per 2014, 2021 e 2022
# (minimo e recupero) vengono dai messaggi INPS 840/2024 e 707/2026, letti in copia.
TASSI_CAPITALIZZAZIONE = {
    1996: 1.062054,   # rivaluta il montante al 31/12/1995, che nel contributivo è zero (INPS pubblica dal 1997)
    1997: 1.055871, 1998: 1.053597, 1999: 1.056503, 2000: 1.051781, 2001: 1.047781,
    2002: 1.043698, 2003: 1.041614, 2004: 1.039272, 2005: 1.040506, 2006: 1.035386,
    2007: 1.033937, 2008: 1.034625, 2009: 1.033201, 2010: 1.017935, 2011: 1.016165,
    2012: 1.011344, 2013: 1.001643,
    2014: 1.000000,   # ISTAT 0,998073: minimo a 1, senza recupero (DL 65/2015 art. 5 c. 1-bis)
    2015: 1.005058, 2016: 1.004684, 2017: 1.005205, 2018: 1.013478, 2019: 1.018254,
    2020: 1.019199,
    2021: 1.000000,   # ISTAT 0,999785: minimo a 1, da recuperare
    2022: 1.009756,   # ISTAT 1,009973 × 0,999785 (recupero del 2021)
    2023: 1.023082,
    2024: 1.036622,
    2025: 1.040445,   # rivaluta il montante al 31/12/2024 (decorrenze 2026)
}
# Anni senza tasso: quelli dopo l'ultimo pubblicato (l'ISTAT lo comunica in ottobre-novembre
# dell'anno stesso). Nessuna rivalutazione inventata: il montante resta quello dell'ultimo tasso.
TASSO_CAP_DEFAULT = 1.000
# Primo anno del sistema contributivo: le retribuzioni precedenti valgono per la quota retributiva
# (L. 335/1995 art. 1 c. 12-13: fino al 1995, o fino al 2011 con 18 anni di contributi al 31/12/1995)
# e non entrano nel montante.
INIZIO_CONTRIBUTIVO = 1996

# Stima euristica della quota azionaria di un comparto dal suo nome (keyword → % azioni).
# Prima corrispondenza vince: le keyword SPECIFICHE precedono le generiche
# ("obbligazionar" prima di "azionar", che ne è una sottostringa).
MAPPA_AZIONARIA = [
    ("obbligazionar", 0.05), ("bond", 0.05),
    ("garantit", 0.00), ("monetar", 0.00), ("liquidit", 0.00), ("tfr", 0.00),
    ("prudent", 0.20),
    ("bilanciat", 0.50),
    ("dinamic", 0.60), ("crescita", 0.70), ("sviluppo", 0.70), ("espansion", 0.75),
    ("azionar", 0.90), ("equity", 0.90),
]

# =======================================================================


def _tag(e):
    """Nome del tag senza namespace."""
    return e.tag.split('}')[-1]


def _num_it(s):
    """Converte un numero in formato italiano ('1.234,56') o vuoto in float."""
    s = (s or "").strip()
    if not s:
        return 0.0
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


# ----------------------------- INPS (XML) -----------------------------

def leggi_estratto_inps(path):
    """Estrae anagrafica e righe contributive dall'XML dell'estratto conto INPS."""
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        sys.exit(f"ERRORE: '{path}' non è un XML valido ({e}).")

    # anagrafica
    anag = {}
    for e in root.iter():
        t = _tag(e)
        if t in ("Cognome", "Nome", "Sesso", "LuogoNascita") and (e.text or "").strip():
            anag[t] = e.text.strip()
        if t == "DataNascita":
            gg = {_tag(c): (c.text or "").strip() for c in e}
            if {"Giorno", "Mese", "Anno"} <= set(gg):
                anag["nascita"] = datetime.date(int(gg["Anno"]), int(gg["Mese"]), int(gg["Giorno"]))

    righe = []
    for rg in (e for e in root.iter() if _tag(e) == "RigaContributi"):
        nums = [c.text for c in rg.iter() if _tag(c) in ("Giorno", "Mese", "Anno") and c.text]
        if len(nums) < 6:
            continue  # riga senza periodo leggibile: la salto
        campi = {_tag(c): (c.text or "").strip()
                 for c in rg.iter() if _tag(c) not in ("Giorno", "Mese", "Anno", "RigaContributi")}
        try:
            riga = {
                "dal": datetime.date(int(nums[2]), int(nums[1]), int(nums[0])),
                "al": datetime.date(int(nums[5]), int(nums[4]), int(nums[3])),
                "tipo": campi.get("TipoContribuzione", ""),
                "settimane": int(float(campi.get("ContributiUtiliCalcolo", "0") or 0)),
                "retribuzione": float(campi.get("RetribuzioneEuro", "0") or 0),
                "datore": campi.get("Descrizione", ""),
            }
        except (ValueError, TypeError):
            continue
        righe.append(riga)

    if not righe:
        sys.exit("ERRORE: nessuna RigaContributi leggibile nell'XML. "
                 "Struttura diversa dall'estratto conto standard INPS?")
    return anag, righe


def ricostruisci_montante(retrib_per_anno, anno_corrente):
    """Montante contributivo ricostruito: contributi × aliquota, capitalizzati anno per anno.

    Meccanica (L.335/1995): al 31/12 di ogni anno X il montante accumulato al 31/12/(X-1)
    si rivaluta col tasso dell'anno X; i contributi dell'anno X entrano senza rivalutazione.
    Contano solo le retribuzioni dal 1996 (INIZIO_CONTRIBUTIVO): le precedenti sono quota retributiva.
    Restituisce (montante, contributi_nominali, anni_con_tasso_default).
    """
    montante, nominali, anni_default = 0.0, 0.0, []
    anni = [a for a in retrib_per_anno if a >= INIZIO_CONTRIBUTIVO]
    if not anni:
        return montante, nominali, anni_default
    for anno in range(min(anni), anno_corrente + 1):
        tasso = TASSI_CAPITALIZZAZIONE.get(anno)
        if tasso is None:
            if anno > min(anni):  # il primo anno parte da montante 0: il tasso non serve
                anni_default.append(anno)
            tasso = TASSO_CAP_DEFAULT
        montante *= tasso
        contributo = retrib_per_anno.get(anno, 0.0) * ALIQUOTA_COMPUTO
        montante += contributo
        nominali += contributo
    return montante, nominali, anni_default


# ------------------------- FONDO PENSIONE (CSV) -------------------------

def leggi_storico_fondo(path):
    """Legge lo storico movimenti del fondo (formato tipico: sep ';', decimali con virgola)."""
    with open(path, encoding="utf-8", errors="replace") as f:
        testa = f.read(4096)
    sep = ";" if testa.count(";") >= testa.count(",") else ","

    with open(path, encoding="utf-8", errors="replace") as f:
        rows = [{(k or "").strip(): (v or "").strip() for k, v in r.items()}
                for r in csv.DictReader(f, delimiter=sep)]
    if not rows:
        sys.exit(f"ERRORE: '{path}' vuoto o non leggibile come CSV.")

    def col(*candidati):
        """Trova la colonna reale che contiene una delle keyword (match case-insensitive)."""
        for k in rows[0]:
            kl = k.lower()
            if any(c in kl for c in candidati):
                return k
        return None

    C = {
        "data": col("avvalorato", "data"),
        "causale": col("causale"),
        "comparto": col("comparto", "linea"),
        "segno": col("segno"),
        "nav": col("valore quota", "nav"),
        "q_iscr": col("quote iscritto"), "q_az": col("quote azienda"), "q_tfr": col("quote tfr"),
        "c_iscr": col("contr. iscritto", "contributo iscritto"),
        "c_az": col("contr. azienda", "contributo azienda"),
        "c_tfr": col("contr. tfr", "contributo tfr"),
    }
    mancanti = [k for k in ("data", "comparto", "nav") if C[k] is None]
    if mancanti:
        sys.exit(f"ERRORE: colonne non riconosciute nel CSV: {mancanti}. "
                 f"Colonne trovate: {list(rows[0])}")

    quote = defaultdict(float)                      # comparto → quote nette
    nav = {}                                        # comparto → (data, NAV) più recente
    versamenti = defaultdict(lambda: defaultdict(float))  # anno → fonte → €
    for r in rows:
        segno = -1.0 if (C["segno"] and r.get(C["segno"], "") == "-") else 1.0
        comp = r.get(C["comparto"], "") or "(comparto non indicato)"
        try:
            data = datetime.datetime.strptime(r[C["data"]], "%d/%m/%Y").date()
        except (ValueError, KeyError):
            data = None

        q = sum(_num_it(r.get(C[k], "")) for k in ("q_iscr", "q_az", "q_tfr") if C[k])
        quote[comp] += q * segno

        v = _num_it(r.get(C["nav"], ""))
        if v > 0 and data and (comp not in nav or data > nav[comp][0]):
            nav[comp] = (data, v)

        causale = (r.get(C["causale"], "") or "").upper() if C["causale"] else ""
        if data and ("VERSAMENTO" in causale or "TFR PREGRESSO" in causale):
            for k, fonte in (("c_iscr", "iscritto"), ("c_az", "azienda"), ("c_tfr", "TFR")):
                if C[k]:
                    versamenti[data.year][fonte] += _num_it(r.get(C[k], "")) * segno
    return quote, nav, versamenti


def quota_azionaria(nome_comparto):
    nl = nome_comparto.lower()
    for kw, pct in MAPPA_AZIONARIA:
        if kw in nl:
            return pct, True
    return 0.50, False


# ================================ MAIN ================================

def main():
    if len(sys.argv) < 2:
        sys.exit("Uso: python importa-previdenza.py estratto_inps.xml [storico_fondo.csv]")
    path_xml = sys.argv[1]
    path_csv = sys.argv[2] if len(sys.argv) > 2 else None
    oggi = datetime.date.today()

    # ------------------------------ INPS ------------------------------
    anag, righe = leggi_estratto_inps(path_xml)
    print("=" * 72)
    print("PILASTRO PUBBLICO — estratto conto contributivo INPS")
    print("=" * 72)
    if anag.get("Cognome"):
        eta = ""
        if "nascita" in anag:
            n = anag["nascita"]
            anni = (oggi - n).days / 365.25
            eta = f" — nato {n.strftime('%d/%m/%Y')} ({anni:.1f} anni)"
        print(f"Intestatario: {anag.get('Cognome','')} {anag.get('Nome','')}{eta}")

    retrib = defaultdict(float)
    sett = defaultdict(int)
    for r in righe:
        retrib[r["al"].year] += r["retribuzione"]
        sett[r["al"].year] += r["settimane"]
    tot_sett = sum(sett.values())
    primo = min(r["dal"] for r in righe)

    print(f"Prima contribuzione: {primo.strftime('%m/%Y')} | "
          f"settimane utili: {tot_sett} (≈ {tot_sett/52:.2f} anni)")
    print(f"\n  {'anno':<6}{'retribuzione €':>15}{'settimane':>11}")
    for a in sorted(retrib):
        print(f"  {a:<6}{retrib[a]:>15,.0f}{sett[a]:>11}")

    montante, nominali, anni_def = ricostruisci_montante(retrib, oggi.year)
    anni_completi = [a for a in retrib if sett[a] >= 52]
    ral_rif = retrib[max(anni_completi)] if anni_completi else retrib[max(retrib)]

    print(f"\nContributi nominali (retribuzioni × {ALIQUOTA_COMPUTO:.0%}): € {nominali:,.0f}")
    print(f"MONTANTE CONTRIBUTIVO RICOSTRUITO: ≈ € {montante:,.0f}")
    print(f"  rivalutazione con tassi ufficiali ISTAT (PIL nominale quinquennale)")
    ultimo = max(TASSI_CAPITALIZZAZIONE)
    dopo = [a for a in anni_def if a > ultimo]
    prima = sorted(a for a in retrib if a < INIZIO_CONTRIBUTIVO)
    if dopo:
        print(f"  ⚠ tasso {ultimo + 1}{'-' + str(max(dopo)) if max(dopo) > ultimo + 1 else ''} "
              f"non ancora pubblicato: il montante al 31/12/{ultimo} non è ancora rivalutato "
              f"per gli anni successivi")
    if prima:
        anni_prima = sum(sett[a] for a in prima) / 52
        intervallo = f"{prima[0]}-{prima[-1]}" if len(prima) > 1 else f"{prima[0]}"
        print(f"  ⚠ retribuzioni prima del 1996 ({intervallo}, ≈ {anni_prima:.1f} anni): posizione mista, "
              "con una quota retributiva che lo script non calcola (L. 335/1995 art. 1 c. 12-13). "
              "Il montante sopra conta solo i contributi dal 1996")
        if anni_prima >= 18:
            print("    con 18 anni o più al 31/12/1995 la quota retributiva arriva al 2011: "
                  "il montante sopra è ancora più lontano dalla tua posizione")
        print("    per la pensione usa \"La mia pensione futura\" sul portale INPS, non proiezione-inps.py")
    print("  ⚠ ricostruzione ±qualche %: il valore esatto è ne \"La mia pensione futura\" (portale INPS)")

    # -------------------------- FONDO PENSIONE --------------------------
    fp_montante = None
    if path_csv:
        quote, nav, versamenti = leggi_storico_fondo(path_csv)
        print("\n" + "=" * 72)
        print("PILASTRO COMPLEMENTARE — storico movimenti del fondo pensione")
        print("=" * 72)
        fp_montante, az_ponderata, euristiche = 0.0, 0.0, False
        print(f"  {'comparto':<38}{'quote':>10}{'NAV':>9}{'valore €':>11}{'~%az':>6}")
        for comp in sorted(quote, key=lambda c: -quote[c] * nav.get(c, (None, 0))[1]):
            if abs(quote[comp]) < 1e-6:
                continue
            v_nav = nav.get(comp, (None, 0.0))[1]
            val = quote[comp] * v_nav
            pct, riconosciuto = quota_azionaria(comp)
            euristiche |= not riconosciuto
            fp_montante += val
            az_ponderata += val * pct
            flag = "" if riconosciuto else "?"
            print(f"  {comp[:37]:<38}{quote[comp]:>10.3f}{v_nav:>9.3f}{val:>11,.0f}{pct*100:>5.0f}{flag}")
        mix = az_ponderata / fp_montante if fp_montante else 0.0
        print(f"\nMONTANTE FONDO: ≈ € {fp_montante:,.0f} | mix azionario stimato ≈ {mix:.0%}")
        print("  ⚠ % azionaria EURISTICA dal nome del comparto"
              + (" ('?' = non riconosciuto, assunto 50%)" if euristiche else "")
              + ": verificala sulla nota informativa")

        if versamenti:
            print(f"\n  Versamenti per anno (€):")
            print(f"  {'anno':<6}{'iscritto':>10}{'azienda':>10}{'TFR':>10}{'totale':>10}")
            for a in sorted(versamenti):
                v = versamenti[a]
                tot = sum(v.values())
                print(f"  {a:<6}{v.get('iscritto',0):>10,.0f}{v.get('azienda',0):>10,.0f}"
                      f"{v.get('TFR',0):>10,.0f}{tot:>10,.0f}")
            ultimo_anno_v = max(a for a in versamenti if a < oggi.year) if \
                [a for a in versamenti if a < oggi.year] else max(versamenti)
            v_annuo = sum(versamenti[ultimo_anno_v].values())

    # -------------------------- PARAMETRI PRONTI --------------------------
    print("\n" + "=" * 72)
    print("PARAMETRI PRONTI (da incollare negli script della skill)")
    print("=" * 72)
    print("per proiezione-inps.py:")
    print(f"  MONTANTE_ATTUALE = {montante:,.0f}".replace(",", "_") +
          ("   # solo i contributi dal 1996: posizione mista, vedi l'avviso sopra" if prima else ""))
    print(f"  RAL_ATTUALE      = {ral_rif:,.0f}".replace(",", "_") +
          "   # ultima annualità completa dall'estratto: verifica con la RAL da contratto")
    if "nascita" in anag:
        print(f"  ETA_ATTUALE      = {(oggi - anag['nascita']).days / 365.25:.1f}")
    if fp_montante is not None:
        print("per montecarlo-pensione.py:")
        print(f"  FP_POT_ATTUALE      = {fp_montante:,.0f}".replace(",", "_"))
        if versamenti:
            print(f"  FP_VERSAMENTO_ANNUO = {v_annuo:,.0f}".replace(",", "_") +
                  f"   # osservato nel {ultimo_anno_v}: aggiorna se cambi contribuzione")
    print("\nQuesto strumento è educativo e non costituisce consulenza finanziaria o previdenziale.")


if __name__ == "__main__":
    main()
