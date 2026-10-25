# Capitale umano, lente diagnostica: piano di implementazione

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aggiungere a `it-pianificazione-obiettivi` lo script `capitale-umano.py`, che mette il portafoglio finanziario dentro la ricchezza totale (finanziario + capitale umano + capitale pensionistico) e ne dà cinque diagnosi, senza toccare i target.

**Architecture:** Un solo script con funzioni pure e importabili (valutazione, bilancio, equivalenza, proiezione, sovrapposizione, sensibilità) più un `main()` che usa l'interfaccia comune `motore_bootstrap.cli`. I profili stanno in un CSV accanto allo script; i dati della persona in un JSON `--dati`; la composizione settoriale in un CSV `--composizione`. Tutto offline.

**Tech Stack:** Python ≥ 3.11, numpy; runner `tests/run_tests.py` (decoratore `@test`, nessun pytest).

**Spec:** `docs/sviluppo/specs/2026-10-25-capitale-umano-design.md` (le sezioni citate sotto come «spec §N»).

## Global Constraints

- Python 3.11 o successivo; dipendenze solo numpy (già richiesta). Nessuna chiamata di rete (spec D10).
- Codici d'uscita 0 riuscito, 1 dati incoerenti con `ERRORE:` su stderr (via `errore()`), 2 riga di comando errata (argparse).
- Numeri in stampa solo via `numero()`, `euro()`, `pct()` di `motore_bootstrap`: nessun format spec anglosassone (`{x:,.0f}`, `{x:.1%}`, `{x:.1f}`), lo verifica `t_formati_italiani`.
- `open()` sempre con `encoding=` esplicito; UTF-8 su stdout (lo fa `cli()`).
- Euro di oggi, termini reali, redditi netti (spec §3).
- Default delle costanti: `R_F = 0.01`, `NU_PENSIONE = 0.0075`, `ETA_FINE = 90`, `REND_AZ_REALE = 0.03`, `REND_OBB_REALE = 0.005`, `SIGMA_AZ = 0.18`, `N_SIM = 2000`, `SEED = 42`, `SOGLIA_SOVRAPPESO = 2.0`.
- Precedenza dei valori: `--set` > `--dati` > `--from` > costanti dello script.
- Ogni etichetta della riga di equivalenza dice: «calcolo, non target: non modifica l'allocazione degli obiettivi né quella di it-rebalance».
- Lingua: italiano, nello stile delle skill esistenti; ogni commit termina con le righe di attribuzione della sessione.
- I test nuovi si chiamano `T15 capitale umano: …` e stanno in una sezione `# ═══ T15: capitale umano ═══` di `tests/run_tests.py`, prima del blocco «freshness · json · guardia».

## Review Focus

1. **Persona già in pensione** (`eta ≥ eta_pensione` con `netto_annuo` e `tfr_annuo` a 0; con un reddito > 0 la validazione la respinge, spec §5): HC = 0, proiezione che parte dalla pensione, `eta_sorpasso` null, nessuna divisione per zero. Test nel Task 3.
2. **Portafoglio finanziario vuoto** (`posizioni` vuote e `liquidita` 0) con l'equivalenza richiesta: niente divisione per zero; `equivalenza` con `x` null e messaggio «nessun portafoglio su cui calcolarla»; esposizione finanziaria stampata «n/d» se F = 0. Test nel Task 2.
3. **CSV di composizione salvato da Excel italiano**: BOM, `;`, pesi in percento con la virgola («23,4»). Va letto senza errori. Test nel Task 4.
4. **Glide path più corto della proiezione** (`--from` del JSON di `glidepath-obiettivi.py` con meno anni dell'orizzonte): dopo l'ultimo anno si tiene l'ultima quota, e lo si dice. Test nel Task 3.
5. **`asset_class` diversa da azionario/obbligazionario/monetario** (per esempio `oro`): contata come non azionaria con un avviso che la nomina. Test nel Task 2.

---

### Task 1: Profili e funzioni di valutazione

**Files:**
- Create: `skills/it-pianificazione-obiettivi/assets/profili-capitale-umano.csv`
- Create: `skills/it-pianificazione-obiettivi/assets/capitale-umano.py` (costanti in testa, funzioni di questo task, `main()` minimo che stampa «in costruzione» e un «€»: lo completa il Task 2)
- Test: `tests/run_tests.py`

**Interfaces:**
- Produces:
  - `carica_profili(path: str | None = None) -> dict[str, dict]`: chiave il nome del profilo; valori float per `quota_azionaria_hc, nu, rho, sigma_h, p_u, durata_anni, sostituzione_naspi`, str per `settore_default` (None se vuoto), `fonte`, `natura`. Default `path`: il CSV accanto allo script (via `__file__`). Virgola decimale accettata.
  - `profilo_effettivo(persona: dict, profili: dict) -> dict`: copia del profilo con `persona["override"]` applicato; profilo sconosciuto → `errore()` con l'elenco dei profili.
  - `frazione_lavorata(p_u: float, durata_anni: float, sostituzione_naspi: float) -> float` = `1 − p_u × durata_anni × (1 − sostituzione_naspi)`.
  - `valore_capitale_umano(reddito0: float, g: float, anni: int, r_f: float, nu: float, frazione: float) -> float` = Σ_{t=1..anni} reddito0 × (1+g)^t × frazione / (1+r_f+nu)^t; 0 se `anni ≤ 0`.
  - `valore_pensione(pensione: float, anni_a_pensione: int, anni_a_fine: int, r_f: float, nu_pens: float) -> float` = Σ_{t=max(anni_a_pensione,0)+1..anni_a_fine} pensione / (1+r_f+nu_pens)^t.
  - `quota_azionaria_effettiva(s: float, quota_azioni_datore: float) -> float` = `q + (1 − q) × s`.
  - Costante `SETTORI_GICS`: tupla degli 11 nomi GICS inglesi (`Information Technology`, `Financials`, `Health Care`, `Consumer Discretionary`, `Communication Services`, `Industrials`, `Consumer Staples`, `Energy`, `Materials`, `Utilities`, `Real Estate`).

- [ ] **Step 1: Scrivi i test che falliscono**

```python
CU = ("it-pianificazione-obiettivi", "capitale-umano.py")

@test("T15 capitale umano: valori chiusi della valutazione")
def t_cu_valutazione():
    m = carica_modulo(asset(*CU))
    # rendita: g = 0, frazione 1, ν = 0 → formula chiusa
    assert abs(m.valore_capitale_umano(32000, 0, 32, 0.01, 0, 1) - 32000 * (1 - 1.01 ** -32) / 0.01) < 0.01
    assert m.valore_capitale_umano(32000, 0.01, 0, 0.01, 0.03, 1) == 0
    assert abs(m.frazione_lavorata(0.08, 0.5, 0.6) - 0.984) < 1e-12
    assert abs(m.valore_pensione(18000, 32, 55, 0.01, 0.0075) - 194248.56) < 0.01
    assert m.quota_azionaria_effettiva(0.3, 1) == 1 and abs(m.quota_azionaria_effettiva(0.3, 0.5) - 0.65) < 1e-12
    # invarianti: HC decresce con ν e con p_u, cresce con g
    base = m.valore_capitale_umano(35000, 0.01, 32, 0.01, 0.03, 0.984)
    assert abs(base - 705036.01) < 0.01
    assert m.valore_capitale_umano(35000, 0.01, 32, 0.01, 0.04, 0.984) < base
    assert m.valore_capitale_umano(35000, 0.01, 32, 0.01, 0.03, m.frazione_lavorata(0.16, 0.5, 0.6)) < base
    assert m.valore_capitale_umano(35000, 0.02, 32, 0.01, 0.03, 0.984) > base

@test("T15 capitale umano: profili con fonte, natura e valori plausibili")
def t_cu_profili():
    m = carica_modulo(asset(*CU))
    p = m.carica_profili()
    assert set(p) == {"pubblico", "privato_stabile", "privato_ciclico", "finanza", "autonomo", "imprenditore"}
    assert p["privato_ciclico"]["quota_azionaria_hc"] == 0.30 and p["privato_ciclico"]["nu"] == 0.03
    assert p["finanza"]["settore_default"] == "Financials"
    for nome, r in p.items():
        assert r["fonte"].strip() and r["natura"].strip(), nome
        assert 0 <= r["quota_azionaria_hc"] <= 1 and 0 <= r["nu"] <= 0.10 and -1 <= r["rho"] <= 1, nome
        assert 0 <= r["sigma_h"] <= 0.5 and 0 <= r["p_u"] <= 0.5 and 0 <= r["sostituzione_naspi"] <= 1, nome
        assert r["settore_default"] in (None, *m.SETTORI_GICS), nome
    e = m.profilo_effettivo({"profilo": "privato_ciclico", "override": {"p_u": 0.08}}, p)
    assert e["p_u"] == 0.08 and p["privato_ciclico"]["p_u"] == 0.05   # l'override non tocca la tabella
```

- [ ] **Step 2: Esegui e verifica che falliscano**

Run: `python tests/run_tests.py --only "T15 capitale umano"`
Expected: 2 test ❌ (file non trovato).

- [ ] **Step 3: Crea il CSV dei profili**

Valori esatti dalla tabella della spec §4 (sei righe, separatore `;`, virgola decimale, intestazione `profilo;quota_azionaria_hc;nu;rho;sigma_h;p_u;durata_anni;sostituzione_naspi;settore_default;fonte;natura`). `fonte` cita gli autori e l'anno della colonna «Ancoraggio»; `natura` campo per campo, per esempio `s:letteratura; nu:giudizio; rho:letteratura; sigma_h:letteratura; p_u:giudizio; naspi:da verificare`. Righe di commento in testa con `#` (data, rinvio a `references/capitale-umano.md`), saltate dal lettore.

- [ ] **Step 4: Implementa le funzioni dell'Interfaces block in `capitale-umano.py`**

Intestazione come gli altri script (docstring con scopo, uso, avvertenza «non è consulenza»), `from motore_bootstrap import cli, errore, numero, euro, pct, scrivi_json, carica_da_json`. Costanti dei Global Constraints più `ETA_PENSIONE = None`, `PENSIONE_NETTA = None`, `QUOTE_GLIDE = None`.

- [ ] **Step 5: Esegui i test**

Run: `python tests/run_tests.py --only "T15 capitale umano"`
Expected: 2 ✅.

- [ ] **Step 6: Commit**

```bash
git add skills/it-pianificazione-obiettivi/assets/profili-capitale-umano.csv skills/it-pianificazione-obiettivi/assets/capitale-umano.py tests/run_tests.py
git commit -m "feat: profili e valutazione del capitale umano (T15)"
```

---

### Task 2: Dati, bilancio, esposizione, equivalenza e CLI

**Files:**
- Create: `skills/it-pianificazione-obiettivi/assets/esempio-capitale-umano.json`
- Modify: `skills/it-pianificazione-obiettivi/assets/capitale-umano.py`
- Modify: `tests/run_tests.py` (`SCRIPT_CLI`: aggiungi `("it-pianificazione-obiettivi", "capitale-umano.py")`; in `t_cli_help` l'assert `len(tutti) == 14` diventa `== 15`)

**Interfaces:**
- Consumes: Task 1.
- Produces:
  - `leggi_dati(path: str) -> dict`: JSON validato (spec §5, «Controlli sui dati»); errori con `errore()`. `persone` al posto di `persona` → «un solo reddito per ora: usa "persona"».
  - `bilancio(dati: dict, profilo: dict, c: dict) -> dict` con chiavi `voci` (lista di `{"nome", "valore", "peso", "quota_azionaria"}` nell'ordine portafoglio, fondo pensione, TFR maturato, liquidità, capitale umano azionario, capitale umano obbligazionario, capitale pensionistico), `F`, `F_az`, `F_portafoglio`, `F_az_fondo`, `HC`, `HC_az`, `PP`, `W`, `esposizione_finanziaria` (None se F = 0), `esposizione_totale`, `altri_attivi`, `avvisi` (lista di stringhe). Le chiavi facoltative di `dati` (`liquidita`, `altri_attivi`, `fondo_pensione`, `tfr_maturato_azienda`, `risparmio_annuo`, `esposizione_totale_desiderata`, `persona.override`, `persona.contributo_datore_fp`, `persona.quota_reddito_azioni_datore`) valgono 0, vuote o None se assenti: `bilancio` si chiama anche su un dizionario non passato da `leggi_dati` (test di Ibbotson, Task 3). `c` è il dizionario delle costanti risolte: `R_F, NU_PENSIONE, ETA_FINE, ETA_PENSIONE, PENSIONE_NETTA`.
  - `equivalenza(T: float, b: dict) -> dict` con `x` (float o None), `limite` (`None`, `"min"`, `"max"`), `messaggio`; formula della spec §5.2, `x` limitato a [0, 1].
  - `main()`: `--dati FILE` (default l'esempio accanto allo script, dichiarato in stampa come «dati d'esempio»), `--composizione FILE` (usato dal Task 4), `--json`, `--set`, `--from` con la mappa `{"eta_pensionamento": ("ETA_PENSIONE", int), "netto_pensione_inps": "PENSIONE_NETTA", "portafoglio": "QUOTE_GLIDE"}`. Per la precedenza `--set` > `--dati`, i nomi passati a `--set` si ricavano da `args.set` e i campi di `--dati` non li sovrascrivono.

- [ ] **Step 1: Crea l'esempio**

`esempio-capitale-umano.json` = il JSON della spec §5, con `posizioni`: `[{"asset_class": "azionario", "valore": 60000, "strumento": "ETF MSCI World"}, {"asset_class": "obbligazionario", "valore": 20000, "strumento": "ETF obbligazionario euro"}]` e `pensione.netta_annua` 18000.

- [ ] **Step 2: Scrivi i test che falliscono**

```python
def _cu(*args, cwd=None):
    return run_script_split(asset(*CU), *args, cwd=cwd)

@test("T15 capitale umano: bilancio, esposizione ed equivalenza sull'esempio")
def t_cu_bilancio():
    import json as _json
    tmp = tempfile.mkdtemp()
    try:
        out_json = os.path.join(tmp, "cu.json")
        rc, so, se = _cu("--json", out_json, cwd=tmp)
        assert rc == 0 and "dati d'esempio" in so, se[-300:]
        j = _json.load(open(out_json, encoding="utf-8"))
        b = j["bilancio"]
        assert abs(b["HC"] - 705036.01) < 0.01 and abs(b["PP"] - 194248.56) < 0.01 and b["F"] == 113000
        assert abs(j["esposizione_finanziaria"] - 0.610619) < 1e-5 and abs(j["esposizione_totale"] - 0.277107) < 1e-5
        assert j["equivalenza"] is None
        m = carica_modulo(asset(*CU))
        assert m.equivalenza(0.5, b)["limite"] == "max" and m.equivalenza(0.5, b)["x"] == 1
        assert m.equivalenza(0.1, b)["limite"] == "min" and m.equivalenza(0.1, b)["x"] == 0
        assert abs(m.equivalenza(0.25, b)["x"] - 0.361781) < 1e-5
        assert "calcolo, non target" in m.equivalenza(0.25, b)["messaggio"]
        # s = 0 con un portafoglio azionario: esposizione totale < finanziaria
        dati = _json.load(open(asset("it-pianificazione-obiettivi", "esempio-capitale-umano.json"), encoding="utf-8"))
        dati["persona"]["override"]["quota_azionaria_hc"] = 0
        p = os.path.join(tmp, "s0.json")
        with open(p, "w", encoding="utf-8") as f:
            _json.dump(dati, f)
        rc, so, se = _cu("--dati", p, "--json", out_json, cwd=tmp)
        j = _json.load(open(out_json, encoding="utf-8"))
        assert rc == 0 and j["esposizione_totale"] < j["esposizione_finanziaria"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

@test("T15 capitale umano: dati incoerenti respinti con rc 1, casi limite gestiti")
def t_cu_errori():
    import json as _json
    base = _json.load(open(asset("it-pianificazione-obiettivi", "esempio-capitale-umano.json"), encoding="utf-8"))
    tmp = tempfile.mkdtemp()
    def con(modifica):
        d = _json.loads(_json.dumps(base)); modifica(d)
        p = os.path.join(tmp, "d.json")
        with open(p, "w", encoding="utf-8") as f:
            _json.dump(d, f)
        return p
    try:
        for modifica, atteso in [
            (lambda d: d["persona"].update(profilo="astronauta"), "profilo"),
            (lambda d: d["persona"].update(eta=95), "eta_fine"),
            (lambda d: d["persona"].update(eta_pensione=30), "eta_pensione"),
            (lambda d: d["fondo_pensione"].update(quota_azionaria=60), "quota"),
            (lambda d: d.update(liquidita=-1), "negativ"),
            (lambda d: d.update(persone=[d.pop("persona")]), "persona"),
        ]:
            rc, so, se = _cu("--dati", con(modifica), cwd=tmp)
            assert rc == 1 and se.lstrip().startswith("ERRORE:") and atteso in se, (atteso, rc, se[-200:])
        # Review Focus 2: portafoglio vuoto con equivalenza richiesta
        def vuoto(d):
            d.update(posizioni=[], liquidita=0, esposizione_totale_desiderata=0.3)
        rc, so, se = _cu("--dati", con(vuoto), "--json", os.path.join(tmp, "o.json"), cwd=tmp)
        j = _json.load(open(os.path.join(tmp, "o.json"), encoding="utf-8"))
        assert rc == 0 and j["equivalenza"]["x"] is None and "nessun portafoglio" in j["equivalenza"]["messaggio"]
        # Review Focus 5: asset_class sconosciuta → non azionaria, con avviso
        rc, so, se = _cu("--dati", con(lambda d: d["posizioni"].append({"asset_class": "oro", "valore": 5000})), cwd=tmp)
        assert rc == 0 and "oro" in so and "non azionari" in so
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 3: Esegui e verifica che falliscano**

Run: `python tests/run_tests.py --only "T15 capitale umano"`
Expected: i 2 nuovi ❌; anche «T9 interfaccia» ❌ finché lo script non ha `--help` completo.

- [ ] **Step 4: Implementa `leggi_dati`, `bilancio`, `equivalenza` e `main()` (diagnosi 1 e 2)**

Report: titolo, avvertenza, «1. Bilancio patrimoniale totale» (tabella delle voci con `euro()` e `pct()`), «2. Esposizione azionaria» (due numeri e la frase spec §5.2), riga di equivalenza solo con `esposizione_totale_desiderata`. JSON con le chiavi della spec §5 «Output»; quelle dei Task 3-5 valgono `null` per ora. `profilo_usato` include gli override e l'origine di età di pensione e pensione (`dati`, `from`, `set`).

- [ ] **Step 5: Esegui la suite dei T15 e dei T9**

Run: `python tests/run_tests.py --only "T15 capitale umano" --only "T9"`
Expected: tutti ✅ (compresi `--help`, flag ignoto rc 2, cp1252, formati italiani).

- [ ] **Step 6: Commit**

```bash
git add skills/it-pianificazione-obiettivi/assets/ tests/run_tests.py
git commit -m "feat: bilancio totale, esposizione ed equivalenza del capitale umano (T15)"
```

---

### Task 3: Proiezione nel tempo e Monte Carlo

**Files:**
- Modify: `skills/it-pianificazione-obiettivi/assets/capitale-umano.py`
- Test: `tests/run_tests.py`

**Interfaces:**
- Consumes: Task 1-2 (`bilancio`, `valore_capitale_umano`, `valore_pensione`, costanti).
- Produces:
  - `proiezione(dati: dict, profilo: dict, c: dict, quote_glide: list[float] | None, n_sim: int, seed: int) -> dict` con `anni` (lista di `{"eta", "F", "HC", "PP", "quota_hc", "esposizione", "p10", "p50", "p90"}` dall'età attuale a `eta_pensione + 5`), `eta_sorpasso` (la prima età dopo quella attuale in cui F_det ≥ HC_det mentre l'anno prima era minore; None se F ≥ HC già all'inizio o mai prima della fine), `avvisi`. Legge `REND_AZ_REALE`, `REND_OBB_REALE` e `SIGMA_AZ` dai globali del modulo al momento della chiamata, non come default degli argomenti: il test li modifica.
  - Chiavi JSON `proiezione` (= `anni`) e `eta_sorpasso`.

L'algoritmo è nella spec §5.3. Le scelte che la spec lascia aperte:
- F è un solo contenitore con quota azionaria `q_t` = l'esposizione finanziaria attuale, oppure `quote_glide[t]`, con l'ultima quota tenuta oltre la fine della lista (Review Focus 4, avviso «glide path più corto della proiezione: tenuta l'ultima quota»).
- Il Monte Carlo usa `np.random.default_rng(seed)`. Per ogni anno si estraggono `Z_S` e `Z`; poi `Z_h = ρ Z_S + √(1−ρ²) Z`, il rendimento azionario è `exp(ln(1+REND_AZ_REALE) + SIGMA_AZ Z_S) − 1` e il reddito è `h_{t+1} = h_t exp(ln(1+g) + σ_h Z_h)`. Il risparmio scala con `h_t/h_0`; `HC_t` si rivaluta con `valore_capitale_umano` partendo dal reddito simulato; i percentili riguardano l'esposizione totale.
- Dopo la pensione il risparmio è 0 e la pensione non entra in F.

- [ ] **Step 1: Scrivi i test che falliscono**

```python
@test("T15 capitale umano: proiezione, fascia Monte Carlo e caso di Ibbotson")
def t_cu_proiezione():
    m = carica_modulo(asset(*CU))
    import json as _json
    dati = _json.load(open(asset("it-pianificazione-obiettivi", "esempio-capitale-umano.json"), encoding="utf-8"))
    prof = m.profilo_effettivo(dati["persona"], m.carica_profili())
    c = {"R_F": 0.01, "NU_PENSIONE": 0.0075, "ETA_FINE": 90, "ETA_PENSIONE": 67, "PENSIONE_NETTA": 18000}
    p = m.proiezione(dati, prof, c, None, 500, 7)
    righe = {r["eta"]: r for r in p["anni"]}
    assert min(righe) == 35 and max(righe) == 72
    hc = [righe[e]["HC"] for e in range(35, 68)]
    assert all(a > b for a, b in zip(hc, hc[1:])) and righe[67]["HC"] == 0 and righe[70]["HC"] == 0
    assert righe[66]["PP"] > righe[35]["PP"] and righe[72]["PP"] < righe[67]["PP"]
    assert all(r["p10"] <= r["p50"] <= r["p90"] for r in p["anni"])
    assert p == m.proiezione(dati, prof, c, None, 500, 7)                      # riproducibile col seme
    # ρ = σ_h = 0 e σ_S = 0: nessuna dispersione, fascia sul deterministico
    m.SIGMA_AZ = 0.0
    piatto = dict(prof, rho=0.0, sigma_h=0.0)
    for r in m.proiezione(dati, piatto, c, None, 200, 7)["anni"]:
        assert abs(r["p10"] - r["p90"]) < 1e-9 and abs(r["p50"] - r["esposizione"]) < 1e-9
    m.SIGMA_AZ = 0.18
    # Review Focus 4: glide path più corto
    g = m.proiezione(dati, prof, c, [0.6, 0.5, 0.4], 200, 7)
    assert any("più corto" in a for a in g["avvisi"])
    # Review Focus 1: già in pensione
    pens = _json.loads(_json.dumps(dati)); pens["persona"].update(eta=68, netto_annuo=0, tfr_annuo=0)
    r = m.proiezione(pens, prof, dict(c), None, 200, 7)
    assert r["eta_sorpasso"] is None and all(x["HC"] == 0 for x in r["anni"])
    # Ibbotson et al. 2007, fig. 2.3: (HC + PP)/W ≈ 94% a 25 anni (tolleranza larga: letto da un grafico)
    ib = {"persona": {"profilo": "pubblico", "eta": 25, "eta_pensione": 65, "netto_annuo": 50000, "crescita_reale": 0,
                      "tfr_annuo": 0, "contributo_datore_fp": 0, "quota_reddito_azioni_datore": 0,
                      "override": {"p_u": 0, "nu": 0.04}},
          "pensione": {"netta_annua": 10000, "eta_fine": 85}, "posizioni": [], "liquidita": 50000,
          "fondo_pensione": {"valore": 0, "quota_azionaria": 0}, "tfr_maturato_azienda": 0, "risparmio_annuo": 5000}
    pi = m.profilo_effettivo(ib["persona"], m.carica_profili())
    b = m.bilancio(ib, pi, {"R_F": 0.02, "NU_PENSIONE": 0.04, "ETA_FINE": 85, "ETA_PENSIONE": 65, "PENSIONE_NETTA": 10000})
    assert 0.92 <= (b["HC"] + b["PP"]) / b["W"] <= 0.96, (b["HC"], b["PP"], b["W"])
```

- [ ] **Step 2: Esegui e verifica che falliscano**

Run: `python tests/run_tests.py --only "T15 capitale umano: proiezione"`
Expected: ❌ (`proiezione` non definita).

- [ ] **Step 3: Implementa `proiezione` e la sezione «3. Proiezione» del report**

Tabella ogni 5 anni più l'ultima riga; «Il capitale finanziario supera il capitale umano a N anni» oppure «non lo supera prima della pensione». `--set N_SIM`, `--set SEED` rispettati.

- [ ] **Step 4: Esegui i T15 e i T9**

Run: `python tests/run_tests.py --only "T15 capitale umano" --only "T9"`
Expected: tutti ✅; lo script sui default resta sotto i 10 secondi.

- [ ] **Step 5: Commit**

```bash
git add skills/it-pianificazione-obiettivi/assets/capitale-umano.py tests/run_tests.py
git commit -m "feat: proiezione del capitale umano con fascia Monte Carlo (T15)"
```

---

### Task 4: Sovrapposizione settoriale

**Files:**
- Create: `skills/it-pianificazione-obiettivi/assets/esempio-composizione.csv`
- Modify: `skills/it-pianificazione-obiettivi/assets/capitale-umano.py`
- Test: `tests/run_tests.py`

**Interfaces:**
- Consumes: `bilancio` (`F_az`, `HC_az`), `SETTORI_GICS`.
- Produces:
  - `leggi_composizione(path: str) -> dict[str, dict[str, float]]`: strumento → {settore: peso in frazione}. Legge in `utf-8-sig`, separatore `;`, virgola o punto decimale. Se i pesi di uno strumento sommano più di 1,5 sono percentuali (÷100). Se la somma si scosta da 1 più di 0,02 → `errore()`. Un settore fuori da `SETTORI_GICS` → `errore()` con l'elenco.
  - `sovrapposizione(posizioni: list[dict], composizione: dict, settore: str, F_az: float, HC_az: float, pesi_mondo: dict) -> dict` con `quota_settore_fin`, `peso_mondo`, `rapporto`, `esposizione_combinata`, `sovrappeso` (bool, rapporto > `SOGLIA_SOVRAPPESO`), `mancanti` (strumenti azionari senza composizione).
  - Costante `PESI_MONDO`: dizionario GICS → peso dell'indice MSCI ACWI, dalla scheda MSCI più recente. In commento: mese e URL della scheda. La somma deve stare tra 0,99 e 1,01.
  - Chiave JSON `settore` (null senza `--composizione`). La persona deve avere `settore` (o `settore_default` dal profilo) quando c'è `--composizione`, altrimenti `errore()`.

- [ ] **Step 1: Crea `esempio-composizione.csv`**

Intestazione `strumento;settore;peso`. `ETF MSCI World` con pesi verosimili in percento e virgola (IT `26,0` e gli altri 10 settori fino a 100), `ETF obbligazionario euro` assente: non è azionario.

- [ ] **Step 2: Scrivi il test che fallisce**

```python
@test("T15 capitale umano: sovrapposizione settoriale e CSV da Excel italiano")
def t_cu_settore():
    m = carica_modulo(asset(*CU))
    assert set(m.PESI_MONDO) == set(m.SETTORI_GICS) and 0.99 <= sum(m.PESI_MONDO.values()) <= 1.01
    tmp = tempfile.mkdtemp()
    try:
        p = os.path.join(tmp, "comp.csv")
        with open(p, "w", encoding="utf-8-sig") as f:              # Review Focus 3: BOM, «;», percento con virgola
            f.write("strumento;settore;peso\nA;Information Technology;50,0\nA;Financials;50,0\n"
                    "B;Health Care;1,0\n")
        comp = m.leggi_composizione(p)
        assert comp == {"A": {"Information Technology": 0.5, "Financials": 0.5}, "B": {"Health Care": 1.0}}
        pos = [{"asset_class": "azionario", "valore": 30000, "strumento": "A"},
               {"asset_class": "azionario", "valore": 10000, "strumento": "B"},
               {"asset_class": "azionario", "valore": 10000, "strumento": "C"}]
        s = m.sovrapposizione(pos, comp, "Information Technology", 40000, 60000, {**m.PESI_MONDO, "Information Technology": 0.25})
        assert abs(s["quota_settore_fin"] - 15000 / 40000) < 1e-12 and s["mancanti"] == ["C"]
        assert abs(s["esposizione_combinata"] - (40000 * 0.375 + 60000) / 100000) < 1e-12
        assert abs(s["rapporto"] - 1.5) < 1e-12 and s["sovrappeso"] is False
        with open(p, "w", encoding="utf-8") as f:
            f.write("strumento;settore;peso\nA;Tecnologia;100\n")
        rc, so, se = run_script_split(asset(*CU), "--composizione", p, cwd=tmp)
        assert rc == 1 and "Information Technology" in se
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

Note sul test: le posizioni azionarie senza composizione («C») sono escluse dal numeratore e dal denominatore di `quota_settore_fin` (15.000 / 40.000 sulle sole A e B), come dice la spec §5.4; `F_az` passato alla funzione è quello delle posizioni con composizione.

- [ ] **Step 3: Esegui e verifica che fallisca**

Run: `python tests/run_tests.py --only "T15 capitale umano: sovrapposizione"`
Expected: ❌.

- [ ] **Step 4: Implementa `leggi_composizione`, `sovrapposizione` e `PESI_MONDO`, più la sezione «4. Sovrapposizione settoriale» del report**

Recupera i pesi settoriali dell'MSCI ACWI dalla scheda ufficiale MSCI («Index Factsheet», sezione Sector Weights) e annota mese e URL. Se non è raggiungibile, fermati e chiedi: non inventare i pesi. Il report nomina gli strumenti mancanti e ricorda che il fondo pensione è escluso. In `main()`, il `F_az` passato è la somma delle posizioni azionarie che hanno una composizione.

- [ ] **Step 5: Esegui i T15 e i T9**

Run: `python tests/run_tests.py --only "T15 capitale umano" --only "T9"`
Expected: tutti ✅.

- [ ] **Step 6: Commit**

```bash
git add skills/it-pianificazione-obiettivi/assets/ tests/run_tests.py
git commit -m "feat: sovrapposizione settoriale tra capitale umano e portafoglio (T15)"
```

---

### Task 5: Sensibilità e catena `--from`

**Files:**
- Modify: `skills/it-pianificazione-obiettivi/assets/capitale-umano.py`
- Test: `tests/run_tests.py`

**Interfaces:**
- Consumes: `bilancio`, `profilo_effettivo`.
- Produces:
  - `sensibilita(dati: dict, profilo: dict, c: dict) -> list[dict]`: una riga per variante, `{"parametro", "variante", "HC", "esposizione_totale", "delta"}`. Varianti: `s` ±0,10 (limitata a [0, 1]), `nu` ±0,015 (minimo 0), `g` a 0 e a 0,02, `p_u` × 2, `r_f` ±0,01. Ordinate per `max |delta|` del parametro, decrescente, con le varianti dello stesso parametro adiacenti.
  - Chiave JSON `sensibilita`; sezione «5. Sensibilità» del report.

- [ ] **Step 1: Scrivi i test che falliscono**

```python
@test("T15 capitale umano: sensibilità ordinata e catena --from dagli script previdenziali")
def t_cu_sensibilita_catena():
    import json as _json
    m = carica_modulo(asset(*CU))
    dati = _json.load(open(asset("it-pianificazione-obiettivi", "esempio-capitale-umano.json"), encoding="utf-8"))
    prof = m.profilo_effettivo(dati["persona"], m.carica_profili())
    c = {"R_F": 0.01, "NU_PENSIONE": 0.0075, "ETA_FINE": 90, "ETA_PENSIONE": 67, "PENSIONE_NETTA": 18000}
    righe = m.sensibilita(dati, prof, c)
    assert {r["parametro"] for r in righe} == {"s", "nu", "g", "p_u", "r_f"} and len(righe) == 9
    ampiezze = []
    for r in righe:
        if not ampiezze or ampiezze[-1][0] != r["parametro"]:
            ampiezze.append([r["parametro"], 0])
        ampiezze[-1][1] = max(ampiezze[-1][1], abs(r["delta"]))
    assert [a[1] for a in ampiezze] == sorted((a[1] for a in ampiezze), reverse=True)
    assert next(r for r in righe if r["parametro"] == "nu" and r["variante"] == "+0,015")["HC"] < m.bilancio(dati, prof, c)["HC"]
    tmp = tempfile.mkdtemp()
    try:
        A = "it-pianificazione"
        assert run_script(asset(A, "proiezione-inps.py"), "--json", os.path.join(tmp, "inps.json"), cwd=tmp)[0] == 0
        assert run_script(asset(A, "netto-pensione.py"), "--json", os.path.join(tmp, "netto.json"), cwd=tmp)[0] == 0
        senza = _json.loads(_json.dumps(dati)); senza["persona"].pop("eta_pensione"); senza.pop("pensione")
        p = os.path.join(tmp, "d.json")
        with open(p, "w", encoding="utf-8") as f:
            _json.dump(senza, f)
        rc, so, se = run_script_split(asset(*CU), "--dati", p, "--from", os.path.join(tmp, "inps.json"),
                                      "--from", os.path.join(tmp, "netto.json"), "--json", os.path.join(tmp, "cu.json"), cwd=tmp)
        assert rc == 0, se[-300:]
        j = _json.load(open(os.path.join(tmp, "cu.json"), encoding="utf-8"))
        inps = _json.load(open(os.path.join(tmp, "inps.json"), encoding="utf-8"))
        netto = _json.load(open(os.path.join(tmp, "netto.json"), encoding="utf-8"))
        assert j["profilo_usato"]["eta_pensione"] == int(inps["eta_pensionamento"])
        assert j["profilo_usato"]["pensione_netta"] == netto["netto_pensione_inps"]
        # --set prevale su --dati
        rc, so, se = run_script_split(asset(*CU), "--set", "ETA_PENSIONE=70", "--json", os.path.join(tmp, "cu.json"), cwd=tmp)
        assert rc == 0 and _json.load(open(os.path.join(tmp, "cu.json"), encoding="utf-8"))["profilo_usato"]["eta_pensione"] == 70
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

Per l'etichetta delle varianti usa `numero(x, 3, segno=True)`, oppure «× 2» per p_u e «0%»/«2%» per g: l'unica etichetta fissata dal test è `"+0,015"`.

- [ ] **Step 2: Esegui e verifica che fallisca**

Run: `python tests/run_tests.py --only "T15 capitale umano: sensibilità"`
Expected: ❌.

- [ ] **Step 3: Implementa `sensibilita` e la sezione del report, completa la precedenza `--set` > `--dati` > `--from` in `main()`**

Se dopo la risoluzione mancano età di pensione o pensione netta → `errore()` che indica le tre strade (`--dati`, `--from`, `--set`).

- [ ] **Step 4: Esegui i T15 e i T9**

Run: `python tests/run_tests.py --only "T15 capitale umano" --only "T9"`
Expected: tutti ✅.

- [ ] **Step 5: Commit**

```bash
git add skills/it-pianificazione-obiettivi/assets/capitale-umano.py tests/run_tests.py
git commit -m "feat: sensibilità del capitale umano e catena dagli script previdenziali (T15)"
```

---

### Task 6: Reference, skill e comando

**Files:**
- Create: `skills/it-pianificazione-obiettivi/references/capitale-umano.md`
- Create: `commands/capitale-umano.md`
- Modify: `skills/it-pianificazione-obiettivi/SKILL.md` (Step 7, `description`, `metadata.version` da `"0.20"` a `"0.21"`, Riferimenti)
- Modify: `tests/run_tests.py` (`OBBLIGATI_FRESHNESS` + `"it-pianificazione-obiettivi/references/capitale-umano.md"`)

**Interfaces:**
- Consumes: le chiavi JSON e le sezioni del report dei Task 2-5.
- Produces: la documentazione che il Task 7 richiama.

- [ ] **Step 1: Aggiungi la reference a `OBBLIGATI_FRESHNESS` ed esegui i test di igiene e di freshness**

Run: `python tests/run_tests.py --only freshness --only igiene --only T14`
Expected: ❌ (file mancante; asset del Task 1-4 non nei Riferimenti).

- [ ] **Step 2: Scrivi `references/capitale-umano.md`**

Indice in testa (il file supera le 100 righe). Sezioni:
- cos'è il capitale umano;
- il modello della spec §3 con le formule;
- perché la quota azionaria è esplicita e non deriva da β (spec §3.2);
- i profili e come sceglierli, con i precari come `privato_ciclico` e `p_u` più alto (indicativamente 0,10-0,15);
- le cinque diagnosi e come leggerle;
- un esempio svolto con i numeri dell'esempio: HC €705.036, PP €194.249, esposizione 61,1% contro 27,7%;
- i limiti (spec §9);
- la bibliografia (spec §2) con i link liberi riportati nella spec;
- la NASpI: sostituzione, decalage e tetto mensile verificati sulla circolare INPS dell'anno, con `Verificato: AAAA-MM`. Se la fonte primaria contraddice lo 0,6 del CSV, correggi CSV e test e segnalalo nel commit.

Postura: educativa, «non è consulenza».

- [ ] **Step 3: Aggiorna `SKILL.md`**

- Dopo lo Step 6, aggiungi «### Step 7 (facoltativo): la lente del capitale umano», 10-20 righe: a cosa serve, il comando di lancio con `${CLAUDE_SKILL_DIR}`, le cinque diagnosi in una riga ciascuna, «non modifica i target», rinvio alla reference.
- Nella `description`, aggiungi i trigger «capitale umano», «reddito da lavoro nella ricchezza totale» e «sono un'azione o un'obbligazione», restando entro 1.024 caratteri (oggi sono 972: accorcia altrove senza perdere trigger).
- Nei Riferimenti, aggiungi le righe `- \`references/capitale-umano.md\` — …` e una per ciascuno dei quattro asset nuovi.

- [ ] **Step 4: Crea `commands/capitale-umano.md`**

Sul modello di `commands/obiettivi.md`:
- `name: capitale-umano`;
- description di una riga;
- `argument-hint: "[età, reddito netto, tipo di lavoro]"`;
- `disable-model-invocation: true`;
- corpo che esegue `it-pianificazione-obiettivi` con focus sullo Step 7;
- la riga «Disclaimer obbligatorio …» identica nella forma a quella degli altri comandi.

Nessun `.py` nel testo.

- [ ] **Step 5: Esegui la suite completa**

Run: `python tests/run_tests.py`
Expected: falliscono solo il conteggio e la tabella degli strumenti del README, che sistema il Task 7.

- [ ] **Step 6: Commit**

```bash
git add skills/it-pianificazione-obiettivi/ commands/capitale-umano.md tests/run_tests.py
git commit -m "docs: reference, Step 7 e comando /capitale-umano (T15)"
```

---

### Task 7: Revisione, README, CHANGELOG e ROADMAP

**Files:**
- Modify: `skills/it-revisione/SKILL.md` (tabella «Contratto di input»: riga «Capitale umano»)
- Modify: `skills/it-revisione/assets/template-revisione.md` (sottosezione in «3. Avanzamento per dominio»)
- Modify: `tests/run_tests.py` (`t_contratto_revisione`: in `lanci` aggiungi `"cu.json": (asset("it-pianificazione-obiettivi", "capitale-umano.py"), [])`, con il collegamento riga → file che il test già usa)
- Modify: `README.md` (conteggio dei test, tabella generata con `--tabella-test`, architettura e elenco delle skill con la lente), `CHANGELOG.md` («Non rilasciato»), `ROADMAP.md` (T15 e T16 sotto «Dopo — da decidere», testo della spec §8)

**Interfaces:**
- Consumes: chiavi JSON `esposizione_finanziaria`, `esposizione_totale`, `settore.quota_settore_fin`, `settore.sovrappeso`, `eta_sorpasso`.

- [ ] **Step 1: Aggiungi la riga al contratto e il lancio nel test, poi esegui il test**

Riga: `| Capitale umano | capitale-umano.py --json (it-pianificazione-obiettivi) | esposizione_finanziaria, esposizione_totale; settore.quota_settore_fin e settore.sovrappeso se c'è --composizione; eta_sorpasso | report, nessuna cella |`

Run: `python tests/run_tests.py --only "contratto di input"`
Expected: ✅ (le chiavi esistono nel JSON). Se il test non sa trattare una riga senza cella, estendilo come per la riga «Fiscalità».

- [ ] **Step 2: Aggiungi la sottosezione al template di revisione**

`### Capitale umano *(da it-pianificazione-obiettivi)*` con i campi: esposizione finanziaria contro totale, sovrapposizione di settore, età del sorpasso, e la nota «lente, non target».

- [ ] **Step 3: Aggiorna README, CHANGELOG e ROADMAP**

- **README:** rigenera la tabella con `python tests/run_tests.py --tabella-test` e incollala tra i marcatori esistenti; aggiorna il «N test» al numero dei decoratori; una riga nell'architettura o nell'elenco delle skill per la lente.
- **CHANGELOG:** voce in «Non rilasciato» nello stile delle altre: cosa fa, le cinque diagnosi, i numeri dell'esempio, le fonti principali.
- **ROADMAP:** T15 con le caselle spuntate per ciò che è fatto, T16 con la tabella della spec §8.

- [ ] **Step 4: Esegui la suite completa**

Run: `python tests/run_tests.py`
Expected: tutti ✅ (i test che richiedono LibreOffice possono risultare «saltati» se manca).

- [ ] **Step 5: Commit e push**

```bash
git add -A skills/it-revisione README.md CHANGELOG.md ROADMAP.md tests/run_tests.py
git commit -m "docs: capitale umano in revisione, README, CHANGELOG e ROADMAP (T15, T16)"
git push -u origin claude/eloquent-turing-pu8oip
```
