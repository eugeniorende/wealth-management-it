# Bande di tolleranza dinamiche

Quando ribilanciare, e fin dove? La regola del plugin, la stessa in script, fogli e skill, è questa:

- **soglia 5/25**: si agisce quando il drift di una classe supera il minore tra 5 punti assoluti e il 25% del suo peso target;
- **allargamento cost-aware ×2**: se la correzione paga imposta, si agisce solo oltre il doppio della soglia;
- **rientro misto**: a target se la correzione è a costo netto zero, fino a metà banda per la parte che paga imposta;
- **modulazione per volatilità**: opzionale e spenta di default (`MODULA_VOLATILITA = False`).

Questa reference spiega il perché, con le idee della letteratura di pianificazione (Kitces, Daryanani, Swedroe) adattate al contesto fiscale italiano. È implementata in `assets/ribilanciamento-multibroker.py`; l'IPS, il tracker dei secchielli e il cruscotto usano la stessa 5/25.

## Soglia, non calendario

Ribilanciare "una volta l'anno" a calendario è subottimale: a volte si ribilancia quando non serve (drift piccolo), a volte si lascia correre un drift grande per mesi. L'approccio migliore è **trigger a soglia**: si controlla periodicamente, ma si agisce **solo** quando una classe supera una banda di tolleranza. La ricerca mostra che il ribilanciamento a soglia cattura gran parte del "rebalancing bonus" con **meno operazioni** — e meno operazioni, in Italia, significa meno eventi fiscali.

Un corollario importante (Kitces): **il trigger è alla banda, ma quando scatta non ci si ferma al bordo**. Riportare al bordo lascerebbe la classe a un passo dal ri-sforare, costringendo a operare di nuovo presto. In Italia però ogni euro venduto in plus può pagare imposta, e l'ultima precisione è la più cara. Da qui la **regola di rientro mista**: a target se la correzione è a costo netto zero, fino a metà della banda stretta per la parte che paga imposta. Lo strumento stampa i due costi (a target e a metà banda); il parametro `OBIETTIVO_RIENTRO` permette di scegliere «target» o «banda».

## La regola 5/25

La banda non dovrebbe essere un unico numero assoluto per tutte le classi. La **regola 5/25** (Swedroe) usa il **minore** tra:
- **5 punti percentuali assoluti**, e
- **25% del peso target** (relativo).

La soglia effettiva è `min(5%, 25% × target)`. Perché il minore: per le classi a peso grande domina la soglia assoluta, per quelle a peso piccolo domina quella relativa. Un esempio:

| Classe | Target | 5% assoluto | 25% relativo | Soglia effettiva |
|---|---|---|---|---|
| Azionario | 60% | 5,0% | 15,0% | **5,0%** |
| Obbligazionario | 30% | 5,0% | 7,5% | **5,0%** |
| Monetario | 10% | 5,0% | 2,5% | **2,5%** |

Il monetario al 10% di target ha una banda di soli **2,5 punti**: un drift di 3 punti (dal 10% al 13%) lo manda fuori banda, mentre la banda fissa del 5% lo lascerebbe correre fino al 15%. Per una classe piccola, un drift assoluto modesto è in realtà uno scostamento **relativo** grande, e va corretto. La regola 5/25 lo coglie; la banda fissa no.

## L'allargamento cost-aware (l'adattamento italiano)

Qui sta l'innesto fiscale, ed è ciò che distingue questa skill da un ribilanciatore generico. **La banda si allarga quando correggere costa imposta netta.** Il principio:

- Se il drift si può correggere a **costo netto zero** — con i flussi (Leva 1-2), vendendo posizioni in **minus** (Leva 3), o vendendo plus **interamente compensate** dallo zainetto — allora si agisce sulla **banda stretta** (5/25). Non c'è motivo di tollerare il drift: correggerlo è gratis.
- Se invece la correzione richiede di realizzare plusvalenze che **pagano imposta** (Leva 4 non compensata), si agisce solo oltre una **banda allargata** (nello strumento, ×2 la banda stretta). Tradotto: **non si paga imposta per correggere un drift troppo piccolo per contare.** Solo quando lo scostamento è abbastanza grande — e quindi il beneficio in termini di rischio è reale — vale la pena sostenere il costo fiscale.

Questo formalizza un'intuizione che la skill già esprimeva a parole ("se il costo fiscale supera il beneficio, valutare ribilanciamento parziale o attesa"), trasformandola in una soglia operativa che dipende dal costo effettivo della correzione. È la versione tax-aware del trade-off di Kitces tra beneficio del ribilanciamento e attrito.

### Esempio del comportamento

Azionario al 68% (target 60%, drift +8%). Banda stretta 5%, banda allargata 10%.
- **Con zainetto compensabile** sulla posizione giusta: la riduzione di €8.000 è a costo netto zero → si agisce (drift +8% > banda stretta 5%) e si va a target.
- **Con zainetto parziale** (€2.000 su una plus del 40%): si vende la quota a costo zero, €5.000, e il resto (€3.000) si rinvia, dichiarandolo con il suo costo.
- **Senza zainetto**, con la sola via di vendere ETF capitale (plus tassata): il drift +8% è sotto la banda allargata 10% → **non si vende, si attende**. L'imposta da pagare non è giustificata da uno scostamento ancora moderato; i flussi futuri o un'occasione di harvesting lo correggeranno più avanti a costo minore.
- Se invece il drift fosse +12% (sopra la banda allargata 10%), si venderebbe anche pagando imposta, ma solo fino a metà banda (62,5%): a quel punto lo scostamento è abbastanza grande da giustificarla.

## La modulazione per volatilità (con una tensione onesta)

Una banda fissa rappresenta un rapporto **segnale/rumore diverso** a seconda della classe. Cinque punti di drift su un obbligazionario (volatilità ~6%) sono un movimento grande e raro; cinque punti su un azionario (~16%) o, peggio, su un comparto cripto (~70%) capitano spesso solo per il normale ondeggiare dei prezzi. Tarare la stessa soglia su tutte le classi significa, di fatto, ribilanciare le classi volatili molto più spesso — e ogni ribilanciamento costa commissioni e, spesso, imposta. Da qui l'idea di **scalare la banda con la volatilità**: la deriva attesa su un intervallo scala con la volatilità (≈ σ·√t), quindi una banda proporzionale a σ trasforma la soglia in un evento statisticamente più omogeneo tra le classi — si ribilancia sul *segnale*, non sul rumore.

Qui però va detta una cosa con onestà, perché il punto è conteso. L'intuizione "più volatile → banda più larga" non è una legge: il **controllo ottimo** (Leland e la letteratura sul no-trade region con costi di transazione) porta nella direzione **opposta**. Una deviazione su un asset volatile è più *rischiosa* — il costo atteso di stare lontano dal target cresce con la varianza — quindi un'ottimizzazione che minimizzi la perdita di rischio tollererebbe *meno* deviazione sulle classi volatili, cioè bande più *strette*. Le due visioni ottimizzano cose diverse: l'efficienza di **trading** (meno operazioni da rumore) contro l'aderenza al **target** (meno tracking error). Non c'è una risposta universale; dipende da cosa pesa di più per l'investitore.

Per un risparmiatore italiano **fiscalmente sensibile** — dove ogni vendita può realizzare imposta — l'efficienza di trading ha un peso concreto, e propendere per bande un po' più larghe sulle classi volatili è difendibile. Ma resta una *scelta*, non un automatismo, e il prezzo è una maggiore distanza media dal target proprio sulle classi che si muovono di più. Per questo l'implementazione è **deliberatamente modesta**: il fattore di modulazione `(σ_classe / σ_riferimento)^β` è **clampato** in un intervallo stretto (di default 0,7–1,6), così nessuna banda si allarga o si stringe in modo estremo, e l'intera modulazione è **spenta di default** (`MODULA_VOLATILITA = False`): la regola canonica è la pura 5/25, e accenderla è una scelta dell'utente. Sul comparto tipico: l'azionario si allarga di poco, l'obbligazionario e il monetario si stringono fino al limite del clamp, la cripto va al tetto. Resta sopra di tutto l'allargamento cost-aware, che è la leva fiscalmente decisiva; la modulazione per volatilità è un raffinamento di secondo ordine, da usare con misura.

## Cosa lascia fuori

La soglia di periodicità del controllo (mensile, trimestrale) resta una scelta dell'utente; ciò che conta è che l'**azione** dipenda dalla banda, non dal calendario. Restano fuori anche la correlazione tra classi (una banda per classe non cattura che due classi correlate derivano insieme) e la stima della volatilità stessa, che va impostata sui propri comparti e non è un dato fisso.

Cross-reference: `gerarchia-leve.md` (le quattro leve e il loro costo, che alimentano la decisione cost-aware) e `assets/ribilanciamento-multibroker.py` (implementazione di 5/25 + modulazione per volatilità + allargamento cost-aware).
