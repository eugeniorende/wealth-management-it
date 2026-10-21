# Allocazione di una somma liquida tra gli obiettivi

Quando si parte da una **somma liquida** da investire — il caso tipico è chi liquida un vecchio gestito e costruisce un portafoglio da zero — la domanda non è "voglio un 60/40", ma: *dati i miei obiettivi, il mio orizzonte e il mio profilo, quanto di questo capitale dedico a ogni secchiello, e qual è di conseguenza la mia allocazione aggregata tra azioni, obbligazioni e liquidità?* La risposta è un **risultato**, non una scelta dall'alto: si distribuisce il capitale tra gli obiettivi e l'allocazione complessiva emerge dalla somma.

## Capitale richiesto oggi: present value, con un'eccezione per le riserve

Ogni obiettivo richiede un capitale **oggi** che dipende dalla sua natura.

Un obiettivo **terminante** (università, casa) si spende a una data futura: il capitale da mettere adesso è il suo **present value**, cioè quanto, investito al rendimento atteso del profilo, cresce fino al target nominale entro la scadenza:

```
PV = target_oggi × ((1 + inflazione) / (1 + rendimento))^anni
```

Se il rendimento supera l'inflazione, il PV è inferiore al target di oggi (il capitale cresce in termini reali); se il rendimento è sotto l'inflazione — il caso della liquidità — il PV è *superiore*, perché il potere d'acquisto si erode.

Un terminante però **de-riska** negli ultimi anni (glide path, finestra in Parametri!B7): in quegli anni il rendimento atteso scende verso quello della Preservazione. L'allocatore lo sconta, come il versamento del foglio:

```
PV = target_oggi × (1 + inflazione)^anni / Π (1 + rendimento_anno)
```

dove `rendimento_anno` è quello del profilo finché mancano più anni della finestra, poi scende linearmente con la quota azionaria. È il calendario annuale esatto (`motore_bootstrap.crescita_glide`), non l'approssimazione in due fasi del versamento. Sull'obiettivo d'esempio a 20 anni (Crescita) il capitale richiesto oggi passa da €50.928 a €57.140 (+12%) rispetto al rendimento pieno.

Una riserva **permanente** (fondo di emergenza) è un caso diverso: non è in crescita verso una scadenza, la vuoi **disponibile adesso** al suo valore pieno. Il capitale richiesto è quindi l'**importo pieno di oggi**, tenuto in liquidità, non un valore scontato su un orizzonte. Trattarla a present value come gli altri obiettivi sarebbe un errore concettuale: una riserva di emergenza scontata di qualche anno non sarebbe più una riserva. (Il comportamento è disattivabile, ma è il default corretto.)

In entrambi i casi si sottrae il **già accantonato**: il capitale che è già correttamente nel secchiello riduce quanto serve attingere dalla somma.

## L'ordine: priorità, poi orizzonte

La somma si alloca **in ordine di priorità** — prima gli essenziali, poi gli importanti, poi i desiderabili — e a parità di priorità per **orizzonte crescente** (prima ciò che scade prima). Si finanzia ogni obiettivo fino al suo capitale richiesto, finché la somma non si esaurisce. Questo garantisce che, se il capitale non basta, a restare scoperto sia il discrezionale e il lontano, non l'essenziale e l'imminente.

Da qui due esiti possibili. Se il capitale **avanza**, l'eccedenza è **capitale libero**: non corrisponde ad alcun obiettivo dichiarato. Se il capitale **non basta**, gli obiettivi a priorità più bassa restano da finanziare con i **versamenti** mensili — ed è il Monte Carlo a dire quanto serve al mese e con quale probabilità.

## Il capitale libero: il punto su cui essere onesti

L'eccedenza è la parte più delicata, perché spesso è anche la più grande: chi deploya €130.000 con un fondo emergenza e un obiettivo università può ritrovarsi con metà somma "libera". Quella metà non è neutra — il modo in cui la si alloca **domina l'aggregato**. Trattarla come crescita di lungo termine a profilo azionario è ragionevole *se* esiste davvero un obiettivo di lungo termine dietro (libertà finanziaria, integrazione pensionistica), ma è una **scelta**, non un automatismo. Lo strumento la rende esplicita e invita a **formalizzare** quell'obiettivo — dargli un orizzonte e un target — invece di lasciarla come residuo silenzioso, perché l'allocazione aggregata dipende da questa decisione più che da ogni altra. Spesso il capitale libero non è un blocco unico ma alimenta **più obiettivi di lungo termine** — per esempio un'integrazione alla pensione e un'eredità — che meritano pesi e profili diversi: l'integrazione si spende in decumulo dopo il pensionamento e va de-riskata avvicinandosi, l'eredità che passa agli eredi senza mai essere liquidata ha orizzonte di fatto perpetuo e nessun rischio di sequenza da proteggere, quindi tollera anche un 100% azionario. Dividere il capitale libero tra questi obiettivi (ciascuno col suo profilo) e cambiarne i pesi è la singola scelta che sposta di più l'allocazione aggregata.

## La vista aggregata su tre classi

Sommati i secchielli, l'allocazione complessiva si scompone su **tre** classi, non due. La quota **azionaria** è la somma, su ogni secchiello, del capitale per la sua percentuale azionaria di profilo. La parte non azionaria si divide tra **liquidità** e **obbligazioni**: è liquidità la parte difensiva dei secchielli a profilo Preservazione (le riserve tenute liquide), è obbligazionaria quella degli obiettivi investiti (lo sleeve difensivo). Su orizzonti molto brevi anche la quota difensiva di un obiettivo investito è meglio tenerla liquida. Questa distinzione azioni/obbligazioni/liquidità è precisamente l'allocazione target che il pianificatore Excel e `it-rebalance` mantengono.

## Limiti dichiarati

È una vista **lump sum**: il present value assume di finanziare l'obiettivo col solo capitale. Se si versa anche mensilmente, il capitale richiesto scende e l'eccedenza cresce — i versamenti sono la leva separata, gestita dal Monte Carlo. E un punto pratico spesso dimenticato: **liquidare il vecchio gestito non è gratis**. Vendere fondi realizza plusvalenze tassate al 26% (12,5% sulla quota in titoli di Stato), e la plus al rimborso di un fondo è **reddito di capitale**, non compensabile con le minusvalenze dello zainetto. Prima di reinvestire conviene guardare con `it-tax-optimization` l'ordine di smontaggio.

Cross-reference: `assets/allocatore-capitale.py` (implementazione), `matematica-accumulo.md` (la matematica del valore futuro per i versamenti), `monte-carlo.md` (la leva dei versamenti e la probabilità), `asset-location.md` (in quale contenitore fiscale tenere ciascun secchiello).
