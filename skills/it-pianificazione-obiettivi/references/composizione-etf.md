# Composizione degli ETF: l'importatore

> ⚠️ Strumento di pianificazione personale, non consulenza finanziaria. La composizione è quella dichiarata dall'emittente alla data del file.

## Indice

- A cosa serve
- Come si usa
- Dove si scarica il file delle posizioni
- Cosa legge e cosa esclude
- Il file composizione.csv
- Stato dei formati
- Limiti
- Licenza dei file
- Se un nome non è riconosciuto

## A cosa serve

La diagnosi 4 del capitale umano confronta il settore del proprio lavoro con la parte azionaria del portafoglio (vedi `capitale-umano.md`). Serve sapere quanto pesa ogni settore dentro ciascun ETF. L'importatore lo ricava dal **file delle posizioni** del fondo, cioè l'elenco completo dei titoli con il loro peso, che ogni emittente pubblica nella pagina dell'ETF. Lo script aggrega i titoli per **settore GICS** e per **paese** (codice ISO 3166-1 alpha-2) e scrive `composizione.csv`. I paesi oggi non entrano in nessun calcolo: sono la base di un futuro look-through del portafoglio.

## Come si usa

Dalla cartella di lavoro, un `--file` e un `--strumento` per ogni ETF:

```
python "${CLAUDE_SKILL_DIR}/assets/importa-composizione-etf.py" --file swda.csv --strumento "ETF MSCI World" \
    --file xdem.xlsx --strumento "ETF Momentum" [--out composizione.csv] [--json composizione.json]
python "${CLAUDE_SKILL_DIR}/assets/capitale-umano.py" --dati capitale-umano.json --composizione composizione.csv
```

- `--strumento` va scritto **esattamente** come il campo `strumento` delle posizioni nel JSON del capitale umano (maiuscole e spazi compresi). Se non coincide, lo strumento finisce tra quelli «senza composizione» e il report del capitale umano lo elenca per nome.
- Se `composizione.csv` esiste già, si sostituiscono solo le righe degli strumenti importati; le altre, comprese quelle compilate a mano, restano. Un file nel vecchio formato `strumento;settore;peso` viene convertito nel nuovo, con gli stessi pesi.
- `--emittente ishares|xtrackers|vanguard|amundi|spdr` forza la scheda dell'emittente quando il riconoscimento automatico (dal preambolo del file o dal suo nome) non basta.
- `--json FILE` scrive anche il risultato strutturato (pesi in frazione); `--json -` lo stampa da solo su stdout (gli eventuali `--set` si annotano su stderr).
- Un errore (file sbagliato, nome sconosciuto, pesi che non tornano, `--out` o `--json` in una cartella che non esiste) ferma lo script con `ERRORE:` prima di scrivere: `composizione.csv` resta com'era e il JSON non nasce.
- `--set` cambia le tabelle in testa allo script (per esempio `--set "VALORI_LIQUIDITA=('cash', 'margin')"`); serve una tupla, con la virgola finale anche per un solo nome: `('cash',)`.

## Dove si scarica il file delle posizioni

Sempre dalla pagina del singolo ETF sul sito dell'emittente, nella sezione delle posizioni («Posizioni», «Holdings», «Portafoglio», «Composizione»), con il pulsante di download del file completo. Non va bene la scheda prodotto (factsheet) né il KID: riportano solo i primi dieci titoli o i pesi aggregati, e l'importatore lo dice («scarica il file delle posizioni»).

| Emittente | Formato tipico | Note |
|---|---|---|
| iShares (BlackRock) | CSV | Preambolo di qualche riga con nome del fondo e data («Fund Holdings as of», «Posizioni al»); dal sito italiano intestazioni e settori in italiano, con la virgola decimale |
| Xtrackers (DWS) | XLSX | Disclaimer in testa, intestazione alla riga 4, peso in frazione, data nel nome del foglio |
| Vanguard | XLSX o CSV | Per gli ETF su indici FTSE la classificazione dei settori può essere ICB: vedi sotto |
| Amundi | XLSX | Intestazioni nella lingua del sito |
| SPDR (State Street) | XLSX | Preambolo con «Holdings As Of», paese di negoziazione («Trade Country Name»), righe «Unassigned» per i contratti di cambio |

Se il sito apre la pagina invece di scaricare il file (capita quando si copia il link del pulsante), l'importatore riconosce l'HTML e chiede di usare il pulsante di download.

## Cosa legge e cosa esclude

La riga d'intestazione si cerca nelle prime 40 righe con tabelle di sinonimi in italiano e in inglese: peso (`Weight (%)`, `Weighting`, `Percent of Fund`, `Ponderazione (%)`, `Peso`…), settore (`Sector`, `Sector Classification`, `Industry Classification`, `Settore`…), paese (`Location`, `Country`, `Trade Country Name`, `Area geografica`, `Paese`…), asset class (`Asset Class`, `Type of Security`…). Il preambolo sopra e il disclaimer sotto non contano. La scala dei pesi (frazione o percento) si deduce dalla somma.

Si escludono, con la quota riportata nel report e nel commento del CSV:

1. **liquidità e derivati**: asset class o settore come `Cash`, `Cash and/or Derivatives`, `Futures`, `FX`, `Forward`, `Swap`, `Liquidità`, e ogni riga con **peso negativo** (contratti di cambio). Escluse da settori e paesi;
2. **righe non classificate**, separatamente per dimensione: `unknown`, `Unassigned`, `-`, `Other`, «European Union», «Supranational». Una riga con il paese e senza settore conta nei paesi;
3. le righe con peso `N/A`, che non hanno peso;
4. **il settore delle obbligazioni**: per le righe con asset class a reddito fisso (`Fixed Income`, `Bond`, `Reddito fisso`, `Obbligazioni`) il settore è quello di una tassonomia obbligazionaria («Treasuries», «Banking», «Titoli di Stato»), non GICS: non entra nei settori, mentre il paese conta. Un ETF obbligazionario dà quindi solo i paesi, uno misto i settori della sua parte azionaria; la quota sta nel commento come «obbligazioni senza settore GICS».

I pesi rimasti si **rinormalizzano a 100** per dimensione. Se meno della metà dei titoli ha il settore (o il paese), quella dimensione non si scrive: il 3% del fondo rinormalizzato a 100 descriverebbe un fondo che non esiste. Avvisi: righe non classificate oltre il 5% del fondo in una dimensione; liquidità e derivati oltre il 5% (per un ETF sintetico il file può contenere il paniere di collaterale e non l'esposizione); emittente non riconosciuto; «Telecommunication Services» (GICS prima del 2018) letto come Communication Services.

**ICB.** Gli indici FTSE classificano i titoli con ICB, non con GICS. I due sistemi non si convertono uno a uno: la «Technology» ICB comprende titoli che in GICS stanno in Communication Services. Per un file in ICB l'importatore scrive solo i paesi e lo dice; il capitale umano tratta quello strumento come senza composizione settoriale. Il sistema si riconosce dalla scheda dell'emittente o dai nomi che esistono in uno solo dei due (`Technology`, `Telecommunications`, `Basic Materials` contro `Information Technology`, `Communication Services`, `Materials`); un file che li mescola si ferma.

## Il file composizione.csv

```
# ETF MSCI World: iShares, swda.csv, posizioni al 30/09/2026, importato il 25/10/2026; esclusi liquidità e derivati 0,40%
strumento;dimensione;voce;peso
ETF MSCI World;settore;Information Technology;26,84
ETF MSCI World;paese;US;71,20
```

UTF-8 con BOM, separatore `;`, virgola decimale, pesi in percento con due decimali: si apre in Excel italiano. `capitale-umano.py` legge le righe `settore`; accetta anche il vecchio formato `strumento;settore;peso` compilato a mano.

## Stato dei formati

| Emittente | Layout | Verifica |
|---|---|---|
| Xtrackers | XLSX dal sito britannico in inglese | file reale, 25/10/2026 |
| SPDR | XLSX dal sito EMEA in inglese | file reale, 25/10/2026 |
| iShares | CSV, siti italiano e britannico | da confermare su un file reale |
| Vanguard | — | da confermare su un file reale (GICS o ICB) |
| Amundi | — | da confermare su un file reale |

«Da confermare» vuol dire che i sinonimi coprono i formati documentati ma nessun file reale è ancora passato dall'importatore: se qualcosa non torna, lo script si ferma e dice cosa ha visto.

## Limiti

- **Posizioni del fondo, non dell'indice**: un ETF a replica campionaria espone posizioni diverse dall'indice; un ETF sintetico (swap) può pubblicare il paniere di collaterale.
- **Fotografia a una data**: la composizione cambia; la data delle posizioni è nel commento del CSV e va riguardata a ogni revisione annuale. Una data numerica sotto un'etichetta inglese con giorno e mese entrambi fino a 12 («Holdings as of 03/04/2026») è ambigua tra il formato britannico e quello statunitense: non si scrive, con un avviso. Con un numero oltre il 12 («10/24/2026») o un'etichetta italiana («Posizioni al») la data si legge senza dubbi.
- **Solo GICS** per i settori; nessuna conversione da ICB.
- **Paese secondo l'emittente**: domicilio, paese di rischio o di negoziazione, a seconda del file; il report dice quale colonna ha letto.
- Lingue: italiano e inglese. Niente PDF né XLS del vecchio Excel: si esporta in XLSX o CSV.

## Licenza dei file

I file delle posizioni sono soggetti alle condizioni d'uso dell'emittente: **non si ridistribuiscono**. Il plugin non li scarica e non li contiene; restano nella cartella di lavoro di chi li usa. I test del plugin usano file sintetici con lo stesso layout.

## Se un nome non è riconosciuto

Lo script si ferma ed elenca **tutti** i settori o paesi che non riconosce, con il loro peso: non li indovina e non li mette in «altro», perché un errore silenzioso cambierebbe la diagnosi. Va segnalato il nome (per esempio aprendo una issue sul repository del plugin) per aggiungerlo ai sinonimi (`SINONIMI_COLONNE`, `_VARIANTI_SETTORI`, l'elenco dei paesi) con un test. Nel frattempo si può correggere il nome nella propria copia del file, o compilare a mano le righe di quello strumento in `composizione.csv`.
