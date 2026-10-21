# Ribilanciamento multi-broker: ottimizzazione globale dello zainetto

Quando il portafoglio è diviso su **più broker**, il ribilanciamento tax-aware cambia in un modo che il caso a broker unico nasconde. Questa reference spiega il vincolo e la logica di ottimizzazione, ed è implementata in `assets/ribilanciamento-multibroker.py`.

## Il vincolo: la compensazione non attraversa i broker

In regime amministrato ogni intermediario è un **conto fiscale separato**, con il **proprio zainetto**. La conseguenza operativa è netta: **una minusvalenza realizzata presso il broker A può compensare solo plusvalenze realizzate presso il broker A.** Non puoi usare lo zainetto del broker A contro una plus realizzata sul broker B. (Per consolidare ci sono due vie, entrambe fuori dallo scope del ribilanciamento: chiudere il rapporto e farsi certificare le minus residue, che si portano su un altro rapporto con gli stessi intestatari fino alla scadenza originaria (art. 6 c. 5 D.Lgs. 461/97); oppure il regime dichiarativo, dove plus e minus di tutti i conti confluiscono nella stessa dichiarazione. Vedi `it-tax-optimization/references/multi-intermediario.md`.)

Questo è già noto come anti-pattern ("lo zainetto è per-intermediario"), ma ha una conseguenza costruttiva che la skill base non sfrutta: nel ribilanciamento multi-broker non conta solo **cosa** vendere (quale classe sovrappesata ridurre), ma **dove** venderlo.

## La doppia ottimizzazione: broker × tipo fiscale

Quando per ribilanciare devi ridurre una classe sovrappesata e sei costretto a realizzare plusvalenze (Leva 4), due dimensioni determinano il costo:

1. **Il broker.** Una plusvalenza va realizzata, quando possibile, presso il broker che ha **zainetto capiente**, così la compensazione la azzera. Realizzare la stessa plus presso un broker senza zainetto la lascia tassata al 26%.
2. **Il tipo fiscale dello strumento.** Lo zainetto compensa solo i **redditi diversi** (azioni dirette, certificates, ETC). Le plusvalenze su **ETF e fondi**, armonizzati UCITS e non armonizzati, sono **reddito di capitale** e **non sono mai compensabili**, nemmeno se c'è zainetto sullo stesso broker. Quindi tra due posizioni della stessa classe sovrappesata, quella "diverso" presso un broker con zainetto è fiscalmente molto più economica da vendere di quella "capitale".

La combinazione delle due dà la regola di priorità per le vendite di Leva 4:

> Vendi per prime le posizioni **reddito diverso** presso i broker che hanno **zainetto** (la plus viene assorbita, costo netto ≈ zero), poi quelle a plus latente minore, e per ultime le posizioni **capitale** o quelle presso broker **senza** zainetto (dove la plus è comunque tassata).

E specularmente per gli acquisti: comprare la classe sottopesata presso il broker dove conservi (o vuoi costruire) capacità di harvesting futura preserva flessibilità, anche se l'acquisto in sé è fiscalmente neutro.

## Esempio (lo stesso dello script)

Patrimonio €100.000 su due broker. Target 60% azionario / 30% obbligazionario / 10% monetario. Azionario al 68% (sovrappeso +8%), obbligazionario al 24% (sottopeso −6%), monetario all'8% (in banda).

Posizioni azionarie:
- Fineco — ETF World UCITS (**capitale**), €40.000, plus +€10.000
- Fineco — azioni dirette (**diverso**), €10.000, plus +€4.000
- Directa — ETF World UCITS (**capitale**), €18.000, plus +€3.000

Zainetto: **Fineco €5.000** (in scadenza), Directa €0.

Per riportare l'azionario a target servono **−€8.000**. La scelta ingenua venderebbe pro-quota o la posizione più grande (l'ETF capitale da €40.000): ma quella plus è **non compensabile**, quindi pagheresti imposta. La scelta ottimizzata vende invece **gli €8.000 della posizione "diverso" presso Fineco**: realizza una plus pro-rata di €3.200, **interamente compensata** dai €5.000 di zainetto Fineco → **imposta €0**, e per giunta consuma zainetto che altrimenti sarebbe evaporato. Lo zainetto Fineco scende a €1.800. La cassa (€8.000) compra €6.000 di obbligazionario e €2.000 di monetario (che così arriva a target come effetto collaterale).

**Costo fiscale del ribilanciamento: €0**, contro i ~€520 che sarebbero costati vendendo l'ETF capitale. È la stessa correzione di drift, ma la doppia ottimizzazione broker × tipo la rende gratuita.

## Cosa fa lo script

`assets/ribilanciamento-multibroker.py` prende le posizioni (con broker, classe, tipo fiscale, controvalore e plus/minus latente), lo zainetto per broker, l'allocazione target e i flussi disponibili, e produce: la tabella di drift con la decisione di banda, il piano di vendite **ottimizzato per broker e tipo** (con la compensazione esplicitata), gli acquisti per riempire le sottopesate, il costo fiscale totale, lo zainetto residuo per broker e l'allocazione risultante. Tutti i parametri sono editabili in testa al file; i default sono il caso di validazione qui sopra (costo atteso €0). Integra anche le **bande dinamiche** (vedi `bande-dinamiche.md`).

Caveat: lo strumento calcola i realizzi parziali **pro-rata** sul controvalore della posizione. In amministrato è il calcolo esatto, perché la plus si determina sul costo medio ponderato (art. 6 c. 4 D.Lgs. 461/97): sarebbe un'approssimazione solo per un conto in dichiarativo, dove vale il LIFO. E lo zainetto va sempre verificato per broker, con l'anno di formazione, sul portale dell'intermediario.

Cross-reference: `coordinamento-zainetto.md` (il protocollo di fine anno con `it-tax-optimization`, dove le minus in scadenza incontrano le vendite di ribilanciamento) e `it-tax-optimization/references/multi-intermediario.md` (le regole della frammentazione su più broker).
