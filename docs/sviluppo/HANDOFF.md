# Passaggio della sessione di sviluppo — 24/10/2026

Documento per riprendere lo sviluppo in un'altra sessione (Claude Code in cloud o su un'altra macchina). Sostituisce la versione del 21/10/2026, che descriveva lo stato prima della 0.10.0. Tutto ciò che serve è nel repository: questo file, `ROADMAP.md`, `docs/audit-2026-10.md` e i dati in `docs/sviluppo/`.

## 1. Dove siamo

- **0.10.0 rilasciata il 22/10/2026**: tag `v0.10.0`, release con lo zip, merge back su develop (PR #35 e #36). Dentro: ondata 0, T1-T8, T10, T11 e parte di T13. Le sessioni cloud del 21-23/10 hanno chiuso T2, T3, T13, T8, T7, T11 (sessione A) e T5, T4, T6 con le note previdenziali (sessione B).
- **Dopo il tag, su develop** (e9d804c, CI verde su 3.11 e 3.14): PR #37 (art. 13 c. 10 del TUIR 2027 in `netto-pensione.py`, Inarcassa under 35), PR #38 (corrispondenze 2027 verificate su Normattiva, verbali in `t11/verifica-2026-10-22-*.md`), PR #39 (LibreOffice in CI con i `.deb` in cache, `scripts/installa-libreoffice.sh`), PR #40 (T7: campo `quota_titoli_stato` e aliquota mista per ETF e fondi su titoli di Stato). Nessuna delle quattro è nel changelog del README né nello «Stato al» di `ROADMAP.md`. La prossima versione è la **0.11.0**: la #40 è una funzionalità nuova, quindi niente 0.10.1.
- PR #41 (questo documento) mergiata il 24/10/2026; PR #42 «stato dopo la 0.10.0» (§ 2.1) mergiata; PR #43 T9 (a) (F056 e § 2.3); PR #44 T9 (b) (F028), aperta sul branch della #43; PR #45 T9 (c) (F027, F031), aperta sul branch della #44. Branch remoti già mergiati e **da cancellare dal proprietario**: `claude/kind-meitner-crztg2`, `claude/vigilant-cannon-1otexq`, `feature/verifiche-fonti`, `feature/handoff-0.11` e i `feature/*` delle PR di questa sessione. Dalla sessione cloud la cancellazione è negata: il proxy GitHub risponde 403 sia a `git push origin --delete` sia a `DELETE /git/refs` (`delete_branch_on_merge` è spento sul repository e non si può accendere da qui).
- Suite: 117 test (`@test` in `tests/run_tests.py`; il conteggio nel README è vincolato da un test di igiene). Freshness: nessun marcatore scade prima del 2027-06.
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
- **F033 input esterno.** `genera-ips.py:494-495` prende qualsiasi `argv[1]` come file di output (`--dati x.json` crea un file chiamato `--dati`), dati demo «Mario Rossi» a `:44-45` senza avviso; il ribilanciamento ha portafoglio, zainetto e target cablati. Da fare: `--dati <json>` con schema documentato in SKILL.md e avviso «dati di esempio»; input da file per il ribilanciamento (anche il JSON dell'importatore) e cartella di output come argomento; test per entrambi.
- **F026 vocabolario.** `README.md:497` schema CSV senza `broker` mentre `it-tax-optimization/SKILL.md:109` e `:135` lo dicono obbligatorio; nomi e valori diversi per la categoria fiscale tra README, SKILL e script (`CATEGORIE` in `importa-estratto-broker.py:140`, `CAMPI_CSV` in `ribilanciamento-multibroker.py:521`). Da fare: un solo nome e un solo set di valori (lo script accetta i sinonimi e li normalizza), `broker` nello schema, glossario di circa 8 termini nel README, test di coerenza del lessico.
- **F059 «Dove lavorare».** Nessuna SKILL ha la sezione; `CLAUDE_PLUGIN_ROOT` e `CLAUDE_SKILL_DIR` compaiono solo nell'audit; invocazioni a nome nudo in `it-pianificazione/SKILL.md:112` e `:390`, `it-pianificazione-obiettivi/SKILL.md:223`, `:231`, `:243`, `:254`, `it-revisione/SKILL.md:106`, `commands/minusvalenze.md:15`. Da fare: sezione in ogni SKILL.md, con la variabile giusta verificata sulla documentazione ufficiale di Claude Code (`${CLAUDE_SKILL_DIR}` nelle skill, `${CLAUDE_PLUGIN_ROOT}` nei command) e il file di lavoro sempre come argomento; `userConfig` facoltativo; test di igiene. Si chiude insieme a F058 di T14.
- **F031 contratto di input di it-revisione.** Fatto nella PR #45: tabella «Contratto di input» (dominio → script `--json` → campo → cella del cruscotto) in `skills/it-revisione/SKILL.md`; `template-revisione.md` rimanda agli script; `ROADMAP.md` spuntata.

### 2.3 Windows, encoding e formati italiani (pre-pubblicazione, insieme all'helper di T9)

Chiusa dalla PR #43 (T9a): UTF-8 forzato su stdout e stderr in ogni script, negli `scripts/` e nel runner; `open()` sempre con encoding (test `t_cli_utf8` lo controlla su assets, scripts e tests); `relpath` con `/`; job `test-windows` su `windows-latest` (Python 3.11, senza LibreOffice); `trova_soffice()` con i percorsi di Windows; `numero()`, `euro()` e `pct()` al posto di circa 110 format spec anglosassoni, con `t_formati_italiani` che vieta `{x:,.0f}` e `{x:.1%}` nei sorgenti e `€ 1,234` o `7.0%` negli output; CSV degli ordini con `;`, virgola decimale e BOM (`t_csv_italiano`); i «parametri pronti» di importa-previdenza restano letterali Python (`36_000`). Le voci «Windows ed encoding» e «Formati italiani» di ROADMAP sono spuntate.

### 2.4 T12 — test e CI che vincolano i numeri (P1, L)

Fatto: errori e cache su tutti e 6 gli xlsx (`t_excel_errori`, `t_excel_cache`; il tracker è escluso dal confronto cache per le sue 6 `TODAY()`), F065 per intero, CSV ordini con colonne == `CAMPI_CSV`, ramo bootstrap e `ter_pareggio_pir` con asserzione.

- **Strutturali.** Manca un test uniforme per file: elenco esatto dei fogli, intestazioni chiave, soglia minima di formule (oggi autonomi 690, pianificatore 110, proiezione-pensione 1095, cruscotto 415, IPS 14, tracker 145). L'IPS non ha nessun test di struttura; `cruscotto!Patrimonio` e `pianificatore!Riepilogo` non sono mai letti; per il tracker confronto cache/ricalcolo escludendo le celle volatili.
- **`--json`.** Test per montecarlo-pensione (chiavi di `:152-158`, seed 42 → mediana pinnata) e ponte (`probabilita_successo == 21.1`, `capitale_necessario` monotono); in `t_netto_quota_imponibile` il valore chiuso di `tasso_sostituzione_netto`.
- **`t_allocatore`** sul JSON: `aggregato.totale == 50000` e somma di `obiettivi[*].allocato` + `surplus_capitale_libero` == capitale, tolleranza al centesimo.
- **Rami avanzati.** `CURVATURA=0.5` (frazione a metà finestra maggiore della lineare), buffer del decumulo (`BUFFER_ANNI` 0 contro 2), proiezione-inps senza `COEFF_ESPLICITO` con tabella di sensibilità (monotona nel PIL) e `coeff_vigente(67.5)` uguale alla media dei due coefficienti: oggi `coeff_vigente` non è mai chiamato dai test.
- **Fixture.** BOM (nessuna fixture lo ha; importa-previdenza legge con utf-8 senza `-sig` a `:185` e `:189`), segno «-» nello storico fondo, unità «(EUR)» nelle intestazioni, estratto INPS con `xmlns`; i numeri inglesi sono già coperti.
- **Mutanti.** Verbale con esito per T2, T3 e T13 (oggi solo nei messaggi di commit ccdbc58, 4d7872c, c63be5f: in `revisioni/` mancano esito-t2, esito-t3 ed esito-t13) e per i 4 di F032, rieseguiti sul develop attuale.
- **README.** Tabella strumenti e file ↔ test, generata dal runner come `--tabella-freshness`.

### 2.5 T14 — authoring, documentazione e packaging (P2, M)

Fatto: F051 (nessun nome dell'autore sotto `skills/` e `commands/`), recalc del sandbox rimosso, sezioni del README di F025, `ribilancia.md:13`, `it-pianificazione-obiettivi:40`, `.gitignore` con `.DS_Store`, versioni allineate tra i due manifest.

- **F023 description e frontmatter.** Lunghezze: tax 2.271, autonomi 1.637, obiettivi 1.285, revisione 1.112, pianificazione 1.071, rebalance 1.029 caratteri, tutte oltre 1.024. Tutte e sei contengono «: » non quotati e falliscono un parser YAML stretto (PyYAML, colonne 561 e 948): `claude plugin validate` non lo rileva, ma è un rischio per l'upload in Cowork. «Note per l'iterazione» (202 righe) nel corpo delle SKILL; nessun `metadata.version`; intestazioni stale (`it-pianificazione:19` e `:375`, coda di `it-rebalance:3`). Da fare: description ≤ 1.024 e quotate (cosa fa, trigger essenziali, esclusioni; il resto in `when_to_use`), `metadata: {version: "0.x"}` come stringa con test, Note spostate in CHANGELOG.md; togliere dalla description di it-pianificazione i trigger non gestiti (riscatto, ricongiunzione, totalizzazione).
- **CHANGELOG.md.** Assente; il changelog è `README.md:126-414` (305 righe). Da fare: CHANGELOG.md con le voci del README e le Note delle skill, sezione «Non rilasciato»; rimando dal README; aggiornare `run_tests.py:2480` e, se entra nello zip, `INCLUDI` in `scripts/pacchetto.py:28`.
- **F057 commands come alias.** I 6 command duplicano i workflow delle skill. Da fare: `disable-model-invocation: true`, `argument-hint`, corpo «Esegui la skill `it-…` su: $ARGUMENTS» più il disclaimer richiesto da `t_disclaimer_comandi`; adattare i test che ancorano frasi dei command (`run_tests.py:2932-2937`, `:3693-3704`, `:3708-3719`, `:3725-3732`) e togliere `ribilancia.md` da `t_t7_testi`; test che ogni command punti a una skill esistente.
- **F058.** Invocazioni con la variabile di percorso (vedi F059) e, in `it-revisione/SKILL.md:74`, rimando a `scripts/ricalcola-excel.py` condizionale: non è nello zip di Cowork.
- **F061 manifest e aggiornamenti.** `upstream` al top level di `plugin.json` (con `--strict` il validate dà rc 1); `version` duplicata nel marketplace senza assert; README senza `claude plugin update`, auto-update spento di default e `--scope`; `README.md:440` «aggiornamenti con un comando» in contrasto con `:453`. Da fare: `metadata.upstream`, assert in `t_marketplace`, README, poi `--strict` nel job validate (`tests.yml:74`).
- **F066 indici.** 19 reference oltre 100 righe, più due esattamente a 100 (`mappa-nuovo-tuir.md`, `dividendi-esteri.md`), nessuna con indice. Da fare: «## Indice» con gli H2; eventuale test con soglia ≥ 100.
- **Lingua e titolo dell'IPS.** `genera-ips.py:369-372` crea `Document()` senza `core_properties.title` né lingua, e nessun `w:lang` it-IT sugli stili (`qn` e `OxmlElement` sono già importati a `:37-38`): è un rilievo della critica dell'audit (`docs/audit-2026-10.md:1885-1889`) mai entrato in ROADMAP. Da fare: titolo, lingua e `w:lang` nel generatore, assert in `t_genera_ips` (`run_tests.py:2417`); si accorpa alla rilettura degli output.
- **Icona.** `claude plugin validate` segnala `ICON_MISSING`: serve solo per il plugin directory. Decisione del proprietario, non bloccante.

### 2.6 Pre-pubblicazione, voci di giudizio

- **Rilettura degli output operativi** (decisione 4): stdout e CSV di `ribilanciamento-multibroker.py`, output dell'importatore, IPS di `genera-ips.py`, Excel e sezioni «Formato output» delle 6 SKILL, contro la OPZIONE sulla leva di rischio, il «versa fino a €5.300» (già «tetto fiscale, non importo consigliato» dalla PR #28) e il CSV degli ordini solo con gate. Verbale in `docs/sviluppo/` e spunta.
- **README coerente con un repository pubblico.** Manca solo la parte sugli aggiornamenti (F061) e la pulizia dei conteggi; badge, installazione da GitHub, Releases e marketplace ci sono.
- **Prova di installazione.** Fatta quella locale (21/10, senza verbale). Restano l'installazione da un account esterno, possibile solo dopo la pubblicazione, e l'upload dello zip in Cowork, che richiede l'interfaccia di Cowork: entrambe del proprietario. Scrivere il verbale della prova locale e i passi delle altre due.

### 2.7 Verifiche alle fonti rimaste

- Art. 11 c. 3-quater e 3-quinquies D.Lgs. 252/2005 e delibera COVIP del 25/6/2026: i vincoli in `previdenza-complementare.md:248-253` (alternatività, irrevocabilità, conversione in vitalizia, non cumulo con RITA, beneficiari, transitorio al 31/12/2026) non sono stati riletti su fonte primaria dalla sessione che ha scritto il testo (PR #37: Normattiva e COVIP irraggiungibili), ma stanno dentro il marcatore di `:281`. Da una sessione con rete: leggerli su Normattiva e COVIP; se non confermabili, circoscrivere il marcatore.
- Certificates come redditi diversi compensabili: `skills/it-revisione/assets/genera-ips.py:141-144`, blocco «Verificato: 2026-10» di `POLICY_FISCALITA`, chiude con «Non verificata su fonte primaria la compensabilità dei certificati», e il file è in `OBBLIGATI_FRESHNESS`. Verificare (art. 67 c. 1 lett. c-quater TUIR, dal 2027 art. 76; prassi AdE), allineare `it-tax-optimization/SKILL.md:33`, che li elenca sotto le lettere c-bis/c-ter, e togliere la riserva; altrimenti spostarla fuori dal marcatore.
- DM 21/02/2013 (Tobin tax) e probabile refuso dell'art. 306 c. 6 D.Lgs. 117/2026: restano in «Da verificare» della mappa finché non escono correttivi o errata corrige. Nessuna modifica ai testi; rivedere con la legge di bilancio 2027.
- Facoltativo: rimando a `ponte-pensione.py` in `mercati-e-correlazione.md:23` (esito-t8, nota 3).

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
- `docs/sviluppo/revisioni/`: `review-<tema>.json` (esiti delle revisioni avversariali: `confermati`, `contesi`, `non_verificati`) ed `esito-<tema>.json` (cosa è stato applicato). Mancano esito-t2, esito-t3 ed esito-t13 (§ 2.4, mutanti).
- `docs/sviluppo/t11/`: `mappa-nuovo-tuir.md` e `doppie-citazioni.md` sono bozze storiche, già integrate nella reference; i verbali `verifica-2026-10-22-*.md` sono la fonte delle corrispondenze 2027.
- Circ. AdE 30/E/2023: il PDF sul sito AdE dà 404; copia integrale su dirittobancario.it.
