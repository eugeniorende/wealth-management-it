# Orizzonte, allocazione e strumenti italiani

Questa reference dettaglia come tradurre l'orizzonte di un obiettivo in un profilo di allocazione e poi negli strumenti concreti del mercato italiano. Resta materiale **didattico**: descrive categorie di strumenti, non raccomanda prodotti o emissioni specifiche.

## Indice

- L'obiettivo 0: il fondo di emergenza
- La mappa orizzonte → profilo → strumenti
- Gli strumenti italiani in dettaglio
- Dall'allocazione per obiettivo all'allocazione di portafoglio
- Il glide path (de-risking progressivo)
- Heuristic per la skill

## L'obiettivo 0: il fondo di emergenza

Prima di qualsiasi altro obiettivo viene il **fondo di emergenza**. Non è un investimento: è un cuscinetto di liquidità che serve a non dover liquidare gli investimenti nel momento sbagliato (un imprevisto durante un calo di mercato).

- **Dimensione**: 3-6 mesi di spese (6+ se reddito variabile, autonomo, o famiglia monoreddito; 3 se reddito molto stabile e doppio)
- **Dove**: massima liquidità e certezza del capitale — conto corrente, conto deposito libero, o conto deposito vincolato a breve (3-6 mesi) per spuntare qualche interesse senza perdere accessibilità
- **Obiettivo**: NON il rendimento, ma la sicurezza e l'accessibilità immediata
- **Cosa evitare**: investirlo in ETF, azioni, obbligazioni a lunga, o qualsiasi cosa con rischio di mercato. Se quando serve è in perdita, ha fallito il suo scopo.

⚠️ Senza fondo di emergenza adeguato, qualsiasi piano di investimento è fragile: il primo imprevisto costringe a vendere in perdita. La skill verifica sempre che esista prima di ottimizzare il resto.

Nota fiscale: gli interessi dei conti deposito sono tassati al **26%** e il conto sconta l'**imposta di bollo dello 0,2%** annua sul giacenza. Tutela: il Fondo Interbancario di Tutela dei Depositi (FITD) garantisce fino a **€100.000** per depositante per banca.

## La mappa orizzonte → profilo → strumenti

⚠️ Allocazioni-**tipo** a scopo didattico. La percentuale esatta dipende anche dalla tolleranza al rischio personale.

### Orizzonte < 2 anni — Preservazione (0% azionario)

L'obiettivo è la **certezza dell'importo**. Nessun rischio di mercato.

- **Strumenti**: conto deposito (libero o vincolato di durata pari all'orizzonte), conto corrente
- **Eventuale**: titoli di Stato a brevissima scadenza tenuti a scadenza (es. BOT, BTP molto corti)
- **Logica**: a meno di 2 anni non c'è tempo per recuperare da una correzione; si privilegia la prevedibilità

### Orizzonte 2-4 anni — Conservativo (0-20% azionario)

Prevalenza di strumenti a basso rischio, con un'eventuale piccola quota di crescita.

- **Strumenti**: conto deposito vincolato, **BTP a scadenza breve (1-3 anni)** tenuti a scadenza, ETF obbligazionario governativo a bassa duration
- **Quota azionaria (se presente, max ~20%)**: ETF azionario globale, solo se l'utente accetta un po' di volatilità
- **Vantaggio fiscale BTP**: i titoli di Stato italiani (e di Paesi white list) sono tassati al **12,5%** invece del 26% — un vantaggio rilevante per gli obiettivi a medio termine. Esistono emissioni pensate per il retail (es. BTP Valore con cedole step-up e premio fedeltà, BTP Italia indicizzato all'inflazione italiana) — categorie utili da conoscere, non raccomandazioni su una specifica emissione.

### Orizzonte 4-7 anni — Moderato (30-50% azionario)

Bilanciato: un po' di crescita, rischio contenuto.

- **Strumenti**: mix di ETF azionario globale + componente obbligazionaria (ETF obbligazionario e/o BTP), oppure un singolo ETF bilanciato
- **Logica**: l'orizzonte inizia ad assorbire la volatilità, ma non abbastanza da andare tutto azionario

### Orizzonte 7-12 anni — Crescita (50-75% azionario)

L'orizzonte assorbe bene la volatilità di breve.

- **Strumenti**: prevalenza di ETF azionario globale diversificato, con una quota obbligazionaria a stabilizzare
- **Logica**: il rendimento atteso dell'azionario su 7-12 anni giustifica il rischio, con un cuscinetto obbligazionario

### Orizzonte > 12 anni — Crescita massima (75-100% azionario)

Massimizzare il rendimento atteso di lungo periodo.

- **Strumenti**: ETF azionario globale ampiamente diversificato (esposizione mondiale), tipicamente accumulato via PAC
- **Logica**: su 12+ anni la volatilità si appiattisce statisticamente e il costo-opportunità di stare liquidi (erosione da inflazione) supera di gran lunga il rischio di mercato

## Gli strumenti italiani in dettaglio

### Conto deposito
Per fondo di emergenza e obiettivi a brevissimo. Interessi tassati 26%, bollo 0,2%, garanzia FITD €100k. Vincolato (tasso più alto, capitale bloccato) vs libero (accessibile, tasso più basso).

### BTP / titoli di Stato
Per obiettivi a breve-medio. **Tassazione agevolata 12,5%** (vs 26%) su cedole e plusvalenze. Soggetti a bollo 0,2%. Se tenuti a scadenza, restituiscono il nominale (no rischio di mercato sul capitale, solo rischio emittente/Italia). Emissioni retail: BTP Valore, BTP Italia (indicizzato inflazione). Categoria utile per la parte "sicura" dei secchielli a medio termine, sfruttando l'aliquota ridotta.

### ETF UCITS armonizzati
Il cavallo da battaglia per gli obiettivi a medio-lungo, tipicamente via PAC. Tassazione 26% sulle plusvalenze (12,5% sulla quota investita in titoli di Stato white list). Soggetti a bollo 0,2%.

⚠️ **Asimmetria fiscale importante** (vedi `it-tax-optimization`): la *plusvalenza* su un ETF UCITS armonizzato è reddito di capitale e **non** è compensabile con minusvalenze pregresse, mentre la *minusvalenza* è reddito diverso (compensabile). Questo ha implicazioni quando si ribilancia o si liquida un obiettivo: conoscerla evita sorprese.

### PAC (Piano di Accumulo del Capitale)
Non è uno strumento ma un **metodo**: versamenti regolari (es. mensili) in ETF. Vantaggi: riduce il rischio di timing (si compra a prezzi mediati nel tempo, euro-cost averaging), impone disciplina, sfrutta la capitalizzazione composta su orizzonti lunghi. È il veicolo naturale per gli obiettivi a lungo termine.

### Fondo pensione
Per l'obiettivo "pensione integrativa" specificamente. NON è un generico secchiello di ETF: è un veicolo dedicato con deducibilità fiscale (per i dipendenti) e tassazione agevolata della prestazione finale (15→9%). Va instradato a `it-pianificazione` (dipendenti) o `it-pianificazione-autonomi` (P.IVA, dove per i forfettari la deduzione non esiste). Trattarlo come un secchiello generico sarebbe un errore (doppio conteggio e fiscalità sbagliata).

## Dall'allocazione per obiettivo all'allocazione di portafoglio

Ogni profilo, oltre a rendimento e volatilità, ha una **quota azionaria rappresentativa** (il punto medio della sua fascia), usata per aggregare i secchielli nell'allocazione complessiva:

| Profilo | % Azionario rappresentativa | Fascia |
|---|---|---|
| Preservazione | 0% | 0% |
| Conservativo | 10% | 0-20% |
| Moderato | 40% | 30-50% |
| Crescita | 65% | 50-75% |
| Crescita massima | 90% | 75-100% |

I secchielli per obiettivo non sono portafogli separati nella realtà: la somma delle posizioni È il portafoglio. Pesando la quota azionaria di ogni obiettivo per il suo capitale si ottiene l'**asset allocation complessiva**:

```
quota azionaria del portafoglio = Σ(capitale_obiettivo × %azionario) / capitale_totale
```

Esempio: un fondo emergenza di €8.500 (Preservazione, 0% azionario) + un obiettivo da €50.000 (Crescita, 65% azionario) → portafoglio di €58.500 con €32.500 azionari = **56% azionario / 44% non azionario**. Quel 44% non è omogeneo: €8.500 sono liquidità d'emergenza (conto deposito), €17.500 sono l'obbligazionario dell'obiettivo lungo. Stesso "non azionario" nell'aggregato, ruoli opposti.

Due avvertenze pratiche:
- **Non si compra un singolo fondo bilanciato con la % aggregata**: si implementa secchiello per secchiello, perché i ruoli del "non azionario" sono diversi (liquidità d'emergenza vs zavorra obbligazionaria di lungo termine).
- **Stock ≠ flusso**: l'allocazione del capitale esistente differisce da quella dei versamenti nuovi (i soldi nuovi possono andare tutti in liquidità se l'unico obiettivo da finanziare ora è il fondo emergenza, anche se il patrimonio è già 56% azionario).

Questa allocazione complessiva è il **target operativo di `it-rebalance`**, che la mantiene nel tempo ed esegue il glide path.

## Il glide path (de-risking progressivo)

Un obiettivo non resta nella stessa allocazione per tutta la sua vita. Man mano che si avvicina la scadenza, l'allocazione va resa più conservativa per **bloccare il valore raggiunto** ed evitare che una correzione di mercato colpisca proprio quando i soldi servono.

Esempio: obiettivo "anticipo casa" a 8 anni, importo €40.000.

| Anni alla scadenza | Profilo | Azionario | Logica |
|---|---|---|---|
| 8-5 | Moderato/Crescita | ~50% | C'è tempo, si cerca crescita |
| 5-3 | Conservativo | ~30% | Si inizia a ridurre il rischio |
| 3-1 | Conservativo | ~10-15% | Si protegge il valore accumulato |
| < 1 | Preservazione | 0% | Tutto liquido: l'importo deve esserci con certezza |

Questo de-risking progressivo è **gestito operativamente da `it-rebalance`**: man mano che l'orizzonte si accorcia, l'allocazione-target dell'obiettivo si sposta verso il conservativo, e it-rebalance esegue gli spostamenti (con attenzione agli eventi fiscali che ogni vendita genera). La pianificazione goals-based definisce il calendario del glide path; il ribilanciamento lo esegue.

Il calendario non va costruito a mano: lo script `assets/glidepath-obiettivi.py` lo genera automaticamente anno per anno, sia per obiettivo sia aggregato. La regola è parametrica — l'obiettivo tiene la quota azionaria del profilo finché manca più di una *finestra di de-risking* (default 7 anni), poi scende linearmente fino a una quota di *atterraggio* (default 0%) entro la scadenza. Il de-risking ha un prezzo nel piano di accumulo: negli ultimi anni il rendimento atteso scende, quindi il versamento necessario sale (circa +10% sugli obiettivi a 20 anni); il pianificatore Excel lo include già (Obiettivi, colonne O-P). Per la formula completa, i parametri editabili, la sottigliezza terminanti/permanenti e il coordinamento fiscale, vedi `glide-path.md`.

⚠️ Il glide path genera vendite, e ogni vendita in Italia è un evento fiscale (vedi `it-rebalance`). Quindi il de-risking va pianificato con anticipo e, dove possibile, realizzato sfruttando le sinergie con lo zainetto fiscale.

## Heuristic per la skill

1. **Fondo di emergenza sempre prima**: verificarne l'esistenza e l'adeguatezza prima di ottimizzare qualsiasi altro obiettivo. Se manca, è l'obiettivo 0 con priorità assoluta.
2. **Orizzonte guida l'allocazione, non la personalità**: un investitore "prudente" a 20 anni dalla pensione dovrebbe comunque stare prevalentemente azionario su quell'obiettivo; la prudenza si esprime nel fondo di emergenza e negli obiettivi a breve, non rinunciando alla crescita di lungo periodo.
3. **Sfruttare il 12,5% dei titoli di Stato** per la parte sicura degli obiettivi a medio termine: è un vantaggio fiscale strutturale rispetto al 26%.
4. **PAC per il lungo termine**: per gli obiettivi a 10+ anni, il piano di accumulo regolare è il metodo naturale.
5. **Glide path da pianificare**: ogni obiettivo a medio-lungo ha una scadenza che si avvicina; prevedere il de-risking progressivo e segnalarlo come compito di it-rebalance.
6. **Mai raccomandare emissioni o ISIN specifici**: descrivere categorie (ETF azionario globale, BTP retail, conto deposito), non prodotti. Le scelte concrete sono dell'utente o di un consulente.
7. **Instradare la pensione**: l'obiettivo pensione va alla skill previdenziale dedicata, non trattato qui come secchiello generico.
