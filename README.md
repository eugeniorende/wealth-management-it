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

> **Errori noti.** L'audit del 20/10/2026 ha confermato 65 problemi, alcuni dei quali producevano numeri sbagliati sui percorsi principali. La 0.10.0 chiude l'ondata 0 e i temi T1-T8, T10, T11 e parte di T13: tra gli altri l'importatore broker (F001), il ribilanciamento con i versamenti (F004), il plafond del fondo pensione nell'Excel (F007), la certificazione delle minus alla chiusura del rapporto (F011) e il costo medio in amministrato (F012). Restano aperti l'interfaccia comune degli script (T9), i test strutturali sugli Excel (T12), il riscatto della laurea e i casi del freelance (T13), la documentazione e il packaging (T14), e le corrispondenze del 2027 ancora «da verificare» nella mappa dei testi unici. Il piano è in [ROADMAP.md](ROADMAP.md); il dettaglio è in [docs/audit-2026-10.md](docs/audit-2026-10.md).

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

La suite di smoke test protegge la meccanica di calcolo di tutti gli script:

```bash
python tests/run_tests.py
```

107 test in meno di un minuto, con le dipendenze dei Prerequisiti e, per i test che ricalcolano gli Excel, LibreOffice. Coprono: igiene del repo e della CI (manifest, pipe nei workflow, disclaimer nei comandi, valori normativi superati), compilazione, parser previdenziali su fixture sintetiche, valori chiusi (proiezione INPS, netto pensione, detrazione pensionati nell'Excel), invarianti di allocatore, Monte Carlo e bootstrap, gli Excel ricalcolati in locale italiano (nessuna cella in errore, cache aggiornate), le regressioni dei bug trovati con l'uso e con l'audit, e la freshness dei dati normativi. Diverse regressioni sono state validate per mutazione: rompendo deliberatamente il codice, i test falliscono.

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

**v0.10.0** (corrente):
- **Freshness**: il workflow mensile gira con `shell: bash` (pipefail). Prima l'exit code era quello di `tee`, quindi lo step restava verde anche con i dati scaduti e la issue non si apriva mai. Nuovo test di igiene sulle pipe nei workflow.
- **Ricalcolo degli Excel in CI**: `scripts/ricalcola-excel.py` ricalcola gli xlsx con LibreOffice headless in locale it-IT e segnala le celle in errore. Tre test nuovi: ricalcolo forzato e locale italiano (validati per mutazione), nessuna cella in errore, cache consegnate uguali al ricalcolo. Il runner distingue i test saltati.
- **Bug trovati dal ricalcolo in italiano**: in `proiezione-pensione.xlsx` le otto ipotesi di `Scenari!B5:B8` e `D5:D8` erano testo ("0.022"). Con il punto come separatore delle migliaia diventavano 22 e la pensione degli scenari usciva a −1,7·10¹⁹; ora sono numeri. Nel cruscotto e nell'IPS, `TEXT(x;"0.0%")` dipendeva dal locale e perdeva il decimale; ora è `FIXED(x*100;1)&"%"`, quindi "10,0%" in italiano.

- **Quick win sugli script** (PR #8): la serie storica si trova anche lanciando ponte e Monte Carlo pensione dalla cartella di lavoro; rendimento zero nel ponte senza divisione per zero; la leva di rischio è un'OPZIONE solo per gli obiettivi desiderabili oltre la finestra di de-risking (prima proponeva ~95% azionario per l'anticipo casa a 6 anni); il bootstrap del decumulo campiona anche l'ultimo anno; l'IPS somma tutte le classi azionarie e scrive il mese in italiano.
- **Disclaimer** (PR #9): ogni comando chiede in fondo il disclaimer «non è consulenza»; i CSV degli ordini si chiudono con una riga NOTA e lo stdout del ribilanciamento lo ripete.
- **Quick win fiscali** (PR #10): quadro RW dovuto per titoli e cripto esteri senza soglia (i €15.000 valgono solo per i conti); plus di ETF e fondi non armonizzati come redditi di capitale, mai compensabili; scarto di emissione e cedole come redditi di capitale; polizze vita esenti IRPEF solo per la componente demografica; cripto con soglie penali, doppia tabella del ravvedimento, DAC8 e regime amministrato dal 2023.
- **Previdenza dei dipendenti** (PR #11): il contributo del datore conta nel plafond di €5.300; detrazione pensionati dell'Excel secondo l'art. 13 c. 3 TUIR (pensione netta d'esempio da €30.833 a €29.263); massimale €122.295 e prima fascia €56.224; Quota 103 e Opzione donna solo per requisiti già maturati, anticipata contributiva a 64 anni; trasferimento con il contributo del datore dal 31/10/2026 e adesione automatica dal 1/7/2026. Il capitale del fondo resta al 50%. Tolti i dati personali dell'autore dalle reference.
- **Autonomi e revisione** (PR #12): artigiani e commercianti dichiarati fuori perimetro; CIPAG 20% + 5% (anche verso la PA) ed ENPAM con Quota B al 19,5%; requisiti 2026 nella Gestione Separata; la comunicazione al fondo dei contributi non dedotti entra in tutte le scadenze di fine anno; nel cruscotto il TWR non dà più −100% sulle righe non compilate.
- **Freshness e documentazione** (PR #13): l'elenco `OBBLIGATI_FRESHNESS` rende obbligatorio il marcatore su 19 file normativi. I quattro che ne erano privi sono stati verificati alle fonti: in `criptovalute-casi-speciali.md` corretti gli importi del regime neo-residenti (€300.000 dal 2026), l'IVA del mining (fuori campo, non pro-rata), la localizzazione delle cripto (criteri della circ. 30/E/2023) e la riforma delle successioni (in vigore dal 2025); in it-pianificazione la sterilizzazione oltre €200.000; in it-rebalance la Tobin tax (0,4% fuori mercato, 0,2% sui mercati regolamentati). README: «Cosa il plugin NON fa» riscritto, `/revisione` tra i comandi, un solo conteggio dei test.
- **Stato dei dati normativi** (PR #14): `python tests/run_tests.py --tabella-freshness` stampa per ogni file la verifica più vecchia e il mese fino a cui vale; nel README la tabella e il calendario dei parametri da riverificare nei prossimi 12 mesi.
- **CI** (PR #15, #17): action fissate per SHA, claude-code a versione fissa, matrice Python 3.11 e 3.14, versioni minime delle dipendenze. Il minimo dichiarato passa a Python 3.11.
- **Licenza** (PR #16): LICENSE e NOTICE (Apache-2.0) nel repository e nello zip di release, con l'attribuzione all'upstream fissata al commit `ef165e4160`.
- **Revisione annuale** (PR #18): nel cruscotto il foglio TWR regge fino a 120 rilevazioni e legge da solo l'ultima; la Sintesi confronta la probabilità con la soglia della priorità; Allocazione e tracker usano la regola 5/25 per classe; costi dell'anno a scopo di confronto; foglio Leggimi con i limiti.
- **Ponte pensionistico in euro di oggi**: `ponte-pensione.py` deflaziona anno per anno la serie storica (nominale in dollari) con l'inflazione USA dello stesso anno, come il decumulo degli obiettivi; prima confrontava rendimenti nominali con una spesa reale. **Output cambiati a parità di seed**: sui default la probabilità di coprire il ponte scende dal 44,0% al 21,1%, e il capitale necessario sale da €49.335 a €53.167 (85%) e da €52.750 a €58.619 (95%). Monte Carlo pensione e reference dicono che la serie è nominale in dollari e che se ne usa solo la forma.
- **Asimmetria fiscale e zainetto** (T1, PR #20): in amministrato la base di costo è il costo medio ponderato, non il LIFO, che vale solo in dichiarativo. Alla chiusura del rapporto, o alla revoca dell'amministrato, le minus si certificano e si usano su un altro rapporto con gli stessi intestatari o nel quadro RT, entro la scadenza originaria (nuovo Pattern E; corretta la formula del Pattern D). OICR non armonizzati fuori UE/SEE come reddito di capitale e categoria «da classificare»; esempio su BOT e zero coupon con lo scarto di emissione.
- **Importatore estratti broker** (T2, PR #22): un titolo non riconosciuto resta «da classificare» invece di finire tra i redditi diversi; la categoria si legge dalla descrizione, non dal prefisso ISIN (ETF USA a IRPEF, ETC fisici a reddito diverso). Il 12,5% vale anche per Bund, OAT, Treasury, Gilt, JGB e multilaterali; le altre obbligazioni estere restano al 26% con un avviso. Minus scadute dopo 4 anni escluse rispetto a `--anno`, conversione 12,5/26 nei due versi, zainetto per broker. Sugli esempi distribuiti: plus compensabili 0, zainetto 800 con `--anno 2027`.
- **Broker esteri e regime dichiarativo** (T3, PR #29): stato dei broker verificato a ottobre 2026: Interactive Brokers e Degiro in dichiarativo, Trade Republic in amministrato per i nuovi clienti dal 30/1/2025 (cripto da verificare), Scalable in amministrato su richiesta dal 1/9/2026. Il dichiarativo è trattato come principi: quadri RT, RM e RW, LIFO, cambio del giorno, imposta del quadro RT senza acconti, IVAFE, checklist degli adempimenti. Nei conti in dichiarativo plus e minus si calcolano solo sui lotti in euro; `/minusvalenze` chiede il regime di ogni broker.
- **Dividendi esteri e successioni** (T13, PR #32): due reference nuove in it-tax-optimization. `dividendi-esteri.md` dà le ritenute di sette Paesi con il prelievo totale, il 26% sul netto frontiera in amministrato e sul lordo in dichiarativo, W-8BEN e rimborsi, il credito dell'art. 165. `successione-donazione.md` dà il costo fiscale di eredi e donatari, lo zainetto che si estingue col decesso, aliquote e franchigie dopo il D.Lgs. 139/2024 e il confronto «vendo o lascio». Le richiamano it-rebalance e il bucket «Eredità» degli obiettivi.
- **Pensione pubblica dei dipendenti** (T5, PR #23): `proiezione-pensione.xlsx` è tutto in euro di oggi (PIL reale 0,5% invece dell'1,8% nominale su una RAL reale) e gli Scenari ricalcolano davvero INPS e fondo. Massimale €122.295 anche in `proiezione-inps.py` e `netto-pensione.py`; addizionali solo se c'è IRPEF; tassi di capitalizzazione ufficiali 1996-2025 in `importa-previdenza.py`, che lascia fuori dal montante le retribuzioni prima del 1996. Requisiti 2027-2028 completi (Circ. INPS 28/2026). Con la nuova stima del montante la pensione lorda sui default passa da €31.007 a €30.945.
- **Fondo pensione** (T4, PR #24): il plafond di €5.300 è condiviso tra lavoratore e datore; il foglio Complementare calcola anno per anno quota deducibile, non dedotto e spazio residuo. La tassa in uscita colpisce solo TFR conferito e contributi dedotti (art. 11 c. 6 D.Lgs. 252/2005). Si aggiungono il «Confronto TFR» in azienda contro fondo e le nuove forme di erogazione (durata definita, prelievi, frazionata). Il rendimento del comparto è reale al 2,5% (era 3,5% senza unità): l'esempio TFR con RAL 40k per 30 anni vale €40.121,51 di vantaggio.
- **Autonomi** (T6, PR #26): `proiezione-pensione-autonomi.xlsx` ha il massimale €122.295 e la rivalutazione reale allo 0,5%, come il foglio dei dipendenti. A montante va l'aliquota di computo del 25% IVS (Circ. INPS 8/2026), non il 26,07% versato, con la nuova cella Input!B16: sui default la pensione lorda passa da €14.193 a €13.661. Si aggiungono altri redditi IRPEF, spesa target, pensione netta e Scenari conservativo / base / ottimistico col gap; tabella delle casse con link ufficiale e dati 2026 riverificati.
- **Obiettivi** (T8, PR #25): il versamento dei terminanti tiene conto del glide path, con la finestra in `Parametri!B7` e il versamento in due fasi, nel pianificatore e negli script; un pianificatore senza `Parametri!B7` dà un avviso. Il rendimento del profilo è la media aritmetica annua; `rendimenti-storici.csv` è dichiarato nominale in dollari e il decumulo deflaziona anno per anno. **Output cambiati**: sui default il versamento per la casa sale da €478 a €500 e quello di lungo termine da €346 a €384; a parità di seed cambiano anche montecarlo-obiettivi e il decumulo.
- **Ribilanciamento tax-aware** (T7, PR #33): in `ribilanciamento-multibroker.py` versamenti e flussi entrano nel totale prima del drift, e le minus realizzate ricaricano lo zainetto del broker. Le minus di tutte le classi si vendono prima delle plus e i CSV le elencano per prime; la Leva 4 va per imposta per euro venduto, con l'aliquota della posizione (12,5% per i titoli di Stato, nello zainetto al 48,08%). Regola 5/25 unica e rientro misto: a target se costa zero, a metà banda se tassato, con i due costi e il residuo rinviato nel report. Una sottopesata fuori banda si riempie anche vendendo da classi in banda. Il nuovo `PRELIEVO` calcola il lordo che copre anche l'imposta, con una vendita per posizione; la modulazione per volatilità è spenta di default.
- **Privacy e plafond condiviso** (PR #27, #28, #31): con `--anonimo` `importa-previdenza.py` non stampa intestatario e data di nascita, che altrimenti entrano nel contesto del modello, ma solo `ETA_ATTUALE`. La revisione annuale chiede lo spazio deducibile residuo del fondo (€5.300 − datore − dovuto: un tetto fiscale per i volontari entro il 31/12, non un importo consigliato) e i contributi non dedotti da comunicare. Negli obiettivi SKILL.md, `asset-location.md` e `asset-location-optimizer.py` dicono che il plafond è condiviso col datore; i numeri sui default non cambiano.
- **Testi unici dal 2027** (T11, PR #34): nuova reference `mappa-nuovo-tuir.md` in it-tax-optimization con le corrispondenze tra le norme citate e i testi unici che si applicano dal 1/1/2027 (TUIR nel D.Lgs. 117/2026, GU n. 152 del 3/7/2026; amministrato negli artt. 304-307; monitoraggio, versamenti, sanzioni, tributi minori e successioni), con l'elenco di quelle ancora da verificare. Skill, reference, script ed Excel citano la norma vigente e quella dal 2027, per esempio «art. 68 c. 5 TUIR, dal 2027 art. 77 c. 6»; un test controlla ogni citazione. Nella skill fiscale la flat tax dei neo-residenti non è più ferma a €100.000.

**v0.9.6**:
- **Integrazione GitHub**: repository su `github.com/eugeniorende/wealth-management-it` con `.gitignore`, campo `repository` e `author` strutturato nel manifest (passa `claude plugin validate`), `.claude-plugin/marketplace.json` effettivamente presente, istruzioni di installazione con il repository reale. Gitflow: feature su `develop`, release su `main`.
- **GitHub Actions** (tre workflow): `tests` esegue la suite a ogni push su `main`/`develop` e su ogni PR, più il job `validate` sul manifest; `freshness` esegue il solo test di freshness fiscale il primo di ogni mese e apre una issue quando i dati normativi superano i 12 mesi, così una scadenza non blocca le PR; `release` su tag `vX.Y.Z` verifica il tag contro il manifest, esegue la suite completa (freshness inclusa) e pubblica la GitHub Release con lo zip per Cowork.
- **Runner e packaging**: `tests/run_tests.py` accetta `--only`/`--skip`; `scripts/pacchetto.py` costruisce lo zip del plugin; `tests/requirements.txt` per le dipendenze. Dependabot sulle action, badge della CI. Suite: 24 test.

**v0.9.5**:
- **Integrazione Claude Code**: aggiunto `.claude-plugin/marketplace.json` — il repository è ora un marketplace installabile (`/plugin marketplace add` + `/plugin install wealth-management-it@wm-it`). Sezione Installazione riscritta con le tre vie verificate sulla documentazione ufficiale (GitHub, marketplace locale, `--plugin-dir` per sviluppo), i prerequisiti Python espliciti, la nota sul **caching** (il plugin installato è una copia: si aggiorna dal repository, non si edita in cache) e la convenzione della **cartella di lavoro** (i dati personali e gli Excel compilati vivono fuori dal plugin). Test di igiene sulla coerenza marketplace/plugin. Suite: 22 test.

**v0.9.4**:
- **Freshness fiscale** (skill `it-pianificazione` → v0.11, `it-tax-optimization` → v0.10): i dati normativi in script e reference portano il marcatore `Verificato: AAAA-MM`; la suite fallisce oltre i 12 mesi — le leggi di bilancio cambiano i numeri ogni anno, e ora il plugin "scade" per design finché non si riverifica alle fonti.
- **Pipeline `--json <file>`**: la catena previdenziale (proiezione INPS → Monte Carlo → netto → ponte) e l'allocatore scrivono i risultati chiave anche in JSON — i numeri passano tra gli script senza travasi manuali, componibile con `--set`.
- **Guardia sulle intestazioni Excel** (`it-pianificazione-obiettivi` → v0.19): layout del pianificatore modificato → errore esplicito con colonna e intestazione attesa, invece di dati sbagliati in silenzio. Suite: 21 test.

**v0.9.3**:
- **Ponte pensionistico** (`it-pianificazione` → v0.10, `ponte-pensione.py`): il calcolo completo dell'uscita anticipata — Monte Carlo del capitale-ponte con probabilità e capitale necessario per confidenza, **RITA integrata** (requisiti e tassazione 15%→9% verificati su COVIP/Agenzia delle Entrate) con quota di montante parametrica, e i **costi permanenti** che i calcoli ingenui omettono: contributi INPS mancati, versamenti fermi e montante consumato, in euro/anno di pensione persa per sempre. Collega il secchiello "libertà finanziaria" alla domanda che lo giustifica: "posso smettere a X anni?". Suite: 18 test.

**v0.9.2**:
- **Tasso di sostituzione netto** (`it-pianificazione` → v0.9, `netto-pensione.py`): IRPEF 2026 verificata (scaglioni 23/33/43 post-L.199/2025), detrazioni art. 13 TUIR, contributi IVS, addizionali parametriche e imposta sostitutiva 15%→9% sulla rendita complementare. Confronta pensione netta / ultimo stipendio netto per più scenari di rendita: il lordo sottostima sistematicamente la copertura (caso reale: mediana 74,6% lorda → 97,5% netta; coda P10 63% → 81%).
- **Tracker dei secchielli** (`it-revisione` → v0.6, `tracker-secchielli.xlsx`): il foglio operativo del piano — posizioni assegnate ai secchielli con tendine, effettivo vs target per secchiello e aggregato, semaforo automatico sulle bande 5/25, target che segue il calendario del glide path cambiando l'anno del piano, registro versamenti. 145 formule, recalc 0 errori.
- Suite: 17 test (valori chiusi IRPEF/detrazioni/aliquota rendita; semaforo demo del tracker).

**v0.9.1**:
- **Override `--set NOME=VALORE`** (skill `it-pianificazione` → v0.8, `it-pianificazione-obiettivi` → v0.18): i sette script di scenario delle due skill accettano override delle costanti da riga di comando via `motore_bootstrap.applica_override` — niente più copie modificate a mano o via regex per cambiare parametri. Nomi inesistenti respinti, override stampati (run documentato), componibile con gli argomenti esistenti. La suite stessa ora usa `--set` al posto delle copie temporanee (15 test).

**v0.9.0**:
- **Generatore IPS** (`it-revisione` → skill v0.5, `genera-ips.py`): l'Investment Policy Statement — il deliverable finale del flusso — si genera come documento Word (python-docx) da un unico blocco dati: copertina, 12 sezioni, checklist operativa a caselle, appendice broker opzionale. Testi di policy come default sovrascrivibili; nota di rischio **calcolata** dalla quota azionaria aggregata; validazioni di coerenza (allocazione, capitali) che avvisano senza bloccare. Test dedicato nella suite (14 test totali). Nuova dipendenza: python-docx.
- Il salto a **v0.9** chiude la roadmap della review di metà 2026: ingestione dei dati previdenziali reali, proiezione INPS parametrica, glide path con obiettivi senza target, test suite validata per mutazione, motore bootstrap condiviso, generatore del deliverable finale. Il flusso end-to-end — dai file grezzi INPS/fondo all'IPS in Word — è ora interamente codificato nel plugin.

**v0.8.21**:
- **Motore bootstrap condiviso** (`motore_bootstrap.py`; skill `it-pianificazione` → v0.7, `it-pianificazione-obiettivi` → v0.17): `carica_storico`, campionamento a blocchi circolari e percentili unificati in un modulo unico, presente come copia sincronizzata nelle due skill (autosufficienza preservata: script + motore + CSV si copiano insieme). La test suite verifica l'identità delle copie e le proprietà del motore (blocchi consecutivi circolari, riproducibilità col seed, nessun valore inventato). Refactor validato **bit-per-bit**: con lo stesso seed, entrambi i Monte Carlo producono output identico alla versione precedente. `decumulo-obiettivi.py` resta deliberatamente sulla sua variante (blocchi non circolari): unificarla cambierebbe i percorsi simulati. Suite: 13 test.

**v0.8.20**:
- **Smoke test suite** (`tests/run_tests.py` + fixture sintetiche): 11 test che coprono igiene del repo, compilazione, parser previdenziali, valore chiuso della proiezione INPS, coerenza del Monte Carlo pensione, invarianti dell'allocatore e le regressioni dei due bug reali trovati nel flusso (substring "obbligAZIONARio", glide path senza target). Validata per mutazione (i test falliscono su codice deliberatamente rotto). È il prerequisito per il refactor sicuro del motore bootstrap condiviso.

**v0.8.19**:
- **Glide path con obiettivi senza target** (`it-pianificazione-obiettivi` → skill v0.16): gli obiettivi "il più possibile" (target vuoto) entrano nativamente nel calendario di de-risking — prima venivano saltati e serviva un target fittizio pari al capitale. Nessun versamento "necessario" per questi obiettivi, marcatore `(max)` nell'output, semantica coerente per terminanti (de-riskano e si spendono) e permanenti (mai). Reference `glide-path.md` aggiornata. Validato sul caso reale a quattro obiettivi: la traiettoria (74% → picco ~92% → 70%) è riprodotta senza workaround.

**v0.8.18**:
- **Ingestione dati previdenziali reali** (`it-pianificazione` → skill v0.6): nuovo `importa-previdenza.py` — parser dell'estratto conto INPS (XML) e dello storico movimenti del fondo pensione (CSV), con ricostruzione del montante contributivo sui tassi di capitalizzazione ufficiali ISTAT (tabella verificata giugno 2026) e stima euristica del mix azionario del fondo. Elimina il passaggio più manuale del flusso reale.
- **Proiezione INPS parametrica** (`proiezione-inps.py`): montante → pensione col metodo contributivo in termini reali, coefficienti di trasformazione 2025-26 (DM 436/2024) con riduzione parametrica per speranza di vita, sensibilità 3×3 (PIL reale × coefficienti). Entrambi validati sui dati reali del flusso end-to-end: il parser riproduce 455 settimane e il montante del fondo al centesimo; la proiezione riproduce esattamente la pensione calcolata a mano nel test (€27.138 con parametri severi).

**v0.8.17**:
- **Aggiornamento fiscale**: il tetto di deducibilità dei contributi a previdenza complementare sale da €5.164,57 a **€5.300/anno** (Legge di Bilancio 2026, L. 199/2025 comma 201, dal periodo d'imposta 2026). Aggiornati i riferimenti in `it-pianificazione`.

**v0.8.16**:
- **Crescita reale dei versamenti nel Monte Carlo pensione** (`it-pianificazione` → skill v0.5): il parametro `CRESCITA_VERSAMENTO_REALE` fa salire TFR e contributi al fondo di pari passo con lo stipendio, invece di tenerli costanti. Rende realistica la proiezione per chi prevede progressione di carriera.
- Il correttivo fa emergere l'effetto che una proiezione a stipendio piatto nasconde: una **RAL crescente abbassa il tasso di sostituzione** (la pensione contributiva si basa sulla media dei versamenti di tutta la carriera, quindi rimpiazza una frazione minore di uno stipendio finale più alto). Su caso reale, il passaggio da RAL piatta a +1,5%/anno con coefficiente di trasformazione in calo ha spostato la mediana del tasso di sostituzione da ~100% a ~68%.

**v0.8.15**:
- **Capitale libero divisibile tra più obiettivi di lungo termine** nell'allocatore di `it-pianificazione-obiettivi` (→ skill v0.15): l'eccedenza non va più a un unico bucket ma si può ripartire, con pesi e profili distinti, tra obiettivi come l'integrazione alla pensione e l'eredità (parametro `CAPITALE_LIBERO_SPLIT`). È la leva che muove di più l'allocazione aggregata.
- Aggiunto un **sesto profilo "Azionario totale" (100% azionario)** per obiettivi a orizzonte perpetuo: un'eredità che passa agli eredi senza mai essere liquidata non ha una data di prelievo da proteggere, quindi il rischio di sequenza è nullo e il 100% azionario è difendibile. Il profilo è first-class (tendina dell'Excel, range VLOOKUP estesi, letto da tutti gli script che usano i profili).
- Validato su dati reali: con l'eredità al 100% e uno split 30/70 tra integrazione pensione ed eredità, l'allocazione aggregata passa dal 57% al 70% azionario — mostrando come la scelta sul capitale libero domini l'aggregato. Invariante somma classi = capitale verificato; Monte Carlo, glide path e asset-location continuano a girare col sesto profilo; tutti gli Excel ricalcolano a zero errori.

**v0.8.14**:
- **Allocatore di capitale** in `it-pianificazione-obiettivi` (→ skill v0.14): per chi parte da una **somma liquida** da investire (liquidando un vecchio gestito e costruendo un portafoglio da zero), lo script `allocatore-capitale.py` propone **quanto capitale dedicare a ogni secchiello** e ne ricava la **vista aggregata su tre classi — azioni, obbligazioni, liquidità**. Colma il pezzo tra "ho una somma" e "qual è la mia allocazione": il pianificatore Excel prendeva la ripartizione del capitale come dato e si fermava ad azionario vs non azionario; l'allocatore propone la ripartizione e dà le tre classi.
- Logica goals-based per **valore attuale**, con la distinzione che conta: le **riserve permanenti** (fondo emergenza) si finanziano al valore pieno in liquidità oggi (le vuoi disponibili adesso, non in crescita verso una scadenza), gli obiettivi **terminanti** al **present value** (il capitale che al rendimento del profilo cresce fino al target). Allocazione per priorità poi orizzonte; se la somma avanza, l'eccedenza è **capitale libero**, segnalato come da formalizzare perché a un profilo di crescita domina l'aggregato.
- **Onesto sui limiti**: vista lump sum (i versamenti, se presenti, riducono il capitale richiesto — sono la leva separata del Monte Carlo) e promemoria che liquidare il vecchio gestito realizza plus/minus con la trappola del reddito di capitale (rimando a it-tax-optimization per l'ordine di smontaggio). Validato su dati reali (€130k: 59% azioni / 31,8% obbligazioni / 9,2% liquidità) e casi limite (capitale insufficiente, già accantonato, invariante somma = capitale). Reference `references/allocazione-capitale.md`.

**v0.8.13**:
- **La "seconda strada" nel Monte Carlo degli obiettivi** (→ skill v0.13): quando il versamento per la confidenza supera la capacità e non si può versare di più, `montecarlo-obiettivi.py` ora mostra l'alternativa di **alzare il rischio** (la quota azionaria) a parità di versamento. Nasce da un'osservazione dell'utente e colma una lacuna che ha anche l'upstream di Anthropic, la cui skill di pianificazione tratta l'allocazione come un 60/40 fisso senza offrirla come leva.
- Implementata con **onestà metodologica**, perché il rischio non è un sostituto pulito del versamento: lo strumento fa lo sweep dell'allocazione, trova quella che massimizza la probabilità, ma mostra la **distribuzione intera** (P10/P50/P90), non solo la probabilità — più rischio alza la mediana ma allarga la coda sinistra, e il caso brutto può peggiorare. La relazione rischio-probabilità è **non-monotòna** (oltre una certa quota il volatility drag la riabbassa) e lo sweep ne trova il massimo.
- Verdetti espliciti: la leva è **inadatta** per obiettivi essenziali o a breve orizzonte, **controproducente** se si è già in linea ("quando hai vinto, smetti di giocare"), un'**opzione reale** solo se sotto-finanziati, a lungo orizzonte e su obiettivi discrezionali — sempre col costo sul caso brutto quantificato. Validato su dati reali (università: +3 punti di probabilità ma P10 da €60k a €48k) e sintetici (obiettivo lontano dal target: +18 punti).

**v0.8.12**:
- **Modulazione delle bande di ribilanciamento per la volatilità della classe** in `it-rebalance` (→ skill v0.5), ultima rifinitura autocontenuta della roadmap. La banda 5/25 ora si scala con la volatilità del comparto: una soglia fissa rappresenta un segnale/rumore diverso tra classi (cinque punti di drift su un azionario capitano per rumore, su un obbligazionario sono un movimento raro), e scalare con σ rende la soglia un evento statisticamente più omogeneo.
- Trattata con **onestà la tensione teorica**, che è il punto delicato: l'intuizione "più volatile → banda più larga" (efficienza di trading, meno operazioni da rumore) ha contro di sé il controllo ottimo alla Leland "più volatile → banda più stretta" (una deviazione su un asset volatile è più rischiosa, quindi va tollerata meno). Non è una legge ma un trade-off tra efficienza di trading e aderenza al target; per un investitore fiscalmente sensibile propendere per bande un po' più larghe sulle classi volatili è difendibile, ma resta una scelta.
- Implementazione **deliberatamente modesta**: fattore `(σ/σ_riferimento)^β` clampato in un intervallo stretto (default 0,7–1,6), spegnibile per tornare alla pura 5/25, con l'allargamento cost-aware che resta la leva fiscalmente decisiva. Validato: l'azionario si allarga, le classi stabili si fermano al clamp, la cripto va al tetto, e con la modulazione spenta torna identica alla 5/25.

**v0.8.11**:
- **Monte Carlo della pensione** in `it-pianificazione` (→ skill v0.4): la proiezione del tasso di sostituzione non è più solo deterministica. Nuovo script `assets/montecarlo-pensione.py` + reference `references/montecarlo-pensione.md`.
- Il punto metodologico (e di onestà): i due pilastri hanno rischi **opposti**. La pensione pubblica INPS è rivalutata alla media quinquennale del PIL, non ai mercati — applicarle la volatilità azionaria sarebbe un errore concettuale, quindi fa da **àncora deterministica**. Il fondo pensione è esposto al mercato, e **lì** gira il Monte Carlo (block bootstrap sulla serie storica reale, stesso motore di `it-pianificazione-obiettivi`, media ricentrata sul rendimento del comparto).
- La lettura che ne emerge: **tutta la dispersione del tasso di sostituzione viene dal complementare**; il pubblico la àncora. Lo script stampa la decomposizione (parte fissa pubblica + banda di mercato P10–P90 del complementare), i percentili del tasso di sostituzione e la probabilità di una soglia obiettivo. Restano fuori dal Monte Carlo — perché non sono rischio di mercato — la discesa del coefficiente e la rivalutazione PIL, da trattare come scenari nel foglio. Validato contro replica indipendente (mediana sotto il deterministico per il volatility drag).

**v0.8.10**:
- Primo **asset** di `it-tax-optimization` (→ skill v0.9): l'**importatore di estratti broker** (`assets/importa-estratto-broker.py`), per lavorare sui dati reali del portafoglio invece che su input manuale. Ingerisce un estratto CSV — che scarichi tu, **senza dare credenziali a nessun tool** — calcola le plus/minus latenti per posizione, separa le minus latenti (candidate all'harvesting) dalle plus latenti, e con un secondo CSV per lo zainetto evidenzia quanta plus puoi realizzare a **imposta zero** per compensazione.
- Il parser è **tollerante ai formati**, perché la sfida vera è la varietà tra Directa, Fineco e Trade Republic: riconosce i nomi-colonna tipici dei dossier italiani con sinonimi, gestisce numeri all'italiana e all'inglese, rileva il delimitatore. Validato su due formati diversi più l'incrocio con lo zainetto; un bug di collisione nella mappatura colonne è stato trovato e corretto in fase di test. Con CSV di esempio come template.
- **MCP "live" sui broker: valutato ed escluso, con motivazione** (`references/import-dati-broker.md`). Verifica broker per broker: solo Directa ha un'API ufficiale (socket, richiede la piattaforma Darwin aperta in locale) e comunque non espone lo zainetto fiscale; Fineco e Trade Republic non hanno API retail ufficiali. Il dato che serve all'ottimizzazione vive nei **report esportabili**, non nelle API di trading — da qui la scelta dell'importatore di report, più robusto, conforme alle condizioni d'uso e sicuro.

**v0.8.9**:
- **Excel dedicato all'IPS** in `it-revisione` (→ skill v0.4), ultima voce di roadmap della skill. L'Investment Policy Statement — la "costituzione" del portafoglio — diventa un foglio compilabile (`assets/investment-policy-statement.xlsx`) accanto allo scheletro testuale della reference.
- Rispecchia le nove sezioni dell'IPS con celle da riempire, e aggiunge la parte che si calcola: dalla tabella dei target di allocazione **calcola da sé le bande di ribilanciamento** con la regola 5/25 (minore tra 5 punti assoluti e 25% del target), trasformando la regola astratta in soglie operative per ogni classe — per le classi piccole vince il 25% relativo, per quelle grandi i 5 punti assoluti. Più il controllo che i target sommino a 100%.
- Le regole nei drawdown (il cuore comportamentale) e i vincoli fiscali arrivano precompilati con default sensati. Quinto Excel del plugin. Validato: bande corrette, check 100% funzionante (segnala l'errore se la somma non torna), 0 errori formula.

**v0.8.8**:
- Aggiunto il **regime dichiarativo** a `it-tax-optimization` (→ skill v0.8): il caso di chi investe tramite **broker esteri** (Interactive Brokers, Degiro), finora dichiaratamente non coperto. Nuova reference `references/regime-dichiarativo.md`.
- Copre i **tre regimi a confronto** (amministrato / dichiarativo / gestito), il **quadro RT** (plusvalenze in dichiarazione) e il **quadro RW** (monitoraggio fiscale + **IVAFE** 0,2%, 0,4% per i Paesi black list), con cifre 2026 verificate via web (Agenzia delle Entrate, fonti specializzate).
- Il punto che più conta per l'ottimizzazione: in dichiarativo la **compensazione minus/plus è unificata** a livello di contribuente, quindi la frammentazione dello zainetto per broker — il problema centrale del multi-intermediario in amministrato — **sparisce**. È il "delta vs amministrato" reso esplicito.
- **Corretto un errore** preesistente: l'imposta di bollo sul dossier non ha tetto per le persone fisiche (il tetto di €14.000 vale solo per società ed enti), allineata all'IVAFE estera.

**v0.8.7**:
- **Time-weighted return** nel cruscotto di `it-revisione` (→ skill v0.3), ultima voce di roadmap della skill. Il foglio "Rendimento TWR" (cruscotto ora a sei fogli) misura il rendimento della **strategia** neutralizzando i flussi — il numero da confrontare con un benchmark — incatenando i rendimenti dei sotto-periodi tra un versamento e l'altro.
- Sullo stesso foglio, il **money-weighted esatto via XIRR** (più preciso del Dietz aggregato del foglio Andamento): così TWR e MWR sono calcolati sugli stessi dati e direttamente confrontabili. La **differenza tra i due è l'effetto del timing dei versamenti**: se il MWR batte il TWR, i versamenti sono caduti prima dei rialzi.
- Validato contro un calcolo Python indipendente: sull'esempio TWR 11,63% e MWR (XIRR) 12,15% coincidono al centesimo tra Excel e Python; la differenza −0,52% è l'effetto timing. Cruscotto rivalidato: 80 formule, 0 errori.

**v0.8.6**:
- **Generatore di ordini CSV per broker** in `it-rebalance` (→ skill v0.4), ultima voce di roadmap rimasta sulla skill. Lo script di ribilanciamento ora, oltre a calcolare il piano tax-aware, **esporta gli ordini da eseguire come un CSV per broker**.
- La parte sostanziale è l'**instradamento della cassa**: gli acquisti delle classi sottopesate vengono finanziati dalla liquidità presente su ciascun broker (le vendite realizzate lì + eventuali versamenti che vi atterrano), così ogni file è eseguibile dove sei loggato, senza dover spostare cassa tra intermediari (operazione che richiede giorni). Ogni riga porta l'annotazione fiscale (plus/minus, imposta, compensazione da zainetto) e una colonna `strumento_ISIN` da compilare a mano (il piano ragiona per classe).
- Onestà: i broker italiani non importano ordini da CSV, quindi i file sono una **checklist di esecuzione** e una traccia di audit, non caricabili in un click — detto chiaramente nello script e nella skill. Validato su scenario mono e multi-broker (invariante di cassa per broker), con round-trip CSV verificato.

**v0.8.5**:
- Migliorata l'accuratezza del **montante INPS iniziale** in `it-pianificazione` (→ skill v0.3), l'unica approssimazione nota dichiarata rimasta nel plugin. Verificato via web il coefficiente di trasformazione a 67 anni (5,608%, Decreto 20/11/2024), aliquota 33% e rivalutazione sulla media quinquennale del PIL.
- Il template Excel ora accetta il **montante reale dall'estratto conto INPS** (cella dedicata nel foglio Input) e lo usa quando valorizzato — è il dato esatto, da preferire sempre. La proiezione dei contributi futuri era già corretta (rivalutazione anno per anno); l'unico punto debole era la stima del montante già maturato.
- La **stima di ripiego** (quando l'estratto conto non è disponibile) non è più la grezza `anzianità × RAL × 33%` ma `RAL × 33% × Σ q^k` con `q = (1+rivalutazione)/(1+crescita_RAL)`: tiene conto sia della retribuzione passata più bassa sia della rivalutazione dei contributi già versati, e si riduce alla grezza quando i due effetti si compensano (riv≈g). Validata su tre rami (montante reale fornito → usato; caso limite riv=g → torna alla grezza €267.300; riv>g → corregge al rialzo). Excel rivalidato: 707 formule, 0 errori.

**v0.8.4**:
- Due **correzioni di onestà** al Monte Carlo di `it-pianificazione-obiettivi` (→ skill v0.12), nella nuova reference `references/mercati-e-correlazione.md`. Nessun dato inventato: le cifre vengono dal Global Investment Returns Yearbook 2025 (Dimson-Marsh-Staunton/UBS), verificato.
- **Non-USA-centricità**: il bootstrap ricampiona da serie USA (S&P 500), il mercato storicamente più fortunato; l'azionario mondiale ha reso ~5,2% reale dal 1900 (gli USA di più), e solo ~3,5% nel 21° secolo. Aggiunto un **de-rating** dell'azionario (parametro `DERATING_AZIONARIO` nel decumulo) che trasforma la lente USA in scenario globale: sul caso di test la sola fortuna americana vale ~3,3 punti di probabilità di successo. Più la guida a calibrare i rendimenti attesi su valori mondiali, non USA.
- **Correlazione sistemica tra obiettivi**: il Monte Carlo li simulava come indipendenti, ma condividono lo stesso mercato — un crollo li colpisce insieme. Aggiunta una **simulazione congiunta** (un unico percorso di mercato per simulazione, condiviso tra obiettivi) che riporta la probabilità che tutti gli essenziali falliscano nello stesso scenario: l'indipendenza la **sottostima** (sul caso di test, +3,4 punti; molto di più se gli obiettivi condividono esposizione azionaria). Validate le proprietà strutturali (de-rating monotòno, coda congiunta ≥ prodotto indipendente, marginali invariate).

**v0.8.3**:
- Rifinita `it-revisione` (→ skill v0.2), la skill di sintesi appena nata, con tre aggiunte di usabilità dalla sua roadmap.
- **Template del report** (`assets/template-revisione.md`): scheletro markdown precompilato delle cinque sezioni della revisione, da riempire — rende il report completo e coerente di anno in anno.
- **Foglio "Azioni"** nel cruscotto patrimoniale (ora a cinque fogli): tracker delle azioni emerse (azione, dominio, priorità, scadenza, stato) con la legenda di prioritizzazione, ponte tra report ed esecuzione. Excel rivalidato (0 errori).
- **Investment Policy Statement personale** (`references/investment-policy-statement.md`): la "costituzione" del portafoglio — obiettivi, profilo di rischio, allocazione target, bande, **regole nei drawdown** (il cuore comportamentale: la pre-decisione scritta prima del crollo), politica di versamento e prelievo, vincoli fiscali, cadenza — con scheletro compilabile. Formalizza in policy ciò che le altre skill producono come numeri, e dà alla revisione un riferimento da cui misurare gli scostamenti. Con questa, `it-revisione` copre anche la funzione IPS dell'upstream `investment-proposal`.

**v0.8.2**:
- Aggiunta la **fase di decumulo**, il tassello più trasversale che mancava (era rinviato da tre skill): l'intero plugin ragionava sull'accumulo, ora copre anche il prelievo. Distribuita dove ciascuna metà è di casa.
- In `it-pianificazione-obiettivi` (→ skill v0.11) la parte **"quanto"**: `references/decumulo.md` + `assets/decumulo-obiettivi.py`. Il rischio di **sequenza dei rendimenti** (in prelievo conta l'ordine, non solo la media — stesso insieme di rendimenti, ordini opposti, esiti opposti: lo script lo dimostra), il **tasso di prelievo sostenibile** con la regola del 4% **scontata onestamente** per l'Europa (i dati USA sono il caso favorevole; 3-3,5% più difendibile), e le mitigazioni. Risultato onesto e controintuitivo validato dallo script: il **buffer di liquidità non è un free lunch** (sui dati storici può abbassare il successo; il suo valore è comportamentale), in linea col consenso accademico. Tre proprietà strutturali validate (monotonicità, stessa media nei due ordini, peggiori≤migliori).
- In `it-rebalance` (→ skill v0.3) la parte **"come"**: `references/sequenza-liquidazione.md`. La sequenza di liquidazione fiscalmente efficiente (liquidità → flussi già tassati → vendite tax-aware con la gerarchia delle leve e l'ottimizzazione multi-broker → fondo pensione agevolato 9-15% in erogazione), e il prelievo annuo che diventa anche l'occasione per ribilanciare. Riusa il motore multi-broker della v0.2.

**v0.8.1**:
- Rifinita `it-rebalance` (→ skill v0.2), la skill che era rimasta più indietro, portandola al livello delle altre con due interventi e il suo **primo asset** (script validato).
- **Ottimizzazione globale dello zainetto multi-broker** (`references/ribilanciamento-multibroker.md` + `assets/ribilanciamento-multibroker.py`): in regime amministrato la compensazione non attraversa i broker, quindi non conta solo COSA vendere ma DOVE — la doppia ottimizzazione broker × tipo fiscale realizza le plus presso il broker con zainetto e su strumenti reddito diverso (le plus su ETF armonizzati non sono mai compensabili). Chiude l'asimmetria col motore fiscale, che già ragionava multi-broker. Validato su tre scenari (costo €0 nel caso base, contro i ~€520 della scelta ingenua).
- **Bande di tolleranza dinamiche** (`references/bande-dinamiche.md`): si ribilancia a soglia non a calendario, con la regola **5/25** (minore tra 5 punti assoluti e 25% relativi) e l'**allargamento cost-aware** — la banda si allarga quando correggere costa imposta netta, così non si paga imposta per un drift troppo piccolo per contare. Adatta al fisco italiano il trade-off di Kitces tra beneficio del ribilanciamento e attrito.
- Comando `/ribilancia` aggiornato. Prossimo tassello previsto: il **decumulo** (prelievi tax-efficient), oggi rinviato da più skill.

**v0.8.0**:
- Aggiunta la **sesta skill, `it-revisione`** — il *livello di sintesi* del plugin, che mancava. Le altre cinque skill sono motori analitici (ognuna risponde a una domanda); questa è il direttore d'orchestra: una volta l'anno tiene insieme pensione, obiettivi, fiscalità e allocazione in un quadro unico con azioni prioritizzate e un report. Adatta per chi gestisce i propri soldi i workflow upstream rivolti al consulente (`client-review` + `client-report`, in parte `investment-proposal`).
- **Workflow di revisione in cinque passi** (fotografia → cosa è cambiato → avanzamento per dominio → azioni prioritizzate → report), con la skill che **richiama** le altre invece di duplicarle. La **logica di prioritizzazione** è il cuore: scadenza (minus a fine anno, versamento fondo pensione entro il 31/12) → impatto strutturale (gap previdenziale, obiettivo a rischio) → manutenzione (ribilanciamento, de-risking). E le **azioni cross-dominio** che risolvono più cose insieme (ribilanciare usando le minus in scadenza; indirizzare il versamento annuale dove rende di più).
- **Quarto Excel validato**: `cruscotto-patrimoniale.xlsx` (Patrimonio / Allocazione / Andamento / Sintesi), 38 formule, 0 errori. Il foglio Andamento separa il **rendimento di mercato dai versamenti** (l'errore più comune del fai-da-te) e calcola un rendimento money-weighted semplificato (Dietz) e reale.
- **Reference `metodo-revisione.md`**: la cadenza (annuale + finestra fiscale di fine anno + revisione straordinaria per eventi), come misurare il rendimento senza ingannarsi (money-weighted vs time-weighted, rendimento reale), e le azioni cross-dominio. Comando `/revisione`. Con questa skill il fork ha adattato **tutte** le skill dell'upstream.

**v0.7.15**:
- Aggiunti a `it-tax-optimization` (→ skill v0.7) i **casi speciali cripto** (`references/criptovalute-casi-speciali.md`): la copertura cripto del plugin è ora completa su tre reference (base, avanzata, casi di confine). Dati 2026 verificati via web. I punti contesi restano segnalati come aperti.
- **Trasferimenti, bridge, wrapping**: l'interpello 135/2025 (spostare cripto tra propri wallet non è realizzo se documentato; senza prova, costo zero); bridge dello stesso token come trasferimento neutro; wrapping (BTC→WBTC, ETH→stETH) come permuta "stessa funzione economica" — non imponibile per la tesi prevalente, ma token tecnicamente distinto e prassi AdE assente, quindi caveat.
- **Cripto in impresa/P.IVA**: art. 110 TUIR (per le società le valutazioni di fine esercizio non concorrono a IRES/IRAP, si tassa al realizzo); esenzione IVA del cambio (Hedqvist C-264/14); il forfettario che investe in cripto (compartimento separato, nessun cumulo col reddito d'impresa né impatto sul tetto); mining professionale vs occasionale; cripto come stipendio/compenso (reddito di lavoro a IRPEF).
- **Neo-residenti**: flat tax art. 24-bis (€100.000/anno, €200.000 per i trasferimenti post-estate 2024, +€25.000 per familiare) con la **questione aperta** della fonte (estera o italiana) delle cripto, decisiva per sapere se la flat tax le copre.
- **Successione e donazione**: riforma TUS (D.Lgs. 139/2024), cripto come beni mobili nell'attivo ereditario; territorialità (de cuius residente in Italia → tutto il patrimonio cripto anche estero); costo di carico per eredi (valore in successione) e donatari (costo del donante); il rischio del **costo zero** senza documentazione, da trasmettere agli eredi; l'accesso alle chiavi private come problema di pianificazione successoria.

**v0.7.14**:
- Aggiunti a `it-tax-optimization` (→ skill v0.6) i **temi cripto avanzati** (`references/criptovalute-avanzate.md`), chiudendo l'ultimo tassello cripto del plugin. Dati 2026 verificati via web (9 ricerche). Trattati con onestà metodologica: dove la prassi dell'Agenzia manca, la reference segnala l'incertezza invece di inventare certezza.
- **DeFi**: staking/lending/yield tassati alla percezione sull'intero lordo, con il momento impositivo (maturazione vs disponibilità per lo staking locked) segnalato come dibattuto; deposito in lending non imponibile; **liquidity pool/LP token** come area più incerta (ingresso/uscita come permuta potenzialmente imponibile, impermanent loss); **airdrop e fork** con la questione dell'onerosità — un airdrop gratuito potrebbe non essere imponibile alla ricezione, correggendo la semplificazione della reference base; **mining** occasionale vs professionale.
- **NFT secondo il ruolo**: investitore (33% come cripto-attività, gas fee nel costo) vs artista/creatore (reddito di lavoro autonomo/impresa a IRPEF progressiva); scambio NFT/NFT come questione aperta.
- **Ravvedimento operoso**: come regolarizzare cripto non dichiarate negli anni passati — due violazioni autonome (Quadro RW 3-15%/anno; Quadro RT 70%/120% dell'imposta + IVCA), ridotte in frazioni anno per anno e prima dell'accertamento. La finestra **DAC8** (operativa dal 2026, prima comunicazione all'Agenzia entro il 30/6/2027) la sta chiudendo; soglia **penale** €50.000/anno. Esempio (ottobre 2026): €100k non dichiarati per il 2022-2024 → sanzione minima €9.000, con ravvedimento ≈ €1.304 (≈ €1.360 dopo il 2/11/2026).

**v0.7.13**:
- Aggiunto a `it-pianificazione-autonomi` (→ skill v0.3) il **foglio Excel di proiezione previdenziale per autonomi** (`assets/proiezione-pensione-autonomi.xlsx`), che dà agli autonomi lo stesso strumento operativo che i dipendenti già avevano. 598 formule, 0 errori (validato con recalc.py).
- Sei fogli (Input, Coefficienti, Previdenza, Fiscalità, Complementare, Riepilogo) con le differenze del mondo autonomo: **aliquota contributiva 26,07%** (Gestione Separata) o l'aliquota soggettiva della cassa, editabile; **nessun TFR**; coefficiente di trasformazione proiettato al pensionamento.
- Il foglio **Fiscalità** è il valore aggiunto: confronto forfettario vs ordinario che rende esplicita la deducibilità — i contributi obbligatori si deducono in entrambi i regimi, il versamento al fondo pensione **solo in ordinario**. Verificato sui dati: con €3.000 di versamento, risparmio fiscale €0 in forfettario, €847 in ordinario. È la regola centrale della skill resa numero.
- Completa la roadmap operativa della skill autonomi (era il "v0.5" previsto). Tutto in termini reali, con disclaimer coerente.

**v0.7.12**:
- Aggiunto a `it-pianificazione-autonomi` (→ skill v0.2) il **dettaglio delle casse professionali** (`references/casse-professionali.md`), con dati 2026 verificati via web. Chiude l'ultimo grande buco di copertura del plugin: la skill autonomi ora parla anche a ingegneri, avvocati, medici, commercialisti, psicologi, geometri (e non solo ai freelance in Gestione Separata).
- **Framework comune**: le due cornici normative (D.Lgs. 509/1994 storiche, 103/1996 interamente contributive); i due pilastri — contributo soggettivo (% sul reddito, costruisce la pensione, deducibile) e contributo integrativo (4% in fattura, 5% per CIPAG, pass-through sul cliente, non deducibile); minimi/massimali/deroghe; il calcolo contributivo (montante + coefficiente di trasformazione proprio di ogni cassa).
- **Il punto che si collega al forfettario**: il contributo *obbligatorio* alla cassa (soggettivo) è deducibile **anche in forfettario** (abbatte la base dell'imposta sostitutiva), a differenza del contributo *volontario* al fondo pensione complementare — coerente e complementare al tema centrale della skill.
- **Tabella delle principali casse** con aliquote 2026 (indicative, da verificare): Inarcassa 14,5%+4%; Cassa Forense 17% (18% dal 2027)+4%; CNPADC 12-100% (a scelta)+4%; ENPAM Quota A fissa + Quota B 19,5%; ENPAP 10%+2%; CIPAG 20% (22% dal 2027) + 5%. Più le leve di pianificazione (saturare l'aliquota volontaria deducibile, il fondo pensione come terzo pilastro sopra la cassa). Descrizione YAML e scope aggiornati.

**v0.7.11**:
- Aggiunto a `it-tax-optimization` (→ skill v0.5) il **trattamento delle criptovalute** (`references/criptovalute.md`), con fiscalità 2026 verificata via web.
- **Aliquote 2026**: 33% sulle plusvalenze e proventi da cripto-attività generali (Bitcoin, Ethereum, altcoin, NFT, stablecoin in dollari), salite dal 26%; 26% solo per gli e-money token in euro conformi a MiCA; neutralità per la conversione euro ↔ EMT-euro. Franchigia di €2.000 abolita dal 2025: si tassa dal primo euro, e l'aliquota è quella vigente al realizzo (nessun grandfathering per data di acquisto).
- **Il compartimento separato** (estende il tema centrale della skill): le cripto sono redditi diversi (art. 67 c-sexies) ma le minusvalenze cripto compensano *solo* plusvalenze cripto — mai azioni, ETF o derivati. La tabella centrale di compensazione passa da due a **tre compartimenti** (redditi di capitale, redditi diversi "tradizionali", redditi diversi "cripto").
- Coperti inoltre: eventi tassabili e neutri (con il punto controverso della permuta cripto-cripto trattato onestamente, non semplificato), metodo LIFO (dichiarativo) / costo medio ponderato (amministrato), monitoraggio fiscale quadro RW/W obbligatorio anche per self-custody, imposta sul valore delle cripto-attività 0,2%, il **regime amministrato cripto** (possibile dal 2023, intermediari sostituto d'imposta), e le leve di pianificazione (rivalutazione al 18%, harvesting intra-compartimento). Cripto rimosse dalle esclusioni della skill; descrizione YAML aggiornata per il trigger.

**v0.7.10**:
- Raffinamenti di secondo ordine a `it-pianificazione-obiettivi` (→ skill v0.10), tutti validati sui dati reali.
- **Monte Carlo con bootstrap storico**: nuovo modello `MODELLO='bootstrap'` (oltre alla Normale) che ricampiona a blocchi da una serie storica reale (`assets/rendimenti-storici.csv`: S&P 500 e T-Bond 10 anni 1928-2025, fonte Damodaran/NYU Stern), combinata per il % azionario del profilo, con media ricentrata sull'ipotesi del profilo (calibra la media, mantiene forma/code/correlazioni reali). Cattura code grasse, asimmetria, correlazione azionario/obbligazionario e mean reversion che la Normale i.i.d. ignora. Risultato istruttivo: su orizzonti lunghi il bootstrap dà una distribuzione *più stretta* della Normale (la mean reversion riduce la dispersione che il random walk sovrastima).
- **Reinvestimento del risparmio IRPEF** nell'ottimizzatore asset location (parametro `REINVESTI_RISPARMIO_IRPEF`): reinvestendo la deduzione nel dossier, il vantaggio del fondo pensione sui dati reali sale da +9% a +25% (la deduzione reinvestita vale €101k invece di €52k di cassa).
- **Glide path a curvatura regolabile** (`CURVATURA`): la rampa di de-risking può restare lineare (default) o tenere l'azionario più alto a lungo e poi scendere ripida (più crescita, de-risking tardivo).
- Decumulo delle riserve permanenti lasciato esplicitamente in roadmap: è un problema distinto dall'accumulo (prelievo sostenibile, sequenza in prelievo), più adatto a it-rebalance o a un modulo dedicato che a un innesto forzato qui.

**v0.7.9**:
- Aggiunto a `it-pianificazione-obiettivi` (→ skill v0.9) l'**ottimizzatore quantitativo dell'asset location** (`assets/asset-location-optimizer.py`): dà i *numeri* al framework qualitativo della reference. Calcola il valore finale al netto di tasse E costi in ciascun contenitore, per due decisioni: fondo pensione vs dossier (pensione) e PIR vs dossier (lungo termine).
- **Fondo pensione**: la deduzione IRPEF è il driver (€5.300/anno al 33% = €52.470 cumulati su 30 anni), ma i rendimenti tassati al 20%/anno e l'ISC più alto la erodono; il vantaggio netto resta positivo ma più contenuto della sola deduzione (test sui dati reali: ≈ +9% vs dossier).
- **PIR**: risultato controintuitivo confermato quantitativamente — su orizzonti lunghi il TER più alto del PIR supera il risparmio fiscale dello 0%, e il vantaggio diventa **negativo** (test: università €50k a 19 anni → −€2.861). Lo script stampa il **TER di pareggio** del PIR (nel test 1,15%, sotto i TER tipici 1,2-1,35%): la metrica per decidere se un prodotto PIR concreto conviene.
- Validato sui dati reali (emergenza + università €80k); formattazione dei valori negativi sistemata. Integrato come strumento dello Step 7 (asset location) con i dovuti caveat: la comparazione assume lo stesso rendimento e non cattura il costo di concentrazione del PIR.

**v0.7.8**:
- Aggiunto a `it-pianificazione-obiettivi` (→ skill v0.8) l'**asset location avanzato** (`references/asset-location.md`): non *cosa* comprare né *quanto* azionario, ma in *quale contenitore fiscale* tenere ciascun obiettivo. Affronta la peculiarità italiana: spazio agevolato scarso e vincolato (niente conto tax-deferred generico), quindi poche decisioni mirate invece di una distribuzione libera tra conti.
- Copre i contenitori italiani con la fiscalità 2026 verificata: dossier amministrato (26%/12,5%, default flessibile), fondo pensione (deducibile, rendimenti 20%, prestazione 15→9%, ma vincolato alla pensione), PIR ordinario (esente 0% + esente successione se 5 anni, ma 70/25/5 di concentrazione su PMI italiane, €40k/anno e €200k totali), polizze vita (differimento + esenzione successoria, ma costi alti), conto deposito. Framework "quale contenitore per quale obiettivo" + le tensioni da comunicare (vincolo pensione, costo-concentrazione del PIR, costi delle polizze).
- Integrato come Step 7 nel workflow della skill, con cross-reference a `it-pianificazione` (fondo pensione), `it-tax-optimization` (asimmetria e aliquote dentro il dossier) e `selezione-strumenti.md` (lo strumento dentro il contenitore).

**v0.7.7**:
- Aggiunto a `it-pianificazione-obiettivi` (→ skill v0.7) il **flag terminante/permanente** per obiettivo (colonna Tipo nel foglio Excel, menu a tendina). Chiude l'artefatto del glide path emerso nel test dal vivo: un obiettivo *terminante* si spende a scadenza (casa, università) — de-riska ed esce dal portafoglio; un obiettivo *permanente* è una riserva che resta (fondo emergenza) — non de-riska (non ha scadenza di spesa) e non esce, smussando l'aggregato invece di farlo saltare.
- Senza il flag, alla conclusione del fondo emergenza (0% azionario) l'aggregato saltava verso l'alto (rimuovere una componente a 0% alza la media) — fuorviante, perché il fondo emergenza non si spende. Verificato sui dati reali: l'aggregato ora evolve in modo liscio e monotòno (≈56% durante la crescita, poi de-risking fino a 0%), senza il salto.
- Aggiornati `glidepath-obiettivi.py` (legge il flag, logica permanente vs terminante nella proiezione e nell'aggregato), il foglio Excel (colonna Tipo + dropdown), e la reference `glide-path.md` (la distinzione è ora automatica, non più un raffinamento futuro).

**v0.7.6**:
- Aggiunto a `it-pianificazione-obiettivi` (→ skill v0.6) il **glide path automatico**: lo script `glidepath-obiettivi.py` genera il calendario di de-risking anno per anno. Per ogni obiettivo, la quota azionaria target a ciascun anno (tiene la quota del profilo finché manca più della finestra di de-risking, default 7 anni, poi scende linearmente fino all'atterraggio, default 0%, entro la scadenza); più l'aggregato di portafoglio pesato per il capitale proiettato. È il programma di spostamento dei target che `it-rebalance` esegue — la dimensione dinamica dell'allocazione, finora solo descritta, ora operativa.
- Reso operativo il legame col fisco: ogni spostamento del glide path genera vendite = eventi fiscali; la reference `glide-path.md` codifica le contromosse (de-risking graduale per distribuire gli eventi, uso dei flussi per ridurre le vendite, coordinamento con lo zainetto).
- Esempio dal vivo sui dati reali: l'università tiene il 65% azionario per 12 anni, poi de-riska a 0% negli ultimi 7. Nuova reference `glide-path.md` (formula, parametri, viste per-obiettivo/aggregata, limiti). Identificato un raffinamento (flag terminante/permanente: il fondo emergenza è un cuscinetto perpetuo, non si spende a scadenza).

**v0.7.5**:
- Aggiunta a `it-pianificazione-obiettivi` (→ skill v0.5) l'**allocazione complessiva del portafoglio**: la skill ora aggrega i secchielli per obiettivo (ciascuno pesato per il suo capitale, con una quota azionaria rappresentativa per profilo) nell'asset allocation totale, in vista **stock** (sul capitale esistente) e **flusso** (sui versamenti). È l'anello che chiude il cerchio con `it-rebalance`: il target che quella skill mantiene nasce da questa aggregazione, non da un numero scelto a mano.
- Concetti chiave codificati: l'allocazione è *emergente* (non scelta dall'alto), NON si implementa come un singolo fondo bilanciato (il "non azionario" ha ruoli diversi: liquidità d'emergenza vs zavorra obbligazionaria), stock ≠ flusso, ed è dinamica (glide path). Esempio dal vivo sui dati reali dell'utente: portafoglio 56% azionario / 44% non azionario, ma versamenti 0% azionario (l'unico da finanziare ora è il fondo emergenza in liquidità).
- Excel esteso: colonna % Azionario nella tabella profili, scomposizione azionaria per obiettivo (capitale e versamento), sezione "Allocazione complessiva" nel Riepilogo. Versamento mensile ora **floored a 0** per obiettivi già sovra-finanziati (coerente col fix del Monte Carlo, evitava aggregazioni di flusso assurde). 90 formule, zero errori. Reference `orizzonte-allocazione.md` aggiornata con le %azionario e il concetto di aggregazione.

**v0.7.4**:
- Fix in `montecarlo-obiettivi.py` (emerso da un test su dati reali): per gli obiettivi già **sovra-finanziati** dal capitale esistente (versamento deterministico negativo), lo script non simula più prelievi — azzera il versamento e riporta la probabilità con €0/mese. La domanda corretta è "il capitale che ho basta da solo?", non "quanto posso prelevare?". Senza il fix, un obiettivo con grande anticipo e target basso produceva numeri depressi e fuorvianti.

**v0.7.3**:

- Aggiunto a `it-pianificazione-obiettivi` (→ skill v0.4) il **Monte Carlo**: lo script `montecarlo-obiettivi.py` legge gli obiettivi dal foglio Excel e simula migliaia di percorsi di accumulo (rendimenti casuali con media e volatilità del profilo), restituendo per ciascun obiettivo la probabilità di successo, i percentili del capitale finale e il versamento necessario per una confidenza-obiettivo. Aggiunta la colonna "Volatilità attesa" alla tabella profili dell'Excel (alimenta la simulazione).
- L'insight chiave: il versamento deterministico del foglio centra la media → ~50% di probabilità (meno per orizzonti lunghi ad alta volatilità, per il *volatility drag*). Esempio dal vivo: obiettivo a 20 anni in azionario, deterministico €346/mese = 41% di successo, servono €544 per l'85%. Trasforma il limite "deterministico" dichiarato in v0.7.2 in una feature.
- Nuova reference `monte-carlo.md`: metodologia, volatilità per profilo, come calibrare la confidenza alla criticità dell'obiettivo, il rischio di sequenza, e soprattutto i **limiti del modello** (rendimenti normali senza code grasse, i.i.d., parametri ipotetici, niente correlazioni tra obiettivi). I numeri sono ordini di grandezza per calibrare il rischio, non garanzie.

**v0.7.2**:
- Aggiunto a `it-pianificazione-obiettivi` (→ skill v0.3) il pianificatore Excel `pianificatore-obiettivi.xlsx`: complemento operativo della skill, analogo a `proiezione-pensione.xlsx`. Tre fogli (Parametri, Obiettivi, Riepilogo), tabella multi-obiettivo da 10 slot con menu a tendina per profilo e priorità, calcolo automatico del versamento mensile necessario per ciascun obiettivo (formula del valore futuro di una rendita, con ramo per rendimento 0), e riconciliazione totale vs capacità di risparmio con breakdown per priorità. 50 formule, zero errori, validato. La matematica è quella di `matematica-accumulo.md`, così i numeri dell'Excel e del report coincidono (esempi: emergenza €513/mese, casa €478/mese, lungo termine €346/mese).

**v0.7.1**:
- Estesa `it-pianificazione-obiettivi` (→ skill v0.2) con la reference `selezione-strumenti.md`: per l'**uso personale**, una selection spec criteri-based per scegliere lo strumento concreto in ciascun comparto. Niente ISIN fissi (che invecchiano e sono fragili), ma criteri precisi cuciti sulla fiscalità italiana — UCITS armonizzato, domicilio Irlanda per l'azionario USA-heavy, accumulazione per il differimento fiscale, TER/AUM come filtri di qualità, BTP a 12,5% per la parte sicura. Lo strumento concreto si trova applicando i criteri su uno screener aggiornato.
- Chiarita la distinzione: postura advisor-client (richiede abilitazione MiFID/OCF, profilazione, valutazione di adeguatezza, IPS — non è un cambio di tono ma di regolamentazione) vs uso personale (la selection spec è lecita e robusta). Il plugin resta a postura personale/educativa.

**v0.7**:
- Nuova skill `it-pianificazione-obiettivi`: pianificazione finanziaria goals-based multi-obiettivo. È il pezzo **a monte** che mancava: definisce gli obiettivi (fondo emergenza, casa, figli, obiettivi liberi), li mappa a profili di allocazione per orizzonte, e calcola il piano di accumulo. L'allocazione che produce diventa il target di `it-rebalance`.
- Copre il framework goals-based (orizzonte → rischio → allocazione → strumenti italiani), il fondo di emergenza come obiettivo 0, il glide path (de-risking progressivo), e la riconciliazione multi-obiettivo quando le risorse non bastano.
- Due reference: `orizzonte-allocazione.md` (mappa orizzonte→strumenti IT: conto deposito, BTP a 12,5%, ETF UCITS, PAC + glide path) e `matematica-accumulo.md` (formule del piano di accumulo, inflazione, esempi worked, prioritizzazione). Slash command `/obiettivi`.
- **Postura educativa/metodologica** coerente con `it-rebalance`: mostra allocazioni-tipo come esempi, NON raccomanda titoli specifici, NON sceglie l'allocazione al posto dell'utente. Risolve il buco emerso dal confronto con l'upstream (dove il goals-based è spezzato tra `financial-plan` e `investment-proposal`).
- Origine architetturale: questa skill chiude il cerchio del plugin — è l'anello a monte di `it-rebalance`, che finora riceveva l'allocazione-target come input senza una skill che la definisse.

**v0.6.1**:
- Fix sostanziale in `it-pianificazione` (→ skill v0.4), emerso da un test su profilo reale: il coefficiente di trasformazione viene ora **proiettato in calo** all'anno di pensionamento, invece di usare quello attuale. I coefficienti calano ~1,8% per biennio (speranza di vita), quindi usare quello attuale per una pensione lontana sovrastimava l'assegno — su 30 anni, fino al 31% (tasso di sostituzione 79% irrealistico → 61% realistico). Prima c'era uno scollamento tra la guida testuale (che diceva di proiettare) e il motore di calcolo/Excel (che usava il coefficiente attuale via VLOOKUP); ora combaciano.
- Excel: nuovo parametro editabile "Decadimento coefficiente / biennio" (default 1,8%), nuovo derivato "Coefficiente proiettato", il foglio Pubblica mostra sia il coefficiente attuale (riferimento) sia quello proiettato (usato), e gli scenari variano anche il ritmo di decadimento (2,2% conservativo / 1,5% ottimistico). 707 formule, zero errori.
- Pseudocodice Step 2, reference `previdenza-obbligatoria.md` (formula esplicita + esempio worked) e anti-pattern aggiornati di conseguenza.

**v0.6**:
- Nuova skill `it-pianificazione-autonomi`: pianificazione pensionistica per lavoratori autonomi e partite IVA. Copre Gestione Separata INPS (26,07%, no TFR, no contributo minimo) e i principi delle casse professionali.
- **Punto centrale**: per i forfettari il contributo volontario al fondo pensione NON è deducibile (regime sostitutivo ≠ IRPEF), il che inverte la logica valida per i dipendenti. La reference `fiscalita-forfettario.md` include il confronto numerico fondo pensione vs ETF per il forfettario puro.
- Due reference dedicate: `previdenza-gestione-separata.md`, `fiscalita-forfettario.md`. Riusa (non duplica) le reference condivise di `it-pianificazione` su complementare e tenore di vita.
- Slash command `/pensione-autonomi`. Numeri 2026 verificati: Gestione Separata 26,07% (Circolare INPS 8/2026), massimale €122.295, soglia forfettario €85.000, coefficiente redditività 78% per IT/professioni, imposta sostitutiva 15%/5%.
- Aggiornati i cross-reference in `it-pianificazione` per puntare alla skill gemella.

**v0.5**:
- Nuova skill `it-rebalance`: ribilanciamento di portafoglio tax-aware. Principio cardine: in Italia ogni vendita per ribilanciare è un evento fiscale (no tax-deferred rebalancing). Gerarchia di 4 leve ordinate per costo fiscale crescente (versamenti → flussi → vendite in minus → vendite in plus).
- Due reference: `gerarchia-leve.md` (4 leve con esempi numerici per accumulo e decumulo), `coordinamento-zainetto.md` (protocollo per il ribilanciamento di fine anno coordinato con lo zainetto in scadenza).
- Slash command `/ribilancia`.

**v0.4**:
- Patch `it-tax-optimization`: aggiornata la Tobin tax 2026 (L. 199/2025, art. 1 commi 29-31). Aliquote azioni raddoppiate dal 1° gennaio 2026: 0,20% su mercato regolamentato (era 0,10%), 0,40% OTC (era 0,20%). Derivati invariati (misura fissa a scaglioni). Chiarita l'esenzione ampia (ETF, fondi, obbligazioni, titoli di Stato) che rende il retail in ETF sostanzialmente non impattato.
- Aggiunto codice tributo F24 4058 e soglia capitalizzazione €500M (lista Consob).

**v0.3**:
- Aggiunta skill `it-pianificazione` per pianificazione pensionistica integrata (previdenza obbligatoria INPS + complementare + proiezione tenore di vita)
- Quattro reference: `previdenza-obbligatoria.md` (con tabella ufficiale completa DM 20/11/2024, 15 coefficienti 57-71 anni + formula interpolazione mensile), `previdenza-complementare.md`, `proiezione-tenore-vita.md`, `integrazione-fiscale-joint.md` (4 pattern joint con `it-tax-optimization`)
- Asset Excel `proiezione-pensione.xlsx`: template editabile con 5 fogli, 704 formule, validato zero errori
- Slash command `/pensione`; numeri 2026: IRPEF 23%/33%/43%, deduzione fondo pensione €5.300, coefficienti trasformazione 2025-2026
- Profilo coperto: lavoratore dipendente privato

**v0.2**:
- Gestione completa aliquota 12,5% con coefficiente di abbattimento (`references/aliquote-12-5-26.md`)
- Gestione multi-intermediario con escape hatch regime dichiarativo (`references/multi-intermediario.md`)
- Schema CSV input esteso con colonna `broker` obbligatoria e `aliquota` opzionale
- Pattern D: raccomandazione passaggio a dichiarativo con quantificazione delta vs costi
- Edge case ETF UCITS su titoli di Stato: aliquota mista
- Workflow di analisi separato per-broker + aggregato cross-broker

**v0.1** (iniziale):
- Skill `it-tax-optimization` con tre pattern (consumo zainetto, creazione zainetto, non operare)
- Regole asimmetria reddito diverso vs reddito di capitale (art. 67 vs art. 44 TUIR)
- LIFO obbligatorio, no wash sale, scadenza zainetto 4 anni
- Reference dedicata alla trappola ETF UCITS armonizzati
- Slash command `/minusvalenze`

Roadmap di skill nel fork (stato corrente):

| # | Skill upstream | Skill fork | Stato |
|---|---|---|---|
| 1 | `tax-loss-harvesting` | `it-tax-optimization` | ✅ v0.10 (minus/plus, multi-broker, dichiarativo RT/RW/IVAFE, Tobin tax 2026, cripto: base + avanzata + casi speciali) + importatore estratti broker |
| 2 | `financial-plan` | `it-pianificazione` | ✅ v0.11 (pensione dipendenti, importatore estratto INPS + fondo, proiezione INPS parametrica con sensibilità, Monte Carlo tasso sostituzione) |
| 2b | `financial-plan` | `it-pianificazione-autonomi` | ✅ v0.3 (pensione autonomi/forfettari, casse professionali, Excel) |
| 2c | `financial-plan` + `investment-proposal` | `it-pianificazione-obiettivi` | ✅ v0.19 (goals-based, allocatore di capitale con split + 6 profili, Monte Carlo onesto + leva di rischio, glide path, asset location, decumulo) |
| 3 | `portfolio-rebalance` | `it-rebalance` | ✅ v0.6 (tax-aware con versamenti, aliquota per posizione e rientro misto, multi-broker, bande 5/25, prelievo in decumulo, sequenza di liquidazione, ordini CSV) |
| 4 | `client-review` + `client-report` + `investment-proposal` (IPS) | `it-revisione` | ✅ v0.6 (revisione di sintesi, template report, tracker azioni, **generatore IPS in Word**, Excel, TWR) |

Le sei skill attive formano un sistema coordinato attorno a un flusso end-to-end: `it-pianificazione-obiettivi` definisce gli obiettivi e le allocazioni (a monte), le due skill previdenziali coprono il secchiello pensione, `it-rebalance` mantiene le allocazioni nel tempo, `it-tax-optimization` ottimizza la fiscalità delle vendite, e `it-revisione` è il **livello di sintesi** che una volta l'anno tiene insieme tutto in un quadro unico con azioni prioritizzate. Vedi la sezione "Architettura" sotto. Note: il goals-based, che nell'upstream è spezzato tra `financial-plan` (modellazione obiettivi) e `investment-proposal` (allocazione/IPS), nel fork è unificato in `it-pianificazione-obiettivi` con postura personale/educativa; e le skill upstream rivolte al consulente (`client-review`, `client-report`, in parte `investment-proposal`) sono riformulate per chi gestisce i propri soldi nell'unica `it-revisione`.

## Installazione

### Prerequisiti

Python 3.11 o successivo (la CI prova 3.11 e 3.14) con le dipendenze degli script: `pip install "numpy>=1.26" "openpyxl>=3.1" "python-docx>=1.1"` (oppure `pip install -r tests/requirements.txt`, lo stesso file usato dalla CI).

### Claude Code

Il repository include `.claude-plugin/marketplace.json`, quindi è esso stesso un marketplace installabile. Tre vie (procedura verificata sulla documentazione ufficiale, luglio 2026):

```bash
# A) Uso quotidiano — da GitHub (consigliata: aggiornamenti con un comando)
#    dentro una sessione Claude Code:
/plugin marketplace add eugeniorende/wealth-management-it
/plugin install wealth-management-it@wm-it

# B) Solo locale — senza GitHub (path assoluto della directory del plugin)
/plugin marketplace add /percorso/assoluto/wealth-management-it
/plugin install wealth-management-it@wm-it

# C) Sviluppo — carica il plugin senza installarlo (sessione usa-e-getta)
claude --plugin-dir /percorso/assoluto/wealth-management-it
```

**Nota sul caching**: l'installazione COPIA il plugin nella cache di Claude Code (`~/.claude/plugins/`). Non modificare la copia in cache: le modifiche si fanno nel repository e si propagano con `/plugin marketplace update wm-it` seguito dalla reinstallazione (via A) o riavviando la sessione (via C).

### Cartella di lavoro (importante)

Il plugin fornisce skill e script; i **tuoi dati vivono altrove**. Crea una cartella dedicata al piano (es. `~/piano-finanziario/`) e lavora sempre da lì: metti lì i file reali (estratto conto INPS, storico del fondo, CSV dei broker), **copia** lì gli Excel da compilare (`pianificatore-obiettivi.xlsx`, `tracker-secchielli.xlsx`, `cruscotto-patrimoniale.xlsx`, `investment-policy-statement.xlsx`, `proiezione-pensione.xlsx` o `proiezione-pensione-autonomi.xlsx` — mai editare quelli dentro il plugin), e lì finiranno gli output degli script (JSON della pipeline, CSV degli ordini, l'IPS generato). Il plugin resta immutabile e aggiornabile; la cartella di lavoro è la tua.

### Dove vanno i tuoi dati

Gli script del plugin girano **in locale** e non fanno chiamate di rete: leggono i file che indichi e scrivono gli output (JSON, CSV degli ordini, IPS in Word) nella cartella da cui li lanci. Però tutto ciò che scrivi in chat, che Claude legge dai tuoi file e che gli script stampano **entra nel contesto del modello** e nei transcript della sessione: in Claude Code i transcript restano sul tuo computer (`~/.claude/projects/`), in Cowork e su claude.ai sono gestiti secondo le impostazioni del tuo account Anthropic.

Cosa conviene sapere:
- `importa-previdenza.py` legge l'estratto conto INPS e il prospetto del fondo pensione. Di default stampa intestatario e data di nascita, da cui calcola l'età; con `--anonimo` li omette e stampa l'età arrotondata all'anno. Le retribuzioni le stampa aggregate per anno, senza i datori di lavoro;
- gli estratti dei broker contengono posizioni e importi; prima di passarli, togli quello che al calcolo non serve: intestatario, codice fiscale, IBAN, numero di dossier;
- per i calcoli bastano età, importi e date: nomi e identificativi non servono a nessuno strumento del plugin.

### Verifica

Dal repository: `python tests/run_tests.py` (40 test, circa 15 secondi, richiede le dipendenze dei Prerequisiti). Tre test ricalcolano gli Excel con LibreOffice headless in locale italiano (`scripts/ricalcola-excel.py`): verificano che nessuna cella vada in errore e che le cache salvate nei file coincidano col ricalcolo. Senza LibreOffice risultano saltati; nella CI è installato e obbligatorio (`RICHIEDI_LIBREOFFICE=1`). Dopo aver modificato un Excel, `python scripts/ricalcola-excel.py FILE --in-place` ne aggiorna le cache. `--only NOME` e `--skip NOME` filtrano i test per sottostringa del nome. La stessa suite gira come GitHub Action (`.github/workflows/tests.yml`) a ogni push su `main`/`develop` e su ogni pull request, escluso il test di freshness fiscale (vedi sotto): il badge in cima al README ne riporta lo stato.

### Cowork

Settings → Plugins → Add plugin → Upload a zip. Lo zip pronto (`wealth-management-it-vX.Y.Z.zip`) è allegato a ogni [GitHub Release](https://github.com/eugeniorende/wealth-management-it/releases); in alternativa si costruisce dal repository con `python scripts/pacchetto.py` (finisce in `dist/`). Contiene solo manifest, comandi, skill e README, sotto la cartella `wealth-management-it/`.

## Uso

Comandi espliciti:

```
/obiettivi         → it-pianificazione-obiettivi (pianificazione goals-based multi-obiettivo)
/minusvalenze      → it-tax-optimization (ottimizzazione minus/plus, zainetto)
/pensione          → it-pianificazione (pensione dipendenti: INPS + complementare + TFR)
/pensione-autonomi → it-pianificazione-autonomi (pensione autonomi/forfettari: Gestione Separata)
/ribilancia        → it-rebalance (ribilanciamento tax-aware del portafoglio)
/revisione         → it-revisione (revisione periodica: stato, scostamenti, azioni)
```

Trigger automatico: ogni skill si attiva sui propri argomenti. `it-pianificazione-obiettivi` su obiettivi/pianificare investimenti/fondo emergenza/quanto risparmiare; `it-tax-optimization` su minusvalenze/plusvalenze/zainetto/Tobin tax; `it-pianificazione` su pensione/fondo pensione/TFR per dipendenti; `it-pianificazione-autonomi` su pensione/Gestione Separata/forfettario per P.IVA; `it-rebalance` su ribilanciamento/drift/allocazione target.

### Input richiesto

L'utente deve fornire:

1. **Snapshot portafoglio** in CSV o testo (l'estratto CSV del broker si legge con `skills/it-tax-optimization/assets/importa-estratto-broker.py`, che classifica le posizioni, esclude le minus scadute e incrocia lo zainetto broker per broker). Schema:
   ```
   isin,descrizione,quantita,pmc,prezzo_corrente,categoria_fiscale
   IE00B4L5Y983,iShares Core MSCI World,100,75.20,89.50,reddito_capitale
   IT0003132476,ENI,500,12.40,14.80,reddito_diverso
   ```

2. **Stato zainetto fiscale** (scaricabile da quasi tutti i broker italiani come "rendiconto fiscale annuale"):
   ```
   anno_realizzo,importo_residuo,aliquota
   2022,4500,26
   2023,1200,26
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

1. Da `develop`, aprire un release branch e allineare la versione in `.claude-plugin/plugin.json` e `marketplace.json` (il test di igiene e lo script di packaging la verificano) con la voce di changelog qui sopra.
2. Pull request del release branch su `main`; la CI (`tests` + `validate`) deve essere verde.
3. Dopo il merge, tag `vX.Y.Z` su `main` e push del tag. Il workflow `release.yml` rifiuta un tag diverso dalla versione del manifest, esegue la suite **completa, freshness inclusa** (non si rilascia con dati normativi scaduti), costruisce lo zip e crea la GitHub Release con le note generate dai commit.
4. Merge back di `main` su `develop`.

Il workflow si può avviare a mano senza tag (Actions → release → Run workflow): costruisce lo zip come artifact del run senza creare la release, utile per collaudarlo.

## Licenza

Apache-2.0: il testo è in [LICENSE](LICENSE), l'attribuzione all'upstream e le modifiche sono in [NOTICE](NOTICE). Entrambi i file entrano nello zip di release. Il progetto è nato come fork del plugin `wealth-management` di anthropics/financial-services (commit `ef165e4160`), ma skill, comandi, script ed Excel sono stati riscritti da zero per la fiscalità italiana: il confronto con l'upstream non trova righe di testo in comune.

## Disclaimer (di nuovo, perché conta)

Questo plugin produce **bozze di analisi fiscale personale**. Non è consulenza professionale. L'autore e gli eventuali contributor non si assumono responsabilità per decisioni operative basate sull'output. Verificare sempre con il proprio commercialista e con il portale dell'intermediario.
