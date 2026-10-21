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


def _montante_stimato(ral, g, r, anzianita, massimale, aliquota):
    """Replica indipendente della stima di Pubblica!E5 (montante al 31/12 dell'anno scorso):
    la retribuzione dell'anno −k è RAL/(1+g)^k, il massimale è costante in euro di oggi
    (L. 335/1995 art. 2 c. 18: rivalutato sui prezzi) e il contributo dell'anno −k si è
    rivalutato k−1 volte (il contributo dell'anno scorso non ancora)."""
    return sum(min(ral / (1 + g) ** k, massimale) * aliquota * (1 + r) ** (k - 1)
               for k in range(1, int(anzianita) + 1))


PP = ("it-pianificazione", "proiezione-pensione.xlsx")
VARIANTI_PP = {"ral150k": {("Input", "B10"): 150_000, ("Input", "B12"): 0.0},
               "ral150k_g": {("Input", "B10"): 150_000, ("Input", "B12"): 0.015},
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
    var = _varianti(*PP, VARIANTI_PP)
    for nome, wb in (("default", base), ("ral150k", var["ral150k"]), ("ral150k_g", var["ral150k_g"])):
        i, p = wb["Input"], wb["Pubblica"]
        massimale = _per_etichetta(i, "Massimale contributivo")
        n = int(i["B6"].value - i["B5"].value)
        # REGRESSIONE (revisione T5): E5 applicava il massimale alla RAL di oggi e poi lo
        # deflazionava con la RAL, e rivalutava anche il contributo dell'anno scorso
        assert not i["B14"].value, f"{nome}: la variante deve usare la stima del montante"
        stima = _montante_stimato(i["B10"].value, i["B12"].value, i["B16"].value, i["B11"].value,
                                  massimale, i["B13"].value)
        assert abs(p["E5"].value - stima) <= 1e-6 * stima, \
            f"{nome}: Pubblica!E5 = {p['E5'].value:,.2f}, stima anno per anno col massimale = {stima:,.2f}"
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
    # segno) e righe crescita RAL / PIL / rendimento decorative. Anche sopra il massimale
    # (revisione T5): con i default il tetto di B11/D11 non scatta mai.
    from openpyxl import load_workbook
    base = load_workbook(xlsx_ricalcolati()[asset(*PP)], data_only=True)
    netto = _modulo_previdenza("netto-pensione.py")
    for nome, wb in (("default", base), ("ral150k", _varianti(*PP, VARIANTI_PP)["ral150k"])):
        s, i, p = wb["Scenari"], wb["Input"], wb["Pubblica"]
        for col in "BCD":
            assert abs(s[f"{col}18"].value - i["B39"].value) < 0.01, \
                f"{nome}: Scenari!{col}18 = {s[f'{col}18'].value:,.0f}: la spesa target va in euro di oggi ({i['B39'].value:,.0f})"
        for riga, (foglio, cella) in ((11, ("Pubblica", "B61")), (12, ("Pubblica", "B66")),
                                      (13, ("Complementare", "B58")), (14, ("Complementare", "B61")),
                                      (15, ("Complementare", "B62"))):
            assert abs(s[f"C{riga}"].value - wb[foglio][cella].value) < 0.01, \
                f"{nome}: Base Scenari!C{riga} ≠ {foglio}!{cella}"
        n = int(i["B6"].value - i["B5"].value)
        massimale = _per_etichetta(i, "Massimale contributivo")
        coeff = _coeff_excel(wb, i["B6"].value)
        for col in "BD":
            g, r, d, rend = (s[f"{col}{k}"].value for k in (5, 6, 8, 9))
            atteso = _pensione_contributiva(p["E5"].value, i["B10"].value, g, r, n, massimale, i["B13"].value,
                                            coeff * (1 - d) ** (n / 2))
            assert abs(s[f"{col}11"].value - atteso) <= 1e-6 * atteso, \
                f"{nome}: Scenari!{col}11 = {s[f'{col}11'].value:,.0f}, ricalcolo con i parametri di colonna = {atteso:,.0f}"
            assert abs(s[f"{col}12"].value - netto.netto_pensionato(atteso, 0.02, 0.0)[0]) < 0.01, \
                f"{nome}: Scenari!{col}12"
            fondo = _fondo_scenario(wb, g, rend, n)
            assert abs(s[f"{col}13"].value - fondo) <= 1e-6 * fondo, \
                f"{nome}: Scenari!{col}13 = {s[f'{col}13'].value:,.0f}, fondo col rendimento di colonna = {fondo:,.0f}"
        assert s["B11"].value < s["C11"].value < s["D11"].value and s["B13"].value < s["C13"].value < s["D13"].value, nome


def _fondo_scenario(wb, g, rend, n):
    """Montante del fondo (foglio Complementare) ricalcolato con crescita RAL g e rendimento rend."""
    i = wb["Input"]
    m = i["B22"].value + i["B25"].value
    for t in range(n):
        ral = i["B10"].value * (1 + g) ** t
        m = m * (1 + rend) + ral * 0.0691 * i["B21"].value + min(i["B26"].value, 5300) + ral * i["B27"].value
    return m


def _estratto_inps_xml(retrib_per_anno, path):
    """Estratto conto INPS sintetico: una riga di 52 settimane per anno."""
    righe = "".join(
        f"<RigaContributi><PeriodoDal><Giorno>01</Giorno><Mese>01</Mese><Anno>{a}</Anno></PeriodoDal>"
        f"<PeriodoAl><Giorno>31</Giorno><Mese>12</Mese><Anno>{a}</Anno></PeriodoAl>"
        f"<TipoContribuzione>Lavoro dipendente</TipoContribuzione><ContributiUtiliCalcolo>52</ContributiUtiliCalcolo>"
        f"<RetribuzioneEuro>{r}</RetribuzioneEuro><Descrizione>AZIENDA TEST SRL</Descrizione></RigaContributi>"
        for a, r in sorted(retrib_per_anno.items()))
    with open(path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?><EstrattoConto><DatiAnagrafici><Cognome>ROSSI</Cognome>'
                '<Nome>MARIO</Nome></DatiAnagrafici><RegimeGenerale><Contributi>' + righe +
                '</Contributi></RegimeGenerale></EstrattoConto>')


@test("importa-previdenza: tassi di capitalizzazione ufficiali 1996-2025, solo contributi dal 1996, avvisi veri")
def t_tassi_capitalizzazione():
    # REGRESSIONE F062: tabella limitata al 2021-2025, default 1,01 per gli anni precedenti
    # (sottostima ~8% per chi ha iniziato a fine anni '90) e anche per l'anno in corso, non pubblicato.
    # Revisione T5: i contributi prima del 1996 entravano nel montante e si rivalutavano (×2,31)
    # mentre l'avviso diceva il contrario, e l'avviso perdeva il primo anno (carriera dal 1995: nessuno).
    ufficiali = {  # nota ISTAT 16/10/2025 (lavoro.gov.it); 2014 e 2021 a 1, 2022 con recupero (DL 65/2015 art. 5)
        1996: 1.062054,
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
    for anno in range(1998, 2027):  # il 2026 non ha ancora un tasso: il montante al 31/12/2025 resta lì
        atteso = atteso * ufficiali.get(anno, 1.0) + retrib.get(anno, 0.0) * 0.33
    assert abs(montante - atteso) < 0.01, f"montante {montante:,.2f} ≠ {atteso:,.2f}"
    assert mancanti == [2026], f"anni senza tasso pubblicato: {mancanti}"
    # posizione mista: le retribuzioni prima del 1996 non entrano nel montante contributivo
    # (L. 335/1995 art. 1 c. 12-13: quota retributiva), né come nominali né rivalutate
    dal96 = {a: 30_000.0 for a in range(1996, 2026)}
    solo96, nom96, _ = m.ricostruisci_montante(dal96, 2026)
    for prima in ({1995: 25_000.0}, {1994: 30_000.0}, {a: 20_000.0 for a in range(1990, 1996)}):
        misto, nom, _ = m.ricostruisci_montante({**prima, **dal96}, 2026)
        assert abs(misto - solo96) < 0.01 and abs(nom - nom96) < 0.01, \
            f"{sorted(prima)}: montante {misto:,.2f} ≠ {solo96:,.2f} dei soli contributi dal 1996"
    rc, out = run_script(asset("it-pianificazione", "importa-previdenza.py"),
                         os.path.join(FIXTURES, "estratto-inps-test.xml"))
    assert rc == 0, out[-300:]
    assert "sono i primi anni" not in out and "non ancora pubblicat" in out, out[-600:]
    assert "prima del 1996" not in out, "carriera dal 2023: nessun avviso sugli anni prima del 1996"
    tmp = tempfile.mkdtemp()
    try:
        for inizio, intervallo in ((1995, "(1995,"), (1990, "(1990-1995,")):
            xml = os.path.join(tmp, f"da{inizio}.xml")
            _estratto_inps_xml({a: 30_000 for a in range(inizio, 2026)}, xml)
            rc, out = run_script(asset("it-pianificazione", "importa-previdenza.py"), xml)
            assert rc == 0, out[-300:]
            avviso = next((r for r in out.splitlines() if "prima del 1996" in r), "")
            assert intervallo in avviso and "retributiv" in avviso, f"carriera dal {inizio}: avviso «{avviso.strip()}»"
            assert "non sono rivalutati" not in out, f"carriera dal {inizio}: avviso falso sulla rivalutazione"
            atteso = m.ricostruisci_montante({a: 30_000.0 for a in range(1996, 2026)},
                                             __import__("datetime").date.today().year)[0]
            assert abs(euro(out, "MONTANTE CONTRIBUTIVO RICOSTRUITO") - atteso) <= 1, \
                f"carriera dal {inizio}: il montante stampato deve contare solo i contributi dal 1996"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


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
    # RAL 150.000: niente contributi oltre il massimale di €122.295 (revisione T5, mutante «base = ral»)
    _, contr, _, _ = netto.netto_lavoratore(150_000, netto.ALIQ_CONTRIBUTI_DIP, 0.0, 0.0)
    assert abs(contr - (122_295 * 0.0919 + (122_295 - 56_224) * 0.01)) < 0.01, f"RAL 150k: contributi {contr:,.2f}"
    # fasce del c. 4: 7,1% fino a 8.500 di reddito, 5,3% fino a 15.000 (limiti inclusi)
    for ral, quota in ((9_000, 0.071), (12_000, 0.053)):
        n, _, irpef, _ = netto.netto_lavoratore(ral, netto.ALIQ_CONTRIBUTI_DIP, 0.0, 0.0)
        r = ral * (1 - 0.0919)
        assert abs(n - (r - irpef + r * quota)) < 0.01, f"RAL {ral}: netto {n:,.2f}, somma esente al {quota:.1%} attesa"
    assert netto.netto_lavoratore(9_000, netto.ALIQ_CONTRIBUTI_DIP, 0.0, 0.0)[2] == 0, "RAL 9k: IRPEF dovuta"
    for r, quota in ((8_500, 0.071), (15_000, 0.053), (20_000, 0.048)):
        assert abs(netto.cuneo_l207(r)[0] - r * quota) < 0.01, f"reddito {r}: «non superiore a» include il limite"


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


@test("previdenza: requisiti 2027-2028 completi nelle due reference, tassi storici veri, nessun dominio inesistente")
def t_requisiti_e_link_inps():
    # Revisione T5. Requisiti: Circ. INPS 28/2026, All. 2 (anticipata ordinaria 43a1m/42a1m dal 2028,
    # contributi dell'anticipata contributiva adeguati anche loro, finestra di 3 mesi).
    dip = open(os.path.join(SKILLS, "it-pianificazione", "references", "previdenza-obbligatoria.md"),
               encoding="utf-8").read()
    gs = open(os.path.join(SKILLS, "it-pianificazione-autonomi", "references", "previdenza-gestione-separata.md"),
              encoding="utf-8").read()
    for nome, testo in (("previdenza-obbligatoria.md", dip), ("previdenza-gestione-separata.md", gs)):
        for req in ("42 anni e 11 mesi", "43 anni e 1 mese", "42 anni e 1 mese", "20 anni e 1 mese", "20 anni e 3 mesi"):
            assert req in testo, f"{nome}: manca «{req}» tra i requisiti 2027-2028"
    assert not re.search(r"Dal 2027: 42 anni e 11 mesi", dip), "anticipata ordinaria: «dal 2027» copre anche il 2028"
    for req in ("71 anni e 3 mesi", "41 anni e 3 mesi"):
        assert req in dip, f"previdenza-obbligatoria.md: manca «{req}»"
    ponte = open(asset("it-pianificazione", "ponte-pensione.py"), encoding="utf-8").read()
    inizio = ponte.index('"""') + 3
    doc = " ".join(ponte[inizio:ponte.index('"""', inizio)].split())
    assert "20 anni e 1 mese" in doc and "20 anni e 3 mesi" in doc and re.search(r"(tre|3) mesi dopo", doc), \
        "ponte-pensione: anticipata contributiva senza i contributi adeguati o senza la finestra di 3 mesi"
    # tassi nominali di rivalutazione: medie dalla tabella ufficiale dello script, non «1,5-2,5%»
    tassi = carica_modulo(asset("it-pianificazione", "importa-previdenza.py")).TASSI_CAPITALIZZAZIONE
    def media(da, a):
        prodotto = 1.0
        for anno in range(da, a + 1):
            prodotto *= tassi[anno]
        return prodotto ** (1 / (a - da + 1)) - 1
    for da in (1996, 2006):
        cifra = f"~{media(da, 2025) * 100:.1f}%".replace(".", ",")
        assert f"{cifra} annuo nel {da}-2025" in dip, f"previdenza-obbligatoria.md: media {da}-2025 attesa {cifra}"
    assert "1,5-2,5% annuo negli ultimi decenni" not in dip
    # mypensione.it non è un dominio INPS: le credenziali SPID vanno solo sul portale INPS
    for rel, testo in _file_testo(SKILLS, os.path.join(ROOT, "commands")):
        assert "mypensione" not in testo.lower(), f"{rel}: rimando a «mypensione», dominio che non è dell'INPS"
        assert "PIN/CIE/SPID" not in testo, f"{rel}: il PIN INPS dei cittadini non esiste più dal 2021"
    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    assert "mypensione" not in readme.lower(), "README: rimando a «mypensione»"
    # cuneo L. 207/2024: il c. 6 (ulteriore detrazione) vale fino al 2026, poi il TUIR 2027
    netto = open(asset("it-pianificazione", "netto-pensione.py"), encoding="utf-8").read()
    netto = " ".join(netto.split())
    assert re.search(r"c\. 6 vale fino al 2026", netto) and "D.Lgs. 117/2026" in netto, \
        "netto-pensione: il c. 6 della L. 207/2024 senza la doppia citazione dal 2027"


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
                         os.path.join(FIXTURES, "estratto-broker-test.csv"), "--json", "-")
    assert rc == 0 and json.loads(out)["analisi"]["plus_latenti_compensabili"] == 300, "importatore broker: " + out[-200:]


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


IMPORTATORE = os.path.join(TAX, "assets", "importa-estratto-broker.py")


def _importa(*args):
    """Lancia l'importatore con --json - e ritorna (rc, dati JSON o None, output grezzo)."""
    rc, out = run_script(IMPORTATORE, *args, "--json", "-")
    try:
        return rc, json.loads(out), out
    except ValueError:
        return rc, None, out


@test("T2 importatore: sugli esempi distribuiti nessuna plus «a imposta zero» (ETF = reddito di capitale)")
def t_t2_esempi():
    # REGRESSIONE F001: con il default «diverso» la plus di €1.650 su iShares Core MSCI World
    # risultava compensabile; la minus 2021 scaduta finiva nello zainetto.
    es = lambda f: os.path.join(TAX, "assets", f)
    rc, d, out = _importa(es("esempio-estratto.csv"), es("esempio-zainetto.csv"), "--anno", "2027")
    assert rc == 0 and d, out[-400:]
    a = d["analisi"]
    assert a["plus_latenti_compensabili"] == 0, a
    assert a["zainetto_totale"] == 800, a                 # solo la minus 2023, valida fino al 31/12/2027
    assert a["zainetto_scaduto"] == 1200, a               # la 2022 è scaduta il 31/12/2026
    assert a["plus_realizzabili_a_costo_zero"] == 0, a
    ishares = next(p for p in d["posizioni"] if p["isin"] == "IE00B4L5Y983")
    assert ishares["categoria_fiscale"] == "reddito_capitale" and ishares["plus_minus"] == 1650, ishares
    btp = next(p for p in d["posizioni"] if p["isin"] == "IT0005454241")
    assert btp["aliquota"] == 12.5, btp
    rc, d, out = _importa(es("esempio-estratto.csv"), es("esempio-zainetto.csv"), "--anno", "2026")
    assert rc == 0 and d["analisi"]["zainetto_totale"] == 2000 and d["analisi"]["zainetto_in_scadenza"] == 1200, out[-400:]
    assert all(z["stato"] != "scaduta" for z in d["zainetto"]), "l'esempio distribuito non deve contenere minus già scadute"


@test("T2 importatore: casi limite (costo zero, migliaia italiane, azione DE, ETF USA, minus scaduta, 12,5/26)")
def t_t2_casi_limite():
    # REGRESSIONE F034/F001/F003: costo zero mandava in crash, «1.000» diventava 1,0 e
    # «1.234.567» spariva, gli ETF USA risultavano compensabili, il 12,5% era sommato nominale.
    rc, d, out = _importa(os.path.join(FIXTURES, "estratto-casi-limite.csv"),
                          os.path.join(FIXTURES, "zainetto-casi-limite.csv"), "--anno", "2026")
    assert rc == 0 and d, out[-400:]
    pos = {p["isin"]: p for p in d["posizioni"]}
    sap = pos["DE0007164600"]
    assert sap["categoria_fiscale"] == "reddito_diverso", sap          # azione tedesca, non un ETF
    assert sap["costo"] == 120_000 and sap["valore"] == 150_000, sap   # «1.000» e «150.000,00»
    assert pos["IE00BK5BQT80"]["valore"] == 1_234_567, pos["IE00BK5BQT80"]
    assert pos["US9229083632"]["categoria_fiscale"] == "reddito_capitale_irpef", pos["US9229083632"]
    assert pos["JE00B1VS3770"]["categoria_fiscale"] == "reddito_diverso", "ETC: reddito diverso"
    assert pos["IT0004965148"]["categoria_fiscale"] == "da_classificare", "nessun indizio → da classificare"
    assert pos["IT0005611659"]["categoria_fiscale"] == "da_classificare", "BOT: la plus è scarto di emissione"
    assert pos["IT0005436693"]["aliquota"] == 12.5 and pos["IT0005436693"]["categoria_fiscale"] == "reddito_diverso"
    gratuite = pos["IT0005218380"]
    assert gratuite["costo"] == 0 and gratuite["pct"] is None and gratuite["plus_minus"] == 250, gratuite
    assert "XS0000000000" not in pos and any("Riga senza prezzi" in av for av in d["avvisi"]), d["avvisi"]
    a = d["analisi"]
    assert a["plus_latenti_compensabili"] == 30_650, a                 # SAP + BTP + gratuite + ETC
    assert a["plus_irpef"] == 1_000 and a["plus_da_classificare"] == 125, a
    assert a["zainetto_totale"] == 3_000 and a["zainetto_scaduto"] == 1_000, a
    k = 12.5 / 26
    zeq = 2_000 + 1_000 * k
    assert abs(a["zainetto_26_equivalente"] - zeq) < 0.01, a
    # minus 26% assorbe 2,08 € di plus al 12,5% per euro: si coprono prima i €100 di BTP
    assert abs(a["plus_realizzabili_a_costo_zero"] - (100 + zeq - 100 * k)) < 0.02, a
    assert abs(a["imposta_risparmiabile"] - 0.26 * zeq) < 0.02, a
    rc, testo = run_script(IMPORTATORE, os.path.join(FIXTURES, "estratto-casi-limite.csv"),
                           os.path.join(FIXTURES, "zainetto-casi-limite.csv"), "--anno", "2026")
    assert rc == 0 and "Traceback" not in testo, testo[-400:]
    for atteso in ("31/12/2026", "scaduta", "da classificare", "non costituisce consulenza"):
        assert atteso in testo, f"report senza «{atteso}»"


@test("T2 importatore: zainetto per broker, formato inglese, --json su file completo, errori leggibili")
def t_t2_broker_json_errori():
    # REGRESSIONE F034/F001: la compensazione non attraversa i broker; il JSON era troncato
    # a 1.200 caratteri; file mancanti davano un traceback.
    rc, d, out = _importa(os.path.join(FIXTURES, "estratto-multibroker.csv"),
                          os.path.join(FIXTURES, "zainetto-multibroker.csv"), "--anno", "2026")
    assert rc == 0 and d, out[-400:]
    a = d["analisi"]
    assert a["plus_latenti_compensabili"] == 1_700, a                 # «12.40» letto all'inglese
    assert a["plus_realizzabili_a_costo_zero"] == 800, a               # 300 su Directa + 500 su Fineco
    assert set(a["per_broker"]) == {"Directa", "Fineco"}, a
    tmp = tempfile.mkdtemp()
    try:
        dest = os.path.join(tmp, "estratto.json")
        rc, out = run_script(IMPORTATORE, os.path.join(TAX, "assets", "esempio-estratto.csv"),
                             "--broker", "Fineco", "--anno", "2026", "--json", dest)
        assert rc == 0, out[-400:]
        dati = json.load(open(dest, encoding="utf-8"))
        assert len(dati["posizioni"]) == 4 and all(p["broker"] == "Fineco" for p in dati["posizioni"]), dati
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    rc, out = run_script(IMPORTATORE, os.path.join(FIXTURES, "non-esiste.csv"))
    assert rc == 2 and "Traceback" not in out and "non trovato" in out, out[-300:]
    rc, out = run_script(IMPORTATORE, os.path.join(FIXTURES, "estratto-multibroker.csv"),
                         os.path.join(TAX, "assets", "esempio-zainetto.csv"))
    assert rc == 2 and "Traceback" not in out and "broker" in out, out[-300:]


def _fx(nome):
    return os.path.join(FIXTURES, nome)


@test("T2 importatore: 12,5% a Stati white list, enti territoriali e sovranazionali; ETC e nomi di emittenti senza default rischiosi")
def t_t2_pubblici_etc():
    # REGRESSIONE revisione T2: Bund, Treasury e BEI uscivano al 26% senza avviso (art. 6 c. 1
    # D.Lgs. 461/97 → art. 306 c. 1 TU 2027); «WisdomTree Physical Gold» (JE) finiva a IRPEF
    # con quadro RL; «Vanguard … Inc» e «ISHARES III PLC» erano azioni con la plus compensabile.
    rc, d, out = _importa(_fx("estratto-pubblici-etc.csv"), _fx("zainetto-un-broker.csv"), "--anno", "2026")
    assert rc == 0 and d, out[-400:]
    pos = {p["descrizione"]: p for p in d["posizioni"]}
    for nome in ("Bund 0% 15/02/2032", "BEI 1,5% 15/11/2030", "US Treasury 4,5% 15/11/2033",
                 "Comune di Roma 5,345% 2048", "Land Berlin 1% 2030", "BTP 2,5% 01/12/2032"):
        assert pos[nome]["categoria_fiscale"] == "reddito_diverso" and pos[nome]["aliquota"] == 12.5, pos[nome]
    enel = pos["Enel Finance 3% 2030"]
    assert enel["categoria_fiscale"] == "reddito_diverso" and enel["aliquota"] == 26, enel
    avvisi_aliquota = [av for av in d["avvisi"] if "12,5%" in av]
    assert any("Enel Finance" in av for av in avvisi_aliquota), d["avvisi"]
    assert not any(re.search(r"Bund|BEI|Treasury|Comune|Land Berlin|BTP", av) for av in avvisi_aliquota), avvisi_aliquota
    for nome in ("WisdomTree Physical Gold", "iShares Physical Gold"):
        assert pos[nome]["categoria_fiscale"] == "reddito_diverso", pos[nome]
    assert pos["Vanguard FTSE All-World High Dividend Yield Inc"]["categoria_fiscale"] == "reddito_capitale"
    for nome in ("ISHARES III PLC", "WisdomTree Brent Crude Oil", "Fondo Esempio non armonizzato",
                 "Fondo Immobiliare Esempio", "HSBC MSCI World Inc", "SPDR S&P 500 Trust"):
        assert pos[nome]["categoria_fiscale"] == "da_classificare", pos[nome]
    assert not any(p["categoria_fiscale"] == "reddito_capitale_irpef" for p in d["posizioni"])
    a = d["analisi"]
    assert a["plus_latenti_compensabili"] == 1_050 and a["plus_non_compensabili"] == 100, a
    assert a["plus_da_classificare"] == 270 and a["plus_irpef"] == 0, a
    # 1.000 di minus al 26% coprono prima i 550 al 12,5% (264,42 in 26%-equivalente), poi i 500 al 26%
    assert a["plus_realizzabili_a_costo_zero"] == 1_050, a
    assert abs(a["imposta_risparmiabile"] - (550 * 0.125 + 500 * 0.26)) < 0.02, a
    assert set(a["per_broker"]) == {"Fineco"}, a
    # Revisione di T2: nomi che somigliano a emittenti pubblici, ETC o indici senza esserlo
    rc, d, out = _importa(_fx("estratto-falsi-positivi.csv"), "--anno", "2026")
    assert rc == 0 and d, out[-400:]
    pos = {p["descrizione"]: p for p in d["posizioni"]}
    for nome in ("UBS Bloomberg US Treasury Bond 1-10", "JPM BetaBuilders US Treasury Bond 0-1 yr",
                 "OATLY GROUP AB ADR", "ETFS Brent Crude", "Bundesrepublik Deutschland"):
        assert pos[nome]["categoria_fiscale"] == "da_classificare", pos[nome]
    for nome in ("BUNDESIMMOBILIENGESELLSCHAFT 3,375% 2030", "OESTERREICHISCHE BUNDESBAHNEN 3% 2033",
                 "OATLY GROUP 9,25% 2028"):
        assert pos[nome]["categoria_fiscale"] == "reddito_diverso" and pos[nome]["aliquota"] == 26, pos[nome]
    for nome in ("ETFS Physical Gold", "MSCI Inc", "S&P Global Inc", "World Kinect Corp"):
        assert pos[nome]["categoria_fiscale"] == "reddito_diverso", pos[nome]
    assert pos["Xtrackers FTSE Developed Europe Real Estate UCITS ETF"]["categoria_fiscale"] == "reddito_capitale"
    assert not any(p["aliquota"] == 12.5 or p["categoria_fiscale"] == "reddito_capitale_irpef" for p in d["posizioni"])


@test("T2 importatore: zainetto per anno di scadenza, residuo accanto al lordo, righe anomale")
def t_t2_zainetto_colonne():
    # REGRESSIONE revisione T2: «Anno di scadenza» era letto come anno di realizzo (+4 anni);
    # con «Minusvalenza» e «Residuo» vinceva il lordo; «-» nell'aliquota fermava tutto l'import.
    estratto = _fx("estratto-migliaia-it.csv")
    rc, d, out = _importa(estratto, _fx("zainetto-scadenza.csv"), "--anno", "2026")
    assert rc == 0 and d, out[-400:]
    z = sorted(d["zainetto"], key=lambda r: r["anno"])
    assert [r["anno"] for r in z] == [2022, 2023], z
    assert z[0]["scade_il"] == "31/12/2026" and z[0]["stato"] == "in_scadenza", z
    assert d["analisi"]["zainetto_in_scadenza"] == 1_000 and d["analisi"]["zainetto_totale"] == 1_800, d["analisi"]
    assert any("scadenza" in av for av in d["avvisi"]), d["avvisi"]
    rc, testo = run_script(IMPORTATORE, estratto, _fx("zainetto-scadenza.csv"), "--anno", "2026")
    assert rc == 0 and "Priorità" in testo, testo[-400:]
    # lordo 5.000, utilizzato 1.000 e residuo 500: vale il residuo, non lordo − utilizzato
    for nome in ("zainetto-lordo-residuo.csv", "zainetto-plurale.csv", "zainetto-utilizzato.csv",
                 "zainetto-compensabili.csv"):
        rc, d, out = _importa(estratto, _fx(nome), "--anno", "2026")
        assert rc == 0 and d, f"{nome}: {out[-300:]}"
        assert d["analisi"]["zainetto_totale"] == 500, f"{nome}: {d['analisi']}"
        if nome != "zainetto-plurale.csv":
            assert any("residu" in av.lower() for av in d["avvisi"]), f"{nome}: {d['avvisi']}"
    rc, d, out = _importa(estratto, _fx("zainetto-esercizio-scadenza.csv"), "--anno", "2026")
    assert rc == 0 and d["zainetto"][0]["anno"] == 2022 and d["zainetto"][0]["stato"] == "in_scadenza", out[-300:]
    # CSV con la virgola come delimitatore e importi interi all'italiana: «1.500» sono millecinquecento
    rc, d, out = _importa(estratto, _fx("zainetto-virgola-interi.csv"), "--anno", "2026")
    assert rc == 0 and d["analisi"]["zainetto_totale"] == 3_500, out[-300:]
    assert any(av.startswith("zainetto: formato numeri") for av in d["avvisi"]), d["avvisi"]
    rc, d, out = _importa(estratto, _fx("zainetto-anomalie.csv"), "--anno", "2026")
    assert rc == 0 and d, out[-400:]
    assert d["analisi"]["zainetto_totale"] == 1_000, d["analisi"]          # la riga senza anno resta fuori
    assert [r["stato"] for r in d["zainetto"]].count("anno_mancante") == 1, d["zainetto"]
    assert any("riga 3" in av and "aliquota" in av for av in d["avvisi"]), d["avvisi"]


@test("T2 importatore: numeri senza indizi di formato, colonna tipo fiscale, broker unico, errori di input")
def t_t2_numeri_colonne():
    # REGRESSIONE revisione T2: «1,000» in un CSV con la virgola come delimitatore diventava 1;
    # «Redditi diversi (capital gain)» diventava reddito di capitale; «Natura strumento» era
    # scambiata per il tipo fiscale; errori su aliquota e cartelle senza file né riga.
    for nome in ("estratto-migliaia-it.csv", "estratto-migliaia-en.csv"):
        rc, d, out = _importa(_fx(nome))
        assert rc == 0 and d, f"{nome}: {out[-300:]}"
        sap = d["posizioni"][0]
        assert sap["costo"] == 120_000 and sap["valore"] == 150_000, f"{nome}: {sap}"
        assert any("formato numeri" in av for av in d["avvisi"]), f"{nome}: {d['avvisi']}"
    rc, d, out = _importa(_fx("estratto-tipo-fiscale.csv"))
    assert rc == 0 and d, out[-400:]
    pos = {p["isin"]: p for p in d["posizioni"]}
    assert pos["IE00B4L5Y983"]["categoria_fiscale"] == "reddito_capitale_irpef", pos["IE00B4L5Y983"]
    assert pos["IE00B4L5Y983"]["costo"] == 10_000 and pos["IE00B4L5Y983"]["valore"] == 12_000, pos["IE00B4L5Y983"]
    assert pos["US0378331005"]["categoria_fiscale"] == "reddito_diverso", pos["US0378331005"]
    assert pos["IE00B5BMR087"]["categoria_fiscale"] == "reddito_capitale", pos["IE00B5BMR087"]
    assert any("boh" in av for av in d["avvisi"]), d["avvisi"]
    rc, d, out = _importa(_fx("estratto-migliaia-it.csv"), _fx("zainetto-un-broker.csv"), "--anno", "2026")
    assert rc == 0 and d["analisi"]["plus_realizzabili_a_costo_zero"] == 1_000, out[-400:]
    rc, out = run_script(IMPORTATORE, _fx("estratto-migliaia-it.csv"), _fx("zainetto-multibroker.csv"))
    assert rc == 2 and "Traceback" not in out and "broker" in out, out[-300:]
    tmp = tempfile.mkdtemp()
    try:
        natura = os.path.join(tmp, "natura.csv")
        with open(natura, "w", encoding="utf-8") as f:
            f.write("ISIN;Descrizione;Natura strumento;Quantità;Prezzo medio di carico;Controvalore\n"
                    "DE0007164600;SAP SE;Azione;10;100,00;1.500,00\n")
        rc, d, out = _importa(natura)
        assert rc == 0 and d["posizioni"][0]["categoria_fiscale"] == "reddito_diverso", out[-300:]
        assert d["posizioni"][0]["fonte_categoria"] == "descrizione", d["posizioni"][0]
        assert not any("tipo fiscale" in av for av in d["avvisi"]), d["avvisi"]
        ambiguo = os.path.join(tmp, "ambiguo.csv")
        with open(ambiguo, "w", encoding="utf-8") as f:
            f.write("Anno realizzo;Importo;Ammontare;Aliquota\n2024;5.000,00;500,00;26%\n")
        rc, out = run_script(IMPORTATORE, _fx("estratto-migliaia-it.csv"), ambiguo)
        assert rc == 2 and "Traceback" not in out and "ambigu" in out, out[-300:]
        vuota = os.path.join(tmp, "vuota.csv")
        with open(vuota, "w", encoding="utf-8") as f:
            f.write("Anno realizzo;Minusvalenza residua;Aliquota\n2024;1.000,00;\n")
        rc, d, out = _importa(_fx("estratto-migliaia-it.csv"), vuota)
        assert rc == 0 and any("riga 2" in av and "aliquota" in av for av in d["avvisi"]), out[-300:]
        zain = os.path.join(tmp, "zainetto.csv")
        with open(zain, "w", encoding="utf-8") as f:
            f.write("Anno realizzo;Minusvalenza residua;Aliquota\n2024;1.000,00;30%\n")
        rc, out = run_script(IMPORTATORE, _fx("estratto-migliaia-it.csv"), zain)
        assert rc == 2 and "Traceback" not in out and "zainetto.csv" in out and "riga 2" in out, out[-300:]
        rc, out = run_script(IMPORTATORE, tmp)
        assert rc == 2 and "Traceback" not in out, out[-300:]
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
