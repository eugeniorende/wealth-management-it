# Glide path automatico (calendario di de-risking)

Questa reference spiega la logica, i parametri e i limiti del glide path automatico. Lo strumento è `assets/glidepath-obiettivi.py`, che genera il calendario di de-risking che alimenta `it-rebalance`.

## Perché de-riskare

Un obiettivo con una data fissa (la retta dell'università, l'anticipo della casa) non può permettersi una correzione di mercato proprio quando i soldi servono. A 13% di volatilità, un crollo l'anno prima della scadenza può azzerare anni di crescita nel momento peggiore. Il glide path riduce progressivamente l'esposizione azionaria man mano che la scadenza si avvicina, per **bloccare il valore raggiunto**. È la risposta al rischio di sequenza (vedi `monte-carlo.md`): non elimina la volatilità, ma la sposta lontano dal momento critico.

Il prezzo del de-risking è un rendimento atteso più basso negli ultimi anni — ma su un obiettivo con scadenza fissa la certezza vale più del rendimento marginale.

## La formula

Per ogni obiettivo, la quota azionaria target dipende dagli anni residui alla scadenza:

```
finestra_effettiva = min(finestra_de-risking, orizzonte_obiettivo)

se quota_partenza <= atterraggio:          → quota_partenza   (già conservativo, niente da fare)
se anni_residui >= finestra_effettiva:     → quota_partenza   (ancora lontano: tiene la quota piena)
se anni_residui <= 0:                       → atterraggio       (alla scadenza)
altrimenti (dentro la finestra):
    frazione = (anni_residui / finestra_effettiva) ^ curvatura
    quota = atterraggio + (quota_partenza − atterraggio) × frazione
```

In parole: l'obiettivo tiene la quota azionaria del suo profilo finché manca più tempo della finestra di de-risking; poi scende fino alla quota di atterraggio entro la scadenza. Con `curvatura = 1` la discesa è **lineare**; con `curvatura < 1` tiene l'azionario **più alto all'inizio** della finestra e scende ripido vicino alla scadenza (più crescita, de-risking tardivo); con `curvatura > 1` de-riska prima e più dolcemente.

La `finestra_effettiva = min(finestra, orizzonte)` fa sì che:
- un obiettivo **lungo** (es. 19 anni) tenga la quota piena per anni, poi de-riski solo negli ultimi (es. 7);
- un obiettivo **corto** (es. 5 anni) de-riski sull'intera sua vita, partendo già dalla quota piena.

## I parametri (editabili)

In cima allo script:

| Parametro | Default | Significato |
|---|---|---|
| `FINESTRA_DERISK` | dal foglio (Parametri!B7: 7 anni) | Quanti anni prima della scadenza inizia il de-risking |
| `ATTERRAGGIO_AZ` | 0% | Quota azionaria target alla scadenza |
| `CURVATURA` | 1.0 | Forma della rampa: 1 lineare, <1 azionario alto più a lungo poi discesa ripida, >1 de-risking anticipato |

Come tararli:
- **Finestra più lunga** (es. 10 anni) = de-risking più graduale e prudente, ma rinuncia prima alla crescita. **Più corta** (es. 4-5) = tiene la crescita più a lungo, ma concentra il de-risking e lascia meno margine se il mercato gira male proprio in quegli anni.
- **Atterraggio 0%** = tutto liquido/sicuro alla scadenza, per obiettivi con data e importo rigidi. Un **atterraggio più alto** (es. 20-30%) ha senso per obiettivi senza una vera scadenza (es. "libertà finanziaria") o dove si può tollerare oscillazione anche alla fine.

La quota azionaria di partenza di ogni profilo è nella tabella Parametri del foglio Excel (colonna % Azionario), anch'essa editabile. La finestra sta nel foglio (Parametri!B7) perché la usano anche il versamento del foglio, il Monte Carlo e l'allocatore: cambiarla lì la cambia ovunque; `--set FINESTRA_DERISK=5` la sovrascrive solo per il singolo script.

## Il glide path nel versamento

Il de-risking abbassa il rendimento atteso proprio negli ultimi anni, quando il capitale è più grande: un versamento calcolato al rendimento pieno del profilo non basta. Per questo il versamento del foglio (Obiettivi, colonna I) è calcolato in due fasi: gli anni a quota piena al rendimento del profilo, poi gli anni di de-risking (colonna O) al loro rendimento medio (colonna P), che con la rampa lineare è la media tra il rendimento del profilo e quello di atterraggio (Preservazione). La quota di ciascun anno è quella del calendario a inizio anno: con la finestra di 7 anni si scende per 6 anni. Rispetto al calcolo anno per anno la formula sbaglia per difetto di meno dell'1,5%. Formule ed esempi in `matematica-accumulo.md`.

L'ordine di grandezza: sull'obiettivo d'esempio a 20 anni con profilo Crescita il versamento passa da €346 a €384 al mese (+11%); con il vecchio versamento a quota fissa il capitale finale, seguendo il glide path, si fermerebbe a circa il 90% del target. Sull'anticipo casa a 6 anni (Moderato) passa da €478 a €500. Lo stesso numero lo usano il Monte Carlo (che simula il percorso glide), questo script (per proiettare il capitale) e l'allocatore (per il capitale richiesto oggi).

## Le due viste

**Per obiettivo** — per ciascun obiettivo, la quota azionaria target a ogni anno. È la vista esatta e azionabile: ogni colonna è il target che `it-rebalance` mantiene per quel secchiello.

**Aggregata (portafoglio)** — la quota azionaria complessiva attesa a ogni anno, pesata per il **capitale proiettato** di ogni obiettivo ancora attivo. Mostra come l'esposizione totale al rischio del portafoglio evolve nel tempo. La proiezione del capitale (crescita + versamenti del foglio) usa il rendimento atteso di ciascun anno lungo il glide path. In fondo all'output lo script riepiloga i versamenti usati, gli stessi della colonna I del foglio.

## Obiettivi terminanti vs permanenti (flag)

Gli obiettivi si comportano in due modi diversi a scadenza, e il foglio Excel ha una colonna **Tipo** (menu a tendina) per distinguerli:

- **terminante** (default): l'obiettivo si *spende* a scadenza (la retta dell'università, l'anticipo della casa). De-riska secondo il glide path e, raggiunta la scadenza, **esce** dal portafoglio (il capitale viene speso). Nell'aggregato compare come `concl.` dopo la scadenza.
- **permanente**: l'obiettivo è una *riserva* che resta (il fondo di emergenza, o un patrimonio di lungo periodo che non si spende a una data). **Non de-riska** (tiene la quota azionaria del suo profilo, perché non ha una scadenza di spesa verso cui ridurre il rischio) e **non esce** dal portafoglio: la sua "scadenza" indica solo *quando è pienamente finanziato* (marcato `(piena)`).

Perché conta: un obiettivo permanente che resta nel portafoglio **smussa l'aggregato** invece di farlo saltare. Senza il flag, quando il fondo di emergenza (0% azionario) "concludeva" e usciva dal calcolo, l'aggregato saltava verso l'alto (rimuovere una componente a 0% alza la media) — un artefatto fuorviante, perché il fondo di emergenza non si spende. Marcandolo permanente, resta come fetta stabile a bassa/zero quota azionaria e l'aggregato evolve in modo coerente.

La maggior parte degli obiettivi è terminante (casa, università, auto, viaggio: si spendono). Il caso permanente tipico è il fondo di emergenza; lo è anche un eventuale patrimonio di lungo periodo che non ha una data di liquidazione. La vista **per obiettivo** non dipende dal flag (ogni secchiello ha il suo target); il flag conta per l'**aggregato** e per capire quando un capitale lascia il portafoglio.

## Il collegamento con it-rebalance (e la fiscalità)

Il calendario di glide path è il **programma di spostamento dei target** che `it-rebalance` esegue. Ogni anno il target di un secchiello in de-risking si abbassa, e `it-rebalance` vende azionario per comprare obbligazionario/liquidità.

⚠️ **Ogni vendita in Italia è un evento fiscale** (vedi `it-rebalance` e `it-tax-optimization`): non esiste il tax-deferred. Quindi il de-risking non è gratis — genera plus/minus da gestire. Implicazioni:
- Il de-risking graduale (un po' all'anno) distribuisce gli eventi fiscali nel tempo, evitando di realizzare tutto in un colpo.
- Dove possibile, coordinare le vendite del de-risking con lo zainetto fiscale (compensare le plus con minus pregresse in scadenza).
- I nuovi versamenti possono fare parte del lavoro: indirizzare i versamenti verso la componente che deve crescere (obbligazionario, man mano che si de-riska) riduce la necessità di vendere azionario. È la leva "flussi" della gerarchia di `it-rebalance`.

## I limiti

1. **Proiezione deterministica del capitale**: l'aggregato pesa per il capitale proiettato al rendimento atteso, senza modellare la volatilità. È un'illustrazione della traiettoria, non una previsione.
2. **Glide lineare**: la discesa lineare è un'euristica ragionevole ma arbitraria; esistono glide path a forma diversa (convessi, a gradini). Il lineare è semplice e trasparente.
3. **Rendimento lineare nella quota durante la rampa**: man mano che un obiettivo de-riska il suo rendimento atteso scende, e versamento e proiezione ne tengono conto. Trattarlo come costante, come si faceva prima, sovrastimava il capitale finale di circa il 10% su orizzonti di 7 anni e più (profilo Crescita, finestra di default) e quindi sottostimava il versamento. Resta una semplificazione la linearità tra il portafoglio del profilo e quello di atterraggio.
4. **Costo fiscale non modellato nel calendario**: il calendario dice *cosa* fare, non quanto costa fiscalmente farlo; quello è compito di `it-rebalance` + `it-tax-optimization`.
5. **Glide solo per obiettivi terminanti**: gli obiettivi permanenti (flag Tipo) tengono la quota del profilo e non de-riskano, perché non hanno una data di spesa. Il prelievo da una riserva permanente è un'altra cosa, il decumulo: vedi `decumulo.md`.

Come sempre: non è consulenza di investimento; è un calendario metodologico, le % sono esempi editabili, e le scelte concrete restano dell'utente.

## Come eseguirlo

```bash
pip install openpyxl
python glidepath-obiettivi.py [percorso/pianificatore-obiettivi.xlsx]
```

Legge gli obiettivi e i parametri dal foglio Excel. Senza argomenti cerca `pianificatore-obiettivi.xlsx` nella stessa cartella. I parametri del glide path (finestra, atterraggio, curvatura) sono in cima allo script; la finestra di default si legge dal foglio.

## Heuristic per la skill

1. **Il glide path è per-obiettivo**: ogni obiettivo de-riska sulla *sua* data. La vista per-obiettivo è quella esatta che alimenta it-rebalance.
2. **Tenere la quota piena finché c'è tempo**: de-riskare troppo presto rinuncia a crescita inutilmente; la finestra (default 7 anni) concentra il de-risking dove serve.
3. **Atterraggio coerente con la rigidità dell'obiettivo**: 0% per obiettivi a data/importo fissi; più alto per obiettivi flessibili.
4. **Coordinare il de-risking con la fiscalità**: ogni vendita è un evento fiscale; distribuire nel tempo, usare i flussi, sfruttare lo zainetto.
5. **Comunicare i limiti**: proiezione deterministica, glide lineare euristico, costo fiscale a parte.
6. **Il de-risking costa versamento**: il versamento del foglio lo include già; chi ricalcola a mano al rendimento pieno del profilo sottostima il piano di circa il 10% sugli orizzonti lunghi.

## Obiettivi senza target ("il più possibile")

Un obiettivo può avere la colonna target vuota: significa "accumula il più possibile". Il glide path lo tratta così: nessun versamento "necessario" viene calcolato (non c'è un traguardo da centrare), si proietta il solo capitale assegnato, e la traiettoria azionaria segue le stesse regole degli altri — un terminante de-riska nella finestra e a scadenza si spende, un permanente tiene la quota del profilo per sempre. Nell'output è marcato `(max)`. Il caso tipico è la coppia "libertà finanziaria" (terminante, de-riska verso la data in cui il capitale servirà) ed "eredità" (permanente: mai liquidata, quindi senza rischio di sequenza, può restare piena).
