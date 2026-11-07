# Look-through del portafoglio: piano di implementazione

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `look-through-portafoglio.py` aggrega settori, paesi e primi titoli di tutti gli ETF posseduti, pesati per controvalore, da `composizione.csv` e dalle posizioni dell'estratto del broker; il suo `--json` entra in `it-revisione` e nel cruscotto.

**Architecture:** L'importatore della composizione impara a scrivere i primi titoli (`dimensione=titolo`) e ad accettare l'ISIN come chiave; il capitale umano impara a confrontare le posizioni anche per ISIN e a saltare le righe `titolo`. Lo script nuovo legge il CSV con un lettore proprio (tre formati), carica le posizioni da uno o più JSON, confronta per ISIN poi per nome, aggrega per dimensione sulla parte coperta e dichiara la copertura. Il cruscotto riconosce il JSON dalla firma e aggiunge una sezione.

**Tech Stack:** Python ≥ 3.11, libreria standard; `cli()`, `errore()`, `numero()`, `euro()`, `pct()`, `scrivi_json()` di `motore_bootstrap.py`; le tabelle `SETTORI_GICS`, `PAESI` e `normalizza()` di `importa-composizione-etf.py` caricate con `importlib` (stessa cartella, ancorata a `__file__`); runner `tests/run_tests.py` (decoratore `@test`, nessun pytest); Playwright per i test del browser.

**Spec:** `docs/sviluppo/specs/2026-11-01-look-through-design.md` (citata sotto come «spec §N»).

## Global Constraints

- Nessuna chiamata di rete: solo file locali (spec §1).
- Interfaccia comune: `cli()` con `allow_abbrev=False`; exit 0 riuscito, 1 dati con `ERRORE:` su stderr, 2 riga di comando errata; `configura_stdout()` prima di ogni stampa (lo fa `cli()`).
- Formati italiani con `numero()`, `euro()`, `pct()`: niente `{x:,.0f}`, `{x:.1%}`, `{x:.1f}` (`t_formati_italiani`); `open()` sempre con `encoding=` (`t_cli_utf8`).
- Niente mezzo output: tutto letto e validato prima di scrivere `--json`.
- `composizione.csv` resta `strumento;dimensione;voce;peso`, UTF-8 con BOM, `;`, virgola decimale, due decimali; le righe `titolo` portano il peso nel fondo non rinormalizzato (spec §3.1).
- Il cruscotto non porta nomi né ISIN delle posizioni dell'utente (spec §4): il bundle `look_through` non ha `posizioni` né `senza_composizione`.
- I test nuovi si chiamano `T16 look-through: …` in una sezione `# ═══ T16: look-through del portafoglio ═══` di `tests/run_tests.py`, dopo il blocco T16 della composizione e prima di T17. Costante `LT = ("it-pianificazione-obiettivi", "look-through-portafoglio.py")`.
- Nessun comando nuovo (`t_comandi_alias`: un comando per skill). Nessuna icona. Nessun dato personale reale nelle fixture (gli ISIN degli ETF sono pubblici).
- Commit in italiano, con le righe di attribuzione della sessione; `(T16)` in coda al messaggio.

## Review Focus

1. **Lo stesso ETF su due broker** (stesso ISIN in due `--posizioni`): un'unica posizione con la somma, nel conteggio e nel report. Test nel Task 3.
2. **Un ETF importato con il nome e una posizione che ha solo l'ISIN** (l'utente ha importato prima del ciclo, con `--strumento "ETF MSCI World"`, e ora passa il JSON del broker): la posizione va in `senza_composizione` con nome e ISIN, e il report dice di reimportare con l'ISIN o di aggiungere la riga. Test nel Task 3.
3. **CSV con sole righe `titolo` per uno strumento** (compilate a mano senza settori): quello strumento conta nei titoli e in nessun'altra dimensione; la copertura dei settori non lo include. Test nel Task 3.
4. **Un nome di titolo che dopo la normalizzazione resta vuoto** («S.A.» da solo, o «-»): la riga si ignora con un avviso, non diventa una chiave vuota che somma titoli diversi. Test nel Task 2.
5. **Il JSON del look-through generato prima di una modifica delle chiavi** (per esempio senza `n_titoli_aggregati`): il cruscotto lo rifiuta con «manca …» e il nome del file, non con un traceback. Test nel Task 4.

---

### Task 1: L'importatore scrive i primi titoli e accetta l'ISIN

**Files:**
- Modify: `skills/it-pianificazione-obiettivi/assets/importa-composizione-etf.py` (`SINONIMI_COLONNE`, nuova costante `N_TITOLI`, `componi()`, `righe_strumento()`, `stampa()`, `main()`, docstring)
- Modify: `skills/it-pianificazione-obiettivi/assets/capitale-umano.py:448-500` (`leggi_composizione()`, `sovrapposizione()`, il filtro `F_az_comp` in `main()`), `assets/esempio-capitale-umano.json`
- Test: `tests/run_tests.py` (dopo `t_ce_tabelle_set`)

**Interfaces:**
- Produces:
  - `N_TITOLI = 10` in testa all'importatore, letto in `componi()` al momento dell'uso (`--set` ha effetto); un valore non intero positivo → `errore()`.
  - `SINONIMI_COLONNE["isin"] = ("isin", "codice isin", "isin code")`; il ruolo è facoltativo come `asset_class`.
  - `componi()` ritorna in più `"titoli": [{"nome": str, "isin": str | None, "peso": float}]` (frazione del fondo, dopo la scala, ordinati per peso decrescente, al massimo `N_TITOLI`, solo righe non escluse da liquidità, derivati e peso negativo; nome con `.strip()`; righe con nome vuoto o segnaposto saltate). Se la colonna `nome` manca: lista vuota e avviso «il file non ha la colonna del nome: titoli non scritti».
  - `righe_strumento()` scrive dopo settori e paesi le righe `strumento;titolo;<nome>;<peso %>`.
  - `stampa()` aggiunge la riga «   Primi titoli: A 30,00% · B 20,00% · …» (i primi 5).
  - `--isin` come secondo nome di `--strumento` (stesso `dest`, stesso `action="append"`); help: «nome o ISIN dello strumento, come nelle posizioni (uno per --file); con le posizioni dell'estratto del broker usa l'ISIN».
  - `capitale-umano.leggi_composizione()` salta le righe con `dimensione == "titolo"` (e continua a respingere ogni altra dimensione sconosciuta). Ritorna come oggi `{strumento: {settore: frazione}}`.
  - `capitale-umano.chiave_composizione(pos: dict, composizione: dict) -> str | None`: la prima tra `pos["isin"]` e `pos["strumento"]` (con `.strip()`) presente in `composizione`, altrimenti `None`. Usata da `sovrapposizione()` e dal calcolo di `F_az_comp`; `mancanti` elenca `strumento`, o `isin` se manca, o «(senza strumento)».
  - `esempio-capitale-umano.json`: le due posizioni prendono `"isin": "IE00B4L5Y983"` e `"isin": "IE00B3F81R35"` con una nota `_nota` che li dichiara ISIN d'esempio.

- [ ] **Step 1: Scrivi il test `T16 look-through: l'importatore scrive i primi titoli, --isin è --strumento, il JSON porta l'ISIN dei titoli`**

```python
@test("T16 look-through: l'importatore scrive i primi titoli, --isin è --strumento, il JSON porta l'ISIN dei titoli")
def t_lt_importatore_titoli():
    tmp = tempfile.mkdtemp()
    try:
        out, js = os.path.join(tmp, "composizione.csv"), os.path.join(tmp, "c.json")
        rc, so, se = run_script_split(asset(*CE), "--file", os.path.join(FIXTURES, "composizione-ishares-en.csv"),
                                      "--isin", "IE00B4L5Y983", "--out", out, "--json", js, cwd=tmp)
        assert rc == 0, se[-300:]
        righe = [r for r in open(out, encoding="utf-8-sig").read().splitlines() if ";titolo;" in r]
        # pesi nel fondo, non rinormalizzati; liquidità e future fuori; ordine per peso
        assert righe == ["IE00B4L5Y983;titolo;ALPHA CORP;30,00", "IE00B4L5Y983;titolo;BETA BANK;20,00",
                         "IE00B4L5Y983;titolo;GAMMA PHARMA;15,00", "IE00B4L5Y983;titolo;DELTA INDUSTRIES;15,00",
                         "IE00B4L5Y983;titolo;EPSILON SOFT;10,00", "IE00B4L5Y983;titolo;ZETA ENERGY;9,00"], righe
        s = json.load(open(js, encoding="utf-8"))["strumenti"][0]
        assert s["strumento"] == "IE00B4L5Y983" and s["titoli"][0] == {"nome": "ALPHA CORP", "isin": None, "peso": 0.30}
        assert "Primi titoli: ALPHA CORP 30,00%" in so
        # --set N_TITOLI=2 e un XLSX con la colonna ISIN (Xtrackers): isin nel JSON, settori di prima conservati
        rc, so, se = run_script_split(asset(*CE), "--file", _xlsx_emittente("xtrackers", tmp), "--strumento", "XD",
                                      "--out", out, "--json", js, "--set", "N_TITOLI=2", cwd=tmp)
        assert rc == 0, se[-300:]
        testo = open(out, encoding="utf-8-sig").read()
        assert testo.count("XD;titolo;") == 2 and testo.count("IE00B4L5Y983;titolo;") == 6, testo
        t = json.load(open(js, encoding="utf-8"))["strumenti"][0]["titoli"]
        assert [x["isin"] for x in t] == ["XX0000000001", "XX0000000002"] and t[0]["peso"] == 0.40, t
        rc, so, se = run_script_split(asset(*CE), "--file", os.path.join(FIXTURES, "composizione-ishares-en.csv"),
                                      "--strumento", "A", "--out", out, "--set", "N_TITOLI=0", cwd=tmp)
        assert rc == 1 and "N_TITOLI" in se, se[-300:]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 2: Scrivi il test `T16 look-through: capitale-umano ignora le righe titolo e confronta le posizioni per ISIN`**

```python
@test("T16 look-through: capitale-umano ignora le righe titolo e confronta le posizioni per ISIN")
def t_lt_capitale_umano_isin():
    cu = carica_modulo(asset(*CU))
    tmp = tempfile.mkdtemp()
    try:
        out = os.path.join(tmp, "composizione.csv")
        rc, so, se = run_script_split(asset(*CE), "--file", os.path.join(FIXTURES, "composizione-ishares-en.csv"),
                                      "--isin", "IE00B4L5Y983", "--out", out, cwd=tmp)
        assert rc == 0, se[-300:]
        comp = cu.leggi_composizione(out)
        assert set(comp) == {"IE00B4L5Y983"} and abs(comp["IE00B4L5Y983"]["Information Technology"] - 0.4040) < 1e-9, comp
        assert cu.chiave_composizione({"isin": "IE00B4L5Y983", "strumento": "ETF World"}, comp) == "IE00B4L5Y983"
        assert cu.chiave_composizione({"strumento": "IE00B4L5Y983"}, comp) == "IE00B4L5Y983"
        assert cu.chiave_composizione({"isin": "IE00B4L5Y984", "strumento": "ETF World"}, comp) is None
        dati = json.load(open(asset("it-pianificazione-obiettivi", "esempio-capitale-umano.json"), encoding="utf-8"))
        dati["persona"]["settore"] = "Information Technology"
        dati["posizioni"] = [{"asset_class": "azionario", "valore": 60000, "isin": "IE00B4L5Y983"},
                             {"asset_class": "azionario", "valore": 20000, "isin": "IE00B4L5Y984"},
                             {"asset_class": "azionario", "valore": 20000, "strumento": "ETF FTSE", "isin": "IE00B3RBWM25"}]
        pd_ = os.path.join(tmp, "cu.json")
        json.dump(dati, open(pd_, "w", encoding="utf-8"))
        rc, so, se = run_script_split(asset(*CU), "--dati", pd_, "--composizione", out, "--json", os.path.join(tmp, "o.json"), cwd=tmp)
        assert rc == 0, se[-300:]
        z = json.load(open(os.path.join(tmp, "o.json"), encoding="utf-8"))["settore"]
        assert abs(z["quota_settore_fin"] - 0.4040) < 1e-4 and z["mancanti"] == ["IE00B4L5Y984", "ETF FTSE"], z
        # l'esempio del plugin ha gli ISIN e gira ancora sull'esempio-composizione.csv (vecchio formato, per nome)
        rc, out_es = run_script(asset(*CU), "--composizione", asset("it-pianificazione-obiettivi", "esempio-composizione.csv"))
        assert rc == 0 and "ETF MSCI World" not in out_es.split("SOVRAPPOSIZIONE")[1].split("Senza composizione")[0], out_es[-600:]
        es = json.load(open(asset("it-pianificazione-obiettivi", "esempio-capitale-umano.json"), encoding="utf-8"))
        assert all(re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}\d", p["isin"]) for p in es["posizioni"]), es["posizioni"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 3: Esegui e verifica che falliscano** — `python tests/run_tests.py --only "T16 look-through"` → 2 FAIL (`--isin` non riconosciuto; `chiave_composizione` assente).

- [ ] **Step 4: Implementa nell'importatore**: `N_TITOLI`, il ruolo `isin`, la raccolta dei titoli in `componi()` (nello stesso ciclo delle esclusioni, prima del `continue` delle dimensioni: la riga conta se non è liquidità o derivato), `righe_strumento()`, `stampa()`, l'alias `--isin`, la docstring («Uso:» e la regola dei titoli). In `capitale-umano.py`: `leggi_composizione()` salta `titolo`; `chiave_composizione()`; `sovrapposizione()` e `main()` la usano; `esempio-capitale-umano.json` con gli ISIN e la nota.

- [ ] **Step 5: Esegui e verifica** — `python tests/run_tests.py --only "T16"` → tutti PASS (anche i test della composizione esistenti: le righe `titolo` in più non devono rompere `t_ce_fusione` e `t_ce_capitale_umano`; se `t_ce_fusione` conta le righe del CSV, aggiorna il conteggio con il motivo nel test).

- [ ] **Step 6: Commit** — `feat: l'importatore della composizione scrive i primi titoli e accetta l'ISIN come chiave (T16)`

---

### Task 2: `look-through-portafoglio.py`: lettura, chiave dei titoli, aggregazione

**Files:**
- Create: `skills/it-pianificazione-obiettivi/assets/look-through-portafoglio.py`
- Create: `tests/fixtures/estratto-look-through.csv`, `tests/fixtures/composizione-look-through.csv`
- Test: `tests/run_tests.py`

**Interfaces:**
- Consumes: `cli`, `errore`, `numero`, `euro`, `pct`, `scrivi_json` dal motore; `SETTORI_GICS`, `PAESI`, `normalizza` da `importa-composizione-etf.py` via `importlib.util.spec_from_file_location("importa_composizione_etf", <percorso accanto a __file__>)`.
- Produces:
  - Costanti in testa: `N_TITOLI_REPORT = 10`, `N_PAESI_REPORT = 10`, `SUFFISSI_SOCIETARI = ("inc", "corp", "corporation", "co", "ltd", "limited", "plc", "sa", "spa", "ag", "se", "nv", "ab", "asa", "oyj", "kk", "holdings", "holding", "group")`, `CLASSI_AZIONI = ("class a", "class b", "class c", "cl a", "cl b", "cl c", "ord", "adr", "reit")`.
  - `chiave_titolo(nome: str) -> str`: `normalizza(nome)`, poi tolte le parole di `SUFFISSI_SOCIETARI` in coda (ripetutamente: «nestle s a» → «nestle»; «s a» nasce da «S.A.» perché `normalizza` spezza sulla punteggiatura, quindi anche `"s", "a"` vanno gestite: si tolgono in coda le sequenze `s a`, `s p a`, `n v` prima dei suffissi) e le classi di `CLASSI_AZIONI` ovunque come parole intere; spazi compressi; maiuscole. Stringa vuota se non resta nulla.
  - `leggi_composizione(path) -> dict[str, dict[str, dict[str, float]]]`: `{chiave: {"settori": {voce: frazione}, "paesi": {codice: frazione}, "titoli": {nome: frazione}}}`; accetta i tre formati (`strumento;settore;peso` → solo settori; `strumento;dimensione;voce;peso`); pesi in percento o frazione per strumento e dimensione come in `capitale-umano.leggi_composizione` (somma > 1,5 → percento); dimensione sconosciuta, peso non numerico, colonne sconosciute → `errore()`. Le voci dei settori si validano contro `SETTORI_GICS`, i paesi contro `PAESI` (codice ISO).
  - `leggi_posizioni(percorsi: list[str]) -> list[dict]`: per ogni file un JSON con `posizioni` (lista), altrimenti `errore()` «{file}: manca la lista posizioni: serve il --json di importa-estratto-broker.py o il --dati del capitale umano»; ogni posizione → `{"isin": str | None, "nome": str, "valore": float}` con `nome` da `descrizione` o `strumento` o l'ISIN; `valore` assente o non numerico o negativo → `errore()` con l'indice; zero → saltata con avviso. Posizioni con lo stesso ISIN (non vuoto) si sommano in una, con il primo nome; lo stesso nome senza ISIN pure.
  - `aggrega(posizioni, composizione) -> dict`: il JSON della spec §3.2, con `chiave` = ISIN se presente nel CSV, altrimenti il nome se presente, altrimenti `None` (→ `senza_composizione`). `titoli[].da` ordinato per contributo decrescente; `nome` del titolo dallo strumento che contribuisce di più; `n_titoli_aggregati`; `quota_primi_titoli` sui primi `N_TITOLI_REPORT`. Nessuna posizione con chiave → `errore()` «nessuna posizione ha una composizione in {csv}: importa i file delle posizioni con l'ISIN come --strumento, o compila le righe a mano».
  - `stampa(r)`: il report della spec §3.5.
  - `main()`: `cli(..., spazio=globals(), json=True, argomenti=[--composizione (required), --posizioni (append, required)])`; con `--json -` stampa solo il JSON.

- [ ] **Step 1: Crea le due fixture.** `estratto-look-through.csv` (formato dell'estratto, `;` e virgola decimale):

```
broker;ISIN;Descrizione;Quantità;Prezzo medio di carico;Controvalore
Fineco;IE00B4L5Y983;iShares Core MSCI World;100;75,50;9.200,00
Fineco;IE00B5BMR087;iShares Core S&P 500;50;420,00;19.500,00
Directa;IE00B4L5Y983;iShares Core MSCI World;40;80,00;3.800,00
Directa;IT0005454241;BTP Futura 2037;30;98,00;2.850,00
Directa;DE0007164600;SAP SE;10;100,00;1.500,00
```

`composizione-look-through.csv` (chiave ISIN; il BTP a mano con il solo paese; un titolo in comune scritto in due modi; pesi dei titoli nel fondo):

```
# Fixture sintetica per il look-through: pesi illustrativi, non di un ETF reale.
strumento;dimensione;voce;peso
IE00B4L5Y983;settore;Information Technology;30,00
IE00B4L5Y983;settore;Financials;20,00
IE00B4L5Y983;settore;Health Care;50,00
IE00B4L5Y983;paese;US;60,00
IE00B4L5Y983;paese;JP;25,00
IE00B4L5Y983;paese;GB;15,00
IE00B4L5Y983;titolo;APPLE INC;5,00
IE00B4L5Y983;titolo;NESTLE SA;3,00
IE00B5BMR087;settore;Information Technology;40,00
IE00B5BMR087;settore;Financials;60,00
IE00B5BMR087;paese;US;100,00
IE00B5BMR087;titolo;Apple Inc.;7,00
IE00B5BMR087;titolo;MICROSOFT CORP;6,00
IT0005454241;paese;IT;100,00
```

- [ ] **Step 2: Scrivi il test `T16 look-through: chiave dei titoli (suffissi, classi, accenti) e nomi che restano vuoti`**

```python
@test("T16 look-through: chiave dei titoli (suffissi, classi, accenti) e nomi che restano vuoti")
def t_lt_chiave_titolo():
    m = carica_modulo(asset(*LT))
    for a, b in (("Apple Inc.", "APPLE INC"), ("ALPHABET INC CLASS A", "Alphabet Inc Class C"),
                 ("Microsoft Corp", "MICROSOFT CORPORATION"), ("Nestlé SA", "NESTLE S.A."),
                 ("Taiwan Semiconductor Manufacturing", "TAIWAN SEMICONDUCTOR MANUFACTURING CO LTD"),
                 ("Samsung Electronics Co Ltd", "SAMSUNG ELECTRONICS"), ("Eni SpA", "ENI S.P.A."),
                 ("Prologis REIT Inc", "PROLOGIS")):
        assert m.chiave_titolo(a) == m.chiave_titolo(b) != "", (a, b, m.chiave_titolo(a), m.chiave_titolo(b))
    for a, b in (("Bank of America", "Bank of Montreal"), ("Nvidia", "Novartis"), ("Shell", "Shell Midstream")):
        assert m.chiave_titolo(a) != m.chiave_titolo(b), (a, b)
    assert m.chiave_titolo("S.A.") == "" and m.chiave_titolo("-") == "" and m.chiave_titolo("Co") == ""
```

- [ ] **Step 3: Scrivi il test `T16 look-through: valori chiusi sulle fixture, due broker sommati, BTP solo nei paesi, senza composizione`**

```python
def _broker_look_through(tmp, estratto="estratto-look-through.csv"):
    rc, out = run_script(asset("it-tax-optimization", "importa-estratto-broker.py"), os.path.join(FIXTURES, estratto),
                         "--anno", "2026", "--json", "broker.json", cwd=tmp)
    assert rc == 0, out[-300:]
    return os.path.join(tmp, "broker.json")


@test("T16 look-through: valori chiusi sulle fixture, due broker sommati, BTP solo nei paesi, senza composizione")
def t_lt_valori_chiusi():
    tmp = tempfile.mkdtemp()
    try:
        comp = os.path.join(FIXTURES, "composizione-look-through.csv")
        rc, so, se = run_script_split(asset(*LT), "--composizione", comp, "--posizioni", _broker_look_through(tmp),
                                      "--json", "lt.json", cwd=tmp)
        assert rc == 0, se[-300:]
        r = json.load(open(os.path.join(tmp, "lt.json"), encoding="utf-8"))
        tot = 9200 + 19500 + 3800 + 2850 + 1500                                   # 36.850
        assert r["controvalore_totale"] == tot
        pos = {p["chiave"]: p for p in r["posizioni"]}
        assert pos["IE00B4L5Y983"]["valore"] == 13000 and pos["IE00B4L5Y983"]["nome"] == "iShares Core MSCI World"   # due broker
        assert pos["IT0005454241"] == {"chiave": "IT0005454241", "nome": "BTP Futura 2037", "valore": 2850,
                                       "quota": 2850 / tot, "settori": False, "paesi": True, "titoli": False}
        assert r["senza_composizione"] == [{"chiave": "DE0007164600", "nome": "SAP SE", "valore": 1500, "quota": 1500 / tot}]
        V_s = 13000 + 19500                                                         # settori e titoli: i due ETF
        assert abs(r["copertura"]["settori"] - V_s / tot) < 1e-12 and abs(r["copertura"]["titoli"] - V_s / tot) < 1e-12
        assert abs(r["copertura"]["paesi"] - (V_s + 2850) / tot) < 1e-12
        settori = {s["voce"]: s["peso"] for s in r["settori"]}
        assert abs(settori["Information Technology"] - (13000 * .30 + 19500 * .40) / V_s) < 1e-12
        assert abs(settori["Financials"] - (13000 * .20 + 19500 * .60) / V_s) < 1e-12
        assert abs(settori["Health Care"] - 13000 * .50 / V_s) < 1e-12 and abs(sum(settori.values()) - 1) < 1e-12
        assert r["settori"][0]["voce"] == "Financials" and r["settori"][0]["nome"] == "Finanza"   # ordinati per peso
        paesi = {p["voce"]: p["peso"] for p in r["paesi"]}
        V_p = V_s + 2850
        assert abs(paesi["US"] - (13000 * .60 + 19500) / V_p) < 1e-12 and abs(paesi["IT"] - 2850 / V_p) < 1e-12
        assert r["paesi"][0]["nome"] == "Stati Uniti"
        titoli = {t["nome"]: t for t in r["titoli"]}
        assert abs(titoli["Apple Inc."]["peso"] - (13000 * .05 + 19500 * .07) / V_s) < 1e-12      # sommati, nome dal maggiore
        assert titoli["Apple Inc."]["da"] == ["IE00B5BMR087", "IE00B4L5Y983"]
        assert abs(titoli["MICROSOFT CORP"]["peso"] - 19500 * .06 / V_s) < 1e-12 and titoli["NESTLE SA"]["da"] == ["IE00B4L5Y983"]
        assert r["n_titoli_aggregati"] == 3 and abs(r["quota_primi_titoli"] - sum(t["peso"] for t in r["titoli"])) < 1e-12
        assert "SAP SE (DE0007164600)" in so and "minimo della concentrazione" in so and "€36.850" in so
        assert "Finanza" in so and "Stati Uniti" in so and "Apple Inc." in so
        # Review Focus 2: una posizione che ha solo l'ISIN mentre il CSV ha il nome
        with open(os.path.join(tmp, "nome.csv"), "w", encoding="utf-8") as f:
            f.write("strumento;settore;peso\nETF MSCI World;Information Technology;100\n")
        rc, so, se = run_script_split(asset(*LT), "--composizione", os.path.join(tmp, "nome.csv"),
                                      "--posizioni", os.path.join(tmp, "broker.json"), cwd=tmp)
        assert rc == 1 and "nessuna posizione ha una composizione" in se and "ISIN" in se, se[-300:]
        # Review Focus 3: uno strumento con sole righe titolo conta solo nei titoli
        with open(os.path.join(tmp, "solo-titoli.csv"), "w", encoding="utf-8") as f:
            f.write("strumento;dimensione;voce;peso\nDE0007164600;titolo;SAP SE;100\n")
        rc, so, se = run_script_split(asset(*LT), "--composizione", os.path.join(tmp, "solo-titoli.csv"),
                                      "--posizioni", os.path.join(tmp, "broker.json"), "--json", "-", cwd=tmp)
        assert rc == 0, se[-300:]
        r = json.loads(so)
        assert r["copertura"] == {"settori": 0.0, "paesi": 0.0, "titoli": 1500 / tot} and r["settori"] == [] and r["titoli"][0]["peso"] == 1.0
        # il --dati del capitale umano come sorgente, con --posizioni ripetuto che somma
        dati = {"persona": {"profilo": "privato_stabile", "eta": 35},
                "posizioni": [{"asset_class": "azionario", "valore": 1000, "isin": "IE00B5BMR087"},
                              {"asset_class": "obbligazionario", "valore": 500, "strumento": "IT0005454241"}]}
        json.dump(dati, open(os.path.join(tmp, "cu.json"), "w", encoding="utf-8"))
        rc, so, se = run_script_split(asset(*LT), "--composizione", comp, "--posizioni", os.path.join(tmp, "cu.json"),
                                      "--posizioni", os.path.join(tmp, "cu.json"), "--json", "-", cwd=tmp)
        assert rc == 0, se[-300:]
        r = json.loads(so)
        assert r["controvalore_totale"] == 3000 and {p["chiave"]: p["valore"] for p in r["posizioni"]} == {"IE00B5BMR087": 2000, "IT0005454241": 1000}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 4: Scrivi il test `T16 look-through: errori con rc 1 (CSV, posizioni, valori), avvisi sul valore zero`**

```python
@test("T16 look-through: errori con rc 1 (CSV, posizioni, valori), avvisi sul valore zero")
def t_lt_errori():
    tmp = tempfile.mkdtemp()
    try:
        comp = os.path.join(FIXTURES, "composizione-look-through.csv")
        broker = _broker_look_through(tmp)
        def caso(*args):
            rc, so, se = run_script_split(asset(*LT), *args, cwd=tmp)
            assert rc == 1 and se.startswith("ERRORE:") and "ERRORE" not in so and "Traceback" not in se, (rc, se[-300:])
            return se
        assert "non trovato" in caso("--composizione", os.path.join(tmp, "no.csv"), "--posizioni", broker)
        with open(os.path.join(tmp, "colonne.csv"), "w", encoding="utf-8") as f:
            f.write("isin;settore;peso\nX;Energy;100\n")
        assert "colonne" in caso("--composizione", os.path.join(tmp, "colonne.csv"), "--posizioni", broker)
        with open(os.path.join(tmp, "dim.csv"), "w", encoding="utf-8") as f:
            f.write("strumento;dimensione;voce;peso\nIE00B4L5Y983;valuta;USD;100\n")
        assert "valuta" in caso("--composizione", os.path.join(tmp, "dim.csv"), "--posizioni", broker)
        json.dump({"persona": {}}, open(os.path.join(tmp, "senza.json"), "w", encoding="utf-8"))
        assert "manca la lista posizioni" in caso("--composizione", comp, "--posizioni", os.path.join(tmp, "senza.json"))
        json.dump({"posizioni": [{"isin": "IE00B4L5Y983", "valore": -1}]}, open(os.path.join(tmp, "neg.json"), "w", encoding="utf-8"))
        assert "posizioni[0]" in caso("--composizione", comp, "--posizioni", os.path.join(tmp, "neg.json"))
        json.dump({"posizioni": [{"isin": "IE00B4L5Y983", "valore": 0}]}, open(os.path.join(tmp, "zero.json"), "w", encoding="utf-8"))
        assert "controvalore totale" in caso("--composizione", comp, "--posizioni", os.path.join(tmp, "zero.json"))
        json.dump({"posizioni": [{"isin": "IE00B4L5Y983", "valore": 0}, {"isin": "IE00B5BMR087", "valore": 100}]},
                  open(os.path.join(tmp, "unozero.json"), "w", encoding="utf-8"))
        rc, so, se = run_script_split(asset(*LT), "--composizione", comp, "--posizioni", os.path.join(tmp, "unozero.json"), cwd=tmp)
        assert rc == 0 and "valore zero" in so and "IE00B4L5Y983" in so, (so[-400:], se[-300:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 5: Esegui e verifica che falliscano** — `python tests/run_tests.py --only "T16 look-through"` → i tre test nuovi FAIL (modulo assente).

- [ ] **Step 6: Implementa `look-through-portafoglio.py`** con le interfacce sopra. Docstring in testa come gli altri script: perché esiste, cosa legge, le regole (copertura, parte coperta, primi N come minimo, chiave dei titoli per nome), i limiti della spec §9, «Uso:». Aggiungi `LT` e registra lo script nelle liste che i test di igiene e d'interfaccia percorrono (`t_cli_help`, `t_formati_italiani`, `t_cli_utf8`, `t_dove_lavorare` e `tabella_test()`: cerca `importa-composizione-etf.py` in `tests/run_tests.py` e aggiungi la riga gemella dove l'elenco è esplicito; la tabella strumenti ↔ test del README si rigenera nel Task 5).

- [ ] **Step 7: Esegui e verifica** — `python tests/run_tests.py --only "T16 look-through"` → PASS; poi `--only "T9"` → PASS (interfaccia, formati, UTF-8, «Dove lavorare»).

- [ ] **Step 8: Commit** — `feat: look-through-portafoglio.py, settori, paesi e primi titoli aggregati per controvalore (T16)`

---

### Task 3: Il cruscotto disegna il look-through

**Files:**
- Modify: `skills/it-revisione/assets/genera-cruscotto.py` (`FIRME`, `ORDINE`, `_look_through()`, `componi_bundle()`, docstring del bundle, elenco `sezioni` in `main()`, messaggio dei tipi accettati)
- Modify: `skills/it-revisione/assets/cruscotto.html` (`sezioneLookThrough()`, `disegna()`)
- Test: `tests/run_tests.py` (`_json_esempio()`, `SEZIONI_CRUSCOTTO`, nuovo test, estensione di `t_t17_bundle`)

**Interfaces:**
- Consumes: il JSON del Task 2.
- Produces:
  - `FIRME`: `("look_through", lambda d: _ha(d, "copertura", "settori", "paesi", "titoli", "controvalore_totale"))` dopo `allocatore`.
  - `_look_through(lt) -> dict | None`: `{"copertura": {settori, paesi, titoli} (numeri), "settori": [{nome, peso}] (nome italiano), "paesi": [{nome, peso}] (i primi 10 per peso più, se restano altri, {"nome": "altri N paesi", "peso": somma}), "titoli": [{nome, peso}] (i primi 10), "quota_primi_titoli", "n_posizioni": len(posizioni), "n_senza_composizione": len(senza_composizione), "quota_senza_composizione": somma delle quote}`. Campi mancanti → `ErroreDati` «manca …» (via `campo`, `numero_di`, `lista_di`, `estrai`).
  - Bundle: chiave `look_through`; `main()` la elenca in `sezioni` dopo `allocazione`.
  - `cruscotto.html`: `sezioneLookThrough(l)` con `sezione("look_through", "Look-through", nota)`; `barre()` dei settori e dei paesi (etichette con la copertura: «Settori (copertura 88,2%)»); `tabella(["Titolo", "Peso"])` dei titoli con la riga finale «primi 10: X%»; `p.nota` «N posizioni senza composizione (X% del controvalore)» se `n_senza_composizione > 0`; nota del limite «i titoli sono i primi di ogni ETF: un minimo della concentrazione». In `disegna()` subito dopo `sezioneAllocazione`.

- [ ] **Step 1: Aggiungi il look-through ai JSON d'esempio e alla lista delle sezioni**: in `_json_esempio()` un lancio `("lt.json", OB("look-through-portafoglio.py"), ["--composizione", os.path.join(FIXTURES, "composizione-look-through.csv"), "--posizioni", "<broker-lt.json>"])`, preceduto da un lancio dell'importatore dei broker su `estratto-look-through.csv` → `broker-lt.json` (che **non** va in `_tutti_i_json()`, altrimenti sarebbe un secondo `broker`: tienilo fuori con un filtro sul nome, e scrivi il motivo in un commento). `SEZIONI_CRUSCOTTO` prende `"look_through"` dopo `"allocazione"`.

- [ ] **Step 2: Scrivi il test `T16 look-through: il cruscotto riconosce il JSON, il bundle non porta posizioni né ISIN, la sezione in pagina`**

```python
@test("T16 look-through: il cruscotto riconosce il JSON, il bundle non porta posizioni né ISIN, la sezione in pagina")
def t_lt_cruscotto():
    js = _json_esempio()
    rc, so, se, b, html = _cruscotto(js["alloc.json"], js["lt.json"])
    assert rc == 0, se[-300:]
    lt, r = b["look_through"], json.load(open(js["lt.json"], encoding="utf-8"))
    assert set(lt) == {"copertura", "settori", "paesi", "titoli", "quota_primi_titoli", "n_posizioni", "n_senza_composizione", "quota_senza_composizione"}
    assert lt["settori"][0] == {"nome": "Finanza", "peso": r["settori"][0]["peso"]} and lt["n_senza_composizione"] == 1
    assert lt["paesi"][0]["nome"] == "Stati Uniti" and lt["titoli"][0]["nome"] == "Apple Inc."
    for vietato in ("IE00B4L5Y983", "DE0007164600", "SAP SE", "iShares Core MSCI World", "BTP Futura"):
        assert vietato not in html, vietato
    assert "look_through" in so and "lt.json → look_through" in so
    # Review Focus 5: un JSON di prima di una modifica delle chiavi si rifiuta con «manca …»
    def senza(d):
        del d["quota_primi_titoli"]
    rc, so, se, _, _ = _cruscotto(_json_variante("lt.json", senza))
    assert rc == 1 and "manca quota_primi_titoli" in se and "variante-lt.json" in se, se[-300:]
    sync_playwright, lancia = browser()
    with sync_playwright() as p:
        br = lancia(p)
        try:
            page, errori, eccezioni, _ = _apri_cruscotto(br, html)
            assert errori == [] and eccezioni == [], (errori, eccezioni)
            assert page.locator("#sez-look_through svg").count() >= 2
            testo = page.inner_text("#sez-look_through")
            assert "1 posizione senza composizione" in testo and "minimo della concentrazione" in testo, testo[:800]
            assert formato_it_percento(lt["copertura"]["settori"]) in testo, testo[:800]
        finally:
            br.close()
```

- [ ] **Step 3: Estendi `t_t17_bundle`**: tra i file del bundle c'è ora anche `lt.json`; conferma che l'asserzione «nessuna posizione dell'estratto» copra anche i nomi e gli ISIN di `estratto-look-through.csv` (aggiungili alla lista dei vietati, con un commento).

- [ ] **Step 4: Esegui e verifica che falliscano** — `python tests/run_tests.py --only "cruscotto"` → `t_lt_cruscotto` FAIL («non è un output riconosciuto»), `t_t17_riconosci` FAIL (lt.json senza firma), `t_t17_browser_rendering` FAIL (manca `#sez-look_through`).

- [ ] **Step 5: Implementa** in `genera-cruscotto.py` e `cruscotto.html`. Il messaggio dei tipi accettati di `leggi_sorgenti()` nomina anche il look-through.

- [ ] **Step 6: Esegui e verifica** — `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python tests/run_tests.py --only "cruscotto"` → tutti PASS; `--only "T16 look-through"` → PASS.

- [ ] **Step 7: Controllo a occhio** — screenshot a 1200 px e a 375 px della sezione, chiaro e scuro, nello scratchpad: etichette dei settori e dei paesi leggibili, tabella dei titoli entro la larghezza.

- [ ] **Step 8: Commit** — `feat: la sezione Look-through nel cruscotto, settori, paesi e primi titoli con la copertura (T16)`

---

### Task 4: Skill, reference, README, CHANGELOG, ROADMAP

**Files:**
- Modify: `skills/it-pianificazione-obiettivi/SKILL.md` (Step 8, elenco degli asset, `version: "0.24"`), `references/composizione-etf.md`, `references/capitale-umano.md`
- Modify: `skills/it-revisione/SKILL.md` (passo 3, passo 6, contratto di input, `version: "0.9"`)
- Modify: `README.md`, `CHANGELOG.md` («Non rilasciato», storia delle due skill), `ROADMAP.md`
- Test: `tests/run_tests.py`

- [ ] **Step 1: Scrivi il test `T16 look-through: skill, reference, revisione, README, CHANGELOG e ROADMAP allineati`**

```python
@test("T16 look-through: skill, reference, revisione, README, CHANGELOG e ROADMAP allineati")
def t_lt_documentazione():
    ob = os.path.join(SKILLS, "it-pianificazione-obiettivi")
    skill = open(os.path.join(ob, "SKILL.md"), encoding="utf-8").read()
    step8 = skill.split("Step 8")[1]
    assert "${CLAUDE_SKILL_DIR}/assets/look-through-portafoglio.py" in step8 and "--posizioni" in step8 and "--isin" in step8
    assert 'version: "0.24"' in skill and "look-through-portafoglio.py" in skill.split("## Riferimenti")[1]
    ref = open(os.path.join(ob, "references", "composizione-etf.md"), encoding="utf-8").read()
    for parola in ("look-through", "titolo", "ISIN", "a mano", "copertura", "minimo"):
        assert parola in ref, parola
    assert "isin" in open(os.path.join(ob, "references", "capitale-umano.md"), encoding="utf-8").read()
    rev = open(os.path.join(SKILLS, "it-revisione", "SKILL.md"), encoding="utf-8").read()
    assert 'version: "0.9"' in rev
    contratto = rev.split("### Contratto di input")[1].split("\n## ")[0]
    assert "look-through-portafoglio.py" in contratto and "senza_composizione" in contratto
    assert "look-through" in rev.split("### 3. Avanzamento")[1].split("### 4.")[0].lower()
    assert "look-through" in rev.split("### 6. Cruscotto grafico")[1].split("\n## ")[0].lower()
    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    assert "Tutti i 18 script" in readme and "look-through-portafoglio.py" in readme
    assert "look-through" in readme.split("### Dove vanno i tuoi dati")[1].split("\n### ")[0].lower()
    assert "look-through" in open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8").read().split("## v0.11.0")[0].lower()
    t16 = open(os.path.join(ROOT, "ROADMAP.md"), encoding="utf-8").read().split("**T16")[1]
    assert "[x] **Look-through del portafoglio**" in t16 and "2026-11-01-look-through" in t16, t16[:1200]
```

- [ ] **Step 2: Esegui e verifica che fallisca** — `python tests/run_tests.py --only "T16 look-through: skill"` → FAIL.

- [ ] **Step 3: Scrivi la documentazione.** Step 8 di `it-pianificazione-obiettivi`: dopo il blocco dell'importatore, il paragrafo «**Look-through del portafoglio**» con il comando della spec §2.1, la raccomandazione dell'ISIN come `--strumento` (`--isin`) quando le posizioni vengono da `importa-estratto-broker.py --json`, cosa si riporta (copertura accanto a ogni numero, titoli come minimo), «legge e riporta, non cambia i target»; l'asset in «Riferimenti»; `version: "0.24"`. `composizione-etf.md`: sezione «Il look-through del portafoglio» (chiave ISIN, righe `titolo` con il peso nel fondo, posizioni dirette a mano con l'esempio del BTP, copertura, limiti della spec §9) nell'indice; la frase «I paesi oggi non entrano in nessun calcolo» diventa il rimando al look-through; «Il file composizione.csv» mostra anche una riga `titolo`. `capitale-umano.md`: il campo `isin` delle posizioni e l'ordine di confronto. `it-revisione`: passo 3, dominio allocazione («con `composizione.csv` e il JSON dell'estratto, `look-through-portafoglio.py --json` …»); passo 6 con `lt.json` tra i `--from`; riga «Look-through» nel contratto di input (campi `settori[]`, `paesi[]`, `titoli[]`, `copertura`, `senza_composizione[]`; «report, nessuna cella»); `version: "0.9"`. Entrambi i `SKILL.md` restano sotto le 500 righe.

- [ ] **Step 4: README, CHANGELOG, ROADMAP.** README: «Tutti i 18 script»; la frase sul look-through in «Cosa fa» di `it-pianificazione-obiettivi` (tabella delle skill, v0.24) e di `it-revisione` (v0.9); un punto in «Dove vanno i tuoi dati» (il look-through legge il JSON dell'estratto e il CSV, scrive solo aggregati; nel cruscotto non vanno le posizioni); conteggio dei test; tabella strumenti ↔ test rigenerata con `python tests/run_tests.py --tabella-test`. CHANGELOG: voce «**Look-through del portafoglio** (T16)» in «Non rilasciato» (script, righe `titolo`, `--isin`, sezione del cruscotto, limiti) e le righe v0.24 e v0.9 nella storia delle skill. ROADMAP: la voce spuntata con spec e piano; nei «Sviluppi successivi» di T16 le tre evolutive della spec §8.

- [ ] **Step 5: Esegui la suite completa** — `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python tests/run_tests.py` → tutti PASS, 0 saltati; `claude plugin validate . --strict` se disponibile.

- [ ] **Step 6: Commit** — `docs: look-through in Step 8, reference, revisione, cruscotto, README, CHANGELOG e ROADMAP (T16)`

---

### Task 5: Revisione finale

- [ ] **Step 1: Rileggi la spec con il codice davanti** (§3.2 chiavi del JSON, §3.4 formule, §4 bundle, §9 limiti nel report e nella reference). Scrivi in `docs/sviluppo/revisioni/esito-t16c.json` cosa è stato applicato e cosa no, con il motivo (formato di `esito-t16a.json`).
- [ ] **Step 2: Mutanti** — tre mutazioni e la suite che le uccide: (a) nel look-through `peso / V_tot` al posto di `/ V_d` (copertura ignorata); (b) `chiave_titolo` senza i suffissi (Apple non si somma); (c) nel cruscotto `posizioni` lasciata nel bundle. Risultato nel file dell'esito.
- [ ] **Step 3: Commit** — `docs: esito della revisione finale del look-through (T16)`
