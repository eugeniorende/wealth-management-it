#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_tests.py — smoke test suite del plugin wealth-management-it.

Uso (dalla radice del plugin o da qualunque directory):
    python tests/run_tests.py

Filosofia: nessuna dipendenza oltre a quelle del plugin (numpy, openpyxl).
Ogni test è veloce e verifica una proprietà ROBUSTA (invariante, valore chiuso,
regressione di un bug reale), non l'output cosmetico. La suite protegge i
refactor: se passa, la meccanica di calcolo non è cambiata.
"""

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")
FIXTURES = os.path.join(ROOT, "tests", "fixtures")

RISULTATI = []  # (nome, ok, dettaglio)


def asset(skill, nome):
    return os.path.join(SKILLS, skill, "assets", nome)


def carica_modulo(path):
    """Importa uno script (anche con trattini nel nome) come modulo."""
    spec = importlib.util.spec_from_file_location(
        os.path.basename(path).replace("-", "_").replace(".py", ""), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_script(path, *args, cwd=None):
    """Esegue uno script e ritorna (returncode, output)."""
    r = subprocess.run([sys.executable, path, *args],
                       capture_output=True, text=True, timeout=180,
                       cwd=cwd or os.path.dirname(path))
    return r.returncode, r.stdout + r.stderr


def euro(testo, etichetta):
    """Estrae il primo importo '€ 1.234' (o '€ 1,234') che segue l'etichetta."""
    m = re.search(re.escape(etichetta) + r"[^€\n]*€\s*([\d.,]+)", testo)
    if not m:
        raise AssertionError(f"etichetta '{etichetta}' non trovata nell'output")
    return float(m.group(1).replace(".", "").replace(",", ""))


def test(nome):
    def deco(fn):
        def wrapped():
            try:
                fn()
                RISULTATI.append((nome, True, ""))
            except Exception as e:  # noqa: BLE001 — un test fallito non ferma la suite
                RISULTATI.append((nome, False, f"{type(e).__name__}: {e}"))
        wrapped.__test__ = True
        wrapped.__nome__ = nome
        return wrapped
    return deco


# ═══════════════════════════ IGIENE DEL REPO ═══════════════════════════

@test("igiene: marketplace.json valido e coerente col plugin.json")
def t_marketplace():
    mk = json.load(open(os.path.join(ROOT, ".claude-plugin", "marketplace.json")))
    pl = json.load(open(os.path.join(ROOT, ".claude-plugin", "plugin.json")))
    assert mk.get("name") and mk.get("owner", {}).get("name"), "marketplace: name/owner mancanti"
    assert len(mk.get("plugins", [])) >= 1, "marketplace: nessun plugin elencato"
    voce = mk["plugins"][0]
    assert voce["name"] == pl["name"], "marketplace e plugin.json dichiarano nomi diversi"
    assert voce.get("source") == "./", "il plugin del marketplace deve puntare a './'"


@test("igiene: plugin.json valido, SKILL.md < 500 righe, nessun tag cite nei deliverable")
def t_igiene():
    d = json.load(open(os.path.join(ROOT, ".claude-plugin", "plugin.json")))
    assert re.match(r"^\d+\.\d+\.\d+$", d.get("version", "")), "version non semver"
    assert isinstance(d.get("author"), dict) and d["author"].get("name"), \
        "author deve essere un oggetto {name, ...} (claude plugin validate lo richiede)"
    assert str(d.get("repository", "")).startswith("https://github.com/"), \
        "repository mancante o non è un URL GitHub"
    for skill in sorted(os.listdir(SKILLS)):
        p = os.path.join(SKILLS, skill, "SKILL.md")
        if os.path.exists(p):
            n = sum(1 for _ in open(p, encoding="utf-8"))
            assert n < 500, f"{skill}/SKILL.md ha {n} righe (limite 500)"
    for base, _, files in os.walk(ROOT):
        for f in files:
            if f.endswith(".md"):
                testo = open(os.path.join(base, f), encoding="utf-8").read()
                assert "antml:cite" not in testo, f"tag cite in {f}"


@test("compilazione: tutti gli script Python compilano")
def t_compila():
    import py_compile
    trovati = 0
    for base, _, files in os.walk(SKILLS):
        for f in files:
            if f.endswith(".py"):
                py_compile.compile(os.path.join(base, f), doraise=True)
                trovati += 1
    assert trovati >= 10, f"attesi ≥10 script, trovati {trovati}"


# ══════════════════════ it-pianificazione (previdenza) ══════════════════════

@test("importa-previdenza: parser XML INPS su fixture (settimane, retribuzioni)")
def t_inps_parser():
    m = carica_modulo(asset("it-pianificazione", "importa-previdenza.py"))
    anag, righe = m.leggi_estratto_inps(os.path.join(FIXTURES, "estratto-inps-test.xml"))
    assert anag["Cognome"] == "ROSSI" and "nascita" in anag
    assert len(righe) == 2 and sum(r["settimane"] for r in righe) == 104
    assert abs(sum(r["retribuzione"] for r in righe) - 61000) < 0.01


@test("importa-previdenza: ricostruzione montante = formula replicata a mano")
def t_inps_montante():
    m = carica_modulo(asset("it-pianificazione", "importa-previdenza.py"))
    retrib = {2023: 30000.0, 2024: 31000.0}
    montante, nominali, _ = m.ricostruisci_montante(retrib, 2026)
    # replica indipendente della meccanica L.335/1995 con la stessa tabella tassi
    atteso = 0.0
    for anno in range(2023, 2027):
        atteso *= m.TASSI_CAPITALIZZAZIONE.get(anno, m.TASSO_CAP_DEFAULT)
        atteso += retrib.get(anno, 0.0) * m.ALIQUOTA_COMPUTO
    assert abs(montante - atteso) < 0.01, f"{montante} != {atteso}"
    assert abs(nominali - 61000 * m.ALIQUOTA_COMPUTO) < 0.01


@test("importa-previdenza: fondo su fixture + REGRESSIONE substring (obbligazionario ≠ azionario)")
def t_fondo():
    m = carica_modulo(asset("it-pianificazione", "importa-previdenza.py"))
    quote, nav, vers = m.leggi_storico_fondo(os.path.join(FIXTURES, "storico-fondo-test.csv"))
    val = {c: quote[c] * nav[c][1] for c in quote}
    assert abs(sum(val.values()) - 2000.0) < 0.01, f"montante fondo {sum(val.values())}"
    # regressione del bug reale: 'azionar' è sottostringa di 'obbligAZIONARio'
    pct_ob, _ = m.quota_azionaria("FONDO TEST COMPARTO OBBLIGAZIONARIO")
    pct_az, _ = m.quota_azionaria("FONDO TEST COMPARTO AZIONARIO")
    assert pct_ob == 0.05, f"obbligazionario → {pct_ob} (bug substring?)"
    assert pct_az == 0.90
    assert abs(sum(vers[2025].values()) - 2000.0) < 0.01


@test("proiezione-inps: valore chiuso via --set (formula annuità indipendente, PIL ≠ 0)")
def t_proiezione():
    rc, out = run_script(asset("it-pianificazione", "proiezione-inps.py"),
                         "--set", "MONTANTE_ATTUALE=100_000.0", "--set", "RAL_ATTUALE=30_000.0",
                         "--set", "ETA_ATTUALE=37.0", "--set", "ETA_PENSIONAMENTO=67.0",
                         "--set", "CRESCITA_REALE_RAL=0.0", "--set", "PIL_REALE=0.02",
                         "--set", "COEFF_ESPLICITO=0.05")
    assert rc == 0, out[-400:]
    assert "[override]" in out, "gli override applicati devono essere loggati"
    # verifica incrociata: lo script usa un loop, qui la formula chiusa dell'annuità.
    # Il PIL ≠ 0 rende osservabile la meccanica "l'ultimo anno non si rivaluta":
    # montante = 100k×1.02^30 + 9.900×(1.02^30 − 1)/0.02, pensione = montante × 5%.
    atteso = (100_000 * 1.02 ** 30 + 30_000 * 0.33 * ((1.02 ** 30 - 1) / 0.02)) * 0.05
    pens = euro(out, "PENSIONE LORDA ANNUA")
    assert abs(pens - atteso) <= 2, f"pensione {pens} != {atteso:.0f}"


@test("override --set: refuso su costante inesistente respinto con errore chiaro")
def t_override_refuso():
    rc, out = run_script(asset("it-pianificazione", "proiezione-inps.py"),
                         "--set", "COSTANTE_INESISTENTE=1")
    assert rc != 0, "un --set su costante inesistente deve fermare lo script"
    assert "sconosciuta" in out, out[-200:]


@test("montecarlo-pensione: run sui default, mediana simulata ≈ check deterministico")
def t_mc_pensione():
    rc, out = run_script(asset("it-pianificazione", "montecarlo-pensione.py"))
    assert rc == 0, out[-400:]
    det = euro(out, "montante FP deterministico")
    med = euro(out, "mediana simulata")
    dev = abs(det - med) / det
    assert dev < 0.20, f"mediana devia dal deterministico del {dev:.0%} (>20%)"


# ══════════════════ it-pianificazione-obiettivi (goals-based) ══════════════════

def _excel_test(obiettivi):
    """Copia del pianificatore con gli obiettivi dati; ritorna il path."""
    from openpyxl import load_workbook
    tmp = tempfile.mkdtemp()
    dst = os.path.join(tmp, "p.xlsx")
    shutil.copy(asset("it-pianificazione-obiettivi", "pianificatore-obiettivi.xlsx"), dst)
    wb = load_workbook(dst)
    o = wb["Obiettivi"]
    for i, (nome, target, oriz, prof, gia, prio, tipo) in enumerate(obiettivi):
        r = 5 + i
        for col, v in zip("ABCDFGN", (nome, target, oriz, prof, gia, prio, tipo)):
            o[f"{col}{r}"] = v
    r = 5 + len(obiettivi)
    for col in "ABCDFGN":
        o[f"{col}{r}"] = None
    wb.save(dst)
    return dst


@test("glidepath: REGRESSIONE obiettivi senza target (entrano, marcati (max), aggregato coerente)")
def t_glidepath_senza_target():
    xlsx = _excel_test([
        ("Con target", 50000, 10, "Moderato", 10000, "importante", "terminante"),
        ("Senza target", None, 20, "Crescita massima", 20000, "desiderabile", "permanente"),
    ])
    rc, out = run_script(asset("it-pianificazione-obiettivi", "glidepath-obiettivi.py"), xlsx)
    shutil.rmtree(os.path.dirname(xlsx), ignore_errors=True)
    assert rc == 0, out[-400:]
    assert "(max" in out, "marcatore (max) assente: obiettivo senza target saltato?"
    assert "PORTAFOGLIO" in out
    # il permanente senza target non de-riska: la sua colonna resta al 90% anche all'ultimo anno
    ultima = [r for r in out.splitlines() if re.match(r"\s*20\s\s", r)]
    assert ultima and "90%" in ultima[-1], "il permanente senza target deve restare al 90%"


@test("allocatore-capitale: invariante — la somma allocata è il capitale dato")
def t_allocatore():
    xlsx = _excel_test([
        ("Emergenza", 10000, 5, "Preservazione", 0, "essenziale", "permanente"),
        ("Casa", 40000, 12, "Moderato", 0, "importante", "terminante"),
    ])
    rc, out = run_script(asset("it-pianificazione-obiettivi", "allocatore-capitale.py"),
                         xlsx, "50000")
    shutil.rmtree(os.path.dirname(xlsx), ignore_errors=True)
    assert rc == 0, out[-400:]
    tot = sum(float(x.replace(".", "").replace(",", "."))
              for x in re.findall(r"€\s*([\d.]+,?\d*)\s", out.split("AGGREGATA")[-1])[:3])
    assert abs(tot - 50000) < 50, f"somma aggregata {tot} != 50000"


@test("montecarlo-obiettivi: obiettivo ampiamente finanziato → probabilità alta")
def t_mc_obiettivi():
    xlsx = _excel_test([("Quasi fatto", 10000, 10, "Moderato", 9500, "importante", "terminante")])
    rc, out = run_script(asset("it-pianificazione-obiettivi", "montecarlo-obiettivi.py"), xlsx)
    shutil.rmtree(os.path.dirname(xlsx), ignore_errors=True)
    assert rc == 0, out[-400:]
    probs = [float(p) for p in re.findall(r"(\d+(?:[.,]\d+)?)\s*%", out.replace(",", "."))]
    assert probs and max(probs) > 85, f"nessuna probabilità alta trovata (max {max(probs) if probs else '—'})"


@test("smoke: decumulo, asset-location, ribilanciamento, importa-estratto-broker girano")
def t_smoke_altri():
    rc, out = run_script(asset("it-pianificazione-obiettivi", "decumulo-obiettivi.py"))
    assert rc == 0 and "%" in out, "decumulo: " + out[-200:]
    rc, out = run_script(asset("it-pianificazione-obiettivi", "asset-location-optimizer.py"))
    assert rc == 0, "asset-location: " + out[-200:]
    tmp = tempfile.mkdtemp()  # il ribilanciamento scrive ordini/ nella cwd: non deve sporcare gli assets
    rc, out = run_script(asset("it-rebalance", "ribilanciamento-multibroker.py"), cwd=tmp)
    shutil.rmtree(tmp, ignore_errors=True)
    assert rc == 0, "ribilanciamento: " + out[-200:]
    rc, out = run_script(asset("it-tax-optimization", "importa-estratto-broker.py"),
                         os.path.join(FIXTURES, "estratto-broker-test.csv"))
    assert rc == 0 and ("ETF" in out or "BTP" in out), "importatore broker: " + out[-200:]


# ══════════════════════ motore bootstrap condiviso ══════════════════════

@test("sincronia: motore_bootstrap.py e rendimenti-storici.csv identici tra le due skill")
def t_sincronia():
    import hashlib
    def h(p):
        return hashlib.md5(open(p, "rb").read()).hexdigest()
    for nome in ("motore_bootstrap.py", "rendimenti-storici.csv"):
        a = h(asset("it-pianificazione", nome))
        b = h(asset("it-pianificazione-obiettivi", nome))
        assert a == b, f"{nome} DIVERGE tra le skill: riallineare le copie"


@test("motore bootstrap: blocchi circolari, valori dalla serie, riproducibile col seed")
def t_motore():
    import numpy as np
    m = carica_modulo(asset("it-pianificazione", "motore_bootstrap.py"))
    port = np.array([0.10, -0.05, 0.03, 0.20, -0.15, 0.07, 0.01])
    np.random.seed(7)
    idx = m.indici_bootstrap(len(port), n_sim=50, anni=12, blocco=5)
    assert idx.shape == (50, 12) and idx.min() >= 0 and idx.max() < len(port)
    # dentro un blocco gli indici sono consecutivi (circolari): idx[:,k+1] == (idx[:,k]+1) % n
    for k in range(4):  # il primo blocco copre le colonne 0..4
        assert (idx[:, k + 1] == (idx[:, k] + 1) % len(port)).all(), "blocco non consecutivo"
    np.random.seed(7)
    idx2 = m.indici_bootstrap(len(port), 50, 12, 5)
    assert (idx == idx2).all(), "stesso seed → indici diversi (non riproducibile)"
    np.random.seed(7)
    rend = m.blocchi_bootstrap(port, 50, 12, 5)
    assert (rend == port[idx]).all(), "blocchi_bootstrap incoerente con indici_bootstrap"
    assert set(np.unique(rend)) <= set(port), "il bootstrap ha inventato valori"


# ══════════════════════ it-revisione (generatore IPS) ══════════════════════

@test("genera-ips: documento completo (sezioni, tabelle, nota di rischio calibrata)")
def t_genera_ips():
    try:
        from docx import Document
    except ImportError:
        raise AssertionError("python-docx non installato: pip install python-docx")
    tmp = tempfile.mkdtemp()
    out = os.path.join(tmp, "ips.docx")
    rc, log = run_script(asset("it-revisione", "genera-ips.py"), out)
    assert rc == 0, log[-400:]
    doc = Document(out)
    testo = "\n".join(p.text for p in doc.paragraphs)
    shutil.rmtree(tmp, ignore_errors=True)
    assert len(doc.tables) >= 3, f"solo {len(doc.tables)} tabelle"
    for chiave in ("INVESTMENT POLICY STATEMENT", "Obiettivi", "Glide path",
                   "ribilanciamento", "Appendice A", "Onestà sul rischio"):
        assert chiave in testo, f"sezione mancante: {chiave}"
    # la nota di rischio è CALCOLATA dalla quota azionaria (57% nell'esempio → ~28%)
    m = re.search(r"perdere circa il (\d+)%", testo)
    assert m and abs(int(m.group(1)) - 28) <= 1, "nota di rischio non calibrata sull'allocazione"


# ══════════════════════ fiscalità e tracker ══════════════════════

@test("netto-pensione: IRPEF 2026, detrazioni e aliquota rendita FP (valori chiusi)")
def t_netto():
    d = os.path.join(SKILLS, "it-pianificazione", "assets")
    sys.path.insert(0, d)
    try:
        m = carica_modulo(os.path.join(d, "netto-pensione.py"))
    finally:
        sys.path.remove(d)
    assert abs(m.irpef_lorda(30_000) - 7_100) < 0.01      # 6.440 + 660 (scaglione 33%, L.199/2025)
    assert abs(m.irpef_lorda(50_000) - 13_700) < 0.01
    assert abs(m.detrazione_pensione(8_500) - 1_955) < 0.01
    assert m.detrazione_pensione(60_000) == 0.0
    assert m.aliquota_rendita_fp(15) == 0.15
    assert abs(m.aliquota_rendita_fp(20) - 0.135) < 1e-9
    assert m.aliquota_rendita_fp(37) == 0.09              # floor
    # valore chiuso: pensione 27.138 → IRPEF 6.241,74 − detr 755,48; addizionali 2,23%
    netto, irpef, addiz = m.netto_pensionato(27_138, 0.0173, 0.005)
    att_irpef = 27_138 * 0.23 - (700 + 1_255 * (28_000 - 27_138) / 19_500)
    assert abs(irpef - att_irpef) < 0.01 and abs(addiz - 27_138 * 0.0223) < 0.01
    assert abs(netto - (27_138 - att_irpef - 27_138 * 0.0223)) < 0.01


@test("tracker-secchielli: fogli, formule vive, semaforo demo funzionante")
def t_tracker():
    from openpyxl import load_workbook
    p = asset("it-revisione", "tracker-secchielli.xlsx")
    wb = load_workbook(p)
    for foglio in ("Leggimi", "Impostazioni", "Glide", "Posizioni", "Controllo", "Versamenti"):
        assert foglio in wb.sheetnames, f"foglio mancante: {foglio}"
    assert str(wb["Controllo"]["B5"].value).startswith("=IF") and "SUMIFS" in str(wb["Controllo"]["B5"].value)
    assert len(wb["Posizioni"].data_validations.dataValidation) >= 2, "tendine mancanti"
    wv = load_workbook(p, data_only=True)  # il file è recalcolato: i valori demo devono esserci
    c = wv["Controllo"]
    assert c["G7"].value == "RIBILANCIA", "il semaforo demo (Lungo termine oltre banda) non scatta"
    assert c["G6"].value == "OK" and c["B18"].value and c["B18"].value > 100_000


@test("ponte-pensione: proprietà limite (capitale enorme, spesa zero, RITA copre tutto)")
def t_ponte():
    sc = asset("it-pianificazione", "ponte-pensione.py")
    def prob(*sets):
        rc, out = run_script(sc, *sets)
        assert rc == 0, out[-300:]
        m = re.search(r"PROBABILITÀ di coprire il ponte: ([\d.]+)%", out)
        return float(m.group(1))
    assert prob("--set", "CAPITALE_PONTE=10_000_000.0") == 100.0
    assert prob("--set", "SPESA_ANNUA_PONTE=0.0", "--set", "CAPITALE_PONTE=0.0") == 100.0
    # RITA dall'uscita con rata netta > spesa: il capitale non serve
    assert prob("--set", "CAPITALE_PONTE=0.0", "--set", "ANNI_MAX_RITA=10",
                "--set", "SPESA_ANNUA_PONTE=20000.0") == 100.0
    # e il capitale necessario per confidenza è monotono nel senso giusto: con RITA
    # ordinaria (5 anni) e capitale 0, la probabilità NON può essere 100
    assert prob("--set", "CAPITALE_PONTE=0.0", "--set", "ANNI_MAX_RITA=5") < 100.0


# ══════════════════════ freshness · json · guardia ══════════════════════

@test("freshness fiscale: marcatori 'Verificato: AAAA-MM' presenti (≥7) e ≤12 mesi")
def t_freshness():
    import datetime
    trovati = []
    for base, _, files in os.walk(SKILLS):
        for f in files:
            if f.endswith((".py", ".md")):
                testo = open(os.path.join(base, f), encoding="utf-8", errors="replace").read()
                for m in re.finditer(r"Verificato: (\d{4})-(\d{2})", testo):
                    trovati.append((f, int(m.group(1)), int(m.group(2))))
    assert len(trovati) >= 7, f"attesi ≥7 marcatori freshness, trovati {len(trovati)}"
    oggi = datetime.date.today()
    for f, a, m in trovati:
        eta = (oggi.year - a) * 12 + (oggi.month - m)
        assert 0 <= eta <= 12, (f"{f}: dato normativo verificato {a}-{m:02d}, {eta} mesi fa. "
                                "È il design: i dati fiscali scadono — riverificare alle fonti "
                                "e aggiornare il marcatore.")


@test("pipeline --json: proiezione-inps scrive i risultati chiave su file")
def t_json():
    import json as _json
    tmp = tempfile.mkdtemp()
    out = os.path.join(tmp, "p.json")
    rc, log = run_script(asset("it-pianificazione", "proiezione-inps.py"),
                         "--set", "MONTANTE_ATTUALE=100_000.0", "--set", "RAL_ATTUALE=30_000.0",
                         "--set", "ETA_ATTUALE=37.0", "--set", "ETA_PENSIONAMENTO=67.0",
                         "--set", "CRESCITA_REALE_RAL=0.0", "--set", "PIL_REALE=0.02",
                         "--set", "COEFF_ESPLICITO=0.05", "--json", out)
    assert rc == 0, log[-300:]
    d = _json.load(open(out))
    shutil.rmtree(tmp, ignore_errors=True)
    atteso = (100_000 * 1.02 ** 30 + 30_000 * 0.33 * ((1.02 ** 30 - 1) / 0.02)) * 0.05
    assert abs(d["pensione_inps_lorda_annua"] - atteso) <= 2
    for k in ("montante_finale", "ral_finale", "tasso_sostituzione_lordo_vs_ral_finale"):
        assert k in d, f"chiave JSON mancante: {k}"


@test("guardia intestazioni: colonna spostata → errore esplicito, non dati sbagliati")
def t_guardia():
    from openpyxl import load_workbook
    tmp = tempfile.mkdtemp()
    rotto = os.path.join(tmp, "rotto.xlsx")
    shutil.copy(asset("it-pianificazione-obiettivi", "pianificatore-obiettivi.xlsx"), rotto)
    wb = load_workbook(rotto)
    wb["Obiettivi"]["B4"] = "Colonna a caso"
    wb.save(rotto)
    rc, out = run_script(asset("it-pianificazione-obiettivi", "glidepath-obiettivi.py"), rotto)
    shutil.rmtree(tmp, ignore_errors=True)
    assert rc != 0, "lo script deve FALLIRE su layout non riconosciuto"
    assert "NON riconosciuta" in out, out[-300:]


@test("runner: --only/--skip filtrano i test per sottostringa del nome")
def t_filtro():
    me = os.path.abspath(__file__)
    r = subprocess.run([sys.executable, me, "--only", "freshness"],
                       capture_output=True, text=True, timeout=120)
    assert "1/1 test passati" in r.stdout, r.stdout[-400:]
    assert "freshness fiscale" in r.stdout
    r = subprocess.run([sys.executable, me, "--skip", "freshness", "--only", "igiene"],
                       capture_output=True, text=True, timeout=120)
    assert "2/2 test passati" in r.stdout, r.stdout[-400:]
    assert "freshness" not in r.stdout
    r = subprocess.run([sys.executable, me, "--only", "nome-inesistente"],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode != 0, "nessun test selezionato deve essere un errore, non un verde vuoto"


# ═══════════════════════════════ RUNNER ═══════════════════════════════

def seleziona(tests, only, skip):
    """Filtra i test per sottostringa (case-insensitive) del nome dichiarato."""
    def nome(fn):
        return fn.__nome__.lower()
    if only:
        tests = [fn for fn in tests if any(o.lower() in nome(fn) for o in only)]
    if skip:
        tests = [fn for fn in tests if not any(k.lower() in nome(fn) for k in skip)]
    return tests


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Smoke test suite del plugin wealth-management-it.")
    ap.add_argument("--only", action="append", metavar="NOME",
                    help="esegui solo i test il cui nome contiene NOME (ripetibile)")
    ap.add_argument("--skip", action="append", metavar="NOME",
                    help="salta i test il cui nome contiene NOME (ripetibile)")
    args = ap.parse_args()

    print("=" * 74)
    print("SMOKE TEST SUITE — wealth-management-it")
    print("=" * 74)
    tests = [v for v in globals().values() if getattr(v, "__test__", False)]
    tests = seleziona(tests, args.only, args.skip)
    if not tests:
        print("Nessun test selezionato: controlla --only/--skip.")
        sys.exit(2)
    for fn in tests:
        fn()
    ok = sum(1 for _, esito, _ in RISULTATI if esito)
    for nome, esito, dett in RISULTATI:
        print(("  ✅ " if esito else "  ❌ ") + nome)
        if not esito:
            print("       → " + dett)
    print("-" * 74)
    print(f"{ok}/{len(RISULTATI)} test passati")
    sys.exit(0 if ok == len(RISULTATI) else 1)


if __name__ == "__main__":
    main()
