# Composizione degli ETF: l'importatore

> ⚠️ Strumento di pianificazione personale, non consulenza finanziaria. La composizione è quella dichiarata dall'emittente alla data del file.

## Indice

- A cosa serve
- Come si usa
- Dove si scarica il file delle posizioni
- Cosa legge e cosa esclude
- Il file composizione.csv
- Stato dei formati
- Il look-through del portafoglio
- Limiti
- Licenza dei file
- Se un nome non è riconosciuto

## A cosa serve

La diagnosi 4 del capitale umano confronta il settore del proprio lavoro con la parte azionaria del portafoglio (vedi `capitale-umano.md`). Serve sapere quanto pesa ogni settore dentro ciascun ETF. L'importatore lo ricava dal **file delle posizioni** del fondo, cioè l'elenco completo dei titoli con il loro peso, che ogni emittente pubblica nella pagina dell'ETF. Lo script aggrega i titoli per **settore GICS** e per **paese** (codice ISO 3166-1 alpha-2), tiene i **primi dieci titoli** per peso e scrive `composizione.csv`. Paesi e titoli servono al look-through del portafoglio (sezione in fondo), i settori anche alla diagnosi 4.

## Come si usa

Dalla cartella di lavoro, un `--file` e un `--strumento` per ogni ETF:

```
python "${CLAUDE_SKILL_DIR}/assets/importa-composizione-etf.py" --file swda.csv --strumento "ETF MSCI World" \
    --file xdem.xlsx --strumento "ETF Momentum" [--out composizione.csv] [--json composizione.json]
python "${CLAUDE_SKILL_DIR}/assets/capitale-umano.py" --dati capitale-umano.json --composizione composizione.csv
```

- `--strumento` è la **chiave** con cui le posizioni trovano la composizione: l'**ISIN** (alias `--isin`) quando le posizioni vengono dall'estratto del broker, altrimenti il testo **esatto** del campo `strumento` delle posizioni nel JSON del capitale umano (maiuscole e spazi compresi). Il confronto avviene prima per ISIN e poi per nome; se nessuno coincide, lo strumento finisce tra quelli «senza composizione» e i report lo elencano per nome.
- Se `composizione.csv` esiste già, si sostituiscono solo le righe degli strumenti importati; le altre, comprese quelle compilate a mano, restano. Un file nel vecchio formato `strumento;settore;peso` viene convertito nel nuovo, con gli stessi pesi.
- `--emittente ishares|xtrackers|vanguard|amundi|spdr` forza la scheda dell'emittente quando il riconoscimento automatico (dal preambolo del file o dal suo nome) non basta.
- `--json FILE` scrive anche il risultato strutturato (pesi in frazione); `--json -` lo stampa da solo su stdout (gli eventuali `--set` si annotano su stderr).
- Un errore (file sbagliato, nome sconosciuto, pesi che non tornano, `--out` o `--json` in una cartella che non esiste) ferma lo script con `ERRORE:` prima di scrivere: `composizione.csv` resta com'era e il JSON non nasce.
- `--set` cambia le tabelle in testa allo script (per esempio `--set "VALORI_LIQUIDITA=('cash', 'margin')"`); serve una tupla, con la virgola finale anche per un solo nome: `('cash',)`.

## Dove si scarica il file delle posizioni

Sempre dalla pagina del singolo ETF sul sito dell'emittente, nella sezione delle posizioni («Posizioni», «Holdings», «Portafoglio», «Composizione»), con il pulsante di download del file completo. Non va bene la scheda prodotto (factsheet) né il KID: riportano solo i primi dieci titoli o i pesi aggregati, e l'importatore lo dice («scarica il file delle posizioni»).

| Emittente | Formato tipico | Note |
|---|---|---|
| iShares (BlackRock) | CSV | Preambolo di qualche riga con nome del fondo e data («Fund Holdings as of», «Posizioni al»); dal sito italiano (file `iShare_<ticker>_holdings.csv`) solo «Al» e la data, una riga vuota, intestazioni e settori in italiano abbreviati («IT», «Comunicazione», «Generi di largo consumo»), campi tra virgolette con la virgola decimale |
| Xtrackers (DWS) | XLSX | Disclaimer in testa, intestazione alla riga 2 o 4, peso in frazione, data nel nome del foglio; dal sito tedesco («Constituent_<ISIN>.xlsx») le intestazioni restano in inglese e i valori sono in tedesco («Industrieunternehmen», «Vereinigte Staaten von Amerika», «Aktien», «unbekannt») |
| Vanguard | XLSX o CSV | Dal sito italiano («Dati delle partecipazioni»): «Al 30 set 2026» nel preambolo, pesi come testo con «%», colonna «Regione» con i codici ISO; per gli ETF su indici FTSE la classificazione dei settori è ICB: vedi sotto |
| Amundi | XLSX | Due file dalla pagina dell'ETF. La **«Composizione dell'indice»** non elenca i titoli ma la ripartizione per settore e per paese su fogli separati («Ripartizione Settoriale», «Ripartizione Geografica»): l'importatore la legge come **file di ripartizione** (vedi sotto). Il **«Fund Holdings»** è l'elenco dei titoli, con intestazioni in inglese («ISIN code», «Name», «Asset class», «Weight», «Sector», «Country») e la data dd/mm/aaaa anche sotto l'etichetta inglese; per un ETF a swap sono il **collaterale**, e il file lo dichiara («Replication method: Synthetic»). Entrambi hanno uno stile Excel non valido, che l'importatore aggira |
| SPDR (State Street) | XLSX | Preambolo con «Holdings As Of», paese di negoziazione («Trade Country Name»), righe «Unassigned» per i contratti di cambio |

Se il sito apre la pagina invece di scaricare il file (capita quando si copia il link del pulsante), l'importatore riconosce l'HTML e chiede di usare il pulsante di download.

**File di ripartizione.** Un XLSX con fogli chiamati «Ripartizione Settoriale» e «Ripartizione Geografica» (o «Sector breakdown», «Répartition sectorielle», «Sektoraufteilung»…) non elenca i titoli: ogni foglio ha una tabella «nome;peso» già aggregata. L'importatore la legge così com'è, con le stesse esclusioni delle righe non classificate («Altro»), e scrive settori e paesi ma nessuna riga `titolo`; lo dice con un avviso, perché i pesi sono quelli dell'**indice** (non del fondo) e per i primi titoli serve il file delle posizioni. Se il foglio di stile dell'XLSX non è valido (i file di Amundi del novembre 2026), lo rilegge senza stili e lo dice.

**Replica sintetica.** Se il preambolo dichiara la replica sintetica («Replication method: Synthetic», «replica sintetica»), le posizioni sono il paniere di collaterale dello swap e non l'esposizione all'indice: l'importatore le scrive lo stesso, ma lo dice nel report, nel JSON (`replica_sintetica`) e nel commento del CSV, perché settori, paesi e titoli descrivono il collaterale. Per l'esposizione vera serve la composizione dell'indice.

## Cosa legge e cosa esclude

La riga d'intestazione si cerca nelle prime 40 righe con tabelle di sinonimi in italiano, inglese, tedesco e francese: peso (`Weight (%)`, `Weighting`, `Percent of Fund`, `Ponderazione (%)`, `Peso`, `Gewichtung (%)`, `Poids (%)`…), settore (`Sector`, `Sector Classification`, `Industry Classification`, `Settore`, `Branche`, `Secteur`…), paese (`Location`, `Country`, `Trade Country Name`, `Area geografica`, `Paese`, `Land`, `Pays`…), asset class (`Asset Class`, `Type of Security`, `Wertpapierart`, `Classe d'actifs`…). Le stesse tabelle coprono i nomi dei settori GICS (`Informationstechnologie`, `Technologies de l'information`…), le esclusioni (`Barmittel`, `Liquidités`, `Anleihen`, `Obligations`, `Unbekannt`, `Non classé`…), le etichette della data (`Stand`, `Stichtag`, `Données au`…) e i nomi tedeschi e francesi dei paesi dei file reali; un paese assente nelle tabelle si legge dal codice ISO. In tedesco e francese `Technologie`, `Telekommunikation`/`Télécommunications` e `Grundstoffe`/`Matériaux de base` sono nomi ICB, `Informationstechnologie`/`Technologies de l'information`, `Kommunikationsdienste`/`Services de communication` e `Roh-, Hilfs- & Betriebsstoffe`/`Matériaux` nomi GICS. Il preambolo sopra e il disclaimer sotto non contano. La scala dei pesi (frazione o percento) si deduce dalla somma.

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
ETF MSCI World;titolo;NVIDIA CORP;5,12
```

UTF-8 con BOM, separatore `;`, virgola decimale, pesi in percento con due decimali: si apre in Excel italiano. Le righe `settore` e `paese` sono rinormalizzate a 100; le righe `titolo` (i primi `N_TITOLI`, dieci, per peso, liquidità e derivati esclusi) portano il **peso nel fondo** così com'è, e sommate danno la quota del fondo coperta dai primi titoli. `capitale-umano.py` legge le righe `settore` e salta le altre; accetta anche il vecchio formato `strumento;settore;peso` compilato a mano.

## Stato dei formati

| Emittente | Layout | Verifica |
|---|---|---|
| Xtrackers | XLSX dal sito britannico in inglese | file reale, 25/10/2026 |
| SPDR | XLSX dal sito EMEA in inglese | file reale, 25/10/2026 |
| iShares | CSV dal sito italiano (`iShare_SWDA_holdings.csv`, MSCI World) | file reale, 7/11/2026 |
| iShares | CSV dal sito britannico | da confermare su un file reale |
| Vanguard | XLSX dal sito italiano («Dati delle partecipazioni», FTSE All-World, ICB: solo paesi) | file reale, 7/11/2026 |
| Amundi | XLSX dal sito italiano («Composizione dell'indice»: file di ripartizione, senza titoli) | file reale, 7/11/2026 |
| Amundi | XLSX «Fund Holdings» (elenco dei titoli, intestazioni inglesi; ETF a swap: collaterale) | file reale, 7/11/2026 |
| Xtrackers | XLSX dal sito tedesco («Constituent_<ISIN>.xlsx», intestazioni inglesi e valori tedeschi) | file reale, 7/11/2026 |
| Amundi | sito tedesco e francese; Xtrackers con le intestazioni in tedesco | da confermare su un file reale (fixture sintetiche) |

«Da confermare» vuol dire che i sinonimi coprono i formati documentati ma nessun file reale è ancora passato dall'importatore: se qualcosa non torna, lo script si ferma e dice cosa ha visto. I file reali non entrano nel repository: le fixture dei test ne riproducono il layout.

## Il look-through del portafoglio

`look-through-portafoglio.py` somma le composizioni di tutti gli ETF posseduti, **pesate per controvalore**, e risponde a «cosa possiedo davvero?»:

```
python "${CLAUDE_SKILL_DIR}/assets/look-through-portafoglio.py" --composizione composizione.csv \
    --posizioni broker.json [--posizioni broker-2.json] [--json look-through.json]
```

- **Posizioni**: il `--json` di `importa-estratto-broker.py` (un file per broker; la stessa posizione su due broker è un'unica esposizione e si somma) oppure il `--dati` del capitale umano. Ogni posizione si confronta con il CSV per **ISIN** e poi per nome: con l'estratto del broker si importa ogni ETF con `--isin`.
- **Copertura**: per ogni dimensione (settori, paesi, titoli) contano solo le posizioni che la hanno nel CSV; i pesi sono rinormalizzati sulla **parte coperta** e la copertura (quota del controvalore totale) sta sempre accanto. Niente «altro» inventato: ciò che non si sa non entra nei pesi.
- **Titoli**: sono i primi dieci di ogni ETF, quindi la concentrazione sui titoli è un **minimo**, non il totale. Lo stesso titolo scritto in modo diverso da due emittenti («Apple Inc.», «APPLE INC») si somma con una chiave normalizzata del nome (senza punteggiatura, suffissi societari come Inc, Corp, SpA, SA, e classi di azioni); `da` nel JSON elenca gli ETF che contribuiscono, per accorgersi di quelli rimasti separati.
- **Posizioni dirette** (una singola azione, un BTP): non hanno un file delle posizioni; si compilano **a mano** nel CSV con l'ISIN della posizione come chiave, per esempio `IT0005454241;paese;IT;100` e, se si vuole il titolo tra i primi, `IT0005454241;titolo;BTP Futura 2037;100`. Una riga `titolo` al 100% da sola identifica una posizione diretta: nel report a terminale e nel JSON compare (`diretto: true`), nel cruscotto no, perché è una posizione dell'utente e non un titolo di un ETF. Lo script non deduce il paese dall'ISIN: un ISIN irlandese può essere un ETF di titoli americani.
- **Pesi scritti a mano**: in percento, come li scrive l'importatore (`5` o `5,00` per il 5%, `0,05` è lo 0,05%). I pesi dei titoli seguono la scala delle altre righe dello strumento; quando sono tutti fino a 1 e la scala è un'inferenza, il report lo dice con un avviso.
- **Senza composizione**: le posizioni senza riscontro restano fuori dai pesi e il report le elenca per nome (e ISIN), con il controvalore: si importa il file dell'emittente, o si aggiungono le righe.
- Il JSON (`controvalore_totale`, `posizioni`, `senza_composizione`, `copertura`, `settori`, `paesi`, `titoli`, `quota_primi_titoli`) entra nel passo 3 di `it-revisione` e nel cruscotto grafico, dove passano solo gli aggregati: niente nomi né ISIN delle posizioni.
- Ogni ETF ha la data del suo file (nel commento del CSV): il look-through non le allinea. Il fondo pensione non entra, perché la sua composizione non è disponibile.

## Limiti

- **Posizioni del fondo, non dell'indice**: un ETF a replica campionaria espone posizioni diverse dall'indice; un ETF sintetico (swap) può pubblicare il paniere di collaterale. Un file di ripartizione dice invece la composizione dell'**indice**: utile per settori e paesi, muto sui titoli.
- **Fotografia a una data**: la composizione cambia; la data delle posizioni è nel commento del CSV e va riguardata a ogni revisione annuale. Una data numerica sotto un'etichetta inglese con giorno e mese entrambi fino a 12 («Holdings as of 03/04/2026») è ambigua tra il formato britannico e quello statunitense: non si scrive, con un avviso. Con un numero oltre il 12 («10/24/2026») o un'etichetta italiana («Posizioni al») la data si legge senza dubbi.
- **Solo GICS** per i settori; nessuna conversione da ICB.
- **Paese secondo l'emittente**: domicilio, paese di rischio o di negoziazione, a seconda del file; il report dice quale colonna ha letto.
- Lingue: italiano, inglese, tedesco e francese (i siti tedesco e francese di Xtrackers e Amundi, verificati su file sintetici con il loro layout, non su file reali). Niente PDF né XLS del vecchio Excel: si esporta in XLSX o CSV.

## Licenza dei file

I file delle posizioni sono soggetti alle condizioni d'uso dell'emittente: **non si ridistribuiscono**. Il plugin non li scarica e non li contiene; restano nella cartella di lavoro di chi li usa. I test del plugin usano file sintetici con lo stesso layout.

## Se un nome non è riconosciuto

Lo script si ferma ed elenca **tutti** i settori o paesi che non riconosce, con il loro peso: non li indovina e non li mette in «altro», perché un errore silenzioso cambierebbe la diagnosi. Va segnalato il nome (per esempio aprendo una issue sul repository del plugin) per aggiungerlo ai sinonimi (`SINONIMI_COLONNE`, `_VARIANTI_SETTORI`, l'elenco dei paesi) con un test. Nel frattempo si può correggere il nome nella propria copia del file, o compilare a mano le righe di quello strumento in `composizione.csv`.
