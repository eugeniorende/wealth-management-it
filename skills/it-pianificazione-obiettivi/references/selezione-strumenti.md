# Selezione degli strumenti per comparto (criteri, non ISIN)

Questa reference serve per l'**uso personale**: dà i criteri concreti per scegliere lo strumento in ciascun comparto del portafoglio, cuciti sulla fiscalità italiana. Non elenca ISIN specifici, e per una ragione precisa.

## Perché criteri e non ISIN

Anche quando dare strumenti concreti è perfettamente lecito (decidere per sé stessi), **hardcodare un ISIN è un errore tecnico**: gli ISIN cambiano, i fondi chiudono o si fondono, nascono nuove classi di quote, i TER variano, la disponibilità cambia da broker a broker. Un elenco statico invecchia in pochi mesi e inizia a indicare strumenti superati o inesistenti — lo stesso scollamento "guida vs realtà" che è un anti-pattern in tutto il plugin.

Il pattern robusto è la **selection spec**: criteri di selezione abbastanza precisi da restringere a una manciata di strumenti equivalenti, tra cui scegliere quello disponibile e più economico *adesso*, applicando i criteri su uno screener aggiornato (es. justETF, il comparatore del proprio broker, i siti degli emittenti). La spec invecchia molto più lentamente di un ISIN; i criteri restano validi anche quando i prodotti specifici cambiano.

⚠️ Questa reference NON è consulenza di investimento. Fornisce criteri di selezione per decisioni personali. La scelta finale tra strumenti equivalenti, e la valutazione di adeguatezza alla propria situazione, restano dell'utente (o di un consulente abilitato).

## I criteri universali per un ETF UCITS (la checklist)

Per qualsiasi comparto basato su ETF, applicare questi criteri. Sono ordinati per importanza.

1. **UCITS armonizzato**: fondamentale per il trattamento fiscale italiano noto. La plusvalenza è reddito di capitale (NON compensabile con minusvalenze), la minusvalenza è reddito diverso (compensabile). Vedi `it-tax-optimization/references/etf-trap-redditi-capitale.md`. Tutti gli ETF quotati su Borsa Italiana – ETFplus sono UCITS.

2. **Domicilio Irlanda (ISIN che inizia per IE)** per i comparti azionari con forte componente USA: grazie al trattato fiscale USA-Irlanda, la ritenuta sui dividendi statunitensi sottostanti scende dal 30% al 15% **a livello di fondo**, migliorando il rendimento netto. Il Lussemburgo (LU) non gode dello stesso vantaggio nella stessa misura. Per i comparti obbligazionari o solo-Europa il domicilio conta meno.

3. **Politica dei proventi: accumulazione (ACC) per la crescita di lungo termine**. Gli ETF ad accumulazione reinvestono internamente dividendi/cedole: in Italia questo **differisce la tassazione** fino alla vendita (plusvalenza), invece di generare ogni anno un dividendo tassato al 26% (reddito di capitale, non compensabile). Per obiettivi di crescita, ACC è quasi sempre preferibile. La distribuzione (DIST) ha senso solo se serve un flusso di reddito periodico.

4. **TER (costo annuo) sotto soglia**, indicativamente:
   - Azionario globale ampio: < 0,25% (i migliori stanno a 0,12-0,20%)
   - Azionario emergenti / settoriale: < 0,40%
   - Obbligazionario: < 0,20%
   Su orizzonti lunghi, 0,2 punti di TER in più capitalizzati erodono parecchio: il costo è una delle pochissime variabili sotto il tuo controllo certo.

5. **Dimensione del fondo (AUM) adeguata**: indicativamente > €500M, meglio > €1mld per i comparti core. Un fondo grande ha più liquidità (spread denaro-lettera bassi) e minor rischio di chiusura/fusione (che sarebbe un evento fiscale forzato).

6. **Replica fisica** (totale o a campionamento) preferibile alla sintetica per trasparenza e assenza di rischio di controparte sullo swap. La sintetica può avere vantaggi fiscali specifici su certe esposizioni USA, ma per semplicità e robustezza la fisica è il default.

7. **Quotazione su Borsa Italiana (ETFplus)** e negoziazione in EUR: accesso facile dal broker italiano, niente costi di cambio sulla transazione. Attenzione a distinguere la *valuta di negoziazione* (EUR) dalla *valuta hedged/unhedged* del fondo (vedi sotto).

8. **Qualità della replica** (tracking difference contenuta): a parità di indice e TER, preferire chi storicamente replica meglio l'indice. I siti degli emittenti e justETF riportano la tracking difference pluriennale.

## La spec per ciascun comparto

Le allocazioni per orizzonte sono in `orizzonte-allocazione.md`. Qui, per ogni comparto, i criteri di selezione dello strumento.

### Azionario globale (il cuore degli obiettivi a lungo termine)

- **Indice**: esposizione mondiale ampia. Famiglie tipiche: MSCI World (Paesi sviluppati), FTSE All-World o MSCI ACWI (sviluppati **+** emergenti, più completi). Per la massima diversificazione, un indice che include gli emergenti.
- **Domicilio**: Irlanda (per la ritenuta USA).
- **Proventi**: accumulazione.
- **Replica**: fisica.
- **Valuta**: unhedged (non coperta). Su orizzonti lunghi la copertura valutaria costa senza un beneficio chiaro; il rischio cambio si media nel tempo.
- **TER target**: < 0,22%.
- **AUM**: > €1mld (questi sono i comparti più capienti del mercato).
- Risultato atteso applicando la spec: una manciata di ETF azionari globali ad accumulazione domiciliati in Irlanda, tra i più grandi e a basso costo. Si sceglie il più economico/liquido disponibile sul proprio broker.

### Azionario Paesi emergenti (raffinamento opzionale)

Solo se si vuole sovrappesare gli emergenti oltre la quota già presente in un indice ACWI/All-World.
- **Indice**: MSCI Emerging Markets o FTSE Emerging.
- Stessi criteri (IE, ACC, fisica), **TER target < 0,40%** (gli emergenti costano un po' di più).

### Obbligazionario governativo Euro / titoli di Stato

Per la parte "sicura" degli obiettivi a medio termine. Qui c'è una scelta a monte: **BTP diretti vs ETF obbligazionario**.

- **BTP diretti (titoli di Stato italiani)**:
  - **Vantaggio fiscale 12,5%** su cedole e plusvalenze (vs 26%).
  - Se tenuti a scadenza, restituiscono il nominale: niente rischio di mercato sul capitale (solo rischio emittente Italia).
  - Adatti quando la scadenza del BTP coincide con l'orizzonte dell'obiettivo (es. obiettivo a 4 anni → BTP che scade tra ~4 anni).
  - Emissioni retail da conoscere: BTP a tasso fisso, BTP Italia (indicizzato all'inflazione italiana), BTP Valore (cedole step-up + premio fedeltà). Categorie, non raccomandazioni su una specifica emissione.
- **ETF obbligazionario governativo Euro**:
  - Diversificato su più emittenti euro (non solo Italia), ma **niente scadenza fissa** → rischio di mercato sul prezzo (sale/scende coi tassi).
  - Tassazione: mista, la quota in titoli di Stato white list è al 12,5%, il resto al 26%.
  - **Duration da abbinare all'orizzonte**: per obiettivi a breve, ETF a bassa duration (1-3 anni); per medio, duration intermedia. Una duration troppo lunga su un obiettivo a breve è rischio di prezzo non necessario.
  - Criteri ETF: UCITS, EUR, accumulazione, TER < 0,20%, AUM elevato.

Regola pratica: se l'orizzonte è preciso e si vuole certezza dell'importo, **BTP a scadenza** (sfruttando il 12,5%). Se si vuole diversificazione e flessibilità accettando oscillazioni di prezzo, **ETF obbligazionario** con duration coerente.

### Obbligazionario aggregate / corporate (diversificatore opzionale)

- **Indice**: Bloomberg Euro Aggregate (govt + corporate investment grade) o corporate euro IG.
- Criteri ETF standard (UCITS, EUR-hedged se l'indice è globale, ACC, TER < 0,25%).
- ⚠️ Il corporate aggiunge rischio di credito: rende un po' di più ma è meno "rifugio" del governativo. Per la parte difensiva pura, il governativo è più coerente.

### Monetario / liquidità (obiettivi a brevissimo e fondo di emergenza)

- **Fondo di emergenza**: NON in ETF. Conto deposito (libero o vincolato breve) o conto corrente. Vedi `orizzonte-allocazione.md`. La priorità è accessibilità e certezza, non rendimento.
- **Liquidità di portafoglio a brevissimo** (parcheggio in attesa di investire, o obiettivo a < 1-2 anni): in alternativa al conto deposito, un **ETF monetario in EUR** (che replica un tasso a brevissimo tipo €STR). Criteri: UCITS, EUR (non hedged da altre valute), accumulazione, TER < 0,15%, AUM elevato. Tassazione 26% sui proventi.

### Inflazione (per obiettivi sensibili al carovita)

Se un obiettivo è particolarmente esposto all'inflazione (es. spese future indicizzate):
- **BTP Italia** (titoli di Stato indicizzati all'inflazione italiana, 12,5%, retail-friendly), oppure
- **ETF su titoli di Stato inflation-linked** euro (criteri ETF standard, EUR-hedged).

## I ganci fiscali (collegamento a it-tax-optimization)

Tre cose da tenere a mente nella selezione, tutte già codificate altrove nel plugin:

1. **Accumulazione = differimento**: l'ETF ad accumulazione non distribuisce, quindi non genera dividendi tassati ogni anno; la tassazione (26%) scatta solo alla vendita, sulla plusvalenza. Vantaggio di capitalizzazione composta al lordo.
2. **Asimmetria reddito diverso/capitale**: sugli ETF UCITS armonizzati la *plus* è reddito di capitale (non compensabile con lo zainetto), la *minus* è reddito diverso (compensabile). Questo influenza quali strumenti convenga vendere quando si ribilancia o si liquida un obiettivo. Vedi `it-tax-optimization`.
3. **12,5% sui titoli di Stato**: BTP e govt white list sono al 12,5%. Per la parte sicura del portafoglio, preferire titoli di Stato (diretti o la loro quota dentro un ETF) ha un vantaggio fiscale strutturale.
4. **Bollo 0,2%**: si applica a tutto (ETF, conti deposito, titoli) sul controvalore. Non discrimina tra strumenti, ma va contato nei costi totali.

## Come applicare la spec (workflow)

1. Stabilire l'allocazione dell'obiettivo (da `orizzonte-allocazione.md`): quali comparti e in che percentuale.
2. Per ogni comparto, prendere la spec qui sopra.
3. Aprire uno screener aggiornato (justETF, comparatore del broker) e filtrare per i criteri: indice/famiglia, domicilio, accumulazione, replica, TER massimo, AUM minimo.
4. Tra i risultati (di solito 2-5 strumenti equivalenti), scegliere il più economico e liquido **disponibile sul proprio broker**.
5. Verificare che sia negoziabile su Borsa Italiana in EUR (o sul mercato a cui si ha accesso).
6. Per la parte obbligazionaria sicura a orizzonte preciso, valutare il BTP a scadenza coerente come alternativa all'ETF.

In questo modo lo strumento concreto è sempre quello giusto **oggi**, e la spec resta valida anche tra due anni quando i prodotti specifici saranno cambiati.

## Asset location (quale strumento in quale obiettivo)

Oltre a *cosa* comprare, conta *dove* collocarlo tra gli obiettivi, per efficienza fiscale:

- Gli strumenti a forte crescita attesa e lunga detenzione (azionario globale ACC) stanno bene negli obiettivi a **lungo termine**, dove il differimento della tassazione lavora più a lungo.
- I titoli di Stato al 12,5% stanno bene nella parte sicura degli obiettivi a **medio termine**.
- Il fondo di emergenza e gli obiettivi a brevissimo restano **fuori dal mercato** (liquidità).
- L'obiettivo pensione ha il suo veicolo dedicato (fondo pensione, vedi `it-pianificazione`), fiscalmente diverso da un ETF su dossier: non va trattato con questa spec.

## Heuristic per la skill

1. **Mai dare ISIN fissi**: dare la spec criteri-based, e indicare di applicarla su uno screener aggiornato. È più utile e non invecchia.
2. **UCITS armonizzato sempre**: è il presupposto del trattamento fiscale noto.
3. **Irlanda per l'azionario USA-heavy, accumulazione per la crescita**: i due criteri fiscali a maggior impatto.
4. **TER e AUM come filtri di qualità**: costo basso e fondo grande sono proxy robusti.
5. **BTP a scadenza per la parte sicura a orizzonte preciso**: sfrutta il 12,5% e dà certezza dell'importo.
6. **Ribadire che è uso personale, non consulenza**: la spec aiuta a decidere per sé; non è una raccomandazione personalizzata né una lista da seguire ciecamente.
7. **Rinviare allo screener e, per dubbi, a un consulente abilitato**: la skill dà il metodo, non sostituisce la verifica di adeguatezza alla propria situazione.
