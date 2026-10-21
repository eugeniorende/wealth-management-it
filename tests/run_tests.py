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


# ══════════════════════ previdenza (T5, T4, T6) ══════════════════════

def _modulo_previdenza(nome):
    """Importa uno script di it-pianificazione/assets (importano motore_bootstrap dalla loro cartella)."""
    cartella = os.path.join(SKILLS, "it-pianificazione", "assets")
    sys.path.insert(0, cartella)
    try:
        return carica_modulo(os.path.join(cartella, nome))
    finally:
        sys.path.remove(cartella)


def _per_etichetta(ws, testo, col="B"):
    """Valore della colonna col nella riga la cui etichetta in A contiene testo (layout-indipendente)."""
    for r in range(1, ws.max_row + 1):
        if testo.lower() in str(ws[f"A{r}"].value or "").lower():
            return ws[f"{col}{r}"].value
    raise AssertionError(f"{ws.title}: nessuna riga con etichetta «{testo}»")


_VARIANTI = {}


def _varianti(skill, nome_xlsx, varianti):
    """Copie ricalcolate di un xlsx con input modificati, una sola volta per suite.

    varianti: {nome: {(foglio, cella): valore}} → {nome: workbook data_only}.
    Le copie sono temporanee: l'originale non viene mai salvato con openpyxl."""
    from openpyxl import load_workbook
    chiave = (skill, nome_xlsx, repr(sorted((k, sorted(v.items())) for k, v in varianti.items())))
    if chiave not in _VARIANTI:
        mod = ricalcolatore()
        tmp = tempfile.mkdtemp()
        try:
            percorsi = []
            for nome, celle in varianti.items():
                wb = load_workbook(asset(skill, nome_xlsx))
                for (foglio, cella), v in celle.items():
                    wb[foglio][cella] = v
                percorsi.append(os.path.join(tmp, f"{nome}.xlsx"))
                wb.save(percorsi[-1])
            prodotti = mod.ricalcola(percorsi, os.path.join(tmp, "out"))
            _VARIANTI[chiave] = {n: load_workbook(p, data_only=True) for n, p in zip(varianti, prodotti)}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return _VARIANTI[chiave]


def _pensione_contributiva(m0, ral, g, r, n, massimale, aliquota, coeff):
    """Replica indipendente della meccanica L. 335/1995 in euro di oggi: il montante si rivaluta
    al PIL reale r, il contributo dell'anno entra senza rivalutazione, la retribuzione oltre il
    massimale non versa contributi."""
    m = m0
    for t in range(n):
        m = m * (1 + r) + min(ral * (1 + g) ** t, massimale) * aliquota
    return m * coeff


def _coeff_excel(wb, eta):
    c = wb["Coefficienti"]
    return next(c[f"C{r}"].value for r in range(5, 20) if c[f"A{r}"].value == eta)


PP = ("it-pianificazione", "proiezione-pensione.xlsx")
VARIANTI_PP = {"ral150k": {("Input", "B10"): 150_000, ("Input", "B12"): 0.0},
               "ral8k": {("Input", "B10"): 8_000}}


@test("proiezione-pensione.xlsx: Pubblica in euro di oggi = proiezione-inps.py (PIL reale, massimale, contributo dell'anno)")
def t_pubblica_vs_script():
    # REGRESSIONE F013/F002: Pubblica!F rivalutava anche il contributo dell'anno, il PIL era
    # nominale (1,8%) su una RAL reale, e né l'Excel né lo script applicavano il massimale.
    from openpyxl import load_workbook
    inps = _modulo_previdenza("proiezione-inps.py")
    base = load_workbook(xlsx_ricalcolati()[asset(*PP)], data_only=True)
    assert base["Input"]["B16"].value == inps.PIL_REALE, \
        f"PIL dell'Excel {base['Input']['B16'].value} ≠ PIL_REALE di proiezione-inps.py {inps.PIL_REALE}"
    for nome, wb in (("default", base), ("ral150k", _varianti(*PP, VARIANTI_PP)["ral150k"])):
        i, p = wb["Input"], wb["Pubblica"]
        massimale = _per_etichetta(i, "Massimale contributivo")
        n = int(i["B6"].value - i["B5"].value)
        atteso = _pensione_contributiva(p["E5"].value, i["B10"].value, i["B12"].value, i["B16"].value,
                                        n, massimale, i["B13"].value, p["B60"].value)
        assert abs(p["B61"].value - atteso) <= 1e-6 * atteso, \
            f"{nome}: Pubblica!B61 = {p['B61'].value:,.2f}, meccanica L. 335/1995 = {atteso:,.2f}"
        sets = (f"MONTANTE_ATTUALE={p['E5'].value!r}", f"RAL_ATTUALE={float(i['B10'].value)!r}",
                f"ETA_ATTUALE={float(i['B5'].value)!r}", f"ETA_PENSIONAMENTO={float(i['B6'].value)!r}",
                f"CRESCITA_REALE_RAL={float(i['B12'].value)!r}", f"PIL_REALE={float(i['B16'].value)!r}",
                f"COEFF_ESPLICITO={p['B60'].value!r}", f"MASSIMALE_CONTRIBUTIVO={float(massimale)!r}")
        rc, out = run_script(asset("it-pianificazione", "proiezione-inps.py"),
                             *[x for s in sets for x in ("--set", s)])
        assert rc == 0, out[-300:]
        pens = euro(out, "PENSIONE LORDA ANNUA")
        assert abs(pens - p["B61"].value) <= 1.0, f"{nome}: script {pens:,.0f} ≠ Excel {p['B61'].value:,.0f}"
    p = _varianti(*PP, VARIANTI_PP)["ral150k"]["Pubblica"]
    assert abs(p["D5"].value - 122_295 * 0.33) < 0.01, f"RAL 150k: contributo {p['D5'].value:,.2f} senza massimale"
    # lo script da solo, valore chiuso: 30 anni sopra il massimale, PIL 0, coefficiente 5%
    rc, out = run_script(asset("it-pianificazione", "proiezione-inps.py"),
                         "--set", "MONTANTE_ATTUALE=0.0", "--set", "RAL_ATTUALE=150_000.0",
                         "--set", "ETA_ATTUALE=37.0", "--set", "ETA_PENSIONAMENTO=67.0",
                         "--set", "CRESCITA_REALE_RAL=0.0", "--set", "PIL_REALE=0.0",
                         "--set", "COEFF_ESPLICITO=0.05")
    assert rc == 0, out[-300:]
    assert abs(euro(out, "PENSIONE LORDA ANNUA") - 30 * 122_295 * 0.33 * 0.05) <= 1, out[-500:]


@test("proiezione-pensione.xlsx: IRPEF, addizionali e netto di Pubblica = netto_pensionato() di netto-pensione.py")
def t_pubblica_netto():
    # Deliverable T5: Pubblica!B63:B66 ricostruite dallo script sugli stessi input, anche sotto
    # la no tax area (addizionali dovute solo se c'è IRPEF, come nello script).
    from openpyxl import load_workbook
    netto = _modulo_previdenza("netto-pensione.py")
    base = load_workbook(xlsx_ricalcolati()[asset(*PP)], data_only=True)
    for nome, wb in (("default", base), ("ral8k", _varianti(*PP, VARIANTI_PP)["ral8k"])):
        p = wb["Pubblica"]
        lorda = p["B61"].value
        n, irpef, addiz = netto.netto_pensionato(lorda, 0.02, 0.0)
        assert abs(max(0.0, p["B63"].value - p["B64"].value) - irpef) < 0.01, f"{nome}: IRPEF netta"
        assert abs(p["B65"].value - addiz) < 0.01, f"{nome}: addizionali {p['B65'].value:.2f} ≠ {addiz:.2f} (lorda {lorda:,.0f})"
        assert abs(p["B66"].value - n) < 0.01, f"{nome}: netto {p['B66'].value:,.2f} ≠ {n:,.2f}"


@test("proiezione-pensione.xlsx: Scenari in euro di oggi, Base = fogli di calcolo, parametri di colonna usati davvero")
def t_scenari_reali():
    # REGRESSIONE F013: spesa target inflazionata contro pensione in euro di oggi (il gap cambiava
    # segno) e righe crescita RAL / PIL / rendimento decorative.
    from openpyxl import load_workbook
    wb = load_workbook(xlsx_ricalcolati()[asset(*PP)], data_only=True)
    s, i, p, c = wb["Scenari"], wb["Input"], wb["Pubblica"], wb["Complementare"]
    for col in "BCD":
        assert abs(s[f"{col}18"].value - i["B39"].value) < 0.01, \
            f"Scenari!{col}18 = {s[f'{col}18'].value:,.0f}: la spesa target va in euro di oggi ({i['B39'].value:,.0f})"
    for riga, (foglio, cella) in ((11, ("Pubblica", "B61")), (12, ("Pubblica", "B66")),
                                  (13, ("Complementare", "B58")), (14, ("Complementare", "B61")),
                                  (15, ("Complementare", "B62"))):
        assert abs(s[f"C{riga}"].value - wb[foglio][cella].value) < 0.01, \
            f"Base Scenari!C{riga} ≠ {foglio}!{cella}"
    n = int(i["B6"].value - i["B5"].value)
    massimale = _per_etichetta(i, "Massimale contributivo")
    coeff = _coeff_excel(wb, i["B6"].value)
    netto = _modulo_previdenza("netto-pensione.py")
    for col in "BD":
        g, r, d, rend = (s[f"{col}{k}"].value for k in (5, 6, 8, 9))
        atteso = _pensione_contributiva(p["E5"].value, i["B10"].value, g, r, n, massimale, i["B13"].value,
                                        coeff * (1 - d) ** (n / 2))
        assert abs(s[f"{col}11"].value - atteso) <= 1e-6 * atteso, \
            f"Scenari!{col}11 = {s[f'{col}11'].value:,.0f}, ricalcolo con i parametri di colonna = {atteso:,.0f}"
        assert abs(s[f"{col}12"].value - netto.netto_pensionato(atteso, 0.02, 0.0)[0]) < 0.01, f"Scenari!{col}12"
        fondo = _fondo_scenario(wb, g, rend, n)
        assert abs(s[f"{col}13"].value - fondo) <= 1e-6 * fondo, \
            f"Scenari!{col}13 = {s[f'{col}13'].value:,.0f}, fondo col rendimento di colonna = {fondo:,.0f}"
    assert s["B11"].value < s["C11"].value < s["D11"].value and s["B13"].value < s["C13"].value < s["D13"].value


def _fondo_scenario(wb, g, rend, n):
    """Montante del fondo (foglio Complementare) ricalcolato con crescita RAL g e rendimento rend."""
    i = wb["Input"]
    dovuto = _per_etichetta(i, "Contributo dovuto lavoratore")
    m = i["B22"].value * i["B21"].value + i["B25"].value   # il saldo TFR entra solo se conferito
    for t in range(n):
        ral = i["B10"].value * (1 + g) ** t
        m = m * (1 + rend) + ral * (0.0691 * i["B21"].value + i["B27"].value + dovuto) + i["B26"].value
    return m


@test("importa-previdenza: tassi di capitalizzazione ufficiali 1997-2025, carriera dal 1998 senza tassi inventati")
def t_tassi_capitalizzazione():
    # REGRESSIONE F062: tabella limitata al 2021-2025, default 1,01 per gli anni precedenti
    # (sottostima ~8% per chi ha iniziato a fine anni '90) e anche per l'anno in corso, non pubblicato.
    ufficiali = {  # nota ISTAT 16/10/2025 (lavoro.gov.it); 2014 e 2021 a 1, 2022 con recupero (DL 65/2015 art. 5)
        1997: 1.055871, 1998: 1.053597, 1999: 1.056503, 2000: 1.051781, 2001: 1.047781, 2002: 1.043698,
        2003: 1.041614, 2004: 1.039272, 2005: 1.040506, 2006: 1.035386, 2007: 1.033937, 2008: 1.034625,
        2009: 1.033201, 2010: 1.017935, 2011: 1.016165, 2012: 1.011344, 2013: 1.001643, 2014: 1.000000,
        2015: 1.005058, 2016: 1.004684, 2017: 1.005205, 2018: 1.013478, 2019: 1.018254, 2020: 1.019199,
        2021: 1.000000, 2022: 1.009756, 2023: 1.023082, 2024: 1.036622, 2025: 1.040445}
    m = carica_modulo(asset("it-pianificazione", "importa-previdenza.py"))
    for anno, tasso in ufficiali.items():
        assert m.TASSI_CAPITALIZZAZIONE.get(anno) == tasso, f"tasso {anno}: {m.TASSI_CAPITALIZZAZIONE.get(anno)} ≠ {tasso}"
    retrib = {a: 30_000.0 for a in range(1998, 2026)}
    montante, _, mancanti = m.ricostruisci_montante(retrib, 2026)
    atteso = 0.0
    for anno in range(1998, 2027):  # il 2026 non ha ancora un tasso: nessuna rivalutazione
        atteso = atteso * ufficiali.get(anno, 1.0) + retrib.get(anno, 0.0) * m.ALIQUOTA_COMPUTO
    assert abs(montante - atteso) < 0.01, f"montante {montante:,.2f} ≠ {atteso:,.2f}"
    assert mancanti == [2026], f"anni senza tasso pubblicato: {mancanti}"
    rc, out = run_script(asset("it-pianificazione", "importa-previdenza.py"),
                         os.path.join(FIXTURES, "estratto-inps-test.xml"))
    assert rc == 0, out[-300:]
    assert "sono i primi anni" not in out and "non ancora pubblicat" in out, out[-600:]


@test("netto-pensione: netto dello stipendio con le misure L. 207/2024 c. 4-6 e il contributo IVS aggiuntivo")
def t_netto_stipendio():
    netto = _modulo_previdenza("netto-pensione.py")
    # RAL 30.000: reddito 27.243 → ulteriore detrazione di 1.000 € (c. 6, reddito tra 20.000 e 32.000)
    _, contr, irpef, _ = netto.netto_lavoratore(30_000, netto.ALIQ_CONTRIBUTI_DIP, 0.0, 0.0)
    imponibile = 30_000 - 30_000 * 0.0919
    atteso = imponibile * 0.23 - (1_910 + 1_190 * (28_000 - imponibile) / 13_000) - 1_000
    assert abs(irpef - atteso) < 0.01, f"RAL 30k: IRPEF {irpef:,.2f} ≠ {atteso:,.2f}"
    # RAL 36.000: reddito 32.692,40 → detrazione decrescente 1.000 × (40.000 − R) / 8.000
    _, _, irpef, _ = netto.netto_lavoratore(36_000, netto.ALIQ_CONTRIBUTI_DIP, 0.0, 0.0)
    r = 36_000 * (1 - 0.0919)
    atteso = 6_440 + (r - 28_000) * 0.33 - 1_910 * (50_000 - r) / 22_000 - 1_000 * (40_000 - r) / 8_000
    assert abs(irpef - atteso) < 0.01, f"RAL 36k: IRPEF {irpef:,.2f} ≠ {atteso:,.2f}"
    # RAL 18.000: reddito 16.345,80 ≤ 20.000 → somma esente del 4,8% del reddito di lavoro (c. 4)
    n18, _, irpef18, _ = netto.netto_lavoratore(18_000, netto.ALIQ_CONTRIBUTI_DIP, 0.0, 0.0)
    r = 18_000 * (1 - 0.0919)
    assert abs(n18 - (r - irpef18 + r * 0.048)) < 0.01, f"RAL 18k: netto {n18:,.2f} senza la somma del c. 4"
    # RAL 80.000: 1% aggiuntivo sulla parte oltre la prima fascia di €56.224
    _, contr, _, _ = netto.netto_lavoratore(80_000, netto.ALIQ_CONTRIBUTI_DIP, 0.0, 0.0)
    assert abs(contr - (80_000 * 0.0919 + (80_000 - 56_224) * 0.01)) < 0.01, f"RAL 80k: contributi {contr:,.2f}"


def _file_testo(*basi):
    for base in basi:
        for cartella, _, files in os.walk(base):
            for f in sorted(files):
                if f.endswith((".md", ".py")):
                    p = os.path.join(cartella, f)
                    yield os.path.relpath(p, ROOT), open(p, encoding="utf-8").read()


@test("coerenza tra skill: massimale, prima fascia, plafond e assegno sociale 2026 uguali in tutte le copie")
def t_coerenza_parametri_2026():
    # Decisione 5 della roadmap: copie dei dati normativi in ogni skill, con un test di coerenza.
    from openpyxl import load_workbook
    regole = {
        "massimale": r"(?:[Mm]assimale(?: annuo)?(?: contributivo)?(?: 2026)?|[Tt]etto contributivo(?: annuo)?(?: 2026)?)"
                     r"\**:?\**\s*(?:di\s*)?€\s*(\d{3}\.\d{3})|massimale_(\d{6})",
        "prima fascia": r"prima fascia[^€\n]{0,60}€\s*(\d{2}\.\d{3})(?![\d.,])",
        "plafond": r"(?:[Dd]educibil\w*|plafond|[Tt]etto di deducibilità)[^€\n]{0,40}€\s*(\d\.\d{3}(?:,\d{2})?)(?![\d.])",
        "assegno sociale": r"assegno sociale[^€\n]{0,60}€\s*(\d{3},\d{2}) al mese",
    }
    trovati = {k: {} for k in regole}
    for rel, testo in _file_testo(SKILLS, os.path.join(ROOT, "commands")):
        for riga in testo.splitlines():
            if "120.607" in riga:
                assert "2025" in riga, f"{rel}: 120.607 (massimale 2025) senza l'anno: {riga.strip()[:120]}"
            for nome, rx in regole.items():
                for m in re.finditer(rx, riga):
                    v = next(g for g in m.groups() if g)
                    v = v.replace(".", "").replace(",", ".")
                    trovati[nome].setdefault(float(v), set()).add(rel)
    for nome, valori in trovati.items():
        assert len(valori) == 1, f"{nome}: valori diversi tra le copie {valori}"
    massimale = next(iter(trovati["massimale"]))
    prima_fascia = next(iter(trovati["prima fascia"]))
    assert _modulo_previdenza("proiezione-inps.py").MASSIMALE_CONTRIBUTIVO == massimale
    np_ = _modulo_previdenza("netto-pensione.py")
    assert np_.MASSIMALE_CONTRIBUTIVO == massimale and np_.PRIMA_FASCIA_PENSIONABILE == prima_fascia
    wb = load_workbook(asset(*PP))
    assert _per_etichetta(wb["Input"], "Massimale contributivo") == massimale, "massimale dell'Excel dipendenti"
    plafond = next(iter(trovati["plafond"]))
    for skill, nome in (PP, ("it-pianificazione-autonomi", "proiezione-pensione-autonomi.xlsx")):
        assert _per_etichetta(load_workbook(asset(skill, nome))["Input"], "Plafond deducibilità") == plafond, \
            f"{nome}: plafond diverso da €{plafond:,.0f}"


def _colonna(ws, testo, riga=4):
    """Lettera della colonna la cui intestazione (riga 4) contiene testo."""
    from openpyxl.utils import get_column_letter
    for c in range(1, ws.max_column + 1):
        if testo.lower() in str(ws.cell(riga, c).value or "").lower():
            return get_column_letter(c)
    raise AssertionError(f"{ws.title}: nessuna colonna «{testo}» in riga {riga}")


def _irpef(r):
    return r * 0.23 if r <= 28_000 else 6_440 + (r - 28_000) * 0.33 if r <= 50_000 else 13_700 + (r - 50_000) * 0.43


def _base_uscita_fondo(i, g, n, infl):
    """Base imponibile in uscita del fondo dei dipendenti, in euro di oggi: TFR conferito e contributi
    dedotti (lavoratore + datore entro il plafond), al valore nominale riportato a oggi. Esclusi i
    rendimenti già tassati e i contributi non dedotti comunicati (art. 11 c. 6 D.Lgs. 252/2005)."""
    plafond = _per_etichetta(i, "Plafond deducibilità")
    dovuto = _per_etichetta(i, "Contributo dovuto lavoratore")
    base = (i["B22"].value * i["B21"].value + i["B25"].value) * (1 + infl) ** -n
    for t in range(n):
        ral = i["B10"].value * (1 + g) ** t
        dedotti = min(plafond, i["B26"].value + ral * (dovuto + i["B27"].value))
        base += (ral * 0.0691 * i["B21"].value + dedotti) * (1 + infl) ** (t - n)
    return base


VARIANTI_T4 = {
    "ral60k": {("Input", "B10"): 60_000, ("Input", "B27"): 0.02, ("Input", "B26"): 5_000},
    "ral60k_dovuto": {("Input", "B10"): 60_000, ("Input", "B27"): 0.02, ("Input", "B47"): 0.01},
    "rend6": {("Input", "B28"): 0.06},
    "tfr_azienda": {("Input", "B21"): 0},
    "tfr40k": {("Input", "B5"): 37, ("Input", "B6"): 67, ("Input", "B10"): 40_000, ("Input", "B12"): 0.0,
               ("Input", "B22"): 0, ("Input", "B48"): 0, ("Input", "B29"): 0, ("Input", "B17"): 0.02,
               ("Input", "B28"): 0.035, ("Input", "B21"): 1},
}


@test("proiezione-pensione.xlsx: plafond condiviso col datore, quota deducibile e spazio residuo (RAL 60k, datore 2% → €4.100)")
def t_plafond_excel():
    # REGRESSIONE F007: Complementare!E5 tappava solo il volontario a 5.300 e B64 deduceva tutto il
    # volontario anche quando il datore aveva già usato parte del plafond.
    v = _varianti(*PP, VARIANTI_T4)
    for nome, residuo, deducibile, non_dedotto in (("ral60k", 4_100, 4_100, 900), ("ral60k_dovuto", 3_500, 2_000, 0)):
        wb = v[nome]
        i, c = wb["Input"], wb["Complementare"]
        assert abs(_per_etichetta(c, "Spazio deducibile residuo") - residuo) < 0.01, \
            f"{nome}: spazio residuo {_per_etichetta(c, 'Spazio deducibile residuo')} ≠ {residuo}"
        q, nd, e = _colonna(c, "Quota deducibile"), _colonna(c, "Non dedotto"), _colonna(c, "Contrib. lavoratore")
        assert abs(c[f"{q}5"].value - deducibile) < 0.01, f"{nome}: quota deducibile {c[f'{q}5'].value}"
        assert abs(c[f"{nd}5"].value - non_dedotto) < 0.01, f"{nome}: non dedotto {c[f'{nd}5'].value}"
        attesi = i["B26"].value + i["B10"].value * _per_etichetta(i, "Contributo dovuto lavoratore")
        assert abs(c[f"{e}5"].value - attesi) < 0.01, f"{nome}: il contributo del lavoratore va tutto a montante"
        somma = sum(c[f"{q}{r}"].value or 0 for r in range(5, 55))
        assert abs(_per_etichetta(c, "Risparmio IRPEF") - somma * i["B37"].value) < 0.01, \
            f"{nome}: il risparmio IRPEF va calcolato sulla quota deducibile"
    formula = load_workbook_formule(asset(*PP))["Complementare"][f"{_colonna(v['ral60k']['Complementare'], 'Quota deducibile')}5"].value
    assert "Input!$B$44" in formula, f"la quota deducibile deve usare la cella del plafond: {formula}"


def load_workbook_formule(path):
    from openpyxl import load_workbook
    return load_workbook(path)


@test("proiezione-pensione.xlsx: tassa in uscita solo su TFR e contributi dedotti, TFR in azienda fuori dal fondo")
def t_uscita_fondo_excel():
    # REGRESSIONE F014/F037: B60 tassava l'intero montante (rendimenti già tassati compresi) e
    # G5/H5 sommavano al fondo il saldo TFR anche con il TFR lasciato in azienda.
    from openpyxl import load_workbook
    base = load_workbook(xlsx_ricalcolati()[asset(*PP)], data_only=True)
    v = _varianti(*PP, VARIANTI_T4)
    for nome, wb in (("default", base), ("rend6", v["rend6"]), ("tfr_azienda", v["tfr_azienda"])):
        i, c = wb["Input"], wb["Complementare"]
        n = int(i["B36"].value)
        attesa = _base_uscita_fondo(i, i["B12"].value, n, i["B17"].value) * i["B38"].value
        assert abs(c["B60"].value - attesa) < 0.01, f"{nome}: tassa in uscita {c['B60'].value:,.2f} ≠ {attesa:,.2f}"
    assert abs(v["rend6"]["Complementare"]["B60"].value - base["Complementare"]["B60"].value) < 0.01, \
        "il rendimento non deve cambiare la base imponibile in uscita"
    assert v["rend6"]["Complementare"]["B58"].value > base["Complementare"]["B58"].value
    c, i = v["tfr_azienda"]["Complementare"], v["tfr_azienda"]["Input"]
    assert c["D5"].value == 0 and abs(c["H5"].value - (i["B25"].value * (1 + i["B28"].value) + c["E5"].value + c["F5"].value)) < 0.01, \
        "con il TFR in azienda il saldo TFR non entra nel montante del fondo"
    f = load_workbook_formule(asset(*PP))["Complementare"]
    assert "Input!$B$22*Input!$B$21" in f["G5"].value and "Input!$B$22*Input!$B$21" in f["H5"].value
    # Scenari: la prestazione netta di ogni colonna usa la stessa base, con crescita RAL e inflazione della colonna
    s, i = base["Scenari"], base["Input"]
    n = int(i["B36"].value)
    for col in "BCD":
        g, infl, rend = s[f"{col}5"].value, s[f"{col}7"].value, s[f"{col}9"].value
        netta = _fondo_scenario(base, g, rend, n) - _base_uscita_fondo(i, g, n, infl) * i["B38"].value
        assert abs(s[f"{col}14"].value - netta) <= 1e-6 * netta, f"Scenari!{col}14 = {s[f'{col}14'].value:,.0f} ≠ {netta:,.0f}"


def _tfr_confronto(i):
    """Confronto TFR in azienda vs nel fondo, in euro di oggi, replicato dalle regole di legge:
    quota RAL × 6,91%; in azienda rivalutazione 1,5% + 75% dell'inflazione tassata al 17% e
    tassazione separata all'aliquota media sul reddito di riferimento (base × 12 / anni);
    nel fondo rendimento del comparto e 15%→9% sulle sole quote (art. 2120 c.c., art. 19 TUIR,
    art. 11 c. 6 D.Lgs. 252/2005)."""
    n, infl, rend = int(i["B36"].value), i["B17"].value, i["B28"].value
    r_tfr = (1 + (0.015 + 0.75 * infl) * 0.83) / (1 + infl) - 1
    azienda = fondo = i["B22"].value
    base = i["B22"].value * (1 + infl) ** -n
    for t in range(n):
        quota = i["B10"].value * (1 + i["B12"].value) ** t * 0.0691
        azienda = azienda * (1 + r_tfr) + quota
        fondo = fondo * (1 + rend) + quota
        base += quota * (1 + infl) ** (t - n)
    rif = base * 12 / (_per_etichetta(i, "Anni di servizio già maturati") + n)
    aliq_sep = _irpef(rif) / rif if rif > 0 else 0.0
    netto_azienda = azienda - base * aliq_sep
    netto_fondo = fondo - base * i["B38"].value
    return netto_azienda, netto_fondo


@test("proiezione-pensione.xlsx: confronto TFR in azienda vs fondo (RAL 40k per 30 anni) e TFR in azienda negli Scenari")
def t_tfr_confronto():
    # F037: il confronto era promesso dalla skill ma nessuno strumento lo calcolava.
    from openpyxl import load_workbook
    v = _varianti(*PP, VARIANTI_T4)
    base = load_workbook(xlsx_ricalcolati()[asset(*PP)], data_only=True)
    for nome, wb in (("tfr40k", v["tfr40k"]), ("default", base)):
        i, c = wb["Input"], wb["Complementare"]
        azienda, fondo = _tfr_confronto(i)
        assert abs(_per_etichetta(c, "TFR in azienda NETTO") - azienda) < 0.01, \
            f"{nome}: TFR in azienda netto {_per_etichetta(c, 'TFR in azienda NETTO'):,.2f} ≠ {azienda:,.2f}"
        assert abs(_per_etichetta(c, "TFR nel fondo NETTO") - fondo) < 0.01, f"{nome}: TFR nel fondo netto"
        assert abs(_per_etichetta(c, "Vantaggio netto del fondo") - (fondo - azienda)) < 0.01, f"{nome}: delta"
    # valore chiuso del caso RAL 40k × 30 anni (inflazione 2%, comparto 3,5% reale, nessun saldo)
    delta = _per_etichetta(v["tfr40k"]["Complementare"], "Vantaggio netto del fondo")
    # azienda: lordo 88.963,53, base 61.903,80 al 23% → netto 74.725,66; fondo: 142.685,08 − 10,5% della base
    assert abs(delta - 61_459.52) < 0.5, f"RAL 40k × 30 anni: vantaggio del fondo {delta:,.2f} ≠ 61.459,52"
    s = v["tfr_azienda"]["Scenari"]
    assert abs(s["C16"].value - _per_etichetta(v["tfr_azienda"]["Complementare"], "TFR in azienda NETTO")) < 0.01, \
        "Scenari: con il TFR in azienda il suo netto va mostrato come capitale fuori dalla rendita"
    assert base["Scenari"]["C16"].value == 0, "con il TFR nel fondo la riga del TFR in azienda è zero"


PA = ("it-pianificazione-autonomi", "proiezione-pensione-autonomi.xlsx")
VARIANTI_PA_T4 = {
    "forf_comunica": {("Input", "B28"): 3_000, ("Input", "B19"): 1},
    "forf_non_comunica": {("Input", "B28"): 3_000, ("Input", "B19"): 1, ("Input", "B47"): 0},
    "ordinario": {("Input", "B28"): 6_000, ("Input", "B19"): 2},
}


@test("proiezione-pensione-autonomi.xlsx: forfettario che comunica i non dedotti → tassa in uscita zero")
def t_uscita_fondo_autonomi():
    # REGRESSIONE F014: Complementare!B60 tassava l'intero versato anche per il forfettario puro, che
    # non deduce e, comunicando i non dedotti, in uscita non paga nulla su quella parte.
    v = _varianti(*PA, VARIANTI_PA_T4)
    for nome, dedotto_annuo, comunica in (("forf_comunica", 0, 1), ("forf_non_comunica", 0, 0), ("ordinario", 5_300, 1)):
        i, c = v[nome]["Input"], v[nome]["Complementare"]
        n, infl = int(i["B7"].value), i["B39"].value
        assert _per_etichetta(i, "Versamento dedotto") == dedotto_annuo, f"{nome}: dedotto {_per_etichetta(i, 'Versamento dedotto')}"
        tassato = dedotto_annuo + (0 if comunica else i["B28"].value - dedotto_annuo)
        attesa = (i["B31"].value * (1 + infl) ** -n + sum(tassato * (1 + infl) ** (t - n) for t in range(n))) * i["B38"].value
        tassa = _per_etichetta(c, "Tassa finale")
        assert abs(tassa - attesa) < 0.01, f"{nome}: tassa in uscita {tassa:,.2f} ≠ {attesa:,.2f}"
    assert _per_etichetta(v["forf_comunica"]["Complementare"], "Tassa finale") == 0


@test("previdenza complementare: base in uscita, non dedotti, nuove erogazioni 2026, capitale al 50%, marcatore")
def t_testi_fondo():
    pc = open(os.path.join(SKILLS, "it-pianificazione", "references", "previdenza-complementare.md"), encoding="utf-8").read()
    for atteso in ("non dedott", "durata definita", "frazionata", "9-15%", "6,91%"):
        assert atteso in pc, f"previdenza-complementare.md: manca «{atteso}»"
    assert "Verificato: 2026-06" not in pc, "marcatore di giugno non aggiornato dopo la riverifica"
    assert re.search(r"201-204[^\n]*Verificato: 2026-10|Verificato: 2026-10[^\n]*201-204", pc), "marcatore senza i commi 201-204"
    assert "contributi + rendimenti già tassati" not in pc, "base imponibile in uscita con i rendimenti già tassati"
    assert not re.search(r"(?:fino al|massimo) 60%", pc), "il capitale resta al 50% (DL 62/2026)"
    ff = open(os.path.join(SKILLS, "it-pianificazione-autonomi", "references", "fiscalita-forfettario.md"), encoding="utf-8").read()
    assert "12.800" not in ff and "15→9% sulla prestazione" not in ff, "fiscalita-forfettario.md: uscita del forfettario ancora tassata"
    for rel in ("it-pianificazione/SKILL.md", "it-pianificazione-autonomi/SKILL.md"):
        testo = open(os.path.join(SKILLS, rel), encoding="utf-8").read()
        assert "tassazione agevolata della prestazione finale (15→9%)" not in testo, f"{rel}: uscita del forfettario"


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
