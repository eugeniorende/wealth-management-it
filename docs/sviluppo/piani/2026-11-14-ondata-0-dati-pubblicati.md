# Ondata 0, dati già pubblicati e igiene: piano di implementazione

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Il plugin usa i coefficienti di trasformazione 2027-2028 e il tasso di capitalizzazione 2026 in tutte le copie, i pesi MSCI ACWI di ottobre 2026, e la tabella della freshness del README non può più restare indietro.

**Architecture:** Nessuna funzione nuova: si cambiano dati e testi, più due piccoli interventi di codice (la tabella dei coefficienti prende un nome che non porta il biennio; `importa-previdenza.py` prende l'anno corrente da una costante fissabile, per rendere i test indipendenti dalla data). Ogni dato entra prima in un test con i valori dell'atto, poi negli script, nelle reference e negli Excel. Gli Excel si modificano nell'XML e si ricalcolano con LibreOffice.

**Tech Stack:** Python ≥ 3.11, libreria standard, numpy, openpyxl (solo in lettura nei test); runner `tests/run_tests.py` (decoratore `@test`, nessun pytest); LibreOffice headless tramite `scripts/ricalcola-excel.py`.

**Spec:** `docs/sviluppo/specs/2026-11-14-completamento-roadmap-design.md`, §6 (citata sotto come «spec §N»).

## Global Constraints

- **Fonti primarie.** Prima di scrivere un numero normativo si rilegge l'atto, non questo piano: il decreto direttoriale del 16/10/2026 (`https://www.lavoro.gov.it/documenti-e-norme/normativa/decreto-direttoriale-16102026-coefficienti-trasformazione-montante`), la nota ISTAT prot. 2582754/26 del 16/10/2026 (dalla pagina `https://lavoro.gov.it/notizie/pagine/tasso-annuo-di-capitalizzazione-la-rivalutazione-dei-montanti-contributivi-anno-2026`), la scheda MSCI ACWI (`https://www.msci.com/documents/10199/255599/msci-acwi-net.pdf`). Se un valore letto differisce da quello scritto qui, vale l'atto e lo si annota nel commit.
- **Marcatori.** `Verificato: AAAA-MM` con il mese della rilettura, solo sulla parte verificata; non si ringiovanisce il resto del file.
- **Propagazione.** Ogni dato in tutte le copie (`git grep` su `skills/`, `commands/`, README). `git grep` non entra negli xlsx: lì si cerca nell'XML estratto.
- **Excel.** Mai salvati con openpyxl: si modifica l'XML nello zip, poi `python scripts/ricalcola-excel.py FILE --in-place`.
- **Output cambiati.** Ogni numero che cambia a parità di input va nella sezione «Non rilasciato» di `CHANGELOG.md`, con la dicitura «Output cambiati».
- **Nessuna rete negli script.** Gli script del plugin leggono solo file locali.
- **Test.** Suite completa: `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium RICHIEDI_BROWSER=1 RICHIEDI_LIBREOFFICE=1 python3 tests/run_tests.py` (in questa sessione Playwright per Python è già installato: `pip install playwright==1.55.0`). Un solo gruppo: `python3 tests/run_tests.py --only "sottostringa del nome"`. Con i mutanti usare `python3 -B`.
- **README dopo ogni test nuovo.** Due test di igiene lo pretendono: il numero dei test nella sezione «Test» è `grep -c '^@test' tests/run_tests.py`, e la tabella «Copertura degli strumenti» è l'output di `python3 tests/run_tests.py --tabella-test`. Ogni task che aggiunge un test li aggiorna prima del commit.
- **Commit** in italiano, con le due righe di attribuzione della sessione in coda; un commit per task.

## Review Focus

1. **JSON salvati prima dell'aggiornamento.** Chi ha in cartella un `inps.json` della 0.12.0 e lo passa con `--from` a `riscatto-laurea.py` o `ponte-pensione.py` porta a valle il coefficiente vecchio. Ci si aspetta che la skill e il changelog dicano di rilanciare la catena. Test nel Task 2.
2. **La copia dell'Excel che l'utente ha già compilato.** Il plugin aggiorna il modello, non il file nella cartella di lavoro: ci si aspetta l'istruzione su cosa fare del proprio foglio `Coefficienti`. Test nel Task 2.
3. **`--set ANNO_CORRENTE` con un valore che non è un anno** (`1990`, `2026.5`, un testo): errore pulito con codice 1, non un traceback. Test nel Task 4.
4. **Gennaio 2027, prima del tasso 2027.** Lo script lanciato nel 2027 deve avvisare che il tasso 2027 non è pubblicato e lasciare il montante al valore del 31/12/2026. Test nel Task 4.
5. **Età di pensionamento non intera.** Con la tabella nuova l'interpolazione sui dodicesimi deve dare il valore dell'esempio scritto nella reference (67 anni e 7 mesi: 5,6266%). Test nel Task 1.

---

### Task 1: Coefficienti 2027-2028 negli script

**Files:**
- Modify: `skills/it-pianificazione/assets/proiezione-inps.py` (commento e tabella alle righe 50-62, `coeff_vigente()`, la stringa `origine` in `main()`)
- Modify: `skills/it-pianificazione/assets/riscatto-laurea.py` (la stringa `origine` in `main()`)
- Modify: `skills/it-pianificazione/assets/ponte-pensione.py:91` (default `COEFF_TRASFORMAZIONE`)
- Test: `tests/run_tests.py` (nuovo test dopo `t_proiezione`; `t_riscatto_laurea`; `t_rami_avanzati`)

**Interfaces:**
- Produces:
  - `proiezione-inps.COEFF_VIGENTI: dict[int, float]` al posto di `COEFF_2025_2026`, con i quindici valori del decreto; `proiezione-inps._BIENNIO_COEFF = "2027-2028"` (privata: `--set` non la elenca).
  - `coeff_vigente(eta: float) -> float` invariata nella firma e nel comportamento.
  - In `tests/run_tests.py`, la costante `DECRETO_COEFF_2027: dict[int, tuple[float, float]]` (età → divisore, coefficiente), usata anche dai Task 2 e 3.
  - Default di `ponte-pensione.COEFF_TRASFORMAZIONE`: `0.047`.

- [ ] **Step 1: Rileggi la tabella sul decreto** e confrontala con i valori del test qui sotto.

- [ ] **Step 2: Scrivi il test nuovo, dopo `t_proiezione`**

```python
# Decreto direttoriale Min. Lavoro-MEF del 16/10/2026, tabella allegata: età → (divisore, coefficiente)
DECRETO_COEFF_2027 = {
    57: (24.080, 0.04153), 58: (23.507, 0.04254), 59: (22.929, 0.04361), 60: (22.345, 0.04475), 61: (21.756, 0.04596),
    62: (21.163, 0.04725), 63: (20.565, 0.04863), 64: (19.963, 0.05009), 65: (19.357, 0.05166), 66: (18.747, 0.05334),
    67: (18.136, 0.05514), 68: (17.523, 0.05707), 69: (16.908, 0.05914), 70: (16.290, 0.06139), 71: (15.669, 0.06382)}


@test("proiezione-inps: coefficienti 2027-2028 del decreto 16/10/2026, 1/divisore, default di proiezione, riscatto e ponte")
def t_coefficienti_2027():
    pi = _modulo_previdenza("proiezione-inps.py")
    assert pi.COEFF_VIGENTI == {eta: c for eta, (_, c) in DECRETO_COEFF_2027.items()}, pi.COEFF_VIGENTI
    assert all(round(1 / d, 5) == c for d, c in DECRETO_COEFF_2027.values()), "un coefficiente non è 1/divisore"
    assert pi._BIENNIO_COEFF == "2027-2028" and not hasattr(pi, "COEFF_2025_2026")
    # Review Focus 5: 67 anni e 7 mesi, l'esempio della reference (5,6266%)
    assert abs(pi.coeff_vigente(67 + 7 / 12) - 0.0562658) < 5e-7, pi.coeff_vigente(67 + 7 / 12)
    tmp = tempfile.mkdtemp()
    try:
        j = os.path.join(tmp, "x.json")
        rc, out = run_script(asset("it-pianificazione", "proiezione-inps.py"), "--json", j)
        r = json.load(open(j, encoding="utf-8"))
        assert rc == 0 and r["coefficiente_trasformazione"] == 0.04723 and r["pensione_inps_lorda_annua"] == 29247.4, r
        assert "tabella 2027-2028 a 69 anni (5,914%)" in out and "2025-26" not in out, out[-900:]
        rc, out = run_script(asset("it-pianificazione", "riscatto-laurea.py"), "--json", j)
        assert rc == 0 and "tabella 2027-2028" in out and "2025-26" not in out, out[-900:]
        rc, out = run_script(asset("it-pianificazione", "ponte-pensione.py"), "--json", j)
        r = json.load(open(j, encoding="utf-8"))
        assert rc == 0 and r["costo_permanente_lordo_annuo"] == 19916.59, r["costo_permanente_lordo_annuo"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    assert _modulo_previdenza("ponte-pensione.py").COEFF_TRASFORMAZIONE == 0.047
```

- [ ] **Step 3: Aggiorna i valori chiusi di `t_riscatto_laurea`** (i soli che dipendono dal coefficiente):

```python
        assert r["delta_pensione_lorda_annua"] == 1719.48 and r["anni_per_rientrare"] == 19.5, r   # × 4,7234%; netto/(× 0,62)
        assert r["coefficiente_trasformazione"] == 0.04723 and r["eta_pensionamento"] == 69.0, r
```

Nella lista delle stringhe attese `"€ 1.751"` diventa `"€ 1.719"`, e l'espressione regolare `r"rientrare\s+19,1\s+19,1"` diventa `r"rientrare\s+19,5\s+19,5"`.

- [ ] **Step 4: In `t_rami_avanzati` sostituisci `pi.COEFF_2025_2026` con `pi.COEFF_VIGENTI`** (quattro occorrenze in due righe).

- [ ] **Step 5: Lancia e verifica il fallimento**

Run: `python3 tests/run_tests.py --only "coefficienti 2027-2028"`
Expected: FAIL con `AttributeError: … has no attribute 'COEFF_VIGENTI'`.

- [ ] **Step 6: Aggiorna `proiezione-inps.py`.** La tabella diventa `COEFF_VIGENTI` con i valori di `DECRETO_COEFF_2027`; sopra, `_BIENNIO_COEFF = "2027-2028"`. Il commento della tabella: `# Tabella vigente (biennio 2027-2028, decreto direttoriale Min. Lavoro-MEF del 16/10/2026, decorrenza 1/1/2027; Verificato: AAAA-MM) — età: coefficiente`. Il commento di `RIDUZIONE_COEFF_ANNUA` dice `revisioni biennali osservate tra -1,2% e -2,2%`. La stringa `origine` usa `_BIENNIO_COEFF`: `f"tabella {_BIENNIO_COEFF} a {ETA_PENSIONAMENTO:.0f} anni ({pct(c_vig, 3)}) ridotto del …"`.

- [ ] **Step 7: Aggiorna `riscatto-laurea.py` e `ponte-pensione.py`.** In `riscatto-laurea.py` la stringa `origine` usa `pi._BIENNIO_COEFF` al posto di `2025-26`. In `ponte-pensione.py`: `COEFF_TRASFORMAZIONE = 0.047  # coefficiente a 69 anni sui default di proiezione-inps.py (4,723% con la tabella 2027-2028)`.

- [ ] **Step 8: Lancia i test toccati e poi tutta la suite**

Run: `python3 tests/run_tests.py --only "coefficienti 2027-2028"`, poi `--only "riscatto della laurea"`, poi `--only "rami avanzati"`
Expected: PASS.
Run: la suite completa (vedi Global Constraints).
Expected: possono fallire solo tre gruppi, da annotare per nome: i due test di igiene del README (li chiude lo Step 9), i test che confrontano una reference con uno script (li chiude il Task 2) e quelli che confrontano la tabella dell'Excel con lo script (li chiude il Task 3). Ogni altro fallimento è un valore chiuso che dipende dal coefficiente: va ricalcolato qui, non lasciato rosso.

- [ ] **Step 9: Aggiorna README (conteggio e tabella dei test) e fai il commit**

```bash
python3 tests/run_tests.py --tabella-test   # incolla l'output nel README, sotto il marcatore
git add tests/run_tests.py README.md skills/it-pianificazione/assets/proiezione-inps.py skills/it-pianificazione/assets/riscatto-laurea.py skills/it-pianificazione/assets/ponte-pensione.py
git commit -m "feat: coefficienti di trasformazione 2027-2028 negli script previdenziali (decreto 16/10/2026)"
```

### Task 2: Coefficienti nelle reference e nelle skill

**Files:**
- Modify: `skills/it-pianificazione/references/previdenza-obbligatoria.md` (sezione «Coefficienti di trasformazione», righe 58-141 di oggi; «Esempio numerico» della tassazione, righe 228-237)
- Modify: `skills/it-pianificazione/SKILL.md` (righe 42, 213-217, 230-233 e 370 di oggi; `metadata.version`)
- Modify: `skills/it-pianificazione-autonomi/references/previdenza-gestione-separata.md` (righe 65 e 148 di oggi), `skills/it-pianificazione-autonomi/SKILL.md` (riga 221 di oggi; `metadata.version`)
- Test: `tests/run_tests.py` (nuovo test dopo `t_requisiti_e_link_inps`)

**Interfaces:**
- Consumes: `DECRETO_COEFF_2027` del Task 1.
- Produces: i testi esatti che il test cerca (sotto). Nessun codice.

- [ ] **Step 1: Scrivi il test**

```python
@test("previdenza: coefficienti 2027-2028 nella reference e nelle skill, esempi ricalcolati, cosa fare di JSON e fogli vecchi")
def t_coefficienti_testi_2027():
    leggi = lambda *p: open(os.path.join(SKILLS, *p), encoding="utf-8").read()
    rif = leggi("it-pianificazione", "references", "previdenza-obbligatoria.md")
    it = lambda x, d: f"{x:.{d}f}".replace(".", ",")
    for eta, (div, coeff) in DECRETO_COEFF_2027.items():
        assert f"| {eta} | {it(div, 3)} | **{it(coeff * 100, 3)}%** |" in rif, f"reference: riga dei {eta} anni"
    for atteso in ("16 ottobre 2026", "1° gennaio 2027", "| 67 | 5,608% | 5,514% | -1,68% |", "5,6266%", "€16.542",
                   "€16.880", "€17.121", "4,199%", "€33.004", "€43.340", "1,2-2,2%", "2029-2030", "€13.844"):
        assert atteso in rif, f"previdenza-obbligatoria.md: manca «{atteso}»"
    for superato in ("atteso entro novembre 2026", "atteso novembre 2026", "5,7247%", "€16.824", "4,271%", "1,5-2,2%"):
        assert superato not in rif, f"previdenza-obbligatoria.md: resta «{superato}»"
    skill = leggi("it-pianificazione", "SKILL.md")
    gs = leggi("it-pianificazione-autonomi", "references", "previdenza-gestione-separata.md")
    assert "a 67 anni = **5,514%** (era 5,608%)" in skill and "Coefficiente attuale a 67 anni: 5,514%" in skill
    assert "4,199%" in skill and "€33.004" in skill and "€43.340" in skill
    assert "A 67 anni = 5,514% per il biennio 2027-2028" in gs and "5,608%" not in gs
    for nome, testo in (("it-pianificazione/SKILL.md", skill), ("previdenza-gestione-separata.md", gs),
                        ("it-pianificazione-autonomi/SKILL.md", leggi("it-pianificazione-autonomi", "SKILL.md"))):
        assert "20/11/2024" not in testo and "16/10/2026" in testo, f"{nome}: il decreto citato è ancora quello del 2024"
    # Review Focus 1 e 2: i JSON e i fogli compilati prima dell'aggiornamento portano i numeri vecchi
    assert "rilancia la catena dall'inizio" in skill and "foglio Coefficienti della tua copia" in skill
```

- [ ] **Step 2: Lancia e verifica il fallimento**

Run: `python3 tests/run_tests.py --only "coefficienti 2027-2028 nella reference"`
Expected: FAIL con «reference: riga dei 57 anni».

- [ ] **Step 3: Riscrivi la sezione dei coefficienti di `previdenza-obbligatoria.md`** con questi contenuti, nello stile del file:
  - titolo «Coefficienti di trasformazione 2027-2028»; fonte: decreto direttoriale del Ministero del Lavoro di concerto con il MEF del 16 ottobre 2026, valido per le pensioni con decorrenza dal 1° gennaio 2027; la Gazzetta Ufficiale si cita quando esce; marcatore `Verificato: AAAA-MM` sulla tabella;
  - tabella età, divisore, coefficiente con le quindici righe nel formato `| 57 | 24,080 | **4,153%** |`;
  - confronto «2025-2026 contro 2027-2028» con le righe di 57, 64, 67, 70 e 71 anni: `-1,21%`, `-1,55%`, `-1,68%`, `-1,90%`, `-1,97%`; tendenza: tutte negative, e il prossimo aggiornamento è per il biennio 2029-2030, con il decreto atteso nell'autunno 2028;
  - età non intera, 67 anni e 7 mesi: `5,514% + (7/12) × 0,193% = 5,6266%`;
  - montante di €300.000: €16.542 a 67 anni, €16.880 a 67 anni e 7 mesi (+€338), €17.121 a 68 anni (+€579);
  - decadimento storico: `~1,8% per biennio (range osservato 1,2-2,2%)`; coefficiente proiettato: `5,514% × (1 − 0,018)^15 = 5,514% × 0,7615 = 4,199%`; su €786k: €33.004 invece di €43.340, sovrastima del 31%;
  - la nota 3 dell'euristica nomina il biennio 2027-2028 e i prossimi aggiornamenti (autunno 2028 per il 2029-2030).

- [ ] **Step 4: Ricalcola l'«Esempio numerico» della tassazione** sulla pensione lorda di €16.542: IRPEF lorda €3.805; detrazione `700 + 1.255 × (28.000 − 16.542) / 19.500 = €1.437`; IRPEF netta €2.367; addizionali €331; netta `€16.542 - €2.367 - €331 = €13.844`; mensile €1.065.

- [ ] **Step 5: Aggiorna `SKILL.md` di it-pianificazione.**
  - riga dei coefficienti: `Per il biennio 2027-2028 (decreto direttoriale del 16/10/2026, in vigore dal 1° gennaio 2027): a 67 anni = **5,514%** (era 5,608%); range 57-71 anni.`;
  - commento del blocco di calcolo: `# da tabella del decreto 16/10/2026`; nella descrizione dell'Excel: `**Coefficienti**: tabella ufficiale completa del decreto 16/10/2026 (15 valori 57-71 anni) con note operative.`;
  - «Esempio del perché conta»: `Coefficiente attuale a 67 anni: 5,514%`; proiettato `**4,199%**`; `pensione lorda €33.004 col proiettato, contro €43.340 col coefficiente attuale (sovrastima del 31%!)`; tassi di sostituzione `da un irrealistico 78% a un realistico 60%`;
  - nella nota sulla catena `--json` → `--from`, una frase: `Dopo un aggiornamento del plugin rilancia la catena dall'inizio: i JSON salvati portano i numeri della versione che li ha scritti (dalla 0.13.0 i coefficienti sono quelli del 2027-2028).`;
  - dove la skill descrive `proiezione-pensione.xlsx`, una frase: `Se hai compilato il foglio prima della 0.13.0, aggiorna il foglio Coefficienti della tua copia con la tabella 2027-2028 (o ricopia il modello e riporta i tuoi input).`;
  - `metadata.version: "0.14"`.

- [ ] **Step 6: Aggiorna la skill degli autonomi.** In `previdenza-gestione-separata.md`: `Vedi la tabella ufficiale completa (decreto del 16/10/2026) in …previdenza-obbligatoria.md. A 67 anni = 5,514% per il biennio 2027-2028.`, e nell'elenco finale `stessi dei dipendenti (tabella del decreto 16/10/2026)`. In `skills/it-pianificazione-autonomi/SKILL.md`: `**Coefficienti**: tabella ufficiale del decreto 16/10/2026, con la nota che le casse possono usare coefficienti propri.` e `metadata.version: "0.6"`.

- [ ] **Step 7: Allinea README e CHANGELOG alle due versioni**, perché `t_frontmatter_skill` le confronta: nella tabella «Le skill e le loro versioni» del README `v0.14` e `v0.6`; in `CHANGELOG.md`, in testa a `### it-pianificazione` e a `### it-pianificazione-autonomi`, le voci `#### v0.14 (plugin 0.13.0)` e `#### v0.6 (plugin 0.13.0)` con una riga: coefficienti di trasformazione 2027-2028.

- [ ] **Step 8: Lancia i test**

Run: `python3 tests/run_tests.py --only "coefficienti 2027-2028 nella reference"`, poi `--only "T14 skill"`, poi `--only "riscatto della laurea"` (un test confronta reference e script)
Expected: PASS. Se il test T13 sulla reference del riscatto fallisce, la frase «Sui default di `assets/riscatto-laurea.py`…» della reference porta ancora la pensione in più e gli anni per rientrare vecchi: diventano €1.719 e 19,5 anni.

- [ ] **Step 9: README (conteggio e tabella dei test) e commit**

```bash
git add -A skills/it-pianificazione skills/it-pianificazione-autonomi tests/run_tests.py README.md CHANGELOG.md
git commit -m "docs: coefficienti 2027-2028 in reference e skill, esempi ricalcolati"
```

### Task 3: Coefficienti nei due Excel

**Files:**
- Modify: `skills/it-pianificazione/assets/proiezione-pensione.xlsx` (`Coefficienti!A1`, `A2`, `B5:C19`, note `A23`, `A25`, `A28`; `Pubblica!A59`)
- Modify: `skills/it-pianificazione-autonomi/assets/proiezione-pensione-autonomi.xlsx` (`Coefficienti!A1`, `A2`, `B5:C19`, nota `A23`; `Input!C42`)
- Test: `tests/run_tests.py` (nuovo test dopo `t_excel_struttura`)

**Interfaces:**
- Consumes: `DECRETO_COEFF_2027` del Task 1.
- Produces: i due xlsx con la tabella nuova e le cache ricalcolate.

- [ ] **Step 1: Scrivi il test**

```python
@test("Excel previdenziali: foglio Coefficienti con la tabella 2027-2028 del decreto, nessuna cella con il biennio vecchio")
def t_coefficienti_excel_2027():
    from openpyxl import load_workbook
    for skill, nome in (("it-pianificazione", "proiezione-pensione.xlsx"),
                        ("it-pianificazione-autonomi", "proiezione-pensione-autonomi.xlsx")):
        wb = load_workbook(asset(skill, nome))
        c = wb["Coefficienti"]
        tabella = {c[f"A{r}"].value: (c[f"B{r}"].value, c[f"C{r}"].value) for r in range(5, 20)}
        assert tabella == DECRETO_COEFF_2027, (nome, tabella)
        assert "2027-2028" in c["A1"].value and "16 ottobre 2026" in c["A2"].value, (nome, c["A1"].value, c["A2"].value)
        vecchie = [f"{ws.title}!{x.coordinate}" for ws in wb.worksheets for riga in ws.iter_rows() for x in riga
                   if isinstance(x.value, str) and re.search(r"2025-2026|2025-26|20 novembre 2024|1,5-2,2%", x.value)]
        assert not vecchie, f"{nome}: celle con il biennio o l'intervallo vecchio: {vecchie}"
```

- [ ] **Step 2: Lancia e verifica il fallimento**

Run: `python3 tests/run_tests.py --only "Excel previdenziali"`
Expected: FAIL sulla tabella di `proiezione-pensione.xlsx`.

- [ ] **Step 3: Modifica l'XML dei due file** con uno script usa e getta nella cartella di scratch (non va nel repository). In entrambi i file il foglio `Coefficienti` è `xl/worksheets/sheet2.xml`, le celle numeriche hanno la forma `<c r="B5" s="19" t="n"><v>23.789</v></c>` e i testi stanno in `xl/sharedStrings.xml`. Lo script:

```python
import re, shutil, sys, zipfile
NUOVI = {57: (24.080, 0.04153), 58: (23.507, 0.04254), 59: (22.929, 0.04361), 60: (22.345, 0.04475), 61: (21.756, 0.04596),
         62: (21.163, 0.04725), 63: (20.565, 0.04863), 64: (19.963, 0.05009), 65: (19.357, 0.05166), 66: (18.747, 0.05334),
         67: (18.136, 0.05514), 68: (17.523, 0.05707), 69: (16.908, 0.05914), 70: (16.290, 0.06139), 71: (15.669, 0.06382)}
TESTI = [("biennio 2025-2026", "biennio 2027-2028"),
         ("Decreto direttoriale del 20 novembre 2024 (Min. Lavoro / MEF) — GU n. 35 del 12/02/2025",
          "Decreto direttoriale del 16 ottobre 2026 (Min. Lavoro / MEF), decorrenza 1° gennaio 2027"),
         ("Decreto direttoriale 20 novembre 2024 (Min. Lavoro / MEF) — GU n. 35 del 12/02/2025",
          "Decreto direttoriale del 16 ottobre 2026 (Min. Lavoro / MEF), decorrenza 1° gennaio 2027"),
         ("2025-2026", "2027-2028"), ("1,5-2,2%", "1,2-2,2%")]
def patch(path):
    tmp = path + ".nuovo"
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            dati = zin.read(item.filename)
            if item.filename == "xl/worksheets/sheet2.xml":
                x = dati.decode("utf-8")
                for i, eta in enumerate(range(57, 72)):
                    for col, v in zip("BC", NUOVI[eta]):
                        x, n = re.subn(rf'(<c r="{col}{5 + i}"[^>]*><v>)[^<]*(</v>)', rf"\g<1>{v!r}\g<2>", x)
                        assert n == 1, (path, col, 5 + i)
                dati = x.encode("utf-8")
            elif item.filename == "xl/sharedStrings.xml":
                x = dati.decode("utf-8")
                for vecchio, nuovo in TESTI:
                    x = x.replace(vecchio, nuovo)
                dati = x.encode("utf-8")
            zout.writestr(item, dati)
    shutil.move(tmp, path)
for p in sys.argv[1:]:
    patch(p)
```

- [ ] **Step 4: Ricalcola e controlla la struttura**

```bash
python3 scripts/ricalcola-excel.py skills/it-pianificazione/assets/proiezione-pensione.xlsx --in-place
python3 scripts/ricalcola-excel.py skills/it-pianificazione-autonomi/assets/proiezione-pensione-autonomi.xlsx --in-place
python3 tests/run_tests.py --only "Excel"
```

Expected: `0 celle in errore` per entrambi; PASS per il test nuovo, per `T12 Excel` (fogli, ancore e numero di formule invariati), per le cache uguali al ricalcolo e per i test che confrontano `Pubblica` con `proiezione-inps.py`.

- [ ] **Step 5: README (conteggio e tabella dei test) e commit**

```bash
git add skills/it-pianificazione/assets/proiezione-pensione.xlsx skills/it-pianificazione-autonomi/assets/proiezione-pensione-autonomi.xlsx tests/run_tests.py README.md
git commit -m "feat: coefficienti 2027-2028 nei due Excel previdenziali, cache ricalcolate"
```

### Task 4: Tasso di capitalizzazione 2026 e anno corrente fissabile

**Files:**
- Modify: `skills/it-pianificazione/assets/importa-previdenza.py` (docstring, commento e tabella `TASSI_CAPITALIZZAZIONE`, nuova costante, `main()`)
- Modify: `skills/it-pianificazione/references/previdenza-obbligatoria.md:39-40` (medie del tasso nominale)
- Test: `tests/run_tests.py` (`t_tassi_capitalizzazione`, `t_requisiti_e_link_inps`)

**Interfaces:**
- Produces:
  - `TASSI_CAPITALIZZAZIONE[2026] = 1.063359`.
  - `ANNO_CORRENTE = None` in testa a `importa-previdenza.py`, elencata da `--set`. `None` vuol dire l'anno di oggi. `main()` usa quell'anno al posto di `oggi.year` nei due punti in cui compare (ricostruzione del montante, ultimo anno dei versamenti al fondo); l'età resta calcolata sulla data di oggi. Un valore che non è un intero tra `INIZIO_CONTRIBUTIVO` e 2100 ferma lo script con `errore("ANNO_CORRENTE = …: serve un anno, per esempio 2026")`.

- [ ] **Step 1: Rileggi il tasso sulla nota ISTAT** (0,063359; coefficiente 1,063359).

- [ ] **Step 2: Aggiorna `t_tassi_capitalizzazione`.** Il nome diventa `"importa-previdenza: tassi di capitalizzazione ufficiali 1996-2026, solo contributi dal 1996, avvisi veri"`. Nel dizionario `ufficiali` si aggiunge `2026: 1.063359` e il commento cita la nota ISTAT del 16/10/2026. Le asserzioni sul montante e sugli avvisi diventano:

```python
    retrib = {a: 30_000.0 for a in range(1998, 2026)}
    montante, _, mancanti = m.ricostruisci_montante(retrib, 2026)
    atteso = 0.0
    for anno in range(1998, 2027):  # il 2026 ha il suo tasso: il montante al 31/12/2025 si rivaluta
        atteso = atteso * ufficiali.get(anno, 1.0) + retrib.get(anno, 0.0) * 0.33
    assert abs(montante - atteso) < 0.01, f"montante {montante:,.2f} ≠ {atteso:,.2f}"
    assert mancanti == [], f"anni senza tasso pubblicato: {mancanti}"
    # Review Focus 4: nel 2027, prima del tasso 2027, il montante resta quello del 31/12/2026
    montante_2027, _, mancanti = m.ricostruisci_montante(retrib, 2027)
    assert mancanti == [2027] and abs(montante_2027 - montante) < 0.01, (mancanti, montante_2027)
```

e, al posto del lancio con la data di sistema che pretende l'avviso:

```python
    P, X = asset("it-pianificazione", "importa-previdenza.py"), os.path.join(FIXTURES, "estratto-inps-test.xml")
    rc, out = run_script(P, X, "--set", "ANNO_CORRENTE=2026")
    assert rc == 0 and "non ancora pubblicat" not in out and "sono i primi anni" not in out, out[-600:]
    assert "prima del 1996" not in out, "carriera dal 2023: nessun avviso sugli anni prima del 1996"
    rc, out = run_script(P, X, "--set", "ANNO_CORRENTE=2027")
    assert rc == 0 and "tasso 2027 non ancora pubblicato" in out and "31/12/2026" in out, out[-600:]
    # Review Focus 3: un valore che non è un anno
    for cattivo in ("ANNO_CORRENTE=1990", "ANNO_CORRENTE=2026.5", "ANNO_CORRENTE='prossimo'"):
        rc, so, se = run_script_split(P, X, "--set", cattivo)
        assert rc == 1 and se.lstrip().startswith("ERRORE:") and "ANNO_CORRENTE" in se and "Traceback" not in se, (cattivo, se[-200:])
```

Nel ciclo sulle carriere dal 1995 e dal 1990, i due lanci dello script prendono `"--set", "ANNO_CORRENTE=2026"` e l'atteso si calcola con `2026` al posto di `__import__("datetime").date.today().year`.

- [ ] **Step 3: Aggiorna `t_requisiti_e_link_inps`**: `media(da, 2025)` diventa `media(da, 2026)` e la frase cercata `f"{cifra} annuo nel {da}-2026"`.

- [ ] **Step 4: Lancia e verifica il fallimento**

Run: `python3 tests/run_tests.py --only "tassi di capitalizzazione"`
Expected: FAIL con «tasso 2026: None ≠ 1.063359».

- [ ] **Step 5: Aggiorna `importa-previdenza.py`.** Riga nuova in tabella: `2026: 1.063359,   # rivaluta il montante al 31/12/2025 (decorrenze 2027)`. Il commento della tabella cita «Tassi ISTAT 1996-2026: nota ISTAT prot. 2582754/26 del 16/10/2026 (lavoro.gov.it) — Verificato: AAAA-MM» e il docstring «La tabella dei tassi copre 1996-2026». Aggiungi `ANNO_CORRENTE = None` con il suo commento e la validazione descritta nelle Interfaces.

- [ ] **Step 6: Aggiorna le medie nella reference**: `Tasso nominale: media ~2,9% annuo nel 1996-2026 e ~2,0% annuo nel 2006-2026 (da 0% a 6,3% nei singoli anni).`

- [ ] **Step 7: Lancia i test**

Run: `python3 tests/run_tests.py --only "importa-previdenza"`, poi `--only "previdenza: requisiti"`, poi `--only "catena"`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add skills/it-pianificazione/assets/importa-previdenza.py skills/it-pianificazione/references/previdenza-obbligatoria.md tests/run_tests.py
git commit -m "feat: tasso di capitalizzazione 2026 (nota ISTAT 16/10/2026), anno corrente fissabile in importa-previdenza"
```

### Task 5: Pesi MSCI ACWI e marcatore

**Files:**
- Modify: `skills/it-pianificazione-obiettivi/assets/capitale-umano.py:78-85` (commento e `PESI_MONDO`)
- Modify: `skills/it-pianificazione-obiettivi/SKILL.md` (`metadata.version`), `README.md` (tabella delle skill, sezione «Release»), `CHANGELOG.md` (storia della skill)
- Test: `tests/run_tests.py` (`OBBLIGATI_FRESHNESS`; nuovo test dopo `t_cu_profili`)

**Interfaces:**
- Produces: `PESI_MONDO` con i pesi della scheda del 30/10/2026; `it-pianificazione-obiettivi/assets/capitale-umano.py` in `OBBLIGATI_FRESHNESS`.

- [ ] **Step 1: Rileggi la scheda MSCI ACWI** (sezione «Sector Weights»). Se è uscita quella di novembre, usa quella e aggiorna valori e data nel test. Se la scheda non si raggiunge, il task si ferma qui: i pesi restano quelli di settembre, senza marcatore e senza la voce in `OBBLIGATI_FRESHNESS`, e la voce si segnala al proprietario (spec §6.3).

- [ ] **Step 2: Scrivi il test**

```python
@test("T15 capitale umano: pesi MSCI ACWI della scheda del 30/10/2026, marcatore di freshness obbligatorio")
def t_cu_pesi_mondo():
    m = carica_modulo(asset(*CU))
    assert m.PESI_MONDO == {
        "Information Technology": 0.3118, "Financials": 0.1663, "Industrials": 0.1023, "Health Care": 0.0936,
        "Consumer Discretionary": 0.0857, "Communication Services": 0.0704, "Consumer Staples": 0.0509,
        "Energy": 0.0449, "Materials": 0.0345, "Utilities": 0.0244, "Real Estate": 0.0153}, m.PESI_MONDO
    sorgente = open(asset(*CU), encoding="utf-8").read()
    commento = sorgente.split("PESI_MONDO = {")[0][-600:]
    assert "30/10/2026" in commento and re.search(r"Verificato: \d{4}-\d{2}", commento), commento
    assert "it-pianificazione-obiettivi/assets/capitale-umano.py" in OBBLIGATI_FRESHNESS
```

- [ ] **Step 3: Lancia e verifica il fallimento**

Run: `python3 tests/run_tests.py --only "pesi MSCI ACWI"`
Expected: FAIL sul confronto dei pesi.

- [ ] **Step 4: Aggiorna `capitale-umano.py`**: i pesi del test; nel commento la data della scheda (30/10/2026) e, sulla stessa riga della fonte, `Verificato: AAAA-MM`. Aggiungi il file a `OBBLIGATI_FRESHNESS`, dopo `capitale-umano.md`.

- [ ] **Step 5: Versione della skill e passo di rilascio.** `metadata.version: "0.25"` in `skills/it-pianificazione-obiettivi/SKILL.md`; README: `v0.25` nella tabella delle skill e, nel passo 1 di «Release», la frase `aggiornare PESI_MONDO di capitale-umano.py dalla scheda MSCI ACWI del mese, con il suo marcatore`; CHANGELOG: `#### v0.25 (plugin 0.13.0)` in testa a `### it-pianificazione-obiettivi`, con una riga sui pesi di ottobre 2026. Due test esistenti cercano la versione vecchia nel testo della skill (`t_ce_documentazione` e `t_lt_documentazione`, `'version: "0.24"'`): diventa `'version: "0.25"'` in entrambi.

- [ ] **Step 6: Lancia i test**

Run: `python3 tests/run_tests.py --only "T15"`, poi `--only "freshness"`, poi `--only "T14 skill"`
Expected: PASS.

- [ ] **Step 7: README (conteggio e tabella dei test) e commit**

```bash
git add skills/it-pianificazione-obiettivi tests/run_tests.py README.md CHANGELOG.md
git commit -m "feat: pesi settoriali MSCI ACWI del 30/10/2026, capitale-umano.py tra i file con il marcatore obbligatorio"
```

### Task 6: Tabella della freshness, calendario, changelog e ROADMAP

**Files:**
- Modify: `README.md` (tabella «Stato dei dati normativi», «Calendario dei parametri da riverificare»)
- Modify: `CHANGELOG.md` (nuova sezione «Non rilasciato» in testa), `ROADMAP.md`
- Test: `tests/run_tests.py` (nuovo test dopo `t_tabella_dati_normativi`)

**Interfaces:**
- Consumes: i marcatori nuovi dei Task 1, 2, 4 e 5 (la tabella li riflette).

- [ ] **Step 1: Scrivi il test**

```python
@test("igiene: la tabella della freshness del README è quella generata dal runner (--tabella-freshness)")
def t_tabella_freshness_readme():
    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    marcatore = "<!-- generata con: python tests/run_tests.py --tabella-freshness -->"
    assert marcatore in readme, "README senza la tabella dello stato dei dati normativi"
    nel_readme = readme.split(marcatore)[1].strip().split("\n\n")[0].strip()
    assert nel_readme == tabella_freshness(), ("la tabella del README è diversa da quella generata: "
                                               "rigenerarla con python tests/run_tests.py --tabella-freshness")
```

- [ ] **Step 2: Lancia e verifica il fallimento**

Run: `python3 tests/run_tests.py --only "tabella della freshness"`
Expected: FAIL (mancano almeno le righe di `capitale-umano.md` e `riscatto-laurea.py`).

- [ ] **Step 3: Rigenera la tabella** con `python3 tests/run_tests.py --tabella-freshness` e incollala nel README sotto il marcatore.

- [ ] **Step 4: Aggiorna il «Calendario dei parametri da riverificare»** allo stato di novembre 2026: via la riga «entro fine 2026» del decreto sui coefficienti; righe nuove «ottobre-novembre 2027 | Tasso di capitalizzazione 2027 (nota ISTAT) | `importa-previdenza.py`, `previdenza-obbligatoria.md`», «autunno 2028 | Decreto sui coefficienti di trasformazione 2029-2030 (l'ultimo è del 16/10/2026) | `previdenza-obbligatoria.md`, foglio Coefficienti dei due Excel, `proiezione-inps.py`, `ponte-pensione.py`» e «a ogni release | Pesi settoriali MSCI ACWI | `capitale-umano.py`».

- [ ] **Step 5: Apri «Non rilasciato» nel CHANGELOG**, sopra `## v0.12.0`, con quattro voci:
  - **Coefficienti di trasformazione 2027-2028**: fonte, file toccati, e «**Output cambiati**: sui default la pensione INPS lorda di `proiezione-inps.py` passa da €29.791 a €29.247 (coefficiente da 4,811% a 4,723%); in `riscatto-laurea.py` la pensione in più da €1.751 a €1.719 e il rientro da 19,1 a 19,5 anni; in `ponte-pensione.py` il costo permanente da €20.340 a €19.917. I JSON e i fogli compilati prima portano i numeri vecchi»;
  - **Tasso di capitalizzazione 2026**: 1,063359, e `ANNO_CORRENTE`;
  - **Pesi MSCI ACWI** di ottobre 2026 e marcatore obbligatorio;
  - **Tabella della freshness** del README vincolata da un test.

  Verifica il valore di partenza della pensione sui default (`git stash` non serve: è nel changelog della 0.12.0 o si ricava da `619.198,73 × 0,04811`).

- [ ] **Step 6: Aggiorna `ROADMAP.md`**: in testa lo stato al giorno del commit; sotto «Dopo — da decidere» una sezione «Programma di completamento (deciso il 14/11/2026)» con le cinque ondate, i tre rilasci e il rimando alla spec; la riga «Bassa | Pesi settoriali dell'indice mondiale» della tabella di T16 diventa «Bassa, fatta | … | a ogni release, con marcatore».

- [ ] **Step 7: Suite completa**

Run: la suite completa (vedi Global Constraints).
Expected: tutti i test passati, nessuno saltato.

- [ ] **Step 8: Prova i mutanti** (con `python3 -B`, ripristinando dopo ognuno): un coefficiente della tabella cambiato di un'unità all'ultima cifra; il tasso 2026 tolto; `ANNO_CORRENTE` ignorato (lo script usa sempre `oggi.year`); un peso MSCI scambiato con un altro; una riga tolta dalla tabella della freshness del README. Ognuno deve far fallire almeno un test: annota quale nel messaggio del commit.

- [ ] **Step 9: README (conteggio e tabella dei test) e commit**

```bash
git add README.md CHANGELOG.md ROADMAP.md tests/run_tests.py
git commit -m "docs: tabella della freshness vincolata da un test, calendario, changelog e programma in ROADMAP"
```

### Chiusura

Prima del merge su `develop`: la revisione finale prevista dal modo di esecuzione scelto e, se il proprietario la chiede, la revisione avversariale del repository (`docs/sviluppo/workflows/review-tema-roadmap.js`, § 4 di `HANDOFF.md`). Le correzioni vanno in un commit a parte, che ne riporta l'esito. La pull request si apre quando il proprietario la chiede.
