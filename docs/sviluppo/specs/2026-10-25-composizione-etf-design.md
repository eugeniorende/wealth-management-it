# Importatore della composizione degli ETF (design)

Stato: spec da rivedere, 25/10/2026. Nasce dal brainstorming con il proprietario sulla richiesta «parti dall'importatore della composizione degli ETF», la voce ad alta priorità di **T16 Fonti dati esterne e connettori** in ROADMAP.

> ⚠️ Come il resto del plugin: strumento di pianificazione personale, non consulenza finanziaria o fiscale.

## 1. Obiettivo e perimetro

**Cosa si vuole.** Oggi `capitale-umano.py --composizione` legge un CSV `strumento;settore;peso` che l'utente compila a mano dalla scheda dell'ETF. L'importatore legge invece il **file delle posizioni** (holdings) che l'utente scarica dal sito dell'emittente, aggrega i titoli per **settore GICS** e per **paese**, e scrive `composizione.csv`. Lo script resta offline, come da principio di T16: il dato si procura a parte e lo script legge un file locale.

**Decisioni prese nel brainstorming:**

| # | Decisione | Scelta |
|---|---|---|
| D1 | Cosa produce | Settori **e** paesi (opzione B). Il report di look-through dell'intero portafoglio (opzione C) è un'evolutiva tracciata (§8) |
| D2 | Lingue dei file | Italiano e inglese, con tabelle di sinonimi. Tedesco e francese sono un'evolutiva tracciata (§8) |
| D3 | Chiave del paese | Codice ISO 3166-1 alpha-2 nel CSV, nome italiano solo nel report. Un paese non riconosciuto è un errore, non si indovina |
| D4 | Legame con la posizione | `--strumento NOME` obbligatorio per ogni file, lo stesso testo del campo `strumento` delle posizioni. L'ISIN come chiave arriva con l'evolutiva C |
| D5 | Architettura | Approccio 1: motore generico con tabelle di sinonimi e una piccola scheda per emittente (non un parser per emittente, non un motore senza schede) |
| D6 | Classificazioni non GICS | Nessuna conversione ICB → GICS: per un file in ICB si scrivono i paesi, si saltano i settori e lo si dice con un avviso |

**Fuori perimetro (YAGNI):** report di look-through del portafoglio (C); ISIN come chiave; tedesco e francese; conversione ICB → GICS; valuta come terza dimensione; download dei file (lo fa l'utente, o Claude nella cartella di lavoro, mai lo script); un comando dedicato (arriva con C); le altre fonti di T16 (BCE, ISTAT, NASpI, French, MSCI).

## 2. Componenti

| File | Cosa fa |
|---|---|
| `skills/it-pianificazione-obiettivi/assets/importa-composizione-etf.py` | Nuovo. Legge uno o più file delle posizioni, scrive o aggiorna `composizione.csv`, stampa il report, `--json` facoltativo |
| `skills/it-pianificazione-obiettivi/assets/capitale-umano.py` | `leggi_composizione()` accetta anche il nuovo formato con la colonna `dimensione` (§3.3) |
| `skills/it-pianificazione-obiettivi/references/composizione-etf.md` | Nuova reference: come scaricare il file per emittente, cosa si esclude e perché, limiti, licenza |

Accanto al consumatore (`capitale-umano.py`), nella stessa skill. Usa `cli()`, `errore()`, `numero()`, `pct()` e `scrivi_json()` di `motore_bootstrap.py`; legge gli XLSX con `openpyxl`, già tra le dipendenze.

### 2.1 Interfaccia

```
python "${CLAUDE_SKILL_DIR}/assets/importa-composizione-etf.py" \
    --file swda.csv --strumento "ETF MSCI World" \
    [--file xdem.xlsx --strumento "ETF Momentum" ...] \
    [--emittente ishares|xtrackers|vanguard|amundi|spdr] \
    [--out composizione.csv] [--json FILE|-]
```

- `--file` e `--strumento` in coppia, ripetibili, appaiati per posizione. Numero diverso → errore di riga di comando (rc 2). Uno stesso `--strumento` ripetuto → rc 2.
- `--emittente`: forza la scheda per tutti i file della chiamata, quando il riconoscimento automatico fallisce o sbaglia.
- `--out FILE` (default `composizione.csv` nella cartella corrente): se esiste, si **sostituiscono solo le righe e il commento degli strumenti importati**; le altre righe, comprese quelle compilate a mano nel vecchio formato, restano (§3.2).
- `--json FILE|-`: il risultato strutturato (§3.4).
- Interfaccia comune degli script (T9): `--help`; exit 0 riuscito, 1 errore nei dati con `ERRORE:` su stderr, 2 riga di comando errata; UTF-8 su qualunque console; numeri in formato italiano nel report.
- **Niente mezzo output**: tutti i file si leggono e si validano prima di scrivere `--out` e `--json`; un errore su un file lascia `composizione.csv` com'era.

## 3. Formati

### 3.1 `composizione.csv` (nuovo formato)

```
# ETF MSCI World: iShares, swda.csv, posizioni al 30/09/2026, importato il 25/10/2026; esclusi liquidità e derivati 0,40%, settore non classificato 0,05%
strumento;dimensione;voce;peso
ETF MSCI World;settore;Information Technology;26,84
ETF MSCI World;settore;Financials;16,90
ETF MSCI World;paese;US;71,20
ETF MSCI World;paese;JP;5,40
```

- `dimensione`: `settore` o `paese`.
- `voce`: per i settori uno degli 11 nomi GICS inglesi di `SETTORI_GICS` in `capitale-umano.py`; per i paesi un codice ISO alpha-2 maiuscolo.
- `peso`: percento, virgola decimale, due decimali, **rinormalizzato a 100 per dimensione** dopo le esclusioni (§4.5). L'arrotondamento a due decimali può lasciare la somma a 100 ± 0,05: il lettore già tollera il 2%.
- Righe ordinate per strumento (ordine di prima comparsa nel file), poi dimensione (settore, paese), poi peso decrescente.
- Separatore `;`, UTF-8 con BOM, come il CSV degli ordini: si apre in Excel italiano.
- Una riga di commento per strumento, subito prima delle sue righe, con emittente, nome del file, data delle posizioni (se nota), data d'importazione e quote escluse.

### 3.2 Fusione con un file esistente

- Si legge `--out` se esiste, nel vecchio o nel nuovo formato. Il vecchio (`strumento;settore;peso`) si converte nel nuovo (`dimensione = settore`, pesi riportati in percento) e si riscrive nel nuovo: chi lancia l'importatore accetta il formato nuovo, e il report lo dice.
- Per ogni strumento importato si tolgono le sue righe e il suo commento e si aggiungono quelle nuove, in fondo. Gli altri strumenti e i commenti che non appartengono a uno strumento importato restano nell'ordine in cui erano.
- Un `--out` illeggibile (colonne sconosciute) → `ERRORE:` e nessuna scrittura: non si sovrascrive un file che non si capisce.

### 3.3 Lettura in `capitale-umano.py`

`leggi_composizione()` accetta i due formati, riconosciuti dalle colonne:

- vecchio `strumento;settore;peso`: comportamento invariato (stessi numeri di oggi, vincolati da un test);
- nuovo `strumento;dimensione;voce;peso`: legge solo le righe con `dimensione = settore`, con le stesse validazioni (settore GICS, peso numerico, somma a 100% con tolleranza 2%). Le righe `paese` si ignorano. Un valore di `dimensione` diverso da `settore` e `paese` → `ERRORE:`.

Uno strumento con le sole righe `paese` (il caso ICB) non entra nella composizione settoriale e finisce tra i «Senza composizione, esclusi dal calcolo», come oggi gli strumenti mancanti. `esempio-composizione.csv` resta nel vecchio formato: è il caso d'uso «compilato a mano», e il test di compatibilità lo usa.

### 3.4 `--json`

```json
{
  "strumenti": [
    {"strumento": "ETF MSCI World", "emittente": "ishares", "riconosciuto_da": "preambolo",
     "file": "swda.csv", "data_posizioni": "2026-09-30", "classificazione": "GICS",
     "colonne": {"peso": "Weight (%)", "settore": "Sector", "paese": "Location", "asset_class": "Asset Class"},
     "titoli": 1320,
     "esclusi": {"liquidita_derivati": 0.004, "settore_non_classificato": 0.0005, "paese_non_classificato": 0.0},
     "settori": {"Information Technology": 0.2684, "...": 0.0},
     "paesi": {"US": 0.712, "...": 0.0},
     "avvisi": []}
  ],
  "out": "composizione.csv"
}
```

Pesi in frazione, come negli altri JSON del plugin; `data_posizioni` ISO o `null`; `settori` vuoto (`{}`) con `classificazione: "ICB"` o quando il file non ha la colonna del settore. È la base che l'evolutiva C leggerà con `--from`.

### 3.5 Report a terminale

Per ogni strumento: emittente e come è stato riconosciuto (preambolo, nome del file, `--emittente`, nessuno); data delle posizioni; le intestazioni lette per peso, settore e paese (per esempio `Trade Country Name`); titoli letti; quote escluse; i primi 5 settori con il nome italiano (`SETTORI_GICS`) e i primi 5 paesi con il nome italiano; gli avvisi. In fondo il percorso di `--out` e, se c'era, cosa si è conservato (strumenti non toccati) e se il file è stato convertito dal vecchio formato.

## 4. Lettura dei file

### 4.1 Apertura

- `.xlsx`: `openpyxl` in sola lettura con `data_only=True`, primo foglio con dati (gli emittenti ne esportano uno). I numeri arrivano già come numeri.
- `.csv` e `.txt`: decodifica UTF-8 con BOM, ripiego su cp1252 (come `leggi_composizione()`); separatore riconosciuto tra `,`, `;` e tab con `csv.Sniffer` sulle righe dopo il preambolo, con ripiego sul separatore più frequente nella riga d'intestazione.
- Altre estensioni (`.xls`, `.pdf`, `.html`) e file che sono una pagina HTML (iniziano con `<!doctype` o `<html`: il sito ha restituito la pagina invece del file) → `ERRORE:` con l'indicazione di esportare in XLSX o CSV dal pulsante di download delle posizioni.

### 4.2 Riga d'intestazione

Nelle prime 40 righe, la prima riga che contiene una colonna di **peso** e almeno una tra **settore** e **paese**, riconosciute dai sinonimi. Confronto dopo normalizzazione: minuscole, accenti tolti, spazi e punteggiatura compressi (lo stesso criterio di `importa-estratto-broker.py`).

| Ruolo | Sinonimi iniziali (italiano e inglese) |
|---|---|
| peso | `weight (%)`, `weight`, `weighting`, `percent of fund`, `% of net assets`, `% of fund`, `market value weight`, `ponderazione (%)`, `ponderazione`, `peso (%)`, `peso`, `% del patrimonio` |
| settore | `sector`, `gics sector`, `sector classification`, `industry classification`, `settore`, `settore gics` |
| paese | `location`, `country`, `trade country name`, `country of risk`, `domicile`, `area geografica`, `paese`, `nazione` |
| asset class | `asset class`, `type of security`, `security type`, `asset type`, `classe di attivo`, `tipo di strumento` |
| nome | `name`, `security name`, `holding name`, `nome`, `titolo`, `emittente` |

Con due colonne candidate per lo stesso ruolo vale la prima della tabella dei sinonimi (per esempio in SPDR `sector classification` batte `industry classification`, che lì è il livello GICS sotto il settore). Le righe sopra l'intestazione sono il **preambolo**. La tabella finisce alla prima riga vuota dopo almeno una riga di dati, o alla prima riga senza peso numerico né `N/A`: quello che segue (disclaimer, note legali) si scarta.

Nessuna intestazione trovata → `ERRORE:` che elenca le celle non vuote delle prime righe viste e ricorda di scaricare il file delle **posizioni** (holdings), non la scheda prodotto (factsheet) né il KID.

### 4.3 Scheda dell'emittente

Una tabella di dati nello script, non codice per emittente. Per ciascuno dei cinque:

| Campo | Cosa contiene |
|---|---|
| `riconosci` | Parole cercate nel preambolo e nel nome del file: `ishares`/`blackrock`; `xtrackers`/`dws`; `vanguard`; `amundi`/`lyxor`; `spdr`/`state street`/`ssga` |
| `classificazione` | `GICS` per iShares, Xtrackers, Amundi e SPDR; per Vanguard `GICS` o `ICB` secondo il file reale (§4.7) |
| `etichette_data` | Etichette della data nel preambolo: `fund holdings as of`, `holdings as of`, `as of`, `posizioni al`, `dati al`; per Xtrackers il titolo del foglio (`2026-10-25`) |
| `liquidita` | Valori della colonna asset class che indicano liquidità e derivati (§4.5), in aggiunta a quelli generici |
| `verificato` | Il mese e la fonte della verifica del layout su un file reale, o `da confermare` |

Riconoscimento: `--emittente` se dato; altrimenti la prima scheda le cui parole compaiono nel preambolo; altrimenti nel nome del file; altrimenti nessuna scheda, regole generiche e avviso «emittente non riconosciuto: regole generiche, controlla le esclusioni». Data delle posizioni: dalla cella accanto all'etichetta, nei formati `30/09/2026`, `30-Sep-2026`, `30/set/2026`, `2026-09-30`, `Sep 30, 2026`; non trovata → `null` e nessun avviso (non tutti i file la riportano).

**Stato dei layout a oggi.** Verificati su file reali scaricati il 25/10/2026 dal sito dell'emittente:

- **Xtrackers** (XLSX, sito britannico in inglese): disclaimer in riga 2, intestazione in riga 4 (`Name`, `ISIN`, `Country`, `Currency`, `Exchange`, `Type of Security`, `Rating`, `Primary Listing`, `Industry Classification`, `Weighting`), peso in **frazione**, data nel titolo del foglio, righe con settore `unknown` e peso `N/A`, `Type of Security` con `Equities`, `Future`, `Warrants`.
- **SPDR** (XLSX, sito EMEA in inglese): preambolo con `Fund Name:`, `ISIN:`, `Ticker Symbol:`, `Holdings As Of: 22-Oct-2026`; intestazione in riga 6 (`ISIN`, `SEDOL`, `Security Name`, `Currency`, `Number of Shares`, `Percent of Fund`, `Trade Country Name`, `Local Price`, `Sector Classification`, `Industry Classification`, `Base Market Value`); peso in **percento**; righe `Unassigned` (settore e paese) con pesi negativi per i contratti di cambio; disclaimer in fondo.

**Da confermare su un file reale** (dalla sessione cloud i siti restituiscono la pagina HTML o un 404, non il file): iShares (sito italiano e britannico), Vanguard e Amundi. Il proprietario ne fornisce due o tre nella cartella di lavoro, fuori dal repository; fino ad allora le schede portano `verificato: da confermare` e i sinonimi coprono i formati documentati (iShares: `Ticker`, `Name`, `Sector`, `Asset Class`, `Market Value`, `Weight (%)`, `Location`, … e, dal sito italiano, `Settore`, `Asset class`, `Ponderazione (%)`, `Area geografica`).

### 4.4 Numeri

- Il formato decimale si decide per file sulla colonna del peso, come in `importa-estratto-broker.py`: se compare una virgola decimale il file è all'italiana e `1.000` vale mille; negli XLSX i numeri arrivano già come numeri. Il segno `%` in coda si toglie.
- La **scala** si decide dalla somma dei pesi delle righe di titoli, prima delle esclusioni di righe non classificate: tra 0,9 e 1,1 → frazione; tra 90 e 110 → percento. Fuori da entrambi → `ERRORE:` («i pesi sommano a X: file troncato o colonna sbagliata?»).
- Un peso non numerico che non sia un segnaposto (`N/A`, `-`, `n.d.`, vuoto) → `ERRORE:` con riga e valore.

### 4.5 Righe escluse

Ogni esclusione si conta in quota del fondo e si riporta nel report, nel commento del CSV e nel JSON.

1. **Liquidità e derivati**: asset class tra i valori generici (`cash`, `cash and/or derivatives`, `cash collateral and margins`, `money market`, `fx`, `futures`, `future`, `forward`, `swap`, `liquidita`, `derivati`, `contanti`) o tra quelli della scheda; oppure settore del tipo `cash and/or derivatives`; oppure **peso negativo**. Escluse da entrambe le dimensioni.
2. **Peso segnaposto** (`N/A`, `-`, vuoto): la riga non ha peso, si conta nel numero di righe scartate ma non nelle quote.
3. **Non classificate**, separatamente per dimensione: settore o paese `unknown`, `unassigned`, `other`, `-`, `n/a`, `non classificato`, `altro`, vuoto. Una riga con il paese ma senza settore conta nei paesi e non nei settori.
4. Avviso se le non classificate superano il **5%** del fondo in una dimensione, e se liquidità e derivati superano il **5%** (un ETF sintetico o un file con il collaterale: la composizione potrebbe non descrivere l'esposizione).

I pesi rimasti si **rinormalizzano a 100** per dimensione. Nessuna riga valida in una dimensione → quella dimensione resta vuota con un avviso; in entrambe → `ERRORE:`.

### 4.6 Settori e paesi

- **Settori**: sinonimi in italiano e in inglese verso gli 11 nomi GICS. Per esempio `Informatica`, `Tecnologia dell'informazione` → `Information Technology`; `Finanza`, `Finanziari` → `Financials`; `Sanità`, `Salute` → `Health Care`; `Beni voluttuari`, `Beni di consumo discrezionali` → `Consumer Discretionary`; `Beni di prima necessità` → `Consumer Staples`; `Servizi di comunicazione`, `Comunicazioni` → `Communication Services`; `Industriali`, `Industria` → `Industrials`; `Materiali`, `Materie prime` → `Materials`; `Servizi di pubblica utilità` → `Utilities`; `Immobiliare` → `Real Estate`; `Energia` → `Energy`. `Telecommunication Services` (GICS prima del 2018) → `Communication Services` con un avviso, perché il perimetro non è identico.
- **Paesi**: sinonimi verso ISO alpha-2 per i paesi dei mercati sviluppati ed emergenti degli indici MSCI ACWI IMI e FTSE All-World, più i domicili frequenti nei file (Irlanda, Lussemburgo, Paesi Bassi, Bermuda, Isole Cayman, Jersey, Guernsey, Curaçao, Panama, Liberia, Isola di Man, Macao). Varianti incluse: `United States`/`USA`/`Stati Uniti`; `United Kingdom`/`UK`/`Great Britain`/`Regno Unito`; `Korea (South)`/`Korea, Republic of`/`South Korea`/`Corea del Sud`; `Hong Kong`/`Hong Kong SAR`; `Taiwan`/`Taiwan, Province of China`; `Russian Federation`/`Russia`; `Czech Republic`/`Czechia`/`Repubblica Ceca`; `Türkiye`/`Turkey`/`Turchia`. Il nome italiano del report viene dalla stessa tabella.
- **Non riconosciuti** → `ERRORE:` con l'elenco di **tutti** i nomi non riconosciuti del file, ciascuno con il peso, e l'indicazione di segnalarli: non si indovina, non si mette in «altro».

### 4.7 Classificazione ICB

Molti nomi sono comuni ai due sistemi (`Financials`, `Health Care`, `Industrials`, `Energy`, `Utilities`, `Real Estate`, `Consumer Staples`, `Consumer Discretionary`), quindi decidono solo quelli esclusivi: ICB `Technology`, `Telecommunications`, `Basic Materials`; GICS `Information Technology`, `Communication Services`, `Materials`. Se la scheda dice `ICB`, o se il file ha almeno un nome esclusivo ICB e nessuno esclusivo GICS, la dimensione `settore` si salta: si scrivono solo i paesi, `classificazione: "ICB"`, avviso «classificazione ICB, non convertibile in GICS senza errore: settori non scritti, il capitale umano tratterà lo strumento come senza composizione settoriale». Il riconoscimento dai nomi serve solo se la scheda non lo dice; un file misto (nomi esclusivi di entrambi i sistemi) → `ERRORE:`.

## 5. Flusso nelle skill

1. L'utente scarica il file delle posizioni dalla pagina dell'ETF sul sito dell'emittente (pulsante «Posizioni», «Holdings», «Portafoglio completo»), oppure chiede a Claude di scaricarlo nella cartella di lavoro.
2. `importa-composizione-etf.py --file … --strumento …` scrive `composizione.csv`.
3. `capitale-umano.py --dati … --composizione composizione.csv` usa la composizione per la diagnosi 4.

Nella `SKILL.md` di it-pianificazione-obiettivi lo Step 8 aggiunge il passo 2 prima di `capitale-umano.py`, ricordando che `--strumento` va scritto come il campo `strumento` delle posizioni; l'elenco degli asset aggiunge lo script. `commands/capitale-umano.md` lo cita. `it-revisione/SKILL.md`, nella riga del contratto di input sul capitale umano, cita l'importatore come fonte di `--composizione`.

## 6. File

| File | Cambio |
|---|---|
| `skills/it-pianificazione-obiettivi/assets/importa-composizione-etf.py` | Nuovo |
| `skills/it-pianificazione-obiettivi/assets/capitale-umano.py` | `leggi_composizione()` con i due formati |
| `skills/it-pianificazione-obiettivi/references/composizione-etf.md` | Nuova: dove si scarica il file per emittente, formati, esclusioni, limiti, licenza |
| `skills/it-pianificazione-obiettivi/references/capitale-umano.md` | Paragrafo su `--composizione`: prima l'importatore, la compilazione a mano come alternativa |
| `skills/it-pianificazione-obiettivi/SKILL.md` | Step 8, elenco degli asset e delle reference |
| `commands/capitale-umano.md` | Accenno all'importatore |
| `skills/it-revisione/SKILL.md` | Riga del contratto di input sul capitale umano |
| `tests/run_tests.py`, `tests/fixtures/composizione-*.csv` | Test di §7 |
| `README.md` | Conteggio dei test, tabella strumenti ↔ test rigenerata, script nell'elenco degli strumenti |
| `CHANGELOG.md` | Voce sotto «Non rilasciato» |
| `ROADMAP.md` | T16: la voce della composizione degli ETF spuntata; le evolutive di §8 |

## 7. Test (TDD, prima del codice)

Nomi `T16 composizione ETF: …`. Le fixture sono sintetiche: i file degli emittenti non si ridistribuiscono. Riproducono il layout reale (§4.3) con 8-12 titoli inventati; i CSV stanno in `tests/fixtures/`, gli XLSX li genera il test con `openpyxl` in una cartella temporanea, così il layout si legge nel codice del test e nel repository non entrano binari.

1. **Valori chiusi per emittente**: Xtrackers (XLSX, frazione, `unknown`, `N/A`, `Future`), SPDR (XLSX, percento, preambolo con data, `Unassigned` con peso negativo, disclaimer in fondo), iShares inglese (CSV con `,`, preambolo di righe di testata) e iShares italiano (CSV con `;` e virgola decimale, intestazioni e settori in italiano). Per ciascuno: pesi per settore e per paese al centesimo dopo esclusione e rinormalizzazione, quote escluse, numero di titoli, data delle posizioni, emittente riconosciuto.
2. **Riconoscimento**: dal preambolo, dal nome del file, da `--emittente` (che vince sul preambolo); emittente sconosciuto con colonne note → rc 0 con l'avviso.
3. **Errori, rc 1 con il messaggio**: pagina HTML al posto del file; scheda prodotto senza intestazione delle posizioni (il messaggio elenca le celle viste); settori e paesi sconosciuti (tutti elencati, non solo il primo); somma dei pesi incoerente; peso non numerico; file misto GICS e ICB; nessuna riga valida. In tutti i casi `--out` non è stato toccato (contenuto e data di modifica invariati).
4. **Riga di comando, rc 2**: `--file` e `--strumento` spaiati; stesso `--strumento` ripetuto.
5. **ICB**: un file Vanguard sintetico in ICB scrive solo i paesi, con `classificazione: "ICB"` e l'avviso.
6. **Soglie**: non classificate sopra il 5% e liquidità sopra il 5% → avvisi; sotto → nessun avviso.
7. **Fusione**: `composizione.csv` con uno strumento nel vecchio formato e uno importato; reimportare il secondo ne sostituisce righe e commento, il primo è convertito nel nuovo formato con gli stessi pesi; nessuna riga duplicata.
8. **Formato del CSV**: BOM, `;`, virgola decimale, due decimali, ordinamento, somma per dimensione entro 100 ± 0,05; il file si rilegge con `csv` senza perdite.
9. **Catena con il capitale umano**: importatore → `composizione.csv` → `capitale-umano.py --composizione --json` dà la `quota_settore_fin` calcolata a mano sulla fixture; con `esempio-composizione.csv` (vecchio formato) i numeri sono identici a quelli di prima della modifica; uno strumento con i soli paesi finisce in `mancanti`; `dimensione` sconosciuta → rc 1.
10. **`--json`**: le chiavi di §3.4 (con `colonne`), pesi in frazione che sommano a 1 per dimensione, `-` scrive su stdout.
11. **Mutanti**, verbalizzati come in T12 e T15: rinormalizzazione tolta, pesi negativi non esclusi, scala frazione/percento invertita, prima colonna candidata ignorata (in SPDR vince `Industry Classification`). Ognuno deve far fallire almeno un test.

I test di igiene esistenti coprono già `--help`, flag ignoto, UTF-8 e cp1252, formati italiani negli output e Windows; la tabella strumenti ↔ test del README si rigenera con `--tabella-test` e il conteggio dei test si aggiorna.

## 8. ROADMAP

Sotto T16 la riga «Composizione degli ETF per settore e paese» diventa una voce spuntata, con spec e piano; si aggiungono due evolutive da decidere:

- **C — Look-through del portafoglio**: report di settori, paesi e primi titoli aggregati su tutti gli ETF posseduti, pesati per controvalore, con `--json` per `it-revisione` e una sezione del cruscotto (T17). Le posizioni arrivano dall'estratto del broker (`importa-estratto-broker.py --json`), con l'**ISIN** come chiave al posto di `--strumento`; `capitale-umano.py` impara il campo `isin` delle posizioni. Richiede di conservare nel JSON dell'importatore anche i primi titoli per peso.
- **Lingue tedesca e francese**: sinonimi delle intestazioni, dei settori e dei paesi per gli export di Xtrackers e Amundi dai siti tedesco e francese; solo dati nelle tabelle, nessun cambio al motore.

## 9. Limiti dichiarati

- **Posizioni del fondo, non dell'indice**: un ETF a replica campionaria o sintetica (swap) espone posizioni diverse dall'indice; per gli ETF sintetici il file può contenere il paniere di collaterale, che non descrive l'esposizione. L'avviso sulla liquidità sopra il 5% lo segnala, ma non lo risolve.
- **Fotografia a una data**: la composizione cambia; la data delle posizioni sta nel commento del CSV e va riguardata a ogni revisione annuale.
- **GICS soltanto**: nessuna conversione da ICB; un ETF Vanguard su indice FTSE, se il file è in ICB, contribuisce solo con i paesi.
- **Paese secondo l'emittente**: domicilio, paese di rischio o di quotazione a seconda del file (SPDR usa il paese di negoziazione). Il report dice quale colonna è stata letta.
- **Licenza**: i file degli emittenti sono soggetti alle loro condizioni d'uso; il plugin non li scarica né li ridistribuisce, l'utente li tiene nella propria cartella di lavoro.
