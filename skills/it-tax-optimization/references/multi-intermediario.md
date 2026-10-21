# Zainetto multi-intermediario

## Il principio

In **regime amministrato**, lo zainetto fiscale (registro delle minus pregresse) è **per-intermediario**, anzi per rapporto: le minus si compensano con le plus realizzate «nell'ambito del medesimo rapporto» (art. 6 c. 5 D.Lgs. 461/97 → art. 306 c. 6 TU 2027). Ogni broker tiene il proprio "libro" delle minus realizzate sui dossier presso di lui. Conseguenze:

- Le minus realizzate su Directa **non possono** compensare plus realizzate su Fineco finché il rapporto Directa resta aperto
- Il broker A non comunica con il broker B su questioni fiscali
- L'AdE non vede un quadro consolidato (in amministrato sei "esonerato" dalla dichiarazione su questi redditi, ma per il fisco non hai un cumulato)

In **regime dichiarativo**, invece, lo zainetto è dell'investitore: tu lo dichiari nel quadro RT del Modello Redditi PF e puoi cumulare cross-broker.

Tra i due c'è una terza via, spesso ignorata: alla **chiusura del rapporto** le minus residue vengono **certificate** e si portano su un altro rapporto (Caso 2).

## Implicazioni operative

### Caso 1: hai dossier su 2+ broker e minus distribuite

Scenario tipico: hai €5.000 di minus su Directa (dove fai trading attivo) e €30.000 di plus latenti su Fineco (dove tieni il portafoglio "buy and hold").

In amministrato, finché entrambi i rapporti restano aperti, non puoi compensare. Le €5.000 di minus Directa si consumeranno solo con plus realizzate **presso Directa** entro i 4 anni di scadenza. Se nei prossimi 4 anni su Directa non realizzi abbastanza plus, le minus evaporeranno.

Le vie per consolidare sono due: chiudere il rapporto Directa e farsi certificare le minus (Caso 2), oppure passare al dichiarativo e consolidare le posizioni nel quadro RT, usando le minus contro le plus indipendentemente da quale broker le abbia generate.

### Caso 2: chiusura del rapporto — le minus si certificano

Se chiudi il rapporto con un broker dove hai zainetto attivo, le minus **non vanno perse**. L'art. 6 c. 5 D.Lgs. 461/97 (→ art. 306 c. 6 TU 2027) prevede che, quando il rapporto di custodia o amministrazione viene chiuso o l'opzione per l'amministrato viene revocata, l'intermediario rilasci un'apposita **certificazione** delle minus non utilizzate. Con quella certificazione le minus possono essere portate in deduzione:

- dalle plus realizzate in **un altro rapporto in amministrato intestato agli stessi soggetti** del rapporto di provenienza. Con le cointestazioni gli intestatari devono coincidere: le minus di un dossier cointestato non passano a un dossier individuale. La norma non richiede che l'altro rapporto sia presso un intermediario diverso;
- oppure in **dichiarazione**, nel quadro RT, nei righi dedicati alle «eccedenze di minusvalenze certificate dagli intermediari» (RT4, RT14 e RT44 nelle istruzioni Redditi PF 2026), secondo l'art. 68 c. 5 TUIR (il comma 5 richiama ancora l'art. 82 c. 4, la numerazione precedente al 2004).

**La scadenza non si azzera**: le minus certificate restano utilizzabili «non oltre il quarto periodo d'imposta successivo a quello del realizzo», come prima.

Cosa costa davvero, anche se non c'è un'imposta da pagare:
- la certificazione si ottiene **solo chiudendo il rapporto** (o revocando l'opzione, che però manda quel rapporto in dichiarativo dall'anno successivo): un conto di trading attivo va spostato altrove;
- i titoli vanno venduti o trasferiti (il trasferimento a un rapporto con gli stessi intestatari conserva il costo di carico, art. 6 c. 7);
- i tempi di rilascio della certificazione e di caricamento presso il nuovo intermediario sono quelli dei due broker, e la modalità di consegna (originale, PEC) va chiesta prima: verificarli con entrambi, perché a fine anno possono non bastare.

Quindi: **chiudere un rapporto con zainetto attivo non lo fa sparire**, ma va pianificato. È il Pattern E della skill.

### Caso 3: trasferimento titoli inter-broker (senza chiudere)

Se trasferisci titoli da Broker A a Broker B (operazione tecnica, non vendita) e il rapporto A resta aperto:
- Il PMC viene preservato (Broker B eredita il costo di carico storico, sulla base della certificazione del costo rilasciata da A)
- Lo zainetto NO: resta su Broker A. Quindi se vendi su Broker B realizzi una plus che NON può essere compensata dallo zainetto di A.

Conclusione: il trasferimento titoli da solo non consolida lo zainetto; centralizza la custodia. Se però trasferisci tutto **e chiudi** il rapporto A, scatta il Caso 2: le minus residue vengono certificate e si portano su B.

### Caso 4: cambio regime entro lo stesso broker

L'opzione per l'amministrato si esercita all'apertura del rapporto o, per i rapporti in essere, prima dell'inizio del periodo d'imposta; si può revocare entro la fine di ogni anno solare, con effetto dall'anno successivo (art. 6 c. 2 D.Lgs. 461/97 → art. 306 c. 3 TU 2027). Verificare le condizioni e i moduli del broker.

## Il regime dichiarativo

### Come funziona

Optando per dichiarativo:
- L'intermediario NON è più sostituto d'imposta per i tuoi redditi finanziari
- Le ritenute non vengono applicate alla fonte (broker non trattiene il 26%)
- TU sei responsabile di dichiarare in Modello Redditi PF, quadro RT (per redditi diversi) e quadro RM (per redditi di capitale dove pertinente)
- Le minus si dichiarano nel quadro RT e fanno cumulo cross-broker

### Pro

- Consolidamento zainetto cross-broker **senza chiudere alcun rapporto**
- Possibilità di rinviare il pagamento (versi a giugno-luglio dell'anno successivo, non subito)
- Tracciabilità: il registro delle minus è tuo, nel quadro RT

Il coefficiente del 48,08% per i titoli di Stato vale anche in dichiarativo (art. 5 c. 2 D.Lgs. 461/97): il dichiarativo non dà più flessibilità sul cross-rate.

### Contro

- **Carico amministrativo**: devi compilare il quadro RT (o farlo fare dal commercialista, con costi). Per portafogli attivi è non banale.
- **Calcolo manuale**: in amministrato il broker certifica plus/minus pronte all'uso. In dichiarativo ricostruisci tu (a partire dalle "certificazioni" del broker), con i lotti in ordine LIFO e i cambi del giorno per i titoli in valuta (vedi `regime-dichiarativo.md`).
- **Modello Redditi obbligatorio**: anche se non hai altri redditi che richiedono dichiarazione, il quadro RT ti obbliga al Modello Redditi (non 730). Per chi normalmente fa 730, è cambio di paradigma.
- **Liquidità tempistiche**: se realizzi plus, paghi in F24 a saldo entro 30/6 e in acconto. In amministrato la ritenuta è alla fonte, "out of sight".
- **Irrevocabile per l'anno e solo dall'anno successivo**: non puoi cambiare idea a metà strada, e le minus che scadono quest'anno non si salvano passando al dichiarativo l'anno prossimo.

### Quando conviene optare per dichiarativo

Casi tipici dove vale la pena valutare il dichiarativo:
- **Multi-intermediario con squilibri** — hai minus su un broker e plus su un altro, gli importi sono significativi (almeno €5-10k di tasse in gioco) e **non vuoi chiudere** il rapporto con le minus (altrimenti confronta prima la certificazione, Caso 2)
- **Trading concentrato su strumenti esotici** — certificates complessi, derivati, dove la certificazione del broker è sub-ottimale
- **Pianificazione successoria** — vuoi tracciabilità storica del PMC

Casi dove NON conviene:
- Singolo broker, portafoglio buy-and-hold con poche operazioni
- Importi sotto i €500-1.000 di tasse — il costo del commercialista mangia il beneficio
- Minus da recuperare su un rapporto che puoi chiudere senza costi rilevanti: la certificazione arriva allo stesso risultato restando in amministrato
- Aversione all'adempimento — la complessità amministrativa è reale

### Tempi operativi

L'opzione si esercita di solito:
- All'apertura del rapporto (scelta iniziale)
- Entro la fine dell'anno precedente quello di applicazione (es. per applicare nel 2027, comunicare entro 31/12/2026)
- Modalità: form proprietario del broker, da firmare e inviare

## Heuristic per la skill

### Input multi-intermediario

Quando l'utente fornisce dati, accettare una colonna `broker` sia sul portafoglio sia sullo zainetto:

```csv
broker,isin,descrizione,quantita,pmc,prezzo_corrente,categoria_fiscale
directa,IT0003132476,ENI,500,12.40,14.80,reddito_diverso
fineco,IE00B4L5Y983,iShares MSCI World,100,75.20,89.50,reddito_capitale
```

```csv
broker,anno_realizzo,importo_residuo,aliquota
directa,2022,4500,26
fineco,2023,1200,26
```

### Analisi separata + consolidata

Lo step 2 dell'analisi deve:

1. **Analizzare per-broker**: per ciascun intermediario, calcolare zainetto + plus latenti compensabili + opportunità in regime amministrato corrente
2. **Aggregare cross-broker**: calcolare anche gli scenari "chiudo il rapporto con le minus incagliate e le porto altrove" (certificazione) e "tutto in dichiarativo" — quanto risparmio fiscale extra emerge da ciascuno

### Output multi-intermediario

Nel report:

- Sezione "Stato attuale" con tabelle separate per broker + totali
- Sezione "Opportunità in regime amministrato" — solo quelle realizzabili dentro lo stesso broker
- Sezione **dedicata al consolidamento** — chiusura con certificazione e dichiarativo a confronto
  - Quantificare il delta di risparmio di ciascuna via
  - Stimare i costi: per la certificazione chiusura, trasferimenti e tempi; per il dichiarativo commercialista, tempo e complessità
  - Raccomandazione: vale la pena solo se delta_risparmio > soglia (suggerirei €1.000 minimo per il dichiarativo, che ha costi ricorrenti)

### Anti-pattern multi-intermediario

- ❌ Proporre trade cross-broker assumendo che la compensazione avvenga — in amministrato NON avviene finché i rapporti restano aperti
- ❌ Suggerire trasferimenti titoli pensando di "spostare anche lo zainetto" — il PMC si sposta, lo zainetto no (a meno di chiudere il rapporto di origine)
- ❌ Dire che chiudendo il rapporto lo zainetto va perso — si certifica e si porta altrove fino alla scadenza originaria
- ❌ Proporre la chiusura senza verificare tempi, modalità e accettazione della certificazione da parte del broker ricevente, né il costo di spostare l'operatività
- ❌ Ignorare il delta tra amministrato, certificazione e dichiarativo: l'utente ha diritto a conoscerlo per decidere

## Caso pratico

Un investitore d'esempio, a ottobre dell'anno N, ha:

| Broker | Zainetto (€) | Scadenza | Plus latenti compensabili (€) |
|---|---|---|---|
| Directa | 3.200 | 31/12/N+1 | 800 |
| Fineco | 0 | — | 6.500 |
| Banca Sella | 1.500 | 31/12/N | 0 |

I tre rapporti hanno lo stesso intestatario. Directa è il conto di trading attivo, Banca Sella un dossier fermo senza posizioni in plus.

**Scenario (a) — consumo in loco (amministrato, status quo)**:
- Su Directa consuma €800 di zainetto con le plus disponibili: risparmio €800 × 26% = €208. Restano €2.400 che rischiano di evaporare a fine N+1.
- Su Banca Sella zero plus: €1.500 evaporano il 31/12/N.
- Su Fineco €6.500 di plus restano tassabili al 26% (€1.690).
- **Risparmio: €208.** Minus che evaporano: €3.900 (€1.014 di risparmio mancato).

**Scenario (b) — chiusura con certificazione (Pattern E)**:
- Banca Sella è il caso ideale: si chiude il dossier (vendendo o trasferendo i titoli), si ottiene la certificazione delle €1.500, la si consegna a Fineco e lì si realizzano almeno €1.500 di plus compensabili. Tutto **entro il 31/12/N**, perché la scadenza resta quella originaria: risparmio €390. Se i tempi dei due broker non stanno nell'anno, le minus evaporano comunque.
- Directa, consumate le €800 in loco (€208), ha ancora €2.400. Chiudere anche Directa le porterebbe su Fineco entro il 31/12/N+1 (+€624), ma vuol dire spostare altrove il conto di trading: un costo non monetario reale, da valutare.
- **Risparmio: €598** chiudendo solo Banca Sella, **€1.222** chiudendo anche Directa. Nessun commercialista, si resta in amministrato.

**Scenario (c) — dichiarativo dall'anno N+1 (Pattern D)**:
- L'opzione comunicata entro il 31/12/N vale dal 1/1/N+1: le €1.500 di Banca Sella, che scadono il 31/12/N, **non si salvano**.
- Con tutti i rapporti in dichiarativo nel N+1, le €2.400 di Directa compensano nel quadro RT le plus realizzate su Fineco: +€624, oltre ai €208 dello scenario (a).
- Costi: commercialista per il quadro RT, €200-400 l'anno, Modello Redditi obbligatorio e onere personale ricorrente.
- **Risparmio: €832, netto circa €430-630.**

| Scenario | Risparmio | Costi | Note |
|---|---|---|---|
| (a) Consumo in loco | €208 | commissioni | €3.900 di minus evaporano |
| (b) Chiusura Sella + certificazione | €598 | chiusura di un dossier fermo | €1.222 chiudendo anche Directa |
| (c) Dichiarativo dal N+1 | €832 | €200-400 l'anno + adempimenti | le €1.500 di Sella si perdono comunque |

In questo caso la skill deve proporre per prima la certificazione di Banca Sella, con il calendario stretto di fine anno da verificare con i due broker. Per le minus di Directa la scelta è tra chiudere quel rapporto (b) e il dichiarativo (c): il Pattern D resta la via quando non si vuole chiudere alcun rapporto. Il confronto va presentato con i numeri, non come automatismo.

---
*Zainetto per rapporto, certificazione alla chiusura e revoca dell'opzione (art. 6 c. 2, 5 e 7 D.Lgs. 461/97, testo vigente fino al 31/12/2026; dal 2027 art. 306 TU D.Lgs. 117/2026), riporto in dichiarazione (art. 68 c. 5 TUIR; righi RT4, RT14 e RT44 delle istruzioni Redditi PF 2026) — Verificato: 2026-10.*
