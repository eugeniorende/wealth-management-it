# Importatore della composizione degli ETF: piano di implementazione

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `importa-composizione-etf.py` legge i file delle posizioni degli emittenti di ETF (CSV o XLSX, italiano o inglese) e scrive `composizione.csv` per settore GICS e paese ISO, che `capitale-umano.py --composizione` legge per la diagnosi 4.

**Architecture:** Un motore generico, nello stesso file: apre il file, trova la riga d'intestazione con tabelle di sinonimi, legge pesi, settori e paesi, esclude liquidità, derivati e righe non classificate, rinormalizza per dimensione. Una piccola tabella di schede per emittente porta solo quello che il motore non deduce (parole di riconoscimento, classificazione, etichette della data, valori di liquidità). L'uscita è un CSV `strumento;dimensione;voce;peso` fuso con quello esistente, più un `--json` facoltativo; `capitale-umano.py` legge il vecchio e il nuovo formato.

**Tech Stack:** Python ≥ 3.11, libreria standard più `openpyxl` (già tra le dipendenze) per gli XLSX; helper `cli()`, `errore()`, `numero()`, `pct()`, `scrivi_json()` di `motore_bootstrap.py`; runner `tests/run_tests.py` (decoratore `@test`, nessun pytest).

**Spec:** `docs/sviluppo/specs/2026-10-25-composizione-etf-design.md` (citata sotto come «spec §N»).

## Global Constraints

- Nessuna chiamata di rete: lo script legge solo file locali (spec §1).
- Interfaccia comune: `cli()` di `motore_bootstrap.py` (`allow_abbrev=False`); exit 0 riuscito, 1 dati con messaggio che inizia per `ERRORE:` su stderr e nulla di `ERRORE:` su stdout, 2 riga di comando errata; `configura_stdout()` prima di qualsiasi stampa.
- Numeri stampati in formato italiano con `numero()` e `pct()`: nessun format spec anglosassone (`{x:,.0f}`, `{x:.1%}`, `{x:.1f}`), lo verifica `t_formati_italiani`.
- `open()` sempre con `encoding=` esplicito, o in modalità binaria (`t_cli_utf8`).
- Niente mezzo output: tutti i file letti e validati prima di scrivere `--out` o `--json`.
- Le 11 voci GICS sono esattamente le chiavi di `SETTORI_GICS` di `capitale-umano.py`, con gli stessi nomi italiani; un test lo vincola.
- `composizione.csv`: UTF-8 con BOM, separatore `;`, virgola decimale, due decimali, pesi in percento rinormalizzati a 100 per dimensione (spec §3.1).
- `--json`: pesi in frazione; con `--json -` su stdout c'è solo il JSON (come `importa-estratto-broker.py`), `--out` si scrive comunque.
- I file degli emittenti non entrano nel repository: le fixture sono sintetiche, i CSV in `tests/fixtures/composizione-*.csv`, gli XLSX generati dai test con `openpyxl`.
- Lingua: italiano, nello stile degli script esistenti; commenti densi come in `importa-estratto-broker.py`. Docstring in testa con «Uso:», le regole applicate e i limiti dichiarati.
- I test nuovi si chiamano `T16 composizione ETF: …` e stanno in una sezione `# ═══ T16: composizione degli ETF ═══` di `tests/run_tests.py`, subito dopo il blocco T15 e prima di T17. Costante `CE = ("it-pianificazione-obiettivi", "importa-composizione-etf.py")`.
- Ogni commit termina con le righe di attribuzione della sessione.

## Review Focus

1. **Un CSV esportato da Excel italiano dopo averlo aperto e salvato** (cp1252, `;`, righe vuote con soli `;;;`, celle tra virgolette): si legge come l'originale. Test nel Task 1.
2. **Lo stesso ETF scaricato in inglese e in italiano** dà gli stessi pesi al centesimo, anche se cambiano separatore, decimali, intestazioni e nomi. Test nel Task 2.
3. **Reimportare lo stesso strumento più volte** (aggiornamento annuale) non duplica righe né commenti e non sposta gli altri strumenti. Test nel Task 3.
4. **Un `--strumento` scritto diversamente dalla posizione** (maiuscole, spazi): `capitale-umano.py` lo mette tra i mancanti e lo dice per nome, così l'utente vede il refuso. Il confronto resta esatto, come oggi. Test nel Task 4.
5. **Un file con pochissime righe classificate** (per esempio un ETF obbligazionario, settore vuoto ovunque): la dimensione settore resta vuota con un avviso, i paesi si scrivono, niente traceback. Test nel Task 2.

---

### Task 1: Lettura della tabella (apertura, intestazione, fine tabella, numeri)

**Files:**
- Create: `skills/it-pianificazione-obiettivi/assets/importa-composizione-etf.py` (docstring, costanti dei sinonimi delle colonne, funzioni di lettura; `main()` minimo che stampa le colonne trovate, completato nel Task 3)
- Create: `tests/fixtures/composizione-ishares-en.csv`, `tests/fixtures/composizione-ishares-it.csv`
- Test: `tests/run_tests.py`

**Interfaces:**
- Produces:
  - `normalizza(testo) -> str`: minuscole, accenti tolti (`unicodedata` NFKD), spazi e punteggiatura diversa da `%` compressi in uno spazio, estremi tolti.
  - `leggi_righe(path: str) -> tuple[list[list], str | None]`: tutte le righe come liste di celle (stringhe per i CSV; numeri, date o stringhe per gli XLSX) e il titolo del foglio (XLSX) o `None`. `.xlsx` con `openpyxl.load_workbook(read_only=True, data_only=True)`, primo foglio con almeno una cella non vuota. `.csv`/`.txt`: UTF-8 con BOM, ripiego cp1252; separatore dal `csv.Sniffer` tra `,;\t` sulle righe dopo le prime 10 (su tutte se il file è più corto), ripiego sul separatore più frequente nel testo. Pagina HTML (`<!doctype` o `<html` all'inizio, ignorando spazi e maiuscole), estensione diversa, file mancante → `errore()`.
  - `SINONIMI_COLONNE: dict[str, tuple[str, ...]]` con i ruoli `peso`, `settore`, `paese`, `asset_class`, `nome` e i sinonimi della spec §4.2, nell'ordine della spec (l'ordine decide tra due colonne candidate).
  - `trova_intestazione(righe) -> tuple[int, dict[str, int], dict[str, str]]`: indice della riga, ruolo → indice di colonna, ruolo → testo originale dell'intestazione. Cerca nelle prime 40 righe la prima con `peso` e almeno uno tra `settore` e `paese`; per ogni ruolo vince il sinonimo che compare prima in `SINONIMI_COLONNE`. Nessuna → `errore()` con le celle non vuote delle prime 15 righe e la frase «scarica il file delle posizioni (holdings), non la scheda prodotto né il KID».
  - `righe_dati(righe, i_intestazione, col_peso) -> list[list]`: le righe dopo l'intestazione fino alla prima riga vuota (tutte le celle vuote o di soli spazi) dopo almeno una riga di dati, o alla prima riga il cui peso non è né numerico né un segnaposto.
  - `SEGNAPOSTO = ("", "-", "n/a", "na", "n.d.", "nd")` (confronto su `normalizza`).
  - `virgola_decimale(valori) -> bool`: `True` se almeno un valore stringa del peso ha la forma `\d+,\d+` senza punti dopo la virgola.
  - `peso_numerico(valore, virgola: bool) -> float | None`: numeri lasciati come sono; stringhe senza `%` in coda; con `virgola` si tolgono i punti e la virgola diventa punto, senza si tolgono le virgole; segnaposto → `None`; altro → `ValueError`.

- [ ] **Step 1: Crea le due fixture iShares** (spec §7.1). Stessi otto titoli, stessi pesi; cambiano solo lingua e formato.

`composizione-ishares-en.csv` (separatore `,`, punto decimale, campi con virgole tra virgolette):
```
iShares Core MSCI World UCITS ETF
Fund Holdings as of,"Sep 30, 2026"
Inception Date,"Sep 25, 2009"
Shares Outstanding,"1,000,000.00"

Ticker,Name,Sector,Asset Class,Market Value,Weight (%),Notional Value,Location,Exchange,Currency
AAA,ALPHA CORP,Information Technology,Equity,"3,000.00",30.00,"3,000.00",United States,NASDAQ,USD
BBB,BETA BANK,Financials,Equity,"2,000.00",20.00,"2,000.00",United States,New York Stock Exchange Inc.,USD
CCC,GAMMA PHARMA,Health Care,Equity,"1,500.00",15.00,"1,500.00",Japan,Tokyo Stock Exchange,JPY
DDD,DELTA INDUSTRIES,Industrials,Equity,"1,500.00",15.00,"1,500.00",United Kingdom,London Stock Exchange,GBP
EEE,EPSILON SOFT,Information Technology,Equity,"1,000.00",10.00,"1,000.00","Korea (South)",Korea Exchange,KRW
FFF,ZETA ENERGY,Energy,Equity,900.00,9.00,900.00,Canada,Toronto Stock Exchange,CAD
USD,USD CASH,Cash and/or Derivatives,Cash,80.00,0.80,80.00,United States,-,USD
ESZ6,S&P500 EMINI DEC 26,Cash and/or Derivatives,Futures,20.00,0.20,"5,000.00",United States,Chicago Mercantile Exchange,USD

"The content contained herein is owned or licensed by BlackRock and/or its third-party information providers."
```

`composizione-ishares-it.csv` (separatore `;`, virgola decimale, punto delle migliaia): preambolo `iShares Core MSCI World UCITS ETF`, `Posizioni al;30/set/2026`; intestazione `Ticker dell'emittente;Nome;Settore;Asset class;Valore di mercato;Ponderazione (%);Valore nozionale;Area geografica;Borsa;Valuta`; settori `Informatica`, `Finanza`, `Sanità`, `Industriali`, `Energia`, `Liquidità e/o derivati`; asset class `Azionario`, `Liquidità`, `Futures`; paesi `Stati Uniti`, `Giappone`, `Regno Unito`, `Corea del Sud`, `Canada`; pesi `30,00` … `0,20`, valori di mercato `3.000,00`; disclaimer in italiano in fondo dopo una riga vuota.

- [ ] **Step 2: Scrivi il test `T16 composizione ETF: lettura della tabella (intestazione, preambolo, fine, numeri, formati di file)`**

```python
m = carica_modulo(asset(*CE))
for nome, sep in (("composizione-ishares-en.csv", ","), ("composizione-ishares-it.csv", ";")):
    righe, foglio = m.leggi_righe(os.path.join(FIXTURES, nome))
    i, col, testi = m.trova_intestazione(righe)
    assert i == 5 and foglio is None, (nome, i)
    assert set(col) == {"peso", "settore", "paese", "asset_class", "nome"}, col
    dati = m.righe_dati(righe, i, col["peso"])
    assert len(dati) == 8, (nome, len(dati))                 # il disclaimer in fondo non entra
    v = m.virgola_decimale([r[col["peso"]] for r in dati])
    assert v is (sep == ";")
    assert [m.peso_numerico(r[col["peso"]], v) for r in dati] == [30, 20, 15, 15, 10, 9, 0.8, 0.2]
assert testi["peso"] == "Ponderazione (%)" and testi["paese"] == "Area geografica"
assert m.peso_numerico("1.234,5", True) == 1234.5 and m.peso_numerico("1,234.5", False) == 1234.5
assert m.peso_numerico("4,46%", True) == 4.46 and m.peso_numerico("N/A", False) is None
assert m.peso_numerico(0.0565, False) == 0.0565
# precedenza tra due candidate: «Sector Classification» batte «Industry Classification»
_, col, testi = m.trova_intestazione([["ISIN", "Percent of Fund", "Trade Country Name",
                                       "Industry Classification", "Sector Classification"]])
assert testi["settore"] == "Sector Classification" and col["settore"] == 4
# CSV risalvato da Excel italiano: cp1252, «;», righe di soli «;»
tmp = tempfile.mkdtemp()
try:
    p = os.path.join(tmp, "excel.csv")
    with open(p, "w", encoding="cp1252") as f:
        f.write("Fondo;;;\nPosizioni al;30/09/2026;;\n;;;\nNome;Settore;Area geografica;Ponderazione (%)\n"
                "ALPHA;Informatica;Stati Uniti;60,0\nBETA;Sanità;Giappone;40,0\n;;;\n")
    righe, _ = m.leggi_righe(p)
    i, col, _ = m.trova_intestazione(righe)
    assert i == 3 and len(m.righe_dati(righe, i, col["peso"])) == 2
    # XLSX con l'intestazione alla riga 4 e il titolo del foglio
    import openpyxl
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "2026-10-25"
    ws.append([None]); ws.append(["Although information in this document…"]); ws.append([None])
    ws.append([None, "Name", "ISIN", "Country", "Type of Security", "Industry Classification", "Weighting"])
    ws.append([1, "ALPHA", "US0000000001", "United States", "Equities", "Information Technology", 0.6])
    px = os.path.join(tmp, "x.xlsx"); wb.save(px)
    righe, foglio = m.leggi_righe(px)
    i, col, _ = m.trova_intestazione(righe)
    assert foglio == "2026-10-25" and i == 3 and col["peso"] == 6
    # errori: pagina HTML, scheda prodotto, estensione, file mancante
    ph = os.path.join(tmp, "pagina.csv")
    with open(ph, "w", encoding="utf-8") as f:
        f.write("  <!DOCTYPE html><html><head><title>iShares</title></head></html>")
    for args, atteso in (((ph,), "pagina HTML"), (("/non/esiste.csv",), "non trovato")):
        rc, so, se = run_script_split(asset(*CE), "--file", args[0], "--strumento", "X", cwd=tmp)
        assert rc == 1 and se.startswith("ERRORE:") and atteso in se and "Traceback" not in se, se[-300:]
    ps = os.path.join(tmp, "scheda.csv")
    with open(ps, "w", encoding="utf-8") as f:
        f.write("Caratteristiche principali\nTER,0.20%\nValuta,USD\n")
    rc, so, se = run_script_split(asset(*CE), "--file", ps, "--strumento", "X", cwd=tmp)
    assert rc == 1 and "file delle posizioni" in se and "TER" in se, se[-300:]
    pp = os.path.join(tmp, "f.pdf")
    with open(pp, "w", encoding="ascii") as f:    # non «wb»: t_cli_utf8 vuole encoding= o «rb» in ogni open()
        f.write("%PDF-1.4")
    rc, so, se = run_script_split(asset(*CE), "--file", pp, "--strumento", "X", cwd=tmp)
    assert rc == 1 and "XLSX o CSV" in se, se[-300:]
finally:
    shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 3: Esegui e verifica che fallisca** — `python tests/run_tests.py --only "T16 composizione ETF: lettura"` → FAIL (lo script non esiste).

- [ ] **Step 4: Implementa le funzioni dell'Interfaces block** e un `main()` provvisorio con `cli()` (`--file` e `--strumento` con `action="append"`, required) che legge il primo file, trova l'intestazione e stampa le colonne; gli errori passano da `errore()`. I messaggi: «il file è una pagina HTML, non il file delle posizioni: dal sito dell'emittente usa il pulsante di download delle posizioni (XLSX o CSV)»; «formato non supportato (.pdf): esporta le posizioni in XLSX o CSV».

- [ ] **Step 5: Esegui e verifica che passi** — stesso comando → PASS.

- [ ] **Step 6: Commit** — `feat: importa-composizione-etf.py, lettura della tabella degli emittenti (T16)`

---

### Task 2: Composizione di un file (emittente, esclusioni, nomi, rinormalizzazione, ICB)

**Files:**
- Modify: `skills/it-pianificazione-obiettivi/assets/importa-composizione-etf.py`
- Test: `tests/run_tests.py` (helper `_xlsx_emittente(tipo, cartella) -> str` che scrive le fixture XLSX sintetiche e ne ritorna il percorso)

**Interfaces:**
- Consumes: le funzioni del Task 1.
- Produces:
  - `SETTORI_GICS: dict[str, str]` (GICS inglese → nome italiano, identico a quello di `capitale-umano.py`) e `SINONIMI_SETTORI: dict[str, str]` (normalizzato → GICS) con i sinonimi della spec §4.6, i nomi GICS stessi e `telecommunication services` → `Communication Services` (con avviso).
  - `NOMI_ICB_ESCLUSIVI = {"technology", "telecommunications", "basic materials"}`, `NOMI_GICS_ESCLUSIVI = {"information technology", "communication services", "materials"}` (normalizzati).
  - `PAESI: dict[str, tuple[str, tuple[str, ...]]]`: ISO alpha-2 → (nome italiano, sinonimi). Copre i paesi sviluppati ed emergenti di MSCI ACWI IMI (AU AT BE CA DK FI FR DE HK IE IL IT JP NL NZ NO PT SG ES SE CH GB US; BR CL CN CO CZ EG GR HU IN ID KR KW MY MX PE PH PL QA SA ZA TW TH TR AE), i domicili della spec §4.6 (LU BM KY JE GG CW PA LR IM MO) e AR RU PK VN NG KZ IS MT CY RO EE LT LV SK SI HR BG UY MA KE; per ciascuno il nome inglese, quello italiano e le varianti della spec §4.6. Il codice stesso è un sinonimo valido.
  - `VALORI_LIQUIDITA` (spec §4.5 punto 1, normalizzati), `VALORI_NON_CLASSIFICATI = ("unknown", "unassigned", "other", "-", "n/a", "non classificato", "altro", "")`, `SOGLIA_AVVISO = 0.05`.
  - `SCHEDE: dict[str, dict]` con chiavi `ishares`, `xtrackers`, `vanguard`, `amundi`, `spdr`; ogni scheda ha `riconosci` (tuple di parole normalizzate), `classificazione` (`"GICS"`, o `None` per Vanguard: la si deduce dai nomi finché un file reale non la conferma), `etichette_data` (le generiche della spec §4.3 più `as at` per Vanguard), `data_nel_foglio` (bool, `True` per Xtrackers), `liquidita` (valori in più), `verificato` (`"2026-10, file reale"` per Xtrackers e SPDR, `"da confermare"` per gli altri).
  - `riconosci_emittente(preambolo: list[list], nome_file: str, forzato: str | None) -> tuple[str | None, str]`: (chiave, `"--emittente"` | `"preambolo"` | `"nome del file"` | `"nessuno"`).
  - `data_posizioni(preambolo, titolo_foglio, scheda) -> str | None`: ISO `AAAA-MM-GG`; formati della spec §4.3 più `30 Sep 2026` (mesi abbreviati inglesi e italiani), e una cella data di openpyxl; la cella accanto all'etichetta o il resto della stessa cella dopo `:`.
  - `componi(path: str, strumento: str, forzato: str | None = None) -> dict`: la voce di `strumenti` della spec §3.4 (`strumento`, `emittente`, `riconosciuto_da`, `file` come nome base, `data_posizioni`, `classificazione`, `colonne`, `titoli`, `esclusi` con le tre chiavi, `settori`, `paesi`, `avvisi`). `titoli` = righe con peso numerico positivo non di liquidità. `esclusi.liquidita_derivati` somma i valori assoluti, in frazione del totale dei pesi numerici. Pesi in frazione, rinormalizzati a 1 per dimensione, ordinati per peso decrescente (dict ordinato). Gli errori passano da `errore()` con il nome del file.

Regole di `componi` (spec §4.4-§4.7), nell'ordine:
0. le righe con peso segnaposto si saltano subito: i loro settore e paese non si leggono (in Xtrackers una riga `N/A` può avere un paese qualsiasi);
1. scala: somma dei pesi numerici (negativi compresi) tra 0,9 e 1,1 → frazione, tra 90 e 110 → percento, altrimenti `errore("… i pesi sommano a X: file troncato o colonna sbagliata?")`;
2. una riga è liquidità o derivato se la sua asset class o il suo settore normalizzati stanno in `VALORI_LIQUIDITA` (o in `scheda["liquidita"]`), o se il peso è negativo;
3. per ogni dimensione, una riga non classificata (valore in `VALORI_NON_CLASSIFICATI`) conta in `esclusi.<dimensione>_non_classificato`;
4. i nomi restanti passano per i sinonimi; i non riconosciuti di un file si raccolgono **tutti** con il loro peso e danno un solo `errore()` che li elenca e chiede di segnalarli;
5. classificazione: `scheda["classificazione"]` se c'è; altrimenti ICB se i settori normalizzati hanno un nome di `NOMI_ICB_ESCLUSIVI` e nessuno di `NOMI_GICS_ESCLUSIVI`; entrambi → `errore("… classificazione mista GICS e ICB …")`; con ICB i settori non si mappano, `settori = {}` e avviso «classificazione ICB, non convertibile in GICS senza errore: settori non scritti, il capitale umano tratterà lo strumento come senza composizione settoriale»;
6. avvisi: non classificati sopra `SOGLIA_AVVISO` in una dimensione; liquidità e derivati sopra `SOGLIA_AVVISO`; emittente non riconosciuto; `Telecommunication Services` convertito; dimensione vuota (nessuna riga classificata, o colonna assente); entrambe vuote → `errore()`.

- [ ] **Step 1: Scrivi l'helper `_xlsx_emittente(tipo, cartella)`** con quattro layout sintetici (spec §4.3, §7.1). I file si chiamano `f-<tipo>.xlsx`: il nome non contiene l'emittente, così il riconoscimento passa dal preambolo.

| tipo | Preambolo | Intestazione (riga) | Righe (nome, settore, paese, tipo/asset, peso) |
|---|---|---|---|
| `xtrackers` | foglio `2026-10-25`; riga 2 «Although information in this document has been obtained from sources believed to be reliable, DWS does not guarantee…» | riga 4: `None, Name, ISIN, Country, Currency, Type of Security, Industry Classification, Weighting` | A, Information Technology, United States, Equities, 0.40; B, Financials, Japan, Equities, 0.25; C, Health Care, Germany, Equities, 0.20; D, Materials, Switzerland, Equities, 0.12; E, unknown, Germany, Equities, 0.02; F, Health Care, United Arab Emirates, Equities, `"N/A"`; G, unknown, Germany, Future, 0.01 |
| `spdr` | `Fund Name:` «State Street SPDR MSCI ACWI IMI UCITS ETF»; `ISIN:`; `Ticker Symbol:`; `Holdings As Of:` «22-Oct-2026»; riga vuota | riga 6: `ISIN, Security Name, Percent of Fund, Trade Country Name, Sector Classification, Industry Classification`; dopo i dati una riga vuota e «Marketing communication…» | A, Information Technology (industry «Semiconductors»), United States, 50.0; B, Consumer Discretionary («Broadline Retail»), Taiwan, 30.0; C, Communication Services («Interactive Media»), Hong Kong, 15.0; D, Unassigned, Unassigned, 5.04; E «CNY:HKD 20250930», Unassigned, Unassigned, −0.04 |
| `vanguard` | «Vanguard FTSE All-World UCITS ETF»; «As at 30 Sep 2026» | riga 4: `Holding name, Sector, Country, % of net assets` | A, Technology, United States, 40; B, Financials, Japan, 30; C, Telecommunications, France, 10; D, Basic Materials, Australia, 20 |
| `amundi` | «Amundi MSCI Europe UCITS ETF»; `Dati al` «30/09/2026» | riga 4: `Nome, Settore, Paese, Peso (%)` | A, Beni di prima necessità, Francia, 50; B, Servizi di pubblica utilità, Italia, 30; C, Immobiliare, Paesi Bassi, 20 |

- [ ] **Step 2: Scrivi il test `T16 composizione ETF: valori chiusi per emittente, riconoscimento ed esclusioni`**

```python
m = carica_modulo(asset(*CE))
r2 = lambda d: {k: round(v * 100, 2) for k, v in d.items()}
en = m.componi(os.path.join(FIXTURES, "composizione-ishares-en.csv"), "ETF MSCI World")
it = m.componi(os.path.join(FIXTURES, "composizione-ishares-it.csv"), "ETF MSCI World")
for c in (en, it):
    assert c["emittente"] == "ishares" and c["riconosciuto_da"] == "preambolo" and c["classificazione"] == "GICS"
    assert c["data_posizioni"] == "2026-09-30" and c["titoli"] == 6
    assert r2(c["settori"]) == {"Information Technology": 40.40, "Financials": 20.20, "Health Care": 15.15,
                                "Industrials": 15.15, "Energy": 9.09}
    assert r2(c["paesi"]) == {"US": 50.51, "JP": 15.15, "GB": 15.15, "KR": 10.10, "CA": 9.09}
    assert abs(c["esclusi"]["liquidita_derivati"] - 0.01) < 1e-9 and c["avvisi"] == []
assert list(en["settori"]) == list(it["settori"]) and en["settori"] == it["settori"]   # stesso ordine e valori
tmp = tempfile.mkdtemp()
try:
    x = m.componi(_xlsx_emittente("xtrackers", tmp), "X")
    assert x["emittente"] == "xtrackers" and x["data_posizioni"] == "2026-10-25" and x["titoli"] == 5
    assert r2(x["settori"]) == {"Information Technology": 41.24, "Financials": 25.77, "Health Care": 20.62, "Materials": 12.37}
    assert r2(x["paesi"]) == {"US": 40.40, "JP": 25.25, "DE": 22.22, "CH": 12.12}
    assert abs(x["esclusi"]["liquidita_derivati"] - 0.01) < 1e-9
    assert abs(x["esclusi"]["settore_non_classificato"] - 0.02) < 1e-9 and x["esclusi"]["paese_non_classificato"] == 0
    s = m.componi(_xlsx_emittente("spdr", tmp), "S")
    assert s["emittente"] == "spdr" and s["data_posizioni"] == "2026-10-22"
    assert s["colonne"]["settore"] == "Sector Classification" and s["colonne"]["paese"] == "Trade Country Name"
    assert r2(s["settori"]) == {"Information Technology": 52.63, "Consumer Discretionary": 31.58, "Communication Services": 15.79}
    assert r2(s["paesi"]) == {"US": 52.63, "TW": 31.58, "HK": 15.79}
    assert abs(s["esclusi"]["liquidita_derivati"] - 0.0004) < 1e-9
    assert any("non classificat" in a and "5%" in a for a in s["avvisi"]), s["avvisi"]   # 5,04% > 5%
    v = m.componi(_xlsx_emittente("vanguard", tmp), "V")
    assert v["emittente"] == "vanguard" and v["classificazione"] == "ICB" and v["settori"] == {}
    assert r2(v["paesi"]) == {"US": 40.0, "JP": 30.0, "AU": 20.0, "FR": 10.0} and v["data_posizioni"] == "2026-09-30"
    assert any("ICB" in a for a in v["avvisi"])
    a = m.componi(_xlsx_emittente("amundi", tmp), "A")
    assert r2(a["settori"]) == {"Consumer Staples": 50.0, "Utilities": 30.0, "Real Estate": 20.0}
    assert r2(a["paesi"]) == {"FR": 50.0, "IT": 30.0, "NL": 20.0}
    # riconoscimento: --emittente vince sul preambolo; dal nome del file; nessuno con colonne note → avviso
    assert m.componi(os.path.join(FIXTURES, "composizione-ishares-en.csv"), "Z", "spdr")["riconosciuto_da"] == "--emittente"
    g = os.path.join(tmp, "posizioni.csv")
    with open(g, "w", encoding="utf-8") as f:
        f.write("Name,Sector,Country,Weight\nA,Energy,Italy,100\n")
    c = m.componi(g, "G")
    assert c["emittente"] is None and c["riconosciuto_da"] == "nessuno" and any("regole generiche" in w for w in c["avvisi"])
    os.rename(g, os.path.join(tmp, "SWDA_holdings_ishares.csv"))
    assert m.componi(os.path.join(tmp, "SWDA_holdings_ishares.csv"), "G")["riconosciuto_da"] == "nome del file"
    # Review Focus 5: ETF obbligazionario, settore vuoto ovunque → solo paesi, avviso
    with open(g, "w", encoding="utf-8") as f:
        f.write("Name,Sector,Asset Class,Location,Weight (%)\nBTP 2030,-,Fixed Income,Italy,60\nOAT 2031,-,Fixed Income,France,40\n")
    c = m.componi(g, "B")
    assert c["settori"] == {} and r2(c["paesi"]) == {"IT": 60.0, "FR": 40.0} and any("settore" in w for w in c["avvisi"])
    # soglia della liquidità: 6% di cash → avviso; Telecommunication Services → Communication Services con avviso
    with open(g, "w", encoding="utf-8") as f:
        f.write("Name,Sector,Asset Class,Location,Weight (%)\nA,Telecommunication Services,Equity,Italy,94\n"
                "CASH,Cash and/or Derivatives,Cash,Italy,6\n")
    c = m.componi(g, "C")
    assert c["settori"] == {"Communication Services": 1.0}
    assert any("liquidit" in w for w in c["avvisi"]) and any("Telecommunication" in w for w in c["avvisi"])
finally:
    shutil.rmtree(tmp, ignore_errors=True)
assert m.SETTORI_GICS == carica_modulo(asset(*CU)).SETTORI_GICS
```

- [ ] **Step 3: Scrivi il test `T16 composizione ETF: nomi sconosciuti, somme incoerenti e classificazione mista respinti`** — da riga di comando, in una cartella temporanea con un `composizione.csv` preesistente (contenuto e `os.path.getmtime` salvati prima):
  - due paesi sconosciuti (`Atlantide` 30, `Lemuria` 20) e un settore sconosciuto (`Spazio` 10) nello stesso file → rc 1, `se` contiene `Atlantide`, `Lemuria` e `Spazio`, e la parola `segnala`;
  - pesi che sommano a 60 → rc 1 e `sommano a 60` in `se`;
  - peso `abc` → rc 1 con `abc` e il numero di riga;
  - `Technology` e `Information Technology` nello stesso file → rc 1 e `mista` in `se`;
  - solo righe `Cash` → rc 1 («nessuna riga»);
  - dopo ciascuno: `composizione.csv` con lo stesso contenuto e lo stesso mtime, nessun `Traceback`, nulla di `ERRORE:` su stdout.

- [ ] **Step 4: Esegui e verifica che falliscano** — `python tests/run_tests.py --only "T16 composizione ETF"` → i due test nuovi FAIL.

- [ ] **Step 5: Implementa le costanti e le funzioni dell'Interfaces block** e collega `main()` a `componi()` (il CSV si scrive nel Task 3).

- [ ] **Step 6: Esegui e verifica che passino** — stesso comando → PASS.

- [ ] **Step 7: Commit** — `feat: composizione per settore GICS e paese ISO, schede degli emittenti ed esclusioni (T16)`

---

### Task 3: Uscita (CSV fuso, `--json`, report) e interfaccia comune

**Files:**
- Modify: `skills/it-pianificazione-obiettivi/assets/importa-composizione-etf.py` (`main()` completo)
- Modify: `tests/run_tests.py`: `SCRIPT_CLI` aggiunge `("it-pianificazione-obiettivi", "importa-composizione-etf.py")` dopo `capitale-umano.py`; `ARGOMENTI_DEFAULT["importa-composizione-etf.py"] = ("--file", os.path.join(FIXTURES, "composizione-ishares-en.csv"), "--strumento", "ETF MSCI World")`; in `t_cli_help` il conteggio 16 → 17 e `errore_pulito(asset(*CE), "--file", "/non/esiste.csv", "--strumento", "X", atteso="non trovato")`; in `t_cli_utf8` l'asserzione sul «€» diventa: ogni script stampa «€», tranne `importa-composizione-etf.py` che deve stampare «à» (il report contiene «liquidità»); il controllo su `�` resta per tutti
- Test: `tests/run_tests.py`

**Interfaces:**
- Consumes: `componi()` del Task 2.
- Produces:
  - CLI della spec §2.1: `--file` e `--strumento` ripetibili (`action="append"`, obbligatori), `--emittente` con `choices=sorted(SCHEDE)`, `--out` (default `composizione.csv`), `--json` da `cli(json=True)`. Numero di `--file` diverso da `--strumento`, o uno `--strumento` ripetuto → `args.parser.error(...)` (rc 2).
  - `leggi_out(path) -> list[tuple[str | None, list[str]]]`: i blocchi del file esistente in ordine, `(strumento, righe)` dove `righe` sono le righe di testo del blocco compreso il suo commento; i commenti non seguiti da righe di uno strumento formano blocchi con `strumento=None`. Riconosce il vecchio formato (colonne `strumento;settore;peso`: righe convertite in `strumento;settore;<settore>;<peso in percento, due decimali>`, pesi in frazione portati a percento con la stessa regola di `leggi_composizione`) e il nuovo; altre colonne → `errore()` senza scrivere. Ritorna anche se il file era nel vecchio formato.
  - `righe_strumento(c: dict, oggi: str) -> list[str]`: il commento della spec §3.1 (`# <strumento>: <Emittente o «emittente non riconosciuto»>, <file>, posizioni al <GG/MM/AAAA>` se nota`, importato il <GG/MM/AAAA>; esclusi liquidità e derivati <pct>, settore non classificato <pct>, paese non classificato <pct>` — le quote nulle si omettono), poi le righe `settore` e `paese` con `numero(peso * 100, 2)`.
  - `scrivi_out(path, blocchi, nuovi: list[dict], oggi: str)`: toglie i blocchi degli strumenti importati, aggiunge i nuovi in fondo nell'ordine della riga di comando, scrive con BOM e l'intestazione `strumento;dimensione;voce;peso`; percorso non scrivibile → `errore()`.
  - Data d'importazione: `datetime.date.today()`; `cli()` si chiama senza `spazio` (lo script non ha costanti sovrascrivibili), e i test confrontano la riga di commento con una regex sulla data. Le quote del commento sono `pct(x, 2)`.
  - I commenti che precedono l'intestazione del file esistente restano in testa, sopra l'intestazione riscritta.
  - Report della spec §3.5 su stdout; con `--json -` solo il JSON su stdout.

- [ ] **Step 1: Scrivi il test `T16 composizione ETF: CSV fuso con l'esistente, formato, --json e report`**

```python
tmp = tempfile.mkdtemp()
try:
    out = os.path.join(tmp, "composizione.csv")
    with open(out, "w", encoding="utf-8") as f:     # vecchio formato, scritto a mano, con un commento libero
        f.write("# compilato a mano\nstrumento;settore;peso\nETF Europa;Financials;0,6\nETF Europa;Industrials;0,4\n"
                "ETF MSCI World;Energy;100\n")
    en = os.path.join(FIXTURES, "composizione-ishares-en.csv")
    uscite = []
    for _ in range(2):                             # Review Focus 3: reimportare due volte non duplica
        rc, so, se = run_script_split(asset(*CE), "--file", en, "--strumento", "ETF MSCI World",
                                      "--out", out, "--json", os.path.join(tmp, "c.json"), cwd=tmp)
        assert rc == 0, se[-400:]
        uscite.append(so)
    assert "convertito" in uscite[0] and "convertito" not in uscite[1]   # solo il primo giro trova il vecchio formato
    testo = open(out, encoding="utf-8-sig").read()
    assert open(out, "rb").read().startswith(b"\xef\xbb\xbf")
    righe = testo.splitlines()
    assert righe[0] == "# compilato a mano" and righe[1] == "strumento;dimensione;voce;peso"
    assert righe[2:4] == ["ETF Europa;settore;Financials;60,00", "ETF Europa;settore;Industrials;40,00"]
    assert sum(1 for r in righe if r.startswith("# ETF MSCI World:")) == 1
    commento = next(r for r in righe if r.startswith("# ETF MSCI World:"))
    assert re.fullmatch(r"# ETF MSCI World: iShares, composizione-ishares-en\.csv, posizioni al 30/09/2026, "
                        r"importato il \d\d/\d\d/\d{4}; esclusi liquidità e derivati 1,00%", commento), commento
    mw = [r for r in righe if r.startswith("ETF MSCI World;")]
    assert mw[0] == "ETF MSCI World;settore;Information Technology;40,40" and "ETF MSCI World;paese;KR;10,10" in mw
    assert len(mw) == 10 and not any(";Energy;100" in r for r in righe)
    for dim in ("settore", "paese"):
        tot = sum(float(r.split(";")[3].replace(",", ".")) for r in mw if r.split(";")[1] == dim)
        assert abs(tot - 100) <= 0.05, (dim, tot)
    assert "ETF Europa" in so                                            # il report dice cosa ha conservato
    assert "Tecnologia dell'informazione" in so and "Corea del Sud" in so and "Weight (%)" in so
    d = json.load(open(os.path.join(tmp, "c.json"), encoding="utf-8"))
    assert d["out"] == out and [s["strumento"] for s in d["strumenti"]] == ["ETF MSCI World"]
    s = d["strumenti"][0]
    assert {"strumento", "emittente", "riconosciuto_da", "file", "data_posizioni", "classificazione", "colonne",
            "titoli", "esclusi", "settori", "paesi", "avvisi"} == set(s)
    assert abs(sum(s["settori"].values()) - 1) < 1e-9 and abs(sum(s["paesi"].values()) - 1) < 1e-9
    # --json - : solo JSON su stdout, --out scritto lo stesso
    rc, so, se = run_script_split(asset(*CE), "--file", en, "--strumento", "Y", "--out", out, "--json", "-", cwd=tmp)
    assert rc == 0 and json.loads(so)["strumenti"][0]["strumento"] == "Y" and "Y;paese;US;50,51" in open(out, encoding="utf-8-sig").read()
    # due file in una chiamata; riga di comando spaiata o ripetuta → rc 2
    rc, so, se = run_script_split(asset(*CE), "--file", en, "--strumento", "A", "--file",
                                  os.path.join(FIXTURES, "composizione-ishares-it.csv"), "--strumento", "B", "--out", out, cwd=tmp)
    assert rc == 0 and "A;settore;Energy;9,09" in open(out, encoding="utf-8-sig").read()
    for args in (("--file", en, "--file", en, "--strumento", "A"), ("--file", en, "--strumento", "A", "--file", en, "--strumento", "A")):
        rc, so, se = run_script_split(asset(*CE), *args, "--out", out, cwd=tmp)
        assert rc == 2 and "usage:" in se, se[-300:]
    # un --out con colonne sconosciute non si sovrascrive
    strano = os.path.join(tmp, "strano.csv")
    with open(strano, "w", encoding="utf-8") as f:
        f.write("isin;quota\nIE00;1\n")
    rc, so, se = run_script_split(asset(*CE), "--file", en, "--strumento", "A", "--out", strano, cwd=tmp)
    assert rc == 1 and open(strano, encoding="utf-8").read() == "isin;quota\nIE00;1\n", se[-300:]
finally:
    shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 2: Esegui e verifica che fallisca** — `python tests/run_tests.py --only "T16 composizione ETF: CSV"` → FAIL.

- [ ] **Step 3: Implementa `leggi_out`, `righe_strumento`, `scrivi_out` e il `main()` completo**; aggiorna `SCRIPT_CLI`, `ARGOMENTI_DEFAULT`, `t_cli_help` e `t_cli_utf8` come nei Files.

- [ ] **Step 4: Esegui e verifica che passino** — `python tests/run_tests.py --only "T16 composizione ETF" --only "T9"` → PASS, compresi `T9 interfaccia` (×2) e `T9 formati`.

- [ ] **Step 5: Commit** — `feat: composizione.csv fuso con l'esistente, --json e report dell'importatore (T16)`

---

### Task 4: `capitale-umano.py` legge i due formati e la catena

**Files:**
- Modify: `skills/it-pianificazione-obiettivi/assets/capitale-umano.py` (`leggi_composizione`, docstring dell'help di `--composizione`)
- Test: `tests/run_tests.py`

**Interfaces:**
- Consumes: il CSV del Task 3.
- Produces: `leggi_composizione(path) -> dict[str, dict[str, float]]` invariata nella firma e nel risultato; in più accetta le colonne `strumento;dimensione;voce;peso` e ne legge solo le righe `settore` (spec §3.3). `dimensione` diversa da `settore`/`paese` → `errore()`. Uno strumento con solo righe `paese` non compare nel risultato. Help di `--composizione`: «CSV della composizione (strumento;dimensione;voce;peso da importa-composizione-etf.py, o strumento;settore;peso compilato a mano)».

- [ ] **Step 1: Scrivi il test `T16 composizione ETF: capitale-umano legge i due formati, catena dall'importatore`**

```python
cu = carica_modulo(asset(*CU))
vecchio = asset("it-pianificazione-obiettivi", "esempio-composizione.csv")
atteso_vecchio = cu.leggi_composizione(vecchio)
assert abs(atteso_vecchio["ETF MSCI World"]["Information Technology"] - 0.27) < 1e-12   # invariato
tmp = tempfile.mkdtemp()
try:
    out = os.path.join(tmp, "composizione.csv")
    rc, so, se = run_script_split(asset(*CE), "--file", os.path.join(FIXTURES, "composizione-ishares-en.csv"),
                                  "--strumento", "ETF MSCI World", "--file", _xlsx_emittente("vanguard", tmp),
                                  "--strumento", "ETF FTSE", "--out", out, cwd=tmp)
    assert rc == 0, se[-300:]
    comp = cu.leggi_composizione(out)
    assert set(comp) == {"ETF MSCI World"}                                   # il Vanguard in ICB non ha settori
    assert abs(comp["ETF MSCI World"]["Information Technology"] - 0.4040) < 1e-9
    dati = json.load(open(asset("it-pianificazione-obiettivi", "esempio-capitale-umano.json"), encoding="utf-8"))
    dati["persona"]["settore"] = "Information Technology"
    dati["posizioni"] = [{"asset_class": "azionario", "valore": 60000, "strumento": "ETF MSCI World"},
                         {"asset_class": "azionario", "valore": 20000, "strumento": "ETF FTSE"},
                         {"asset_class": "azionario", "valore": 20000, "strumento": "etf msci world"}]
    pd_ = os.path.join(tmp, "cu.json"); json.dump(dati, open(pd_, "w", encoding="utf-8"))
    rc, so, se = run_script_split(asset(*CU), "--dati", pd_, "--composizione", out, "--json", os.path.join(tmp, "o.json"), cwd=tmp)
    assert rc == 0, se[-300:]
    z = json.load(open(os.path.join(tmp, "o.json"), encoding="utf-8"))["settore"]
    assert abs(z["quota_settore_fin"] - 0.4040) < 1e-4, z                   # solo la posizione con la composizione
    assert z["mancanti"] == ["ETF FTSE", "etf msci world"], z["mancanti"]  # Review Focus 4: il refuso è visibile
    assert "etf msci world" in so
    with open(out, "a", encoding="utf-8") as f:
        f.write("ETF MSCI World;valuta;USD;100\n")
    rc, so, se = run_script_split(asset(*CU), "--dati", pd_, "--composizione", out, cwd=tmp)
    assert rc == 1 and "valuta" in se, se[-300:]
finally:
    shutil.rmtree(tmp, ignore_errors=True)
```

`sovrapposizione()` divide per il valore delle sole posizioni azionarie con una composizione, quindi la quota è quella dell'unica posizione composta (0,4040). `sovrapposizione()` non cambia.

- [ ] **Step 2: Esegui e verifica che fallisca** — `python tests/run_tests.py --only "T16 composizione ETF: capitale-umano"` → FAIL («servono le colonne strumento;settore;peso»).

- [ ] **Step 3: Implementa i due formati in `leggi_composizione`** — dopo il `DictReader`, se le colonne contengono `dimensione` e `voce`, filtra le righe `settore` e usa `voce` come settore; il resto del codice (validazione GICS, scala, somma) è condiviso.

- [ ] **Step 4: Esegui e verifica che passino** — `python tests/run_tests.py --only "T15" --only "T16"` → PASS: i test T15 sulla sovrapposizione danno gli stessi numeri.

- [ ] **Step 5: Commit** — `feat: capitale-umano legge la composizione importata, oltre a quella compilata a mano (T16)`

---

### Task 5: Documentazione, mutanti e chiusura

**Files:**
- Create: `skills/it-pianificazione-obiettivi/references/composizione-etf.md` (spec §6: dove si scarica il file per emittente, con il pulsante e il formato; colonne riconosciute; esclusioni; la tabella dello stato dei layout della spec §4.3; limiti della spec §9; licenza; come segnalare un nome non riconosciuto; indice se supera le 100 righe; gli esempi di comando con `python "${CLAUDE_SKILL_DIR}/assets/importa-composizione-etf.py"`, mai a nome nudo, come vuole `t_dove_lavorare`)
- Modify: `skills/it-pianificazione-obiettivi/references/capitale-umano.md` (il punto su `--composizione`: prima l'importatore, la compilazione a mano come alternativa, rimando a `composizione-etf.md`)
- Modify: `skills/it-pianificazione-obiettivi/SKILL.md` (Step 8: il passo `python "${CLAUDE_SKILL_DIR}/assets/importa-composizione-etf.py" --file … --strumento …` prima di `capitale-umano.py`, con la frase «`--strumento` va scritto come il campo `strumento` delle posizioni»; elenco degli asset e delle reference; `metadata.version` 0.22 → 0.23; il file resta sotto le 500 righe)
- Modify: `commands/capitale-umano.md` (una frase: per la diagnosi 4 la composizione si importa dal file delle posizioni dell'emittente con l'importatore)
- Modify: `skills/it-revisione/SKILL.md` (riga «Capitale umano» del contratto di input: «con `--composizione` da `importa-composizione-etf.py` per il settore»)
- Modify: `README.md` («Tutti i 16 script» → 17; nella tabella delle skill it-pianificazione-obiettivi v0.23 con «importatore della composizione degli ETF»; conteggio dei test; tabella rigenerata con `python tests/run_tests.py --tabella-test`; in «Dove vanno i tuoi dati» una frase: i file degli emittenti restano nella cartella di lavoro e lo script non li invia a nessuno)
- Modify: `CHANGELOG.md` («Non rilasciato»: voce **Importatore della composizione degli ETF** (T16), in testa; «Storia delle skill»: it-pianificazione-obiettivi 0.23)
- Modify: `ROADMAP.md` (T16: la riga ad alta priorità diventa una voce spuntata con spec e piano; le due evolutive della spec §8 come voci da decidere)
- Create: `docs/sviluppo/revisioni/esito-t16a.json` (verbale dei mutanti, chiavi come `esito-t12.json`: `branch`, `data`, `applicati`, `non_applicati`, con `mutanti` al posto di `mutanti_f032`, e `revisione` compilata dopo la revisione finale)
- Test: `tests/run_tests.py`

**Interfaces:**
- Consumes: la CLI del Task 3.

- [ ] **Step 1: Scrivi il test `T16 composizione ETF: skill, reference, comando e revisione allineati`**

```python
skill = open(os.path.join(SKILLS, "it-pianificazione-obiettivi", "SKILL.md"), encoding="utf-8").read()
step8 = skill.split("Step 8")[1]
assert "${CLAUDE_SKILL_DIR}/assets/importa-composizione-etf.py" in step8 and "--strumento" in step8
assert step8.index("importa-composizione-etf.py") < step8.index("capitale-umano.py --dati")
assert "references/composizione-etf.md" in skill and 'version: "0.23"' in skill
ref = open(os.path.join(SKILLS, "it-pianificazione-obiettivi", "references", "composizione-etf.md"), encoding="utf-8").read()
for parola in ("iShares", "Xtrackers", "Vanguard", "Amundi", "SPDR", "ICB", "da confermare", "non si ridistribuisc"):
    assert parola in ref, parola
assert "importa-composizione-etf.py" in open(os.path.join(SKILLS, "it-pianificazione-obiettivi", "references", "capitale-umano.md"), encoding="utf-8").read()
assert "importa-composizione-etf.py" in open(os.path.join(ROOT, "commands", "capitale-umano.md"), encoding="utf-8").read()
rev = open(os.path.join(SKILLS, "it-revisione", "SKILL.md"), encoding="utf-8").read()
assert "importa-composizione-etf.py" in rev.split("Contratto di input")[1]
roadmap = open(os.path.join(ROOT, "ROADMAP.md"), encoding="utf-8").read()
t16 = roadmap.split("**T16")[1]
assert "composizione-etf" in t16 and "Look-through" in t16 and "tedesc" in t16
```

- [ ] **Step 2: Esegui e verifica che fallisca** — `python tests/run_tests.py --only "T16 composizione ETF: skill"` → FAIL.

- [ ] **Step 3: Scrivi documentazione, README, CHANGELOG e ROADMAP** come nei Files. Le description delle skill non cambiano (restano entro 1.024 caratteri). Rigenera la tabella con `python tests/run_tests.py --tabella-test` e incollala; aggiorna il conteggio dei test.

- [ ] **Step 4: Esegui i mutanti della spec §7.11** su una copia di lavoro, uno alla volta, con `python -B` o cancellando `__pycache__` (vedi HANDOFF: il bytecode resta vecchio con mutanti della stessa lunghezza):
  1. rinormalizzazione tolta (pesi divisi per il totale dei pesi numerici invece che per quello delle righe classificate);
  2. pesi negativi non esclusi;
  3. scala invertita (frazione trattata come percento);
  4. precedenza tra colonne candidate rovesciata (vince l'ultima).

  Expected: per ciascuno almeno un test `T16` FAIL. Ripristina il file (`git diff` vuoto) e scrivi `esito-t16a.json` con mutante, test che lo uccide ed esito.

- [ ] **Step 5: Esegui la suite completa**

Run: `python tests/run_tests.py --skip freshness`
Expected: tutti PASS (i test di LibreOffice e del browser possono risultare saltati in locale); in particolare `T16` (×6), `T15`, `T9 interfaccia` (×2), `T9 formati`, `T9 «Dove lavorare»`, `T14 skill`, `T14 comandi`, `igiene: … conteggio`, `T12 README`.

- [ ] **Step 6: Commit** — `docs: importatore della composizione in skill, reference, revisione, README, CHANGELOG e ROADMAP (T16)`

- [ ] **Step 7: Prova su file reali** — se il proprietario ha messo nella cartella di lavoro file scaricati da iShares, Vanguard o Amundi, lancia l'importatore su ciascuno (mai copiarli nel repository) e aggiorna `verificato` delle schede e la tabella della reference; un nome non riconosciuto si aggiunge ai sinonimi con un test. Senza file, le schede restano «da confermare» e lo si dice nel riepilogo finale.
