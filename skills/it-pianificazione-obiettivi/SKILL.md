---
name: it-pianificazione-obiettivi
description: Pianificazione finanziaria goals-based (per obiettivi) per investitori privati italiani. Aiuta a definire più obiettivi finanziari (fondo di emergenza, acquisto casa, università dei figli, pensione integrativa, obiettivi liberi), ciascuno con orizzonte temporale, importo e priorità, e per ognuno determina il profilo di allocazione appropriato all'orizzonte e il piano di accumulo necessario per raggiungerlo. Usa questa skill quando l'utente parla di: pianificare gli investimenti, da dove iniziare a investire, quanto mettere da parte al mese, obiettivi finanziari, fondo di emergenza, risparmiare per la casa / per i figli / per la pensione, asset allocation per obiettivo, orizzonte temporale e rischio, "ho X € e non so come allocarli", PAC piano di accumulo, bucket strategy, quanto devo risparmiare per raggiungere un obiettivo, probabilità di raggiungere un obiettivo, simulazione Monte Carlo del piano. È il passo A MONTE di `it-rebalance`: definisce l'allocazione target che poi it-rebalance mantiene. È EDUCATIVA e METODOLOGICA: insegna il framework e mostra allocazioni-tipo come esempi illustrativi, NON raccomanda titoli specifici né costituisce consulenza di investimento. NON sceglie l'asset allocation "giusta" al posto dell'utente; gli dà gli strumenti per decidere.
---

# it-pianificazione-obiettivi

Skill per la pianificazione finanziaria **goals-based** (per obiettivi) di un investitore privato italiano. È il pezzo a monte dell'intero plugin: definisce *da quali allocazioni partire* dato un insieme di obiettivi, allocazioni che poi `it-rebalance` mantiene nel tempo e che `it-tax-optimization` ottimizza fiscalmente.

## Postura della skill (importante)

Questa skill è **educativa e metodologica**, non prescrittiva. Il principio è lo stesso di `it-rebalance`: dà all'utente il framework per decidere, non decide al suo posto.

- ✅ Insegna il metodo: come legare orizzonte temporale, capacità di rischio e profilo di allocazione
- ✅ Mostra allocazioni-tipo per orizzonte come **esempi illustrativi**
- ✅ Calcola il piano di accumulo (quanto risparmiare al mese) per raggiungere ciascun obiettivo
- ✅ Aiuta a dare priorità tra obiettivi quando le risorse non bastano
- ❌ NON raccomanda titoli o ISIN specifici da comprare
- ❌ NON dichiara quale sia "l'allocazione giusta" per l'utente (dipende dalla sua tolleranza al rischio, che solo lui conosce)
- ❌ NON costituisce consulenza finanziaria o di investimento personalizzata

Per le scelte concrete di portafoglio e per una valutazione personalizzata, la skill rinvia sempre a un consulente finanziario abilitato (autonomo/fee-only, o iscritto all'albo OCF).

**Nota per l'uso personale**: chi usa la skill per sé stesso (non per erogare un servizio a terzi) può legittimamente arrivare allo strumento concreto. In quel caso la skill fornisce una **selection spec criteri-based** (vedi `references/selezione-strumenti.md`): non ISIN fissi — che invecchiano e sono fragili — ma i criteri precisi per selezionare lo strumento giusto in ciascun comparto, cuciti sulla fiscalità italiana (UCITS armonizzato, domicilio Irlanda per l'azionario USA-heavy, accumulazione per il differimento, TER e AUM come filtri, 12,5% sui titoli di Stato). Lo strumento concreto si trova applicando i criteri su uno screener aggiornato, così la spec resta valida anche quando i prodotti cambiano. Questo NON è consulenza personalizzata né una lista da seguire ciecamente: è un metodo di selezione per decisioni personali.

## Scope esplicito

**Cosa fa:**
1. **Elicita gli obiettivi** dell'utente: nome, importo target, orizzonte temporale, priorità
2. **Mappa ogni obiettivo a un profilo di allocazione** appropriato al suo orizzonte (più corto = più conservativo)
3. **Calcola il piano di accumulo** per ciascun obiettivo: quanto risparmiare al mese, dato il rendimento atteso del profilo
4. **Gestisce la priorità multi-obiettivo**: quando la capacità di risparmio non basta per tutti, aiuta a decidere cosa viene prima
5. **Aggrega i secchielli nell'allocazione complessiva** del portafoglio (vista stock e flusso) e la passa come target a `it-rebalance`; genera il **glide path** (de-risking nel tempo) e l'**asset location** (in quale contenitore fiscale tenere ciascun obiettivo); gli strumenti richiamano la fiscalità di `it-tax-optimization`; l'obiettivo pensione viene instradato a `it-pianificazione`/`it-pianificazione-autonomi`

**Cosa NON fa:**
- ❌ Non sceglie l'asset allocation al posto dell'utente (no robo-advisory)
- ❌ Non raccomanda strumenti finanziari specifici
- ❌ Non gestisce il ribilanciamento nel tempo (quello è `it-rebalance`)
- ❌ Non fa la pianificazione pensionistica dettagliata (quella è `it-pianificazione`: il fondo pensione è un veicolo dedicato con fiscalità propria)
- ❌ Non fa previsioni puntuali: il Monte Carlo (`assets/montecarlo-obiettivi.py`) dà probabilità e distribuzioni sotto ipotesi dichiarate, non garanzie

## Il framework goals-based

### Principio cardine: l'orizzonte determina il rischio sopportabile

Il cuore del goals-based investing è semplice: **più corto è l'orizzonte di un obiettivo, meno rischio di mercato puoi prenderti**, perché non hai tempo di recuperare da una perdita. Un obiettivo a 18 mesi non può stare in azionario: se il mercato cala del 30% poco prima della scadenza, l'obiettivo salta. Un obiettivo a 20 anni invece può (e dovrebbe) stare prevalentemente in azionario, perché la volatilità di breve si appiattisce e il rendimento atteso fa la differenza.

Da qui il concetto di **bucket** (secchielli): ogni obiettivo ha il suo secchiello, con un'allocazione cucita sul suo orizzonte. Non esiste "un portafoglio" unico: esistono tanti portafogli quanti sono gli obiettivi, ciascuno con il suo profilo di rischio.

### La gerarchia degli obiettivi (cosa viene prima)

```
OBIETTIVO 0 — Fondo di emergenza (PRIMA di qualsiasi altro)
  3-6 mesi di spese, massima liquidità, MAI investito in mercato
  È la fondazione: senza, qualsiasi imprevisto costringe a liquidare
  gli investimenti nel momento sbagliato

OBIETTIVI per orizzonte (dopo il fondo di emergenza):
  Breve (<3-4 anni):  preservazione del capitale (liquidità, obbligazionario)
  Medio (4-10 anni):  bilanciato (mix azionario/obbligazionario)
  Lungo (>10 anni):   crescita (prevalentemente azionario)

PRIORITÀ TRASVERSALI (prima di investire per obiettivi discrezionali):
  - Estinguere debiti ad alto interesse (es. carte revolving, prestiti cari)
  - Attivare il contributo datoriale al fondo pensione se previsto dal CCNL
    ("soldi gratis", vedi it-pianificazione)
```

### La mappa orizzonte → allocazione (esempi illustrativi)

⚠️ Queste sono allocazioni-**tipo** a scopo didattico, non raccomandazioni. La percentuale esatta dipende anche dalla tolleranza al rischio personale dell'utente.

| Orizzonte | Profilo | Azionario tipico | Logica |
|---|---|---|---|
| < 2 anni | Preservazione | 0% | Nessun rischio di mercato: serve certezza dell'importo |
| 2-4 anni | Conservativo | 0-20% | Prevalenza obbligazionario/liquidità |
| 4-7 anni | Moderato | 30-50% | Bilanciato: un po' di crescita, rischio contenuto |
| 7-12 anni | Crescita | 50-75% | L'orizzonte assorbe la volatilità |
| > 12 anni | Crescita massima | 75-100% | Massimizzare il rendimento atteso di lungo periodo |

Per la mappatura dettagliata agli strumenti italiani (conto deposito, BTP, ETF UCITS, PAC) e il concetto di **glide path** (de-risking progressivo all'avvicinarsi dell'obiettivo), vedi `references/orizzonte-allocazione.md`.

### Il glide path (de-risking all'avvicinarsi dell'obiettivo)

Un obiettivo non resta nella stessa allocazione per sempre: man mano che si avvicina la scadenza, l'allocazione va resa progressivamente più conservativa, per "bloccare" il valore raggiunto. Esempio: un obiettivo casa a 8 anni può partire bilanciato (50% azionario), ma 2 anni prima dell'acquisto va spostato quasi tutto in liquidità/obbligazionario, per non rischiare che una correzione di mercato eroda l'anticipo proprio quando serve. Questo de-risking progressivo è gestito operativamente da `it-rebalance` quando l'orizzonte si accorcia.

## Workflow operativo

### Step 1: Fotografia della situazione attuale

Raccogliere:
- `entrate_mensili_nette` e `spese_mensili` → **capacità di risparmio** mensile
- `liquidità_attuale` (conti correnti, conti deposito)
- `investimenti_esistenti` (se presenti: cosa, quanto, in quale obiettivo idealmente rientrano)
- `debiti` (mutuo, prestiti, carte) con tasso — i debiti cari hanno priorità sull'investire
- Esistenza di un **fondo di emergenza** adeguato (3-6 mesi di spese liquide): se manca, è l'obiettivo 0

### Step 2: Elicitazione degli obiettivi

Per ogni obiettivo, raccogliere:
- `nome` (es. "anticipo casa", "università figlia", "pensione integrativa", "auto nuova")
- `importo_target` (in € di oggi)
- `orizzonte_anni` (tra quanti anni serve)
- `priorità` (essenziale / importante / desiderabile)
- `importo_già_accantonato` per questo obiettivo (se esiste)

Se l'utente non ha chiari gli obiettivi, aiutarlo a strutturarli partendo dalle categorie tipiche (emergenza, casa, figli, pensione, acquisti pianificati, libertà finanziaria).

⚠️ **Obiettivo pensione**: se compare, instradarlo a `it-pianificazione` (dipendenti) o `it-pianificazione-autonomi` (P.IVA). Il fondo pensione è un veicolo dedicato con deducibilità e tassazione proprie, da NON trattare come un generico secchiello di ETF (sarebbe un doppio conteggio). Questa skill lo segnala e rinvia.

### Step 3: Profilo di allocazione per obiettivo

Per ciascun obiettivo, in base all'orizzonte, proporre il profilo-tipo (vedi mappa sopra) come **punto di partenza illustrativo**, spiegando la logica orizzonte→rischio. Invitare l'utente a calibrare in base alla propria tolleranza al rischio.

### Step 4: Piano di accumulo

Per ogni obiettivo, calcolare quanto risparmiare al mese:

```
# Importo target aggiustato per inflazione (se in € di oggi)
target_nominale = importo_target × (1 + inflazione)^orizzonte

# Rendimento atteso del profilo di allocazione scelto
rendimento_atteso = f(profilo)   # es. preservazione ~1-2%, bilanciato ~3-4%, azionario ~5-7%

# Versamento mensile necessario (formula del valore futuro di una rendita)
# target = già_accantonato × (1+r)^n + PMT × [((1+r_m)^(n×12) - 1) / r_m]
# risolvere per PMT
PMT_mensile = calcola_versamento(target_nominale, già_accantonato, rendimento_atteso, orizzonte)
```

Vedi `references/matematica-accumulo.md` per le formule complete, gli esempi worked e il trattamento dell'inflazione.

### Step 5: Riconciliazione multi-obiettivo

Sommare i versamenti mensili necessari per tutti gli obiettivi e confrontarli con la capacità di risparmio:

```
totale_versamenti_necessari = Σ PMT_mensile(obiettivo)

se totale_versamenti_necessari <= capacità_risparmio:
    → il piano è sostenibile, eventualmente avanza margine
se totale_versamenti_necessari > capacità_risparmio:
    → serve dare priorità (vedi sotto)
```

Quando le risorse non bastano, le leve per chiudere il gap (in ordine):
1. **Fondo di emergenza sempre prima** (non negoziabile)
2. **Estinguere debiti cari** prima di investire per obiettivi discrezionali
3. **Allungare l'orizzonte** di un obiettivo non urgente (più tempo = meno versamento mensile)
4. **Ridurre l'importo target** di un obiettivo desiderabile
5. **Posticipare** gli obiettivi a priorità più bassa, concentrando le risorse sugli essenziali
6. **Aumentare la capacità di risparmio** (revisione spese, se possibile — senza forzature irrealistiche)

La skill mostra il gap e le opzioni, ma la scelta di cosa sacrificare è dell'utente.

### Step 6: Allocazione complessiva del portafoglio

Gli obiettivi non sono portafogli separati nella realtà operativa: la somma delle posizioni (ETF, conti deposito, BTP) È il portafoglio. Aggregando i secchielli pesati per il loro capitale si ottiene l'**asset allocation totale** da implementare e poi mantenere con `it-rebalance`.

```
# A ogni profilo è associata una quota azionaria rappresentativa (punto medio della fascia):
# Preservazione 0% · Conservativo 10% · Moderato 40% · Crescita 65% · Crescita massima 90% · Azionario totale 100%

# Vista STOCK (sul capitale già accantonato): quanto deve essere il portafoglio OGGI
azionario_totale = Σ (capitale_obiettivo × %azionario_profilo)
quota_azionaria_portafoglio = azionario_totale / capitale_totale

# Vista FLUSSO (sui versamenti mensili): dove indirizzare i soldi NUOVI
azionario_flusso = Σ (versamento_obiettivo × %azionario_profilo)
quota_azionaria_flusso = azionario_flusso / versamento_totale
```

Punti da comunicare sempre:
- **È emergente, non scelta dall'alto**: deriva dai profili degli obiettivi pesati per il capitale. Non si decide "voglio un 60/40", lo si ottiene.
- **NON è un singolo fondo bilanciato**: implementare secchiello per secchiello. Il fondo emergenza resta liquido; l'obbligazionario di un obiettivo lungo è un'altra cosa, anche se entrambi finiscono nel "non azionario" dell'aggregato.
- **Stock ≠ flusso**: l'allocazione del capitale esistente differisce da quella dei nuovi versamenti (un portafoglio può essere 56% azionario ma avere versamenti che vanno al 100% in liquidità, se l'unico obiettivo da finanziare ora è il fondo emergenza).
- **È dinamica**: il glide path (de-risking all'avvicinarsi degli obiettivi) la sposta verso il conservativo nel tempo. Lo strumento `assets/glidepath-obiettivi.py` genera il **calendario di de-risking** anno per anno (per obiettivo e aggregato), che è il programma di spostamento dei target che `it-rebalance` esegue. Vedi `references/glide-path.md`.
- **È il target di `it-rebalance`**: questo è l'anello che collega le due skill. L'allocazione complessiva calcolata qui (e la sua evoluzione nel glide path) è esattamente l'input che `it-rebalance` mantiene.

### Step 7: Asset location (in quale contenitore fiscale)

Definita l'allocazione e gli strumenti, resta *dove* tenerli. In Italia lo spazio fiscalmente agevolato è scarso e vincolato (niente conto tax-deferred generico), quindi l'asset location è un insieme di poche decisioni mirate, non una distribuzione libera tra conti.

Il framework, per obiettivo:
- **Pensione** → **fondo pensione** (deducibile, rendimenti 20%, prestazione 15→9%): dominante per la pensione, ma vincolato fino alla pensione e quindi inutilizzabile per altri obiettivi. Instradato a `it-pianificazione`/`-autonomi`.
- **Fondo emergenza / breve** → **conto deposito** (liquidità, FITD).
- **Lungo termine (crescita)** → **dossier amministrato** con ETF ad accumulazione (default flessibile); una *quota* in **PIR** solo se si accetta consapevolmente la concentrazione su PMI italiane e il vincolo di 5 anni, in cambio dello 0% di tasse (e dell'esenzione successoria).
- **Parte sicura a medio termine** → **BTP nel dossier** (12,5%): location vantaggiosa senza vincoli aggiuntivi.
- **Finalità successoria** → polizza vita / BTP / PIR (esenti da imposta di successione), solo se la successione è prioritaria e i costi accettabili.

Principio: il **dossier amministrato è il default**; si devia verso un contenitore vincolato solo quando il suo vincolo coincide con la natura dell'obiettivo e il vantaggio fiscale supera costi e perdita di flessibilità/diversificazione. Tensioni da comunicare sempre: il fondo pensione è dominante ma vincolato; il PIR azzera le tasse ma costa concentrazione italiana (≈2% del mondo) e commissioni che possono annullare il beneficio; le polizze hanno vantaggio successorio ma costi spesso elevati. Per i **numeri** del beneficio netto c'è lo script `assets/asset-location-optimizer.py` (vedi sotto). Vedi `references/asset-location.md`.

## Strumento operativo: il pianificatore Excel

La skill include un template Excel editabile, `assets/pianificatore-obiettivi.xlsx`, complemento operativo del report. Va offerto quando l'utente vuole uno strumento riutilizzabile in cui inserire i propri obiettivi e vedere il piano aggiornarsi.

Tre fogli:
- **Parametri**: capacità di risparmio mensile, inflazione, e la tabella dei **sei profili** (Preservazione, Conservativo, Moderato, Crescita, Crescita massima, **Azionario totale** 100% per obiettivi a orizzonte perpetuo come l'eredità) con rendimento atteso, **volatilità** e **% azionario** — tutti editabili (celle blu).
- **Obiettivi**: tabella multi-obiettivo (10 slot) con menu a tendina per profilo, priorità e **tipo** (terminante/permanente). Per ogni obiettivo l'utente inserisce nome, importo target (€ di oggi), orizzonte, profilo, già accantonato, priorità, tipo; il foglio calcola target nominale, **versamento mensile necessario** (valore futuro di una rendita, ramo per rendimento 0, **floored a 0** per obiettivi già sovra-finanziati dal capitale esistente), e la scomposizione azionaria per obiettivo (capitale azionario e versamento azionario). Il **tipo** distingue gli obiettivi che si spendono a scadenza (terminante: casa, università) da quelli che restano come riserva (permanente: fondo emergenza), ed è usato dal glide path. Tre obiettivi di esempio precompilati coerenti con `references/matematica-accumulo.md`.
- **Riepilogo**: riconciliazione totale versamenti vs capacità (margine/gap, stato), breakdown per priorità (SUMIF), e l'**allocazione complessiva del portafoglio** in vista stock (sul capitale) e flusso (sui versamenti), con le note su come usarla.

Convenzioni industry-standard (blu = input, nero = formule, verde = cross-sheet). 50 formule, zero errori. La matematica è quella della reference, così i numeri dell'Excel e del report coincidono.

### Allocatore di capitale (distribuzione di una somma liquida)

Quando l'utente parte da una **somma liquida da investire** (es. liquida un vecchio gestito e costruisce un portafoglio da zero), il primo passo non è il pianificatore ma lo script `assets/allocatore-capitale.py`: dati la somma e gli obiettivi (li legge dallo stesso Excel), propone **quanto capitale dedicare a ogni secchiello** e ne ricava la **vista aggregata su tre classi — azioni, obbligazioni, liquidità**. È il complemento dell'Excel: l'Excel prende la ripartizione del capitale come *dato* e calcola i versamenti; l'allocatore *propone* la ripartizione e dà l'aggregato a tre classi (l'Excel si ferma ad azionario vs non azionario).

La logica è goals-based per **valore attuale**, con una distinzione che conta: le **riserve permanenti** (fondo emergenza) si finanziano al **valore pieno in liquidità oggi** — le vuoi disponibili adesso, non in crescita verso una scadenza; gli obiettivi **terminanti** ricevono il loro **present value** (`target_oggi × ((1+inflazione)/(1+rendimento))^anni`), il capitale che al rendimento del profilo cresce fino al target entro la scadenza. La somma si alloca in ordine di **priorità** (essenziale prima), poi per orizzonte; se **avanza**, l'eccedenza è capitale libero, che può essere **diviso tra più obiettivi di lungo termine** (parametro `CAPITALE_LIBERO_SPLIT`: es. integrazione pensione + eredità, ciascuno con peso e profilo propri) — è la parte che pesa di più sull'aggregato, e cambiarne pesi o profili lo sposta più di ogni altra leva; se **non basta**, si finanzia per priorità e il resto va ai versamenti. L'aggregato distingue obbligazioni e liquidità: la parte non azionaria dei secchielli a profilo Preservazione è liquidità, quella degli obiettivi investiti è obbligazionaria. È **onesto sui limiti**: vista "lump sum" (i versamenti, se presenti, riducono il capitale richiesto), e ricorda che liquidare il vecchio gestito realizza plus/minus con la trappola del reddito di capitale (rimanda a `it-tax-optimization` per l'ordine di smontaggio). Esecuzione: `pip install openpyxl` poi `python allocatore-capitale.py [percorso.xlsx] [capitale]`. L'aggregato che produce è il **target** che alimenta il pianificatore Excel e `it-rebalance`.

### Monte Carlo (probabilità di successo)

Il foglio Excel calcola il versamento **deterministico**, che centra il rendimento medio → tipicamente ~50% di probabilità di raggiungere l'obiettivo. Per la visione probabilistica c'è lo script `assets/montecarlo-obiettivi.py`: legge gli obiettivi dal foglio Excel, simula migliaia di percorsi di accumulo con rendimenti casuali (media = rendimento del profilo, deviazione = volatilità del profilo, ora nella tabella Parametri), e per ciascun obiettivo restituisce la **probabilità di successo**, i percentili del capitale finale (10°/50°/90°) e il versamento che servirebbe per una confidenza-obiettivo (default 85%).

Il messaggio chiave: il versamento "esatto" del foglio è poco più di un testa-o-croce (~50%, meno per orizzonti lunghi ad alta volatilità per via del *volatility drag*). Per gli obiettivi essenziali si vuole confidenza alta, quindi un versamento più alto del deterministico. Offrire il Monte Carlo quando l'utente vuole capire il rischio reale del piano, non solo il numero medio.

Esecuzione: `pip install numpy openpyxl` poi `python montecarlo-obiettivi.py`. **Due modelli dei rendimenti** (parametro `MODELLO`): `"normale"` (Normale i.i.d., default) o `"bootstrap"`, che ricampiona a blocchi da una **serie storica reale** (`assets/rendimenti-storici.csv`: S&P 500 e T-Bond decennale 1928-2025, fonte Damodaran/NYU Stern), combinata per il % azionario del profilo, con la media ricentrata sull'ipotesi del profilo (calibra la media, mantiene forma/code/correlazioni reali). Confrontare i due modelli mostra quanto le conclusioni dipendono dalle ipotesi distributive; spesso su orizzonti lunghi il bootstrap dà una distribuzione *più stretta* (mean reversion e correlazione azionario/obbligazionario reali, che la Normale i.i.d. ignora). La metodologia, le volatilità per profilo, l'interpretazione della confidenza e i **limiti** sono in `references/monte-carlo.md`. I numeri sono ordini di grandezza per calibrare il rischio, non garanzie.

In modalità bootstrap lo script aggiunge una sezione **rischio sistemico**: gli obiettivi non sono indipendenti, perché condividono lo stesso mercato (un crollo li colpisce insieme). Una **simulazione congiunta** estrae un unico percorso di mercato per simulazione e lo applica a tutti gli obiettivi, riportando la probabilità che **tutti gli essenziali falliscano nello stesso scenario** — confrontata con il prodotto ingenuo delle probabilità indipendenti, che la **sottostima**. È una delle due correzioni di onestà del Monte Carlo (l'altra è la non-USA-centricità: vedi `references/mercati-e-correlazione.md`).

Per ogni obiettivo lo script mostra anche la **seconda strada**: quando il versamento per la confidenza supera la capacità e non si può versare di più, resta la leva di **alzare il rischio** (la quota azionaria) a parità di versamento. Lo strumento fa lo sweep dell'allocazione, trova quella che massimizza la probabilità, e — punto chiave di onestà — mostra la **distribuzione intera**, non solo la probabilità, perché più rischio alza la mediana ma allarga la coda sinistra (il 10° percentile può peggiorare). Segnala quando la leva è **inadatta** (obiettivo essenziale o importante, oppure entro la finestra di de-risking di 7 anni, dove il glide path abbassa la quota azionaria), **controproducente** (già in linea) o un'**opzione reale** (sotto-finanziato, lungo orizzonte, discrezionale), e ne quantifica il costo sul caso brutto. La relazione rischio-probabilità non è monotòna: oltre una certa quota il volatility drag riabbassa la probabilità. Trattare l'allocazione come una leva con un costo esplicito, e non come un parametro fisso, è una scelta di metodo; dettagli in `references/monte-carlo.md`.

### Glide path (calendario di de-risking)

L'allocazione complessiva non è statica: man mano che gli obiettivi si avvicinano, i loro secchielli vanno de-riskati. Lo script `assets/glidepath-obiettivi.py` genera il **calendario di de-risking** anno per anno: per ciascun obiettivo, la quota azionaria target a ogni anno (tiene la quota piena finché manca più della finestra di de-risking, default 7 anni, poi scende linearmente fino all'atterraggio, default 0%, entro la scadenza), e l'aggregato di portafoglio pesato per il capitale proiettato.

È il **programma di spostamento dei target che `it-rebalance` esegue**: ogni anno il target di un secchiello in de-risking si abbassa, e it-rebalance vende azionario per comprare obbligazionario/liquidità. Gli obiettivi marcati **permanenti** (colonna Tipo: il fondo emergenza) non de-riskano e restano in portafoglio come riserva, smussando l'aggregato invece di farlo saltare quando un obiettivo si conclude; i **terminanti** de-riskano ed escono a scadenza (si spendono). ⚠️ Ogni vendita è un evento fiscale: il de-risking graduale distribuisce gli eventi nel tempo, e i nuovi versamenti verso la componente in crescita riducono la necessità di vendere. Offrire il glide path quando l'utente ha obiettivi a data fissa (casa, università) e vuole sapere come ridurre il rischio avvicinandosi.

Esecuzione: `pip install openpyxl` poi `python glidepath-obiettivi.py`. La formula, i parametri editabili (finestra, atterraggio, **curvatura** della rampa: lineare di default, oppure azionario più alto a lungo poi discesa ripida), la sottigliezza obiettivi terminanti vs permanenti, il coordinamento fiscale e i limiti sono in `references/glide-path.md`.

### Ottimizzatore asset location (beneficio fiscale netto)

La reference `asset-location.md` dà il framework qualitativo (quale contenitore per quale obiettivo); lo script `assets/asset-location-optimizer.py` ne dà i **numeri**. Calcola il valore finale **al netto di tasse E costi** in ciascun contenitore, per le due decisioni dove il beneficio è quantificabile:

- **Fondo pensione vs dossier** (per la pensione): la deduzione IRPEF è il driver (es. €5.300/anno al 33% = €52.470 cumulati su 30 anni), ma i rendimenti tassati al 20% ogni anno e l'ISC più alto la erodono; il vantaggio netto resta positivo ma più contenuto di quanto suggerisca la sola deduzione (nel test sui dati reali ≈ +9% vs dossier).
- **PIR vs dossier** (per obiettivi a lungo termine): l'esenzione (0% sulle plus) contro il TER più alto del PIR. Risultato spesso **controintuitivo**: su orizzonti lunghi il costo del PIR supera il risparmio fiscale e il vantaggio diventa **negativo** (nel test, università €50k a 19 anni: −€2.861, con TER di pareggio 1,15% contro TER tipici 1,2-1,35%). Lo script stampa il **TER di pareggio**: sotto quel costo il PIR conviene, sopra no.

È la conferma quantitativa dello scetticismo della reference: lo 0% del PIR è spesso mangiato dai costi. ⚠️ La comparazione PIR/dossier assume lo *stesso* rendimento e quindi NON cattura il costo di concentrazione del PIR (PMI italiane) — un rischio in più, non meno. Parametri (aliquota marginale, TER, ISC, anni, contributo) editabili in cima allo script. Esecuzione: `pip install openpyxl` poi `python asset-location-optimizer.py`. Offrirlo quando l'utente vuole sapere *quanto* vale davvero un contenitore agevolato, non solo se usarlo.

## La fase di decumulo (prelievo)

Tutto quanto sopra riguarda l'**accumulo**. Quando un obiettivo si trasforma in fonte di prelievo (la pensione integrativa una volta in pensione, o una riserva permanente da cui si attinge), il problema cambia natura: **il decumulo non è l'accumulo al contrario**. Conta l'**ordine** dei rendimenti, non solo la media — una brutta sequenza nei primi anni costringe a vendere a prezzi bassi e può esaurire il capitale anche con un rendimento medio buono. È il **rischio di sequenza dei rendimenti**, il rischio dominante del prelievo.

Lo script `assets/decumulo-obiettivi.py` lo rende quantitativo: calcola la **probabilità che il capitale duri** l'orizzonte (bootstrap a blocchi dalla serie storica, che preserva la sequenza), una **tabella di sensibilità** su più tassi di prelievo, la **dimostrazione del rischio di sequenza** (lo stesso insieme di rendimenti nei due ordini opposti — stessa media, esiti opposti: uno esaurisce, l'altro cresce), il confronto **con/senza buffer di liquidità**, e il confronto **lente USA vs scenario globale** (parametro `DERATING_AZIONARIO`, vedi sotto). Tre avvertenze da comunicare sempre: (1) la celebre **regola del 4%** nasce su dati USA (mercato storicamente eccezionale) e orizzonte 30 anni → per un investitore europeo con orizzonte lungo va **scontata** (3-3,5% più difendibile); (2) il **buffer di liquidità non è un free lunch** — sui dati storici può addirittura abbassare il tasso di successo (la liquidità rende ~0), e il suo valore è soprattutto comportamentale e contro i bear prolungati; (3) le mitigazioni più efficaci sono i **prelievi dinamici** (guardrail) e la **flessibilità di spesa**. Tutto in `references/decumulo.md`. Il **de-rating** dell'azionario (trasformare la serie USA in scenario globale, −1,5% sull'azionario reale per riflettere lo scarto USA-vs-mondo del Global Investment Returns Yearbook) è in `references/mercati-e-correlazione.md`. La dimensione **fiscale** del prelievo (quali posizioni e contenitori liquidare per minimizzare l'imposta, e l'aliquota agevolata 9-15% del fondo pensione in erogazione) è in `it-rebalance/references/sequenza-liquidazione.md`.

## Formato output

Report markdown in sezioni:

### 1. Situazione attuale

| Voce | Valore |
|---|---|
| Capacità di risparmio mensile | €X |
| Liquidità attuale | €X |
| Fondo di emergenza | Adeguato / Da costruire (€X mancanti) |
| Debiti rilevanti | … |

### 2. Obiettivi definiti

| Obiettivo | Importo | Orizzonte | Priorità | Profilo allocazione |
|---|---|---|---|---|
| Fondo emergenza | €X (3-6 mesi spese) | immediato | essenziale | 100% liquidità |
| Anticipo casa | €X | 6 anni | importante | moderato (~40% azionario) |
| … | | | | |

### 3. Piano di accumulo per obiettivo

Per ciascun obiettivo: importo target (nominale, con inflazione), rendimento atteso del profilo, versamento mensile necessario, e cosa serve già avere accantonato.

### 4. Quadro complessivo e riconciliazione

- Totale versamenti mensili necessari vs capacità di risparmio
- Se sostenibile: conferma + eventuale margine
- Se non sostenibile: gap e opzioni di priorità

### 5. Collegamento alle altre skill

- Le allocazioni-target definite → input per `it-rebalance`
- Gli strumenti (ETF UCITS, BTP, conti deposito) → trattamento fiscale in `it-tax-optimization`
- L'obiettivo pensione → `it-pianificazione` / `it-pianificazione-autonomi`

### Disclaimer (obbligatorio in fondo)

> **Disclaimer**: questo report ha finalità informative ed educative di pianificazione personale. Non costituisce consulenza finanziaria, di investimento, fiscale o legale. Le allocazioni-tipo per orizzonte sono esempi didattici, non raccomandazioni: la composizione adatta dipende dalla tolleranza al rischio e dalla situazione complessiva di ciascuno. La skill NON raccomanda strumenti finanziari specifici. I rendimenti attesi sono ipotesi di lungo periodo con forte variabilità; i risultati reali possono divergere significativamente. Per definire la propria asset allocation, scegliere strumenti concreti e ricevere una valutazione personalizzata, consultare un consulente finanziario abilitato (autonomo/fee-only o iscritto all'albo OCF).

## Anti-pattern (NON FARE MAI)

- ❌ **Raccomandare titoli o ISIN specifici come "da comprare" a terzi**: la skill è educativa. Per l'uso personale può dare una selection spec criteri-based (vedi `references/selezione-strumenti.md`), ma mai ISIN fissi — che invecchiano — né raccomandazioni personalizzate a soggetti diversi da chi decide per sé. La spec dà i criteri, lo strumento concreto si trova su uno screener aggiornato.
- ❌ **Dichiarare quale allocazione sia "giusta" per l'utente**: dipende dalla sua tolleranza al rischio, che la skill non può conoscere. Proporre profili-tipo e far calibrare a lui.
- ❌ **Investire il fondo di emergenza**: deve restare liquido e accessibile. Metterlo in ETF azionario è l'errore più pericoloso (quando serve, potrebbe essere in perdita).
- ❌ **Mettere obiettivi a breve in azionario**: senza tempo per recuperare da un drawdown, si rischia l'importo proprio quando serve.
- ❌ **Lasciare obiettivi a lunghissimo termine in liquidità**: l'inflazione erode il potere d'acquisto; a 20 anni la liquidità è una perdita reale quasi certa.
- ❌ **Ignorare l'inflazione sull'importo target**: €30.000 tra 10 anni valgono meno di €30.000 oggi. Sempre proiettare il target a nominale.
- ❌ **Doppio conteggio dell'obiettivo pensione**: il fondo pensione è un veicolo dedicato (it-pianificazione), non un generico secchiello di ETF. Instradarlo, non duplicarlo.
- ❌ **Ottimizzare le allocazioni senza il fondo di emergenza in piedi**: è la fondazione, viene prima di tutto.
- ❌ **Trattare l'allocazione proposta come definitiva**: ogni obiettivo ha un glide path (de-risking all'avvicinarsi), gestito poi da it-rebalance.
- ❌ **Forzare una capacità di risparmio irrealistica** per far quadrare i conti: meglio un piano sostenibile e parziale che uno perfetto sulla carta e insostenibile.
- ❌ **Presentare i rendimenti attesi come certezze**: sono ipotesi con ampia variabilità, vanno comunicati come range.

## Sinergia con le altre skill del plugin

`it-pianificazione-obiettivi` è il pezzo a **monte** che alimenta gli altri:

- **→ `it-rebalance`**: le allocazioni-target dei singoli obiettivi, **aggregate per capitale**, danno l'asset allocation complessiva del portafoglio (Step 6) — ed è esattamente questa l'allocazione-target che `it-rebalance` riceve in input e mantiene nel tempo, eseguendo il glide path (de-risking all'avvicinarsi degli obiettivi). Questo chiude il cerchio: prima `it-rebalance` riceveva il target "dall'esterno"; ora la sua fonte è l'aggregazione dei secchielli calcolata qui.
- **→ `it-tax-optimization`**: gli strumenti suggeriti per i secchielli (ETF UCITS armonizzati, BTP a 12,5%, conti deposito) portano con sé il trattamento fiscale; quando si realizzano plus/minus, entra in gioco it-tax-optimization.
- **→ `it-pianificazione` / `it-pianificazione-autonomi`**: l'obiettivo "pensione integrativa", se presente, viene instradato alla skill previdenziale dedicata, perché il fondo pensione ha deducibilità e tassazione proprie (e per i forfettari la deduzione non c'è — vedi quella skill).

Workflow tipico end-to-end: l'utente parte da qui per definire obiettivi e allocazioni → usa `it-pianificazione`/`it-pianificazione-autonomi` per il secchiello pensione → usa `it-rebalance` per mantenere le allocazioni → usa `it-tax-optimization` a fine anno per ottimizzare la fiscalità delle vendite.

## Riferimenti

- `references/orizzonte-allocazione.md` — mappatura dettagliata orizzonte → profilo → strumenti italiani (conto deposito, BTP/titoli di Stato, ETF UCITS, PAC), il fondo di emergenza, il glide path
- `references/matematica-accumulo.md` — formule del piano di accumulo (valore futuro, versamento necessario, rendimento richiesto), trattamento inflazione, esempi worked, riconciliazione multi-obiettivo
- `references/allocazione-capitale.md` — come distribuire una somma liquida tra gli obiettivi (present value per i terminanti, valore pieno in liquidità per le riserve permanenti, ordine per priorità, capitale libero da formalizzare) e la vista aggregata su tre classi (azioni/obbligazioni/liquidità); i limiti (vista lump sum, fiscalità della liquidazione)
- `references/selezione-strumenti.md` — (uso personale) selection spec criteri-based per scegliere lo strumento in ciascun comparto: criteri universali ETF UCITS, spec per comparto, ganci fiscali, workflow con screener. Niente ISIN fissi.
- `assets/pianificatore-obiettivi.xlsx` — template Excel editabile (3 fogli: Parametri, Obiettivi, Riepilogo), tabella multi-obiettivo con versamento mensile, riconciliazione vs capacità, scomposizione azionaria per obiettivo e **allocazione complessiva del portafoglio** (stock + flusso), 90 formule
- `assets/allocatore-capitale.py` — allocatore di una somma liquida tra i secchielli per valore attuale (riserve permanenti al valore pieno in liquidità, obiettivi terminanti al present value), con la **vista aggregata su tre classi** (azioni/obbligazioni/liquidità) che fa da target per l'Excel e it-rebalance; onesto sul capitale libero e sulla fiscalità della liquidazione (richiede openpyxl)
- `references/monte-carlo.md` — metodologia della simulazione Monte Carlo: perché il deterministico dà ~50%, i due modelli (Normale i.i.d. e bootstrap storico), le volatilità per profilo, come calibrare la confidenza, il rischio di sequenza, le **tre strade per colmare un gap** (versare di più, alzare il rischio come leva a doppio taglio, aggiustare l'obiettivo), e i limiti del modello
- `references/glide-path.md` — metodologia del glide path: la formula (finestra + atterraggio + curvatura), le viste per-obiettivo e aggregata, la sottigliezza terminanti/permanenti, il coordinamento fiscale con it-rebalance, i limiti
- `references/asset-location.md` — (uso personale) in quale contenitore fiscale tenere ciascun obiettivo: dossier amministrato, fondo pensione, PIR, polizze, conto deposito; il framework per obiettivo, le tensioni (vincolo pensione, concentrazione PIR, costi polizze), l'interazione con le altre skill
- `assets/glidepath-obiettivi.py` — script che genera il calendario di de-risking anno per anno (per obiettivo e aggregato), il programma di target che alimenta it-rebalance (richiede openpyxl)
- `assets/montecarlo-obiettivi.py` — script che legge gli obiettivi dall'Excel e calcola la probabilità di successo, i percentili del capitale finale e il versamento per una confidenza-obiettivo; due modelli (Normale i.i.d. o bootstrap storico) (richiede numpy, openpyxl)
- `assets/rendimenti-storici.csv` — serie annuale azionario (S&P 500) e obbligazionario (T-Bond 10 anni) 1928-2025 per il bootstrap del Monte Carlo (fonte Damodaran/NYU Stern; sostituibile con una propria serie)
- `references/decumulo.md` — la fase di prelievo: tasso sostenibile (regola del 4% e perché va scontata per l'Europa), rischio di sequenza dei rendimenti, mitigazioni (buffer, guardrail, flessibilità di spesa, bond tent)
- `assets/decumulo-obiettivi.py` — simulazione del decumulo: probabilità di successo, sensibilità sul tasso di prelievo, dimostrazione del rischio di sequenza, confronto con/senza buffer, lente USA vs scenario globale (de-rating) (richiede numpy; usa rendimenti-storici.csv)
- `references/mercati-e-correlazione.md` — le due correzioni di onestà al Monte Carlo: la **non-USA-centricità** (l'azionario mondiale rende ~5,2% reale vs gli USA eccezionali, fonte DMS; de-rating e calibrazione globale) e la **correlazione sistemica** tra obiettivi (un crollo li colpisce insieme; l'indipendenza sottostima il rischio che saltino tutti nello stesso scenario)
- **Vedi anche** `it-rebalance/SKILL.md` (mantenimento delle allocazioni), `it-tax-optimization/SKILL.md` (fiscalità degli strumenti), `it-pianificazione/SKILL.md` (obiettivo pensione)

## Note per l'iterazione

Questa è la versione 0.19 della skill (introdotta in v0.7 del plugin, estesa fino a v0.9.4).

In quest'iterazione (v0.19):
- **Guardia sulle intestazioni** del pianificatore (via `motore_bootstrap.verifica_intestazioni_obiettivi`): gli script leggono le colonne per posizione, quindi un layout modificato produrrebbe dati sbagliati in silenzio — ora produce un errore esplicito che indica colonna e intestazione attesa. Attiva in tutti e quattro i lettori (Monte Carlo, glide path, allocatore, asset location).
- **`--json <file>`** sull'allocatore: aggregato a tre classi, surplus/deficit e allocazioni per obiettivo in output machine-readable (alimenta il tracker e il glide path senza ricopiare numeri).

In quest'iterazione (v0.18):
- **Override `--set NOME=VALORE`** su tutti gli script della skill (Monte Carlo, glide path, allocatore, asset location, decumulo), via `motore_bootstrap.applica_override`: parametri di scenario da riga di comando, senza toccare i file, componibili con gli argomenti esistenti — es. `python glidepath-obiettivi.py piano.xlsx --set FINESTRA_DERISK=5`. Refusi respinti, override loggati.

In quest'iterazione (v0.17):
- **Motore bootstrap condiviso** (`motore_bootstrap.py`, copia sincronizzata con `it-pianificazione`): `montecarlo-obiettivi.py` importa `carica_storico`, `blocchi_bootstrap` (traiettorie di portafoglio) e `indici_bootstrap` (estrazione condivisa di anni storici per il rischio congiunto — stessi shock per tutti gli obiettivi). Refactor validato bit-per-bit sul modello bootstrap con seed. `decumulo-obiettivi.py` mantiene deliberatamente la sua variante (blocchi non circolari, Generator): unificarla cambierebbe i percorsi simulati.

In quest'iterazione (v0.16):
- **Glide path con obiettivi senza target**: `glidepath-obiettivi.py` accetta nativamente gli obiettivi "il più possibile" (colonna target vuota) — prima venivano saltati e serviva un target fittizio. Per questi obiettivi non si calcola alcun versamento "necessario" (si proietta il solo capitale assegnato); il marcatore `(max)` li identifica nell'output. Se terminanti de-riskano e a scadenza si spendono; se permanenti restano e non de-riskano mai. Validato sul caso reale a quattro obiettivi (due con target, due senza).

In quest'iterazione (v0.15):
- **Capitale libero divisibile tra più obiettivi di lungo termine** nell'allocatore (`CAPITALE_LIBERO_SPLIT`): l'eccedenza non va più a un unico bucket ma può essere ripartita (con pesi e profili distinti) tra obiettivi come integrazione pensione ed eredità — è la leva che muove di più l'aggregato. Aggiunto un **sesto profilo "Azionario totale" (100%)** per obiettivi a orizzonte perpetuo (es. eredità che passa agli eredi senza mai liquidare: nessun rischio di sequenza da proteggere). Il profilo è first-class (tendina Excel, VLOOKUP estesi, letto da tutti gli script). Validato su dati reali (aggregato che passa dal 57% al 70% azionario spostando l'eredità al 100%) e a invariante (somma classi = capitale).

In quest'iterazione (v0.14):
- **Allocatore di capitale** (`assets/allocatore-capitale.py`): per chi parte da una **somma liquida** da investire (es. liquidando un vecchio gestito), propone come distribuirla tra i secchielli e ne ricava la **vista aggregata a tre classi** (azioni/obbligazioni/liquidità). Logica per valore attuale: riserve permanenti al valore pieno in liquidità, obiettivi terminanti al present value; allocazione per priorità; eccedenza come capitale libero (segnalato come da formalizzare). Colma il pezzo mancante tra "ho una somma" e "qual è la mia allocazione": l'Excel prendeva la ripartizione come dato e si fermava ad azionario vs non azionario, l'allocatore propone la ripartizione e dà le tre classi. Onesto sui limiti (vista lump sum; fiscalità della liquidazione rimandata a it-tax-optimization). Validato su dati reali e casi limite (capitale insufficiente, già accantonato, invariante somma = capitale). Dettagli in `references/allocazione-capitale.md`.

In quest'iterazione (v0.13):
- **Seconda strada nel Monte Carlo — la leva di rischio** (`assets/montecarlo-obiettivi.py`): quando il versamento per la confidenza supera la capacità e non si può versare di più, lo strumento mostra l'alternativa di alzare la quota azionaria a parità di versamento. Fa lo sweep dell'allocazione, trova quella che massimizza la probabilità, e — punto di onestà — mostra la **distribuzione intera** (non solo la probabilità) perché più rischio peggiora la coda sinistra. Segnala quando la leva è inadatta (essenziale/breve), controproducente (già in linea) o un'opzione reale (sotto-finanziato, lungo orizzonte), col costo sul caso brutto quantificato. Validato su dati reali e sintetici; la relazione rischio-probabilità non-monotòna è catturata. Allinea il modello allo spirito del fork (l'allocazione è una leva con un costo, non un 60/40 fisso). Dettagli in `references/monte-carlo.md`.

Versioni precedenti:
- Pianificazione goals-based generale multi-obiettivo
- Profili di allocazione come esempi illustrativi (no robo-advisory)
- Strumenti italiani principali (conto deposito, BTP, ETF UCITS, PAC)
- Selection spec criteri-based per la scelta dello strumento concreto (uso personale)
- Pianificatore Excel multi-obiettivo (`assets/pianificatore-obiettivi.xlsx`)
- Simulazione Monte Carlo della probabilità di raggiungimento (`assets/montecarlo-obiettivi.py`)
- Allocazione complessiva del portafoglio (aggregazione dei secchielli, stock + flusso)
- Glide path automatico: calendario di de-risking anno per anno (`assets/glidepath-obiettivi.py`)
- Flag terminante/permanente per obiettivo
- Asset location avanzato: quale contenitore fiscale per quale obiettivo (`references/asset-location.md`)
- Ottimizzatore quantitativo dell'asset location: beneficio fiscale netto per contenitore (`assets/asset-location-optimizer.py`), con reinvestimento opzionale del risparmio IRPEF
- Monte Carlo con modello **bootstrap** da serie storica reale (`assets/rendimenti-storici.csv`) in alternativa alla Normale: code grasse, correlazioni e mean reversion reali
- **Fase di decumulo** (`references/decumulo.md` + `assets/decumulo-obiettivi.py`): tasso di prelievo sostenibile, rischio di sequenza dei rendimenti, mitigazioni, con la regola del 4% scontata onestamente per l'Europa
- **Due correzioni di onestà al Monte Carlo** (`references/mercati-e-correlazione.md`): la non-USA-centricità del bootstrap (de-rating dell'azionario per passare dalla serie USA — eccezionale — allo scenario globale ~5,2% reale del Global Investment Returns Yearbook) e la correlazione sistemica tra obiettivi (simulazione congiunta con un unico percorso di mercato condiviso: l'indipendenza sottostima il rischio che saltino tutti insieme). Entrambe spostano le conclusioni verso il prudente.
- Glide path a **curvatura** regolabile (lineare o non lineare)

Roadmap:
- ✅ Fase di **decumulo** delle riserve permanenti: coperta in `references/decumulo.md` + `assets/decumulo-obiettivi.py` (tasso sostenibile, rischio di sequenza, mitigazioni); la sequenza di liquidazione **fiscale** è in `it-rebalance/references/sequenza-liquidazione.md`
- Possibile: bootstrap da serie storiche multiple (Europa, mondo) oltre a quella USA; correlazione sistemica tra obiettivi nel Monte Carlo
