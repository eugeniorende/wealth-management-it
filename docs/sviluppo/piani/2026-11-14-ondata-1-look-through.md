# Ondata 1, look-through (regioni, ISIN dei titoli, valuta): piano di implementazione

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Il look-through del portafoglio dice anche in quali regioni e in quali valute sono investiti gli ETF messi insieme, e somma lo stesso titolo tra ETF diversi con l'ISIN quando l'emittente lo riporta.

**Architecture:** Le regioni si derivano dai paesi al momento dell'aggregazione, senza toccare `composizione.csv`. L'ISIN dei titoli e la valuta entrano nel CSV: una quinta colonna `isin` e una dimensione `valuta` in più, con i tre lettori (`capitale-umano.py`, `look-through-portafoglio.py`, l'importatore) che continuano a leggere i formati a tre e a quattro colonne. Il cruscotto disegna le due dimensioni nuove e accetta ancora il JSON della 0.12.0.

**Tech Stack:** Python ≥ 3.11, libreria standard; `cli()`, `errore()`, `numero()`, `euro()`, `pct()`, `scrivi_json()` di `motore_bootstrap.py`; le tabelle dell'importatore caricate dal look-through con `importlib` (come oggi `SETTORI_GICS`, `PAESI`, `normalizza`); runner `tests/run_tests.py`; Playwright per il test nel browser.

**Spec:** `docs/sviluppo/specs/2026-11-14-completamento-roadmap-design.md`, §7 (regole comuni) e §7.3, §7.4, §7.5 (citata sotto come «spec §N»).

## Global Constraints

- **Compatibilità** (spec §2, obiettivo 4): `composizione.csv` a tre colonne (`strumento;settore;peso`) e a quattro (`strumento;dimensione;voce;peso`) si legge come oggi, con gli stessi numeri; il cruscotto accetta un JSON del look-through senza `regioni`, `valute` e `quota_euro`.
- **Nessun «altro» inventato**: ciò che non si sa resta fuori dai pesi, con la copertura accanto; un nome o un codice non riconosciuto ferma lo script con l'elenco, come per settori e paesi.
- **Nessuna rete negli script**; i file degli emittenti non entrano nel repository: le fixture sono sintetiche.
- **Il cruscotto non porta posizioni dell'utente**: né nomi né ISIN delle posizioni; gli ISIN dei titoli degli ETF non entrano nel bundle.
- **Interfaccia comune**: exit 0, 1 con `ERRORE:` su stderr, 2 per la riga di comando; formati italiani con `numero()`, `euro()`, `pct()`; `open()` sempre con `encoding=`.
- **Nomi dei test**: `T16 look-through: …`, nella sezione del look-through di `tests/run_tests.py`. Costanti già definite: `CE`, `CU`, `LT`; helper `_broker_look_through(tmp)`, `_cruscotto(*sorgenti, extra=())`, `_json_esempio()`, `_json_variante(nome, modifica)`, `browser()`, `_apri_cruscotto(...)`.
- **Test**: suite completa con `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium RICHIEDI_BROWSER=1 RICHIEDI_LIBREOFFICE=1 python3 tests/run_tests.py`; un gruppo con `--only`.
- **README dopo ogni test nuovo**: conteggio dei test (`grep -c '^@test' tests/run_tests.py`) e tabella `--tabella-test`, prima del commit.
- **Commit** in italiano, con le due righe di attribuzione della sessione; `(T16)` in coda al messaggio.

## Review Focus

1. **Righe a quattro campi sotto un'intestazione a cinque** (l'utente aggiunge una riga a mano e dimentica il `;` finale): i tre lettori la leggono come una riga con l'ISIN vuoto. Test nel Task 2.
2. **Un ISIN scritto a mano in minuscolo o con spazi** (` us0000000011 `): si normalizza prima di validarlo, e unisce i titoli come quello maiuscolo. Test nel Task 2.
3. **Valuta presente solo su una parte del fondo**: sotto la metà dei titoli la dimensione non si scrive, con l'avviso, come per settori e paesi; un segnaposto (`-`) conta come valuta non classificata. Test nel Task 3.
4. **Reimportare senza `--copertura` uno strumento importato prima con la copertura**: tornano le valute dei titoli, senza residui della riga unica. Test nel Task 3.
5. **Uno strumento con le sole righe `valuta`** (un conto in valuta o un BTP descritto a mano): conta nelle valute e in nessun'altra dimensione; se l'euro manca tra le valute coperte, `quota_euro` è 0 e non `null`. Test nel Task 4.

---

### Task 1: Regioni derivate dai paesi

**Files:**
- Modify: `skills/it-pianificazione-obiettivi/assets/look-through-portafoglio.py` (tabella `REGIONI` dopo le costanti, `aggrega()`, `stampa()`, docstring)
- Test: `tests/run_tests.py` (nuovo test dopo `t_lt_chiave_titolo`; `t_lt_valori_chiusi`)

**Interfaces:**
- Produces:
  - `REGIONI: dict[str, tuple[str, tuple[str, ...]]]`, nell'ordine `nord_america`, `america_latina`, `europa`, `asia`, `oceania`, `africa`, `antartide`; valore: nome italiano («Nord America», «America Latina e Caraibi», «Europa», «Asia», «Oceania», «Africa», «Antartide») e codici ISO. Ogni codice di `PAESI` sta in una sola regione.
  - `regione_di(codice: str) -> str`: la chiave della regione di un codice ISO.
  - `aggrega()` aggiunge `"regioni": [{"voce": str, "nome": str, "peso": float}]`, per peso decrescente, e `copertura["regioni"]`, uguale a `copertura["paesi"]`.

- [ ] **Step 1: Leggi la classificazione alla fonte**: «Standard country or area codes for statistical use (M49)», vista «Geographic Regions», `https://unstats.un.org/unsd/methodology/m49/`. Le Americhe si dividono nelle sottoregioni «Northern America» e «Latin America and the Caribbean». Due scelte fuori dallo standard, decise dalla spec §7.3: Taiwan (`TW`), che M49 non elenca, va in `asia`; l'Antartide (`AQ`) ha la voce `antartide`.

- [ ] **Step 2: Scrivi il test**

```python
@test("T16 look-through: regioni derivate dai paesi (standard ONU M49), ogni codice ISO in una sola regione")
def t_lt_regioni():
    m = carica_modulo(asset(*LT))
    codici = [c for _, cc in m.REGIONI.values() for c in cc]
    assert sorted(codici) == sorted(m.PAESI) and len(codici) == len(set(codici)) == 249
    assert list(m.REGIONI) == ["nord_america", "america_latina", "europa", "asia", "oceania", "africa", "antartide"]
    for codice, regione in (("US", "nord_america"), ("CA", "nord_america"), ("BM", "nord_america"), ("MX", "america_latina"),
                            ("BR", "america_latina"), ("GB", "europa"), ("RU", "europa"), ("TR", "asia"), ("IL", "asia"),
                            ("CY", "asia"), ("SA", "asia"), ("JP", "asia"), ("TW", "asia"), ("AU", "oceania"),
                            ("ZA", "africa"), ("EG", "africa"), ("AQ", "antartide")):
        assert m.regione_di(codice) == regione, (codice, m.regione_di(codice))
    tmp = tempfile.mkdtemp()
    try:
        rc, so, se = run_script_split(asset(*LT), "--composizione", os.path.join(FIXTURES, "composizione-look-through.csv"),
                                      "--posizioni", _broker_look_through(tmp), "--json", "lt.json", cwd=tmp)
        assert rc == 0, se[-300:]
        r = json.load(open(os.path.join(tmp, "lt.json"), encoding="utf-8"))
        V_p = 13000 + 19500 + 2850                                                  # i due ETF e il BTP hanno i paesi
        regioni = {x["voce"]: x for x in r["regioni"]}
        assert abs(regioni["nord_america"]["peso"] - (13000 * .60 + 19500) / V_p) < 1e-12
        assert abs(regioni["europa"]["peso"] - (13000 * .15 + 2850) / V_p) < 1e-12 and regioni["europa"]["nome"] == "Europa"
        assert abs(regioni["asia"]["peso"] - 13000 * .25 / V_p) < 1e-12
        assert [x["voce"] for x in r["regioni"]] == ["nord_america", "europa", "asia"]
        assert abs(sum(x["peso"] for x in r["regioni"]) - 1) < 1e-12 and r["copertura"]["regioni"] == r["copertura"]["paesi"]
        assert "Per regione: Nord America 77,2% · Europa 13,6% · Asia 9,2%" in so, so
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 3: In `t_lt_valori_chiusi` aggiorna il confronto esatto della copertura** del caso con le sole righe `titolo`: `r["copertura"] == {"settori": 0.0, "paesi": 0.0, "titoli": 1500 / tot, "regioni": 0.0}`, e aggiungi `and r["regioni"] == []`.

- [ ] **Step 4: Lancia e verifica il fallimento**

Run: `python3 tests/run_tests.py --only "regioni derivate"`
Expected: FAIL con `AttributeError: … has no attribute 'REGIONI'`.

- [ ] **Step 5: Implementa.** `REGIONI` con i 249 codici, con la fonte, la data di lettura e le due scelte fuori standard nel commento; `regione_di()`; in `aggrega()` le regioni si sommano dai pesi dei paesi già calcolati; in `stampa()`, sotto la riga dei paesi, `   Per regione: Nord America 77,2% · …` (solo se ci sono paesi). Il docstring nomina le regioni tra le regole.

- [ ] **Step 6: Lancia i test**

Run: `python3 tests/run_tests.py --only "T16 look-through"`
Expected: PASS, tranne `t_lt_cruscotto`, che il Task 5 aggiorna, se confronta l'insieme esatto delle chiavi di `copertura` (se fallisce qui, annotalo e prosegui).

- [ ] **Step 7: README (conteggio e tabella dei test) e commit**

```bash
git add skills/it-pianificazione-obiettivi/assets/look-through-portafoglio.py tests/run_tests.py README.md
git commit -m "feat: regioni geografiche nel look-through, derivate dai paesi (T16)"
```

### Task 2: ISIN dei titoli, quinta colonna e regola di somma

**Files:**
- Create: `tests/fixtures/composizione-look-through-v5.csv`
- Modify: `skills/it-pianificazione-obiettivi/assets/importa-composizione-etf.py` (`_INTESTAZIONE_OUT`, `leggi_out()`, `righe_strumento()`, `stampa()`, `main()`, docstring)
- Modify: `skills/it-pianificazione-obiettivi/assets/look-through-portafoglio.py` (`leggi_composizione()`, `aggrega()`)
- Test: `tests/run_tests.py` (due test nuovi dopo `t_lt_valori_chiusi`; righe attese di `t_ce_csv`, del test sui file reali di novembre 2026 e di `t_lt_importatore_titoli`)

**Interfaces:**
- Produces:
  - `_INTESTAZIONE_OUT = "strumento;dimensione;voce;peso;isin"`. `righe_strumento()` scrive sempre cinque campi; il quinto è pieno solo sulle righe `titolo` con `isin` nel JSON dell'importatore.
  - `leggi_out(path) -> tuple[list[str], list[tuple[str | None, list[str]]], str | None]`: il terzo valore, oggi un booleano, diventa il formato trovato: `None` (file assente), `"settore"`, `"quattro"`, `"cinque"`. Le righe di un file a quattro colonne tornano con il quinto campo vuoto. `stampa(composizioni, out, conservati, formato)` aggiunge, per `"quattro"`: `   Il file esistente aveva quattro colonne: aggiunta la colonna isin, stesse righe.`
  - Look-through: `ISIN_TITOLO = re.compile(r"[A-Z]{2}[A-Z0-9]{9}[0-9]")`, usata con `fullmatch` dopo `strip().upper()`. `leggi_composizione()` accetta le tre intestazioni e, per ogni strumento, ritorna in più `"isin": {nome del titolo: ISIN}` (non è una dimensione: resta fuori da `DIMENSIONI`). Un valore non vuoto che non è un ISIN: `errore("--composizione: ISIN {valore!r} malformato per il titolo {nome!r} ({strumento})")`. Il campo si ignora sulle righe che non sono `titolo`.
  - `aggrega()`: due righe `titolo` sono lo stesso titolo se hanno lo stesso ISIN oppure la stessa `chiave_titolo()` (componenti connesse). Ogni titolo aggregato prende `"isin": list[str]`, ordinata, vuota se nessuna riga del gruppo ha l'ISIN. Nome, `da` e `diretto` come oggi.

- [ ] **Step 1: Crea la fixture `tests/fixtures/composizione-look-through-v5.csv`**

```
# Fixture sintetica a cinque colonne per il look-through: pesi illustrativi, ISIN dei titoli inventati.
strumento;dimensione;voce;peso;isin
IE00B4L5Y983;settore;Information Technology;30,00;
IE00B4L5Y983;settore;Financials;20,00;
IE00B4L5Y983;settore;Health Care;50,00;
IE00B4L5Y983;paese;US;60,00;
IE00B4L5Y983;paese;JP;25,00;
IE00B4L5Y983;paese;GB;15,00;
IE00B4L5Y983;valuta;USD;60,00;
IE00B4L5Y983;valuta;JPY;25,00;
IE00B4L5Y983;valuta;GBP;15,00;
IE00B4L5Y983;titolo;APPLE INC;5,00;US0000000011
IE00B4L5Y983;titolo;TAIWAN SEMICONDUCTOR MANUFACTURING;4,00;US0000000029
IE00B4L5Y983;titolo;NESTLE SA;3,00;
IE00B5BMR087;settore;Information Technology;40,00;
IE00B5BMR087;settore;Financials;60,00;
IE00B5BMR087;paese;US;100,00;
IE00B5BMR087;valuta;USD;100,00;
IE00B5BMR087;titolo;Apple Inc.;7,00;
IE00B5BMR087;titolo;TSMC ADR;2,00;US0000000029
IE00B5BMR087;titolo;ALPHABET INC CLASS A;3,00;US0000000037
IE00B5BMR087;titolo;ALPHABET INC CLASS C;2,50;US0000000045
IT0005454241;paese;IT;100,00;
IT0005454241;valuta;EUR;100,00;
```

Le righe `valuta` servono ai Task 4 e 5. In questo task il look-through le deve già tollerare: nella mappa delle dimensioni di `leggi_composizione()` aggiungi `"valuta"` con destinazione «saltata» (il Task 4 la aggrega).

- [ ] **Step 2: Scrivi il test dell'importatore e dei lettori**

```python
@test("T16 look-through: composizione.csv a cinque colonne con l'ISIN dei titoli, file a tre e a quattro colonne ancora letti")
def t_lt_colonna_isin():
    cu, lt = carica_modulo(asset(*CU)), carica_modulo(asset(*LT))
    tmp = tempfile.mkdtemp()
    try:
        out = os.path.join(tmp, "composizione.csv")
        shutil.copy(os.path.join(FIXTURES, "composizione-look-through.csv"), out)    # quattro colonne, come dalla 0.12.0
        rc, so, se = run_script_split(asset(*CE), "--file", os.path.join(FIXTURES, "composizione-amundi-fr.csv"), "--isin", "LU0000000001",
                                      "--file", os.path.join(FIXTURES, "composizione-ishares-en.csv"), "--isin", "IE0000000002",
                                      "--out", out, cwd=tmp)
        assert rc == 0 and "quattro colonne" in so, (so[-400:], se[-300:])
        dati = [r for r in open(out, encoding="utf-8-sig").read().splitlines() if r and not r.startswith("#")]
        assert dati[0] == "strumento;dimensione;voce;peso;isin" and all(r.count(";") == 4 for r in dati), dati[:3]
        assert "LU0000000001;titolo;ALPHA CORP;30,00;US0000000001" in dati          # Amundi ha la colonna «Code ISIN»
        assert "IE0000000002;titolo;ALPHA CORP;30,00;" in dati                      # iShares non la ha: campo vuoto
        assert "IE00B4L5Y983;titolo;APPLE INC;5,00;" in dati and "IT0005454241;paese;IT;100,00;" in dati   # righe di prima
        assert abs(cu.leggi_composizione(out)["IE00B4L5Y983"]["Health Care"] - 0.5) < 1e-9
        comp = lt.leggi_composizione(out)
        assert comp["LU0000000001"]["isin"]["ALPHA CORP"] == "US0000000001" and comp["IE0000000002"]["isin"] == {}
        rc, so, se = run_script_split(asset(*CE), "--file", os.path.join(FIXTURES, "composizione-ishares-en.csv"), "--isin", "IE0000000002",
                                      "--out", out, cwd=tmp)
        assert rc == 0 and "quattro colonne" not in so, so[-300:]
        assert open(out, encoding="utf-8-sig").read().count("IE0000000002;titolo;") == 6
        # Review Focus 1 e 2: una riga a mano senza il quinto campo, un ISIN in minuscolo con gli spazi
        with open(out, "a", encoding="utf-8") as f:
            f.write("DE0007164600;titolo;SAP SE;100\nDE0007164601;titolo;Apple;100; us0000000011 \n")
        comp = lt.leggi_composizione(out)
        assert comp["DE0007164600"]["isin"] == {} and comp["DE0007164601"]["isin"] == {"Apple": "US0000000011"}
        assert "DE0007164600" not in cu.leggi_composizione(out)                     # sole righe titolo: nessun settore
        with open(out, "a", encoding="utf-8") as f:
            f.write("DE0007164602;titolo;Storto;100;US123\n")
        rc, so, se = run_script_split(asset(*LT), "--composizione", out, "--posizioni", _broker_look_through(tmp), cwd=tmp)
        assert rc == 1 and "ISIN" in se and "US123" in se and "Traceback" not in se, se[-300:]
        # il formato a tre colonne resta leggibile dai due lettori
        tre = os.path.join(tmp, "tre.csv")
        open(tre, "w", encoding="utf-8").write("strumento;settore;peso\nIE00B4L5Y983;Energy;100\n")
        assert cu.leggi_composizione(tre) == {"IE00B4L5Y983": {"Energy": 1.0}} and lt.leggi_composizione(tre)["IE00B4L5Y983"]["settori"] == {"Energy": 1.0}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 3: Scrivi il test della regola di somma**

```python
@test("T16 look-through: titoli uniti per ISIN o per nome (componenti connesse), ISIN dei gruppi nel JSON")
def t_lt_titoli_isin():
    tmp = tempfile.mkdtemp()
    try:
        rc, so, se = run_script_split(asset(*LT), "--composizione", os.path.join(FIXTURES, "composizione-look-through-v5.csv"),
                                      "--posizioni", _broker_look_through(tmp), "--json", "lt.json", cwd=tmp)
        assert rc == 0, se[-300:]
        r = json.load(open(os.path.join(tmp, "lt.json"), encoding="utf-8"))
        V_s = 13000 + 19500
        t = {x["nome"]: x for x in r["titoli"]}
        assert [x["nome"] for x in r["titoli"]] == ["Apple Inc.", "ALPHABET INC CLASS A", "TAIWAN SEMICONDUCTOR MANUFACTURING", "NESTLE SA"]
        # una riga con l'ISIN e una senza, stesso nome: un titolo solo
        assert abs(t["Apple Inc."]["peso"] - (13000 * .05 + 19500 * .07) / V_s) < 1e-12 and t["Apple Inc."]["isin"] == ["US0000000011"]
        # nomi che la chiave non unisce, stesso ISIN: un titolo solo
        tsmc = t["TAIWAN SEMICONDUCTOR MANUFACTURING"]
        assert abs(tsmc["peso"] - (13000 * .04 + 19500 * .02) / V_s) < 1e-12 and tsmc["isin"] == ["US0000000029"]
        assert tsmc["da"] == ["IE00B4L5Y983", "IE00B5BMR087"]
        # due classi di azioni, due ISIN, stessa chiave del nome: restano un titolo
        assert abs(t["ALPHABET INC CLASS A"]["peso"] - 19500 * .055 / V_s) < 1e-12
        assert t["ALPHABET INC CLASS A"]["isin"] == ["US0000000037", "US0000000045"]
        assert t["NESTLE SA"]["isin"] == [] and r["n_titoli_aggregati"] == 4
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 4: Aggiorna i test esistenti.** Quelli che confrontano righe intere di `composizione.csv` scritte dall'importatore (`t_ce_csv`, il test sui file reali di novembre 2026, `t_lt_importatore_titoli`): l'intestazione attesa è quella a cinque colonne e ogni riga prende il quinto campo (un `;` in coda, oppure l'ISIN dove la fixture ha la colonna: lo XLSX di Xtrackers). I CSV che i test scrivono a mano come input restano a quattro colonne: provano la compatibilità. In `t_lt_errori` la dimensione sconosciuta non può più essere `valuta`, che il look-through da questo task tollera: il CSV `dim.csv` usa `IE00B4L5Y983;rating;AAA;100` e l'asserzione diventa `"rating" in caso(...)`.

- [ ] **Step 5: Lancia e verifica il fallimento**

Run: `python3 tests/run_tests.py --only "cinque colonne"`, poi `--only "uniti per ISIN"`
Expected: FAIL; il primo perché l'intestazione scritta è ancora a quattro colonne, il secondo perché il lettore rifiuta l'intestazione a cinque.

- [ ] **Step 6: Implementa l'importatore**: intestazione, `righe_strumento()` a cinque campi, `leggi_out()` con il formato e il quinto campo aggiunto alle righe conservate, messaggio in `stampa()`, docstring.

- [ ] **Step 7: Implementa il look-through**: le tre intestazioni in `leggi_composizione()`, la mappa `isin` per strumento con la validazione, le componenti connesse in `aggrega()` (una struttura union-find sui nodi «ISIN» e «chiave del nome» basta).

- [ ] **Step 8: Lancia i test**

Run: `python3 tests/run_tests.py --only "T16"`
Expected: PASS (salvo `t_lt_cruscotto`, come nel Task 1). `t_lt_valori_chiusi`, che gira sulla fixture a quattro colonne, deve passare senza modifiche ai pesi: è la prova che i numeri di oggi non cambiano.

- [ ] **Step 9: README (conteggio e tabella dei test) e commit**

```bash
git add tests/fixtures/composizione-look-through-v5.csv skills/it-pianificazione-obiettivi/assets tests/run_tests.py README.md
git commit -m "feat: ISIN dei titoli in composizione.csv, titoli sommati per ISIN o per nome (T16)"
```

### Task 3: La valuta nell'importatore

**Files:**
- Modify: `skills/it-pianificazione-obiettivi/assets/importa-composizione-etf.py` (`SINONIMI_COLONNE`, tabelle delle valute, `_DIMENSIONI`, `componi()`, `_finalizza()`, `_esclusi()`, `righe_strumento()`, `stampa()`, `main()`, docstring)
- Test: `tests/run_tests.py` (nuovo test dopo `t_lt_titoli_isin`)

**Interfaces:**
- Produces:
  - `SINONIMI_COLONNE["valuta"] = ("market currency", "valuta di mercato", "marktwährung", "devise de cotation", "currency", "valuta", "divisa", "währung", "devise", "currency code")`. L'ordine conta: con due colonne candidate vince la valuta di negoziazione del titolo. «Cambio» non è un sinonimo: nel file italiano di iShares è la borsa.
  - `VALUTE: dict[str, str]`, codice ISO 4217 → nome italiano, almeno per: USD Dollaro USA, EUR Euro, JPY Yen giapponese, GBP Sterlina britannica, CHF Franco svizzero, CAD Dollaro canadese, AUD Dollaro australiano, NZD Dollaro neozelandese, SEK Corona svedese, NOK Corona norvegese, DKK Corona danese, HKD Dollaro di Hong Kong, SGD Dollaro di Singapore, ILS Nuovo shekel israeliano, CNY Renminbi cinese, TWD Nuovo dollaro taiwanese, KRW Won sudcoreano, INR Rupia indiana, IDR Rupia indonesiana, MYR Ringgit malese, PHP Peso filippino, THB Baht thailandese, BRL Real brasiliano, MXN Peso messicano, CLP Peso cileno, COP Peso colombiano, PEN Sol peruviano, ZAR Rand sudafricano, EGP Sterlina egiziana, TRY Lira turca, PLN Zloty polacco, CZK Corona ceca, HUF Fiorino ungherese, SAR Riyal saudita, AED Dirham degli Emirati, QAR Riyal del Qatar, KWD Dinaro kuwaitiano, RUB Rublo russo.
  - `CODICI_VALUTA: frozenset[str]`: tutti i codici attivi di ISO 4217 (lista «List One» dell'agenzia di mantenimento, SIX), letti alla fonte e citati nel commento con la data; contiene le chiavi di `VALUTE`.
  - `ALIAS_VALUTE = {"GBX": "GBP", "ZAC": "ZAR", "ILA": "ILS", "CNH": "CNY", "RMB": "CNY"}`, applicata dopo `strip().upper()` (così `GBp` è già `GBP`).
  - `codice_valuta(valore) -> str | None`: il codice ISO, o `None` se il valore non è un codice noto. `nome_valuta(codice) -> str`: il nome italiano, o il codice stesso.
  - `_DIMENSIONI = (("settore", "settori"), ("paese", "paesi"), ("valuta", "valute"))`. Il risultato di `componi()` prende `"valute": {codice: frazione}` (rinormalizzate a 1, per peso decrescente), `"copertura_cambio": str | None`, `esclusi["valuta_non_classificato"]` e `colonne["valuta"]`. Le obbligazioni contano nelle valute. Codici non riconosciuti: nello stesso `ERRORE:` di settori e paesi, come `valute non riconosciute: ABC (10,00%)`.
  - `componi(path, strumento, forzato=None, copertura=None)`: con `copertura` (un codice ISO) le valute del file si ignorano, `valute = {copertura: 1.0}`, `copertura_cambio = copertura`.
  - `--copertura CHIAVE=VALUTA` (`action="append"`): chiave che non è uno degli `--strumento` della riga di comando, o valuta che non è un codice, sono errori di riga di comando (`args.parser.error`, codice 2).
  - `righe_strumento()` scrive le righe `valuta` dopo i paesi e prima dei titoli; il commento dello strumento aggiunge `; copertura del cambio in EUR dichiarata dall'utente` quando c'è.
  - Avvisi nuovi: `il file non ha la colonna della valuta: valute non scritte`; `valuta non classificata per X del fondo, sopra la soglia del 5%: …`; senza `--copertura`, se il preambolo o il nome del file contengono una di `PAROLE_COPERTURA = ("hedged", "hedge", "copertura del cambio", "con copertura", "couvert", "couverte", "währungsgesichert", "abgesichert")`: `il file sembra di una classe con copertura del cambio: le valute dei titoli non sono l'esposizione; se è così reimporta con --copertura <strumento>=EUR`.
  - `stampa()`: riga `   Valute: Dollaro USA 50,51% · …` (le prime cinque).

- [ ] **Step 1: Scrivi il test**

```python
@test("T16 look-through: l'importatore legge la valuta dei titoli (quattro lingue, «Cambio» è la borsa), unità minori, --copertura")
def t_lt_importatore_valuta():
    m = carica_modulo(asset(*CE))
    r2 = lambda d: {k: round(v * 100, 2) for k, v in d.items()}  # noqa: E731
    F = lambda n: os.path.join(FIXTURES, n)                       # noqa: E731
    en = m.componi(F("composizione-ishares-en.csv"), "X")
    assert en["colonne"]["valuta"] == "Currency" and en["copertura_cambio"] is None
    assert r2(en["valute"]) == {"USD": 50.51, "JPY": 15.15, "GBP": 15.15, "KRW": 10.10, "CAD": 9.09}, en["valute"]
    it = m.componi(F("composizione-ishares-it-2026-11.csv"), "X")
    assert it["colonne"]["valuta"] == "Valuta di mercato", it["colonne"]            # non «Cambio», che è la borsa
    assert r2(it["valute"]) == {"USD": 50.51, "GBP": 15.15, "JPY": 15.15, "HKD": 10.10, "CAD": 9.09}, it["valute"]
    assert m.componi(F("composizione-ishares-it.csv"), "X")["colonne"]["valuta"] == "Valuta"
    de = m.componi(F("composizione-xtrackers-de.csv"), "X")
    assert de["colonne"]["valuta"] == "Währung" and r2(de["valute"])["USD"] == 50.51
    fr = m.componi(F("composizione-amundi-fr.csv"), "X")
    assert fr["valute"] == {} and any("colonna della valuta" in a for a in fr["avvisi"]), fr["avvisi"]
    assert m.codice_valuta(" gbx ") == "GBP" and m.codice_valuta("CNH") == "CNY" and m.codice_valuta("Cambio") is None
    assert m.nome_valuta("USD") == "Dollaro USA" and set(m.VALUTE) <= m.CODICI_VALUTA and len(m.CODICI_VALUTA) > 140
    tmp = tempfile.mkdtemp()
    try:
        def scrivi(nome, righe):
            path = os.path.join(tmp, nome)
            open(path, "w", encoding="utf-8").write("Name,Sector,Asset Class,Location,Currency,Weight (%)\n" + righe)
            return path
        g = scrivi("p.csv", "A,Energy,Equity,United Kingdom,GBp,40\nB,Energy,Equity,South Africa,ZAc,30\n"
                            "C,-,Fixed Income,China,CNH,20\nD,Energy,Equity,Italy,EUR,10\n")
        c = m.componi(g, "U")
        assert r2(c["valute"]) == {"GBP": 40.0, "ZAR": 30.0, "CNY": 20.0, "EUR": 10.0}, c["valute"]   # anche l'obbligazione
        # Review Focus 3: segnaposto sopra il 5% → avviso; sotto la metà dei titoli la dimensione non si scrive
        c = m.componi(scrivi("meta.csv", "A,Energy,Equity,Italy,EUR,40\nB,Energy,Equity,Italy,-,60\n"), "M")
        assert c["valute"] == {} and abs(c["esclusi"]["valuta_non_classificato"] - 0.6) < 1e-9
        assert any("valuta" in a and "meno del" in a for a in c["avvisi"]), c["avvisi"]
        c = m.componi(scrivi("poco.csv", "A,Energy,Equity,Italy,EUR,90\nB,Energy,Equity,Italy,-,10\n"), "P")
        assert c["valute"] == {"EUR": 1.0} and any("valuta non classificata" in a for a in c["avvisi"]), c["avvisi"]
        out, js = os.path.join(tmp, "composizione.csv"), os.path.join(tmp, "c.json")
        rc, so, se = run_script_split(asset(*CE), "--file", scrivi("ignota.csv", "A,Energy,Equity,Italy,ABC,100\n"),
                                      "--strumento", "I", "--out", out, cwd=tmp)
        assert rc == 1 and "valute non riconosciute" in se and "ABC" in se and not os.path.exists(out), se[-300:]
        rc, so, se = run_script_split(asset(*CE), "--file", g, "--strumento", "U", "--copertura", "U=EUR",
                                      "--out", out, "--json", js, cwd=tmp)
        assert rc == 0, se[-300:]
        testo = open(out, encoding="utf-8-sig").read()
        assert [r for r in testo.splitlines() if ";valuta;" in r] == ["U;valuta;EUR;100,00;"], testo
        assert "copertura del cambio in EUR" in next(r for r in testo.splitlines() if r.startswith("# U:")), testo
        assert json.load(open(js, encoding="utf-8"))["strumenti"][0]["copertura_cambio"] == "EUR"
        # Review Focus 4: reimportato senza --copertura, tornano le valute dei titoli
        rc, so, se = run_script_split(asset(*CE), "--file", g, "--strumento", "U", "--out", out, cwd=tmp)
        testo = open(out, encoding="utf-8-sig").read()
        assert rc == 0 and testo.count(";valuta;") == 4 and "U;valuta;GBP;40,00;" in testo and "copertura del cambio" not in testo, testo
        assert "Valute: Sterlina britannica 40,00%" in so, so
        for cattiva in ("Z=EUR", "U=EURO", "U"):
            rc, so, se = run_script_split(asset(*CE), "--file", g, "--strumento", "U", "--copertura", cattiva, "--out", out, cwd=tmp)
            assert rc == 2 and "--copertura" in se, (cattiva, rc, se[-200:])
        coperto = os.path.join(tmp, "world-eur-hedged.csv")
        shutil.copy(g, coperto)
        c = m.componi(coperto, "H")
        assert any("copertura del cambio" in a and "--copertura H=EUR" in a for a in c["avvisi"]), c["avvisi"]
        assert not any("copertura del cambio" in a for a in m.componi(coperto, "H", copertura="EUR")["avvisi"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 2: Lancia e verifica il fallimento**

Run: `python3 tests/run_tests.py --only "legge la valuta"`
Expected: FAIL con `KeyError: 'valuta'` su `en["colonne"]`.

- [ ] **Step 3: Implementa** secondo le Interfaces. La dimensione nuova passa dallo stesso ciclo di settori e paesi in `componi()` e `_finalizza()` (esclusioni, rinormalizzazione, soglia della metà dei titoli); i messaggi che oggi dicono «il file non ha la colonna del {dim}» vanno resi corretti al femminile per la valuta.

- [ ] **Step 4: Lancia i test**

Run: `python3 tests/run_tests.py --only "T16"`
Expected: PASS il test nuovo. Nei test dell'importatore che controllano gli avvisi di file senza la colonna della valuta c'è ora un avviso in più: dove un test pretende `avvisi == []` su un file senza valuta, aggiungi la colonna alla sua fixture temporanea oppure confronta gli avvisi senza quello della valuta, e annota la scelta nel commit.

- [ ] **Step 5: README (conteggio e tabella dei test) e commit**

```bash
git add skills/it-pianificazione-obiettivi/assets/importa-composizione-etf.py tests/run_tests.py README.md
git commit -m "feat: l'importatore della composizione scrive la valuta dei titoli e accetta --copertura (T16)"
```

### Task 4: La valuta nei lettori

**Files:**
- Modify: `skills/it-pianificazione-obiettivi/assets/capitale-umano.py` (`leggi_composizione()`: dimensioni ammesse e messaggio)
- Modify: `skills/it-pianificazione-obiettivi/assets/look-through-portafoglio.py` (`DIMENSIONI`, `leggi_composizione()`, `aggrega()`, `stampa()`, costante `N_VALUTE_REPORT`, docstring)
- Test: `tests/run_tests.py` (nuovo test dopo `t_lt_importatore_valuta`; `t_ce_capitale_umano` per la dimensione sconosciuta; `t_lt_valori_chiusi`)

**Interfaces:**
- Consumes: `VALUTE`, `CODICI_VALUTA`, `codice_valuta()`, `nome_valuta()` del Task 3 (caricate dal look-through insieme alle altre tabelle dell'importatore).
- Produces:
  - `capitale-umano.leggi_composizione()` ammette `settore`, `paese`, `titolo`, `valuta` e salta le ultime tre; ogni altra dimensione resta un errore.
  - Look-through: `DIMENSIONI = ("settori", "paesi", "titoli", "valute")`; `N_VALUTE_REPORT = 8`. `leggi_composizione()` valida il codice con `codice_valuta()` (`errore("--composizione: valuta {voce!r} non è un codice ISO 4217 ({strumento})")`) e tratta la scala delle valute come quella di settori e paesi.
  - `aggrega()` aggiunge `"valute": [{"voce": codice, "nome": nome italiano, "peso": float}]`, `copertura["valute"]`, `"quota_euro": float | None` (il peso dell'euro sulla parte coperta; `0.0` se l'euro manca tra le valute coperte; `None` se la copertura delle valute è zero) e, in ogni posizione, `"valute": bool`.
  - `stampa()`: sezione `4. VALUTE (copertura X)` con le prime `N_VALUTE_REPORT` valute e `altre N valute Y`; sotto, `   In euro: X della parte coperta.`; senza valute `   nessuna posizione con le valute`.

- [ ] **Step 1: Scrivi il test**

```python
@test("T16 look-through: valute aggregate per controvalore con la copertura e la quota in euro, capitale-umano le salta")
def t_lt_valute():
    cu = carica_modulo(asset(*CU))
    tmp = tempfile.mkdtemp()
    try:
        v5, broker = os.path.join(FIXTURES, "composizione-look-through-v5.csv"), _broker_look_through(tmp)
        rc, so, se = run_script_split(asset(*LT), "--composizione", v5, "--posizioni", broker, "--json", "lt.json", cwd=tmp)
        assert rc == 0, se[-300:]
        r = json.load(open(os.path.join(tmp, "lt.json"), encoding="utf-8"))
        tot, V_v = 36850, 13000 + 19500 + 2850
        valute = {x["voce"]: x for x in r["valute"]}
        assert abs(valute["USD"]["peso"] - (13000 * .60 + 19500) / V_v) < 1e-12 and valute["USD"]["nome"] == "Dollaro USA"
        assert abs(valute["JPY"]["peso"] - 13000 * .25 / V_v) < 1e-12 and abs(valute["GBP"]["peso"] - 13000 * .15 / V_v) < 1e-12
        assert abs(valute["EUR"]["peso"] - 2850 / V_v) < 1e-12 and abs(r["quota_euro"] - 2850 / V_v) < 1e-12
        assert [x["voce"] for x in r["valute"]] == ["USD", "JPY", "EUR", "GBP"] and abs(sum(x["peso"] for x in r["valute"]) - 1) < 1e-12
        assert abs(r["copertura"]["valute"] - V_v / tot) < 1e-12 and all(p["valute"] is True for p in r["posizioni"])
        assert "4. VALUTE (copertura 95,9%)" in so and "In euro: 8,1% della parte coperta" in so, so
        # il file a quattro colonne non ha valute: copertura zero, nessuna quota
        rc, so, se = run_script_split(asset(*LT), "--composizione", os.path.join(FIXTURES, "composizione-look-through.csv"),
                                      "--posizioni", broker, "--json", "-", cwd=tmp)
        r4 = json.loads(so)
        assert rc == 0 and r4["valute"] == [] and r4["copertura"]["valute"] == 0.0 and r4["quota_euro"] is None
        # Review Focus 5: uno strumento con le sole righe valuta, senza euro tra le valute coperte
        solo = os.path.join(tmp, "solo-valuta.csv")
        open(solo, "w", encoding="utf-8").write("strumento;dimensione;voce;peso;isin\nDE0007164600;valuta;USD;100;\n")
        rc, so, se = run_script_split(asset(*LT), "--composizione", solo, "--posizioni", broker, "--json", "-", cwd=tmp)
        r = json.loads(so)
        assert rc == 0 and r["copertura"] == {"settori": 0.0, "paesi": 0.0, "titoli": 0.0, "regioni": 0.0, "valute": 1500 / tot}, r["copertura"]
        assert r["quota_euro"] == 0.0 and r["valute"] == [{"voce": "USD", "nome": "Dollaro USA", "peso": 1.0}]
        storta = os.path.join(tmp, "storta.csv")
        open(storta, "w", encoding="utf-8").write("strumento;dimensione;voce;peso;isin\nDE0007164600;valuta;Dollari;100;\n")
        rc, so, se = run_script_split(asset(*LT), "--composizione", storta, "--posizioni", broker, cwd=tmp)
        assert rc == 1 and "ISO 4217" in se and "Dollari" in se, se[-300:]
        # capitale-umano: le righe valuta si saltano, una dimensione sconosciuta resta un errore
        assert abs(cu.leggi_composizione(v5)["IE00B4L5Y983"]["Health Care"] - 0.5) < 1e-9
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 2: Sposta su un'altra dimensione il test del capitale umano che usa `valuta` come dimensione sconosciuta.** In `t_ce_capitale_umano` la riga aggiunta al CSV diventa `"ETF MSCI World;rating;AAA;100\n"` e l'asserzione `"rating" in se` (quello del look-through è già stato spostato nel Task 2).

- [ ] **Step 3: In `t_lt_valori_chiusi` aggiorna i due confronti esatti**: la posizione del BTP prende `"valute": False`, e la copertura del caso con le sole righe `titolo` prende `"valute": 0.0`.

- [ ] **Step 4: Lancia e verifica il fallimento**

Run: `python3 tests/run_tests.py --only "valute aggregate"`
Expected: FAIL con `KeyError: 'valute'`.

- [ ] **Step 5: Implementa** `capitale-umano.py` e `look-through-portafoglio.py` secondo le Interfaces.

- [ ] **Step 6: Lancia i test**

Run: `python3 tests/run_tests.py --only "T16"`, poi `--only "T15"`
Expected: PASS (salvo `t_lt_cruscotto`, che il Task 5 aggiorna).

- [ ] **Step 7: README (conteggio e tabella dei test) e commit**

```bash
git add skills/it-pianificazione-obiettivi/assets tests/run_tests.py README.md
git commit -m "feat: valute nel look-through, con copertura e quota in euro (T16)"
```

### Task 5: Regioni e valute nel cruscotto

**Files:**
- Modify: `skills/it-revisione/assets/genera-cruscotto.py` (`_look_through()`, docstring di `componi_bundle()`)
- Modify: `skills/it-revisione/assets/cruscotto.html` (`sezioneLookThrough()`)
- Test: `tests/run_tests.py` (`_json_esempio()`, `t_lt_cruscotto`)

**Interfaces:**
- Consumes: le chiavi `regioni`, `valute`, `quota_euro`, `copertura.regioni`, `copertura.valute` del JSON del look-through (Task 1 e 4).
- Produces: nel bundle, `look_through` prende `regioni: [{nome, peso}] | null`, `valute: [{nome, peso}] | null` (le prime otto, più `altre N valute` con la somma), `quota_euro: number | null`; `copertura` porta `regioni` e `valute` solo se il JSON le ha. Un JSON senza le chiavi nuove dà `null` e la pagina salta i due grafici. Nessun ISIN di titolo nel bundle.

- [ ] **Step 1: In `_json_esempio()` il lancio di `lt.json` usa la fixture a cinque colonne** (`composizione-look-through-v5.csv`): il cruscotto completo degli esempi mostra così regioni e valute.

- [ ] **Step 2: Aggiorna `t_lt_cruscotto`.** L'insieme atteso delle chiavi di `lt` prende `regioni`, `valute`, `quota_euro`. Aggiungi, dopo le asserzioni sul bundle:

```python
    assert lt["regioni"][0] == {"nome": "Nord America", "peso": r["regioni"][0]["peso"]} and lt["valute"][0]["nome"] == "Dollaro USA"
    assert lt["quota_euro"] == r["quota_euro"] and set(lt["copertura"]) == {"settori", "paesi", "titoli", "regioni", "valute"}
    assert "US0000000011" not in html and "US0000000011" not in json.dumps(b), "l'ISIN di un titolo è finito nella pagina"
    # un JSON della 0.12.0, senza le chiavi nuove: accettato, i due grafici mancano
    def come_prima(d):
        for k in ("regioni", "valute", "quota_euro"):
            d.pop(k)
        d["copertura"] = {k: d["copertura"][k] for k in ("settori", "paesi", "titoli")}
        for t in d["titoli"]:
            t.pop("isin")
    rc, _, se, b_v, html_vecchio = _cruscotto(_json_variante("lt.json", come_prima))
    assert rc == 0 and b_v["look_through"]["regioni"] is None and b_v["look_through"]["valute"] is None, se[-300:]
```

e, nel blocco del browser:

```python
            assert page.locator("#sez-look_through svg").count() >= 5        # settori, regioni, paesi, valute, primi titoli
            assert "Regioni (copertura" in testo and "Valute (copertura" in testo and "In euro:" in testo, testo[:1200]
            page, errori, eccezioni, _ = _apri_cruscotto(br, html_vecchio)
            testo = page.inner_text("#sez-look_through")
            assert errori == [] and eccezioni == [] and "Regioni (copertura" not in testo and "Valute (copertura" not in testo, testo[:600]
```

- [ ] **Step 3: Lancia e verifica il fallimento**

Run: `python3 tests/run_tests.py --only "il cruscotto riconosce il JSON"`
Expected: FAIL sull'insieme delle chiavi di `look_through`.

- [ ] **Step 4: Implementa `_look_through()`** con le chiavi facoltative e aggiorna il docstring di `componi_bundle()`.

- [ ] **Step 5: Implementa `sezioneLookThrough()`**: l'ordine diventa settori, regioni, paesi, valute, primi titoli; regioni e valute sono barre orizzontali come le altre, con la copertura nel titolo (`Regioni (copertura X)`, `Valute (copertura X)`) e, sotto le valute, la nota `In euro: X della parte coperta.` quando `quota_euro` è un numero. Valgono le regole del template (spec §7).

- [ ] **Step 6: Lancia i test del cruscotto**

Run: `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium RICHIEDI_BROWSER=1 python3 tests/run_tests.py --only "cruscotto"`
Expected: PASS, compresi i test nel browser a 375 px.

- [ ] **Step 7: Commit**

```bash
git add skills/it-revisione/assets/genera-cruscotto.py skills/it-revisione/assets/cruscotto.html tests/run_tests.py
git commit -m "feat: regioni e valute nella sezione Look-through del cruscotto (T16)"
```

### Task 6: Documentazione, versioni e chiusura

**Files:**
- Modify: `skills/it-pianificazione-obiettivi/references/composizione-etf.md`, `skills/it-pianificazione-obiettivi/SKILL.md` (Step 8, Riferimenti)
- Modify: `skills/it-revisione/SKILL.md` (passo 3, contratto di input, `metadata.version`)
- Modify: `README.md`, `CHANGELOG.md`, `ROADMAP.md`
- Test: `tests/run_tests.py` (`t_lt_documentazione`)

- [ ] **Step 1: Aggiorna `t_lt_documentazione`.** `'version: "0.9"'` diventa `'version: "0.10"'`; aggiungi:

```python
    for parola in ("regioni", "M49", "Taiwan", "strumento;dimensione;voce;peso;isin", "valuta", "--copertura", "Cambio", "ISO 4217"):
        assert parola in ref, parola
    assert "--copertura" in step8 and "regioni" in step8 and "valute" in step8
    assert "regioni" in contratto and "valute" in contratto and "quota_euro" in contratto
    nr = open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8").read().split("## v0.12.0")[0]
    assert "regioni" in nr and "colonna `isin`" in nr and "--copertura" in nr
    assert "regioni" in t16 and "ISIN dei titoli" in t16 and "valuta" in t16
```

- [ ] **Step 2: Lancia e verifica il fallimento**

Run: `python3 tests/run_tests.py --only "skill, reference, revisione"`
Expected: FAIL sulla versione di it-revisione.

- [ ] **Step 3: Aggiorna `composizione-etf.md`** (e il suo indice, che un test confronta con i titoli):
  - «Cosa legge e cosa esclude»: la colonna della valuta e i suoi sinonimi; «Cambio» nel file italiano di iShares è la borsa; le obbligazioni contano nelle valute; codici ISO 4217 e unità minori;
  - «Il file composizione.csv»: l'intestazione `strumento;dimensione;voce;peso;isin`, un esempio con una riga `valuta` e una riga `titolo` con l'ISIN, i tre formati ancora letti, le righe a mano senza il quinto campo;
  - nuova sezione «Classi con copertura del cambio»: perché la valuta dei titoli non è l'esposizione, `--copertura CHIAVE=VALUTA`, l'avviso su «hedged»;
  - «Il look-through del portafoglio»: regioni (standard ONU M49, Americhe divise in due, Taiwan in Asia, Antartide a parte; Turchia, Israele, Cipro e i paesi del Golfo in Asia, Russia in Europa, Messico in America Latina; niente mercati sviluppati ed emergenti); regola di somma dei titoli per ISIN o per nome; valute, copertura e `quota_euro`; posizioni dirette con la riga `valuta` a mano;
  - «Limiti»: regioni geografiche (Giappone e India nella stessa regione); valuta di negoziazione, non dei ricavi; gli ISIN uniscono solo dove l'emittente li riporta.

- [ ] **Step 4: Aggiorna le due skill.** In `it-pianificazione-obiettivi/SKILL.md`, Step 8: `--copertura` nell'esempio dell'importatore per un ETF con copertura del cambio, e regioni e valute tra ciò che il look-through riporta (la versione resta 0.25, già alzata nell'ondata 0; se questo piano si esegue per primo, alzala qui). In `it-revisione/SKILL.md`: al passo 3 il look-through riporta anche le prime tre regioni e la quota in euro; nel «Contratto di input» la riga «Look-through» aggiunge `regioni[]`, `valute[]` e `quota_euro`; `metadata.version: "0.10"`.

- [ ] **Step 5: README, CHANGELOG, ROADMAP.** README: `v0.10` per it-revisione e le due descrizioni nella tabella delle skill. CHANGELOG: sotto «Non rilasciato» tre voci (regioni; colonna `isin` e regola di somma; valuta e `--copertura`), e nella «Storia delle skill» `#### v0.10 (plugin 0.13.0)` per it-revisione e una riga in più sotto `v0.25` di it-pianificazione-obiettivi. ROADMAP, tema T16: gli sviluppi «regioni come dimensione; ISIN dei titoli nel CSV; valuta di denominazione» diventano fatti, con il rimando a questa spec.

- [ ] **Step 6: Suite completa**

Run: la suite completa (vedi Global Constraints).
Expected: tutti i test passati, nessuno saltato.

- [ ] **Step 7: Prova i mutanti** (con `python3 -B`, ripristinando dopo ognuno): un paese spostato di regione; l'unione per ISIN tolta (resta solo la chiave del nome); l'unione per nome tolta (resta solo l'ISIN); la rinormalizzazione delle valute tolta; `quota_euro` calcolata sul controvalore totale invece che sulla parte coperta; «cambio» aggiunto ai sinonimi della valuta; il quinto campo non scritto sulle righe che non sono `titolo`. Ognuno deve far fallire almeno un test: annota quale nel messaggio del commit.

- [ ] **Step 8: README (conteggio e tabella dei test) e commit**

```bash
git add skills README.md CHANGELOG.md ROADMAP.md tests/run_tests.py
git commit -m "docs: regioni, ISIN dei titoli e valuta in reference, skill, README, CHANGELOG e ROADMAP (T16)"
```

### Chiusura

Prima del merge su `develop`: la revisione finale prevista dal modo di esecuzione scelto e, se il proprietario la chiede, la revisione avversariale del repository (`docs/sviluppo/workflows/review-tema-roadmap.js`, § 4 di `HANDOFF.md`). Le correzioni vanno in un commit a parte, che ne riporta l'esito. La pull request si apre quando il proprietario la chiede.
