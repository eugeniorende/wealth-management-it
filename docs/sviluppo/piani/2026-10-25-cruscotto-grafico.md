# Cruscotto grafico del piano: piano di implementazione

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un cruscotto HTML autosufficiente che disegna i JSON già prodotti dagli script del plugin, generato da `genera-cruscotto.py` in `it-revisione` e pubblicabile come Artifact solo su conferma dell'utente.

**Architecture:** Lo script Python riconosce i JSON dalle chiavi (tabella di firme), ne estrae un «bundle» minimo e lo incorpora in un template fisso `cruscotto.html` (HTML + CSS + JS vanilla) che disegna le sezioni in SVG nel browser. Il ribilanciamento guadagna un `--json`. I test Python vincolano riconoscimento, valori ed errori; i test con Playwright vincolano il rendering.

**Tech Stack:** Python ≥ 3.11 (solo libreria standard per il nuovo script); HTML/CSS/JS ES2020 senza librerie; runner `tests/run_tests.py` (decoratore `@test`, nessun pytest); Playwright per Python `1.55.0` solo nei test del browser.

**Spec:** `docs/sviluppo/specs/2026-10-25-cruscotto-grafico-design.md` (citata sotto come «spec §N»).

## Global Constraints

- Lo script non fa chiamate di rete e usa solo la libreria standard; il template non carica nulla dall'esterno: nessun `http://`, `https://`, `//` in `src`/`href`, `@import`, `fetch(`.
- Interfaccia comune: `argparse` con `allow_abbrev=False`; exit 0 riuscito, 1 dati con messaggio che inizia per `ERRORE:` su stderr e nulla di `ERRORE:` su stdout, 2 riga di comando errata; stdout e stderr riconfigurati in UTF-8 all'avvio (come `_configura_stdout` del ribilanciamento).
- Numeri in stampa in formato italiano: nessun format spec anglosassone (`{x:,.0f}`, `{x:.1%}`, `{x:.1f}`), lo verifica `t_formati_italiani`; nel template `Intl.NumberFormat('it-IT')`.
- `open()` sempre con `encoding=` esplicito (lo verifica `t_cli_utf8`).
- Nel template i dati entrano nel DOM solo con `textContent` o `setAttribute`: la stringa `innerHTML` non compare nel file.
- Incorporando il bundle nell'HTML ogni `<` del JSON diventa `<`; il segnaposto è `__DATI_CRUSCOTTO__`, presente una sola volta nel template.
- Il bundle non contiene ISIN né descrizioni delle posizioni dell'estratto (spec §4).
- Mai pubblicare un Artifact senza un sì esplicito dell'utente (spec D3); le istruzioni nelle skill lo dicono con queste parole.
- Lingua: italiano, nello stile delle skill esistenti; commenti densi come nel resto degli script. Ogni commit termina con le righe di attribuzione della sessione.
- I test nuovi si chiamano `T17 cruscotto: …` (e `T17 ribilanciamento --json: …`) e stanno in una sezione `# ═══ T17: cruscotto grafico ═══` di `tests/run_tests.py`, subito dopo il blocco T15.

## Review Focus

1. **JSON di una versione precedente del plugin** (una chiave usata assente, es. un `mc.json` senza `tasso_sostituzione_lordo.p90`): `ERRORE:` con file e chiave, nessun traceback. Test nel Task 2.
2. **Valori `null` dove il JSON li ammette** (`capitale_umano.equivalenza`, `eta_sorpasso` con `stato_sorpasso="non_prima_della_fine"`, `mc_obiettivi.rischio_sistemico`): la pagina si disegna e la sezione dice «nessun sorpasso entro la proiezione», senza `NaN` né `null` visibili. Test nel Task 3.
3. **Nessun obiettivo `essenziale`** in `mc_obiettivi`: l'indicatore della probabilità minima non c'è, gli altri sì. Test nel Task 2.
4. **Ribilanciamento senza ordini** (zainetto zero, residuo rinviato): `ordini` è `[]`, la sezione mostra il drift e «nessun ordine». Test nel Task 1 (JSON) e nel Task 3 (pagina).
5. **Nomi con caratteri speciali** (accenti, `&`, `<`, apostrofi negli obiettivi o nei broker): visibili identici nella pagina, nessun markup interpretato. Test nel Task 2 (HTML) e nel Task 3 (testo visibile).

---

### Task 1: `--json` del ribilanciamento

**Files:**
- Modify: `skills/it-rebalance/assets/ribilanciamento-multibroker.py` (`main()` e una funzione nuova vicino a `esporta_ordini`)
- Modify: `skills/it-rebalance/SKILL.md` (Step 4 e «Formato output»: il `--json` e le sue chiavi; `metadata.version` 0.7 → 0.8)
- Modify: `README.md` (tabella delle versioni delle skill: it-rebalance v0.8), `CHANGELOG.md` («Storia delle skill»: voce 0.8 di it-rebalance)
- Test: `tests/run_tests.py`

**Interfaces:**
- Produces: `piano_json(plan: dict, ordini: list[dict]) -> dict` con le chiavi della spec §3.3: `totale`, `totale_post`, `imposta`, `prelievo`, `entrate`, `liquidato`, `drift` (per classe `peso`, `target`, `drift`, `tight`, `wide`, `fuori_banda`, `esito`, `motivo`), `risultante`, `zainetto` (il dict broker → residuo del piano), `ordini` (la lista di `genera_ordini(plan)`, stesse chiavi dei CSV). Opzione CLI `--json FILE`. Il Task 2 riconosce il tipo `ribilanciamento` da `drift`, `risultante`, `ordini`.

- [ ] **Step 1: Scrivi il test `T17 ribilanciamento --json: chiavi del piano, ordini uguali ai CSV, stdout invariato`**

Lancia lo script sull'esempio in una cartella temporanea due volte, con `--out ordini` e con `--out ordini --json piano.json`. Asserzioni:
```python
assert rc == 0 and rc_json == 0
assert out == out_json.replace(riga_json, "")      # riga_json: l'unica riga in più, «JSON del piano: piano.json»
d = json.load(open(os.path.join(tmp, "piano.json"), encoding="utf-8"))
assert {"totale", "totale_post", "imposta", "prelievo", "entrate", "liquidato", "drift", "risultante", "zainetto", "ordini"} <= set(d)
assert d["totale"] == 100000 and d["imposta"] == 0
assert d["drift"]["azionario"]["fuori_banda"] is True and abs(d["drift"]["azionario"]["peso"] - 0.68) < 1e-9
assert abs(d["risultante"]["azionario"] - 0.60) < 1e-6
# gli ordini sono quelli dei CSV: stesse righe (broker, operazione, classe, importo) nello stesso ordine
assert [(o["broker"], o["operazione"], o["classe"], o["importo_eur"]) for o in d["ordini"]] == righe_dai_csv
```
Secondo caso, «Review Focus 4», in-process come i test T7: `m = carica_modulo(...)`, `m.ZAINETTO = {"Fineco": 0}` (con le altre chiavi d'esempio invariate), `plan = m.pianifica()`, `d = m.piano_json(plan, m.genera_ordini(plan))` → `d["ordini"] == []`, `d["drift"]["azionario"]["fuori_banda"] is True` e `json.dumps(d)` non solleva. Terzo: `--json /non/esiste/x.json` → rc 1, stderr che inizia per `ERRORE:` e contiene «impossibile scrivere».

- [ ] **Step 2: Esegui e verifica che fallisca**

Run: `python tests/run_tests.py --only "T17 ribilanciamento"`
Expected: FAIL (rc 2, `--json` non riconosciuto).

- [ ] **Step 3: Implementa `piano_json()` e `--json FILE`**

`--json` scrive dopo `esporta_ordini` (gli ordini si calcolano una volta: `esporta_ordini` li restituisce, oppure `genera_ordini` si chiama una volta in `main` e si passa a entrambe); stampa `JSON del piano: FILE`; `OSError` in scrittura → `ERRORE: impossibile scrivere FILE: …`, exit 1. `json.dump(..., ensure_ascii=False, indent=2)`. I float restano tali (nessun arrotondamento nuovo). L'aiuto di `--json` cita il cruscotto: «il piano in JSON, letto da genera-cruscotto.py di it-revisione».

- [ ] **Step 4: Documenta in `it-rebalance/SKILL.md`**

Nello Step 4 il comando con `--json piano.json`; in «Formato output» un paragrafo con le chiavi della spec §3.3 e la riga «Per vederlo in grafico: `/cruscotto` (it-revisione)». Versione 0.8 in frontmatter, README e CHANGELOG.

- [ ] **Step 5: Esegui la suite e verifica**

Run: `python tests/run_tests.py --only ribilanciamento && python tests/run_tests.py --only "T14 skill" && python tests/run_tests.py --only "T9"`
Expected: tutti PASS (i T7 sullo stdout non cambiano).

- [ ] **Step 6: Commit** — `feat: --json del ribilanciamento, il piano per il cruscotto (T17)`

---

### Task 2: `genera-cruscotto.py`: riconoscimento, bundle, HTML

**Files:**
- Create: `skills/it-revisione/assets/genera-cruscotto.py`
- Create: `skills/it-revisione/assets/cruscotto.html` (in questo task solo lo scheletro: `<!doctype html>`, `<meta charset="utf-8">`, viewport, `<title>Cruscotto del piano</title>`, `<script id="dati" type="application/json">__DATI_CRUSCOTTO__</script>`, testata «bozza educativa» e disclaimer della spec §4.9 in HTML statico; il rendering lo aggiunge il Task 3)
- Create: `tests/fixtures/cruscotto-allocatore.json` (output di `allocatore-capitale.py --json` sul pianificatore d'esempio, salvato una volta: serve agli argomenti di default dei test T9)
- Modify: `tests/run_tests.py` (`SCRIPT_CLI` + `("it-revisione", "genera-cruscotto.py")`, `len(tutti) == 16` in `t_cli_help`, `ARGOMENTI_DEFAULT["genera-cruscotto.py"] = ("--from", <fixture>)`; nuovi test)
- Test: `tests/run_tests.py`

**Interfaces:**
- Consumes: il JSON `ribilanciamento` del Task 1.
- Produces:
  - `FIRME: list[tuple[str, Callable[[dict], bool]]]` in testa allo script, una riga per tipo: `allocatore`, `glide_path`, `mc_obiettivi`, `inps`, `mc_pensione`, `netto_pensione`, `capitale_umano`, `broker`, `ribilanciamento` (spec §3.1), più `IGNORATI` con le firme di `importa-previdenza` (`montante_attuale` e `ral_attuale` e `fp_versamento_annuo`), `ponte-pensione` e `riscatto-laurea` (le chiavi di primo livello dei loro `--json`, lette dal test T12 «--json previdenziali» e dal T13 riscatto).
  - `riconosci(dati: dict) -> str | None`: il tipo, `"ignorato:<nome>"` per gli `IGNORATI`, `None` se nessuna firma.
  - `componi_bundle(sorgenti: dict[str, tuple[str, dict]], data: str, versione_plugin: str) -> dict`: `sorgenti` è tipo → (nome file, JSON); restituisce il bundle della spec §4 (chiavi `versione`=1, `generato_il`, `plugin`, `fonti`, `indicatori`, `allocazione`, `obiettivi`, `glide_path`, `pensione`, `capitale_umano`, `fiscalita`, `ribilanciamento`), `None` per le sezioni senza fonte. Solleva `ErroreDati(messaggio)` per un campo mancante, con file e chiave puntata (es. `«mc.json»: manca tasso_sostituzione_lordo.p90`).
  - `indicatori` è una lista ordinata di `{"id", "etichetta", "valore", "formato": "euro"|"percento", "fonte", "nota"}`, con gli id `capitale_allocato`, `valore_portafoglio`, `probabilita_essenziali` (nota = nome dell'obiettivo), `sostituzione_netta`, `zainetto_in_scadenza`; un indicatore senza fonte manca dalla lista.
  - `incorpora(template: str, bundle: dict) -> str`: sostituisce il segnaposto con `json.dumps(bundle, ensure_ascii=False).replace("<", "\\u003c")`; `ErroreDati` se il segnaposto non compare esattamente una volta.
  - CLI della spec §2.1: `--from FILE` (ripetibile, `action="append"`, obbligatorio: senza nessuno exit 2 via `ap.error`), `-o/--output` (default `cruscotto.html`), `--json FILE`, `--data AAAA-MM-GG` (validata; default `datetime.date.today()`). La versione del plugin si legge da `../../../.claude-plugin/plugin.json` relativo allo script, `"?"` se manca.
  - Stampa finale: `Cruscotto: <percorso>`, una riga per fonte `  <file> → <tipo>`, `Sezioni: …`, e gli indicatori in formato italiano (almeno un `€`: lo chiede `t_cli_utf8`). Usa un `numero()` locale come quello di `genera-ips.py` (questa skill non ha il motore).

- [ ] **Step 1: Scrivi l'helper `_json_esempio()` e il test `T17 cruscotto: ogni output reale riconosciuto con il suo tipo, nessuno con due firme`**

`_json_esempio()` (cache a livello di modulo, come `_tutti_gli_script_cp1252`) lancia in una cartella temporanea, con `--set N_SIM=500` dove esiste: allocatore, glide path, Monte Carlo obiettivi sul pianificatore; capitale umano con l'esempio e `--composizione`; la catena `importa-previdenza --anonimo` → `proiezione-inps` → `montecarlo-pensione` → `netto-pensione` sulle fixture INPS e fondo; `importa-estratto-broker` sulle fixture multi-broker con `--anno 2026`; `ribilanciamento-multibroker --json` sull'esempio. Restituisce `{nome_file: percorso}`. Il test carica il modulo con `carica_modulo` e asserisce:
```python
attesi = {"alloc.json": "allocatore", "glide.json": "glide_path", "mco.json": "mc_obiettivi", "inps.json": "inps",
          "mc.json": "mc_pensione", "netto.json": "netto_pensione", "cu.json": "capitale_umano",
          "broker.json": "broker", "piano.json": "ribilanciamento", "dati.json": "ignorato:importa-previdenza"}
for nome, tipo in attesi.items():
    d = json.load(open(js[nome], encoding="utf-8"))
    assert mod.riconosci(d) == tipo, (nome, mod.riconosci(d))
    assert sum(1 for _, firma in mod.FIRME if firma(d)) <= 1, nome
assert mod.riconosci({"a": 1}) is None
```

- [ ] **Step 2: Scrivi il test `T17 cruscotto: il bundle porta i valori dei JSON di origine e nessuna posizione dell'estratto`**

Lancia lo script con tutti i `--from` dell'helper, `--data 2026-10-25`, `-o c.html --json b.json`. Asserzioni (i valori a destra letti dai JSON di origine, non scritti a mano):
```python
assert rc == 0 and b["generato_il"] == "2026-10-25" and b["versione"] == 1
assert b["plugin"] == json.load(open(os.path.join(ROOT, ".claude-plugin", "plugin.json"), encoding="utf-8"))["version"]
assert b["obiettivi"]["obiettivi"][0]["probabilita_successo"] == mco["obiettivi"][0]["probabilita_successo"]
assert b["pensione"]["tasso_lordo"]["mediana"] == mc["tasso_sostituzione_lordo"]["mediana"]
ind = {i["id"]: i for i in b["indicatori"]}
assert ind["sostituzione_netta"]["valore"] == next(s for s in netto["scenari"] if s["nome"] == "mediana")["tasso_sostituzione_netto"]
assert ind["probabilita_essenziali"]["nota"] == "Fondo di emergenza"
assert b["capitale_umano"]["eta_sorpasso"] == cu["eta_sorpasso"]
assert ind["zainetto_in_scadenza"]["valore"] == broker["analisi"]["zainetto_in_scadenza"]
assert b["ribilanciamento"]["drift"]["azionario"]["drift"] == piano["drift"]["azionario"]["drift"]
assert len(b["ribilanciamento"]["ordini"]) == len(piano["ordini"])
html = open(c_html, encoding="utf-8").read()
for p in broker["posizioni"]:
    assert p["isin"] not in html and p["descrizione"] not in html and p["isin"] not in json.dumps(b)
```
Le chiavi interne delle sezioni (`obiettivi.obiettivi`, `pensione.tasso_lordo`, …) le fissa l'implementazione: il test le usa come le scrive lo Step 5, e il Task 3 le legge da lì. Annotarle nel docstring di `componi_bundle`.

- [ ] **Step 3: Scrivi il test `T17 cruscotto: sezioni assenti, indicatori senza fonte, errori con rc 1 e rc 2`**

```python
# solo l'allocatore
assert b["allocazione"] and all(b[k] is None for k in ("obiettivi", "glide_path", "pensione", "capitale_umano", "fiscalita", "ribilanciamento"))
assert [i["id"] for i in b["indicatori"]] == ["capitale_allocato"]
# Review Focus 3: mco senza essenziali (priorita riscritte a "importante") → nessun indicatore probabilita_essenziali
# Review Focus 1: mc.json senza tasso_sostituzione_lordo.p90 → rc 1, stderr con «mc.json» e «tasso_sostituzione_lordo.p90»
# ERRORE: e rc 1 per: file inesistente («non trovato»), file non JSON, JSON lista, {"a": 1} («non è un output riconosciuto»
#   con l'elenco dei tipi), mc.json e una sua copia mc-uscita.json («stesso tipo» con i due nomi), --data 2026-13-01,
#   -o in una cartella inesistente («impossibile scrivere»)
# rc 2: nessun --from; --from senza valore
# dati.json → rc 0 e «ℹ» con «ignorato» nello stdout
```
Ogni errore rispetta `errore_pulito` di `t_cli_help`: rc 1, stderr che inizia per `ERRORE:`, niente `ERRORE:` su stdout, niente traceback.

- [ ] **Step 4: Scrivi il test `T17 cruscotto: HTML autosufficiente, segnaposto unico, nomi pericolosi innocui`**

```python
tpl = open(asset("it-revisione", "cruscotto.html"), encoding="utf-8").read()
assert tpl.count("__DATI_CRUSCOTTO__") == 1
for testo in (tpl, html):
    assert not re.search(r"https?://|(src|href)\s*=\s*[\"']//|@import|fetch\(", testo)
assert "__DATI_CRUSCOTTO__" not in html
# Review Focus 5: un obiettivo chiamato  </script><img src=x onerror=alert(1)> & l'«anticipo»  nel mco.json
assert "</script><img" not in html and html.count("</script>") == tpl.count("</script>")
dati = json.loads(re.search(r'<script id="dati" type="application/json">(.*?)</script>', html, re.S).group(1))
assert dati["obiettivi"]["obiettivi"][0]["nome"] == nome_pericoloso      # il JSON incorporato si rilegge identico
for tpl_rotto in ("<p>senza</p>", "__DATI_CRUSCOTTO__ __DATI_CRUSCOTTO__"):
    try:
        mod.incorpora(tpl_rotto, {})
        raise AssertionError("incorpora deve respingere il template")
    except mod.ErroreDati:
        pass
```

- [ ] **Step 5: Esegui i quattro test e verifica che falliscano**

Run: `python tests/run_tests.py --only "T17 cruscotto"`
Expected: FAIL (script inesistente).

- [ ] **Step 6: Implementa `genera-cruscotto.py` e lo scheletro di `cruscotto.html`**

Docstring in testa nello stile di `genera-ips.py` (uso, cosa legge, onestà: «il cruscotto disegna i numeri degli script, non ne calcola di nuovi», disclaimer). Lettura dei campi con un helper `campo(dati, "a.b.c", file)` che solleva `ErroreDati` con la chiave puntata. Sezioni del bundle con esattamente i campi della spec §4.2-4.8 (es. fiscalità: `totali` da `analisi` — `totale_valore`, `zainetto_26_equivalente`, `zainetto_in_scadenza`, `zainetto_scaduto`, `plus_latenti_compensabili`, `plus_realizzabili_a_costo_zero`, `imposta_risparmiabile` —, `per_broker` così com'è, `zainetto` con `broker`, `anno`, `scade_il`, `stato`, `importo_26_equivalente`, `avvisi`; ordini con `broker`, `operazione`, `classe`, `categoria_fiscale`, `importo_eur`, `imposta_eur`, `nota`). Aggiungi le voci a `SCRIPT_CLI` e `ARGOMENTI_DEFAULT`, porta `len(tutti) == 16`, salva la fixture.

- [ ] **Step 7: Esegui e verifica**

Run: `python tests/run_tests.py --only "T17" && python tests/run_tests.py --only "T9"`
Expected: tutti PASS, compresi `t_cli_help`, `t_cli_utf8` e `t_formati_italiani` con il nuovo script.

- [ ] **Step 8: Commit** — `feat: genera-cruscotto.py, dai JSON degli script al bundle del cruscotto (T17)`

---

### Task 3: Il template disegna le sezioni (rendering e test nel browser)

**Files:**
- Modify: `skills/it-revisione/assets/cruscotto.html`
- Test: `tests/run_tests.py`

**Interfaces:**
- Consumes: il bundle del Task 2 (chiavi annotate nel docstring di `componi_bundle`), letto da `JSON.parse(document.getElementById("dati").textContent)`.
- Produces: ogni sezione presente è un `<section id="sez-<chiave>">` (`sez-indicatori`, `sez-allocazione`, `sez-obiettivi`, `sez-glide_path`, `sez-pensione`, `sez-capitale_umano`, `sez-fiscalita`, `sez-ribilanciamento`) con almeno un `<svg>` (gli indicatori esclusi: sono riquadri di testo); una sezione `null` non crea nulla nel DOM. Ogni numero mostrato sta in un elemento con `data-valore="<id>"` dove serve ai test: gli indicatori (`data-valore="<id dell'indicatore>"`) e la probabilità di ogni obiettivo (`data-valore="prob-<indice>"`). Il Task 5 non dipende da altro.

- [ ] **Step 1: Scrivi l'helper `browser()` e il test `T17 cruscotto nel browser: si apre senza errori, ogni sezione col suo SVG, nessuna richiesta di rete`**

`browser()` come `ricalcolatore()`: importa `playwright.sync_api`; se manca → `Salta("Playwright non installato")`, salvo `RICHIEDI_BROWSER` → `AssertionError`. Lancio `chromium.launch()`, con `executable_path=os.environ["PLAYWRIGHT_CHROMIUM_EXECUTABLE"]` se la variabile c'è (serve dove Chromium è preinstallato fuori dalla cache di Playwright). Il test genera la pagina con tutti i JSON dell'helper `_json_esempio()`, la apre da `file://` e registra `page.on("console")` di tipo `error`, `page.on("pageerror")` e `page.on("request")`:
```python
assert errori == [] and eccezioni == []
assert all(r.startswith("file://") or r.startswith("data:") for r in richieste), richieste
for k in ("allocazione", "obiettivi", "glide_path", "pensione", "capitale_umano", "fiscalita", "ribilanciamento"):
    assert page.locator(f"#sez-{k} svg").count() >= 1, k
assert page.locator("#sez-indicatori").count() == 1
```
Secondo caso con il solo allocatore: `page.locator("section[id^=sez-]").count() == 2` (indicatori e allocazione).

- [ ] **Step 2: Scrivi il test `T17 cruscotto nel browser: numeri in italiano, nomi intatti, null senza NaN, tema scuro, 375px`**

```python
testo = page.inner_text(f'[data-valore="prob-0"]')
assert testo == formato_it_percento(b["obiettivi"]["obiettivi"][0]["probabilita_successo"])   # es. «49,0%»
assert page.inner_text('[data-valore="sostituzione_netta"]') == formato_it_percento(ind["sostituzione_netta"]["valore"])
corpo = page.inner_text("body")
assert "NaN" not in corpo and "undefined" not in corpo and "null" not in corpo
# Review Focus 5: il nome pericoloso del Task 2 compare identico nel testo, nessun <img> nel DOM
assert nome_pericoloso in corpo and page.locator("img").count() == 0
# Review Focus 2: cu.json con eta_sorpasso null e stato_sorpasso "non_prima_della_fine" → «nessun sorpasso» nella sezione
# Review Focus 4: piano.json con ordini [] → «nessun ordine» in #sez-ribilanciamento
chiaro, scuro = sfondo_body(color_scheme="light"), sfondo_body(color_scheme="dark")
assert chiaro != scuro
page.set_viewport_size({"width": 375, "height": 800})
assert page.evaluate("document.documentElement.scrollWidth") <= 375
src = open(asset("it-revisione", "cruscotto.html"), encoding="utf-8").read()
assert "innerHTML" not in src and "outerHTML" not in src and "insertAdjacentHTML" not in src and "document.write" not in src
```
`formato_it_percento(x)` nel runner: `f"{x * 100:.1f}".replace(".", ",") + "%"` costruito senza format spec anglosassoni nel sorgente degli script (il runner non è controllato da `t_formati_italiani`). Il template formatta le percentuali con 1 decimale, gli euro senza decimali.

- [ ] **Step 3: Esegui e verifica che falliscano**

Run: `pip install playwright==1.55.0` (una volta) e `PLAYWRIGHT_CHROMIUM_EXECUTABLE=… python tests/run_tests.py --only "T17 cruscotto nel browser"`
Expected: FAIL (le sezioni non esistono: lo scheletro non disegna nulla).

- [ ] **Step 4: Implementa il rendering in `cruscotto.html`**

Regole della spec §2.2. Struttura del JS: `el(tag, attrs, testo)` e `svg(tag, attrs)` (unici punti che creano nodi, con `textContent`/`setAttribute`), `fmtEuro`, `fmtPct`, e i grafici `barreOrizzontali`, `barreConFascia` (P10–mediana–P90 con segno del target), `lineeNelTempo` (con area di fascia facoltativa e marcatore verticale), `barreImpilate`, `barreDivergenti` (drift attorno a zero con le due bande); una funzione per sezione (`sezioneAllocazione(b.allocazione, b.ribilanciamento)`, …) che restituisce il `<section>` o `null`. Colori come variabili CSS su `:root`, ridefinite in `@media (prefers-color-scheme: dark)`; `body` con `background` esplicito; tabelle in un contenitore con `overflow-x: auto`; SVG con `viewBox` e `width: 100%`. Tooltip con `<title>`. Testi delle sezioni dalla spec §4: la pensione dice che il netto si legge come tenore di vita; il capitale umano «è una lente, non un target»; la frase del sorpasso per ognuno dei tre `stato_sorpasso` (`gia_superato`, `entro_la_proiezione`, `non_prima_della_fine`).

- [ ] **Step 5: Esegui e verifica**

Run: `PLAYWRIGHT_CHROMIUM_EXECUTABLE=… python tests/run_tests.py --only "T17"`
Expected: tutti PASS. Poi, senza Playwright installato in un altro interprete o con `--skip`, i due test browser risultano saltati, non falliti.

- [ ] **Step 6: Controllo a occhio** — salva uno screenshot a 1200px e uno a 375px, in chiaro e in scuro, nello scratchpad e guardali: etichette leggibili, nessuna sovrapposizione, contrasto sufficiente in scuro. Correggi prima del commit.

- [ ] **Step 7: Commit** — `feat: il cruscotto disegna allocazione, obiettivi, glide path, pensione, capitale umano, fiscalità e ribilanciamento (T17)`

---

### Task 4: CI con il browser

**Files:**
- Modify: `.github/workflows/tests.yml` (job `suite`)
- Modify: `tests/run_tests.py` (`t_check_ruleset`: anche `RICHIEDI_BROWSER` nel job suite)

**Interfaces:**
- Consumes: `browser()` del Task 3 e la variabile `RICHIEDI_BROWSER`.

- [ ] **Step 1: Estendi `t_check_ruleset`**: `assert "RICHIEDI_BROWSER" in suite and "playwright==1.55.0" in suite and "playwright install --with-deps chromium" in suite`.
- [ ] **Step 2: Esegui e verifica che fallisca** — `python tests/run_tests.py --only "igiene CI"` → FAIL.
- [ ] **Step 3: Modifica il workflow**: dopo `pip install -r tests/requirements.txt` uno step `Installa Playwright e Chromium` con `timeout-minutes: 10` e `run: pip install playwright==1.55.0 && python -m playwright install --with-deps chromium`, con un commento nello stile degli altri (perché solo qui e non in `requirements.txt`: il job Windows e chi lancia la suite in locale non ne hanno bisogno); nello step della suite `RICHIEDI_BROWSER: "1"` accanto a `RICHIEDI_LIBREOFFICE`. Nessun cambio a `test-windows`, `release.yml`, `freshness.yml` (lì i test browser si saltano).
- [ ] **Step 4: Esegui e verifica** — `python tests/run_tests.py --only "igiene CI"` → PASS.
- [ ] **Step 5: Commit** — `ci: Playwright e Chromium nel job suite, test del cruscotto obbligatori (T17)`

---

### Task 5: Skill, comando, README, CHANGELOG, ROADMAP

**Files:**
- Modify: `skills/it-revisione/SKILL.md` (passo «Cruscotto grafico», anti-pattern, elenco degli asset, `metadata.version` 0.7 → 0.8)
- Create: `commands/cruscotto.md`
- Modify: `skills/it-pianificazione-obiettivi/SKILL.md`, `skills/it-pianificazione/SKILL.md` (una riga a fine workflow; versione invariata)
- Modify: `README.md`, `CHANGELOG.md`, `ROADMAP.md`
- Test: `tests/run_tests.py`

**Interfaces:**
- Consumes: la CLI del Task 2.

- [ ] **Step 1: Scrivi il test `T17 cruscotto: la skill chiede conferma prima di pubblicare, comando e README allineati`**

```python
skill_md = lambda s: os.path.join(SKILLS, s, "SKILL.md")
skill = open(skill_md("it-revisione"), encoding="utf-8").read()
passo = skill.split("### 6. Cruscotto grafico")[1].split("\n## ")[0]
assert "genera-cruscotto.py" in passo and "${CLAUDE_SKILL_DIR}/assets/genera-cruscotto.py" in passo
assert "chiedi" in passo.lower() and "sì esplicito" in passo and "claude.ai" in passo and "Artifact" in passo
anti = skill.split("## Anti-pattern")[1].split("\n## ")[0]
assert "senza conferma" in anti and "a mano" in anti
assert os.path.isfile(os.path.join(ROOT, "commands", "cruscotto.md"))
readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
assert "/cruscotto" in readme and "genera-cruscotto.py" in readme
dati = readme.split("### Dove vanno i tuoi dati")[1].split("\n### ")[0]
assert "Artifact" in dati and "conferma" in dati
for s in ("it-pianificazione-obiettivi", "it-pianificazione", "it-rebalance"):
    assert "/cruscotto" in open(skill_md(s), encoding="utf-8").read(), s
```

- [ ] **Step 2: Esegui e verifica che fallisca** — `python tests/run_tests.py --only "T17 cruscotto: la skill"` → FAIL.

- [ ] **Step 3: Scrivi il passo `### 6. Cruscotto grafico` nel workflow di `it-revisione/SKILL.md`** — i cinque punti della spec §5, con il comando completo `python "${CLAUDE_SKILL_DIR}/assets/genera-cruscotto.py" --from … -o cruscotto.html`; la domanda di conferma con il testo: la pagina va su claude.ai, contiene importi, età e proiezioni, resta privata finché non la condividi, si può cancellare; «senza un sì esplicito non pubblicare»; il ramo per ambiente (Claude Code: strumento Artifact sul file così com'è; claude.ai e Cowork: artifact HTML con il contenuto del file copiato senza modifiche; senza strumento: il file locale). Due righe negli anti-pattern: «Pubblicare il cruscotto senza conferma» e «Scrivere a mano numeri nel cruscotto o modificare il template nel plugin». `genera-cruscotto.py` e `cruscotto.html` nell'elenco degli asset. Versione 0.8. Il file resta sotto le 500 righe (`t_igiene`).

- [ ] **Step 4: Crea `commands/cruscotto.md`** — sul modello di `capitale-umano.md`: `description` ≤ 250 caratteri, `argument-hint: "[file JSON degli script, oppure niente per quelli della cartella di lavoro]"`, `disable-model-invocation: true`; corpo di al massimo 4 righe non vuote: esegui `it-revisione` (nel plugin `wealth-management-it:it-revisione`) dal passo 6 «Cruscotto grafico» su `$ARGUMENTS`; senza argomenti usa i JSON della cartella di lavoro o indica quali script lanciare; disclaimer «non è consulenza».

- [ ] **Step 5: Righe nelle altre skill** — a fine workflow di `it-pianificazione-obiettivi`, `it-pianificazione` (e già fatto in `it-rebalance` nel Task 1): «I JSON prodotti con `--json` si vedono in grafico con `/cruscotto` (it-revisione), che chiede prima di pubblicare».

- [ ] **Step 6: README, CHANGELOG, ROADMAP**
  - README: `/cruscotto        → it-revisione (cruscotto grafico del piano, pubblicabile come Artifact su conferma)` nell'elenco «Uso»; un punto in «Dove vanno i tuoi dati» (il file resta nella cartella di lavoro; la pubblicazione come Artifact manda la pagina su claude.ai, privata finché non la condividi, e si fa solo su conferma; il cruscotto non porta ISIN né descrizioni delle posizioni); «Tutti i 13 script» → 14; nella tabella delle skill it-revisione v0.8 con «cruscotto grafico»; in «Output» una riga sul cruscotto; il conteggio dei test aggiornato e la tabella rigenerata con `python tests/run_tests.py --tabella-test`.
  - CHANGELOG «Non rilasciato»: voce **Cruscotto grafico** (T17) e voce **`--json` del ribilanciamento** (T17); «Storia delle skill»: it-revisione 0.8.
  - ROADMAP: tema T17 come nella spec §8, con spec e piano, spuntato a fine lavoro.

- [ ] **Step 7: Esegui la suite completa**

Run: `PLAYWRIGHT_CHROMIUM_EXECUTABLE=… RICHIEDI_BROWSER=1 python tests/run_tests.py --skip freshness`
Expected: tutti PASS (i test di LibreOffice possono risultare saltati in locale); in particolare `T14 comandi`, `T14 skill`, `T9 «Dove lavorare»`, `postura: … disclaimer`, `igiene: … conteggio`, `T12 README`.

- [ ] **Step 8: Prova del percorso Artifact in questa sessione** — genera il cruscotto sui JSON d'esempio nello scratchpad e, **solo dopo aver chiesto al proprietario**, pubblicalo come Artifact per verificare che la pagina si apra su claude.ai (spec §9: claude.ai e Cowork restano da provare a mano).

- [ ] **Step 9: Commit** — `docs: passo «Cruscotto grafico» in it-revisione, comando /cruscotto, README, CHANGELOG e ROADMAP (T17)`
