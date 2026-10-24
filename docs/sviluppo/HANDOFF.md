# Passaggio della sessione di sviluppo — 24/10/2026

Documento per riprendere lo sviluppo in un'altra sessione (Claude Code in cloud o su un'altra macchina). Sostituisce la versione del 21/10/2026, che descriveva lo stato prima della 0.10.0. Tutto ciò che serve è nel repository: questo file, `ROADMAP.md`, `docs/audit-2026-10.md` e i dati in `docs/sviluppo/`.

## 1. Dove siamo

- **0.10.0 rilasciata il 22/10/2026**: tag `v0.10.0`, release con lo zip, merge back su develop (PR #35 e #36). Dentro: ondata 0, T1-T8, T10, T11 e parte di T13. Le sessioni cloud del 21-23/10 hanno chiuso T2, T3, T13, T8, T7, T11 (sessione A) e T5, T4, T6 con le note previdenziali (sessione B).
- **Dopo il tag, su develop** (e9d804c, CI verde su 3.11 e 3.14): PR #37 (art. 13 c. 10 del TUIR 2027 in `netto-pensione.py`, Inarcassa under 35), PR #38 (corrispondenze 2027 verificate su Normattiva, verbali in `t11/verifica-2026-10-22-*.md`), PR #39 (LibreOffice in CI con i `.deb` in cache, `scripts/installa-libreoffice.sh`), PR #40 (T7: campo `quota_titoli_stato` e aliquota mista per ETF e fondi su titoli di Stato). Nessuna delle quattro è nel changelog del README né nello «Stato al» di `ROADMAP.md`. La prossima versione è la **0.11.0**: la #40 è una funzionalità nuova, quindi niente 0.10.1.
- PR #41 (questo documento), #42 «stato dopo la 0.10.0» e #43 T9 (a) mergiate il 24/10/2026. **Aperte in catena**, ognuna sul branch della precedente, da mergiare in ordine dopo la CI verde: #44 T9 (b), #45 T9 (c), #46 T9 (d), #47 T12, #48 T14, #49 pre-pubblicazione (§ 2.6-2.7). Branch remoti già mergiati e **da cancellare dal proprietario**: `claude/kind-meitner-crztg2`, `claude/vigilant-cannon-1otexq`, `feature/verifiche-fonti`, `feature/handoff-0.11` e i `feature/*` delle PR di questa sessione. Dalla sessione cloud la cancellazione è negata: il proxy GitHub risponde 403 sia a `git push origin --delete` sia a `DELETE /git/refs` (`delete_branch_on_merge` è spento sul repository e non si può accendere da qui).
- Suite: 132 test (`@test` in `tests/run_tests.py`; il conteggio nel README è vincolato da un test di igiene). Freshness: nessun marcatore scade prima del 2027-06.
- Il repository è **privato** e resta tale: la visibilità la decide il proprietario (decisione 2 di `ROADMAP.md`).

Questo documento nasce da una ricognizione del 23/10/2026 su develop e9d804c: cinque lettori, uno per fetta della roadmap, e due verificatori avversariali per ogni voce (lenti «stato» ed «evidenza»). Le righe citate valgono a quel commit. Delle 11 note fuori perimetro del passaggio precedente 10 sono chiuse (PR #27, #28, #30, #31, #32, #38 e i commit dei temi); le revisioni avversariali di T7, T11 e T13 non hanno rilievi non applicati.

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

### 2.8 Da decidere dal proprietario: non toccare senza decisione

- Visibilità del repository (decisione 2) e branch protection (richiede repository pubblico o GitHub Pro).
- T13: riscatto della laurea (F055) e casi del freelance (F063), `ROADMAP.md` § «Dopo». La pulizia della description di it-pianificazione si fa comunque con F023.
- Icona del plugin.

## 3. Ordine di lavoro consigliato

1. Mergiare la PR di questo documento (CI verde → merge commit → elimina il branch), `git pull`, cancellare i tre branch remoti del § 1.
2. PR «stato dopo la 0.10.0»: § 2.1 per intero.
3. T9 in più PR, ognuna con revisione avversariale prima del merge: (a) helper CLI, UTF-8, formati italiani, CSV con `;`, `windows-latest` (F056 e § 2.3); (b) lettore unico del pianificatore (F028); (c) `--from`, `--json` su glidepath e montecarlo-obiettivi, test «catena», contratto di input di it-revisione (F027, F031); (d) input esterno, «Dove lavorare», vocabolario e glossario (F033, F059, F026, insieme a F058).
4. T12 (§ 2.4), in una o due PR.
5. T14 (§ 2.5): description e YAML, CHANGELOG.md, command come alias, manifest e `--strict`, indici, aggiornamenti nel README.
6. § 2.6 e § 2.7: rilettura degli output con verbale, verbale delle prove di installazione, verifiche alle fonti.
7. **Rilascio 0.11.0**: versione in `plugin.json` e `marketplace.json`, changelog, ROADMAP spuntata con il nuovo «Stato al», README (conteggio dei test, tabella freshness rigenerata con `--tabella-freshness`), questo file aggiornato; `release/0.11.0` da develop → PR su main (merge commit) → tag `v0.11.0` → verifica di `release.yml` (suite completa con freshness, zip con LICENSE, NOTICE e CHANGELOG.md) → merge back su develop. Finestra: i marcatori più vecchi sono del 2026-06 e scadono a giugno 2027; `release.yml` esegue anche la freshness, quindi il tag va dato prima, oppure dopo una riverifica alle fonti.
8. Al termine, lasciare in questo file ciò che resta al proprietario (§ 2.8 e le prove di installazione).

## 4. Regole di lavoro

- **Gitflow**: `feature/*` → PR su `develop`, merge commit (`gh pr merge N --merge`), poi eliminazione del branch; `release/X.Y.Z` → `main` con tag e merge back. Messaggi di commit in italiano; la riga `Co-Authored-By` e la chiusura delle PR sono quelle indicate dall'ambiente della sessione.
- **Decisioni del proprietario**: § «Decisioni» di `ROADMAP.md` (repository privato fino alla pre-pubblicazione; dichiarativo solo come principi; uscite operative con gate stretti e disclaimer; F012 come correzione) e il § 2.8 di questo file. Non rendere pubblico il repository.
- **TDD**: prima il test che fallisce per la ragione giusta, poi il fix; test che vincolano i numeri; validazione per mutazione dove possibile.
- **Fonti primarie** (Normattiva, Gazzetta Ufficiale, AdE, INPS, COVIP, MEF) per ogni dato normativo; marcatori `Verificato: AAAA-MM` circoscritti a ciò che è confermato; doppia citazione per le norme che cambiano dal 2027 (`mappa-nuovo-tuir.md`).
- **Propagazione**: ogni correzione in tutte le copie (`git grep` su `skills/`, `commands/`, README, manifest).
- **Excel**: mai salvare con openpyxl i file con convalide o strutture delicate; modificare l'XML nello zip e poi `python scripts/ricalcola-excel.py FILE --in-place` (ricalcolo in locale it-IT). Confrontare la struttura prima e dopo.
- **Revisione avversariale prima di ogni merge di tema**: `docs/sviluppo/workflows/review-tema-roadmap.js` (Workflow tool, args `{repo, scratch, python, branch, base, tema, finding}`); il modello per applicare le correzioni è `correzioni-temi-roadmap.js`. Esito in `docs/sviluppo/revisioni/esito-<tema>.json`.
- **CI verde prima del merge**: `tests` (3.11 e 3.14, LibreOffice obbligatorio) e `validate`.

## 5. Ambiente

```bash
pip install -r tests/requirements.txt          # numpy, openpyxl, python-docx
sudo apt-get install -y libreoffice-calc        # per i test che ricalcolano gli Excel (altrimenti risultano saltati)
python tests/run_tests.py                       # tutta la suite
python tests/run_tests.py --only freshness      # solo freshness
python tests/run_tests.py --tabella-freshness   # tabella per il README
```

In CI: `RICHIEDI_LIBREOFFICE=1` rende obbligatori i test Excel; matrice Python 3.11 e 3.14; `scripts/installa-libreoffice.sh` installa LibreOffice dai `.deb` in cache (PR #39). Il validatore locale: `claude plugin validate .`.

## 6. Storico e materiale

- Passaggio del 21/10/2026: stato prima della 0.10.0, temi su branch separati, note fuori perimetro (§ 4 di allora): tutto chiuso tranne il conteggio dei test del README (§ 2.1).
- `docs/sviluppo/revisioni/`: `review-<tema>.json` (esiti delle revisioni avversariali: `confermati`, `contesi`, `non_verificati`) ed `esito-<tema>.json` (cosa è stato applicato), uno per tema; esito-t2, esito-t3 ed esito-t13 ricostruiti con la PR #47.
- `docs/sviluppo/t11/`: `mappa-nuovo-tuir.md` e `doppie-citazioni.md` sono bozze storiche, già integrate nella reference; i verbali `verifica-2026-10-22-*.md` sono la fonte delle corrispondenze 2027.
- Circ. AdE 30/E/2023: il PDF sul sito AdE dà 404; copia integrale su dirittobancario.it.
