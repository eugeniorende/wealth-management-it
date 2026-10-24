# wealth-management-it

[![tests](https://github.com/eugeniorende/wealth-management-it/actions/workflows/tests.yml/badge.svg)](https://github.com/eugeniorende/wealth-management-it/actions/workflows/tests.yml)

Fork del plugin [`wealth-management`](https://github.com/anthropics/financial-services/tree/ef165e4160/plugins/vertical-plugins/wealth-management) di Anthropic (all'ultimo commit che lo conteneva: l'upstream l'ha rimosso l'11/09/2026), adattato alla fiscalità italiana (regime amministrato).

> ⚠️ **Non costituisce consulenza fiscale, finanziaria o di investimento.** È uno strumento di pianificazione personale. Per casi specifici consultare un commercialista o consulente abilitato.

## Perché un fork e non un'estensione

L'upstream è cablato sulla fiscalità USA: wash sale rule a 30 giorni, scelta del cost basis method (HIFO/LIFO/SpecID), strumenti tax-advantaged tipo Roth IRA/401k. Le regole italiane sono *strutturalmente diverse*, non semplicemente "una variante":

| Aspetto | Upstream (USA) | Fork (IT) |
|---|---|---|
| Wash sale | 30 giorni di vincolo dopo realizzo perdita | Inesistente, riacquisto immediato legittimo |
| Cost basis | Scelta investitore (HIFO/LIFO/SpecID) | Costo medio ponderato in amministrato, LIFO in dichiarativo: il lotto non si sceglie |
| Compensazione cross-category | Cap gain compensa qualsiasi cap gain | Solo "redditi diversi" tra loro; non con "redditi di capitale" |
| Dividendi | Possono essere "qualified" o "ordinary", compensabili in alcuni casi | Sempre reddito di capitale, mai compensabili con minus |
| ETF | Tutti uguali fiscalmente | Trappola ETF: plus reddito di capitale (UCITS e non armonizzati), minus reddito diverso |
| Scadenza loss carryforward | Indefinita | 4 anni |
| Tax-advantaged accounts | Roth/Traditional IRA, 401k, HSA, 529 | Fondo pensione: coperto dalle skill previdenziali (deducibilità, tassazione in uscita, confronto con il PAC) |

Un overlay/extension avrebbe creato conflitti dove Claude pesca dalla skill sbagliata. Meglio sostituzione completa.

## Stato del progetto (v0.10.0)

> **Errori noti.** L'audit del 20/10/2026 ha confermato 65 problemi, alcuni dei quali producevano numeri sbagliati sui percorsi principali. La 0.10.0 chiude l'ondata 0 e i temi T1-T8, T10, T11 e parte di T13: tra gli altri l'importatore broker (F001), il ribilanciamento con i versamenti (F004), il plafond del fondo pensione nell'Excel (F007), la certificazione delle minus alla chiusura del rapporto (F011) e il costo medio in amministrato (F012). Dopo il tag, su `develop` e non ancora rilasciate, sono entrate le correzioni della sezione «Non rilasciato» del changelog; le corrispondenze del 2027 nella mappa dei testi unici sono verificate su Normattiva (PR #38) salvo due punti, i rinvii del DM 21/02/2013 e il probabile refuso dell'art. 306 c. 6 del D.Lgs. 117/2026, che restano «da verificare» finché non escono correttivi. Restano aperti l'interfaccia comune degli script (T9), i test strutturali sugli Excel (T12), il riscatto della laurea e i casi del freelance (T13, da decidere), la documentazione e il packaging (T14). Il piano è in [ROADMAP.md](ROADMAP.md); il dettaglio è in [docs/audit-2026-10.md](docs/audit-2026-10.md).

Sei skill operative: `it-pianificazione-obiettivi` (pianificazione goals-based — il pezzo a monte), `it-tax-optimization` (ottimizzazione minus/plus, titoli e cripto), `it-pianificazione` (pensione dipendenti), `it-pianificazione-autonomi` (pensione autonomi/forfettari), `it-rebalance` (ribilanciamento tax-aware), e `it-revisione` (revisione periodica di sintesi — il livello che tiene insieme tutto).

### Architettura

Le skill non sono isolate: formano un sistema dove le vendite generano eventi fiscali coordinabili e le due skill previdenziali condividono reference.

```
        ┌─────────────────────────────────────────────────┐
        │          it-pianificazione-obiettivi             │  ← A MONTE: dagli obiettivi
        │   (obiettivi → allocazione-target + glide path)  │     all'allocazione-target
        └────────────────────────┬────────────────────────┘
                                 │ definisce l'allocazione-target
                                 ▼
                    ┌─────────────────────┐
                    │  it-tax-optimization │  ← gestisce lo zainetto fiscale
                    │  (minus/plus, 4 anni)│     (minus pregresse, scadenze)
                    └──────────┬──────────┘
                               │ lo zainetto in scadenza
                               │ è la leva di coordinamento
                    ┌──────────┴──────────┐
                    │     it-rebalance     │  ← mantiene l'allocazione-target,
                    │  (drift, leve, PMC)  │     esegue il glide path nel tempo
                    └──────────┬──────────┘
                               │ le scelte di vendita
                               │ cambiano il reddito
        ┌──────────────────────┴──────────────────────────┐
        │   it-pianificazione    it-pianificazione-autonomi │
        │   (dipendenti, IRPEF,  (autonomi, Gestione        │
        │    TFR, deduzione)      Separata 26,07%, no TFR,   │
        │                         fondo NON deducibile)      │
        │   condividono: previdenza-complementare.md,        │
        │                proiezione-tenore-vita.md           │
        └────────────────────────────────────────────────┘
```

Il flusso end-to-end: `it-pianificazione-obiettivi` definisce obiettivi e allocazioni → l'obiettivo pensione passa a `it-pianificazione`/`it-pianificazione-autonomi` → `it-rebalance` mantiene le allocazioni ed esegue il glide path → `it-tax-optimization` ottimizza la fiscalità delle vendite. Le due skill previdenziali sono gemelle ma con regimi opposti: il dipendente deduce il fondo pensione dall'IRPEF; il forfettario, tassato con imposta sostitutiva, NON lo deduce.

## Test

La suite di test protegge la meccanica di calcolo di tutti gli script:

```bash
python tests/run_tests.py
```

La suite conta 132 test (il numero è l'unico nel README e un test di igiene lo confronta con i decoratori `@test` del runner) e gira in meno di un minuto, con le dipendenze dei Prerequisiti e, per i test che ricalcolano gli Excel, LibreOffice. Coprono: igiene del repo e della CI (manifest, pipe nei workflow, disclaimer nei comandi, valori normativi superati), compilazione, parser previdenziali su fixture sintetiche, valori chiusi (proiezione INPS, netto pensione, detrazione pensionati nell'Excel), invarianti di allocatore, Monte Carlo e bootstrap, gli Excel ricalcolati in locale italiano (nessuna cella in errore, cache aggiornate), le regressioni dei bug trovati con l'uso e con l'audit, e la freshness dei dati normativi. Diverse regressioni sono state validate per mutazione: rompendo deliberatamente il codice, i test falliscono.

### Copertura degli strumenti

Per ogni strumento del plugin, i test che lo esercitano (contati dal runner: quelli che nominano il file, direttamente o tramite un helper o una costante; i tre test che ricalcolano tutti gli Excel con LibreOffice e quelli sui testi delle skill non sono attribuiti). La tabella va rigenerata quando cambiano i test, e un test di igiene la confronta con il runner:

<!-- generata con: python tests/run_tests.py --tabella-test -->
| Strumento | Test che lo esercitano |
|---|---|
| `it-pianificazione/assets/importa-previdenza.py` | 13: T12 fixture realistiche; T9 catena --json → --from; T9 formati; T9 interfaccia ×2; freshness fiscale; importa-previdenza ×5 … |
| `it-pianificazione/assets/montecarlo-pensione.py` | 9: T12 --json previdenziali; T9 catena --json → --from; T9 formati; T9 interfaccia ×2; montecarlo-pensione; pensione … |
| `it-pianificazione/assets/motore_bootstrap.py` | 10: T12 rami avanzati; T9 formati; T9 lettore unico del pianificatore; motore bootstrap; obiettivi ×4; serie storica … |
| `it-pianificazione/assets/netto-pensione.py` | 18: T12 --json previdenziali; T9 catena --json → --from; T9 formati; T9 interfaccia ×2; coerenza tra skill; freshness fiscale … |
| `it-pianificazione/assets/ponte-pensione.py` | 11: T12 --json previdenziali; T9 catena --json → --from; T9 formati; T9 interfaccia ×2; freshness fiscale; ponte-pensione ×2 … |
| `it-pianificazione/assets/proiezione-inps.py` | 15: T12 rami avanzati; T9 catena --json → --from; T9 formati; T9 interfaccia ×2; coerenza tra skill; freshness fiscale … |
| `it-pianificazione/assets/proiezione-pensione.xlsx` | 11: T12 Excel; coerenza tra skill; proiezione-pensione-autonomi.xlsx; proiezione-pensione.xlsx ×8 |
| `it-pianificazione/assets/rendimenti-storici.csv` | 7: obiettivi ×2; pensione; ponte-pensione; serie storica ×2; sincronia |
| `it-pianificazione-autonomi/assets/proiezione-pensione-autonomi.xlsx` | 6: T12 Excel; coerenza tra skill; proiezione-pensione-autonomi.xlsx ×4 |
| `it-pianificazione-obiettivi/assets/allocatore-capitale.py` | 8: T9 formati; T9 interfaccia ×2; T9 lettore unico del pianificatore; allocatore-capitale; glidepath e Monte Carlo; obiettivi ×2 |
| `it-pianificazione-obiettivi/assets/asset-location-optimizer.py` | 9: T9 formati; T9 interfaccia ×2; T9 lettore unico del pianificatore; asset-location; obiettivi ×3; smoke |
| `it-pianificazione-obiettivi/assets/decumulo-obiettivi.py` | 9: T12 rami avanzati; T9 formati; T9 interfaccia ×2; decumulo-obiettivi; obiettivi; serie storica ×2 … |
| `it-pianificazione-obiettivi/assets/glidepath-obiettivi.py` | 11: T12 rami avanzati; T9 --json di glide path e Monte Carlo degli obiettivi; T9 formati; T9 interfaccia ×2; T9 lettore unico del pianificatore; glidepath … |
| `it-pianificazione-obiettivi/assets/montecarlo-obiettivi.py` | 15: T9 --json di glide path e Monte Carlo degli obiettivi; T9 formati; T9 interfaccia ×2; T9 lettore unico del pianificatore; glidepath e Monte Carlo; montecarlo-obiettivi ×4 … |
| `it-pianificazione-obiettivi/assets/pianificatore-obiettivi.xlsx` | 17: T12 Excel ×2; T9 interfaccia; T9 lettore unico del pianificatore; allocatore-capitale; asset-location; glidepath … |
| `it-pianificazione-obiettivi/assets/rendimenti-storici.csv` | 7: obiettivi ×2; pensione; ponte-pensione; serie storica ×2; sincronia |
| `it-rebalance/assets/ribilanciamento-multibroker.py` | 19: T1; T7 ribilanciamento ×10; T9 formati ×2; T9 input esterno; T9 interfaccia ×2; T9 vocabolario … |
| `it-revisione/assets/cruscotto-patrimoniale.xlsx` | 6: T12 Excel ×2; bande di ribilanciamento; cruscotto; cruscotto TWR; scadenze di fine anno |
| `it-revisione/assets/genera-ips.py` | 9: T9 formati; T9 input esterno; T9 interfaccia ×2; freshness fiscale; genera-ips ×2; runner … |
| `it-revisione/assets/investment-policy-statement.xlsx` | 3: T12 Excel; bande di ribilanciamento; scadenze di fine anno |
| `it-revisione/assets/tracker-secchielli.xlsx` | 4: T12 Excel ×2; bande di ribilanciamento; tracker-secchielli |
| `it-tax-optimization/assets/esempio-estratto.csv` | 2: T2 importatore ×2 |
| `it-tax-optimization/assets/esempio-zainetto.csv` | 2: T2 importatore ×2 |
| `it-tax-optimization/assets/importa-estratto-broker.py` | 13: T2 importatore ×6; T3; T9 formati; T9 input esterno; T9 interfaccia ×2; T9 vocabolario … |

### Freshness fiscale

I dati normativi (aliquote, scaglioni, coefficienti, requisiti) portano il marcatore `Verificato: AAAA-MM` e il test di freshness li considera **scaduti oltre i 12 mesi** (l'elenco `OBBLIGATI_FRESHNESS` in `tests/run_tests.py` fissa i file che devono portarlo: se uno ne è privo il test fallisce): le leggi di bilancio cambiano i numeri ogni anno, quindi il plugin "scade" per design finché non si riverifica alle fonti. Quel test non gira nella CI delle pull request (una scadenza normativa non deve bloccare un fix sul ribilanciamento) ma in un workflow dedicato, `.github/workflows/freshness.yml`, il primo di ogni mese: se fallisce apre una issue etichettata `freshness` con i file da riverificare, e la commenta ai run successivi finché resta aperta. Nota: GitHub esegue i workflow schedulati solo dal branch di default, che qui è `develop`: il cron controlla quindi i marcatori della versione in sviluppo. In locale: `python tests/run_tests.py --only freshness`.

**Stato dei dati normativi.** `python tests/run_tests.py --tabella-freshness` stampa, per ogni file, la verifica più vecchia e il mese fino a cui vale. La tabella va rigenerata a ogni release:

<!-- generata con: python tests/run_tests.py --tabella-freshness -->
| File | Verificato | Valido fino a |
|---|---|---|
| `it-pianificazione/assets/proiezione-inps.py` | 2026-06 | 2027-06 |
| `it-tax-optimization/references/aliquote-12-5-26.md` | 2026-06 | 2027-06 |
| `it-tax-optimization/references/etf-trap-redditi-capitale.md` | 2026-06 | 2027-06 |
| `it-tax-optimization/references/regime-dichiarativo.md` | 2026-06 | 2027-06 |
| `it-pianificazione/assets/netto-pensione.py` | 2026-07 | 2027-07 |
| `it-pianificazione/assets/ponte-pensione.py` | 2026-07 | 2027-07 |
| `it-pianificazione-autonomi/references/casse-professionali.md` | 2026-10 | 2027-10 |
| `it-pianificazione-autonomi/references/fiscalita-forfettario.md` | 2026-10 | 2027-10 |
| `it-pianificazione-autonomi/references/previdenza-gestione-separata.md` | 2026-10 | 2027-10 |
| `it-pianificazione-obiettivi/references/asset-location.md` | 2026-10 | 2027-10 |
| `it-pianificazione/SKILL.md` | 2026-10 | 2027-10 |
| `it-pianificazione/assets/importa-previdenza.py` | 2026-10 | 2027-10 |
| `it-pianificazione/references/previdenza-complementare.md` | 2026-10 | 2027-10 |
| `it-pianificazione/references/previdenza-obbligatoria.md` | 2026-10 | 2027-10 |
| `it-rebalance/SKILL.md` | 2026-10 | 2027-10 |
| `it-revisione/assets/genera-ips.py` | 2026-10 | 2027-10 |
| `it-tax-optimization/SKILL.md` | 2026-10 | 2027-10 |
| `it-tax-optimization/references/criptovalute-avanzate.md` | 2026-10 | 2027-10 |
| `it-tax-optimization/references/criptovalute-casi-speciali.md` | 2026-10 | 2027-10 |
| `it-tax-optimization/references/criptovalute.md` | 2026-10 | 2027-10 |
| `it-tax-optimization/references/dividendi-esteri.md` | 2026-10 | 2027-10 |
| `it-tax-optimization/references/import-dati-broker.md` | 2026-10 | 2027-10 |
| `it-tax-optimization/references/mappa-nuovo-tuir.md` | 2026-10 | 2027-10 |
| `it-tax-optimization/references/multi-intermediario.md` | 2026-10 | 2027-10 |
| `it-tax-optimization/references/successione-donazione.md` | 2026-10 | 2027-10 |

**Calendario dei parametri da riverificare** (stato a ottobre 2026):

| Quando | Cosa | Dove nel plugin |
|---|---|---|
| dicembre 2026 | Legge di bilancio 2027: IRPEF, plafond del fondo pensione, cripto, bollo, Tobin tax | SKILL.md e reference di it-tax-optimization, it-pianificazione, it-rebalance; `netto-pensione.py` |
| entro fine 2026 | Decreto sui coefficienti di trasformazione 2027-2028 (il precedente è del 20/11/2024) | `previdenza-obbligatoria.md`, foglio Coefficienti di `proiezione-pensione.xlsx`, `proiezione-inps.py` |
| 1° gennaio 2027 | Nuovi testi unici (TUIR D.Lgs. 117/2026 e collegati): cambiano gli articoli citati. Le doppie citazioni ci sono già, verificate su Normattiva il 22/10/2026; restano due punti aperti nella mappa (rinvii del DM 21/02/2013, probabile refuso dell'art. 306 c. 6) | `it-tax-optimization/references/mappa-nuovo-tuir.md` |
| gennaio 2027 | Aggiornamento annuale della serie Damodaran e della CPI USA di dicembre 2026 (BLS, colonna inflazione) | `rendimenti-storici.csv` (due copie identiche) |
| gennaio-febbraio 2027 | Circolari INPS su massimale, minimale e prima fascia 2027; aliquote della Gestione Separata | it-pianificazione, it-pianificazione-autonomi |
| 2027-2028 | Requisiti di pensione già noti (Circ. INPS 28/2026), da applicare alla data | `previdenza-obbligatoria.md`, `previdenza-gestione-separata.md` |
| giugno-luglio 2027 | Scadono i marcatori di giugno-luglio 2026: suite completa e workflow di release falliscono finché non si riverifica | tabella sopra |
| ottobre 2027 | Scadono i marcatori di ottobre 2026 | tabella sopra |

### Changelog

La storia delle versioni del plugin e delle singole skill è in [CHANGELOG.md](CHANGELOG.md), dalla più recente; le modifiche già su `develop` e non ancora rilasciate stanno nella sezione «Non rilasciato».

### Le skill e le loro versioni

Ogni skill ha una versione propria, nel campo `metadata.version` del frontmatter di `SKILL.md` (un test la confronta con questa tabella):

| # | Skill upstream | Skill fork | Stato |
|---|---|---|---|
| 1 | `tax-loss-harvesting` | `it-tax-optimization` | ✅ v0.11 (minus/plus, multi-broker, dichiarativo RT/RW/IVAFE, Tobin tax 2026, cripto: base + avanzata + casi speciali) + importatore estratti broker |
| 2 | `financial-plan` | `it-pianificazione` | ✅ v0.12 (pensione dipendenti, importatore estratto INPS + fondo, proiezione INPS parametrica con sensibilità, Monte Carlo tasso sostituzione) |
| 2b | `financial-plan` | `it-pianificazione-autonomi` | ✅ v0.4 (pensione autonomi/forfettari, casse professionali, Excel) |
| 2c | `financial-plan` + `investment-proposal` | `it-pianificazione-obiettivi` | ✅ v0.20 (goals-based, allocatore di capitale con split + 6 profili, Monte Carlo onesto + leva di rischio, glide path, asset location, decumulo) |
| 3 | `portfolio-rebalance` | `it-rebalance` | ✅ v0.7 (tax-aware con versamenti, aliquota per posizione e rientro misto, multi-broker, bande 5/25, prelievo in decumulo, sequenza di liquidazione, ordini CSV) |
| 4 | `client-review` + `client-report` + `investment-proposal` (IPS) | `it-revisione` | ✅ v0.7 (revisione di sintesi, template report, tracker azioni, **generatore IPS in Word**, Excel, TWR) |

Le sei skill attive formano un sistema coordinato attorno a un flusso end-to-end: `it-pianificazione-obiettivi` definisce gli obiettivi e le allocazioni (a monte), le due skill previdenziali coprono il secchiello pensione, `it-rebalance` mantiene le allocazioni nel tempo, `it-tax-optimization` ottimizza la fiscalità delle vendite, e `it-revisione` è il **livello di sintesi** che una volta l'anno tiene insieme tutto in un quadro unico con azioni prioritizzate. Vedi la sezione "Architettura" sotto. Note: il goals-based, che nell'upstream è spezzato tra `financial-plan` (modellazione obiettivi) e `investment-proposal` (allocazione/IPS), nel fork è unificato in `it-pianificazione-obiettivi` con postura personale/educativa; e le skill upstream rivolte al consulente (`client-review`, `client-report`, in parte `investment-proposal`) sono riformulate per chi gestisce i propri soldi nell'unica `it-revisione`.

## Installazione

### Prerequisiti

Python 3.11 o successivo (la CI prova 3.11 e 3.14) con le dipendenze degli script: `pip install "numpy>=1.26" "openpyxl>=3.1" "python-docx>=1.1"` (oppure `pip install -r tests/requirements.txt`, lo stesso file usato dalla CI).

### Claude Code

Il repository include `.claude-plugin/marketplace.json`, quindi è esso stesso un marketplace installabile. Tre vie (procedura verificata con la prova di installazione locale del 21/10/2026, su un profilo Claude Code vuoto):

```bash
# A) Uso quotidiano — da GitHub (consigliata: si aggiorna dal marketplace)
#    dentro una sessione Claude Code:
/plugin marketplace add eugeniorende/wealth-management-it
/plugin install wealth-management-it@wm-it

# B) Solo locale — senza GitHub (path assoluto della directory del plugin)
/plugin marketplace add /percorso/assoluto/wealth-management-it
/plugin install wealth-management-it@wm-it

# C) Sviluppo — carica il plugin senza installarlo (sessione usa-e-getta)
claude --plugin-dir /percorso/assoluto/wealth-management-it
```

Da una shell, senza aprire una sessione, gli stessi passi sono `claude plugin marketplace add eugeniorende/wealth-management-it` e `claude plugin install wealth-management-it@wm-it`. L'installazione vale per l'utente in tutti i progetti; con `--scope project` vale per chi lavora nel repository corrente (la voce va in `.claude/settings.json`), con `--scope local` solo per te e solo lì.

**Aggiornamenti.** Con la via A l'installazione copia il plugin nella cache di Claude Code (`~/.claude/plugins/cache/`): non modificare quella copia, che a ogni aggiornamento si sostituisce. Con la via B il plugin si legge direttamente dalla cartella indicata. Il manifest fissa la versione, quindi un'installazione resta sulla sua versione finché non esce una release. Per i marketplace di terze parti come questo l'aggiornamento automatico è spento di default. Due modi per aggiornare:

```bash
# a mano, da una shell (dentro una sessione: /plugin → Installed → wealth-management-it → Update now)
claude plugin marketplace update wm-it
claude plugin update wealth-management-it@wm-it

# in automatico all'avvio delle sessioni: /plugin → Marketplaces → wm-it → Enable auto-update
```

Dopo un aggiornamento, `/reload-plugins` lo carica nella sessione aperta; le sessioni nuove lo caricano da sole. Con la via C non c'è nulla da aggiornare: il plugin si legge dalla cartella a ogni avvio. Le novità di ogni versione sono in [CHANGELOG.md](CHANGELOG.md).

### Cartella di lavoro (importante)

Il plugin fornisce skill e script; i **tuoi dati vivono altrove**. Crea una cartella dedicata al piano (es. `~/piano-finanziario/`) e lavora sempre da lì: metti lì i file reali (estratto conto INPS, storico del fondo, CSV dei broker), **copia** lì gli Excel da compilare (`pianificatore-obiettivi.xlsx`, `tracker-secchielli.xlsx`, `cruscotto-patrimoniale.xlsx`, `investment-policy-statement.xlsx`, `proiezione-pensione.xlsx` o `proiezione-pensione-autonomi.xlsx` — mai editare quelli dentro il plugin), e lì finiranno gli output degli script (JSON della pipeline, CSV degli ordini, l'IPS generato). Il plugin resta immutabile e aggiornabile; la cartella di lavoro è la tua. In Claude Code la si indica al plugin come opzione `cartella_lavoro`: all'installazione con `claude plugin install wealth-management-it@wm-it --config cartella_lavoro=/percorso/della/cartella`, oppure dopo con `/plugin configure wealth-management-it@wm-it` in una sessione. Se resta vuota, le skill la chiedono.

### Dove vanno i tuoi dati

Gli script del plugin girano **in locale** e non fanno chiamate di rete: leggono i file che indichi e scrivono gli output (JSON, CSV degli ordini, IPS in Word) nella cartella da cui li lanci. Però tutto ciò che scrivi in chat, che Claude legge dai tuoi file e che gli script stampano **entra nel contesto del modello** e nei transcript della sessione: in Claude Code i transcript restano sul tuo computer (`~/.claude/projects/`), in Cowork e su claude.ai sono gestiti secondo le impostazioni del tuo account Anthropic.

Cosa conviene sapere:
- `importa-previdenza.py` legge l'estratto conto INPS e il prospetto del fondo pensione. Di default stampa intestatario e data di nascita, da cui calcola l'età; con `--anonimo` li omette e stampa l'età arrotondata all'anno. Le retribuzioni le stampa aggregate per anno, senza i datori di lavoro;
- gli estratti dei broker contengono posizioni e importi; prima di passarli, togli quello che al calcolo non serve: intestatario, codice fiscale, IBAN, numero di dossier;
- per i calcoli bastano età, importi e date: nomi e identificativi non servono a nessuno strumento del plugin.

### Verifica

Dal repository: `python tests/run_tests.py` (tutta la suite in meno di un minuto, richiede le dipendenze dei Prerequisiti; il numero dei test è nella sezione «Test»). Tre test ricalcolano gli Excel con LibreOffice headless in locale italiano (`scripts/ricalcola-excel.py`): verificano che nessuna cella vada in errore e che le cache salvate nei file coincidano col ricalcolo. Senza LibreOffice risultano saltati; nella CI è installato e obbligatorio (`RICHIEDI_LIBREOFFICE=1`). Dopo aver modificato un Excel, `python scripts/ricalcola-excel.py FILE --in-place` ne aggiorna le cache. `--only NOME` e `--skip NOME` filtrano i test per sottostringa del nome. La stessa suite gira come GitHub Action (`.github/workflows/tests.yml`) a ogni push su `main`/`develop` e su ogni pull request, escluso il test di freshness fiscale (vedi sotto): il badge in cima al README ne riporta lo stato. Un job su `windows-latest` (Python 3.11, senza LibreOffice) verifica che script e suite girino anche lì.

### Cowork

Settings → Plugins → Add plugin → Upload a zip. Lo zip pronto (`wealth-management-it-vX.Y.Z.zip`) è allegato a ogni [GitHub Release](https://github.com/eugeniorende/wealth-management-it/releases); in alternativa si costruisce dal repository con `python scripts/pacchetto.py` (finisce in `dist/`). Contiene manifest, comandi, skill, README, CHANGELOG, LICENSE e NOTICE, sotto la cartella `wealth-management-it/`; fuori restano test, workflow e script di build.

## Uso

Comandi espliciti: sono scorciatoie che caricano la skill corrispondente, con gli argomenti dati dopo il comando (es. `/minusvalenze estratto.csv`). Se un altro plugin usa lo stesso nome, il comando si scrive con il prefisso del plugin, es. `/wealth-management-it:minusvalenze`.

```
/obiettivi         → it-pianificazione-obiettivi (pianificazione goals-based multi-obiettivo)
/minusvalenze      → it-tax-optimization (ottimizzazione minus/plus, zainetto)
/pensione          → it-pianificazione (pensione dipendenti: INPS + complementare + TFR)
/pensione-autonomi → it-pianificazione-autonomi (pensione autonomi/forfettari: Gestione Separata)
/ribilancia        → it-rebalance (ribilanciamento tax-aware del portafoglio)
/revisione         → it-revisione (revisione periodica: stato, scostamenti, azioni)
```

Trigger automatico: ogni skill si attiva sui propri argomenti. `it-pianificazione-obiettivi` su obiettivi/pianificare investimenti/fondo emergenza/quanto risparmiare; `it-tax-optimization` su minusvalenze/plusvalenze/zainetto/Tobin tax; `it-pianificazione` su pensione/fondo pensione/TFR per dipendenti; `it-pianificazione-autonomi` su pensione/Gestione Separata/forfettario per P.IVA; `it-rebalance` su ribilanciamento/drift/allocazione target.

### Convenzioni degli script

Tutti i 13 script del plugin seguono la stessa interfaccia, verificata dalla suite:

- `--help` descrive argomenti e opzioni; un argomento o un flag non riconosciuto ferma lo script con l'usage.
- Codici d'uscita: **0** riuscito; **1** errore nei dati o nei parametri (file mancante o illeggibile, valori incoerenti, costante `--set` sconosciuta), con un messaggio che inizia per `ERRORE:` su stderr; **2** riga di comando non riconosciuta.
- Output in UTF-8 su qualunque console, anche Windows in cp1252: i simboli `€`, `→` e `≈` non fanno crashare lo script.
- Numeri in formato italiano: punto per le migliaia e virgola per i decimali (`€ 36.000`, `51,4%`). Le uniche eccezioni sono i «parametri pronti» di `importa-previdenza.py`, scritti come letterali Python (`36_000`) perché vanno incollati negli altri script.
- `--set NOME=VALORE` (ripetibile) sovrascrive le costanti in testa agli script di `it-pianificazione` e `it-pianificazione-obiettivi`; `--help` ne elenca i nomi. `--json FILE` scrive i risultati chiave in JSON dove indicato nelle skill; nella catena previdenziale `--from FILE` (ripetibile) legge quel JSON a valle, con la precedenza `--set` > `--from` > default.
- I CSV degli ordini del ribilanciamento si aprono in Excel italiano con un doppio clic: separatore `;`, virgola decimale, UTF-8 con BOM.

### Input richiesto

L'utente deve fornire:

1. **Snapshot portafoglio** in CSV o testo (l'estratto CSV del broker si legge con `skills/it-tax-optimization/assets/importa-estratto-broker.py`, che classifica le posizioni, esclude le minus scadute e incrocia lo zainetto broker per broker; accetta i formati di export dei broker, con sinonimi delle colonne e numeri italiani o inglesi). Schema di riferimento, `broker` compreso perché lo zainetto è per intermediario:
   ```
   broker,isin,descrizione,quantita,pmc,prezzo_corrente,categoria_fiscale
   Fineco,IE00B4L5Y983,iShares Core MSCI World,100,75.20,89.50,reddito_capitale
   Fineco,IT0003132476,ENI,500,12.40,14.80,reddito_diverso
   ```

2. **Stato zainetto fiscale** (scaricabile da quasi tutti i broker italiani come "rendiconto fiscale annuale"), per broker:
   ```
   broker,anno_realizzo,importo_residuo,aliquota
   Fineco,2022,4500,26
   Fineco,2023,1200,26
   ```

3. **Intermediario** (per cut-off operativi specifici).

### Output

Report markdown in tre sezioni:
1. **Stato attuale** — tabella portafoglio + zainetto
2. **Opportunità identificate** — trade candidati con razionale fiscale
3. **Calendario d'azione** — scadenze ordinate cronologicamente

Più disclaimer obbligatorio.

## Cosa il plugin NON fa

- Il motore di ottimizzazione e ribilanciamento assume il regime amministrato: regime dichiarativo e cripto sono coperti come principi e adempimenti (quadri RT, RW e IVAFE, ravvedimento), senza un importatore dedicato
- Non gestisce immobili, partecipazioni qualificate e derivati OTC
- Non copre dipendenti pubblici né artigiani e commercianti iscritti alle gestioni IVS INPS
- Non compila il Modello Redditi e non sostituisce un commercialista o un consulente abilitato
- Non dà consigli su quale azione o ETF comprare per ragioni di rendimento
- Non si connette ai broker via API: un MCP server sui broker è stato valutato ed escluso (le API non espongono lo zainetto e richiederebbero credenziali); i dati si forniscono con gli estratti CSV

## Glossario

I termini usati allo stesso modo in skill, script, Excel e README. Gli script accettano i sinonimi indicati e li normalizzano.

| Termine | Significato | Sinonimi accettati |
|---|---|---|
| **Zainetto fiscale** | Le minusvalenze pregresse che l'intermediario custodisce in regime amministrato, compensabili con le plus dei redditi diversi entro 4 anni; è per broker. In euro al 26% («26%-equivalenti»): una minus al 12,5% vale il 48,08% | «minus pregresse», «credito fiscale» |
| **Categoria fiscale** | La natura del reddito di una posizione: `reddito_diverso` (azioni, obbligazioni, certificates, ETC: plus e minus compensabili tra loro), `reddito_capitale` (ETF e fondi: plus mai compensabile, minus reddito diverso), `reddito_capitale_irpef` (fondi non armonizzati fuori UE/SEE: plus a IRPEF), `da_classificare` | `tipo_fiscale`, `tipo`; forme brevi `diverso`, `capitale` |
| **PMC** | Prezzo medio di carico: in amministrato è la base fiscale (costo medio ponderato), non si sceglie il lotto | «prezzo di carico», `costo` |
| **Asset class** | La classe di un ribilanciamento (azionario, obbligazionario, monetario…): la assegna l'utente, non è la categoria fiscale | `classe` |
| **Secchiello** | Il capitale destinato a un obiettivo, con il suo profilo e il suo glide path (goals-based) | «bucket» |
| **Profilo** | Un'allocazione tipo del pianificatore (Preservazione … Azionario totale) con rendimento atteso, volatilità e quota azionaria | — |
| **Glide path** | Il calendario con cui la quota azionaria di un obiettivo terminante scende verso la scadenza, negli ultimi anni della finestra di de-risking | «de-risking» |
| **Drift e banda 5/25** | Lo scostamento di una classe dal peso target; si ribilancia oltre la banda, la minore tra 5 punti assoluti e il 25% del target | — |
| **Regime amministrato / dichiarativo** | Chi calcola e versa l'imposta: l'intermediario (amministrato, il perimetro del motore) oppure il contribuente in dichiarazione (dichiarativo, solo principi) | — |
| **Tasso di sostituzione** | Pensione / ultimo reddito, lordo o netto; il netto misura il tenore di vita | — |

## Differenza chiave: zainetto fiscale

Il concetto di "zainetto fiscale" è centrale e non ha equivalente diretto USA. È il registro di minusvalenze pregresse custodito dall'intermediario in regime amministrato, con scadenza a 4 anni e regole asimmetriche di compensazione (vedi `skills/it-tax-optimization/references/etf-trap-redditi-capitale.md`). Chiudendo il rapporto non si perde: l'intermediario certifica le minus residue, che si usano su un altro rapporto con gli stessi intestatari o in dichiarazione fino alla scadenza originaria (art. 6 c. 5 D.Lgs. 461/97 → art. 306 c. 6 TU 2027, vedi `multi-intermediario.md`).

## Contribuire

Le regole fiscali italiane cambiano a ogni legge di bilancio: il calendario dei parametri da riverificare e lo stato dei marcatori sono nella sezione «Freshness fiscale». Quando la normativa cambia:
1. verificare il dato su **fonte primaria** (Normattiva, Gazzetta Ufficiale, circolari INPS, Agenzia delle Entrate, COVIP); le fonti secondarie servono a trovarla, non a confermarlo;
2. aggiornarlo in **tutte le copie** (`grep -rn` su `skills/`, `commands/` e README): le skill sono autosufficienti e duplicano alcuni dati;
3. aggiornare il marcatore della parte verificata nel formato esatto `Verificato: AAAA-MM` (il test lo cerca così), senza ringiovanire la data di un file verificato solo in parte;
4. eseguire `python tests/run_tests.py` e, se il dato compare in un Excel, `python scripts/ricalcola-excel.py FILE --in-place`.

## Release

Il repository segue il gitflow: le feature chiudono su `develop`, su `main` arrivano solo i release branch. Per pubblicare una versione:

1. Da `develop`, aprire un release branch e allineare la versione in `.claude-plugin/plugin.json` e `marketplace.json` (il test di igiene verifica che i due manifest coincidano, lo script di packaging che il tag coincida con `plugin.json`); in `CHANGELOG.md` la sezione «Non rilasciato» diventa «vX.Y.Z (data)», e un test verifica che la voce della versione del manifest ci sia.
2. Pull request del release branch su `main`; la CI (`tests` + `validate`) deve essere verde.
3. Dopo il merge, tag `vX.Y.Z` su `main` e push del tag. Il workflow `release.yml` rifiuta un tag diverso dalla versione del manifest, esegue la suite **completa, freshness inclusa** (non si rilascia con dati normativi scaduti), costruisce lo zip e crea la GitHub Release con le note generate dai commit.
4. Merge back di `main` su `develop`.

Il workflow si può avviare a mano senza tag (Actions → release → Run workflow): costruisce lo zip come artifact del run senza creare la release, utile per collaudarlo.

## Licenza

Apache-2.0: il testo è in [LICENSE](LICENSE), l'attribuzione all'upstream e le modifiche sono in [NOTICE](NOTICE). Entrambi i file entrano nello zip di release. Il progetto è nato come fork del plugin `wealth-management` di anthropics/financial-services (commit `ef165e4160`), ma skill, comandi, script ed Excel sono stati riscritti da zero per la fiscalità italiana: il confronto con l'upstream non trova righe di testo in comune.

## Disclaimer (di nuovo, perché conta)

Questo plugin produce **bozze di analisi fiscale personale**. Non è consulenza professionale. L'autore e gli eventuali contributor non si assumono responsabilità per decisioni operative basate sull'output. Verificare sempre con il proprio commercialista e con il portale dell'intermediario.
