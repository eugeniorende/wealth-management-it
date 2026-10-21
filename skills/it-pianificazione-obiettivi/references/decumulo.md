# La fase di decumulo

Tutto il resto della skill ragiona sull'**accumulo**: quanto versare per arrivare a un obiettivo. Il **decumulo** — prelevare da un capitale per viverci (la pensione integrativa una volta in pensione, o una riserva permanente da cui si attinge) — è un problema **diverso**, non l'accumulo al contrario. Questa reference spiega perché, ed è accompagnata dallo script `assets/decumulo-obiettivi.py`. Non è consulenza.

## Perché il decumulo non è l'accumulo al contrario

In accumulo con un PAC, una brutta sequenza di rendimenti **all'inizio** è in realtà un vantaggio: compri a prezzi bassi e il recupero successivo lavora su più quote. In decumulo è l'opposto: una brutta sequenza all'inizio ti costringe a **vendere a prezzi bassi** per finanziare i prelievi, e quel capitale venduto non c'è più quando il mercato recupera. Lo stesso rendimento medio può portare a esiti opposti a seconda dell'**ordine** in cui arriva. Questo è il **rischio di sequenza dei rendimenti**, ed è il rischio dominante del decumulo.

Lo script lo dimostra: preso un identico insieme di rendimenti (stessa media reale), simularlo con i **peggiori prima** esaurisce il capitale all'anno 10 di 30, mentre con i **migliori prima** lo fa crescere a circa il doppio del capitale iniziale. Stessa media, esiti opposti. La conseguenza pratica: i **primi anni** di decumulo sono i più fragili — un crollo nei primi 5-10 anni fa molto più danno dello stesso crollo a metà o fine orizzonte.

## Il tasso di prelievo sostenibile (e perché il "4%" va scontato)

La domanda centrale è: quanto posso prelevare ogni anno senza esaurire il capitale? La risposta più nota è la **regola del 4%** (Bengen; studio Trinity): prelevare il 4% del capitale iniziale, poi adeguare ogni anno all'inflazione, ha storicamente fatto durare un portafoglio bilanciato per 30 anni nella grande maggioranza dei casi.

⚠️ Ma quella regola nasce su **dati USA** e su orizzonte 30 anni, e il mercato azionario americano è storicamente **eccezionale** — non rappresentativo di quello che un investitore europeo può aspettarsi. Tre ragioni per essere più prudenti:

1. **Il campione USA è il caso favorevole.** Su serie storiche europee o mondiali, i rendimenti reali sono stati inferiori e i drawdown più lunghi: il tasso "sicuro" scende. Lo script usa dati USA proprio perché sono quelli disponibili nel CSV, e segnala che i tassi di successo che produce sono **ottimistici**.
2. **L'orizzonte può essere più lungo di 30 anni.** Chi va in pensione a 60-65 anni in Italia, con l'aspettativa di vita attuale, può avere un orizzonte di 30-35 anni o più. Più lungo l'orizzonte, più basso il prelievo sostenibile.
3. **Le tasse e i costi erodono** (vedi la sequenza di liquidazione in `it-rebalance`): il 4% "lordo" non è il 4% "in tasca".

In pratica: trattare il 4% come un **punto di partenza ottimistico**, non una garanzia. Per un orizzonte lungo e un investitore europeo, molti pianificatori indicano un prelievo iniziale più prudente (intorno al **3-3,5%**) come più difendibile. La tabella di sensibilità dello script mostra come la probabilità di successo crolli salendo di tasso: sui dati USA (60/40, 30 anni, buffer di 2 anni, inflazione storica anno per anno) è 99,0% al 3%, 89,6% al 4%, 66,1% al 5% e 39,2% al 6%.

## Le mitigazioni del rischio di sequenza

Quattro leve, dalla più semplice alla più sofisticata:

**1. Buffer di liquidità (strategia bucket).** Tenere 1-3 anni di prelievi in liquidità e attingervi negli anni negativi, invece di vendere in perdita. È intuitiva e popolare, ma attenzione: **non è un free lunch**. Lo script lo confronta e, sui dati USA, il buffer *abbassa* di qualche punto la probabilità di successo — la liquidità rende ~0 e il mercato americano recupera in fretta, quindi il costo in rendimento supera la protezione. È il consenso accademico (Estrada, Kitces): il valore vero del buffer è (a) **comportamentale** — non essere costretti a vendere nel panico di un crollo — e (b) coprire **bear market prolungati**, che la media USA sottostima. Sceglierlo per questi motivi, non aspettandosi un rendimento migliore.

**2. Prelievi dinamici (guardrail, Guyton-Klinger).** Invece di un prelievo fisso adeguato all'inflazione, regole che **tagliano** il prelievo dopo anni negativi e lo **aumentano** dopo anni buoni, entro bande. Rinunciare a un po' di prelievo negli anni cattivi alza sensibilmente la sostenibilità: è la leva più efficace dopo la flessibilità di spesa.

**3. Flessibilità di spesa.** Distinguere prelievi **essenziali** da **discrezionali** e comprimere i discrezionali negli anni negativi. La capacità di ridurre temporaneamente il tenore di vita è, da sola, la difesa più potente contro il rischio di sequenza.

**4. Riduzione del rischio nella finestra fragile (bond tent).** Poiché i primi anni sono i più pericolosi, alcune ricerche (Pfau, Kitces) suggeriscono di **ridurre la quota azionaria avvicinandosi al decumulo** e poi eventualmente rialzarla dopo — una "tenda" obbligazionaria che protegge proprio quando il portafoglio è più vulnerabile. Si collega al glide path della skill (`glide-path.md`), ma con la curva pensata per il passaggio accumulo→decumulo, non per un obiettivo terminante.

## Le riserve permanenti

Lo stesso ragionamento vale, in piccolo, per le **riserve permanenti** (il fondo di emergenza, una riserva da cui si attinge a tempo indefinito): non hanno una scadenza in cui si liquidano, quindi sono un mini-decumulo perpetuo. Per loro il rischio di sequenza conta meno (l'orizzonte è indefinito e il prelievo episodico), ma la logica di tenere una quota liquida e non vendere il rischioso in un cattivo momento è la stessa.

## Lo strumento

`assets/decumulo-obiettivi.py` (parametri editabili in testa): calcola la **probabilità di successo** del decumulo con bootstrap a blocchi dalla serie storica (che preserva la sequenza), una **tabella di sensibilità** su più tassi di prelievo, la **dimostrazione del rischio di sequenza** (stesso insieme di rendimenti nei due ordini opposti) e il **confronto con/senza buffer**. Caveat: dati USA (ottimistici) e in dollari, portati in termini reali anno per anno con l'inflazione USA storica (CPI-U dicembre su dicembre, colonna del CSV): così la stagflazione degli anni '70 resta nella serie, mentre un'inflazione costante del 2% alzerebbe di circa un punto l'anno il rendimento reale dell'azionario e la cancellerebbe. Con `--set INFLAZIONE=0.02` si torna all'inflazione costante, per confronto. I risultati sono ordini di grandezza per ragionare sul rischio, non garanzie.

La dimensione **fiscale** del decumulo — quali posizioni e quali contenitori liquidare per minimizzare l'imposta — è trattata in `it-rebalance/references/sequenza-liquidazione.md`: questa reference dice *quanto* è sostenibile prelevare, quella dice *come* prelevarlo nel modo fiscalmente più efficiente.
