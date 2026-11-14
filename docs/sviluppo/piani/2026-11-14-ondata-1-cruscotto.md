# Ondata 1, cruscotto (confronto tra revisioni, versione anonimizzata): piano di implementazione

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ogni revisione lascia una foto dei suoi numeri, il cruscotto mostra cosa è cambiato rispetto alla precedente, e la pagina si può generare in una versione senza importi né nomi, da mostrare ad altri.

**Architecture:** La foto di una revisione è il bundle che `genera-cruscotto.py` già compone. Lo script impara ad archiviarlo (`--archivia`), a lavorare senza scrivere la pagina (`--solo-dati`), a leggere una revisione precedente da un bundle, da una pagina o da una cartella (`--precedente`) e a mettere le variazioni nel bundle (`confronto`). L'anonimizzazione è una trasformazione applicata per ultima al bundle già composto, guidata da una classificazione dichiarata di ogni campo numerico. Il template disegna una sezione in più e cambia il formato degli importi quando il bundle è anonimo.

**Tech Stack:** Python ≥ 3.11, sola libreria standard in `genera-cruscotto.py` (argparse, json, re, copy); template `cruscotto.html` in HTML, CSS e JavaScript senza librerie; runner `tests/run_tests.py`; Playwright con Chromium per i test nel browser.

**Spec:** `docs/sviluppo/specs/2026-11-14-completamento-roadmap-design.md`, §7 (regole comuni), §7.1 e §7.2 (citata sotto come «spec §N»).

**Ordine:** si esegue dopo il piano del look-through (`2026-11-14-ondata-1-look-through.md`): la classificazione dei campi numerici copre anche le chiavi che quel piano aggiunge al bundle.

## Global Constraints

- **Numeri solo dagli script.** Il confronto usa i valori dei due bundle; il cruscotto non ricalcola e non accetta numeri scritti a mano. Il patrimonio netto resta fuori (spec §7.1, «Perimetro»).
- **Regole del template** (spec T17 §2.2, richiamate dalla spec §7): nessuna risorsa esterna; dati nel DOM solo con `textContent` e `setAttribute`, mai `innerHTML`; numeri all'italiana; tema chiaro e scuro; 375 px senza scorrimento orizzontale; ogni grafico con il dato in testo accanto.
- **Bundle `versione` 2**, con `confronto` e `anonimo` a `null` quando non servono. Si leggono come revisione precedente i bundle di versione 1 e 2.
- **Presentazione neutra del confronto**: segni e numeri, niente verde e rosso; importi nominali, dichiarati tali.
- **Versione anonimizzata**: nessun importo in euro, nessun nome di obiettivo, di broker o di file; mai il lordo e il netto della stessa grandezza; il limite è dichiarato in pagina.
- **Interfaccia**: exit 0, 1 con `ERRORE:` su stderr (classe `ErroreDati`), 2 per la riga di comando (`ap.error`); output UTF-8.
- **Nomi dei test**: `T17 cruscotto: …` e `T17 cruscotto nel browser: …`, nella sezione T17 di `tests/run_tests.py`. Helper esistenti: `_json_esempio()`, `_tutti_i_json()`, `_json_variante(nome, modifica)`, `_cruscotto(*sorgenti, cartella=None, extra=())` (passa sempre `-o`, `--json` e `--data 2026-10-25`; un `--data` in `extra` prevale), `browser()`, `_apri_cruscotto(...)`, `formato_it_percento()`.
- **Test**: suite completa con `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium RICHIEDI_BROWSER=1 RICHIEDI_LIBREOFFICE=1 python3 tests/run_tests.py`; un gruppo con `--only`.
- **README dopo ogni test nuovo**: conteggio dei test e tabella `--tabella-test`, prima del commit.
- **Commit** in italiano, con le due righe di attribuzione della sessione; `(T17)` in coda al messaggio.

## Review Focus

1. **Due revisioni con sezioni diverse** (l'anno scorso senza il capitale umano, quest'anno con): si confronta solo ciò che c'è in entrambe, senza errori e senza righe vuote. Test nel Task 2.
2. **`--precedente` uguale al file di output** (`-o cruscotto.html --precedente cruscotto.html`, il gesto più naturale): la pagina vecchia si legge per intero prima di scrivere la nuova. Test nel Task 2.
3. **Cartella dell'archivio con altri file**: i JSON che non si chiamano `cruscotto-*.json` si ignorano; una foto illeggibile ferma lo script e nomina il file. Test nel Task 1.
4. **Base dell'indice a zero** (capitale allocato 0, o assente): si passa alla base successiva; senza alcun importo la pagina anonima non ha un indice e lo dice. Test nel Task 4.
5. **`--archivia` su un percorso che è un file, o non scrivibile**: `ERRORE:` con codice 1, e nessuna pagina a metà. Test nel Task 1.

---

### Task 1: Archivio, `--solo-dati` e lettura della revisione precedente

**Files:**
- Modify: `skills/it-revisione/assets/genera-cruscotto.py` (`componi_bundle()`, nuove funzioni, `main()`, docstring)
- Test: `tests/run_tests.py` (due helper e un test nuovo dopo `t_t17_html`; `t_t17_bundle`)

**Interfaces:**
- Produces:
  - `componi_bundle()` scrive `"versione": 2`, `"confronto": None`, `"anonimo": None`.
  - `estrai_bundle_da_pagina(html: str) -> dict | None`: il JSON del blocco `<script id="dati" type="application/json">`, o `None` se il blocco manca o contiene ancora il segnaposto.
  - `leggi_precedente(percorso: str, data_corrente: str) -> tuple[str, dict]`: nome del file e bundle della revisione precedente, da un bundle JSON, da una pagina del plugin o da una cartella (tra i `cruscotto-*.json`, la foto con il `generato_il` più recente tra quelli precedenti a `data_corrente`). Solleva `ErroreDati` nei casi dell'elenco della spec §7.1.
  - `archivia(bundle: dict, cartella: str) -> tuple[str, bool]`: scrive `cartella/cruscotto-<generato_il>.json`, creando la cartella; ritorna il percorso e se ha sovrascritto.
  - Riga di comando: `-o/--output` senza default (risolto in `main()`: `cruscotto.html`); `--archivia [CARTELLA]` (`nargs="?"`, `const="revisioni"`); `--solo-dati`; `--precedente FILE|CARTELLA`. Con `--solo-dati` servono `--json` o `--archivia` e non si accetta `-o`: altrimenti `ap.error` (codice 2).
  - Stdout: con `--solo-dati` niente riga `Cruscotto:`, ma `Dati del cruscotto: nessuna pagina scritta`; con `--archivia` la riga `Archiviato: <percorso>`, seguita da ` (sovrascritta la foto dello stesso giorno)` quando succede.
  - Helper di test: `_bundle_di(cartella, nome, *sorgenti, data, extra=()) -> str` e `_come_v1(path, plugin="0.11.0") -> str`.

- [ ] **Step 1: Scrivi gli helper di test**

```python
def _bundle_di(cartella, nome, *sorgenti, data, extra=()):
    """Scrive in cartella/nome il bundle generato dai sorgenti alla data indicata, senza pagina; ritorna il percorso."""
    os.makedirs(cartella, exist_ok=True)
    path = os.path.join(cartella, nome)
    rc, so, se = run_script_split(asset("it-revisione", "genera-cruscotto.py"), *[a for f in sorgenti for a in ("--from", f)],
                                  "--solo-dati", "--json", path, "--data", data, *extra, cwd=cartella)
    assert rc == 0, se[-300:]
    return path


def _come_v1(path, plugin="0.11.0"):
    """Riscrive un bundle come lo scriveva la 0.12.0 (versione 1, senza confronto e anonimo, look-through senza
    regioni e valute), con il plugin di una versione precedente."""
    b = json.load(open(path, encoding="utf-8"))
    b["versione"], b["plugin"] = 1, plugin
    for k in ("confronto", "anonimo"):
        b.pop(k, None)
    for k in ("regioni", "valute", "quota_euro"):
        (b.get("look_through") or {}).pop(k, None)
    json.dump(b, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    return path
```

- [ ] **Step 2: Scrivi il test**

```python
@test("T17 cruscotto: archivio della revisione, --solo-dati, revisione precedente da bundle, pagina e cartella")
def t_t17_archivio():
    G = asset("it-revisione", "genera-cruscotto.py")
    mod, js = carica_modulo(G), _json_esempio()
    tmp = tempfile.mkdtemp()
    try:
        rc, so, se = run_script_split(G, "--from", js["alloc.json"], "--solo-dati", "--archivia", "--data", "2025-11-20", cwd=tmp)
        assert rc == 0 and os.listdir(tmp) == ["revisioni"], (so, se, os.listdir(tmp))       # nessuna pagina
        foto = json.load(open(os.path.join(tmp, "revisioni", "cruscotto-2025-11-20.json"), encoding="utf-8"))
        assert foto["versione"] == 2 and foto["generato_il"] == "2025-11-20" and foto["confronto"] is None and foto["anonimo"] is None
        assert "Archiviato:" in so and "cruscotto-2025-11-20.json" in so and "Cruscotto:" not in so and "sovrascritta" not in so, so
        rc, so, se = run_script_split(G, "--from", js["alloc.json"], "--solo-dati", "--archivia", "--data", "2025-11-20", cwd=tmp)
        assert rc == 0 and "sovrascritta la foto dello stesso giorno" in so, so
        rc, so, se = run_script_split(G, "--from", js["alloc.json"], "--solo-dati", "--archivia", "altrove", "--data", "2026-01-10", cwd=tmp)
        assert rc == 0 and os.path.isfile(os.path.join(tmp, "altrove", "cruscotto-2026-01-10.json")), se
        for args in (("--solo-dati",), ("--solo-dati", "--json", "b.json", "-o", "c.html")):
            rc, so, se = run_script_split(G, "--from", js["alloc.json"], *args, cwd=tmp)
            assert rc == 2 and "--solo-dati" in se, (args, rc, se[-200:])
        # Review Focus 5: l'archivio su un percorso che è un file
        open(os.path.join(tmp, "occupato"), "w", encoding="utf-8").write("x")
        rc, so, se = run_script_split(G, "--from", js["alloc.json"], "--archivia", "occupato", "-o", "p.html", cwd=tmp)
        assert rc == 1 and se.lstrip().startswith("ERRORE:") and "impossibile scrivere" in se and not os.path.exists(os.path.join(tmp, "p.html")), se
        # la revisione precedente: bundle di versione 2 e 1, pagina, cartella
        v2 = _bundle_di(tmp, "prima.json", js["alloc.json"], data="2025-11-20")
        nome, b = mod.leggi_precedente(v2, "2026-10-25")
        assert nome == "prima.json" and b["generato_il"] == "2025-11-20"
        v1 = _come_v1(_bundle_di(tmp, "v1.json", js["alloc.json"], data="2025-11-20"))
        assert mod.leggi_precedente(v1, "2026-10-25")[1]["versione"] == 1
        rc, _, se, b_pagina, html = _cruscotto(js["alloc.json"], extra=("--data", "2025-11-20"))
        pagina = os.path.join(tmp, "vecchio.html")
        open(pagina, "w", encoding="utf-8").write(html)
        assert mod.leggi_precedente(pagina, "2026-10-25")[1] == b_pagina and mod.estrai_bundle_da_pagina(html) == b_pagina
        cartella = os.path.join(tmp, "revisioni")                                   # ha già la foto del 20/11/2025
        _bundle_di(cartella, "cruscotto-2026-10-25.json", js["alloc.json"], data="2026-10-25")   # quella di oggi: si salta
        _bundle_di(cartella, "cruscotto-vecchia.json", js["alloc.json"], data="2026-03-01")      # vale generato_il, non il nome
        open(os.path.join(cartella, "appunti.json"), "w", encoding="utf-8").write("{}")          # Review Focus 3: ignorato
        assert mod.leggi_precedente(cartella, "2026-10-25")[1]["generato_il"] == "2026-03-01"

        def respinto(percorso, data, *attesi):
            try:
                mod.leggi_precedente(percorso, data)
            except mod.ErroreDati as e:
                assert all(a in str(e) for a in attesi), (attesi, str(e))
                return
            raise AssertionError(f"{percorso}: doveva essere respinto")
        respinto(os.path.join(tmp, "non-esiste.json"), "2026-10-25", "non trovat")
        respinto(cartella, "2025-01-01", "nessuna revisione precedente")
        respinto(v2, "2025-11-20", "data", "precedente")                            # stessa data: non è una revisione precedente
        open(os.path.join(tmp, "altro.json"), "w", encoding="utf-8").write('{"a": 1}')
        respinto(os.path.join(tmp, "altro.json"), "2026-10-25", "altro.json", "non è una revisione")
        respinto(asset("it-revisione", "cruscotto.html"), "2026-10-25", "template")
        tre = json.load(open(v2, encoding="utf-8"))
        tre["versione"] = 3
        json.dump(tre, open(os.path.join(tmp, "v3.json"), "w", encoding="utf-8"))
        respinto(os.path.join(tmp, "v3.json"), "2026-10-25", "versione")
        tre["versione"], tre["anonimo"] = 2, {"base": "capitale allocato", "obiettivi": 1, "broker": 0}
        json.dump(tre, open(os.path.join(tmp, "anon.json"), "w", encoding="utf-8"))
        respinto(os.path.join(tmp, "anon.json"), "2026-10-25", "anonimizzata")
        open(os.path.join(cartella, "cruscotto-rotta.json"), "w", encoding="utf-8").write("{rotta")
        respinto(cartella, "2026-10-25", "cruscotto-rotta.json")                    # Review Focus 3: non si salta in silenzio
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 3: In `t_t17_bundle` la versione attesa diventa 2**: `b["versione"] == 2 and b["confronto"] is None and b["anonimo"] is None`.

- [ ] **Step 4: Lancia e verifica il fallimento**

Run: `python3 tests/run_tests.py --only "archivio della revisione"`
Expected: FAIL con codice 2 al primo lancio (`--solo-dati` non riconosciuto).

- [ ] **Step 5: Implementa** secondo le Interfaces. In `main()` l'ordine è: riga di comando, lettura dei sorgenti, lettura della revisione precedente, composizione, e solo alla fine le scritture (archivio, bundle, pagina), ognuna verificata prima di cominciare a scrivere: un errore non lascia file a metà.

- [ ] **Step 6: Lancia i test**

Run: `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium RICHIEDI_BROWSER=1 python3 tests/run_tests.py --only "cruscotto"`
Expected: PASS.

- [ ] **Step 7: README (conteggio e tabella dei test) e commit**

```bash
git add skills/it-revisione/assets/genera-cruscotto.py tests/run_tests.py README.md
git commit -m "feat: archivio della revisione, --solo-dati e lettura della revisione precedente nel cruscotto (T17)"
```

### Task 2: Il confronto nel bundle

**Files:**
- Modify: `skills/it-revisione/assets/genera-cruscotto.py` (tabella `CONFRONTI`, `confronta()`, `main()`, docstring di `componi_bundle()`)
- Test: `tests/run_tests.py` (un helper e un test nuovo dopo `t_t17_archivio`)

**Interfaces:**
- Consumes: `leggi_precedente()` del Task 1.
- Produces:
  - `CONFRONTI`: una riga per grandezza scalare, `(sezione, id, etichetta, formato, estrai)`, con `formato` in `("euro", "percento")` ed `estrai(bundle) -> float | None`. Identificativi dell'elenco minimo: `tasso_lordo_mediana`, `prob_target`, `pensione_inps_lorda`, `montante_fp_mediana`, `pensione_netta_mediana` (sezione `pensione`); `esposizione_finanziaria`, `esposizione_totale`, `patrimonio_finanziario`, `capitale_umano` (sezione `capitale_umano`); `zainetto`, `plus_compensabili` (`fiscalita`); `quota_primi_titoli` (`look_through`); `target_azioni` (`allocazione`); `quota_azionaria_anno_0` (`glide_path`). Le famiglie che dipendono dai dati si generano: i cinque indicatori con il loro `id` (sezione `indicatori`), `peso_<classe>` per ogni classe presente in entrambe le revisioni, `settore_<nome>` per i primi tre settori della revisione di oggi.
  - `confronta(prima: dict, ora: dict) -> dict`: `{"data_precedente": str, "plugin_precedente": str, "versioni_diverse": bool, "voci": [...], "obiettivi": [...]}`. Una voce: `{"sezione", "id", "etichetta", "formato", "prima", "ora", "delta", "delta_rel"}`; `delta_rel` è `delta / prima` per gli importi con `prima` diverso da zero, `None` negli altri casi. Entra solo ciò che è un numero in entrambi i bundle, nell'ordine di `CONFRONTI`.
  - Un obiettivo: `{"nome", "stato", "probabilita", "gia", "versamento"}`, con `stato` in `("presente", "nuovo", "non_piu_presente", "ripetuto")` e le tre grandezze come `{"prima", "ora", "delta"}` (o `None` quando lo stato non è `presente`). Il nome si confronta dopo `strip()`; `versamento` è il versamento «di confidenza».
  - `main()`: con `--precedente` il bundle porta `confronto`; stdout aggiunge `Confronto con la revisione del GG/MM/AAAA (<file>): N grandezze, M obiettivi`.
  - Helper di test: `_revisioni_di_prova(tmp) -> tuple[str, list[str]]`, la revisione precedente (bundle come dalla 0.12.0, senza capitale umano, del 20/11/2025) e i sorgenti di oggi (capitale allocato più alto di 10.000, probabilità del primo obiettivo più bassa di dieci punti, secondo obiettivo rinominato).

- [ ] **Step 1: Scrivi l'helper e il test**

```python
def _revisioni_di_prova(tmp):
    """(bundle della revisione precedente, sorgenti di oggi) per i test del confronto e della versione anonimizzata."""
    tutti = _tutti_i_json()
    prima = _come_v1(_bundle_di(tmp, "prima.json", *[f for f in tutti if not f.endswith("cu.json")], data="2025-11-20"))
    def piu_capitale(d):
        d["capitale"] += 10000
    def obiettivi(d):
        d["obiettivi"][0]["probabilita_successo"] -= 0.10
        d["obiettivi"][1]["nome"] = "Obiettivo rinominato"
    ora = [f for f in tutti if not f.endswith(("alloc.json", "mco.json"))]
    return prima, ora + [_json_variante("alloc.json", piu_capitale), _json_variante("mco.json", obiettivi)]


@test("T17 cruscotto: confronto tra due revisioni, variazioni chiuse, obiettivi nuovi e non più presenti, versioni diverse")
def t_t17_confronto():
    mod, js = carica_modulo(asset("it-revisione", "genera-cruscotto.py")), _json_esempio()
    L = lambda n: json.load(open(js[n], encoding="utf-8"))       # noqa: E731
    tmp = tempfile.mkdtemp()
    try:
        prima, ora = _revisioni_di_prova(tmp)
        rc, so, se, b, html = _cruscotto(*ora, extra=("--precedente", prima))
        assert rc == 0, se[-300:]
        c = b["confronto"]
        assert c["data_precedente"] == "2025-11-20" and c["plugin_precedente"] == "0.11.0" and c["versioni_diverse"] is True
        v = {x["id"]: x for x in c["voci"]}
        cap, p0 = L("alloc.json")["capitale"], L("mco.json")["obiettivi"][0]["probabilita_successo"]
        assert p0 > 0.10, "l'esempio deve lasciare spazio per togliere dieci punti"
        assert v["capitale_allocato"] == {"sezione": "indicatori", "id": "capitale_allocato", "etichetta": "Capitale allocato",
                                          "formato": "euro", "prima": cap, "ora": cap + 10000, "delta": 10000, "delta_rel": 10000 / cap}
        assert abs(v["probabilita_essenziali"]["delta"] + 0.10) < 1e-12 and v["probabilita_essenziali"]["delta_rel"] is None
        assert v["tasso_lordo_mediana"]["formato"] == "percento" and v["tasso_lordo_mediana"]["delta"] == 0
        assert v["zainetto"]["prima"] == L("broker.json")["analisi"]["zainetto_26_equivalente"] and v["zainetto"]["delta"] == 0
        assert {"peso_azionario", "target_azioni", "quota_azionaria_anno_0", "pensione_inps_lorda", "prob_target", "montante_fp_mediana",
                "pensione_netta_mediana", "plus_compensabili", "quota_primi_titoli"} <= set(v), sorted(v)
        assert sum(1 for x in c["voci"] if x["id"].startswith("settore_")) == 3
        # Review Focus 1: la revisione precedente non aveva il capitale umano
        assert not [x for x in c["voci"] if x["sezione"] == "capitale_umano"] and b["capitale_umano"] is not None
        ob, nomi = {o["nome"]: o for o in c["obiettivi"]}, [o["nome"] for o in L("mco.json")["obiettivi"]]
        assert ob[nomi[0]]["stato"] == "presente" and abs(ob[nomi[0]]["probabilita"]["delta"] + 0.10) < 1e-12 and ob[nomi[0]]["gia"]["delta"] == 0
        assert ob[nomi[1]] == {"nome": nomi[1], "stato": "non_piu_presente", "probabilita": None, "gia": None, "versamento": None}
        assert ob["Obiettivo rinominato"]["stato"] == "nuovo"
        assert "Confronto con la revisione del 20/11/2025 (prima.json)" in so, so
        # Review Focus 2: la revisione precedente è la pagina che si sta per riscrivere
        stessa = os.path.join(tmp, "cruscotto.html")
        rc, so, se = run_script_split(asset("it-revisione", "genera-cruscotto.py"), "--from", js["alloc.json"], "-o", stessa, "--data", "2025-11-20", cwd=tmp)
        rc, so, se = run_script_split(asset("it-revisione", "genera-cruscotto.py"), "--from", js["alloc.json"], "-o", stessa,
                                      "--precedente", stessa, "--data", "2026-10-25", cwd=tmp)
        assert rc == 0 and mod.estrai_bundle_da_pagina(open(stessa, encoding="utf-8").read())["confronto"]["data_precedente"] == "2025-11-20", se
        # casi di bordo, sulla funzione: importo di partenza a zero, nome ripetuto
        def minimo(capitale, nomi):
            return {"versione": 2, "generato_il": "2025-01-01", "plugin": "x", "indicatori": [
                        {"id": "capitale_allocato", "etichetta": "Capitale allocato", "valore": capitale, "formato": "euro", "fonte": "", "nota": ""}],
                    "obiettivi": {"obiettivi": [{"nome": n, "probabilita_successo": 0.5, "gia": 0, "versamento_confidenza": 100} for n in nomi]}}
        k = mod.confronta(minimo(0, ["Casa", "Casa"]), dict(minimo(500, ["Casa"]), generato_il="2026-01-01"))
        assert k["voci"][0]["delta"] == 500 and k["voci"][0]["delta_rel"] is None and k["versioni_diverse"] is False
        assert [o["stato"] for o in k["obiettivi"]] == ["ripetuto"], k["obiettivi"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 2: Lancia e verifica il fallimento**

Run: `python3 tests/run_tests.py --only "confronto tra due revisioni"`
Expected: FAIL con `TypeError: 'NoneType' object is not subscriptable` su `b["confronto"]`.

- [ ] **Step 3: Implementa `CONFRONTI` e `confronta()`.** `confronta()` deve reggere un bundle a cui manca qualunque sezione (chiave assente o `None`), compresi quelli di versione 1.

- [ ] **Step 4: Lancia i test**

Run: `python3 tests/run_tests.py --only "T17 cruscotto"`
Expected: PASS.

- [ ] **Step 5: README (conteggio e tabella dei test) e commit**

```bash
git add skills/it-revisione/assets/genera-cruscotto.py tests/run_tests.py README.md
git commit -m "feat: il cruscotto confronta la revisione con la precedente e mette le variazioni nel bundle (T17)"
```

### Task 3: Il confronto nella pagina

**Files:**
- Modify: `skills/it-revisione/assets/cruscotto.html` (`sezioneIndicatori()`, nuova `sezioneConfronto()`, `disegna()`)
- Test: `tests/run_tests.py` (nuovo test dopo `t_t17_browser_contenuti`)

**Interfaces:**
- Consumes: `B.confronto` del Task 2.
- Produces: `section#sez-confronto`, subito dopo `#sez-indicatori`, solo quando `B.confronto` c'è. Formato delle variazioni: importi `+€10.000 (+7,7%)` (senza la parentesi se `delta_rel` è `null`), quote `+1,4 punti` con la funzione `punti()` già nel template.

- [ ] **Step 1: Scrivi il test**

```python
@test("T17 cruscotto nel browser: sezione del confronto con le variazioni all'italiana, assente senza revisione precedente")
def t_t17_browser_confronto():
    sync_playwright, lancia = browser()
    tmp = tempfile.mkdtemp()
    try:
        prima, ora = _revisioni_di_prova(tmp)
        rc, so, se, b, html = _cruscotto(*ora, extra=("--precedente", prima))
        assert rc == 0, se[-300:]
        rc, _, se, _, html_senza = _cruscotto(*ora)
        with sync_playwright() as p:
            br = lancia(p)
            try:
                page, errori, eccezioni, _ = _apri_cruscotto(br, html)
                assert errori == [] and eccezioni == [], (errori, eccezioni)
                assert page.locator("section[id^=sez-]").nth(1).get_attribute("id") == "sez-confronto"
                testo = page.inner_text("#sez-confronto")
                assert "Rispetto alla revisione del 20/11/2025" in testo and "+€10.000 (+7,7%)" in testo and "-10,0 punti" in testo, testo[:1500]
                assert "versione 0.11.0" in testo and "CHANGELOG" in testo and "importi nominali" in testo.lower(), testo[:800]
                assert "Obiettivo rinominato" in testo and "nuovo" in testo and "non più presente" in testo, testo[-800:]
                assert page.locator("#sez-confronto svg").count() >= 1 and page.locator("#sez-confronto table").count() >= 1
                assert "+€10.000" in page.inner_text("#sez-indicatori")
                for brutto in ("NaN", "undefined", "null", "Infinity"):
                    assert brutto not in testo, brutto
                stretta, errori, eccezioni, _ = _apri_cruscotto(br, html, larghezza=375)
                assert stretta.evaluate("document.documentElement.scrollWidth") <= 375 and errori == [] and eccezioni == []
                page, errori, eccezioni, _ = _apri_cruscotto(br, html_senza)
                assert page.locator("#sez-confronto").count() == 0 and errori == [] and eccezioni == []
            finally:
                br.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 2: Lancia e verifica il fallimento**

Run: `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium RICHIEDI_BROWSER=1 python3 tests/run_tests.py --only "sezione del confronto"`
Expected: FAIL: la seconda sezione è `sez-allocazione`.

- [ ] **Step 3: Implementa `sezioneConfronto(c)`** con questi contenuti, nell'ordine:
  - titolo `Rispetto alla revisione del GG/MM/AAAA`;
  - nota fissa: `Importi nominali, ognuno alla data della sua revisione: non sono corretti per l'inflazione.`;
  - se `versioni_diverse`: `La revisione precedente è stata generata con la versione X del plugin: parte delle differenze può venire da dati normativi e metodi aggiornati, non dalla tua situazione (vedi CHANGELOG).`;
  - una tabella per sezione del bundle, con le colonne Voce, Prima, Ora, Variazione (titoli delle sezioni come nel resto della pagina);
  - gli obiettivi presenti: per ognuno due barre affiancate della probabilità, prima e ora, con i valori in testo; in tabella già accumulato e versamento;
  - in testo gli obiettivi nuovi, quelli non più presenti e quelli con il nome ripetuto («non confrontati»).

  Nessun colore di giudizio: le barre usano i colori di serie, le variazioni solo segno e numero.

- [ ] **Step 4: In `sezioneIndicatori()`** aggiungi sotto il valore, quando il confronto ha la voce con lo stesso `id`, una riga `prima €120.000 · +€10.000 (+8,3%)` nello stile della riga della fonte.

- [ ] **Step 5: Lancia i test del cruscotto**

Run: `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium RICHIEDI_BROWSER=1 python3 tests/run_tests.py --only "cruscotto"`
Expected: PASS, compresi i test esistenti sul tema scuro, sui 375 px e su `innerHTML`.

- [ ] **Step 6: README (conteggio e tabella dei test) e commit**

```bash
git add skills/it-revisione/assets/cruscotto.html tests/run_tests.py README.md
git commit -m "feat: sezione «Rispetto alla revisione precedente» nel cruscotto (T17)"
```

### Task 4: Versione anonimizzata, il bundle

**Files:**
- Modify: `skills/it-revisione/assets/genera-cruscotto.py` (classificazione dei campi, `anonimizza()`, `main()`, docstring)
- Test: `tests/run_tests.py` (nuovo test dopo `t_t17_confronto`)

**Interfaces:**
- Consumes: il bundle completo, con `confronto` (Task 2) e con le chiavi del look-through dell'altro piano.
- Produces:
  - Sintassi dei percorsi: punti tra le chiavi, `[]` per gli elementi di una lista, `{}` per i valori di un dizionario a chiavi libere (`fiscalita.per_broker.{}.zainetto_in_scadenza`, `glide_path.obiettivi[].capitale_proiettato[]`).
  - `CAMPI_EURO: frozenset[str]` e `CAMPI_NON_EURO: frozenset[str]`: ogni campo numerico del bundle sta in uno dei due. `CAMPI_EURO_SE_FORMATO = ("indicatori[].valore", "confronto.voci[].prima", "confronto.voci[].ora", "confronto.voci[].delta")`: importi solo se il campo `formato` dello stesso oggetto è `"euro"`.
  - `foglie_numeriche(bundle: dict) -> list[tuple[str, float]]`: percorso generalizzato e valore di ogni numero del bundle (i booleani non sono numeri).
  - `classifica(percorso: str) -> str | None`: `"euro"`, `"altro"`, `"dipende"` (per i percorsi di `CAMPI_EURO_SE_FORMATO`), `None` se il percorso non è dichiarato.
  - `base_indice(bundle: dict) -> tuple[str, float] | None`: la prima base non nulla e maggiore di zero, nell'ordine e con le etichette `capitale allocato`, `valore in portafoglio`, `patrimonio finanziario di oggi`, `totale del ribilanciamento`, `netto dell'ultimo stipendio`, `capitale-ponte`; poi `importo più grande della pagina`; `None` se il bundle non ha importi.
  - `anonimizza(bundle: dict) -> dict`: una copia trasformata secondo la tabella della spec §7.2, con `anonimo = {"base": etichetta | None, "obiettivi": int, "broker": int}`. Campi a `None`: tutti gli importi di `pensione.riscatto`; `pensione.inps.pensione_inps_lorda_annua`, `.montante_finale`, `.ral_finale`; la voce `pensione_inps_lorda` esce da `confronto.voci`. Etichette: `Obiettivo 1…n` e `Broker A, B…`, per ordine di prima comparsa nel bundle. `fonti` tiene solo `tipo`. `fiscalita.avvisi` si svuota e `avvisi_omessi` cresce di altrettanto; `nota` degli ordini e `motivo` del drift a `None`.
  - Riga di comando: `--anonimo`; senza `-o` la pagina è `cruscotto-anonimo.html`; con `--archivia` è `ap.error` (codice 2). Stdout: gli indicatori senza `€` e la riga `Versione anonimizzata: importi come indice (base 100 = <base>); N obiettivi e M broker rinominati`.

- [ ] **Step 1: Scrivi il test**

```python
@test("T17 cruscotto: versione anonimizzata, importi come indice, nomi sostituiti, nessun campo numerico non classificato")
def t_t17_anonimo():
    import copy
    G = asset("it-revisione", "genera-cruscotto.py")
    mod, js = carica_modulo(G), _json_esempio()
    tmp = tempfile.mkdtemp()
    try:
        prima, ora = _revisioni_di_prova(tmp)
        rc, so, se, pieno, _ = _cruscotto(*ora, extra=("--precedente", prima))
        assert rc == 0, se[-300:]
        rc, so, se, anon, html = _cruscotto(*ora, extra=("--precedente", prima, "--anonimo"))
        assert rc == 0, se[-300:]
        # la guardia: ogni numero del bundle completo è dichiarato importo oppure no
        non_classificati = sorted({p for p, _ in mod.foglie_numeriche(pieno) if mod.classifica(p) is None})
        assert not non_classificati, f"campi numerici non classificati: {non_classificati}"
        assert mod.classifica("allocazione.capitale") == "euro" and mod.classifica("obiettivi.obiettivi[].probabilita_successo") == "altro"
        assert mod.classifica("indicatori[].valore") == "dipende" and not (mod.CAMPI_EURO & mod.CAMPI_NON_EURO)
        # indice: un solo fattore, la base vale 100, i rapporti si conservano, il resto non cambia
        cap = pieno["allocazione"]["capitale"]
        assert anon["anonimo"]["base"] == "capitale allocato" and anon["allocazione"]["capitale"] == 100
        assert abs(anon["fiscalita"]["totali"]["totale_valore"] - 100 * pieno["fiscalita"]["totali"]["totale_valore"] / cap) < 1e-9
        o_p, o_a = pieno["obiettivi"]["obiettivi"][0], anon["obiettivi"]["obiettivi"][0]
        assert abs(o_a["gia"] * o_p["target_nominale"] - o_p["gia"] * o_a["target_nominale"]) < 1e-6
        assert o_a["probabilita_successo"] == o_p["probabilita_successo"] and o_a["anni"] == o_p["anni"] and o_a["nome"] == "Obiettivo 1"
        assert anon["pensione"]["netto"]["scenari"] and all(a["tasso_sostituzione_netto"] == p["tasso_sostituzione_netto"]
                                                            for a, p in zip(anon["pensione"]["netto"]["scenari"], pieno["pensione"]["netto"]["scenari"]))
        assert anon["capitale_umano"]["settore"] == pieno["capitale_umano"]["settore"] and anon["look_through"] == pieno["look_through"]
        # nomi, file, testi
        testo = json.dumps(anon, ensure_ascii=False)
        nomi = [o["nome"] for o in pieno["obiettivi"]["obiettivi"]] + list(pieno["fiscalita"]["per_broker"]) + [f["file"] for f in pieno["fonti"]]
        assert nomi and all(n not in testo for n in nomi), [n for n in nomi if n in testo]
        assert anon["anonimo"]["obiettivi"] >= len(pieno["obiettivi"]["obiettivi"]) and anon["anonimo"]["broker"] >= len(pieno["fiscalita"]["per_broker"])
        assert all(set(f) == {"tipo"} for f in anon["fonti"]) and anon["fiscalita"]["avvisi"] == []
        assert anon["fiscalita"]["avvisi_omessi"] == pieno["fiscalita"]["avvisi_omessi"] + len(pieno["fiscalita"]["avvisi"])
        assert all(o["nota"] is None for o in anon["ribilanciamento"]["ordini"]) and all(d["motivo"] is None for d in anon["ribilanciamento"]["drift"].values())
        assert [d["esito"] for d in anon["ribilanciamento"]["drift"].values()] == [d["esito"] for d in pieno["ribilanciamento"]["drift"].values()]
        etichette = {o["nome"] for o in anon["obiettivi"]["obiettivi"]} | {o["nome"] for o in anon["allocazione"]["obiettivi"]}
        assert etichette <= {f"Obiettivo {i}" for i in range(1, 20)} and {o["nome"] for o in anon["confronto"]["obiettivi"]} <= {f"Obiettivo {i}" for i in range(1, 20)}
        # nessun importo vero resta tra gli importi, né il simbolo dell'euro nel blocco dei dati
        veri = {round(v) for p, v in mod.foglie_numeriche(pieno) if mod.classifica(p) == "euro" and abs(v) >= 1000}
        rimasti = {round(v) for p, v in mod.foglie_numeriche(anon) if mod.classifica(p) == "euro"}
        assert veri and not (veri & rimasti), sorted(veri & rimasti)
        blocco = re.search(r'<script id="dati" type="application/json">(.*?)</script>', html, re.S).group(1)
        assert "€" not in blocco and json.loads(blocco) == anon
        # mai il lordo e il netto della stessa grandezza; niente importi di legge del riscatto
        inps = anon["pensione"]["inps"]
        assert inps["pensione_inps_lorda_annua"] is None and inps["montante_finale"] is None and inps["ral_finale"] is None
        assert inps["eta_pensionamento"] == pieno["pensione"]["inps"]["eta_pensionamento"]
        ris = anon["pensione"]["riscatto"]
        assert ris["onere_agevolato"] is None and ris["costo_netto"] is None and ris["rata_mensile"] is None and ris["delta_pensione_lorda_annua"] is None
        assert ris["anni_riscatto"] == pieno["pensione"]["riscatto"]["anni_riscatto"] and ris["modalita"] == pieno["pensione"]["riscatto"]["modalita"]
        assert "pensione_inps_lorda" not in {v["id"] for v in anon["confronto"]["voci"]} and "pensione_inps_lorda" in {v["id"] for v in pieno["confronto"]["voci"]}
        # Review Focus 4: una base a zero si salta; senza importi non c'è indice
        b0 = copy.deepcopy(pieno)
        b0["allocazione"]["capitale"] = 0
        assert mod.base_indice(b0)[0] == "valore in portafoglio"
        assert mod.base_indice({"versione": 2, "indicatori": [], "obiettivi": None}) is None
        # riga di comando: nome di default, niente archivio, stdout senza euro
        rc, so, se = run_script_split(G, "--from", js["alloc.json"], "--anonimo", "--data", "2026-10-25", cwd=tmp)
        assert rc == 0 and os.path.isfile(os.path.join(tmp, "cruscotto-anonimo.html")) and not os.path.exists(os.path.join(tmp, "cruscotto.html")), se
        assert "Versione anonimizzata" in so and "base 100 = capitale allocato" in so and "€" not in so, so
        rc, so, se = run_script_split(G, "--from", js["alloc.json"], "--anonimo", "--archivia", cwd=tmp)
        assert rc == 2 and "--archivia" in se, (rc, se[-200:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 2: Lancia e verifica il fallimento**

Run: `python3 tests/run_tests.py --only "versione anonimizzata"`
Expected: FAIL con codice 2 (`--anonimo` non riconosciuto).

- [ ] **Step 3: Dichiara i campi.** Genera l'elenco dei percorsi numerici dal bundle completo degli esempi (con il confronto) e assegna ciascuno a `CAMPI_EURO` o a `CAMPI_NON_EURO`, uno per uno: sono importi i capitali, i target, i versamenti, i montanti, le pensioni e gli stipendi in euro, gli importi dello zainetto e delle plus, gli importi e le imposte degli ordini, i valori del bilancio e della proiezione del capitale umano; non lo sono pesi, quote, probabilità, tassi, drift e bande, anni, età, conteggi e numeri di simulazioni. Nel dubbio si guarda come il template stampa il campo: `euro(...)` vuol dire importo.

- [ ] **Step 4: Implementa `foglie_numeriche()`, `classifica()`, `base_indice()`, `anonimizza()` e la riga di comando.** `anonimizza()` si applica in `main()` dopo `componi_bundle()` e dopo il confronto, prima di scrivere bundle e pagina.

- [ ] **Step 5: Lancia i test**

Run: `python3 tests/run_tests.py --only "T17 cruscotto"`
Expected: PASS.

- [ ] **Step 6: README (conteggio e tabella dei test) e commit**

```bash
git add skills/it-revisione/assets/genera-cruscotto.py tests/run_tests.py README.md
git commit -m "feat: versione anonimizzata del bundle del cruscotto, con la guardia sui campi numerici (T17)"
```

### Task 5: Versione anonimizzata, la pagina

**Files:**
- Modify: `skills/it-revisione/assets/cruscotto.html` (formato degli importi, testata, piede, `sezionePensione()`, etichette degli assi)
- Test: `tests/run_tests.py` (nuovo test dopo `t_t17_browser_confronto`)

**Interfaces:**
- Consumes: `B.anonimo` del Task 4.
- Produces: quando `B.anonimo` c'è, `euro(x)` stampa l'indice senza simbolo (un decimale da 10 in su, due sotto: `100,0`, `7,69`); la testata mostra il paragrafo `#nota-anonima`; il piede elenca solo i tipi delle fonti; i blocchi con importi a `null` non si disegnano.

- [ ] **Step 1: Scrivi il test**

```python
@test("T17 cruscotto nel browser: versione anonimizzata senza euro né nomi, con la testata che dice cosa resta")
def t_t17_browser_anonimo():
    sync_playwright, lancia = browser()
    tmp = tempfile.mkdtemp()
    try:
        prima, ora = _revisioni_di_prova(tmp)
        rc, so, se, pieno, _ = _cruscotto(*ora, extra=("--precedente", prima))
        rc, so, se, anon, html = _cruscotto(*ora, extra=("--precedente", prima, "--anonimo"))
        assert rc == 0, se[-300:]
        with sync_playwright() as p:
            br = lancia(p)
            try:
                page, errori, eccezioni, _ = _apri_cruscotto(br, html)
                corpo = page.inner_text("body")
                assert errori == [] and eccezioni == [], (errori, eccezioni)
                assert "€" not in corpo, corpo[corpo.index("€") - 60:corpo.index("€") + 20]
                nota = page.inner_text("#nota-anonima")
                assert "Versione anonimizzata" in nota and "base 100 = capitale allocato" in nota, nota
                assert "età" in nota and "settore del lavoro" in nota and "ordine di grandezza del reddito" in nota, nota
                assert page.inner_text('[data-valore="capitale_allocato"]') == "100,0"
                assert "Obiettivo 1" in corpo and "Broker A" in corpo and "(indice)" in corpo
                for nome in [o["nome"] for o in pieno["obiettivi"]["obiettivi"]] + list(pieno["fiscalita"]["per_broker"]) + [f["file"] for f in pieno["fonti"]]:
                    assert nome not in corpo, nome
                pensione = page.inner_text("#sez-pensione")
                assert "Pensione INPS lorda" not in pensione and "Onere agevolato" not in pensione and "n/d" not in pensione, pensione[-900:]
                assert "Tasso di sostituzione lordo" in pensione and "Pensione netta" in pensione
                for brutto in ("NaN", "undefined", "null", "Infinity"):
                    assert brutto not in corpo, brutto
                stretta, errori, eccezioni, _ = _apri_cruscotto(br, html, larghezza=375)
                assert stretta.evaluate("document.documentElement.scrollWidth") <= 375 and errori == [] and eccezioni == []
            finally:
                br.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 2: Lancia e verifica il fallimento**

Run: `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium RICHIEDI_BROWSER=1 python3 tests/run_tests.py --only "senza euro né nomi"`
Expected: FAIL sul simbolo dell'euro nel corpo della pagina.

- [ ] **Step 3: Implementa nel template.**
  - `euro()`: con `B.anonimo` ritorna l'indice; tutte le chiamate esistenti restano come sono.
  - Testata: paragrafo `#nota-anonima`, classe `avviso`, con il testo `Versione anonimizzata: gli importi sono un indice (base 100 = <base>), i nomi di obiettivi e broker sono sostituiti. Restano età, anni, percentuali e settore del lavoro. Nasconde importi e nomi a chi legge; chi conosce già un tuo importo ne ricava gli altri, e dai rapporti rimasti si può stimare l'ordine di grandezza del reddito.` Senza base (`anonimo.base` a `null`) la frase sull'indice non c'è.
  - Dove un grafico o un asse porta importi, il titolo o l'etichetta aggiunge `(indice)`.
  - `sezionePensione()`: la riga della proiezione INPS mostra solo età e anni quando gli importi sono `null`; il blocco del riscatto solo anni, modalità, rientro e anticipo; nessuna barra per valori `null`.
  - Piede: `Fonti:` con i soli tipi quando una fonte non ha `file`.

- [ ] **Step 4: Lancia i test del cruscotto**

Run: `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium RICHIEDI_BROWSER=1 python3 tests/run_tests.py --only "cruscotto"`
Expected: PASS: la pagina completa non cambia, quella anonima non ha euro né nomi.

- [ ] **Step 5: README (conteggio e tabella dei test) e commit**

```bash
git add skills/it-revisione/assets/cruscotto.html tests/run_tests.py README.md
git commit -m "feat: pagina del cruscotto in versione anonimizzata (T17)"
```

### Task 6: Skill, template del report, documentazione e chiusura dell'ondata

**Files:**
- Modify: `skills/it-revisione/SKILL.md` (passi 3, 5 e 6, contratto di input, anti-pattern, Riferimenti), `skills/it-revisione/assets/template-revisione.md`, `commands/cruscotto.md`
- Modify: `README.md`, `CHANGELOG.md`, `ROADMAP.md`, `docs/sviluppo/HANDOFF.md`
- Test: `tests/run_tests.py` (`t_t17_skill`)

- [ ] **Step 1: Aggiungi a `t_t17_skill`**

```python
    passo3 = skill.split("### 3. Avanzamento")[1].split("### 4.")[0]
    assert "--solo-dati" in passo3 and "--archivia" in passo3 and "--precedente revisioni/" in passo3, passo3[-900:]
    passo5 = skill.split("### 5. Report")[1].split("### 6.")[0]
    assert "confronto" in passo5 and "patrimonio netto" in passo5.lower(), passo5
    assert "--precedente" in passo and "--anonimo" in passo and "anonimizzata" in passo and "facoltativ" in passo.lower()
    assert "sottrazioni" in anti and "anonimizzata" in anti, anti[-800:]
    contratto = skill.split("### Contratto di input")[1].split("\n## ")[0]
    assert "| Confronto |" in contratto and "confronto.voci" in contratto and "confronto.obiettivi" in contratto
    modello = open(asset("it-revisione", "template-revisione.md"), encoding="utf-8").read()
    assert "Rispetto alla revisione del" in modello and "due valori che hai scritto tu" in modello
    assert "revisioni/" in dati and "anonimizzata" in dati and "ordine di grandezza del reddito" in dati, dati[-900:]
    nr = open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8").read().split("## v0.12.0")[0]
    assert "confronto" in nr.lower() and "anonimizzata" in nr and "--solo-dati" in nr
    assert "--anonimo" in comando
```

- [ ] **Step 2: Lancia e verifica il fallimento**

Run: `python3 tests/run_tests.py --only "la skill chiede conferma"`
Expected: FAIL su `--solo-dati` nel passo 3.

- [ ] **Step 3: Aggiorna `it-revisione/SKILL.md`** (spec §7.1 e §7.2, «Nella skill»):
  - in fondo al passo 3, «La foto della revisione»: in ogni revisione completa, con i JSON appena scritti, `python "${CLAUDE_SKILL_DIR}/assets/genera-cruscotto.py" --from … --solo-dati --archivia --json bundle.json`, più `--precedente revisioni/` se la cartella ha già una foto; non disegna e non pubblica nulla;
  - passo 5: nel report le variazioni delle grandezze calcolate dagli script vengono da `confronto` del bundle; il patrimonio netto, che non viene da uno script, resta il confronto tra i due valori scritti dall'utente; il passo 2 resta la raccolta di versamenti, eventi e novità normative;
  - passo 6: resta facoltativo; la pagina si genera dagli stessi JSON con lo stesso `--precedente revisioni/`, senza archiviare di nuovo; se l'utente vuole mostrarla ad altri si genera con `--anonimo` e si pubblica quella, dicendo nella richiesta di conferma cosa resta visibile (età, anni, percentuali, settore del lavoro) e il limite (l'ordine di grandezza del reddito si può ancora stimare); un `/cruscotto` fuori da una revisione non archivia, se l'utente non lo chiede;
  - «Contratto di input»: riga `| Confronto | genera-cruscotto.py --precedente … --json (it-revisione) | confronto.voci[] (prima, ora, delta) e confronto.obiettivi[] (stato, probabilità, già accumulato) | report, sezioni 1-3: nessuna cella |`;
  - «Anti-pattern»: mai calcolare con sottrazioni a mano le variazioni di grandezze che vengono dagli script; mai pubblicare la pagina completa quando l'utente vuole mostrarla ad altri: per quello c'è la versione anonimizzata;
  - «Riferimenti»: la riga di `genera-cruscotto.py` nomina archivio, confronto e versione anonimizzata.

  La versione della skill resta 0.10 (alzata dal piano del look-through); la voce `v0.10` del CHANGELOG prende una riga in più. Se questo piano si esegue per primo, la versione si alza qui.

- [ ] **Step 4: Aggiorna `template-revisione.md` e `commands/cruscotto.md`.** Nel template, sezione 1, dopo la riga del patrimonio netto: `*La variazione del patrimonio netto è il confronto tra due valori che hai scritto tu (foglio Patrimonio): non viene da uno script.*`; sezione 2, una riga in testa: `- **Rispetto alla revisione del [data]** (dal confronto del cruscotto): [le variazioni principali, con i numeri di `confronto`]`. Nel comando: una frase su `--precedente` e una su `--anonimo` per la pagina da mostrare ad altri.

- [ ] **Step 5: README, CHANGELOG, ROADMAP.**
  - README, «Dove vanno i tuoi dati»: la cartella `revisioni/` contiene i bundle delle revisioni, con importi ed età, e resta nella cartella di lavoro; la versione anonimizzata sostituisce importi e nomi ma lascia età, settore del lavoro e struttura del piano, e dai rapporti rimasti si può ancora stimare l'ordine di grandezza del reddito. «Output»: il confronto con la revisione precedente.
  - CHANGELOG, «Non rilasciato»: due voci (archivio e confronto, con `--solo-dati`, `--archivia`, `--precedente`; versione anonimizzata, con `--anonimo`, cosa toglie e cosa lascia), e la riga nella storia di it-revisione.
  - ROADMAP, tema T17: «confronto tra due revisioni; versione anonimizzata per la condivisione» diventano fatti, con il rimando alla spec; la linea di taglio della 0.13.0 elenca le ondate 0 e 1.

- [ ] **Step 6: Riscrivi `docs/sviluppo/HANDOFF.md`** allo stato di fine ondata: cosa è entrato (ondate 0 e 1, con i tre piani e la spec), cosa resta al proprietario per la 0.13.0 (pull request, release branch, tag), le ondate 2, 3 e 4 con le date da cui dipendono, e i comandi dell'ambiente compresa la riga per i test nel browser in questa sessione.

- [ ] **Step 7: Suite completa**

Run: la suite completa (vedi Global Constraints).
Expected: tutti i test passati, nessuno saltato.

- [ ] **Step 8: Prova i mutanti** (con `python3 -B`, ripristinando dopo ognuno): `delta` calcolato come `prima - ora`; la foto di oggi non saltata nella cartella; `delta_rel` calcolato anche per le quote; un campo importo spostato in `CAMPI_NON_EURO`; `pensione.inps.ral_finale` non azzerato nella versione anonima; il nome di un broker lasciato negli ordini; `euro()` del template che ignora `B.anonimo`. Ognuno deve far fallire almeno un test: annota quale nel messaggio del commit.

- [ ] **Step 9: README (conteggio e tabella dei test) e commit**

```bash
git add skills commands README.md CHANGELOG.md ROADMAP.md docs/sviluppo/HANDOFF.md tests/run_tests.py
git commit -m "docs: confronto tra revisioni e versione anonimizzata in skill, template, README, CHANGELOG, ROADMAP e HANDOFF (T17)"
```

### Chiusura

Prima del merge su `develop`: la revisione finale prevista dal modo di esecuzione scelto e, se il proprietario la chiede, la revisione avversariale del repository (`docs/sviluppo/workflows/review-tema-roadmap.js`, § 4 di `HANDOFF.md`). Le correzioni vanno in un commit a parte, che ne riporta l'esito. La pull request si apre quando il proprietario la chiede.
