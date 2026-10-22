# Il metodo della revisione periodica

Reference di supporto alla skill `it-revisione`: con che cadenza fare il punto, come misurare il proprio rendimento senza ingannarsi, e come prioritizzare le azioni che emergono da domini diversi. Non è consulenza.

## La cadenza: una volta l'anno, più una finestra di fine anno

Per un risparmiatore di lungo periodo, **una revisione completa all'anno** è la cadenza giusta: abbastanza frequente da correggere la rotta, abbastanza rara da non cedere alla tentazione di intervenire sul rumore di mercato. Rivedere il portafoglio ogni settimana è controproducente — porta a tradare sul rumore e a inseguire la performance.

C'è però un **secondo appuntamento con scadenza fissa**: la finestra di **fine anno fiscale (novembre-dicembre)**. È il momento in cui maturano scadenze che non aspettano la revisione annuale: le **minusvalenze in scadenza** (la finestra di 4 anni; quelle del quarto anno evaporano il 31/12 se non compensate), il **versamento al fondo pensione** entro il 31/12 per ottenere la deduzione dell'anno, la **comunicazione al fondo dei contributi non dedotti** dell'anno precedente (entro il 31/12, art. 8 c. 4 D.Lgs. 252/2005: senza, in uscita quella parte viene tassata di nuovo) e l'**harvesting** di fine anno.

Per il fondo pensione servono due numeri. Per il dipendente lo **spazio deducibile residuo** dell'anno è max(0, €5.300 − datore − dovuto − volontari già versati nell'anno): il plafond meno il contributo del datore, il contributo minimo del lavoratore previsto dal contratto e i volontari già versati, mentre il TFR conferito non conta. È il massimo che i versamenti volontari possono ancora dedurre entro il 31/12, un tetto fiscale e non un importo consigliato; il foglio Complementare dell'Excel di `it-pianificazione` lo mostra per l'inizio dell'anno. Per il forfettario la deduzione arriva solo fino agli altri redditi IRPEF (`it-pianificazione-autonomi`). I **contributi non dedotti** (oltre il plafond, o versati da un forfettario senza capienza IRPEF) vanno invece comunicati al fondo: se non lo sono, in uscita pagano di nuovo l'aliquota del fondo, cioè si perde il 9-15% di quella parte (23% se la posizione esce con un'anticipazione non sanitaria o un riscatto per altre cause). Conviene quindi far coincidere la revisione annuale con la finestra di fine anno, o tenere a fine anno una mini-revisione focalizzata sulla fiscalità.

Oltre alla cadenza fissa, una revisione **straordinaria** è giustificata da un **evento della vita** che cambia il piano: variazione importante del reddito, nascita di un figlio, acquisto casa, un nuovo obiettivo, un'eredità, un cambio di lavoro (es. da dipendente a P.IVA, che cambia tutta la previdenza). Non da un calo di mercato: i cali fanno parte del piano e di norma richiedono di **non** fare nulla.

## Misurare il rendimento senza ingannarsi

È l'errore più comune nel fare il punto da soli: **confondere i versamenti con il rendimento**. Se a inizio anno avevi €70.000, hai versato €9.000 e a fine anno hai €88.000, il saldo è cresciuto di €18.000 — ma non hai "reso" €18.000. Metà (€9.000) è denaro tuo messo da parte. Il rendimento vero è la parte restante.

La decomposizione di base, sullo stesso periodo:

```
variazione saldo = versamenti netti + rendimento di mercato
rendimento di mercato = (saldo finale − saldo iniziale) − versamenti netti
```

In percentuale, il rendimento va rapportato al **capitale medio investito** nel periodo, non al saldo finale. Una buona approssimazione fai-da-te è il **metodo Dietz semplificato**:

```
rendimento % ≈ rendimento di mercato / (saldo iniziale + versamenti netti / 2)
```

Questo è un rendimento **money-weighted** (pesato per il denaro): misura il risultato del **tuo** capitale, tenendo conto di quando hai versato. È il numero che risponde a "quanto ha reso il mio investimento". Il cruscotto (`cruscotto-patrimoniale.xlsx`, foglio Andamento) lo calcola.

Esiste anche un secondo modo di misurare, il **time-weighted return (TWR)**, che **neutralizza** i flussi (versamenti e prelievi) per isolare la bravura della strategia, indipendentemente da quando hai messo i soldi. È il rendimento "ufficiale" dei fondi e quello da confrontare con un **benchmark** (es. un indice 60/40). Si calcola spezzando il periodo a **ogni flusso** e moltiplicando i rendimenti dei sotto-periodi: per ciascun sotto-periodo `r = (valore_fine − flusso) / valore_inizio − 1`, poi `TWR = Π(1 + r) − 1`. Il cruscotto (`cruscotto-patrimoniale.xlsx`, foglio **Rendimento TWR**) lo fa: basta inserire una riga per ogni data di rilevazione con valore e flusso, e calcola il TWR (incatenando i sotto-periodi), il TWR annualizzato, e il MWR **esatto** sugli stessi dati (via XIRR sui flussi datati, più preciso del Dietz aggregato del foglio Andamento).

Il confronto tra i due è esso stesso informativo: la **differenza TWR − MWR è l'effetto del timing dei flussi**. Se il MWR è maggiore del TWR, i versamenti sono caduti prima di periodi forti (timing favorevole); se è minore, prima di periodi deboli (hai versato vicino ai massimi). In sintesi: **money-weighted** per sapere quanto hai reso **tu**, **time-weighted** per giudicare la **strategia** e confrontarla con un benchmark. Per il singolo risparmiatore con un PAC, il money-weighted è di norma il numero più rappresentativo del proprio risultato; il time-weighted serve quando vuoi capire se la strategia, di per sé, batte il mercato.

Infine, **sempre in termini reali**: l'inflazione erode. Un +5% nominale con inflazione al 3% è circa +2% reale, ed è il potere d'acquisto guadagnato che conta davvero. Formula: `(1 + rendimento nominale) / (1 + inflazione) − 1`.

## Costi dell'anno: trasparenza, non correzione

I costi sono l'unica parte del rendimento interamente sotto il controllo dell'investitore, e la revisione annuale è il momento per guardarli. Si annotano:
- **bollo del dossier**: 0,2% del controvalore a fine periodo rendicontato, senza tetto per le persone fisiche; il fondo pensione ne è esente;
- **commissioni e Tobin tax** pagate nell'anno, dall'estratto del broker;
- **TER medio ponderato** del dossier, il costo implicito dei fondi e degli ETF;
- **ISC del fondo pensione**, da confrontare con l'ISC medio della stessa tipologia di forma pubblicato da COVIP: se è molto più alto, il trasferimento a un fondo meno caro (possibile dopo 2 anni di partecipazione) è spesso la decisione a più alto valore, vedi `it-pianificazione/references/previdenza-complementare.md`.

Il rendimento calcolato sui valori di mercato (foglio Andamento) è già al netto di TER, ISC, commissioni e bollo addebitati nel dossier: questi numeri servono a confrontare i costi anno su anno e con le alternative, **non** a sottrarli una seconda volta.

## Prioritizzare le azioni che emergono

La revisione tocca quattro domini (pensione, obiettivi, fiscalità, allocazione) e ne esce una lista di possibili azioni. Ordinarle bene è il vero valore della sintesi. Tre criteri, in ordine:

1. **Scadenza prima di tutto.** Le azioni con una **data limite** vanno fatte entro quella data, a prescindere dal resto: le minusvalenze in scadenza al 31/12, il versamento al fondo pensione entro il 31/12 per la deduzione dell'anno, la comunicazione al fondo dei contributi non dedotti dell'anno precedente. A fine anno sono la priorità operativa.
2. **Poi l'impatto strutturale.** Tra le azioni senza scadenza, contano di più quelle ad alto impatto di lungo periodo: colmare un **gap previdenziale** (aumentare il versamento al fondo pensione quando il tasso di sostituzione proiettato è sotto l'obiettivo), o intervenire su un **obiettivo a rischio** (probabilità Monte Carlo sotto soglia → aumentare il versamento o rivedere il target/orizzonte). Qui vale il principio: **agire presto** vale più che agire tanto, per via della capitalizzazione.
3. **Infine la manutenzione.** Il ribilanciamento quando il drift supera le bande, il de-risking del glide path per gli obiettivi in avvicinamento. Importante, ma raramente urgente.

## Le azioni cross-dominio: dove la sintesi rende

Il motivo per cui la revisione vale più della somma delle singole skill è che le azioni migliori **risolvono più cose insieme**. Tre esempi ricorrenti:

- **Ribilanciare a fine anno usando le minus in scadenza.** Vendere la classe sovrappesata genera plusvalenze; compensarle con le minusvalenze che altrimenti evaporerebbero il 31/12 azzera l'attrito fiscale del ribilanciamento. Un'azione sola corregge il drift **e** salva le minus (vedi `it-rebalance/references/coordinamento-zainetto.md`).
- **Indirizzare il versamento annuale dove serve di più.** Lo stesso versamento può andare (a) al fondo pensione se c'è un gap previdenziale e si è in un regime dove è deducibile (deduzione + colma il gap), (b) all'obiettivo più a rischio, o (c) alla classe sottopesata — ribilanciando **tramite i flussi** invece che con le vendite, cioè senza realizzare plusvalenze. Una scelta che pesa pensione, obiettivi, fiscalità e allocazione in un colpo solo.
- **Coordinare il de-risking di un obiettivo con l'harvesting.** Vendere azionario per de-riskare un obiettivo in avvicinamento può generare plusvalenze: programmarlo nello stesso anno in cui ci sono minus da compensare ne riduce il costo.

Riconoscere queste combinazioni — invece di trattare pensione, obiettivi, fisco e allocazione come quattro liste separate — è esattamente ciò che la revisione fa e che nessuna delle skill specifiche, da sola, può fare.

Cross-reference: `it-pianificazione` e `it-pianificazione-autonomi` (il gap previdenziale), `it-pianificazione-obiettivi` (avanzamento e probabilità degli obiettivi, glide path), `it-tax-optimization` (minus in scadenza, harvesting), `it-rebalance` (drift e ribilanciamento tax-aware). La revisione le orchestra, non le duplica.
