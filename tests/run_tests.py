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


class Salta(Exception):
    """Il test non si può eseguire in questo ambiente (es. LibreOffice assente)."""


def test(nome):
    def deco(fn):
        def wrapped():
            try:
                fn()
                RISULTATI.append((nome, True, ""))
            except Salta as e:
                RISULTATI.append((nome, None, str(e)))
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


@test("igiene CI: i workflow che usano una pipe nei run girano con pipefail")
def t_pipefail():
    # Senza "shell: bash" GitHub usa `bash -e {0}`, senza pipefail: in
    # `comando | tee log` l'exit code è quello di tee e un fallimento passa verde.
    cartella = os.path.join(ROOT, ".github", "workflows")
    for nome in sorted(os.listdir(cartella)):
        righe = open(os.path.join(cartella, nome), encoding="utf-8").read().splitlines()
        con_pipe, blocco = [], None
        for riga in righe:
            rientro = len(riga) - len(riga.lstrip())
            if blocco is not None and riga.strip() and rientro <= blocco:
                blocco = None
            m = re.match(r"^(\s*)(?:- )?run:\s*(.*)$", riga)
            if m:
                if m.group(2)[:1] in ("|", ">"):
                    blocco = len(m.group(1))
                    continue
                comando = m.group(2)
            elif blocco is not None:
                comando = riga
            else:
                continue
            if re.search(r"(?<!\|)\|(?!\|)", comando):
                con_pipe.append(comando.strip())
        if con_pipe:
            testo = "\n".join(righe)
            assert re.search(r"^defaults:\s*\n\s+run:\s*\n\s+shell:\s*bash\s*$", testo, re.M), \
                f"{nome}: pipe senza pipefail ({con_pipe[0]!r}); aggiungere defaults.run.shell: bash"


@test("igiene CI: le action dei workflow sono fissate per SHA completo")
def t_action_sha():
    # Supply chain: un tag (@v4) può essere spostato da chi controlla l'action, uno SHA no.
    # Dependabot aggiorna SHA e commento di versione.
    cartella = os.path.join(ROOT, ".github", "workflows")
    for nome in sorted(os.listdir(cartella)):
        for n, riga in enumerate(open(os.path.join(cartella, nome), encoding="utf-8"), 1):
            m = re.search(r"uses:\s*([^\s#]+)", riga)
            if m:
                assert re.search(r"@[0-9a-f]{40}$", m.group(1)), f"{nome}:{n}: action non fissata per SHA ({m.group(1)})"


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


@test("serie storica: gli script la trovano anche lanciati dalla cartella di lavoro dell'utente")
def t_cwd_esterna():
    # REGRESSIONE F005: ponte e montecarlo-pensione aprivano rendimenti-storici.csv
    # rispetto alla cwd e andavano in FileNotFoundError fuori da assets/.
    tmp = tempfile.mkdtemp()
    try:
        for skill, nome, *args in (("it-pianificazione", "ponte-pensione.py"),
                                   ("it-pianificazione", "montecarlo-pensione.py"),
                                   ("it-pianificazione-obiettivi", "montecarlo-obiettivi.py",
                                    "--set", "MODELLO=bootstrap"),
                                   ("it-pianificazione-obiettivi", "decumulo-obiettivi.py")):
            rc, out = run_script(asset(skill, nome), *args, cwd=tmp)
            assert rc == 0, f"{nome} da una cartella esterna: {out[-300:]}"
            assert "serie storica non trovata" not in out, f"{nome}: serie storica non trovata"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


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
    # F022: azzera TUTTE le righe residue (5..14): prima restava la riga demo 7 con un solo obiettivo
    for r in range(5 + len(obiettivi), 15):
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


def _prob_obiettivi(out):
    """{nome: probabilità di successo col versamento deterministico} dall'output di montecarlo-obiettivi."""
    return {nome: int(re.search(r"Probabilità di successo con questo versamento: (\d+)%", testo).group(1))
            for nome, (_, _, testo) in _sezioni_obiettivi(out).items()}


@test("montecarlo-obiettivi: obiettivo ampiamente finanziato → probabilità alta, controllo a bassa volatilità ≈ 50%")
def t_mc_obiettivi():
    # F022: la fixture lasciava la riga demo 7 e il regex prendeva la quota azionaria dell'OPZIONE
    # (~100%) invece della probabilità: il mutante «già accantonato ignorato» passava.
    xlsx = _excel_test([("Sovra-finanziato", 10000, 10, "Moderato", 14000, "importante", "terminante"),
                        ("Controllo", 20000, 10, "Preservazione", 6000, "importante", "terminante")])
    rc, out = run_script(asset("it-pianificazione-obiettivi", "montecarlo-obiettivi.py"), xlsx)
    shutil.rmtree(os.path.dirname(xlsx), ignore_errors=True)
    assert rc == 0, out[-400:]
    prob = _prob_obiettivi(out)
    assert set(prob) == {"Sovra-finanziato", "Controllo"}, f"obiettivi letti: {sorted(prob)} (riga demo residua?)"
    assert prob["Sovra-finanziato"] >= 95, f"14.000 accantonati su 12.190 nominali: probabilità {prob['Sovra-finanziato']}%"
    # versamento deterministico a volatilità 1,5%: ~50%. Se il già accantonato è ignorato nella
    # simulazione la probabilità crolla; se è ignorato nel versamento sale verso il 100%.
    assert 40 <= prob["Controllo"] <= 55, f"controllo Preservazione: probabilità {prob['Controllo']}%, attesa 40-55%"


def _sezioni_obiettivi(out):
    """{nome: (anni, priorità, testo della sezione)} dall'output di montecarlo-obiettivi."""
    sezioni = {}
    for m in re.finditer(r"▸ (.+?)  \[[^,]+, (\d+) anni, priorità: ([^\]]*)\]\n(.*?)(?=\n▸ |\n={10,})", out, re.S):
        sezioni[m.group(1)] = (int(m.group(2)), m.group(3).strip().lower(), m.group(4))
    return sezioni


@test("montecarlo-obiettivi: la leva di rischio è un'OPZIONE solo per i desiderabili oltre la finestra di de-risking")
def t_leva_rischio():
    # REGRESSIONE F017: sui default proponeva ~95% azionario per l'anticipo casa a 6 anni.
    rc, out = run_script(asset("it-pianificazione-obiettivi", "montecarlo-obiettivi.py"))
    assert rc == 0, out[-400:]
    sezioni = _sezioni_obiettivi(out)
    assert "Anticipo casa" in sezioni, f"obiettivo d'esempio non trovato: {list(sezioni)}"
    assert "INADATTA" in sezioni["Anticipo casa"][2], "anticipo casa a 6 anni: la leva deve essere INADATTA"
    for nome, (anni, prio, testo) in sezioni.items():
        if anni <= 7 or not prio.startswith("desider"):
            assert "OPZIONE:" not in testo, f"{nome} ({anni} anni, {prio}): OPZIONE fuori dal gate"
    # il gate non spegne la leva: un desiderabile lungo e sotto-finanziato la riceve ancora
    xlsx = _excel_test([("Barca", 400000, 20, "Moderato", 0, "desiderabile", "terminante")])
    rc, out = run_script(asset("it-pianificazione-obiettivi", "montecarlo-obiettivi.py"), xlsx)
    shutil.rmtree(os.path.dirname(xlsx), ignore_errors=True)
    assert rc == 0, out[-400:]
    assert "OPZIONE:" in _sezioni_obiettivi(out)["Barca"][2], "desiderabile a 20 anni: OPZIONE attesa"


@test("decumulo-obiettivi: il bootstrap a blocchi campiona ogni anno della serie, ultimo compreso")
def t_decumulo_indici():
    # REGRESSIONE F029: start = integers(0, n - BLOCCO) escludeva l'ultimo anno (2025).
    import numpy as np
    cartella = os.path.join(SKILLS, "it-pianificazione-obiettivi", "assets")
    sys.path.insert(0, cartella)
    try:
        mod = carica_modulo(os.path.join(cartella, "decumulo-obiettivi.py"))
    finally:
        sys.path.remove(cartella)
    n = 98
    rng = np.random.default_rng(0)
    visti = np.zeros(n, dtype=int)
    for _ in range(3000):
        for i in mod.percorso_bootstrap(np.arange(n, dtype=float), rng):
            visti[int(i)] += 1
    assert visti.min() > 0, f"anni mai campionati: {np.flatnonzero(visti == 0).tolist()}"


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


@test("postura: ogni comando chiede in fondo il disclaimer «non è consulenza»")
def t_disclaimer_comandi():
    cartella = os.path.join(ROOT, "commands")
    for nome in sorted(os.listdir(cartella)):
        testo = open(os.path.join(cartella, nome), encoding="utf-8").read()
        assert re.search(r"[Dd]isclaimer obbligatorio[^:\n]*:[^\n]*consulenza", testo), \
            f"commands/{nome}: manca «Disclaimer obbligatorio …: … consulenza …»"


@test("ribilanciamento: CSV degli ordini e stdout portano il disclaimer, intestazione invariata")
def t_disclaimer_csv():
    import csv
    import glob
    tmp = tempfile.mkdtemp()
    try:
        rc, out = run_script(asset("it-rebalance", "ribilanciamento-multibroker.py"), cwd=tmp)
        assert rc == 0, out[-300:]
        assert "non costituisce consulenza" in out, "stdout senza disclaimer"
        files = glob.glob(os.path.join(tmp, "ordini", "ordini_*.csv"))
        assert files, "nessun CSV degli ordini"
        for path in files:
            with open(path, encoding="utf-8", newline="") as f:
                righe = list(csv.DictReader(f))
            assert righe and righe[-1]["operazione"] == "NOTA", f"{os.path.basename(path)}: manca la riga NOTA finale"
            assert "non costituisce consulenza" in righe[-1]["nota"], f"{os.path.basename(path)}: nota senza disclaimer"
            assert all(r["operazione"] in ("VENDITA", "ACQUISTO") for r in righe[:-1]), "righe d'ordine alterate"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

# ══════════════════════ obiettivi (T8) ══════════════════════

def _modulo_obiettivi(nome):
    """Importa uno script di it-pianificazione-obiettivi (con il suo motore_bootstrap)."""
    cartella = os.path.join(SKILLS, "it-pianificazione-obiettivi", "assets")
    sys.path.insert(0, cartella)
    try:
        return carica_modulo(os.path.join(cartella, nome))
    finally:
        sys.path.remove(cartella)


def _testo_obiettivi(rel):
    return open(os.path.join(SKILLS, "it-pianificazione-obiettivi", rel), encoding="utf-8").read()


def _euro_it(x):
    return f"€{x:,.0f}".replace(",", ".")


def _pct_it(x, decimali=1):
    return f"{x:.{decimali}f}".replace(".", ",")


def _pmt_anno_per_anno(target, gia, rend, rend_atterraggio, anni, finestra):
    """Replica indipendente del versamento col calendario annuale del glide path: la quota
    dell'anno y è quella del calendario a inizio anno (anni residui = anni − y), il rendimento
    è lineare nella quota tra il profilo e l'atterraggio; 12 versamenti di fine mese."""
    w = min(finestra, anni)
    tassi = [rend_atterraggio + (rend - rend_atterraggio) * (1.0 if anni - y >= w else (anni - y) / w)
             for y in range(anni)]
    crescita, coeff = 1.0, 0.0
    for r in reversed(tassi):  # FV = gia·Π(1+r) + PMT·Σ a(r_y)·Π_{z>y}(1+r_z)
        coeff += (12.0 if r == 0 else r / ((1 + r) ** (1 / 12) - 1)) * crescita
        crescita *= 1 + r
    return (target - gia * crescita) / coeff, crescita


def _obiettivi_foglio():
    """Obiettivi e parametri del pianificatore d'esempio, dalle cache ricalcolate."""
    from openpyxl import load_workbook
    wb = load_workbook(xlsx_ricalcolati()[asset("it-pianificazione-obiettivi", "pianificatore-obiettivi.xlsx")],
                       data_only=True)
    par, obj = wb["Parametri"], wb["Obiettivi"]
    profili = {par[f"A{r}"].value: (par[f"B{r}"].value, par[f"C{r}"].value, par[f"D{r}"].value)
               for r in range(10, 16) if par[f"A{r}"].value}
    obiettivi = []
    for r in range(5, 15):
        if obj[f"A{r}"].value:
            obiettivi.append({c: obj[f"{col}{r}"].value for c, col in (
                ("nome", "A"), ("target", "B"), ("anni", "C"), ("profilo", "D"), ("gia", "F"),
                ("priorita", "G"), ("versamento", "I"), ("tipo", "N"))})
    return par, profili, obiettivi


@test("obiettivi: versamento col glide path ≥ quota fissa, stesso numero in foglio, motore, Monte Carlo e glide path")
def t_versamento_glide():
    # F040: gli obiettivi terminanti de-riskano negli ultimi anni, ma il versamento usava il
    # rendimento pieno del profilo (shortfall ~10% a 20 anni). Il foglio approssima la rampa col
    # suo rendimento medio: sugli obiettivi d'esempio entro l'1,5% dal calcolo anno per anno, mai
    # sotto la quota fissa (l'errore per profilo e finestra è in t_errore_due_fasi).
    par, profili, obiettivi = _obiettivi_foglio()
    infl = par["B6"].value
    rend_l = min(profili.values(), key=lambda p: p[2])[0]   # rendimento all'atterraggio (0% azionario)
    finestra = 7
    attesi = {}
    for g in obiettivi:
        rend, _, quota = profili[g["profilo"]]
        target_nom = g["target"] * (1 + infl) ** g["anni"]
        fisso, _ = _pmt_anno_per_anno(target_nom, g["gia"] or 0, rend, rend, g["anni"], finestra)
        foglio = g["versamento"]
        if g["tipo"] == "permanente" or quota == 0:
            assert abs(foglio - fisso) < 0.01, f"{g['nome']}: permanente €{foglio:.2f} ≠ quota fissa €{fisso:.2f}"
        else:
            esatto, _ = _pmt_anno_per_anno(target_nom, g["gia"] or 0, rend, rend_l, g["anni"], finestra)
            assert foglio >= 0.985 * esatto, (f"{g['nome']}: il foglio chiede €{foglio:.0f}/mese, col glide path "
                                              f"ne servono €{esatto:.0f}: de-risking ignorato nel versamento")
            assert fisso < foglio <= esatto + 0.01, f"{g['nome']}: €{foglio:.2f} fuori da [{fisso:.2f}, {esatto:.2f}]"
        attesi[g["nome"]] = (foglio, target_nom, g, rend)
    assert "finestra" in str(par["A7"].value).lower() and par["B7"].value == finestra, \
        "Parametri!A7:B7 deve portare la finestra di de-risking (7 anni, come glidepath-obiettivi.py)"
    motore = _modulo_obiettivi("motore_bootstrap.py")
    for nome, (foglio, target_nom, g, rend) in attesi.items():
        glide = g["tipo"] != "permanente" and profili[g["profilo"]][2] > 0
        calcolo = motore.pmt_glide(target_nom, g["gia"] or 0, rend, rend_l if glide else rend, g["anni"], finestra)
        assert abs(calcolo - foglio) < 0.01, f"{nome}: motore €{calcolo:.2f} ≠ foglio €{foglio:.2f}"
    rc, out = run_script(asset("it-pianificazione-obiettivi", "montecarlo-obiettivi.py"))
    assert rc == 0, out[-400:]
    for nome, (_, _, testo) in _sezioni_obiettivi(out).items():
        m = re.search(r"Versamento deterministico:\s*(€[\d.]+)/mese", testo)
        assert m and m.group(1) == _euro_it(attesi[nome][0]), f"Monte Carlo, {nome}: {m and m.group(1)} ≠ foglio"
    rc, out = run_script(asset("it-pianificazione-obiettivi", "glidepath-obiettivi.py"))
    assert rc == 0, out[-400:]
    assert "VERSAMENTI" in out, "glidepath: manca il riepilogo dei versamenti usati nella proiezione"
    for nome, (foglio, *_) in attesi.items():
        m = re.search(re.escape(nome) + r"[^\n]*?(€[\d.]+)/mese", out.split("VERSAMENTI")[-1])
        assert m and m.group(1) == _euro_it(foglio), f"glide path, {nome}: {m and m.group(1)} ≠ foglio"
    # allocatore: il capitale richiesto oggi da un terminante segue la stessa crescita col glide
    tmp = tempfile.mkdtemp()
    try:
        rc, out = run_script(asset("it-pianificazione-obiettivi", "allocatore-capitale.py"),
                             "--json", os.path.join(tmp, "a.json"))
        assert rc == 0, out[-400:]
        righe = {r["nome"]: r for r in json.load(open(os.path.join(tmp, "a.json")))["obiettivi"]}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    g = attesi["Lungo termine / libertà"][2]
    rend = profili[g["profilo"]][0]
    target_nom = g["target"] * (1 + infl) ** g["anni"]
    _, crescita = _pmt_anno_per_anno(target_nom, 0, rend, rend_l, g["anni"], finestra)
    atteso = target_nom / crescita - (g["gia"] or 0)
    assert abs(righe[g["nome"]]["richiesto"] - atteso) < 1, \
        f"allocatore: richiesto €{righe[g['nome']]['richiesto']:.0f}, col glide path €{atteso:.0f}"


@test("obiettivi: l'errore della formula in due fasi è quello documentato, per profilo e finestra")
def t_errore_due_fasi():
    # Revisione T8: «sbaglia per difetto di meno dell'1,5%» era falso già con la finestra di
    # default (Crescita massima 1,7%, Azionario totale 1,8%) e con la finestra di 10 anni, che
    # glide-path.md propone, arriva al 3%. Il caso peggiore è un orizzonte pari alla finestra.
    motore = _modulo_obiettivi("motore_bootstrap.py")
    _, profili, _ = _obiettivi_foglio()
    rend_l = min(profili.values(), key=lambda p: p[2])[0]

    def errore_max(rend, finestra):
        peggiore = 0.0
        for n in range(1, 41):
            target = 100_000 * 1.02 ** n
            esatto, _ = _pmt_anno_per_anno(target, 0, rend, rend_l, n, finestra)
            peggiore = max(peggiore, 1 - motore.pmt_glide(target, 0, rend, rend_l, n, finestra) / esatto)
        return peggiore * 100

    err = {(nome, f): errore_max(p[0], f) for nome, p in profili.items() if p[2] > 0 for f in (7, 10)}
    for (nome, f), e in err.items():
        assert e >= 0, f"{nome}, finestra {f}: la formula in due fasi non sbaglia per difetto"
        if f == 7:
            assert e < 2, f"{nome}: errore {e:.2f}% con la finestra di default, oltre il 2%"
    assert err[("Moderato", 7)] < 1, f"Moderato: errore {err[('Moderato', 7)]:.2f}%, documentato sotto l'1%"
    frasi = ("sotto l'1% con Moderato",
             f"{_pct_it(err[('Crescita', 7)])}% con Crescita",
             f"{_pct_it(err[('Azionario totale', 7)])}% con Azionario totale",
             f"{_pct_it(err[('Crescita massima', 10)])}% con Crescita massima",
             f"{_pct_it(err[('Azionario totale', 10)])}% con Azionario totale")
    motore_txt = open(asset("it-pianificazione-obiettivi", "motore_bootstrap.py"), encoding="utf-8").read()
    for rel, testo in (("references/glide-path.md", _testo_obiettivi("references/glide-path.md")),
                       ("references/matematica-accumulo.md", _testo_obiettivi("references/matematica-accumulo.md")),
                       ("motore_bootstrap.py", " ".join(motore_txt.split()))):
        testo = " ".join(testo.split())
        assert "meno dell'1,5%" not in testo, f"{rel}: «meno dell'1,5%» vale solo fino al profilo Crescita"
        for frase in frasi:
            assert frase in testo, f"{rel}: manca «{frase}» (errore misurato)"


@test("glidepath e Monte Carlo: «come la colonna I» solo coi parametri del foglio, avviso sui pianificatori vecchi")
def t_glide_come_foglio():
    # Revisione T8: su un pianificatore compilato prima della 0.10.0 (senza Parametri!B7, colonna I
    # a quota fissa) o con ATTERRAGGIO_AZ/CURVATURA/FINESTRA_DERISK cambiati, gli script davano un
    # versamento diverso dal foglio dichiarandolo «come la colonna I».
    from openpyxl import load_workbook
    gp = asset("it-pianificazione-obiettivi", "glidepath-obiettivi.py")
    mc = asset("it-pianificazione-obiettivi", "montecarlo-obiettivi.py")
    rc, out = run_script(gp)
    assert rc == 0 and "come la colonna I del foglio" in out, "default: i versamenti sono quelli della colonna I"
    assert "0.10.0" not in out, "default: avviso sul pianificatore vecchio fuori luogo"
    for args in (("--set", "CURVATURA=0.5"), ("--set", "ATTERRAGGIO_AZ=0.2"), ("--set", "FINESTRA_DERISK=5")):
        rc, out = run_script(gp, *args)
        assert rc == 0, out[-400:]
        assert "come la colonna I" not in out and "DIVERSI dalla colonna I" in out, f"{args}: versamenti spacciati per la colonna I"
        rc, out = run_script(mc, *args)
        assert rc == 0 and "non è quello della colonna I" in out, f"Monte Carlo {args}: manca l'avviso"
    xlsx = _excel_test([("Casa", 40000, 6, "Moderato", 5000, "importante", "terminante")])
    try:
        wb = load_workbook(xlsx)
        wb["Parametri"]["A7"] = None
        wb["Parametri"]["B7"] = None
        wb.save(xlsx)
        for script in (gp, mc, asset("it-pianificazione-obiettivi", "allocatore-capitale.py")):
            rc, out = run_script(script, xlsx)
            assert rc == 0, out[-400:]
            assert "prima della 0.10.0" in out, f"{os.path.basename(script)}: nessun avviso sul pianificatore vecchio"
            assert "come la colonna I" not in out, f"{os.path.basename(script)}: «come la colonna I» su un foglio a quota fissa"
    finally:
        shutil.rmtree(os.path.dirname(xlsx), ignore_errors=True)
    assert "prima della 0.10.0" in _testo_obiettivi("SKILL.md"), "SKILL.md: manca la nota sui pianificatori vecchi"
    assert "ATTERRAGGIO_AZ" in _testo_obiettivi("references/glide-path.md").split("## Il glide path nel versamento")[0] \
        and "colonna I" in _testo_obiettivi("references/glide-path.md").split("## Il glide path nel versamento")[0], \
        "glide-path.md: dire che atterraggio e curvatura diversi dal foglio fanno divergere dalla colonna I"


@test("montecarlo-obiettivi: il rendimento del profilo è la media aritmetica annua (volatilità → 0 ⇒ 50%)")
def t_convenzione_media():
    # F041: il modello normale centra la MEDIA del capitale sul versamento deterministico; con
    # volatilità quasi nulla la probabilità tende al 50%. Il mutante «media mensile = rend/12»
    # (media aritmetica annua > rend) la porta al 100%.
    import numpy as np
    mod = _modulo_obiettivi("montecarlo-obiettivi.py")
    mod.MODELLO = "normale"
    np.random.seed(3)
    target, rend, anni = 100_000.0, 0.05, 10
    pmt = mod.pmt_deterministico(target, 0.0, rend, anni)
    p, _ = mod.prob_successo(target, 0.0, pmt, rend, 0.001, anni)
    assert 0.45 <= p <= 0.55, f"volatilità 0,1%: probabilità {p:.1%}, attesa ~50%"
    # le etichette dicevano «geometrica»; serve la nota σ²/2 per tarare su rendimenti annualizzati
    assert "(geometrica)" not in open(asset("it-pianificazione-obiettivi", "montecarlo-obiettivi.py"),
                                      encoding="utf-8").read(), "etichetta «(geometrica)» nello script"
    mc = _testo_obiettivi("references/monte-carlo.md")
    assert "composizione geometrica" not in mc, "monte-carlo.md: «composizione geometrica»"
    for rel in ("references/monte-carlo.md", "references/mercati-e-correlazione.md"):
        assert "σ²/2" in _testo_obiettivi(rel), f"{rel}: manca la conversione σ²/2 tra media aritmetica e annualizzata"


@test("obiettivi: la ricetta DMS → profilo è svolta sui Parametri, confronti tra grandezze omogenee")
def t_ricetta_dms():
    # Revisione T8: la ricetta aggiungeva σ²/2 al lordo e poi tassava, mentre il Monte Carlo applica la
    # volatilità del profilo al rendimento NETTO (e il suo esempio 4,65% ↔ 5,5% era già netto); mancava
    # un esempio svolto fino a un default del foglio, che sta sopra la ricetta mondiale; monte-carlo.md
    # chiamava «prudenti» i profili confrontando il loro netto con la media storica lorda.
    import numpy as np
    foglio, profili, _ = _obiettivi_foglio()
    infl = foglio["B6"].value
    al = _modulo_obiettivi("asset-location-optimizer.py")
    costi, tassa = al.TER_DOSSIER + al.BOLLO, al.TASSA_PLUS_DOSSIER
    rend, vol, _ = profili["Azionario totale"]
    dms = 0.052  # azionario mondiale reale annualizzato 1900-2024 (DMS), citato nella reference
    profilo_dms = ((1 + dms) * (1 + infl) - 1 - costi) * (1 - tassa) + vol ** 2 / 2  # nominale → netto → +σ²/2
    reale_foglio = (1 + (rend - vol ** 2 / 2) / (1 - tassa) + costi) / (1 + infl) - 1  # il default, a ritroso
    mer = " ".join(_testo_obiettivi("references/mercati-e-correlazione.md").split())
    ricetta = mer.split("**Come tradurre un dato DMS")[1].split("**(b)")[0]
    assert ricetta.index("(1 − 26%)") < ricetta.index("aggiungere σ²/2"), \
        "ricetta DMS: σ²/2 si aggiunge al netto, dopo costi e imposte (il Monte Carlo applica σ al netto)"
    for cifra in (f"{_pct_it(profilo_dms * 100)}%", f"{_pct_it(rend * 100)}%", f"{_pct_it(reale_foglio * 100)}% reale"):
        assert cifra in ricetta, f"mercati-e-correlazione.md: manca {cifra} nell'esempio svolto DMS → Azionario totale"
    crescita, vol_c, peso_c = profili["Crescita"]
    m = re.search(r"(\d+,\d+)% netto annualizzato ↔ " + re.escape(_pct_it(crescita * 100)) + "% del foglio", ricetta)
    assert m and abs(float(m.group(1).replace(",", ".")) - (crescita - vol_c ** 2 / 2) * 100) <= 0.006, \
        "ricetta DMS: l'esempio σ²/2 della Crescita va sul netto annualizzato (rendimento − σ²/2)"
    motore = _modulo_obiettivi("motore_bootstrap.py")
    az, ob = motore.carica_storico("rendimenti-storici.csv")
    storico = float(np.mean(peso_c * az + (1 - peso_c) * ob)) * 100
    mc = " ".join(_testo_obiettivi("references/monte-carlo.md").split())
    for cifra in (f"~{_pct_it(storico)}% nominale lordo", f"{_pct_it(al.lordo_da_netto(crescita) * 100)}% lordo"):
        assert cifra in mc, f"monte-carlo.md (ricentratura): manca {cifra}, il confronto va fatto lordo con lordo"


@test("montecarlo-obiettivi (bootstrap): la coda congiunta di due essenziali supera il prodotto delle marginali")
def t_rischio_sistemico():
    # F022: simula_congiunta non era mai esercitata dai test. Con un mercato condiviso la
    # probabilità che falliscano insieme è più alta che sotto indipendenza.
    xlsx = _excel_test([("Casa", 60000, 8, "Moderato", 0, "essenziale", "terminante"),
                        ("Università", 80000, 12, "Crescita", 0, "essenziale", "terminante")])
    rc, out = run_script(asset("it-pianificazione-obiettivi", "montecarlo-obiettivi.py"), xlsx,
                         "--set", "MODELLO=bootstrap")
    shutil.rmtree(os.path.dirname(xlsx), ignore_errors=True)
    assert rc == 0, out[-400:]
    sez = out.split("RISCHIO SISTEMICO")[-1]
    assert "essenziali): Casa, Università" in sez, sez[:300]
    coda = re.search(r"falliscono.*?prodotto\):\s*([\d.]+)%.*?congiunta\):\s*([\d.]+)%", sez, re.S)
    insieme = re.search(r"riescono insieme.*?prodotto\):\s*([\d.]+)%.*?congiunta\):\s*([\d.]+)%", sez, re.S)
    ind, cong = float(coda.group(1)), float(coda.group(2))
    assert cong >= ind + 2, f"P(falliscono insieme): congiunta {cong}% vs prodotto {ind}%: shock non condivisi?"
    assert float(insieme.group(2)) >= float(insieme.group(1)), "P(riescono insieme) congiunta < prodotto"


@test("montecarlo-obiettivi: accanto all'OPZIONE la probabilità sul percorso glide, più bassa che a quota fissa")
def t_opzione_glide():
    # F017 (resto): la OPZIONE a quota fissa (58%) ignorava il de-risking che it-rebalance eseguirà
    # (sul glide path la stessa leva dà molto meno). Si mostrano entrambi i numeri, in entrambi i modelli.
    xlsx = _excel_test([("Barca", 400000, 20, "Moderato", 0, "desiderabile", "terminante")])
    try:
        for args in ((), ("--set", "GLIDE=False")):
            rc, out = run_script(asset("it-pianificazione-obiettivi", "montecarlo-obiettivi.py"), xlsx, *args)
            assert rc == 0, out[-400:]
            testo = _sezioni_obiettivi(out)["Barca"][2]
            assert "OPZIONE:" in testo, f"{args}: OPZIONE attesa per un desiderabile a 20 anni"
            glide = re.search(r"percorso glide[^\n]*dal (\d+)% al (\d+)%", testo)
            fissa = re.search(r"quota fissa[^\n]*dal (\d+)% al (\d+)%", testo)
            assert glide and fissa, f"{args}: mancano le probabilità glide e quota fissa accanto all'OPZIONE"
            assert int(glide.group(2)) < int(fissa.group(2)), "col de-risking la leva non può rendere di più"
            assert int(glide.group(2)) > int(glide.group(1)), "OPZIONE senza guadagno sul percorso glide"
    finally:
        shutil.rmtree(os.path.dirname(xlsx), ignore_errors=True)


@test("asset-location: l'ottimizzatore riceve un rendimento lordo esplicito, «netto» definito ovunque")
def t_rendimento_lordo():
    # F018: i rendimenti dei profili sono netti di costi e imposte; l'ottimizzatore toglie TER,
    # bollo e imposte da sé, quindi deve partire dal LORDO (prima: 5,5% netto trattato come lordo,
    # verdetto PIR ribaltato). Conversione dichiarata: lordo = netto / (1 − 26%) + TER + bollo.
    mod = _modulo_obiettivi("asset-location-optimizer.py")
    lordo = 0.055 / (1 - 0.26) + 0.002 + 0.002
    def dossier(r, gia, anni):  # replica: ETF ad accumulazione, plus 26% alla fine
        m = gia * (1 + r - 0.002 - 0.002) ** anni
        return m - max(0.0, m - gia) * 0.26
    def pareggio(r):
        lo, hi = 0.0, 0.10
        for _ in range(60):  # TER del PIR a cui PIR (plus esente, bollo) = dossier
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if 10_000 * (1 + r - mid - 0.002) ** 15 > dossier(r, 10_000, 15) else (lo, mid)
        return lo
    lo = pareggio(lordo)
    rc, out = run_script(asset("it-pianificazione-obiettivi", "asset-location-optimizer.py"))
    assert rc == 0, out[-400:]
    m = re.search(r"TER di pareggio del PIR: ([\d.]+)%", out)
    assert m and abs(float(m.group(1)) - lo * 100) <= 0.006, \
        f"TER di pareggio {m and m.group(1)}%, atteso {lo*100:.2f}% col lordo {lordo:.2%}"
    assert abs(mod.lordo_da_netto(0.055) - lordo) < 1e-12
    assert re.search(r"lordo[^\n]*7[.,]8%", out), "l'output deve dichiarare il rendimento lordo usato"
    # Revisione T8: la conversione tratta l'imposta come annua, quindi dà il lordo più alto compatibile
    # col netto e favorisce i contenitori esenti. Con l'imposta alla vendita (ETF ad accumulazione) il
    # lordo equivalente è più basso e il pareggio del PIR scende: verso e variante vanno detti.
    differito = ((1.055 ** 15 - 0.26) / 0.74) ** (1 / 15) - 1 + 0.004
    m = re.search(r"lordo equivalente a 15 anni è ([\d.]+)%.*?pareggio scende a ([\d.]+)%", out, re.S)
    assert m, "l'output deve dare la variante con l'imposta alla vendita (lordo equivalente e pareggio)"
    assert abs(float(m.group(1)) - differito * 100) <= 0.006, f"lordo con imposta differita {m.group(1)}%, atteso {differito:.2%}"
    assert abs(float(m.group(2)) - pareggio(differito) * 100) <= 0.006, \
        f"pareggio con imposta differita {m.group(2)}%, atteso {pareggio(differito):.2%}"
    assert "Prudente:" not in (mod.lordo_da_netto.__doc__ or ""), "lordo_da_netto: nell'ottimizzatore non è prudente"
    skill = _testo_obiettivi("SKILL.md")
    for cifra in (f"{_pct_it(pareggio(differito) * 100, 2)}%", "favorisce i contenitori esenti"):
        assert cifra in skill, f"SKILL.md (asset location): manca «{cifra}»"
    rc, out = run_script(asset("it-pianificazione-obiettivi", "asset-location-optimizer.py"),
                         "--set", "RENDIMENTO_LORDO=0.07")
    assert rc == 0 and "@ 7.0%" in out, "RENDIMENTO_LORDO esplicito non usato nello scenario pensione"
    par, _, _ = _obiettivi_foglio()
    note = " ".join(str(par[f"A{r}"].value or "") for r in range(1, 30))
    formula = "(lordo − costi) × (1 − 26%)"
    assert "netti di costi e imposte" in str(par["A8"].value), f"Parametri!A8: {par['A8'].value!r}"
    for dove, testo in (("Parametri", note), ("SKILL.md", _testo_obiettivi("SKILL.md")),
                        ("matematica-accumulo.md", _testo_obiettivi("references/matematica-accumulo.md"))):
        assert formula in testo, f"{dove}: manca la definizione di «netto» ({formula})"


@test("obiettivi: le cifre citate in SKILL.md e nelle reference sono l'output sui default")
def t_cifre_documentate():
    # F043: gli esempi usavano 3,5%/5% (€487/€366/€1.353) contro il 4,0%/5,5% dell'Excel, e le
    # cifre dell'asset location venivano da un «test sui dati reali» non riproducibile.
    from openpyxl import load_workbook
    skill = _testo_obiettivi("SKILL.md")
    mat = _testo_obiettivi("references/matematica-accumulo.md")
    mc = _testo_obiettivi("references/monte-carlo.md")
    dec = _testo_obiettivi("references/decumulo.md")
    mer = _testo_obiettivi("references/mercati-e-correlazione.md")
    # piano di accumulo: i versamenti del foglio d'esempio
    foglio, profili, obiettivi = _obiettivi_foglio()
    totale = sum(g["versamento"] for g in obiettivi)
    for v in [g["versamento"] for g in obiettivi] + [totale]:
        assert _euro_it(v) in mat, f"matematica-accumulo.md non cita {_euro_it(v)} del foglio d'esempio"
    for vecchio in ("€487", "€366", "€1.353"):
        assert vecchio not in mat, f"matematica-accumulo.md: {vecchio} non è l'output dei Parametri"
    glide = {g["nome"]: _euro_it(g["versamento"]) for g in obiettivi}
    for rel, testo, nomi in (("references/glide-path.md", _testo_obiettivi("references/glide-path.md"),
                              ("Anticipo casa", "Lungo termine / libertà")),
                             ("SKILL.md", skill, ("Lungo termine / libertà",))):
        for nome in nomi:
            assert glide[nome] in testo, f"{rel} non cita il versamento col glide path di {nome} ({glide[nome]})"
    tmp = tempfile.mkdtemp()
    try:
        rc, out = run_script(asset("it-pianificazione-obiettivi", "allocatore-capitale.py"),
                             "--json", os.path.join(tmp, "a.json"))
        assert rc == 0, out[-400:]
        righe = {r["nome"]: r for r in json.load(open(os.path.join(tmp, "a.json")))["obiettivi"]}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    richiesto = _euro_it(righe["Lungo termine / libertà"]["richiesto"])
    assert richiesto in _testo_obiettivi("references/allocazione-capitale.md"), \
        f"allocazione-capitale.md non cita il capitale richiesto col glide path ({richiesto})"
    # Revisione T8: anche le cifre a quota fissa e quelle che dipendono dai default o dalla serie
    # (aggiornata ogni gennaio) devono essere l'output, non numeri scritti a mano.
    infl = foglio["B6"].value
    per_nome = {g["nome"]: g for g in obiettivi}
    gp = _testo_obiettivi("references/glide-path.md")
    alloc = _testo_obiettivi("references/allocazione-capitale.md")
    fissi = {}
    for nome in ("Anticipo casa", "Lungo termine / libertà"):
        g = per_nome[nome]
        rend = profili[g["profilo"]][0]
        target_nom = g["target"] * (1 + infl) ** g["anni"]
        fissi[nome], _ = _pmt_anno_per_anno(target_nom, g["gia"] or 0, rend, rend, g["anni"], 7)
        for rel, testo in (("references/glide-path.md", gp), ("references/matematica-accumulo.md", mat)):
            assert _euro_it(fissi[nome]) in testo, \
                f"{rel}: manca il versamento a quota fissa di {nome} ({_euro_it(fissi[nome])})"
    g = per_nome["Lungo termine / libertà"]
    rend, fisso = profili[g["profilo"]][0], fissi["Lungo termine / libertà"]
    target_nom = g["target"] * (1 + infl) ** g["anni"]
    assert _euro_it(fisso) in skill, f"SKILL.md: manca il versamento a quota fissa a 20 anni ({_euro_it(fisso)})"
    aumento = f"(+{round((g['versamento'] / fisso - 1) * 100)}%)"
    assert aumento in gp, f"glide-path.md: il glide path alza il versamento a 20 anni di {aumento}"
    rend_l = min(profili.values(), key=lambda p: p[2])[0]
    cap = 0.0  # capitale finale col versamento a quota fissa, seguendo il glide path
    for r in rend_l + (rend - rend_l) * _modulo_obiettivi("motore_bootstrap.py").frazioni_glide(g["anni"], 7):
        cap = cap * (1 + r) + fisso * r / ((1 + r) ** (1 / 12) - 1)
    quota = f"circa il {round(cap / target_nom * 100)}% del target"
    assert quota in gp, f"glide-path.md: a quota fissa il capitale si ferma a «{quota}»"
    pv_fisso = g["target"] * ((1 + infl) / (1 + rend)) ** g["anni"]
    for rel, testo in (("references/allocazione-capitale.md", alloc), ("SKILL.md", skill)):
        for cifra in (_euro_it(pv_fisso), richiesto):
            assert cifra in testo, f"{rel}: manca {cifra} (present value a rendimento pieno e col glide path)"
    aumento = f"(+{round((righe[g['nome']]['richiesto'] / pv_fisso - 1) * 100)}%)"
    assert aumento in alloc, f"allocazione-capitale.md: il glide path alza il capitale richiesto di {aumento}"
    # tabella dei profili di monte-carlo.md = Parametri (sei profili)
    righe = re.findall(r"^\| ([A-Z][a-z ]+) \| ([\d,]+)% \| ([\d,]+)% \|", mc, re.M)
    doc = {n: (float(r.replace(",", ".")) / 100, float(v.replace(",", ".")) / 100) for n, r, v in righe}
    assert set(doc) == set(profili), f"monte-carlo.md elenca {sorted(doc)}, il foglio {sorted(profili)}"
    for n, (r, v, _) in profili.items():
        assert abs(doc[n][0] - r) < 1e-9 and abs(doc[n][1] - v) < 1e-9, f"monte-carlo.md, {n}: {doc[n]} ≠ {(r, v)}"
    # Monte Carlo sui default
    rc, out = run_script(asset("it-pianificazione-obiettivi", "montecarlo-obiettivi.py"))
    assert rc == 0, out[-400:]
    sez = _sezioni_obiettivi(out)
    casa = sez["Anticipo casa"][2]
    pmt = re.search(r"Versamento deterministico:\s*(€[\d.]+)/mese", casa).group(1)
    p = re.search(r"questo versamento: (\d+)%", casa).group(1)
    pmt85 = re.search(r"confidenza:\s*(€[\d.]+)/mese", casa).group(1)
    frase = f"con {pmt}/mese hai il {p}% di arrivarci; per l'85% te ne servono {pmt85}"
    assert frase in mc, f"monte-carlo.md deve citare l'output sui default: «{frase}»"
    prob = _prob_obiettivi(out)
    assert f"solo il ~{prob['Lungo termine / libertà']}% di probabilità" in mc, "monte-carlo.md: probabilità a 20 anni"
    assert f"vicino al {prob['Fondo di emergenza']}%" in mc, "monte-carlo.md: probabilità del fondo di emergenza"
    # asset location sui default
    rc, out = run_script(asset("it-pianificazione-obiettivi", "asset-location-optimizer.py"))
    assert rc == 0, out[-400:]
    vant = re.search(r"VANTAGGIO FONDO PENSIONE: (€[\d.]+)\s+\(\+(\d+)% vs dossier\)", out)
    pir = re.search(r"(VANTAGGIO|SVANTAGGIO) PIR: (-?€[\d.]+)", out)
    par = re.search(r"TER di pareggio del PIR: ([\d.]+)%", out)
    for cifra in (vant.group(1), f"+{vant.group(2)}% vs dossier", pir.group(2).replace("-", "−"),
                  par.group(1).replace(".", ",") + "%"):
        assert cifra in skill, f"SKILL.md non cita {cifra} dell'ottimizzatore sui default"
    al = _modulo_obiettivi("asset-location-optimizer.py")
    deduzione = _euro_it(al.CONTRIBUTO_ANNUO_FP * al.ALIQUOTA_IRPEF_MARGINALE * al.ANNI_A_PENSIONE)
    reinvestita = re.search(r"Driver: la deduzione IRPEF \((€[\d.]+)\)", out).group(1)
    for cifra in (deduzione, reinvestita):
        assert cifra in skill, f"SKILL.md non cita {cifra} (risparmio IRPEF e suo reinvestimento)"
    # decumulo sui default
    rc, out = run_script(asset("it-pianificazione-obiettivi", "decumulo-obiettivi.py"))
    assert rc == 0, out[-400:]
    sens = dict(re.findall(r"^\s+€\s*[\d,]+\s+([\d.]+)%\s+([\d.]+)%$", out, re.M))
    for tasso in ("3.0", "4.0", "5.0", "6.0"):
        assert f"{_pct_it(float(sens[tasso]))}% al {tasso[0]}%" in dec, \
            f"decumulo.md: manca «{_pct_it(float(sens[tasso]))}% al {tasso[0]}%» (output sui default)"
    anno = re.search(r"peggiori rendimenti PRIMA:\s+ESAURITO all'anno (\d+)", out).group(1)
    assert f"all'anno {anno}" in dec, f"decumulo.md: la sequenza peggiore esaurisce all'anno {anno}"
    iniziale = float(re.search(r"capitale €([\d,]+)", out).group(1).replace(",", ""))
    finale = float(re.search(r"migliori rendimenti PRIMA:\s+capitale finale €([\d,]+)", out).group(1).replace(",", ""))
    assert 1.75 <= finale / iniziale <= 2.25 and "circa il doppio" in dec, \
        f"decumulo.md: «circa il doppio» con i migliori prima, l'output dà {finale / iniziale:.2f} volte"
    # rendimento reale storico dell'azionario USA (dalla serie, deflazionata con la CPI)
    motore = _modulo_obiettivi("motore_bootstrap.py")
    az, _ = motore.carica_storico("rendimenti-storici.csv")
    cpi = motore.carica_inflazione("rendimenti-storici.csv")
    import numpy as np
    reale = (np.prod((1 + az) / (1 + cpi)) ** (1 / len(az)) - 1) * 100
    for rel, testo in (("mercati-e-correlazione.md", mer), ("monte-carlo.md", mc)):
        assert f"~{_pct_it(reale)}%" in testo, f"{rel}: l'azionario USA ha reso ~{_pct_it(reale)}% reale annuo"
    costante = (np.prod((1 + az) / 1.02) ** (1 / len(az)) - 1) * 100
    frase = f"inflazione costante del 2% l'azionario USA renderebbe ~{_pct_it(costante)}% reale invece di ~{_pct_it(reale)}%"
    assert frase in mer, f"mercati-e-correlazione.md: «{frase}»"
    i = 1974 - 1928
    meno = lambda x: x.replace("-", "−")
    frase = (f"1974: {meno(_pct_it(az[i] * 100))}% nominale con inflazione al {_pct_it(cpi[i] * 100)}%, "
             f"{meno(str(round(((1 + az[i]) / (1 + cpi[i]) - 1) * 100)))}% reale")
    assert frase in mer, f"mercati-e-correlazione.md: «{frase}» (dalla serie)"
    # numero di formule del pianificatore
    wb = load_workbook(asset("it-pianificazione-obiettivi", "pianificatore-obiettivi.xlsx"))
    n = sum(1 for ws in wb.worksheets for riga in ws.iter_rows() for c in riga
            if isinstance(c.value, str) and c.value.startswith("="))
    citati = re.findall(r"(\d+) formule", skill)
    assert citati and all(int(c) == n for c in citati), f"SKILL.md cita {citati} formule, il foglio ne ha {n}"


@test("obiettivi: nessun rimando superato nelle reference (decumulo, correlazione, glide path, --json)")
def t_rimandi_superati():
    # F043: rimandi a «roadmap» per cose già fatte e limiti non più veri.
    # Revisione T8: l'allocatore non usa pmt_glide ma crescita_glide; il flag Tipo cambia anche la
    # vista per obiettivo; la finestra si legge da Parametri!B7; i profili non vanno confrontati
    # (netti) con la media storica (lorda) come «ipotesi prudenti»; SKILL.md descriveva l'allocatore
    # a rendimento pieno.
    vietati = {
        "references/monte-carlo.md": ("roadmap di `it-rebalance`", "roadmap di it-rebalance",
                                      "Nessuna correlazione tra obiettivi", "o glide path**",
                                      "7 anni come in `glidepath-obiettivi.py`", "ipotesi prudenti dei profili"),
        "references/glide-path.md": ("roadmap di it-rebalance", "sovrastima leggermente",
                                     "e l'allocatore (per il capitale richiesto oggi)",
                                     "La vista **per obiettivo** non dipende dal flag"),
        "references/matematica-accumulo.md": ("glide path e allocatore usano la stessa",),
        "SKILL.md": ("correlazione sistemica tra obiettivi nel Monte Carlo", "alimenta il tracker e il glide path",
                     "il capitale che al rendimento del profilo cresce fino al target",
                     "finestra di de-risking di 7 anni"),
        "assets/montecarlo-obiettivi.py": ("Parametri!A10:C14",),
    }
    for rel, frasi in vietati.items():
        testo = _testo_obiettivi(rel)
        for frase in frasi:
            assert frase not in testo, f"{rel}: «{frase}»"
    gp = _testo_obiettivi("references/glide-path.md")
    assert re.search(r"circa (il )?10%", gp), "glide-path.md: l'ordine di grandezza del de-risking ignorato (~10%)"
    # Step 4 di SKILL.md: lo pseudocodice era solo a quota fissa (chi lo segue in chat sottostima il
    # versamento dei terminanti); il report deve dichiarare le convenzioni.
    skill = _testo_obiettivi("SKILL.md")
    passo4 = skill.split("### Step 4")[1].split("### Step 5")[0]
    for formula in (r"m\s*=\s*min\(finestra, n\) − 1", r"r2\s*=\s*\(r \+ r_atterraggio\) / 2",
                    r"Quota fissa[^\n]*permanenti"):
        assert re.search(formula, passo4), f"SKILL.md, Step 4: manca «{formula}» (versamento in due fasi)"
    sezione3 = skill.split("### 3. Piano di accumulo")[1].split("### 4.")[0]
    assert "glide path" in sezione3 and "netto" in sezione3, "SKILL.md, report: dichiarare le convenzioni"


@test("serie storica: nominale in USD dichiarata, il decumulo deflaziona anno per anno con la CPI USA")
def t_serie_storica():
    # Critica dell'audit: la serie è nominale in dollari ma il motore la chiamava «reale», e il
    # decumulo la deflazionava con un 2% costante (cancellando la stagflazione degli anni '70).
    csv_path = asset("it-pianificazione-obiettivi", "rendimenti-storici.csv")
    righe = open(csv_path, encoding="utf-8").read().splitlines()
    commenti = " ".join(r for r in righe if r.startswith("#")).lower()
    assert "nominali" in commenti and "dollari" in commenti, "intestazione: dichiarare rendimenti nominali in dollari"
    assert "anno,azionario,obbligazionario,inflazione" in righe, "manca la colonna inflazione"
    dati = {int(r.split(",")[0]): [float(x) for x in r.split(",")[1:]] for r in righe
            if r and r[0].isdigit()}
    assert sorted(dati) == list(range(1928, 2026)) and all(len(v) == 3 for v in dati.values())
    # CPI-U dicembre su dicembre pubblicata dal BLS (tabella storica; release CPI dicembre 2025)
    for anno, bls in ((1946, 18.1), (1974, 12.3), (1979, 13.3), (1980, 12.5), (2008, 0.1), (2022, 6.5), (2025, 2.7)):
        assert abs(dati[anno][2] - bls) <= 0.05 + 1e-9, f"inflazione {anno}: {dati[anno][2]} vs BLS {bls}"
    motore = open(asset("it-pianificazione-obiettivi", "motore_bootstrap.py"), encoding="utf-8").read()
    assert "serie annuali reali" not in motore, "motore_bootstrap: la serie non è reale"
    mod = _modulo_obiettivi("decumulo-obiettivi.py")
    mod.PESO_AZIONARIO, mod.INFLAZIONE = 1.0, None
    reali = mod.carica_rendimenti_reali(0.0)
    atteso = (1 + dati[1974][0] / 100) / (1 + dati[1974][2] / 100) - 1
    assert abs(reali[1974 - 1928] - atteso) < 1e-12, f"1974 reale {reali[1974 - 1928]:.4f}, atteso {atteso:.4f}"
    mod.INFLAZIONE = 0.02  # override esplicito: inflazione costante come prima
    assert abs(mod.carica_rendimenti_reali(0.0)[1974 - 1928] - ((1 + dati[1974][0] / 100) / 1.02 - 1)) < 1e-12


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


@test("genera-ips: quota azionaria sommata su tutte le classi, mese in italiano in copertina")
def t_ips_quota():
    # REGRESSIONE F060: contava solo la prima classe che inizia per "azion" e scriveva il mese in inglese.
    from docx import Document
    mod = carica_modulo(asset("it-revisione", "genera-ips.py"))
    mesi = ("gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
            "agosto", "settembre", "ottobre", "novembre", "dicembre")
    tmp = tempfile.mkdtemp()
    try:
        for allocazione, attesa in (
                ([("Azionario sviluppati", 45_000, 45.0), ("Azionario emergenti", 11_700, 11.7),
                  ("Obbligazionario", 31_300, 31.3), ("Liquidità", 12_000, 12.0)], 57),
                ([("ETF azionario globale", 60_000, 60.0), ("Obbligazioni", 40_000, 40.0)], 60)):
            out = os.path.join(tmp, "ips.docx")
            mod.genera({"allocazione": allocazione, "capitale": 100_000,
                        "obiettivi": [o[:4] + (100_000 * o[4] / mod.DATI["capitale"],) + o[5:]
                                      for o in mod.DATI["obiettivi"]]}, out)
            testo = "\n".join(p.text for p in Document(out).paragraphs)
            m = re.search(r"allocazione al (\d+)% azionario", testo)
            assert m and int(m.group(1)) == attesa, f"quota azionaria {m.group(1) if m else '—'}%, attesa {attesa}%"
        assert any(f"{mese.capitalize()} " in testo for mese in mesi), "mese della copertina non in italiano"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ══════════════════════ it-tax-optimization (T1-T3) ══════════════════════

TAX = os.path.join(SKILLS, "it-tax-optimization")


def _testi_regole():
    """{percorso relativo: testo} di skill, comandi, README (senza il changelog storico) e
    descrizione del plugin.json, con il grassetto Markdown tolto. Il changelog del README
    racconta le versioni passate: gli errata li aggiunge chi rilascia, non questi controlli."""
    testi = {}
    for base in (SKILLS, os.path.join(ROOT, "commands")):
        for cartella, _, files in os.walk(base):
            for f in files:
                if f.endswith((".md", ".py")):
                    p = os.path.join(cartella, f)
                    testi[os.path.relpath(p, ROOT)] = open(p, encoding="utf-8").read()
    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    testi["README.md"] = re.sub(r"\n### Changelog\n.*?(?=\n## )", "\n", readme, flags=re.S)
    plugin = json.load(open(os.path.join(ROOT, ".claude-plugin", "plugin.json"), encoding="utf-8"))
    testi[".claude-plugin/plugin.json"] = plugin["description"]
    return {k: v.replace("*", "") for k, v in testi.items()}


def _frasi(testo):
    """Spezza in frasi (punto/punto e virgola seguiti da maiuscola), righe e celle di tabella.
    Le abbreviazioni come «art. 67» o «c. 1-bis» restano unite perché segue una cifra."""
    return [f for f in re.split(r"(?<=[.!?;])\s+(?=[A-ZÀ-Ý«(`\[])|\n|\|", testo) if f.strip()]


_LIFO = re.compile(r"\bL\.?I\.?F\.?O\b\.?", re.I)
_REGIME = re.compile(r"amministrat|dichiarativ", re.I)
_CONFINE = re.compile(r"[,;:]|\bmentre\b|\binvece\b", re.I)
# LIFO legato subito al dichiarativo: «LIFO in dichiarativo», «LIFO (dichiarativo)», «LIFO solo in
# dichiarativo», «il LIFO vale solo in dichiarativo»; oppure «in dichiarativo è il LIFO».
_LIFO_DICH_DOPO = re.compile(r"\s*\)?\s*\(?\s*(?:vale\s+)?(?:solo\s+)?(?:in|nel|per\s+il)?\s*(?:regime\s+)?dichiarativ", re.I)
_LIFO_DICH_PRIMA = re.compile(r"dichiarativ\w*[^.;:,()]{0,25}$", re.I)
_ELENCO_USA = re.compile(r"HIFO\s*/\s*L\.?I\.?F\.?O|L\.?I\.?F\.?O\.?\s*/\s*Spec", re.I)


def _lifo_errato(frase):
    """True se la frase riferisce il LIFO all'amministrato, o lo nomina senza alcun regime fuori
    dall'elenco dei metodi USA (HIFO/LIFO/SpecID). Ogni occorrenza (anche «Lifo», «L.I.F.O.») si
    lega al regime della propria clausola (confini: , ; : «mentre» «invece»); se la clausola non
    ne nomina, al regime nominato più vicino prima di lei nella frase, o al primo dopo."""
    for m in _LIFO.finditer(frase):
        if _LIFO_DICH_DOPO.match(frase, m.end()) or _LIFO_DICH_PRIMA.search(frase, 0, m.start()):
            continue
        inizio = max([0] + [c.end() for c in _CONFINE.finditer(frase, 0, m.start())])
        dopo = _CONFINE.search(frase, m.end())
        clausola = frase[inizio:dopo.start() if dopo else len(frase)]
        if re.search(r"amministrat", clausola, re.I):
            return True
        if re.search(r"dichiarativ", clausola, re.I):
            continue
        prima = list(_REGIME.finditer(frase, 0, m.start()))
        regime = prima[-1] if prima else _REGIME.search(frase, m.end())
        if regime is None:
            if not _ELENCO_USA.search(frase[max(0, m.start() - 8):m.end() + 8]):
                return True
        elif regime.group(0).lower().startswith("amministrat"):
            return True
    return False


@test("T1: nessun LIFO riferito al regime amministrato (costo medio ponderato, art. 6 c. 4 D.Lgs. 461/97)")
def t_t1_lifo_amministrato():
    # REGRESSIONE F012: in amministrato la base è il costo medio ponderato; il LIFO
    # (art. 67 c. 1-bis TUIR) individua i titoli ceduti solo in dichiarativo. Ogni LIFO deve
    # quindi essere legato al dichiarativo (o all'elenco dei metodi USA), non all'amministrato.
    for frase in ("- ❌ Assumere HIFO o Specific ID per la scelta del lotto: in amministrato è sempre LIFO.",
                  "In regime amministrato la plus si calcola con il LIFO, mentre in dichiarativo si usa il costo medio ponderato.",
                  "- ❌ Ignorare il LIFO: la scelta del lotto NON è libera come negli USA, e influenza la plus realizzata.",
                  "LIFO obbligatorio in regime amministrato",
                  "In regime amministrato il metodo di valorizzazione è Lifo per default.",
                  "In amministrato i lotti si scaricano con il L.I.F.O."):
        assert _lifo_errato(frase), f"il controllo non riconosce: «{frase}»"
    for frase in ("Costo medio ponderato in amministrato, LIFO in dichiarativo: il lotto non si sceglie",
                  "costo medio ponderato (LIFO solo in dichiarativo)",
                  "la base è il costo medio ponderato (il LIFO vale solo in dichiarativo).",
                  "Cambiano il metodo del costo, che in dichiarativo è il LIFO e non il costo medio ponderato dell'amministrato",
                  "Scelta investitore (HIFO/LIFO/SpecID)"):
        assert not _lifo_errato(frase), f"falso positivo: «{frase}»"
    errori = []
    for rel, testo in _testi_regole().items():
        for frase in _frasi(testo):
            if _lifo_errato(frase):
                errori.append(f"{rel}: «{frase.strip()[:110]}»")
    assert not errori, "LIFO riferito all'amministrato o senza regime:\n  " + "\n  ".join(errori[:12])
    skill = open(os.path.join(TAX, "SKILL.md"), encoding="utf-8").read()
    assert re.search(r"costo medio ponderato[^\n]*art\. 6 c\. 4", skill), "SKILL.md: manca la regola del costo medio (art. 6 c. 4)"
    dich = open(os.path.join(TAX, "references", "regime-dichiarativo.md"), encoding="utf-8").read()
    assert re.search(r"LIFO[^\n]*art\. 67 c\. 1-bis", dich), "regime-dichiarativo.md: manca il LIFO con l'art. 67 c. 1-bis"
    assert "identiche all'amministrato" not in dich, "regime-dichiarativo.md: regole «identiche» all'amministrato, ma il metodo del costo cambia"
    # Cripto in dichiarativo: la legge non richiama la lettera c-sexies, ma la Circ. 30/E/2023
    # (par. 3.2.1) prescrive il LIFO: non è una prassi «per analogia» da concordare.
    metodo = open(os.path.join(TAX, "references", "criptovalute.md"), encoding="utf-8").read().split("Metodo di valorizzazione")[1].split("\n")[0]
    assert re.search(r"LIFO[^\n]*Circ\. 30/E/2023, par\. 3\.2\.1", metodo), "criptovalute.md: manca il LIFO della Circ. 30/E/2023 par. 3.2.1"
    assert "analogia" not in metodo and "da concordare" not in metodo, "criptovalute.md: il LIFO cripto presentato come scelta da concordare"


_NA = r"(?:non[ -]armonizzat|non[ -]UCITS|US-listed)"
_NA_COMPENSABILE = (
    re.compile(_NA + r"[^→\n|]*→\s*`?reddito[ _]divers", re.I),          # «ETF non armonizzato → `reddito_diverso`»
    re.compile(r"reddit[oi][ _]divers[oi]`?\s*\([^)\n]*" + _NA, re.I),  # «`reddito_diverso` (azioni, ETF non armonizzati)»
    re.compile(_NA + r"[^\n]{0,40}?(?<!non )(?<!mai )compensabil", re.I),  # «ETF non armonizzati (compensabili)»
    re.compile(_NA + r"[^\n→]*→\s*SÌ"),                                   # «plus su ... ETF non armonizzati → SÌ, consumato»
)


@test("T1: nessun ETF o fondo non armonizzato tra gli strumenti compensabili con lo zainetto")
def t_t1_non_armonizzati():
    # REGRESSIONE F003: la plus di un OICR non armonizzato è reddito di capitale (art. 44
    # c. 1 lett. g TUIR; art. 10-ter L. 77/1983), mai compensabile; solo la minus è reddito diverso.
    # Su tutti i testi, riga per riga (gli anti-pattern «❌» descrivono l'errore e si saltano).
    errori = []
    for rel, testo in _testi_regole().items():
        for riga in testo.splitlines():
            if "❌" not in riga and any(p.search(riga) for p in _NA_COMPENSABILE):
                errori.append(f"{rel}: «{riga.strip()[:110]}»")
    assert not errori, "non armonizzati tra i compensabili:\n  " + "\n  ".join(errori[:12])
    joint = open(os.path.join(SKILLS, "it-pianificazione", "references", "integrazione-fiscale-joint.md"),
                 encoding="utf-8").read()
    mappa = joint.split("```")[1].splitlines()
    col = next(r for r in mappa if "Imposta sostitutiva" in r).index("Imposta sostitutiva")
    for r in mappa:
        assert not re.search(_NA, r[col:], re.I), f"integrazione-fiscale-joint: non armonizzati nella colonna della sostitutiva: {r.strip()}"
    assert re.search(r"regime dichiarativo[^\n]*non armonizzat[^\n]*quadro RL|regime dichiarativo[^\n]*quadro RL[^\n]*non armonizzat", joint.replace("*", "")), \
        "integrazione-fiscale-joint: in dichiarativo manca l'eccezione IRPEF dei non armonizzati"
    etf = open(os.path.join(TAX, "references", "etf-trap-redditi-capitale.md"), encoding="utf-8").read()
    amici = etf.split('## Strumenti "amici"')[1].split('## Strumenti "nemici"')[0]
    assert "armonizzat" not in amici, "etf-trap: un OICR non armonizzato nella tabella «amici»"
    assert re.search(r'## Strumenti "nemici".*non armonizzat', etf, re.S), "etf-trap: non armonizzati assenti dai «nemici»"
    skill = open(os.path.join(TAX, "SKILL.md"), encoding="utf-8").read()
    riga = next(r for r in skill.splitlines() if r.startswith("| **Reddito diverso** (art. 67"))
    assert "armonizzat" not in riga, f"SKILL.md: riga reddito diverso: {riga[:120]}"
    assert "reddito_capitale_irpef" in skill, "SKILL.md: manca la categoria reddito_capitale_irpef per gli OICR extra UE/SEE"
    assert re.search(r"non armonizzat[^\n]*→\s*`reddito_capitale`[^\n]*`reddito_capitale_irpef`", skill), \
        "SKILL.md: la deduzione della categoria non manda i non armonizzati a reddito_capitale/_irpef"
    reb = open(os.path.join(SKILLS, "it-rebalance", "SKILL.md"), encoding="utf-8").read()
    assert re.search(r"`tipo_fiscale`[^\n]*`reddito_capitale`\s*\([^)\n]*non armonizzat", reb), \
        "it-rebalance: la riga tipo_fiscale non mette i non armonizzati sotto reddito_capitale"
    trovate = 0
    for r in reb.splitlines():
        if "reddito diverso" in r and "**può**" in r:
            trovate += 1
            assert "armonizzat" not in r, f"it-rebalance: {r[:120]}"
    assert trovate >= 1, "it-rebalance: manca la riga su cosa il reddito diverso può compensare"
    mb = open(os.path.join(SKILLS, "it-rebalance", "references", "ribilanciamento-multibroker.md"), encoding="utf-8").read()
    m = re.search(r"compensa solo i \*\*redditi diversi\*\* \(([^)]*)\)", mb)
    assert m and "armonizzat" not in m.group(1), "ribilanciamento-multibroker.md: elenco dei redditi diversi"


@test("T1: alla chiusura del rapporto le minus si certificano (art. 6 c. 5 D.Lgs. 461/97), non «si perdono»")
def t_t1_chiusura_rapporto():
    # REGRESSIONE F011: chiudendo il rapporto (o revocando l'opzione) l'intermediario certifica
    # le minus residue, utilizzabili su un altro rapporto con gli stessi intestatari o in
    # dichiarazione entro la scadenza originaria. Il grassetto è tolto prima del confronto.
    for rel, testo in _testi_regole().items():
        assert not re.search(r"si\s+perde\s+definitivamente", testo), f"{rel}: «si perde definitivamente»"
        assert "unico modo per consolidare" not in testo, f"{rel}: il dichiarativo presentato come unica via"
    for rel in ("references/multi-intermediario.md", "SKILL.md"):
        testo = open(os.path.join(TAX, rel), encoding="utf-8").read()
        assert "certificazione" in testo and "art. 6 c. 5" in testo, f"{rel}: manca la certificazione ex art. 6 c. 5"
    skill = open(os.path.join(TAX, "SKILL.md"), encoding="utf-8").read()
    assert "Pattern E" in skill, "SKILL.md: manca il Pattern E (consolidamento via certificazione)"
    multi = open(os.path.join(TAX, "references", "multi-intermediario.md"), encoding="utf-8").read()
    pratico = multi.split("## Caso pratico")[1].split("\n---\n")[0]   # senza il marcatore in fondo
    assert "Verificato" not in pratico, "caso pratico: il taglio include il marcatore"
    for lettera, chiave in (("a", "consumo in loco"), ("b", "certificazione"), ("c", "dichiarativo")):
        assert re.search(rf"^\*\*Scenario \({lettera}\)[^\n]*{chiave}", pratico, re.M), \
            f"caso pratico: manca l'intestazione dello scenario ({lettera}) «{chiave}»"
        assert re.search(rf"^\| \({lettera}\) ", pratico, re.M), f"caso pratico: manca la riga ({lettera}) della tabella riassuntiva"
    # I totali seguono le regole dei Pattern A, D ed E applicate alla tabella dei rapporti: il
    # dichiarativo vale dall'anno dopo e non salva le minus che scadono il 31/12/N.
    rapporti = re.findall(r"^\| (\w[\w ]*?) \| ([\d.]+) \| (31/12/N(?:\+\d)?|—) \| ([\d.]+) \|$", pratico, re.M)
    assert len(rapporti) == 3, f"caso pratico: tabella dei rapporti illeggibile ({rapporti})"
    num = lambda s: int(s.replace(".", ""))
    in_loco = sum(min(num(z), num(p)) for _, z, _, p in rapporti)
    residuo = {b: num(z) - min(num(z), num(p)) for b, z, _, p in rapporti}
    capienza = sum(num(p) - min(num(z), num(p)) for _, z, _, p in rapporti)
    scade_ora = [b for b, _, s, _ in rapporti if s == "31/12/N" and residuo[b] > 0]
    assert scade_ora, "caso pratico: nessun rapporto con minus in scadenza il 31/12/N"
    eur = lambda x: "€" + f"{round(x * 0.26):,}".replace(",", ".")
    certificate = min(sum(residuo[b] for b in scade_ora), capienza)
    tutte = min(sum(residuo.values()), capienza)
    dichiarativo = min(sum(r for b, r in residuo.items() if b not in scade_ora), capienza)
    for lettera, attesi in (("a", [in_loco]), ("b", [in_loco + certificate, in_loco + tutte]),
                            ("c", [in_loco + dichiarativo])):
        riga = re.search(rf"^\| \({lettera}\) [^\n]*", pratico, re.M).group(0)
        for x in attesi:
            assert eur(x) in riga, f"caso pratico, riga ({lettera}): atteso {eur(x)} — {riga}"
    # Pattern D senza le minus in scadenza nell'anno; Pattern E con la capienza della destinazione
    # divisa tra le origini (le stesse plus non si contano due volte).
    pattern_d = skill.split("**Pattern D")[1].split("**Pattern E")[0]
    assert re.search(r"anno_scadenza\s*>\s*anno_corrente", pattern_d), "Pattern D: lo zainetto consolidato conta anche le minus che scadono nell'anno"
    assert "Pattern E" in pattern_d.split("```")[1], "Pattern D: la proposta non passa dal confronto con il Pattern E"
    pattern_e = skill.split("**Pattern E")[1].split("### Step 4")[0]
    assert re.search(r"capienza\s*[−-]=\s*recuperabile", pattern_e), "Pattern E: la capienza della destinazione non si riduce tra un'origine e l'altra"


@test("T1: scarto di emissione e coefficiente 48,08% con fonte corretta, marcatori delle reference")
def t_t1_scarto_marcatori():
    # REGRESSIONE F052/F035/F042: BOT e zero coupon tenuti a scadenza non consumano zainetto;
    # il 48,08% viene dall'art. 3 c. 5 DL 66/2014, non dall'art. 68 c. 6 TUIR.
    aliq = open(os.path.join(TAX, "references", "aliquote-12-5-26.md"), encoding="utf-8").read()
    assert "art. 68 c. 6 TUIR, art. 7 DLgs 461/97" not in aliq, "aliquote: fonte del coefficiente superata"
    assert "art. 3 c. 5 DL 66/2014" in aliq, "aliquote: manca la fonte del 48,08%"
    assert re.search(r"### Esempio D[^\n]*(BOT|zero coupon)", aliq), "aliquote: manca l'esempio BOT/zero coupon"
    assert "prezzo di emissione" in aliq and "scarto di emissione" in aliq, "aliquote: esempio senza prezzo di emissione"
    for rel in ("it-tax-optimization/references/etf-trap-redditi-capitale.md",
                "it-tax-optimization/references/multi-intermediario.md",
                "it-tax-optimization/references/aliquote-12-5-26.md",
                "it-pianificazione-obiettivi/references/asset-location.md"):
        testo = open(os.path.join(SKILLS, rel), encoding="utf-8").read()
        assert "Verificato: 2026-10" in testo, f"{rel}: manca il marcatore della verifica di ottobre 2026"
    al = open(os.path.join(SKILLS, "it-pianificazione-obiettivi", "references", "asset-location.md"), encoding="utf-8").read()
    assert "rischio demografico" in al, "asset-location: polizze esenti IRPEF solo per il rischio demografico"


@test("T1: le citazioni del D.Lgs. 461/97 e dell'art. 10-ter L. 77/1983 portano il riferimento dal 2027")
def t_t1_doppie_citazioni():
    # Regola della roadmap «Citazioni dal 2027»: l'art. 6 D.Lgs. 461/97 confluisce nell'art. 306
    # del TU D.Lgs. 117/2026 (c. 2 → c. 3, c. 4 → c. 5, c. 5 → c. 6, c. 7 → c. 8), l'art. 5 nel 304,
    # l'art. 10-ter L. 77/1983 nell'art. 59 dell'All. 1 al D.Lgs. 33/2025. Nei file del tema T1
    # ogni riga che cita la norma vecchia nomina anche quella nuova.
    file_t1 = ["README.md",
               "skills/it-pianificazione/references/integrazione-fiscale-joint.md",
               "skills/it-rebalance/SKILL.md",
               "skills/it-rebalance/assets/ribilanciamento-multibroker.py",
               "skills/it-rebalance/references/ribilanciamento-multibroker.md",
               "skills/it-rebalance/references/sequenza-liquidazione.md",
               "skills/it-tax-optimization/SKILL.md"] + [
               f"skills/it-tax-optimization/references/{f}" for f in
               ("aliquote-12-5-26.md", "criptovalute.md", "etf-trap-redditi-capitale.md",
                "multi-intermediario.md", "regime-dichiarativo.md")]
    testi = _testi_regole()
    errori = []
    for rel in file_t1:
        for riga in testi[rel].splitlines():
            if re.search(r"D\.\s?Lgs\.\s?461|10-ter", riga) and not re.search(r"30[4-7]|TU 2027|117/2026|33/2025", riga):
                errori.append(f"{rel}: «{riga.strip()[:110]}»")
    assert not errori, "citazioni senza il riferimento dal 2027:\n  " + "\n  ".join(errori)


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


@test("proiezione-pensione.xlsx: detrazione pensionati = netto-pensione.py (art. 13 c. 3 TUIR)")
def t_excel_detrazione():
    # REGRESSIONE F008: Pubblica!B64 usava una formula inventata (1.880 € fissi oltre 28.000).
    from openpyxl import load_workbook
    orig = asset("it-pianificazione", "proiezione-pensione.xlsx")
    ws = load_workbook(xlsx_ricalcolati()[orig], data_only=True)["Pubblica"]
    cartella = os.path.dirname(orig)
    sys.path.insert(0, cartella)  # netto-pensione importa motore_bootstrap
    try:
        netto = carica_modulo(asset("it-pianificazione", "netto-pensione.py"))
    finally:
        sys.path.remove(cartella)
    lorda, detrazione = ws["B61"].value, ws["B64"].value
    attesa = netto.detrazione_pensione(lorda)
    assert abs(detrazione - attesa) < 0.01, f"B64 = {detrazione:.2f} su lorda {lorda:,.0f}, attesa {attesa:.2f}"


@test("parametri previdenziali: nessun valore superato né dato personale dell'autore")
def t_parametri_superati():
    # REGRESSIONE F002/F009/F051: massimale 2025 spacciato per 2026, plafond "era €5.300",
    # "Quota 104" (mai esistita), riferimenti all'autore nelle reference.
    vietati = ("~€120.607", "era €5.300", "Quota 104", "Eugenio", "Calabria", "no, attenzione")
    for base in (SKILLS, os.path.join(ROOT, "commands")):
        for cartella, _, files in os.walk(base):
            for f in files:
                if f.endswith((".md", ".py")):
                    testo = open(os.path.join(cartella, f), encoding="utf-8").read()
                    for v in vietati:
                        assert v not in testo, f"{os.path.relpath(os.path.join(cartella, f), ROOT)}: «{v}»"


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
    # REGRESSIONE F056: rendimento reale del fondo a zero → ZeroDivisionError. A r = 0 i
    # versamenti mancati valgono versamento × anni (annuità lineare).
    rc, out = run_script(sc, "--set", "RENDIMENTO_FP_REALE=0.0", "--set", "VERSAMENTO_FP_ANNUO=1000.0",
                         "--set", "COEFF_TRASFORMAZIONE=0.05")
    assert rc == 0, out[-300:]
    anni = int(re.search(r"\((\d+) anni di contributi in meno", out).group(1))
    assert euro(out, "Rendita fondo:") == 50 * anni, "rendita persa a r = 0 ≠ versamento × anni × coeff."


@test("cruscotto TWR: ultima riga dinamica (5 o 14 rilevazioni), righe vuote senza −100%")
def t_twr_dinamico():
    # REGRESSIONE F049: il foglio funzionava solo con 13 righe esatte (meno → −100%,
    # di più → TWR, XIRR e flusso terminale fermi alla riga 18).
    import datetime
    from openpyxl import load_workbook
    mod = ricalcolatore()
    tmp = tempfile.mkdtemp()
    try:
        orig = asset("it-revisione", "cruscotto-patrimoniale.xlsx")
        corta, lunga = os.path.join(tmp, "corta.xlsx"), os.path.join(tmp, "lunga.xlsx")
        wb = load_workbook(orig)
        for r in range(11, 19):  # compilati solo i primi 5 mesi
            for col in "ABC":
                wb["Rendimento TWR"][f"{col}{r}"] = None
        wb.save(corta)
        wb = load_workbook(orig)
        ws = wb["Rendimento TWR"]
        ws["A19"], ws["B19"], ws["C19"] = datetime.datetime(2026, 2, 1), 90500, 750
        wb.save(lunga)
        out_corta, out_lunga = mod.ricalcola([corta, lunga], os.path.join(tmp, "out"))
        c = load_workbook(out_corta, data_only=True)["Rendimento TWR"]
        assert c["I5"].value == 5, f"rilevazioni contate: {c['I5'].value!r}"
        assert abs(c["I6"].value - (c["E10"].value - 1)) < 1e-9, "TWR non legge l'ultima riga compilata"
        assert isinstance(c["I9"].value, float), f"XIRR su 5 righe: {c['I9'].value!r}"
        for r in range(11, 19):
            for col in "DEF":
                assert c[f"{col}{r}"].value in (None, ""), f"{col}{r} = {c[f'{col}{r}'].value!r} su riga vuota"
        lw = load_workbook(out_lunga, data_only=True)["Rendimento TWR"]
        assert lw["I5"].value == 14 and abs(lw["I6"].value - (lw["E19"].value - 1)) < 1e-9, "la 14ª riga non entra"
        assert lw["F18"].value == -750 and lw["F19"].value == -750 + 90500, "flusso terminale non spostato"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test("cruscotto: Leggimi, Sintesi con soglia per priorità, bande 5/25, costi e riga ISC")
def t_cruscotto_revisione():
    # REGRESSIONE F064 (soglie fisse 70/50), F030 (banda ±5 uguale per tutte le classi),
    # F050 (nessun controllo dei costi), F049 (limiti non dichiarati).
    from openpyxl import load_workbook
    wb = load_workbook(xlsx_ricalcolati()[asset("it-revisione", "cruscotto-patrimoniale.xlsx")], data_only=True)
    assert wb.sheetnames[0] == "Leggimi", f"fogli: {wb.sheetnames}"
    assert any("120" in str(c.value) for r in wb["Leggimi"].iter_rows() for c in r), "Leggimi senza i limiti"
    s = wb["Sintesi"]
    assert (s["G5"].value, s["H5"].value) == ("Priorità", "Soglia"), (s["G5"].value, s["H5"].value)
    assert s["F6"].value == "On track" and s["F7"].value == "A rischio", (s["F6"].value, s["F7"].value)
    a = wb["Allocazione"]
    assert a["F5"].value == 0.05 and abs(a["F7"].value - 0.0375) < 1e-12, (a["F5"].value, a["F7"].value)
    assert str(a["E9"].value).startswith("Sottopeso"), f"alternativi 0% vs target 5%: {a['E9'].value!r}"
    an = wb["Andamento"]
    etichette = {str(an[f"A{r}"].value): r for r in range(1, 40) if an[f"A{r}"].value}
    assert any(e.startswith("COSTI DELL'ANNO") for e in etichette), "blocco costi assente"
    bollo = next(r for e, r in etichette.items() if e.startswith("Bollo"))
    assert abs(an[f"B{bollo}"].value - 88000 * 0.002) < 1e-9, f"bollo: {an[f'B{bollo}'].value!r}"
    assert any("ISC" in str(wb["Azioni"][f"A{r}"].value) for r in range(5, 12)), "manca la riga demo sull'ISC"


@test("bande di ribilanciamento: regola 5/25 in cruscotto, tracker e IPS")
def t_bande_5_25():
    # REGRESSIONE F030: stesso portafoglio «in banda» nel cruscotto e fuori banda nello script.
    from openpyxl import load_workbook
    def formula(nome, foglio, cella):
        return str(load_workbook(asset("it-revisione", nome))[foglio][cella].value)
    assert "MIN($B$12" in formula("cruscotto-patrimoniale.xlsx", "Allocazione", "F5")
    assert "MIN(Impostazioni!$B$14" in formula("tracker-secchielli.xlsx", "Controllo", "F15")
    assert "MIN(0.05" in formula("investment-policy-statement.xlsx", "IPS", "C21")


@test("revisione: costi dell'anno nel metodo e nel template, nessun percorso di sandbox")
def t_revisione_testi():
    cartella = os.path.join(SKILLS, "it-revisione")
    for rel in ("references/metodo-revisione.md", "assets/template-revisione.md"):
        assert "Costi dell'anno" in open(os.path.join(cartella, rel), encoding="utf-8").read(), rel
    assert "/mnt/skills" not in open(os.path.join(cartella, "SKILL.md"), encoding="utf-8").read(), \
        "SKILL.md cita ancora recalc.py del sandbox claude.ai"


@test("scadenze di fine anno: ovunque c'è il fondo pensione c'è anche la comunicazione dei non dedotti")
def t_non_dedotti():
    # REGRESSIONE F020: senza comunicazione al fondo entro il 31/12 dell'anno successivo,
    # i contributi non dedotti vengono tassati di nuovo in uscita.
    from openpyxl import load_workbook
    for rel in ("skills/it-revisione/SKILL.md", "skills/it-revisione/references/metodo-revisione.md",
                "skills/it-revisione/assets/template-revisione.md",
                "skills/it-revisione/references/investment-policy-statement.md",
                "skills/it-revisione/assets/genera-ips.py", "commands/revisione.md",
                "skills/it-pianificazione-autonomi/references/fiscalita-forfettario.md"):
        assert "non dedott" in open(os.path.join(ROOT, rel), encoding="utf-8").read(), f"{rel}: manca la comunicazione"
    for nome, foglio, cella in (("cruscotto-patrimoniale.xlsx", "Azioni", "A2"),
                                ("investment-policy-statement.xlsx", "IPS", "A47")):
        testo = load_workbook(asset("it-revisione", nome))[foglio][cella].value
        assert "non dedott" in testo, f"{nome} {foglio}!{cella}: manca la comunicazione"


@test("autonomi: artigiani e commercianti fuori perimetro, casse CIPAG ed ENPAM aggiornate")
def t_autonomi_perimetro():
    # REGRESSIONE F016/F038/F009: artigiani-commercianti accettati e trattati come Gestione
    # Separata; CIPAG integrativo al 4%; ENPAM senza aliquota di Quota B; soglie superate.
    cartella = os.path.join(SKILLS, "it-pianificazione-autonomi")
    skill = open(os.path.join(cartella, "SKILL.md"), encoding="utf-8").read()
    assert "/ artigiani-commercianti" not in skill, "artigiani-commercianti ancora tra i tipi di cassa in input"
    assert re.search(r"description:[^\n]*artigian", skill), "description senza l'esclusione di artigiani e commercianti"
    comando = open(os.path.join(ROOT, "commands", "pensione-autonomi.md"), encoding="utf-8").read()
    assert "artigian" in comando, "il comando non esclude artigiani e commercianti"
    casse = open(os.path.join(cartella, "references", "casse-professionali.md"), encoding="utf-8").read()
    cipag = next(r for r in casse.splitlines() if r.startswith("| **CIPAG**"))
    enpam = next(r for r in casse.splitlines() if r.startswith("| **ENPAM**"))
    assert "5%" in cipag and "Verificato: 2026-10" in cipag, f"riga CIPAG: {cipag[:120]}"
    assert "19,5" in enpam and "Verificato: 2026-10" in enpam, f"riga ENPAM: {enpam[:120]}"
    gs = open(os.path.join(cartella, "references", "previdenza-gestione-separata.md"), encoding="utf-8").read()
    for superato in ("1,5× assegno sociale", "considerabile anche la rendita della complementare"):
        assert superato not in gs, f"previdenza-gestione-separata.md: «{superato}»"


# ══════════════════════ freshness · json · guardia ══════════════════════

# File con dati normativi che DEVONO portare almeno un marcatore «Verificato: AAAA-MM»:
# senza, i loro numeri resterebbero fuori dal controllo mensile di freshness.yml (F024).
OBBLIGATI_FRESHNESS = (
    "it-tax-optimization/references/aliquote-12-5-26.md",
    "it-tax-optimization/references/etf-trap-redditi-capitale.md",
    "it-tax-optimization/references/regime-dichiarativo.md",
    "it-tax-optimization/references/criptovalute.md",
    "it-tax-optimization/references/criptovalute-avanzate.md",
    "it-tax-optimization/references/criptovalute-casi-speciali.md",
    "it-pianificazione/SKILL.md",
    "it-pianificazione/references/previdenza-obbligatoria.md",
    "it-pianificazione/references/previdenza-complementare.md",
    "it-pianificazione/assets/netto-pensione.py",
    "it-pianificazione/assets/proiezione-inps.py",
    "it-pianificazione/assets/ponte-pensione.py",
    "it-pianificazione/assets/importa-previdenza.py",
    "it-pianificazione-autonomi/references/casse-professionali.md",
    "it-pianificazione-autonomi/references/previdenza-gestione-separata.md",
    "it-pianificazione-autonomi/references/fiscalita-forfettario.md",
    "it-pianificazione-obiettivi/references/asset-location.md",
    "it-rebalance/SKILL.md",
    "it-revisione/assets/genera-ips.py",
)


def marcatori_freshness():
    """[(file relativo a skills/, anno, mese)] per ogni «Verificato: AAAA-MM» nei .py e .md."""
    trovati = []
    for base, _, files in os.walk(SKILLS):
        for f in sorted(files):
            if f.endswith((".py", ".md")):
                rel = os.path.relpath(os.path.join(base, f), SKILLS)
                testo = open(os.path.join(base, f), encoding="utf-8", errors="replace").read()
                for m in re.finditer(r"Verificato: (\d{4})-(\d{2})", testo):
                    trovati.append((rel, int(m.group(1)), int(m.group(2))))
    return trovati


def tabella_freshness():
    """Tabella Markdown per il README: per ogni file la verifica più vecchia e fin quando vale."""
    piu_vecchia = {}
    for rel, a, m in marcatori_freshness():
        piu_vecchia[rel] = min(piu_vecchia.get(rel, (a, m)), (a, m))
    righe = ["| File | Verificato | Valido fino a |", "|---|---|---|"]
    for rel, (a, m) in sorted(piu_vecchia.items(), key=lambda kv: (kv[1], kv[0])):
        righe.append(f"| `{rel}` | {a}-{m:02d} | {a + 1}-{m:02d} |")
    return "\n".join(righe)


@test("freshness fiscale: i file normativi portano 'Verificato: AAAA-MM' e nessuno supera i 12 mesi")
def t_freshness():
    import datetime
    trovati = marcatori_freshness()
    marcati = {rel for rel, _, _ in trovati}
    mancanti = [rel for rel in OBBLIGATI_FRESHNESS if rel not in marcati]
    assert not mancanti, ("file normativi senza marcatore (verificarli alle fonti primarie e "
                          f"aggiungere «Verificato: AAAA-MM»): {mancanti}")
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


# ═══════════════════════════ EXCEL RICALCOLATI ═══════════════════════════
# openpyxl legge solo le cache salvate nei file: questi test ricalcolano gli
# xlsx con LibreOffice in locale italiano (scripts/ricalcola-excel.py). Senza
# LibreOffice i test sono saltati, salvo RICHIEDI_LIBREOFFICE=1 (la CI).

_RICALCOLATI = {}
VOLATILI = ("TODAY(", "NOW(", "RAND(", "RANDBETWEEN(")


def ricalcolatore():
    mod = carica_modulo(os.path.join(ROOT, "scripts", "ricalcola-excel.py"))
    if not mod.trova_soffice():
        if os.environ.get("RICHIEDI_LIBREOFFICE"):
            raise AssertionError("RICHIEDI_LIBREOFFICE è impostato ma LibreOffice non è installato")
        raise Salta("LibreOffice non installato")
    return mod


def xlsx_ricalcolati():
    """{xlsx del plugin: copia ricalcolata}, un solo ricalcolo per esecuzione della suite."""
    if not _RICALCOLATI:
        mod = ricalcolatore()
        originali = mod.tutti_gli_xlsx()
        _RICALCOLATI.update(zip(originali, mod.ricalcola(originali, tempfile.mkdtemp(prefix="ricalcolo-"))))
    return _RICALCOLATI


@test("ricalcolo Excel: LibreOffice ricalcola al caricamento, in locale italiano")
def t_ricalcolo():
    import zipfile
    from openpyxl import Workbook, load_workbook
    mod = ricalcolatore()
    tmp = tempfile.mkdtemp()
    wb = Workbook()
    ws = wb.active
    ws["A1"], ws["A2"], ws["A3"] = 5, "=A1*3", "=FIXED(1.5,1)"
    nuovo = os.path.join(tmp, "nuovo.xlsx")
    wb.save(nuovo)
    # Cache vecchia: A2 dichiara 6 (come se A1 valesse ancora 2), A3 "1.5".
    vecchio = os.path.join(tmp, "vecchio.xlsx")
    with zipfile.ZipFile(nuovo) as zi, zipfile.ZipFile(vecchio, "w") as zo:
        for voce in zi.infolist():
            dati = zi.read(voce.filename)
            if voce.filename == "xl/worksheets/sheet1.xml":
                dati = re.sub(rb"(<c r=\"A2\"[^>]*>\s*<f>A1\*3</f>)\s*(<v\s*/>|<v>\s*</v>)?", rb"\1<v>6</v>", dati)
                dati = re.sub(rb"(<c r=\"A3\")([^>]*>\s*<f>[^<]*</f>)\s*(<v\s*/>|<v>\s*</v>)?",
                              rb'\1 t="str"\2<v>1.5</v>', dati)
            zo.writestr(voce, dati)
    assert load_workbook(vecchio, data_only=True).active["A2"].value == 6, "fixture: cache vecchia non scritta"
    (out,) = mod.ricalcola([vecchio], os.path.join(tmp, "out"))
    ws = load_workbook(out, data_only=True).active
    assert ws["A2"].value == 15, f"cache non ricalcolata: A2 = {ws['A2'].value}"
    assert ws["A3"].value == "1,5", f"locale non italiano: FIXED(1.5;1) = {ws['A3'].value!r}"


@test("Excel: ricalcolati in locale italiano, nessuna cella in errore")
def t_excel_errori():
    mod = ricalcolatore()
    for orig, ricalcolato in xlsx_ricalcolati().items():
        trovati = mod.errori(ricalcolato)
        assert not trovati, f"{os.path.basename(orig)}: {len(trovati)} celle in errore, es. {trovati[:3]}"


@test("Excel: le cache consegnate coincidono col ricalcolo (file aggiornati prima del commit)")
def t_excel_cache():
    import math
    from openpyxl import load_workbook
    problemi = []
    for orig, ricalcolato in xlsx_ricalcolati().items():
        formule = load_workbook(orig)
        if any(isinstance(c.value, str) and any(v in c.value.upper() for v in VOLATILI)
               for ws in formule.worksheets for riga in ws.iter_rows() for c in riga):
            continue  # con OGGI() la cache dipende dal giorno: per questi file contano solo gli errori
        cache, nuovo = load_workbook(orig, data_only=True), load_workbook(ricalcolato, data_only=True)
        diverse = []
        for ws in formule.worksheets:
            for riga in ws.iter_rows():
                for c in riga:
                    if not (isinstance(c.value, str) and c.value.startswith("=")):
                        continue
                    a, b = cache[ws.title][c.coordinate].value, nuovo[ws.title][c.coordinate].value
                    numeri = all(isinstance(x, (int, float)) for x in (a, b))
                    if not (a == b or (numeri and math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9))):
                        diverse.append(f"{ws.title}!{c.coordinate}: {a!r} → {b!r}")
        if diverse:
            problemi.append(f"{os.path.basename(orig)}: {len(diverse)} cache diverse, es. {diverse[:2]}")
    assert not problemi, ("; ".join(problemi) + ". Se le formule sono giuste: "
                          "python scripts/ricalcola-excel.py FILE --in-place")


@test("runner: --only/--skip filtrano i test per sottostringa del nome")
def t_filtro():
    me = os.path.abspath(__file__)
    r = subprocess.run([sys.executable, me, "--only", "freshness"],
                       capture_output=True, text=True, timeout=120)
    assert "1/1 test passati" in r.stdout, r.stdout[-400:]
    assert "freshness fiscale" in r.stdout
    r = subprocess.run([sys.executable, me, "--skip", "freshness", "--only", "igiene"],
                       capture_output=True, text=True, timeout=120)
    assert "4/4 test passati" in r.stdout, r.stdout[-400:]
    assert "freshness" not in r.stdout
    r = subprocess.run([sys.executable, me, "--only", "nome-inesistente"],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode != 0, "nessun test selezionato deve essere un errore, non un verde vuoto"


@test("runner: la tabella dello stato dei dati normativi elenca i file obbligati con la scadenza")
def t_tabella_dati_normativi():
    r = subprocess.run([sys.executable, os.path.abspath(__file__), "--tabella-freshness"],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr[-300:]
    assert r.stdout.startswith("| File | Verificato | Valido fino a |"), r.stdout[:200]
    for rel in OBBLIGATI_FRESHNESS:
        assert f"| `{rel}` |" in r.stdout, f"{rel} assente dalla tabella"


@test("pacchetto: lo zip per Cowork contiene solo il plugin, nome = versione del manifest")
def t_pacchetto():
    import zipfile
    script = os.path.join(ROOT, "scripts", "pacchetto.py")
    ver = json.load(open(os.path.join(ROOT, ".claude-plugin", "plugin.json")))["version"]
    tmp = tempfile.mkdtemp()
    try:
        rc, out = run_script(script, "--out", tmp, "--tag", f"v{ver}", cwd=ROOT)
        assert rc == 0, out[-400:]
        zpath = os.path.join(tmp, f"wealth-management-it-v{ver}.zip")
        assert os.path.exists(zpath), f"zip atteso: {zpath}; presenti: {os.listdir(tmp)}"
        nomi = zipfile.ZipFile(zpath).namelist()
        radice = "wealth-management-it/"
        assert all(n.startswith(radice) for n in nomi), "tutto deve stare sotto wealth-management-it/"
        for atteso in (radice + ".claude-plugin/plugin.json", radice + "README.md",
                       radice + "LICENSE", radice + "NOTICE",  # Apache-2.0 §4: licenza e attribuzione
                       radice + "commands/pensione.md",
                       radice + "skills/it-tax-optimization/SKILL.md",
                       radice + "skills/it-pianificazione/assets/proiezione-inps.py"):
            assert atteso in nomi, f"manca {atteso}"
        for vietato in ("/tests/", "/.github/", "/.remember/", "__pycache__", ".DS_Store",
                        "/.git/", "/scripts/", "/dist/", "/ordini/"):
            assert not any(vietato in n for n in nomi), f"nello zip non deve esserci {vietato}"
        # il tag deve coincidere con la versione del manifest
        rc, out = run_script(script, "--out", tmp, "--tag", "v9.9.9", cwd=ROOT)
        assert rc != 0 and "9.9.9" in out, "tag ≠ manifest deve fallire citando le versioni"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


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
    ap.add_argument("--tabella-freshness", action="store_true",
                    help="stampa la tabella Markdown dello stato dei dati normativi (per il README) ed esce")
    args = ap.parse_args()
    if args.tabella_freshness:
        print(tabella_freshness())
        sys.exit(0)

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
    saltati = sum(1 for _, esito, _ in RISULTATI if esito is None)
    eseguiti = len(RISULTATI) - saltati
    for nome, esito, dett in RISULTATI:
        if esito is None:
            print(f"  ⏭️  {nome} — saltato: {dett}")
            continue
        print(("  ✅ " if esito else "  ❌ ") + nome)
        if not esito:
            print("       → " + dett)
    print("-" * 74)
    print(f"{ok}/{eseguiti} test passati" + (f", {saltati} saltati" if saltati else ""))
    sys.exit(0 if ok == eseguiti else 1)


if __name__ == "__main__":
    main()
