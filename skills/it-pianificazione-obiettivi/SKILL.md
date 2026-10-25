---
name: it-pianificazione-obiettivi
description: "Pianificazione finanziaria per obiettivi (goals-based) per investitori privati italiani: più obiettivi (fondo di emergenza, casa, università dei figli, pensione integrativa, obiettivi liberi), ciascuno con orizzonte, importo e priorità, profilo di allocazione e piano di accumulo. Usa questa skill quando l'utente parla di pianificare gli investimenti, da dove iniziare, quanto mettere da parte al mese, fondo di emergenza, risparmiare per la casa o per i figli, asset allocation per obiettivo, orizzonte e rischio, «ho X € e non so come allocarli», PAC, bucket strategy, probabilità di raggiungere un obiettivo, Monte Carlo del piano, glide path, capitale umano (reddito da lavoro nella ricchezza totale, «sono un'azione o un'obbligazione?»). È il passo a monte di `it-rebalance`: definisce l'allocazione target che quella mantiene. Postura educativa e metodologica: mostra allocazioni-tipo come esempi, NON raccomanda titoli specifici, NON sceglie l'allocazione al posto dell'utente e NON è consulenza di investimento."
metadata:
  version: "0.21"
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

## Dove lavorare

I dati personali e i file compilati vivono nella **cartella di lavoro** dell'utente (per esempio `~/piano-finanziario/`; se il plugin è stato installato con Claude Code, è quella scelta all'installazione: `${user_config.cartella_lavoro}`; se il segnaposto qui sopra non è stato sostituito, chiedila all'utente), mai dentro il plugin: la copia installata si sovrascrive a ogni aggiornamento. Regole:

- i modelli Excel si **copiano** nella cartella di lavoro e si compilano lì, mai in `assets/`: `${CLAUDE_SKILL_DIR}/assets/pianificatore-obiettivi.xlsx`;
- gli script si lanciano dalla cartella di lavoro con il loro percorso nel plugin, e il file da leggere si passa sempre come argomento (`--help` elenca argomenti e opzioni): `python "${CLAUDE_SKILL_DIR}/assets/montecarlo-obiettivi.py" pianificatore-obiettivi.xlsx --json montecarlo.json`, `python "${CLAUDE_SKILL_DIR}/assets/glidepath-obiettivi.py" pianificatore-obiettivi.xlsx --json glide.json`, `python "${CLAUDE_SKILL_DIR}/assets/allocatore-capitale.py" pianificatore-obiettivi.xlsx 50000 --json allocazione.json`;
- gli output (JSON, CSV degli ordini, documenti) finiscono nella cartella di lavoro, mai nel plugin.

`${CLAUDE_SKILL_DIR}` è la cartella di questa skill: Claude Code lo sostituisce con il percorso reale quando carica la skill (anche quando la skill la carica un comando: i comandi sono alias e non lanciano script). Dipendenze degli script: Python 3.11 o successivo con numpy e openpyxl (`pip install numpy openpyxl`).

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

# Rendimento atteso del profilo di allocazione scelto (nominale, netto, media aritmetica)
r = f(profilo)   # es. preservazione ~1-2%, bilanciato ~3-4%, azionario ~5-7%
F(r, a) = ((1+r)^a − 1) / ((1+r)^(1/12) − 1)   # valore futuro di €1 al mese per a anni

# Quota fissa: solo permanenti e profili senza azionario (non de-riskano)
# target = già_accantonato × (1+r)^n + PMT × F(r, n)

# Terminanti con azionario: due fasi, perché il glide path abbassa il rendimento negli ultimi anni
m  = min(finestra, n) − 1          # anni di de-risking (finestra in Parametri!B7)
k  = n − m                         # anni a quota piena
r2 = (r + r_atterraggio) / 2       # rendimento medio della rampa (atterraggio = Preservazione)
# target = [già_accantonato × (1+r)^k + PMT × F(r, k)] × (1+r2)^m + PMT × F(r2, m)

PMT_mensile = risolvere per PMT    # è la colonna I del foglio; floor a 0 se il già accantonato basta
```

Convenzioni da dichiarare (le stesse di foglio e script):
- i rendimenti dei profili sono **nominali** e **netti di costi e imposte**, come se tassati ogni anno: dal lordo atteso, **netto ≈ (lordo − costi) × (1 − 26%)** (prudente: negli ETF ad accumulazione l'imposta si paga alla vendita). Con questa convenzione il versamento non sottostima l'imposta a scadenza. Solo l'ottimizzatore di asset location riparte dal lordo, con la conversione inversa esplicita;
- sono **medie aritmetiche annue attese**: la crescita composta mediana è circa rendimento − volatilità²/2 (lo mostra il Monte Carlo). Per tarare un profilo su rendimenti annualizzati, come quelli DMS, si aggiunge volatilità²/2 (`references/mercati-e-correlazione.md`);
- gli obiettivi **terminanti** de-riskano negli ultimi anni (glide path, finestra in Parametri!B7): il versamento lo sconta, perché il rendimento scende proprio quando il capitale è più grande. Sull'esempio a 20 anni (Crescita) servono €384/mese invece dei €346 a quota fissa; ignorarlo lascia l'obiettivo sotto-finanziato di circa il 10%.

Vedi `references/matematica-accumulo.md` per le formule complete (anche quella in due fasi del glide path), gli esempi worked e il trattamento dell'inflazione.

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
- **Finalità successoria** → polizza vita / BTP / PIR (esenti da imposta di successione), solo se la successione è prioritaria e i costi accettabili. Per azioni e obbligazioni dirette il costo degli eredi riparte dal valore di successione; per fondi ed ETF non è garantito: vedi `it-tax-optimization/references/successione-donazione.md`.

Principio: il **dossier amministrato è il default**; si devia verso un contenitore vincolato solo quando il suo vincolo coincide con la natura dell'obiettivo e il vantaggio fiscale supera costi e perdita di flessibilità/diversificazione. Tensioni da comunicare sempre: il fondo pensione è dominante ma vincolato; il PIR azzera le tasse ma costa concentrazione italiana (≈2% del mondo) e commissioni che possono annullare il beneficio; le polizze hanno vantaggio successorio ma costi spesso elevati. Per i **numeri** del beneficio netto c'è lo script `assets/asset-location-optimizer.py` (vedi sotto). Vedi `references/asset-location.md`.

### Step 8 (facoltativo): la lente del capitale umano

Il portafoglio non è tutta la ricchezza di chi lavora: il bene più grande è spesso il **capitale umano**, il valore attuale dei redditi da lavoro futuri, più la pensione INPS che verrà. Questo step li mette nel conto, per capire se il portafoglio **compensa** il capitale umano o lo **duplica** (un dipendente pubblico ha già una grossa «obbligazione»; chi lavora in finanza o nella tecnologia ha già molta «azione», spesso dello stesso settore).

```
python "${CLAUDE_SKILL_DIR}/assets/capitale-umano.py" --dati capitale-umano.json --composizione composizione.csv --json capitale-umano-out.json
```

Il JSON ha la forma di `assets/esempio-capitale-umano.json` (persona, pensione, posizioni con lo schema di `it-rebalance`); età di pensione e pensione netta possono arrivare con `--from` dai JSON di `proiezione-inps.py` e `netto-pensione.py`. Le cinque diagnosi:

1. **bilancio patrimoniale totale**: finanziario, capitale umano (parte azionaria e obbligazionaria, dal profilo di lavoro) e capitale pensionistico;
2. **esposizione azionaria** del patrimonio finanziario contro quella della ricchezza totale, con la riga di equivalenza facoltativa (`esposizione_totale_desiderata`);
3. **proiezione** fino alla pensione con la fascia Monte Carlo: a parità di allocazione l'esposizione totale sale con l'età;
4. **sovrapposizione settoriale** tra il settore del proprio lavoro e il portafoglio, contro il peso del settore nel mercato mondiale;
5. **sensibilità** ai parametri del profilo.

È una **lente, non un target**: non modifica l'allocazione degli obiettivi né quella che `it-rebalance` mantiene, e la riga di equivalenza è un calcolo, non una raccomandazione. Profili, metodo, esempio svolto e limiti in `references/capitale-umano.md`.

## Strumento operativo: il pianificatore Excel

La skill include un template Excel editabile, `assets/pianificatore-obiettivi.xlsx`, complemento operativo del report. Va offerto quando l'utente vuole uno strumento riutilizzabile in cui inserire i propri obiettivi e vedere il piano aggiornarsi.

Tre fogli:
- **Parametri**: capacità di risparmio mensile, inflazione, **finestra di de-risking** (B7, 7 anni: la usano versamento, Monte Carlo, glide path e allocatore) e la tabella dei **sei profili** (Preservazione, Conservativo, Moderato, Crescita, Crescita massima, **Azionario totale** 100% per obiettivi a orizzonte perpetuo come l'eredità) con rendimento atteso, **volatilità** e **% azionario** — tutti editabili (celle blu).
- **Obiettivi**: tabella multi-obiettivo (10 slot) con menu a tendina per profilo, priorità e **tipo** (terminante/permanente). Per ogni obiettivo l'utente inserisce nome, importo target (€ di oggi), orizzonte, profilo, già accantonato, priorità, tipo; il foglio calcola target nominale, **versamento mensile necessario** (valore futuro di una rendita in due fasi: quota piena, poi gli anni di de-risking al loro rendimento medio, colonne O-P; ramo per rendimento 0, **floored a 0** per obiettivi già sovra-finanziati dal capitale esistente), e la scomposizione azionaria per obiettivo (capitale azionario e versamento azionario). Il **tipo** distingue gli obiettivi che si spendono a scadenza (terminante: casa, università, che de-riskano) da quelli che restano come riserva (permanente: fondo emergenza), ed è usato dal versamento e dal glide path. Tre obiettivi di esempio precompilati coerenti con `references/matematica-accumulo.md`.
- **Riepilogo**: riconciliazione totale versamenti vs capacità (margine/gap, stato), breakdown per priorità (SUMIF), e l'**allocazione complessiva del portafoglio** in vista stock (sul capitale) e flusso (sui versamenti), con le note su come usarla.

Convenzioni industry-standard (blu = input, nero = formule, verde = cross-sheet). 110 formule, zero errori. La matematica è quella della reference, così i numeri dell'Excel e del report coincidono.

Un pianificatore compilato prima della 0.10.0 non ha la finestra in Parametri!B7 né le colonne O-P: la sua colonna I è a quota fissa, più bassa del versamento col glide path (€346 invece di €384 sull'esempio a 20 anni). Gli script lo segnalano e usano 7 anni; per riallineare il foglio basta ricopiare gli obiettivi nel template aggiornato.

### Allocatore di capitale (distribuzione di una somma liquida)

Quando l'utente parte da una **somma liquida da investire** (es. liquida un vecchio gestito e costruisce un portafoglio da zero), il primo passo non è il pianificatore ma lo script `assets/allocatore-capitale.py`: dati la somma e gli obiettivi (li legge dallo stesso Excel), propone **quanto capitale dedicare a ogni secchiello** e ne ricava la **vista aggregata su tre classi — azioni, obbligazioni, liquidità**. È il complemento dell'Excel: l'Excel prende la ripartizione del capitale come *dato* e calcola i versamenti; l'allocatore *propone* la ripartizione e dà l'aggregato a tre classi (l'Excel si ferma ad azionario vs non azionario).

La logica è goals-based per **valore attuale**, con una distinzione che conta: le **riserve permanenti** (fondo emergenza) si finanziano al **valore pieno in liquidità oggi** — le vuoi disponibili adesso, non in crescita verso una scadenza; gli obiettivi **terminanti** ricevono il loro **present value** lungo il glide path (`target_oggi × (1+inflazione)^anni / Π(1 + rendimento_anno)`, col rendimento che scende negli anni della finestra di Parametri!B7; per i profili senza azionario si riduce a `target_oggi × ((1+inflazione)/(1+rendimento))^anni`), il capitale che, seguendo il de-risking, cresce fino al target entro la scadenza. Sull'esempio a 20 anni (Crescita) sono €57.140 invece dei €50.928 a rendimento pieno (`references/allocazione-capitale.md`). La somma si alloca in ordine di **priorità** (essenziale prima), poi per orizzonte; se **avanza**, l'eccedenza è capitale libero, che può essere **diviso tra più obiettivi di lungo termine** (parametro `CAPITALE_LIBERO_SPLIT`: es. integrazione pensione + eredità, ciascuno con peso e profilo propri) — è la parte che pesa di più sull'aggregato, e cambiarne pesi o profili lo sposta più di ogni altra leva; se **non basta**, si finanzia per priorità e il resto va ai versamenti. L'aggregato distingue obbligazioni e liquidità: la parte non azionaria dei secchielli a profilo Preservazione è liquidità, quella degli obiettivi investiti è obbligazionaria. È **onesto sui limiti**: vista "lump sum" (i versamenti, se presenti, riducono il capitale richiesto), e ricorda che liquidare il vecchio gestito realizza plus/minus con la trappola del reddito di capitale (rimanda a `it-tax-optimization` per l'ordine di smontaggio). Esecuzione: `python "${CLAUDE_SKILL_DIR}/assets/allocatore-capitale.py" pianificatore-obiettivi.xlsx [capitale] [--json file]` dalla cartella di lavoro (vedi «Dove lavorare»). L'aggregato che produce è il **target** che alimenta il pianificatore Excel e `it-rebalance`.

### Monte Carlo (probabilità di successo)

Il foglio Excel calcola il versamento **deterministico**, che centra il rendimento medio → tipicamente ~50% di probabilità di raggiungere l'obiettivo. Per la visione probabilistica c'è lo script `assets/montecarlo-obiettivi.py`: legge gli obiettivi dal foglio Excel, simula migliaia di percorsi di accumulo con rendimenti casuali (media = rendimento del profilo, deviazione = volatilità del profilo, ora nella tabella Parametri), e per ciascun obiettivo restituisce la **probabilità di successo**, i percentili del capitale finale (10°/50°/90°) e il versamento che servirebbe per una confidenza-obiettivo (default 85%).

Il messaggio chiave: il versamento "esatto" del foglio è poco più di un testa-o-croce (~50%, meno per orizzonti lunghi ad alta volatilità per via del *volatility drag*: il rendimento del profilo è una media aritmetica, la mediana composta sta circa volatilità²/2 sotto). Gli obiettivi terminanti sono simulati lungo il glide path, col versamento del foglio che già ne tiene conto (`--set GLIDE=False` per la quota fissa fino alla scadenza). Per gli obiettivi essenziali si vuole confidenza alta, quindi un versamento più alto del deterministico. Offrire il Monte Carlo quando l'utente vuole capire il rischio reale del piano, non solo il numero medio.

Esecuzione: `python "${CLAUDE_SKILL_DIR}/assets/montecarlo-obiettivi.py" pianificatore-obiettivi.xlsx [--json file]` dalla cartella di lavoro. **Due modelli dei rendimenti** (parametro `MODELLO`): `"normale"` (Normale i.i.d., default) o `"bootstrap"`, che ricampiona a blocchi da una **serie storica** (`assets/rendimenti-storici.csv`: S&P 500 e T-Bond decennale 1928-2025, fonte Damodaran/NYU Stern, rendimenti nominali in dollari), combinata per il % azionario del profilo, con la media ricentrata sull'ipotesi del profilo (calibra la media, mantiene forma/code/correlazioni della storia). Confrontare i due modelli mostra quanto le conclusioni dipendono dalle ipotesi distributive; spesso su orizzonti lunghi il bootstrap dà una distribuzione *più stretta* (mean reversion e correlazione azionario/obbligazionario storiche, che la Normale i.i.d. ignora). La metodologia, le volatilità per profilo, l'interpretazione della confidenza e i **limiti** sono in `references/monte-carlo.md`. I numeri sono ordini di grandezza per calibrare il rischio, non garanzie.

In modalità bootstrap lo script aggiunge una sezione **rischio sistemico**: gli obiettivi non sono indipendenti, perché condividono lo stesso mercato (un crollo li colpisce insieme). Una **simulazione congiunta** estrae un unico percorso di mercato per simulazione e lo applica a tutti gli obiettivi, riportando la probabilità che **tutti gli essenziali falliscano nello stesso scenario** — confrontata con il prodotto ingenuo delle probabilità indipendenti, che la **sottostima**. È una delle due correzioni di onestà del Monte Carlo (l'altra è la non-USA-centricità: vedi `references/mercati-e-correlazione.md`).

Per ogni obiettivo lo script mostra anche la **seconda strada**: quando il versamento per la confidenza supera la capacità e non si può versare di più, resta la leva di **alzare il rischio** (la quota azionaria) a parità di versamento. Lo strumento fa lo sweep dell'allocazione, trova quella che massimizza la probabilità, e — punto chiave di onestà — mostra la **distribuzione intera**, non solo la probabilità, perché più rischio alza la mediana ma allarga la coda sinistra (il 10° percentile può peggiorare). Segnala quando la leva è **inadatta** (obiettivo essenziale o importante, oppure entro la finestra di de-risking, Parametri!B7, 7 anni nel pianificatore d'esempio, dove il glide path abbassa la quota azionaria), **controproducente** (già in linea) o un'**opzione reale** (sotto-finanziato, lungo orizzonte, discrezionale), e ne quantifica il costo sul caso brutto. Su un obiettivo terminante la leva alza la quota **di partenza** e il glide path la riporta giù negli ultimi anni: accanto all'OPZIONE lo strumento mostra la probabilità **sul percorso glide** (il piano che `it-rebalance` esegue) e quella **a quota fissa** fino alla scadenza, più alta perché ignora il de-risking. La relazione rischio-probabilità non è lineare: oltre una certa quota il volatility drag appiattisce la curva. Trattare l'allocazione come una leva con un costo esplicito, e non come un parametro fisso, è una scelta di metodo; dettagli in `references/monte-carlo.md`.

### Glide path (calendario di de-risking)

L'allocazione complessiva non è statica: man mano che gli obiettivi si avvicinano, i loro secchielli vanno de-riskati. Lo script `assets/glidepath-obiettivi.py` genera il **calendario di de-risking** anno per anno: per ciascun obiettivo, la quota azionaria target a ogni anno (tiene la quota piena finché manca più della finestra di de-risking, Parametri!B7, 7 anni nell'esempio, poi scende linearmente fino all'atterraggio, default 0%, entro la scadenza), e l'aggregato di portafoglio pesato per il capitale proiettato.

È il **programma di spostamento dei target che `it-rebalance` esegue**: ogni anno il target di un secchiello in de-risking si abbassa, e it-rebalance vende azionario per comprare obbligazionario/liquidità. Gli obiettivi marcati **permanenti** (colonna Tipo: il fondo emergenza) non de-riskano e restano in portafoglio come riserva, smussando l'aggregato invece di farlo saltare quando un obiettivo si conclude; i **terminanti** de-riskano ed escono a scadenza (si spendono). ⚠️ Ogni vendita è un evento fiscale: il de-risking graduale distribuisce gli eventi nel tempo, e i nuovi versamenti verso la componente in crescita riducono la necessità di vendere. Offrire il glide path quando l'utente ha obiettivi a data fissa (casa, università) e vuole sapere come ridurre il rischio avvicinandosi.

La proiezione del capitale usa il rendimento atteso anno per anno lungo il glide path e i versamenti del foglio, che lo script riepiloga in fondo. Esecuzione: `python "${CLAUDE_SKILL_DIR}/assets/glidepath-obiettivi.py" pianificatore-obiettivi.xlsx [--json file]` dalla cartella di lavoro. La formula, i parametri editabili (finestra, atterraggio, **curvatura** della rampa: lineare di default, oppure azionario più alto a lungo poi discesa ripida), la sottigliezza obiettivi terminanti vs permanenti, il coordinamento fiscale e i limiti sono in `references/glide-path.md`.

### Ottimizzatore asset location (beneficio fiscale netto)

La reference `asset-location.md` dà il framework qualitativo (quale contenitore per quale obiettivo); lo script `assets/asset-location-optimizer.py` ne dà i **numeri**. Calcola il valore finale **al netto di tasse E costi** in ciascun contenitore, per le due decisioni dove il beneficio è quantificabile:

Lo script parte dal rendimento **lordo** di mercato, perché costi e imposte li toglie contenitore per contenitore: i profili sono netti, quindi lo ricava con la conversione inversa, lordo = netto / (1 − 26%) + TER + bollo (dal 5,5% della Crescita: 7,8%), oppure lo riceve esplicito con `--set RENDIMENTO_LORDO=...`. Trattare come lordo il rendimento netto, come faceva prima, ribaltava il verdetto sul PIR. Attenzione al verso: la conversione tratta l'imposta come annua e dà il lordo più alto compatibile col profilo, e un lordo più alto aumenta il valore delle esenzioni, quindi **favorisce i contenitori esenti**. Con l'imposta pagata alla vendita (ETF ad accumulazione) il lordo equivalente a 15 anni è il 7,15% e il TER di pareggio del PIR scende all'1,45%: lo script stampa anche questa variante, lo scenario prudente. I numeri sotto sono l'output sui default:

- **Fondo pensione vs dossier** (per la pensione): la deduzione IRPEF è il driver (€5.300/anno al 33% = €52.470 di risparmio in 30 anni, se il datore non versa nulla: il plafond di €5.300 è condiviso con il contributo del datore e con quello dovuto del lavoratore, quindi con un datore lo spazio dei volontari è €5.300 − datore − dovuto, vedi il foglio Complementare di `it-pianificazione`; reinvestito nel dossier vale €145.836), ma i rendimenti tassati al 20% ogni anno e l'ISC più alto la erodono; il vantaggio netto resta positivo e ampio: €96.466, +22% vs dossier.
- **PIR vs dossier** (per obiettivi a lungo termine): l'esenzione (0% sulle plus) contro il TER più alto del PIR. Il verdetto dipende da rendimento, orizzonte e TER: sull'esempio di €10.000 a 15 anni il PIR con TER 1,3% chiude a +€828 sul dossier, con un TER di pareggio dell'1,54%, appena sopra i TER tipici 1,2-1,35%. Con rendimenti più bassi o TER più alti il vantaggio diventa **negativo**. Lo script stampa il **TER di pareggio**: sotto quel costo il PIR conviene, sopra no.

È la misura quantitativa dello scetticismo della reference: il margine fiscale del PIR è sottile e i costi possono mangiarlo. ⚠️ La comparazione PIR/dossier assume lo *stesso* rendimento e quindi NON cattura il costo di concentrazione del PIR (PMI italiane) — un rischio in più, non meno. Parametri (aliquota marginale, TER, ISC, anni, contributo) sovrascrivibili con `--set NOME=VALORE`, elencati da `--help`. Esecuzione: `python "${CLAUDE_SKILL_DIR}/assets/asset-location-optimizer.py" pianificatore-obiettivi.xlsx` dalla cartella di lavoro. Offrirlo quando l'utente vuole sapere *quanto* vale davvero un contenitore agevolato, non solo se usarlo.

## La fase di decumulo (prelievo)

Tutto quanto sopra riguarda l'**accumulo**. Quando un obiettivo si trasforma in fonte di prelievo (la pensione integrativa una volta in pensione, o una riserva permanente da cui si attinge), il problema cambia natura: **il decumulo non è l'accumulo al contrario**. Conta l'**ordine** dei rendimenti, non solo la media — una brutta sequenza nei primi anni costringe a vendere a prezzi bassi e può esaurire il capitale anche con un rendimento medio buono. È il **rischio di sequenza dei rendimenti**, il rischio dominante del prelievo.

Lo script `assets/decumulo-obiettivi.py` lo rende quantitativo: calcola la **probabilità che il capitale duri** l'orizzonte (bootstrap a blocchi dalla serie storica, che preserva la sequenza; i rendimenti nominali in dollari sono portati in termini reali anno per anno con l'inflazione USA storica, così gli anni '70 restano nella serie), una **tabella di sensibilità** su più tassi di prelievo, la **dimostrazione del rischio di sequenza** (lo stesso insieme di rendimenti nei due ordini opposti — stessa media, esiti opposti: uno esaurisce, l'altro cresce), il confronto **con/senza buffer di liquidità**, e il confronto **lente USA vs scenario globale** (parametro `DERATING_AZIONARIO`, vedi sotto). Tre avvertenze da comunicare sempre: (1) la celebre **regola del 4%** nasce su dati USA (mercato storicamente eccezionale) e orizzonte 30 anni → per un investitore europeo con orizzonte lungo va **scontata** (3-3,5% più difendibile); (2) il **buffer di liquidità non è un free lunch** — sui dati storici può addirittura abbassare il tasso di successo (la liquidità rende ~0), e il suo valore è soprattutto comportamentale e contro i bear prolungati; (3) le mitigazioni più efficaci sono i **prelievi dinamici** (guardrail) e la **flessibilità di spesa**. Tutto in `references/decumulo.md`. Il **de-rating** dell'azionario (trasformare la serie USA in scenario globale, −1,5% sull'azionario reale per riflettere lo scarto USA-vs-mondo del Global Investment Returns Yearbook) è in `references/mercati-e-correlazione.md`. La dimensione **fiscale** del prelievo (quali posizioni e contenitori liquidare per minimizzare l'imposta, e l'aliquota agevolata 9-15% del fondo pensione in erogazione) è in `it-rebalance/references/sequenza-liquidazione.md`.

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

Per ciascun obiettivo: importo target (nominale, con inflazione), rendimento atteso del profilo, versamento mensile necessario, e cosa serve già avere accantonato. Dichiarare le convenzioni: rendimento nominale, netto di costi e imposte, media aritmetica annua; per i terminanti versamento col glide path (e quanto costa rispetto alla quota fissa).

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
- `assets/pianificatore-obiettivi.xlsx` — template Excel editabile (3 fogli: Parametri, Obiettivi, Riepilogo), tabella multi-obiettivo con versamento mensile, riconciliazione vs capacità, scomposizione azionaria per obiettivo e **allocazione complessiva del portafoglio** (stock + flusso), glide path nel versamento (finestra in Parametri!B7), 110 formule
- `assets/allocatore-capitale.py` — allocatore di una somma liquida tra i secchielli per valore attuale (riserve permanenti al valore pieno in liquidità, obiettivi terminanti al present value), con la **vista aggregata su tre classi** (azioni/obbligazioni/liquidità) che fa da target per l'Excel e it-rebalance; onesto sul capitale libero e sulla fiscalità della liquidazione (richiede openpyxl)
- `references/monte-carlo.md` — metodologia della simulazione Monte Carlo: perché il deterministico dà ~50%, i due modelli (Normale i.i.d. e bootstrap storico), le volatilità per profilo, come calibrare la confidenza, il rischio di sequenza, le **tre strade per colmare un gap** (versare di più, alzare il rischio come leva a doppio taglio, aggiustare l'obiettivo), e i limiti del modello
- `references/glide-path.md` — metodologia del glide path: la formula (finestra + atterraggio + curvatura), le viste per-obiettivo e aggregata, la sottigliezza terminanti/permanenti, il coordinamento fiscale con it-rebalance, i limiti
- `references/asset-location.md` — (uso personale) in quale contenitore fiscale tenere ciascun obiettivo: dossier amministrato, fondo pensione, PIR, polizze, conto deposito; il framework per obiettivo, le tensioni (vincolo pensione, concentrazione PIR, costi polizze), l'interazione con le altre skill
- `assets/glidepath-obiettivi.py` — script che genera il calendario di de-risking anno per anno (per obiettivo e aggregato), il programma di target che alimenta it-rebalance (richiede openpyxl)
- `assets/montecarlo-obiettivi.py` — script che legge gli obiettivi dall'Excel e calcola la probabilità di successo, i percentili del capitale finale e il versamento per una confidenza-obiettivo; due modelli (Normale i.i.d. o bootstrap storico) (richiede numpy, openpyxl)
- `assets/rendimenti-storici.csv` — serie annuale azionario (S&P 500) e obbligazionario (T-Bond 10 anni) 1928-2025, rendimenti nominali in dollari (fonte Damodaran/NYU Stern), con l'inflazione USA di ogni anno (CPI-U dicembre su dicembre, BLS) per il decumulo in termini reali; sostituibile con una propria serie
- `references/decumulo.md` — la fase di prelievo: tasso sostenibile (regola del 4% e perché va scontata per l'Europa), rischio di sequenza dei rendimenti, mitigazioni (buffer, guardrail, flessibilità di spesa, bond tent)
- `assets/asset-location-optimizer.py` — in quale contenitore conviene tenere un obiettivo, al netto di tasse e costi: fondo pensione contro dossier (deduzione, tassa finale, vincolo fino alla pensione) e PIR contro dossier per gli obiettivi lunghi con capitale già accantonato; parametri con `--set`, vedi `references/asset-location.md`
- `assets/decumulo-obiettivi.py` — simulazione del decumulo: probabilità di successo, sensibilità sul tasso di prelievo, dimostrazione del rischio di sequenza, confronto con/senza buffer, lente USA vs scenario globale (de-rating) (richiede numpy; usa rendimenti-storici.csv)
- `references/mercati-e-correlazione.md` — le due correzioni di onestà al Monte Carlo: la **non-USA-centricità** (l'azionario mondiale rende ~5,2% reale vs gli USA eccezionali, fonte DMS; de-rating e calibrazione globale) e la **correlazione sistemica** tra obiettivi (un crollo li colpisce insieme; l'indipendenza sottostima il rischio che saltino tutti nello stesso scenario)
- `references/capitale-umano.md` — il capitale umano nella ricchezza totale: modello (Ibbotson, Milevsky, Chen e Zhu 2007), quota azionaria per profilo di lavoro, NASpI, le cinque diagnosi, esempio svolto, limiti e bibliografia verificata
- `assets/capitale-umano.py` — la lente del capitale umano: bilancio patrimoniale totale, esposizione azionaria del portafoglio contro quella della ricchezza totale (con la riga di equivalenza), proiezione con fascia Monte Carlo, sovrapposizione settoriale, sensibilità; non modifica i target (richiede numpy)
- `assets/profili-capitale-umano.csv` — i sei profili di lavoro (quota azionaria del capitale umano, premio ν, correlazione e volatilità del reddito, probabilità di perdere il lavoro, NASpI), con la fonte e la natura di ogni valore
- `assets/esempio-capitale-umano.json` — dati d'esempio di `capitale-umano.py` (sviluppatore di 35 anni nel privato), da copiare nella cartella di lavoro e compilare
- `assets/esempio-composizione.csv` — composizione settoriale d'esempio (pesi illustrativi) per `capitale-umano.py --composizione`
- **Vedi anche** `it-rebalance/SKILL.md` (mantenimento delle allocazioni), `it-tax-optimization/SKILL.md` (fiscalità degli strumenti), `it-pianificazione/SKILL.md` (obiettivo pensione)
