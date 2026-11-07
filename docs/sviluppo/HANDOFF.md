# Passaggio della sessione di sviluppo — 01/11/2026

Documento per riprendere lo sviluppo in un'altra sessione (Claude Code in cloud o su un'altra macchina). Sostituisce la versione del 24/10/2026, che si fermava a T13; i §§ 2.1-2.8 restano la storia della 0.11.0 e di T13, il § 2.9 copre i temi entrati dopo. Tutto ciò che serve è nel repository: questo file, `ROADMAP.md`, `docs/audit-2026-10.md` e i dati in `docs/sviluppo/`.

## 1. Dove siamo

- **0.11.0 rilasciata il 24/10/2026**: PR #50 su `main` (merge commit `24e0cf1`), merge back su develop (PR #51), tag `v0.11.0` dato dal proprietario e GitHub Release con lo zip pubblicata da `release.yml` (run 40123407611): zip di 79 file con LICENSE, NOTICE e CHANGELOG.md, versione 0.11.0 nel manifest, estratto e validato con `claude plugin validate --strict`. Dalla sessione cloud il push dei tag è respinto con un 403 dal proxy GitHub, mentre i branch passano: al prossimo rilascio il tag lo dà di nuovo il proprietario, con `git tag -a vX.Y.Z <merge commit su main> -m vX.Y.Z && git push origin vX.Y.Z`, senza creare prima la release dall'interfaccia (il passo `gh release create` del workflow fallirebbe). Prima del tag, `release.yml` si collauda su `main` con l'avvio manuale.
- Dentro la 0.11.0, dopo la 0.10.0 del 22/10/2026: PR #37-#40 (verifiche alle fonti, LibreOffice in CI, aliquota mista), PR #42 (stato dopo la 0.10.0), T9 in quattro PR (#43-#46: interfaccia comune degli script, lettore unico del pianificatore, catena `--json` → `--from`, input da file, «Dove lavorare», vocabolario), T12 (#47: test che vincolano i numeri), T14 (#48: description, CHANGELOG.md, comandi alias, manifest `--strict`, indici) e la pre-pubblicazione (#49: rilettura degli output, prove di installazione, verifiche alle fonti). Ogni tema ha la sua revisione avversariale, con gli esiti in `docs/sviluppo/revisioni/` (esito-t9a, esito-t9bcd, esito-t12, esito-t14).
- **0.12.0 in rilascio** (7/11/2026): `release/0.12.0` da `develop` dopo la PR #59, con la versione nei manifest, la sezione v0.12.0 del changelog, README e ROADMAP aggiornati; la PR su `main`, il tag e il merge back restano al proprietario (§ 3). Contenuto, in ordine di merge su `develop`:
  - T13 con la PR #54 (24/10/2026). Riscatto della laurea (F055): `riscatto-laurea.py` nella catena `--json` → `--from` e sezione in `previdenza-obbligatoria.md`. Casi frequenti del freelance (F063): rivalsa del 4%, saldo e acconti del secondo anno, eccedenza LM49 → RP21. Esito della revisione in `docs/sviluppo/revisioni/esito-t13b.json`.
  - T15 capitale umano con le PR #55 e #56 (25/10/2026): `capitale-umano.py`, profili, reference, comando `/capitale-umano`, Step 8 di it-pianificazione-obiettivi, integrazione in it-revisione; le correzioni della revisione finale sono nei commit `9772053` e `cfac020`.
  - T17 cruscotto grafico con la PR #57 (25/10/2026): `ribilanciamento-multibroker.py --json`, `genera-cruscotto.py`, `cruscotto.html`, test in Chromium con Playwright obbligatori nel job `suite`, passo 6 di it-revisione e comando `/cruscotto`.
  - T16 importatore della composizione degli ETF con la PR #58 (aperta il 25/10, merge l'1/11/2026): `importa-composizione-etf.py`, reference `composizione-etf.md`, `capitale-umano.py --composizione` sui due formati; esito della revisione in `esito-t16a.json`.
  - Ogni tema ha spec e piano in `docs/sviluppo/specs/` e `docs/sviluppo/piani/` (file datati 2026-10-25).
- Suite: `@test` in `tests/run_tests.py`; il conteggio è nel README, vincolato da un test di igiene. Freshness: nessun marcatore scade prima del 2027-06.
- Il repository è **pubblico** dal 24/10/2026, per decisione del proprietario, con un ruleset su `main` e `develop`: niente cancellazione né force push, check obbligatori `test` e `validate`. L'icona del plugin non si aggiunge (decisione del proprietario, 24/10/2026).
- **Branch remoti**: all'1/11/2026 su origin restano solo `main` e `develop`; i branch dei temi fino alla PR #58 sono stati cancellati dal proprietario. Dalla sessione cloud la cancellazione resta negata (il proxy GitHub risponde 403 a `git push origin --delete` e a `DELETE /git/refs`), quindi ogni branch di sessione va cancellato dal proprietario dopo il merge, oppure con Settings → General → «Automatically delete head branches».

## 2. Cosa resta: le voci verificate

### 2.1 Incoerenze documentali, da chiudere per prime

Chiusa dalla PR #42 (24/10/2026): `--anonimo` e «Privacy» spuntati; «Stato al 24/10/2026» e sezione «Non rilasciato» del changelog con le PR #37-#40; un solo conteggio dei test nel README vincolato da `t_conteggio_test` (storico del changelog escluso); «Errori noti» aggiornato; `freshness.yml` e `release.yml` su Python 3.11 con `t_python_workflow` che li tiene nella matrice; branch protection rinviata a dopo la pubblicazione; frasi superate del README corrette (zip con LICENSE e NOTICE, prova di installazione del 21/10/2026, niente «smoke test»); `t_marketplace` confronta anche `version` (l'assert di F061); «Linea di taglio e rilascio della 0.11.0» e regola Gitflow generica in ROADMAP.

### 2.2 T9 — interfaccia degli script e flusso dati (P1, XL)

Il primo sottopunto di `ROADMAP.md:143-146` (helper) è fatto nella PR #43 salvo `--from`; restano gli altri tre. Fatto in anticipo: F005 (CSV ancorato a `__file__`), rendimento zero in ponte (parte di F056), `--set` con refuso respinto (`motore_bootstrap.py:154-156`), `valida()` del ribilanciamento (T7), argparse solo in `importa-estratto-broker.py`.

- **F056 helper CLI.** Fatto nella PR #43 (T9a): `cli()`, `errore()`, `configura_stdout()`, `numero()`/`euro()`/`pct()` in `motore_bootstrap.py` (copie identiche, `t_sincronia`); adottati nei 13 script (i tre delle skill senza motore usano argparse e lo stesso `reconfigure`); test `t_cli_help` (`--help` → rc 0, flag ignoto → rc 2, dati mancanti → rc 1), `t_cli_utf8` (cwd esterna e console cp1252), convenzione 0/1/2 nel README («Convenzioni degli script»). Resta `--from` (F027, PR (c)).
- **F028 lettore unico del pianificatore.** Fatto nella PR #44 (T9b): `leggi_pianificatore(path)` in motore_bootstrap, usato dai quattro script; foglio mancante, importo come testo, profilo ignoto e orizzonte non intero → `ERRORE:` con rc 1; profilo con casefold; target vuoto → None (il glide path lo tiene, Monte Carlo e allocatore lo escludono dicendolo); righe incomplete scartate col motivo; `coperto` e stato «✓ già coperto» nell'allocatore; avviso sul modello dentro il plugin; test `t_lettore_pianificatore` (otto workbook limite, tre mutanti). Attenzione ai `__pycache__` quando si provano mutanti della stessa lunghezza nello stesso secondo: il bytecode resta quello vecchio (usare `python -B` o cancellare le cache).
- **F027 `--from`.** Fatto nella PR #45 (T9c): `carica_da_json` e `--from FILE` (ripetibile, letto prima di `--set`) in `cli()`; catena importa-previdenza `--json` → proiezione-inps → montecarlo-pensione → netto-pensione e ponte-pensione, con le mappe chiavi → costanti in testa a ogni `main()` e in `--help`; `--json` su glidepath e montecarlo-obiettivi; `t_catena_previdenziale` (stessi numeri lungo la catena, precedenza, JSON estraneo → rc 1) e `t_json_obiettivi`; SKILL di it-pianificazione (Step 1 e nota della pipeline) riscritte: la promessa ora è vera.
- **F033 input esterno.** Fatto nella PR #46 (T9d): `genera-ips.py --dati ips.json` (chiavi del blocco DATI, schema nella SKILL di it-revisione, avviso «dati di esempio» senza), `ribilanciamento-multibroker.py --dati piano.json --zainetto importatore.json --out DIR` (schema nella SKILL di it-rebalance; lo zainetto dal JSON dell'importatore via `analisi.per_broker[].zainetto_26_equivalente`); test `t_dati_ips` e `t_dati_ribilanciamento`.
- **F026 vocabolario.** Fatto nella PR #46: `categoria_fiscale` con i quattro valori dell'importatore è il nome canonico (README «Input richiesto» con `broker` nei due CSV, SKILL di it-rebalance, colonna del CSV degli ordini); il ribilanciamento accetta e normalizza i sinonimi (`tipo_fiscale`, `tipo`, `classe`, `plus_minus`, `controvalore`, forme brevi) e rifiuta `reddito_capitale_irpef` e `da_classificare` con il motivo; «Glossario» di dieci termini nel README; test `t_lessico`.
- **F059 «Dove lavorare» e F058.** Fatto nella PR #46: sezione in ogni SKILL.md con `${CLAUDE_SKILL_DIR}` (sostituito nel corpo della skill: documentazione ufficiale, pagina skills, «Available string substitutions», letta il 24/10/2026) e `${CLAUDE_PLUGIN_ROOT}` nei command (plugins-reference, «Environment variables»: le variabili non arrivano ai processi del tool Bash, vanno scritte nel markdown), `${user_config.cartella_lavoro}` con `userConfig` di tipo directory e default in `plugin.json` (resta da verificare dal proprietario come Cowork tratti `userConfig`: la documentazione non lo dice); invocazioni a nome nudo sostituite; ricalcolo da riga di comando condizionale in it-revisione; test `t_dove_lavorare`.
- **F031 contratto di input di it-revisione.** Fatto nella PR #45: tabella «Contratto di input» (dominio → script `--json` → campo → cella del cruscotto) in `skills/it-revisione/SKILL.md`; `template-revisione.md` rimanda agli script; `ROADMAP.md` spuntata.

### 2.3 Windows, encoding e formati italiani (pre-pubblicazione, insieme all'helper di T9)

Chiusa dalla PR #43 (T9a): UTF-8 forzato su stdout e stderr in ogni script, negli `scripts/` e nel runner; `open()` sempre con encoding (test `t_cli_utf8` lo controlla su assets, scripts e tests); `relpath` con `/`; job `test-windows` su `windows-latest` (Python 3.11, senza LibreOffice); `trova_soffice()` con i percorsi di Windows; `numero()`, `euro()` e `pct()` al posto di circa 110 format spec anglosassoni, con `t_formati_italiani` che vieta `{x:,.0f}` e `{x:.1%}` nei sorgenti e `€ 1,234` o `7.0%` negli output; CSV degli ordini con `;`, virgola decimale e BOM (`t_csv_italiano`); i «parametri pronti» di importa-previdenza restano letterali Python (`36_000`). Le voci «Windows ed encoding» e «Formati italiani» di ROADMAP sono spuntate.

### 2.4 T12 — test e CI che vincolano i numeri (P1, L)

Chiusa dalla PR #47 (T12): struttura uniforme e valori sentinella dei 6 xlsx dopo il ricalcolo, `--json` degli script previdenziali con valori chiusi sui default, `t_allocatore` sul JSON, rami avanzati (curvatura, buffer, `coeff_vigente` interpolato, sensibilità monotona), fixture con BOM, unità ed `xmlns`, tabella strumenti ↔ test nel README generata da `--tabella-test`, verbali esito-t2, esito-t3, esito-t13 ed esito-t12 con i 4 mutanti di F032 rieseguiti e uccisi.

### 2.5 T14 — authoring, documentazione e packaging (P2, M)

Chiusa dalla PR #48 (T14), salvo l'icona (§ 2.8): description entro 1.024 caratteri e quotate, `metadata.version` per skill, «Note per l'iterazione» e storico del README in `CHANGELOG.md` (anche nello zip), comandi come alias (`disable-model-invocation`, `argument-hint`, `$ARGUMENTS`), `upstream` in `metadata` e `claude plugin validate . --strict` nella CI, indici nelle 21 reference da 100 righe in su, README con `claude plugin update`, auto-update e `--scope`, IPS con titolo e lingua it-IT. F058 era già chiuso dalla PR #46. Costo di contesto sempre caricato: da circa 4.350 a circa 3.050 token (`claude plugin details`, verbale delle prove di installazione).

### 2.6 Pre-pubblicazione, voci di giudizio

Chiusa dalla PR #49, salvo le due prove che richiedono il proprietario:

- **Rilettura degli output operativi**: verbale in `docs/sviluppo/verbale-rilettura-output-2026-10-24.md`. OPZIONE e tetto dei €5.300 conformi al gate; corretti il CSV degli ordini (categoria del vocabolario, dati d'esempio dichiarati nella NOTA, percorso di `--out`), l'IPS d'esempio (avviso in copertina), l'intestazione dell'importatore e la postura delle leve previdenziali (scenari, non raccomandazioni), che stava solo nei comandi diventati alias.
- **README coerente con un repository pubblico**: aggiornamenti, `--scope`, opzione della cartella di lavoro e CHANGELOG nelle PR #48 e #49.
- **Prove di installazione**: verbale in `docs/sviluppo/verbale-installazione-2026-10-24.md` (via locale, via GitHub con le credenziali della sessione, `--config` e `/plugin configure`, script dalla copia in cache, zip estratto e validato con `--strict`). **Restano al proprietario**, con i passi nel verbale: l'installazione da un account senza accesso, possibile solo dopo la pubblicazione, e l'upload dello zip in Cowork.

### 2.7 Verifiche alle fonti rimaste

Fatte nella PR #49:

- **Art. 11 D.Lgs. 252/2005**: commi 3, 3-bis, 3-ter, 3-quater, 3-quinquies, 4, 4-bis, 4-ter, 6-bis e 6-ter riletti su Normattiva il 24/10/2026, con le decorrenze del c. 202 L. 199/2025 come modificato dal DL 62/2026 (1/7/2026; 31/10/2026 per la frazionata) e le corrispondenze 2027 dell'art. 258 D.Lgs. 117/2026 (c. 5 per il 6-bis). **Delibera COVIP del 25/6/2026**: il sito COVIP risponde 403, ma il testo è in GU Serie Generale n. 155 del 7/7/2026 (atto 26A03313), letta il 24/10/2026 su gazzettaufficiale.it (la revisione di T14 l'ha segnalato). Confermati non combinabilità, irrevocabilità salvo conversione in vitalizia, revoca prima del primo importo, niente RITA né anticipazioni con lo switch di comparto ammesso, non cumulo con una RITA in corso, transitorio non oltre il 31/12/2026; corretto «non si versa più»: si versa ancora il TFR di un nuovo rapporto di lavoro, come posizione distinta (par. 4). I vincoli sono dentro il marcatore, separati da quelli di legge; un test lo vincola.
- **Certificates**: l'art. 68 c. 5 TUIR (Normattiva, 24/10/2026) somma tra loro i redditi delle lettere c, c-bis, c-ter, c-quater e c-quinquies dell'art. 67, escluse le plus di partecipazioni in Stati a fiscalità privilegiata del c. 4. I certificates stanno di norma nella lett. c-quater, ma è un'interpretazione: non c'è una risoluzione AdE specifica (la 72/E/2010 riguarda gli ETC), e un certificato a capitale protetto al 100% può essere un titolo similare alle obbligazioni con proventi di capitale (art. 44 c. 2 lett. c n. 2 TUIR, dal 2027 art. 46 c. 2 lett. b n. 2, letti su Normattiva). In `it-tax-optimization` e in `genera-ips.py` la norma sta nel marcatore, l'interpretazione fuori.
- DM 21/02/2013 (Tobin tax) e probabile refuso dell'art. 306 c. 6 D.Lgs. 117/2026: invariati, in «Da verificare» della mappa fino ai correttivi; rivedere con la legge di bilancio 2027.
- Rimando a `ponte-pensione.py` in `mercati-e-correlazione.md` (esito-t8, nota 3): fatto.

### 2.8 Decisioni del proprietario

Prese tutte il 24/10/2026, dopo la 0.11.0:

- **Visibilità**: il repository è pubblico (decisione 2 di `ROADMAP.md`).
- **Branch protection**: un ruleset su `main` e `develop`.
- **T13**: riscatto della laurea (F055) e casi frequenti del freelance (F063), fatti con la PR #54. Per il riscatto, oltre la proposta dell'audit («solo sezione e `--set`»), c'è lo script `riscatto-laurea.py`.
- **Icona del plugin**: non si aggiunge. L'avviso ICON_MISSING di `claude plugin validate --strict` resta, e non cambia l'esito.

### 2.9 Dopo T13: T15, T17 e T16 (25/10-01/11/2026)

Tre temi «da decidere» della ROADMAP sono stati decisi e fatti, ognuno con spec → piano → implementazione in TDD → revisione finale, nello stesso branch:

- **T15 capitale umano** (PR #55 e #56): la lente diagnostica di Ibbotson, Milevsky, Chen e Zhu (2007). Cinque diagnosi (bilancio totale, esposizione azionaria finanziaria contro totale, proiezione con fascia Monte Carlo, sovrapposizione settoriale contro i pesi dell'MSCI ACWI, sensibilità); sei profili in `profili-capitale-umano.csv` con la natura di ogni valore; catena `--from` dai JSON di proiezione INPS, netto e glide path; it-revisione ne legge esposizioni, sovrapposizione e `stato_sorpasso`. Gli otto minori della revisione finale sono nel commit `cfac020`.
- **T17 cruscotto grafico** (PR #57): `genera-cruscotto.py` riconosce i JSON dalle chiavi (`FIRME`), estrae il bundle minimo e lo incorpora in `cruscotto.html`; nove sezioni in SVG senza risorse esterne, tema chiaro e scuro; la pagina non porta ISIN né descrizioni delle posizioni. I test nel browser richiedono Playwright e Chromium (in CI `playwright install --with-deps chromium`; in locale senza Playwright risultano saltati). Pubblicazione come Artifact solo dopo un sì esplicito. Resta da provare a mano la pubblicazione in claude.ai e in Cowork (proprietario).
- **T16 importatore della composizione** (PR #58): `importa-composizione-etf.py` legge i file delle posizioni di iShares, Xtrackers, Vanguard, Amundi e SPDR (CSV o XLSX, italiano o inglese), con una riga d'intestazione da sinonimi e una scheda per emittente, e scrive `composizione.csv` (`strumento;dimensione;voce;peso`) fondendolo con l'esistente; `capitale-umano.py` legge il formato nuovo e il vecchio. Layout di Xtrackers e SPDR verificati su file reali; **iShares, Vanguard e Amundi restano «da confermare»** su un file reale (`SCHEDE` nello script e tabella in `composizione-etf.md`). I minori rinviati della revisione sono nel commit `e5ed676`.

Le evolutive annotate nella ROADMAP a valle dei tre temi: look-through del portafoglio (T16 C), lingue tedesca e francese dell'importatore, le fonti dati a priorità media e bassa della tabella di T16, i quattro sviluppi del capitale umano, i tre del cruscotto.

## 3. Prossimi passi

Ordine di lavoro deciso dal proprietario l'1/11/2026 per il ciclo 0.12.0, dopo la revisione dello stato del repository (suite locale 168/168 con i 4 test del browser saltati senza Playwright):

1. **Igiene documentale** (questo file e l'intestazione della ROADMAP): fatto.
2. **Look-through del portafoglio** (T16 C): fatto sul branch `claude/awesome-albattani-gkn0qc` (spec `docs/sviluppo/specs/2026-11-01-look-through-design.md`, piano `docs/sviluppo/piani/2026-11-01-look-through.md`, esito `docs/sviluppo/revisioni/esito-t16c.json`): `look-through-portafoglio.py`, righe `titolo` e `--isin` dell'importatore, `chiave_composizione()` nel capitale umano, sezione «Look-through» del cruscotto, Step 8, passo 3 e contratto di input di it-revisione.
3. **Ponte pensione e riscatto della laurea nel cruscotto** (sviluppo di T17): fatto sullo stesso branch, nella sezione Pensione.
4. **Lingue tedesca e francese** dell'importatore della composizione: fatto sullo stesso branch, solo tabelle, con le fixture `composizione-xtrackers-de.csv` e `composizione-amundi-fr.csv`.
5. **PR #59 unita su develop** il 7/11/2026. **Rilascio 0.12.0**: `release/0.12.0` preparato lo stesso giorno (manifest, changelog, README, ROADMAP, questo file). Al proprietario: PR di `release/0.12.0` su `main` con merge commit, tag `v0.12.0` sul merge commit (`git tag -a v0.12.0 <sha> -m v0.12.0 && git push origin v0.12.0`, senza creare prima la release dall'interfaccia), controllo di `release.yml` e merge back di `main` su `develop`. Le skill sono a it-pianificazione-obiettivi 0.24 e it-revisione 0.9; la suite conta 182 test.

Rinviati a dopo la legge di bilancio 2027, quando si riapre comunque la calibrazione: le fonti dati a priorità media e bassa di T16 (R_F dalla BCE, `p_u` e durata da ISTAT e INPS, NASpI nella freshness, `sigma_h`, rendimenti europei, `PESI_MONDO`), i quattro sviluppi del capitale umano (secondo reddito, volatilità personale dall'estratto INPS, aggiustamento dei target, polizza vita) e gli altri due del cruscotto (confronto tra due revisioni, versione anonimizzata).

Restano al proprietario: le due prove di installazione del § 2.6 (account senza accesso e upload dello zip in Cowork), la prova manuale della pubblicazione del cruscotto come Artifact in claude.ai e in Cowork, il tag della 0.12.0. I layout iShares, Vanguard e Amundi sono stati confermati il 7/11/2026 su file reali forniti dal proprietario (siti italiani; Amundi come file di ripartizione dell'indice); poi anche il «Fund Holdings» di Amundi (ETF a swap) e il «Constituent» di Xtrackers dal sito tedesco; restano da confermare iShares dal sito britannico e Amundi dai siti tedesco e francese.

Con il calendario del README («Freshness fiscale»):

- **Con la legge di bilancio 2027 e i correttivi del D.Lgs. 117/2026**: rivedere i due punti «Da verificare» della mappa dei testi unici (rinvii del DM 21/02/2013, art. 306 c. 6) e le soglie annuali (massimale contributivo, minimale INPS, onere del riscatto agevolato, coefficienti, tassi di rivalutazione).
- **Dal 1/1/2027** entrano in vigore i testi unici: le doppie citazioni di `mappa-nuovo-tuir.md` restano valide, ma la citazione principale va girata sul testo nuovo quando le prassi dell'AdE lo seguono.
- **Entro giugno 2027**: riverifica alle fonti dei marcatori del 2026-06, prima che la freshness mensile apra la issue e prima di un nuovo tag (`release.yml` esegue anche la freshness).

## 4. Regole di lavoro

- **Gitflow**: `feature/*` → PR su `develop`, merge commit (`gh pr merge N --merge`), poi eliminazione del branch; `release/X.Y.Z` → `main` con tag e merge back. Messaggi di commit in italiano; la riga `Co-Authored-By` e la chiusura delle PR sono quelle indicate dall'ambiente della sessione.
- **Decisioni del proprietario**: § «Decisioni» di `ROADMAP.md` (repository privato fino alla pre-pubblicazione, pubblico dal 24/10/2026; dichiarativo solo come principi; uscite operative con gate stretti e disclaimer; F012 come correzione) e il § 2.8 di questo file. Il repository è pubblico: niente dati personali reali nei file, nelle fixture e nei test.
- **TDD**: prima il test che fallisce per la ragione giusta, poi il fix; test che vincolano i numeri; validazione per mutazione dove possibile.
- **Fonti primarie** (Normattiva, Gazzetta Ufficiale, AdE, INPS, COVIP, MEF) per ogni dato normativo; marcatori `Verificato: AAAA-MM` circoscritti a ciò che è confermato; doppia citazione per le norme che cambiano dal 2027 (`mappa-nuovo-tuir.md`).
- **Propagazione**: ogni correzione in tutte le copie (`git grep` su `skills/`, `commands/`, README, manifest).
- **Excel**: mai salvare con openpyxl i file con convalide o strutture delicate; modificare l'XML nello zip e poi `python scripts/ricalcola-excel.py FILE --in-place` (ricalcolo in locale it-IT). Confrontare la struttura prima e dopo.
- **Revisione avversariale prima di ogni merge di tema**: `docs/sviluppo/workflows/review-tema-roadmap.js` (Workflow tool, args `{repo, scratch, python, branch, base, tema, finding}`); il modello per applicare le correzioni è `correzioni-temi-roadmap.js`. Esito in `docs/sviluppo/revisioni/esito-<tema>.json`.
- **CI verde prima del merge**: `suite` (3.11 e 3.14, LibreOffice e Playwright con Chromium obbligatori), `test-windows`, `validate` (con `--strict`) e `freshness`. Il job `test` le riassume per il ruleset di `main` e `develop`, che chiede i check `test` e `validate`.

## 5. Ambiente

```bash
pip install -r tests/requirements.txt          # numpy, openpyxl, python-docx
sudo apt-get install -y libreoffice-calc        # per i test che ricalcolano gli Excel (altrimenti risultano saltati)
pip install playwright && playwright install --with-deps chromium   # per i test del cruscotto nel browser (altrimenti saltati)
python tests/run_tests.py                       # tutta la suite
python tests/run_tests.py --only freshness      # solo freshness
python tests/run_tests.py --tabella-freshness   # tabella per il README
```

In CI: `RICHIEDI_LIBREOFFICE=1` rende obbligatori i test Excel e `RICHIEDI_BROWSER=1` quelli del browser (`PLAYWRIGHT_CHROMIUM_EXECUTABLE` indica un Chromium già installato); matrice Python 3.11 e 3.14; `scripts/installa-libreoffice.sh` installa LibreOffice dai `.deb` in cache (PR #39). Il validatore locale: `claude plugin validate .`.

## 6. Storico e materiale

- Passaggio del 21/10/2026: stato prima della 0.10.0, temi su branch separati, note fuori perimetro (§ 4 di allora): tutto chiuso tranne il conteggio dei test del README (§ 2.1).
- `docs/sviluppo/revisioni/`: `review-<tema>.json` (esiti delle revisioni avversariali: `confermati`, `contesi`, `non_verificati`) ed `esito-<tema>.json` (cosa è stato applicato), uno per tema; esito-t2, esito-t3 ed esito-t13 ricostruiti con la PR #47. Per la 0.11.0: esito-t9a, esito-t9bcd, esito-t12 ed esito-t14 (quest'ultimo copre anche la PR #49). Dopo: esito-t13b e esito-t16a; per T15 e T17 l'esito della revisione finale è nei commit di correzione (`9772053`, `cfac020`, `daa37cc`, `83c51da`), senza file JSON.
- `docs/sviluppo/t11/`: `mappa-nuovo-tuir.md` e `doppie-citazioni.md` sono bozze storiche, già integrate nella reference; i verbali `verifica-2026-10-22-*.md` sono la fonte delle corrispondenze 2027.
- Circ. AdE 30/E/2023: il PDF sul sito AdE dà 404; copia integrale su dirittobancario.it.
