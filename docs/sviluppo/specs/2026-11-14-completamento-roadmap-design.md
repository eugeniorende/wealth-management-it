# Completamento della roadmap: programma a ondate e ciclo 0.13.0 (design)

Stato: spec da rivedere, 14/11/2026. Nasce dalla richiesta del proprietario dopo la 0.12.0: «voglio completare le attività rimaste aperte» della ROADMAP. Contiene il **programma intero** (§5) e il design di dettaglio delle **ondate 0 e 1**, che insieme fanno la 0.13.0 (§6 e §7). Per le ondate 2, 3 e 4 fissa solo l'impianto (§8): ognuna avrà la sua spec prima del piano.

> ⚠️ Come il resto del plugin: strumento di pianificazione personale, non consulenza finanziaria, fiscale o previdenziale.

## 1. Intento

Dopo la 0.12.0 la ROADMAP ha ancora quindici sviluppi «da decidere» (due del cruscotto, tre del look-through, quattro del capitale umano, sei fonti dati) e un calendario di parametri da riverificare. Il proprietario li vuole chiusi tutti; ordine e modo sono lasciati al progettista.

Tre fatti, trovati nel repository e sulle fonti il 14/11/2026, decidono l'ordine:

- **Due dati del calendario sono già usciti** e dal 1° gennaio 2027 rendono superati due valori del plugin: i coefficienti di trasformazione 2027-2028 (`proiezione-inps.py` ha la tabella 2025-2026) e il tasso di capitalizzazione 2026 (la tabella di `importa-previdenza.py` si ferma al 2025).
- **Solo la calibrazione dipende dalle pubblicazioni di gennaio** (circolare INPS sulla NASpI, legge di bilancio). Gli sviluppi del cruscotto e del look-through sono solo codice.
- **Due voci toccano la postura** (l'aggiustamento dei target contraddice il «lente, non target» scritto in spec, script, skill e test) e una poggia su un'altra (la polizza vita ha senso solo con il nucleo familiare).

## 2. Obiettivi, non obiettivi, anti-obiettivi

**Obiettivi**

1. Chiudere tutte le voci aperte che oggi si possono chiudere (elenco al §5), ognuna con test che vincolano i numeri.
2. Rilasciare la 0.13.0 con i coefficienti nuovi prima del 1° gennaio 2027.
3. Calibrare una volta sola, sui valori 2027.
4. Nessun file dell'utente smette di leggersi: `composizione.csv` nei suoi formati, le pagine e i bundle del cruscotto della 0.12.0, i JSON degli script della 0.12.0.

**Non obiettivi**

- Ciò che non ha ancora una fonte: la legge di bilancio 2027 prima dell'approvazione, i due punti «da verificare» della mappa dei testi unici (aspettano i correttivi), la riverifica dei marcatori di giugno 2027.
- Le prove che richiedono il proprietario (§10).
- Ciò che le spec precedenti hanno già escluso e che nessuna voce della ROADMAP riapre: ottimizzatore di ciclo di vita (opzione C di T15), conversione ICB → GICS, look-through del fondo pensione, importatore per il regime dichiarativo, API dei broker.

**Anti-obiettivi** (sarebbe un fallimento anche se funzionasse)

- Un numero normativo aggiornato da una fonte secondaria.
- Un importo o un nome dell'utente nella pagina anonimizzata.
- Output che cambiano a parità di input senza una riga «Output cambiati» nel CHANGELOG.
- Uno script di calcolo che fa chiamate di rete.
- La lente del capitale umano che diventa target senza una scelta esplicita dell'utente (ondata 4).

## 3. Vincoli

- **Regole del repository** («Regole per ogni intervento» di `ROADMAP.md`, § 4 di `HANDOFF.md`): TDD con valori chiusi o invarianti; fonti primarie e marcatori `Verificato: AAAA-MM` circoscritti; propagazione a tutte le copie; Excel modificati nell'XML e ricalcolati con `scripts/ricalcola-excel.py`; revisione avversariale prima del merge di ogni tema; CI verde; repository pubblico, quindi nessun dato personale reale in file, fixture e test.
- **Date**: i coefficienti nuovi valgono dal 1/1/2027; la legge di bilancio è attesa a fine dicembre (ddl alla Camera dal 30/10/2026, notizia da fonte secondaria); le circolari INPS escono tra gennaio e febbraio; i marcatori del 2026-06 scadono a giugno 2027 e `release.yml` esegue la freshness, quindi nessun tag dopo giugno senza riverifica.
- **Sessione cloud**: tag e cancellazione dei branch li fa il proprietario; le pull request si aprono su sua richiesta; si lavora sul branch della sessione.
- **Compatibilità**: obiettivo 4.

## 4. Approcci considerati

| # | Approccio | Pro | Contro |
|---|---|---|---|
| 1 | **A ondate, per dipendenza**: prima ciò che ha una data, poi il solo codice, poi ciò che aspetta le fonti di gennaio, per ultime le voci di postura | I coefficienti escono prima che servano; la calibrazione si fa una volta; le voci difficili arrivano quando esistono i pezzi su cui poggiano | Tre rilasci invece di uno; un tema della ROADMAP (T16) si chiude in due tempi |
| 2 | Per tema, come nei cicli precedenti (T17, poi T16, poi T15) | Ricalca la ROADMAP e il flusso di revisione per tema | T16 mescola solo codice e calibrazione ferma fino a gennaio; i coefficienti aspettano dietro le funzioni |
| 3 | Un solo ciclo lungo, tutto nella 0.13.0 | Un rilascio, una revisione | I coefficienti escono dopo il 1° gennaio, la calibrazione sui valori 2026 va rifatta, tutto aspetta le due voci più difficili |

**Scelta: il primo.** Il proprietario ha chiesto il risultato («completare») e ha lasciato il come: la scelta è del progettista, da confermare con l'approvazione di questa spec.

## 5. Il programma

| Ondata | Voce | Da dove viene | Dipende da | Rilascio |
|---|---|---|---|---|
| **0** Dati già pubblicati e igiene | 0.1 Coefficienti di trasformazione 2027-2028 | Calendario del README | Decreto del 16/10/2026 | 0.13.0 |
| | 0.2 Tasso di capitalizzazione 2026 | Calendario | Nota ISTAT del 16/10/2026 | 0.13.0 |
| | 0.3 Pesi settoriali dell'indice mondiale (`PESI_MONDO`) | T16, priorità bassa | Scheda MSCI del mese | 0.13.0 |
| | 0.4 Tabella della freshness del README, con il suo test | Trovata nell'analisi | — | 0.13.0 |
| **1** Cruscotto e look-through | 1.1 Archivio e confronto tra due revisioni | T17 | — | 0.13.0 |
| | 1.2 Versione anonimizzata del cruscotto | T17 | 1.1 e 1.3-1.5 (va per ultima) | 0.13.0 |
| | 1.3 Regioni come dimensione del look-through | T16 | — | 0.13.0 |
| | 1.4 ISIN dei titoli in `composizione.csv` | T16 | — | 0.13.0 |
| | 1.5 Valuta di denominazione | T16 | 1.4 (stesso formato del CSV) | 0.13.0 |
| **2** Capitale umano, il modello | 2.1 Volatilità personale del reddito dall'estratto INPS | T15 | — | 0.14.0 |
| | 2.2 Secondo reddito del nucleo | T15 | — | 0.14.0 |
| **3** Calibrazione e parametri 2027 | 3.1 Tasso reale privo di rischio (`R_F`) | T16, media | BCE | 0.14.0 |
| | 3.2 Perdita del lavoro e durata (`p_u`, `durata_anni`) | T16, media | ISTAT, INPS | 0.14.0 |
| | 3.3 NASpI (`sostituzione_naspi`) | T16, media | Circolare INPS di gennaio | 0.14.0 |
| | 3.4 Volatilità delle retribuzioni (`sigma_h`) | T16, bassa | ISTAT, Eurostat, Banca d'Italia | 0.14.0 |
| | 3.5 Rendimenti azionari non USA | T16, bassa | Kenneth French Data Library | 0.14.0 |
| | 3.6 Parametri 2027 del calendario | README | Legge di bilancio, circolari INPS, serie Damodaran | 0.14.0 |
| **4** Postura | 4.1 Polizza vita | T15 | 2.2 | 0.15.0 |
| | 4.2 Aggiustamento dei target | T15 | 3.x (profili calibrati), decisione del proprietario | 0.15.0 |

**Ordine dentro l'ondata 1**: 1.3, 1.4, 1.5 (look-through), poi 1.1, poi 1.2. La versione anonimizzata classifica ogni campo numerico del bundle, quindi si fa quando il bundle ha la sua forma finale.

**Rilasci** (obiettivi, non impegni): 0.13.0 entro metà dicembre 2026; 0.14.0 da febbraio 2027, quando sono uscite le circolari INPS; 0.15.0 dopo, comunque prima di giugno 2027 o dopo la riverifica dei marcatori.

**Fuori dal programma**, perché non si chiudono con il lavoro: le riverifiche di giugno e ottobre 2027, la citazione principale sul testo unico nuovo quando la prassi dell'Agenzia lo segue, i correttivi del D.Lgs. 117/2026. Restano nel calendario del README.

## 6. Ondata 0: dati già pubblicati e igiene

### 6.1 Coefficienti di trasformazione 2027-2028

**Fonte**, letta il 14/11/2026 sul PDF del decreto dal sito del Ministero del Lavoro: decreto direttoriale del Ministero del Lavoro e delle Politiche Sociali di concerto con il Ministero dell'Economia e delle Finanze del **16 ottobre 2026**, articolo unico; basi tecniche nella nota ISTAT n. 1998189/26 del 27/05/2026 e nella Nota tecnica della Conferenza di servizi del 22/06/2026. Decorrenza **1° gennaio 2027**, tasso di sconto 1,5%. La pubblicazione in Gazzetta Ufficiale non risulta ancora: si cita il decreto, e la GU si aggiunge quando esce.

| Età | Divisore | Coefficiente | | Età | Divisore | Coefficiente |
|---|---|---|---|---|---|---|
| 57 | 24,080 | 4,153% | | 65 | 19,357 | 5,166% |
| 58 | 23,507 | 4,254% | | 66 | 18,747 | 5,334% |
| 59 | 22,929 | 4,361% | | 67 | 18,136 | 5,514% |
| 60 | 22,345 | 4,475% | | 68 | 17,523 | 5,707% |
| 61 | 21,756 | 4,596% | | 69 | 16,908 | 5,914% |
| 62 | 21,163 | 4,725% | | 70 | 16,290 | 6,139% |
| 63 | 20,565 | 4,863% | | 71 | 15,669 | 6,382% |
| 64 | 19,963 | 5,009% | | | | |

Rispetto al 2025-2026 i coefficienti scendono tra l'1,21% (57 anni) e l'1,97% (71 anni); a 67 anni da 5,608% a 5,514% (−1,68%). Ogni coefficiente è 1/divisore arrotondato alla terza cifra del percento: il test lo verifica. Il costruttore rilegge la tabella sul decreto prima di scriverla (regola delle fonti primarie).

**Decisioni**

| # | Decisione | Scelta |
|---|---|---|
| D1 | Quale tabella usa lo script | Solo quella vigente, la 2027-2028, già nella 0.13.0 di dicembre: chi proietta oggi va in pensione dal 2027. La tabella 2025-2026 resta nella reference, nel confronto tra bienni |
| D2 | Nome della costante | `COEFF_VIGENTI`, con il biennio in una costante privata (`_BIENNIO_COEFF = "2027-2028"`, che `--set` non elenca) per i testi dell'output: alla prossima revisione cambiano solo i dati. Oggi il nome `COEFF_2025_2026` è scritto anche in un test |
| D3 | Riduzione attesa dei coefficienti futuri | Invariata (`RIDUZIONE_COEFF_ANNUA = 0.007` nello script, decadimento per biennio nell'Excel): la revisione osservata sta nell'intervallo già dichiarato. Nei testi l'intervallo osservato si aggiorna con il dato nuovo |
| D4 | Output | Cambiano a parità di input (pensione proiettata più bassa dell'1-2%): riga «Output cambiati» nel CHANGELOG, con un esempio sui default |

**Copie da aggiornare** (la regola è propagare: `git grep` su `5,608`, `5.608`, `2025-2026`, `2025-26`, `20/11/2024`, `COEFF_2025_2026`):

- `skills/it-pianificazione/assets/proiezione-inps.py`: tabella, commento con fonte e marcatore, stringa «origine»;
- `skills/it-pianificazione/assets/riscatto-laurea.py`: legge tabella e riduzione dal modulo di `proiezione-inps.py`; controllare i testi che nominano il biennio;
- `skills/it-pianificazione/references/previdenza-obbligatoria.md`: tabella con i divisori, confronto 2025-2026 contro 2027-2028, esempi svolti (età non intera, montante di €300.000, coefficiente proiettato), prossimo aggiornamento (biennio 2029-2030, atteso nell'autunno 2028);
- `skills/it-pianificazione/SKILL.md` (il coefficiente a 67 anni e l'esempio «del perché conta», da ricalcolare) e `skills/it-pianificazione-autonomi/references/previdenza-gestione-separata.md`;
- foglio `Coefficienti` di `proiezione-pensione.xlsx` e di `proiezione-pensione-autonomi.xlsx`: titolo, fonte, `B5:C19`, note che nominano il biennio; modifica nell'XML, ricalcolo in locale italiano, struttura confrontata prima e dopo;
- README: tabella della freshness e riga del calendario (il decreto è uscito; la prossima è l'autunno 2028).

**Test, prima del codice**: la tabella dello script è quella del decreto, valore per valore, e ogni coefficiente è 1/divisore; script, reference e i due Excel portano gli stessi quindici valori; i valori chiusi che dipendono dal coefficiente si ricalcolano (proiezione INPS, `--json` previdenziali, Excel contro script, riscatto della laurea, cifre documentate nelle skill). Il costruttore li trova lanciando la suite dopo aver cambiato il primo test.

### 6.2 Tasso di capitalizzazione 2026

**Fonte**, letta il 14/11/2026: nota ISTAT prot. 2582754/26 del **16/10/2026** al Ministero del Lavoro, «Tasso annuo di capitalizzazione per la rivalutazione dei montanti contributivi relativamente al 2026»: tasso **0,063359**, coefficiente **1,063359** (variazione media quinquennale del PIL nominale nei cinque anni precedenti il 2026). È sopra 1 e non c'è un recupero in sospeso, quindi vale così com'è (DL 65/2015 art. 5).

- `importa-previdenza.py`: `TASSI_CAPITALIZZAZIONE[2026] = 1.063359`, con la convenzione già scritta nel file (rivaluta il montante al 31/12/2025, per le decorrenze dal 2027); commento della fonte e marcatore aggiornati; il docstring dice 1996-2026.
- `previdenza-obbligatoria.md`: le medie del tasso nominale e l'intervallo dei singoli anni si ricalcolano (il 6,3% del 2026 è il nuovo massimo dal 1996).
- **Test**: il dizionario dei tassi ufficiali prende il 2026; il test sulle medie documentate segue; il montante ricostruito sulla fixture cambia dove l'anno corrente è il 2026. L'avviso «tasso non ancora pubblicato» resta per gli anni dopo l'ultimo tasso.

### 6.3 Pesi settoriali dell'indice mondiale

`PESI_MONDO` di `capitale-umano.py` viene dalla scheda MSCI ACWI del 30/09/2026. Si aggiorna all'ultima scheda mensile disponibile, dalla stessa fonte indicata nel commento. Perché «manuale a ogni release» non resti una promessa:

- il commento prende il marcatore `Verificato: AAAA-MM` e `capitale-umano.py` entra in `OBBLIGATI_FRESHNESS` (servirà anche alla NASpI dell'ondata 3);
- la sezione «Release» del README aggiunge il passo.

Se la scheda non è raggiungibile dalla sessione, i pesi restano quelli di settembre, il marcatore non si mette e la voce passa al proprietario.

### 6.4 Tabella della freshness del README

Alla tabella «Stato dei dati normativi» mancano due righe (`capitale-umano.md`, `riscatto-laurea.py`): nessun test la confronta con il runner, a differenza della tabella strumenti ↔ test. Si rigenera con `--tabella-freshness` e si aggiunge il test di igiene che la confronta, come per l'altra. Il «Calendario dei parametri da riverificare» si aggiorna allo stato di novembre.

## 7. Ondata 1: cruscotto e look-through

Tre regole valgono per tutte le voci dell'ondata:

- **Chiavi nuove facoltative in lettura.** Il cruscotto accetta un JSON del look-through senza `regioni` e `valute` (quello della 0.12.0) e salta i grafici che mancano.
- **Il bundle passa alla `versione` 2**, con due chiavi nuove, `confronto` e `anonimo`, a `null` quando non servono.
- **Le regole del template non cambiano** (spec T17, §2.2): niente risorse esterne, dati nel DOM solo come testo, numeri all'italiana, tema chiaro e scuro, 375 px senza scorrimento orizzontale, ogni grafico con il dato in testo accanto.

### 7.1 Archivio e confronto tra due revisioni

**Perché.** La revisione chiede «cosa è cambiato dall'ultima volta» (passo 2) e il template del report ha un «variazione vs anno scorso», ma niente conserva la revisione precedente: `cruscotto.html` si sovrascrive a ogni lancio e il bundle (`--json`) è facoltativo. Oggi quella variazione la calcola Claude a mano, o nessuno.

**La foto di una revisione è il bundle**: i dati che la pagina mostra, già senza posizioni né ISIN. Non serve un formato nuovo.

**Interfaccia** (`genera-cruscotto.py`):

- `--archivia [CARTELLA]`: scrive anche il bundle in `CARTELLA/cruscotto-AAAA-MM-GG.json` (default `revisioni/` nella cartella corrente, creata se manca; la data è `generato_il`). Un secondo lancio nello stesso giorno sovrascrive la foto del giorno, e lo dice.
- `--precedente FILE|CARTELLA`: la revisione con cui confrontare. Un **bundle** (`versione` 1 o 2), una **pagina** `cruscotto.html` generata dal plugin (il bundle si estrae dal blocco `<script id="dati" type="application/json">`: così vale anche una pagina della 0.12.0 messa da parte), oppure una **cartella**: tra i suoi `cruscotto-*.json` si prende la foto più recente con data precedente a quella corrente. La data di una foto è il suo `generato_il`, non il nome del file.
- Errori con `ERRORE:` e codice 1: file o cartella inesistente; cartella senza foto precedenti, o con una foto illeggibile (si nomina il file: non si salta in silenzio a una più vecchia); file che non è un bundle né una pagina del plugin (compreso il template senza dati); `versione` sconosciuta; foto anonimizzata; data uguale o successiva a quella corrente.
- A fine esecuzione stampa la data della revisione di confronto e quante grandezze ha confrontato.

**Cosa si confronta.** Una tabella in testa allo script, `CONFRONTI`, una riga per grandezza (sezione, identificativo, etichetta, formato, percorso nel bundle), sul modello di `FIRME`. Una grandezza entra nel confronto solo se è un numero in entrambi i bundle. L'elenco minimo:

| Sezione | Grandezze |
|---|---|
| In sintesi | i cinque indicatori esistenti, per `id` |
| Allocazione | peso attuale di ogni classe presente in entrambe; quota azionaria del target aggregato |
| Glide path | quota azionaria aggregata dell'anno 0 |
| Pensione | pensione INPS lorda annua; tasso di sostituzione lordo mediano; probabilità del target; montante mediano del fondo; pensione netta dello scenario mediana |
| Capitale umano | esposizione azionaria finanziaria e totale; patrimonio finanziario e capitale umano di oggi (prima riga della proiezione) |
| Fiscalità | zainetto in euro 26%-equivalenti; plus latenti compensabili |
| Look-through | quota dei primi titoli; peso dei primi tre settori di oggi |

Gli **obiettivi** si confrontano per nome (uguale dopo aver tolto gli spazi ai bordi): probabilità di successo, già accumulato, versamento «di confidenza». Un obiettivo presente in un solo bundle compare come «nuovo» o «non più presente»; un nome ripetuto in un bundle non si confronta, e lo si dice. Il piano di ribilanciamento non si confronta: è il piano del giorno.

**Nel bundle**: `confronto = {data_precedente, plugin_precedente, versioni_diverse, voci: [{sezione, id, etichetta, formato, prima, ora, delta, delta_rel}], obiettivi: [{nome, stato, probabilita, gia, versamento}]}`. Per gli importi `delta` è in euro e `delta_rel` la variazione relativa (`null` se «prima» è zero); per le quote `delta` è in frazione e la pagina lo scrive in punti.

**Nella pagina**: sezione `#sez-confronto`, «Rispetto alla revisione del GG/MM/AAAA», subito dopo «In sintesi». Una tabella per sezione (voce, prima, ora, variazione), le probabilità degli obiettivi come barre affiancate prima e ora, gli obiettivi nuovi e non più presenti in testo. Sotto ogni indicatore di «In sintesi» una riga piccola con il valore di prima e la variazione. Tre scelte di presentazione:

- **neutra**: segni e numeri, niente verde e rosso. Un aumento non è sempre un bene (lo zainetto in scadenza), e il cruscotto non giudica;
- **importi nominali**: ognuno alla data della sua revisione, non corretti per l'inflazione; la sezione lo dice;
- **versioni diverse**: se le due revisioni vengono da versioni diverse del plugin la sezione avvisa che parte delle differenze può venire da dati normativi e metodi aggiornati, e rimanda al CHANGELOG. Con la 0.13.0 succede subito: la pensione proiettata scende per i coefficienti nuovi, non per la situazione dell'utente.

**Nella skill `it-revisione`**: al passo 6 di una revisione completa si archivia sempre (`--archivia`) e, se in `revisioni/` c'è una foto precedente, la si passa con `--precedente revisioni/`; un `/cruscotto` esplorativo non archivia, se l'utente non lo chiede. Al passo 2 e nel report le variazioni vengono da `confronto`, mai da sottrazioni fatte a mano (nuovo anti-pattern). Il «Contratto di input» prende la riga «Confronto»; `template-revisione.md` la sezione 2 con la riga del confronto. README, «Dove vanno i tuoi dati»: la cartella `revisioni/` contiene i bundle, con importi ed età, e resta nella cartella di lavoro.

**Test**

- Python: valori chiusi dei delta su due bundle costruiti dagli esempi (un obiettivo con probabilità cambiata, uno rinominato); `--precedente` da pagina HTML, da bundle di versione 1 (fixture sintetica), da cartella con più foto; ogni errore dell'elenco; `--archivia` (nome con la data, cartella indicata, sovrascrittura nello stesso giorno); senza `--precedente` il bundle ha `confronto: null`.
- Browser: `#sez-confronto` presente con i numeri all'italiana, assente senza confronto; avviso delle versioni diverse; 375 px; nessun errore in console.
- Documentazione: passi 2 e 6, contratto di input, anti-pattern, template, README.

### 7.2 Versione anonimizzata

**Perché.** La pagina porta importi, nomi degli obiettivi e dei broker: va bene per sé, non per mostrarla ad altri. Il precedente nel plugin è `importa-previdenza.py --anonimo`, che toglie intestatario e data di nascita e tiene l'età.

**Interfaccia**: `--anonimo`. Senza `-o` la pagina si chiama `cruscotto-anonimo.html`, così quella completa non si sovrascrive. `--json` scrive il bundle anonimizzato (è ciò che finisce nella pagina). `--anonimo` con `--archivia` è un errore di riga di comando (codice 2): l'archivio serve al confronto e tiene gli importi veri. `--anonimo` con `--precedente` è ammesso.

**La trasformazione** si applica per ultima, al bundle già composto (confronto compreso):

| Cosa | Diventa |
|---|---|
| Ogni importo in euro | Un **indice**: importo × 100 / base, con un solo fattore per tutta la pagina, così proporzioni e grafici restano veri. La base è la prima disponibile tra: capitale allocato, valore in portafoglio, patrimonio finanziario di oggi (capitale umano), totale del ribilanciamento, netto dell'ultimo stipendio, RAL finale, capitale-ponte; in mancanza, l'importo più grande della pagina. La testata dice qual è |
| Importi del riscatto della laurea | `null`: l'onere agevolato è un importo di legge, e accanto all'indice rivelerebbe il fattore. Restano anni, modalità, anni per rientrare, anticipo |
| Nomi degli obiettivi | «Obiettivo 1…n», lo stesso nome con la stessa etichetta in tutte le sezioni, nel confronto e nella nota dell'indicatore che nomina un obiettivo |
| Nomi dei broker | «Broker A, B…», coerenti tra fiscalità e ribilanciamento |
| Nomi dei file di origine | Tolti; restano i tipi |
| Testi liberi (avvisi dell'importatore, nota degli ordini, esito e motivo del drift) | Tolti; gli avvisi si contano tra gli omessi. Contengono importi e nomi di broker |
| Percentuali, probabilità, anni, **età**, date, conteggi, classi, profili, priorità, settore del lavoro, aggregati del look-through | Invariati |

Nel bundle: `anonimo = {base, obiettivi, broker}` (l'etichetta della base e quanti nomi sono stati sostituiti). Nella pagina: la testata dice che è la versione anonimizzata, cosa è stato sostituito e cosa resta (età, anni, percentuali, settore del lavoro); gli importi si scrivono come numero senza «€», con «(indice)» sugli assi; il blocco del riscatto mostra solo il testo.

**Guardia.** Lo script dichiara quali campi del bundle sono importi in euro (`CAMPI_EURO`, per percorso) e quali no. Un test percorre il bundle completo degli esempi e fallisce se trova un campo numerico non classificato: un campo aggiunto domani non può portare un importo nella pagina anonima per dimenticanza.

**Limite dichiarato**, in pagina e nella reference: nasconde gli importi e i nomi, non rende irriconoscibile chi conosce già un numero dell'utente (con un importo vero si ricava il fattore).

**Nella skill**: al passo 6, se l'utente vuole mostrare la pagina ad altri, si genera e si pubblica la versione anonimizzata; la conferma prima di pubblicare resta, e dice cosa resta visibile.

**Test**

- Python: nel bundle e nell'HTML anonimi non compaiono «€», né gli importi degli esempi da 1.000 euro in su (interi o in formato italiano), né i nomi di obiettivi, broker e file; i rapporti si conservano (già accumulato su target, prima e dopo); la base vale 100; importi del riscatto a `null`; etichette coerenti tra sezioni; `--anonimo --archivia` dà codice 2; il test della guardia.
- Browser: testata della versione anonimizzata, nessun «€» nel testo della pagina, «Obiettivo 1» al posto del nome, 375 px.

### 7.3 Regioni come dimensione del look-through

Le regioni si **derivano dai paesi** al momento dell'aggregazione: nessun cambio a `composizione.csv`, all'importatore, al capitale umano, e valgono anche per le righe compilate a mano.

- **Classificazione**: le regioni geografiche dello standard ONU M49, con le Americhe divise nelle loro due sottoregioni: Nord America, America Latina e Caraibi, Europa, Asia, Oceania, Africa. Stanno in una tabella `REGIONI` di `look-through-portafoglio.py` che copre **ogni** codice di `PAESI`; l'Antartide, che M49 non assegna a una regione, ha una voce sua. È una classificazione stabile e senza licenze, da leggere sulla pagina M49 della Divisione statistica dell'ONU e citare nel commento. La divisione tra mercati sviluppati ed emergenti resta fuori: è di un fornitore di indici, cambia nel tempo e tra fornitori.
- La reference dichiara le assegnazioni che sorprendono un investitore: Turchia, Israele, Cipro e i paesi del Golfo in Asia; Russia in Europa; Messico in America Latina.
- **JSON**: `regioni: [{voce, nome, peso}]` per peso decrescente, `copertura.regioni` uguale a quella dei paesi. **Report**: una riga «Per regione» sotto i paesi. **Cruscotto**: barre «Regioni» prima di «Paesi».
- **Test**: valori chiusi sulla fixture; ogni codice di `PAESI` in una e una sola regione; le assegnazioni dichiarate sopra; il cruscotto con e senza `regioni`.

### 7.4 ISIN dei titoli in `composizione.csv`

**Perché.** Lo stesso titolo in due ETF oggi si somma con una chiave normalizzata del nome; due emittenti che scrivono la società in modi troppo diversi restano separati (limite dichiarato nella spec del look-through). L'importatore legge già l'ISIN dei titoli, quando il file lo ha, ma lo mette solo nel suo JSON.

- **Formato**: l'intestazione diventa `strumento;dimensione;voce;peso;isin`. La quinta colonna è piena solo sulle righe `titolo` il cui file ha l'ISIN, vuota altrove. Un valore presente deve avere la forma di un ISIN (due lettere, nove caratteri alfanumerici, una cifra): altrimenti `ERRORE:` con la riga.
- **Lettori**: `capitale-umano.py`, `look-through-portafoglio.py` e l'importatore accettano i tre formati (`strumento;settore;peso`, quattro colonne, cinque colonne). L'importatore, quando aggiorna un file a quattro colonne, lo riscrive a cinque e lo dice, come già fa con il formato più vecchio. Le righe a mano possono omettere il quinto campo.
- **Regola di somma** nel look-through: due righe `titolo` sono lo stesso titolo se hanno lo stesso ISIN **oppure** la stessa chiave del nome (componenti connesse). Servono entrambe: una riga senza ISIN (iShares non lo riporta) deve sommarsi a quella dello stesso nome che lo ha, e due classi di azioni con ISIN diversi e lo stesso nome restano unite come oggi.
- **JSON** del look-through: ogni titolo aggregato prende `isin`, la lista degli ISIN del gruppo (vuota se nessuno). Nel bundle del cruscotto gli ISIN dei titoli **non** entrano: non servono alla pagina.
- **Test**: l'importatore scrive la colonna da un file che ha gli ISIN e la lascia vuota da uno che non li ha; un file a quattro colonne aggiornato passa a cinque senza perdere righe; il look-through unisce due nomi diversi con lo stesso ISIN, unisce una riga con ISIN e una senza dallo stesso nome, tiene unite due classi; ISIN malformato; sui file esistenti a tre e a quattro colonne i numeri restano identici a oggi.

### 7.5 Valuta di denominazione

**Cosa.** Una quarta dimensione, `valuta`: in quali valute sono denominati i titoli dentro gli ETF, sommati per controvalore. La valuta è quella di negoziazione del titolo che l'emittente riporta, non quella dei ricavi della società: limite dichiarato.

- **Importatore**: ruolo `valuta` nei sinonimi delle colonne (`Currency`, `Market Currency`, `Valuta`, `Valuta di mercato`, `Währung`, `Devise`…). Attenzione al file italiano di iShares: la colonna «Cambio» è la **borsa** (c'è «NASDAQ»), la valuta è «Valuta di mercato». La dimensione segue le regole delle altre: liquidità e derivati esclusi, righe senza valuta contate come non classificate, rinormalizzazione a 100, soglia della metà dei titoli. Le obbligazioni contano (a differenza dei settori).
- **Codici**: ISO 4217, validati sull'elenco completo dei codici attivi, con il nome italiano per le valute principali e il codice per le altre; le unità minori si riportano alla valuta (`GBX` e `GBp` a `GBP`, `ZAc` a `ZAR`, `ILa` a `ILS`). Un valore che non è un codice ferma lo script con l'elenco, come per settori e paesi.
- **Classi con copertura del cambio**: la valuta dei titoli non è l'esposizione, e il file delle posizioni non lo dice in modo affidabile. Nuova opzione `--copertura CHIAVE=VALUTA` (ripetibile; la chiave è uno degli `--strumento` della stessa riga di comando, altrimenti codice 2): per quello strumento si scrive una sola riga `valuta` al 100% nella valuta di copertura, con la nota nel commento del CSV. Se il preambolo o il nome del file contengono «hedged» o i suoi equivalenti e l'opzione manca, un avviso dice come reimportare. Lo script non decide da solo.
- **CSV**: righe `strumento;valuta;USD;71,20;`. Le posizioni dirette si compilano a mano (`IT0005454241;valuta;EUR;100`).
- **Lettori**: `capitale-umano.py` riconosce `valuta` e la salta; `look-through-portafoglio.py` la aggrega come le altre: `valute: [{voce, nome, peso}]`, `copertura.valute`, `quota_euro` (il peso dell'euro sulla parte coperta), sezione «VALUTE» del report, `valute` tra le dimensioni di ogni posizione. **Cruscotto**: barre «Valute» (le prime otto e «altre»), con la copertura.
- **Test**: colonne della valuta nelle quattro lingue e «Cambio» non letta come valuta; valori chiusi dopo esclusioni e rinormalizzazione; unità minori; codice sconosciuto; file senza la colonna (avviso, nessuna riga); `--copertura`; avviso su «hedged»; look-through con copertura e `quota_euro`; i due test che oggi usano `valuta` come dimensione sconosciuta ne usano un'altra; cruscotto con e senza `valute`.

## 8. Ondate 2, 3 e 4: l'impianto

Ogni ondata ha la sua spec, scritta quando ci si arriva e con le fonti lette. Qui solo ciò che è già deciso e ciò che la spec deve chiudere.

| Voce | Impianto | Resta alla spec dell'ondata |
|---|---|---|
| 2.1 Volatilità personale | `importa-previdenza.py` ha già le retribuzioni per anno: stima la volatilità delle variazioni reali sugli anni pieni e la scrive nel suo JSON. È un'**indicazione**: il default resta il profilo, e la lente la usa solo se l'utente la sceglie | Serie dei prezzi italiana per deflazionare (ISTAT, con marcatore); numero minimo di anni; errore della stima; effetto di massimale, part-time e cambi di lavoro |
| 2.2 Secondo reddito | `persone` (lista) accanto a `persona`, che continua a dare gli stessi numeri di oggi; ogni persona ha profilo, settore, età, pensione, fondo e TFR; patrimonio e diagnosi del nucleo | Schema del JSON; correlazione tra i due redditi nel Monte Carlo; asse della proiezione con due età; come arrivano i JSON previdenziali di due persone; cruscotto e contratto di `it-revisione` |
| 3.1 `R_F` | Nessuna rete negli script: la reference dice dove leggere il tasso, il default si riverifica con data e marcatore, Claude può procurarlo su richiesta e passarlo con `--set` | Quale misura (curva BCE meno inflazione attesa, o titoli indicizzati) |
| 3.2 `p_u`, durata; 3.4 `sigma_h` | Valori dei profili da fonte primaria, con fonte, anno e natura nel CSV; «Output cambiati» nel CHANGELOG | Le serie ISTAT, INPS, Eurostat e Banca d'Italia da usare e la corrispondenza con i sei profili |
| 3.3 NASpI | Importi 2027 dalla circolare INPS; sostituzione calcolata con la formula di legge quando l'utente dà la retribuzione lorda, altrimenti il default del profilo | Forma dell'input; trattamento del calo mensile |
| 3.5 Rendimenti non USA | Un importatore converte il file che l'utente scarica dalla Kenneth French Data Library nel formato di `rendimenti-storici.csv`, nella cartella di lavoro; gli script che usano la serie prendono un'opzione per leggerla. I dati non entrano nel repository. Il default resta la serie USA | Quale serie (mondo sviluppato, Europa); colonne di obbligazioni e inflazione; serie più corta e bootstrap a blocchi |
| 3.6 Parametri 2027 | Legge di bilancio, circolari INPS, serie Damodaran e CPI, ognuno su fonte primaria e in tutte le copie | Elenco dei parametri, quando le fonti sono uscite |
| 4.1 Polizza vita | Una diagnosi in più della lente: il **fabbisogno** di copertura in caso di morte per chi ha persone a carico, mai un prodotto o una compagnia | Metodo (Chen, Ibbotson, Milevsky e Zhu 2006); pensione ai superstiti e detrazione dei premi, con le loro fonti e la freshness; perimetro, da confermare con il proprietario |
| 4.2 Aggiustamento dei target | Proposta: sul modello della decisione 4 della ROADMAP, un'**opzione** con gate e disclaimer; il default resta la lente. Solo su richiesta esplicita, solo sugli obiettivi lontani e non essenziali, entro un tetto dichiarato | Tutto il metodo; **la decisione di postura è del proprietario** e si prende lì, perché cambia la decisione D1 della spec T15 |

## 9. Processo e rilascio della 0.13.0

- **Per ogni ondata**: spec (questa, per le ondate 0 e 1), piano in `docs/sviluppo/piani/`, implementazione in TDD, revisione avversariale con `docs/sviluppo/workflows/review-tema-roadmap.js` ed esito in `docs/sviluppo/revisioni/`, pull request su `develop` quando il proprietario la chiede.
- **Versioni delle skill** a fine ondata 1: it-pianificazione 0.14, it-pianificazione-autonomi 0.6, it-pianificazione-obiettivi 0.25, it-revisione 0.10; README e CHANGELOG le seguono (un test le confronta).
- **File trasversali**: `CHANGELOG.md` («Non rilasciato», con gli «Output cambiati»); README (conteggio dei test, tabella strumenti ↔ test, tabella della freshness, «Dove vanno i tuoi dati», «Release»); `ROADMAP.md` (voci spuntate, questo programma, linea di taglio della 0.13.0); `HANDOFF.md` riscritto a fine ciclo.
- **Rilascio**: `release/0.13.0` da `develop`, pull request su `main`, tag del proprietario, `release.yml`, merge back; come per la 0.12.0.

## 10. Cosa resta al proprietario

- Approvare questa spec; decidere la postura della 4.2 quando arriva la sua spec.
- Le prove già sue: installazione da un account senza accesso e in Cowork; pubblicazione del cruscotto come Artifact in claude.ai e in Cowork; file reali di iShares dal sito britannico e di Amundi dai siti tedesco e francese.
- Il tag di ogni rilascio e la cancellazione dei branch di sessione.
- Se fa la revisione di fine anno prima della 0.13.0: mettere da parte il `cruscotto.html`. Il confronto lo leggerà.

## 11. Cosa resta al costruttore

Nomi delle funzioni interne e testo esatto dei messaggi; il disegno dei grafici nuovi dentro le regole del template; quante valute hanno il nome italiano; i test oltre il minimo indicato; la divisione in commit; le grandezze in più da aggiungere a `CONFRONTI`. Ogni scelta che cambia un'interfaccia descritta qui si annota nel piano.

## 12. Limiti dichiarati

- Il confronto mette accanto due fotografie: non distingue quanto di una variazione viene dal mercato, dai versamenti o da un dato normativo cambiato; l'avviso sulle versioni diverse copre solo l'ultimo caso.
- La versione anonimizzata nasconde importi e nomi, non età, settore del lavoro e struttura del piano.
- Le regioni sono geografiche: Giappone e India stanno entrambi in Asia.
- La valuta è quella di negoziazione dei titoli; per le classi con copertura del cambio conta ciò che dichiara l'utente con `--copertura`.
- Gli ISIN uniscono i titoli solo dove il file dell'emittente li riporta.
- Subito dopo un cambio di tabella dei coefficienti le pensioni proiettate scendono di un gradino: la riduzione attesa si conta dagli anni mancanti alla pensione, non dall'anno della tabella. È così da prima, e questo ciclo non lo cambia.
