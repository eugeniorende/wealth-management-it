# Zainetto multi-intermediario

## Il principio

In **regime amministrato**, lo zainetto fiscale (registro delle minus pregresse) è **per-intermediario**. Ogni broker tiene il proprio "libro" delle minus realizzate sui dossier presso di lui. Conseguenze:

- Le minus realizzate su Directa **non possono** compensare plus realizzate su Fineco
- Il broker A non comunica con il broker B su questioni fiscali
- L'AdE non vede un quadro consolidato (in amministrato sei "esonerato" dalla dichiarazione su questi redditi, ma per il fisco non hai un cumulato)

In **regime dichiarativo**, invece, lo zainetto è dell'investitore: tu lo dichiari nel quadro RT del Modello Redditi PF e puoi cumulare cross-broker.

## Implicazioni operative

### Caso 1: hai dossier su 2+ broker e minus distribuite

Scenario tipico: hai €5.000 di minus su Directa (dove fai trading attivo) e €30.000 di plus latenti su Fineco (dove tieni il portafoglio "buy and hold").

In amministrato: non puoi compensare. Le €5.000 di minus Directa si consumeranno solo con plus realizzate **presso Directa** entro i 4 anni di scadenza. Se nei prossimi 4 anni su Directa non realizzi abbastanza plus, le minus evaporeranno.

In dichiarativo: puoi consolidare le posizioni nel quadro RT e usare le minus contro le plus, indipendentemente da quale broker le abbia generate.

### Caso 2: chiusura rapporto

Se chiudi il rapporto con un broker dove hai zainetto attivo, in amministrato lo zainetto **si perde** definitivamente. Eccezione: se per l'anno in corso hai optato per dichiarativo, le minus restano dichiarabili in RT e quindi conservate.

Quindi: **mai chiudere un rapporto a cuor leggero se c'è zainetto attivo** senza aver prima optato per dichiarativo o senza aver consumato lo zainetto.

### Caso 3: trasferimento titoli inter-broker

Se trasferisci titoli da Broker A a Broker B (operazione tecnica, non vendita):
- Il PMC viene preservato (Broker B eredita il costo di carico storico)
- Lo zainetto NO: resta su Broker A. Quindi se vendi su Broker B realizzi una plus che NON può essere compensata dallo zainetto di A.

Conclusione: il trasferimento titoli non aiuta a consolidare; aiuta solo a centralizzare la custodia. Per consolidare zainetto serve il dichiarativo.

### Caso 4: cambio regime entro lo stesso broker

Su molti broker puoi scegliere amministrato o dichiarativo all'apertura del rapporto. Alcuni permettono il cambio annuale (di solito da comunicare entro il 31/12 dell'anno precedente, irrevocabile). Verificare condizioni specifiche del broker.

## Il regime dichiarativo: l'escape hatch

### Come funziona

Optando per dichiarativo:
- L'intermediario NON è più sostituto d'imposta per i tuoi redditi finanziari
- Le ritenute non vengono applicate alla fonte (broker non trattiene il 26%)
- TU sei responsabile di dichiarare in Modello Redditi PF, quadro RT (per redditi diversi) e quadro RM (per redditi di capitale dove pertinente)
- Le minus si dichiarano nel quadro RT e fanno cumulo cross-broker

### Pro

- Consolidamento zainetto cross-broker
- Possibilità di compensare cross-rate (12,5% vs 26%) con maggiore flessibilità
- Possibilità di rinviare il pagamento (versi a giugno-luglio dell'anno successivo, non subito)
- Tracciabilità: hai tu il libro mastro, non lo perdi se cambi broker

### Contro

- **Carico amministrativo**: devi compilare il quadro RT (o farlo fare dal commercialista, con costi). Per portafogli attivi è non banale.
- **Calcolo manuale**: in amministrato il broker certifica plus/minus pronte all'uso. In dichiarativo ricostruisci tu (a partire dalle "certificazioni" del broker).
- **Modello Redditi obbligatorio**: anche se non hai altri redditi che richiedono dichiarazione, il quadro RT ti obbliga al Modello Redditi (non 730). Per chi normalmente fa 730, è cambio di paradigma.
- **Liquidità tempistiche**: se realizzi plus, paghi in F24 a saldo entro 30/6 e in acconto. In amministrato la ritenuta è alla fonte, "out of sight".
- **Irrevocabile per l'anno**: non puoi cambiare idea a metà strada.

### Quando conviene optare per dichiarativo

Casi tipici dove vale la pena valutare il dichiarativo:
- **Multi-intermediario con squilibri** — hai minus su un broker e plus su un altro, e gli importi sono significativi (almeno €5-10k di tasse in gioco)
- **Trading concentrato su strumenti esotici** — certificates complessi, derivati, dove la certificazione del broker è sub-ottimale
- **Pianificazione successoria** — vuoi tracciabilità storica del PMC
- **Anno di chiusura rapporto** — vuoi preservare zainetto in vista di trasferimento ad altro broker

Casi dove NON conviene:
- Singolo broker, portafoglio buy-and-hold con poche operazioni
- Importi sotto i €500-1.000 di tasse — il costo del commercialista mangia il beneficio
- Aversione all'adempimento — la complessità amministrativa è reale

### Tempi operativi

L'opzione si esercita di solito:
- All'apertura del rapporto (scelta iniziale)
- Entro la fine dell'anno precedente quello di applicazione (es. per applicare nel 2026, comunicare entro 31/12/2025)
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
2. **Aggregare cross-broker**: calcolare anche lo scenario "se tutto fosse in dichiarativo" — quanto risparmio fiscale extra emerge dalla compensazione cross-broker

### Output multi-intermediario

Nel report:

- Sezione "Stato attuale" con tabelle separate per broker + totali
- Sezione "Opportunità in regime amministrato" — solo quelle realizzabili dentro lo stesso broker
- Sezione **dedicata "Opportunità in dichiarativo"** — quelle che richiederebbero passaggio a dichiarativo per essere catturate
  - Quantificare il delta di risparmio
  - Stimare il costo (commercialista, tempo, complessità)
  - Raccomandazione: vale la pena solo se delta_risparmio > soglia (suggerirei €1.000 minimo per coprire costi commercialista e ammortizzare onere)

### Anti-pattern multi-intermediario

- ❌ Proporre trade cross-broker assumendo che la compensazione avvenga — in amministrato NON avviene
- ❌ Suggerire trasferimenti titoli pensando di "spostare anche lo zainetto" — il PMC si sposta, lo zainetto no
- ❌ Ignorare il delta amministrato-vs-dichiarativo: l'utente ha diritto a conoscerlo per decidere
- ❌ Suggerire chiusura rapporto senza prima allertare sulla perdita zainetto

## Caso pratico

Un investitore d'esempio ha:

| Broker | Zainetto (€) | Anno scad. | Plus latenti compensabili (€) |
|---|---|---|---|
| Directa | 3.200 | 2026 | 800 |
| Fineco | 0 | — | 6.500 |
| Banca Sella | 1.500 | 2025 | 0 |

**Scenario amministrato (status quo)**:
- Su Directa può consumare al massimo €800 di zainetto (per le plus disponibili). €2.400 rischiano evaporazione 2026.
- Su Banca Sella zero plus disponibili: €1.500 destinati a evaporare a fine 2025.
- Su Fineco €6.500 di plus tassabili al 26% = €1.690 di tasse.
- **Risparmio fiscale ottenibile in amministrato**: €800 × 26% = €208.
- **Minus che evaporeranno**: €2.400 + €1.500 = €3.900 (= €1.014 di mancato risparmio fiscale future).

**Scenario dichiarativo per l'anno**:
- Zainetto consolidato: €4.700 totale
- Plus realizzabili compensabili: €7.300 totale
- Compensazione possibile: €4.700 → tutto consumato
- **Risparmio fiscale**: €4.700 × 26% = €1.222
- **Costo aggiuntivo**: commercialista per quadro RT, stimiamo €200-400. Onere amministrativo personale: alcune ore.

**Delta**: €1.222 − €208 − €400 commercialista = **€614** di vantaggio netto a favore del dichiarativo. Più: si evita l'evaporazione di €3.900 di minus a fine 2025/2026.

In questo caso, la skill deve raccomandare il dichiarativo, con disclaimer che la scelta va comunicata entro 31/12/2025 al broker e che è irrevocabile per il 2026.
