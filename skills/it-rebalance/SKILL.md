---
name: it-rebalance
description: Ribilanciamento di portafoglio tax-aware sotto la fiscalità italiana (regime amministrato). Usa questa skill ogni volta che l'utente parla di ribilanciamento, rebalancing, riequilibrio del portafoglio, allocazione target vs effettiva, drift dell'asset allocation, portafoglio sbilanciato, "le azioni sono cresciute troppo", riportare i pesi all'allocazione obiettivo, ribilanciare con/senza vendere, ribilanciamento tramite nuovi versamenti (cashflow), ribilanciamento di fine anno coordinato con le minusvalenze. Trigger anche quando l'utente ha un portafoglio multi-asset (azioni/obbligazioni/ETF) e chiede come ririportarlo ai pesi voluti minimizzando l'impatto fiscale. Coordina con `it-tax-optimization` perché in Italia ogni vendita per ribilanciare è un evento fiscale (realizzo plus/minus sul costo medio ponderato, interazione con lo zainetto). NON è consulenza di investimento: la skill è fiscale e operativa, non raccomanda QUALE asset allocation scegliere. NON copre fondi pensione (vincolati) né dipendenti pubblici.
---

# it-rebalance

Skill per il ribilanciamento di un portafoglio di investimento **tax-aware** sotto il regime fiscale italiano amministrato. Il punto centrale, e la differenza radicale rispetto al modello USA, è che **in Italia ogni vendita per ribilanciare genera un evento fiscale immediato**: non esiste il "tax-deferred rebalancing" dentro un conto pensione come negli USA (dove si ribilancia un 401k senza conseguenze fiscali). Ogni spostamento di peso che richiede una vendita realizza plusvalenze o minusvalenze tassabili.

## Scope esplicito

**Cosa fa:**
1. **Misura il drift** — confronta allocazione effettiva vs target, identifica gli scostamenti
2. **Genera un piano di ribilanciamento tax-aware** — privilegia le leve a costo fiscale zero o negativo
3. **Coordina con lo zainetto fiscale** — sfrutta le vendite di ribilanciamento per consumare minus pregresse in scadenza (sinergia con `it-tax-optimization`)
4. **Quantifica l'impatto fiscale** di ogni mossa, per scegliere la sequenza meno costosa

**Cosa NON fa:**
- ❌ Non raccomanda *quale* asset allocation adottare (60/40, 70/30, all-equity, ecc.). La skill prende l'allocazione target come **input dell'utente**, non la sceglie. Quella è una decisione di investimento personale.
- ❌ Non dà consigli su quali specifici ETF/azioni comprare per ragioni di rendimento/rischio.
- ❌ Non sostituisce un consulente finanziario abilitato per la definizione della strategia.
- ❌ Non copre il ribilanciamento dentro fondi pensione (i comparti si cambiano con regole proprie, vedi `it-pianificazione`), né dipendenti pubblici.
- ❌ Non opera in regime dichiarativo (assume regime amministrato con sostituto d'imposta).

## Il principio cardine: la gerarchia delle leve

Il ribilanciamento tax-aware italiano segue una **gerarchia di leve ordinata per costo fiscale crescente**. La skill DEVE sempre proporre le leve in quest'ordine, esaurendo le più economiche prima di passare alle più care:

```
LEVA 1 (costo fiscale ZERO): Ribilanciamento via nuovi versamenti
  → Indirizza i nuovi contributi (PAC, liquidità) verso le asset class sottopesate
  → Nessuna vendita = nessun realizzo = nessuna tassa
  → È quasi sempre la leva preferibile per chi è in fase di accumulo

LEVA 2 (costo fiscale ZERO): Ribilanciamento via dividendi/cedole
  → Reinveste i flussi in entrata (dividendi, cedole) nelle asset class sottopesate
  → invece di reinvestirli pro-quota
  → Nessuna vendita aggiuntiva

LEVA 3 (costo fiscale NEGATIVO o nullo): Vendita di posizioni in MINUS
  → Se ci sono posizioni sovrappesate che sono anche in perdita latente,
    venderle ribilancia E crea/usa zainetto fiscale
  → Coordinare con it-tax-optimization: la minus realizzata compensa plus
    o resta nello zainetto 4 anni

LEVA 4 (costo fiscale POSITIVO ma ottimizzabile): Vendita di posizioni in PLUS
  → Ultima risorsa. Realizza plusvalenza tassabile.
  → Ottimizzazione: vendere posizioni in plus dove si può compensare con
    minus pregresse in scadenza (sinergia zainetto)
  → Preferire vendite di strumenti "reddito diverso" (compensabili) rispetto a
    ETF UCITS armonizzati (plus = reddito capitale, NON compensabile)
```

**Insight chiave**: un investitore in fase di accumulo con versamenti regolari può spesso ribilanciare **interamente con la Leva 1**, a costo fiscale zero, semplicemente dirigendo i nuovi soldi dove servono. La vendita (Leve 3-4) serve solo quando il drift è troppo grande per essere corretto dai soli flussi, o in fase di decumulo.

## Regole fiscali che condizionano il ribilanciamento

### Ogni vendita è un evento fiscale (no tax-deferred rebalancing)

A differenza degli USA, dove si ribilancia dentro un IRA/401k senza conseguenze, in Italia il dossier titoli ordinario tassa ogni realizzo. Vendere €10.000 di un ETF azionario cresciuto del 40% realizza ~€2.857 di plusvalenza → tassa 26% = ~€743. Questo costo va **sempre** quantificato prima di proporre una vendita.

### La plus realizzata si calcola sul costo medio ponderato

In regime amministrato la plus o minus di una vendita si calcola sul **costo medio ponderato** del titolo in quel rapporto (art. 6 c. 4 D.Lgs. 461/97 → art. 306 c. 5 TU 2027): (prezzo − PMC) × quantità venduta. Il lotto non si sceglie e l'ordine degli acquisti non conta: una vendita parziale realizza una plus proporzionale e lascia invariato il PMC del residuo. Per ridurre la plus realizzata si sceglie quale **posizione** vendere (quella con la plus latente più bassa in proporzione al valore), non quale lotto. Il LIFO dell'art. 67 c. 1-bis TUIR vale solo per i conti in dichiarativo, fuori dallo scope di questa skill. *(Costo medio ponderato in amministrato — Verificato: 2026-10.)*

### L'asimmetria redditi diversi vs capitale (vedi it-tax-optimization)

Quando si vende per ribilanciare:
- Vendita di **azioni dirette, certificates, ETC** in plus → reddito diverso → la plus **può** essere compensata con minus pregresse
- Vendita di **ETF UCITS armonizzati** in plus → reddito di capitale → la plus **NON può** essere compensata con minus pregresse
- Vendita di **ETF o fondi non armonizzati** (non UCITS) in plus → reddito di capitale, mai compensabile; se l'OICR non è UE/SEE con gestore vigilato concorre all'IRPEF progressiva → sono le ultime posizioni da vendere in plus

⚠️ **Conseguenza per il ribilanciamento**: se devi vendere asset azionario in plus per ribilanciare, e hai zainetto disponibile, è fiscalmente più efficiente vendere **azioni dirette** (compensabili) piuttosto che ETF, armonizzati o no (non compensabili). A parità di drift da correggere, la scelta dello strumento da vendere cambia il conto fiscale.

### Costi di transazione e Tobin tax (2026)

Ogni vendita/acquisto di ribilanciamento comporta:
- **Commissioni di negoziazione** (variabili per broker)
- **Tobin tax** a carico dell'acquirente di **azioni di società italiane**: **0,4%** fuori mercato, **0,2%** su mercati regolamentati e MTF (aliquote raddoppiate dal 1/1/2026, L. 199/2025); escluse le azioni quotate di società con capitalizzazione media **< €500M**. **ETF, fondi (OICR, comprese le SICAV) e obbligazioni sono esclusi** (DM 21/02/2013, artt. 2 e 15) → per portafogli in ETF la Tobin tax sul ribilanciamento è zero.
- **Imposta di bollo**: 0,2% annuo sul controvalore al 31/12, indipendente dal ribilanciamento (ma vendite di fine anno riducono marginalmente la base)

*Imposta sulle transazioni finanziarie 2026 (art. 1 c. 491-494 L. 228/2012, mod. L. 199/2025 c. 29-31; esclusione di OICR e obbligazioni, DM 21/02/2013) — Verificato: 2026-10. Dal 2027 la disciplina passa agli artt. 42 ss. del D.Lgs. 174/2024.*

Per un portafoglio tipico in ETF UCITS, il costo di transazione del ribilanciamento è essenzialmente solo le commissioni del broker.

## Workflow operativo

### Step 1: Ingestion

Raccogliere:

**Portafoglio attuale** (CSV o testo strutturato), per ogni posizione:
- `broker` — intermediario (lo zainetto è per-broker)
- `isin` / `ticker`
- `descrizione` — es. "iShares Core MSCI World UCITS ETF"
- `asset_class` — es. azionario_globale, azionario_EU, obbligazionario_governativo, obbligazionario_corporate, monetario, oro/commodity, ecc.
- `tipo_fiscale` — `reddito_diverso` (azioni dirette, certificates, ETC) o `reddito_capitale` (ETF e fondi, UCITS e non armonizzati). Se non noto, dedurre da descrizione (ETF o fondo → capitale)
- `quantita`
- `pmc` (prezzo medio di carico), che in amministrato è la base fiscale delle vendite
- `prezzo_corrente` o `controvalore_attuale`

**Allocazione target** (input utente, NON suggerita dalla skill):
- Peso obiettivo per asset class, es. "60% azionario globale, 30% obbligazionario, 10% monetario"

**Parametri di ribilanciamento:**
- `banda` — soglia oltre cui si ribilancia. Default **dinamico** (regola 5/25 + modulazione per volatilità + allargamento cost-aware, vedi `references/bande-dinamiche.md`) invece di una banda fissa: la soglia è il minore tra 5 punti assoluti e 25% del peso target, scalata (in modo modesto e clampato) per la volatilità della classe, e allargata quando correggere richiede di pagare imposta. L'utente può forzare una banda fissa o spegnere la modulazione di volatilità se preferisce.
- `nuovi_versamenti_disponibili` — liquidità in entrata da poter usare per Leva 1 (€, eventualmente ricorrente)
- `flussi_attesi` — dividendi/cedole attesi nei prossimi mesi (per Leva 2)
- `fase` — accumulo (versamenti netti positivi) o decumulo (prelievi netti)

**Zainetto fiscale** (per coordinamento con it-tax-optimization):
- Minus pregresse disponibili per broker, con anno di formazione (per la scadenza 4 anni)

Se mancano dati critici (allocazione target, PMC, tipo fiscale degli strumenti) → CHIEDERE, non inventare.

### Step 2: Misura il drift (con bande dinamiche)

```
per ogni asset_class:
    peso_effettivo = controvalore_classe / controvalore_totale
    peso_target = input_utente[asset_class]
    drift_assoluto = peso_effettivo - peso_target

    # banda dinamica (regola 5/25): soglia = il minore tra assoluto e relativo
    banda_stretta = min(0,05; 0,25 × peso_target)
    banda_larga   = banda_stretta × 2   # usata quando correggere costa imposta netta

    fuori_banda = |drift_assoluto| > banda_stretta
```

Output: tabella asset class con peso effettivo, target, drift, banda stretta/larga, flag fuori/dentro banda. Identificare quali classi sono **sovrappesate** (da ridurre) e **sottopesate** (da aumentare).

La banda **5/25** corregge il difetto della banda fissa: per le classi a peso piccolo (es. monetario al 10%) la soglia effettiva scende (2,5%), perché un drift assoluto modesto è uno scostamento relativo grande; per le classi grandi domina il 5% assoluto. Vedi `references/bande-dinamiche.md`.

L'**allargamento cost-aware** entra nello Step 3: se correggere un sovrappeso si fa a costo netto zero (flussi, vendita di minus, o plus interamente compensata dallo zainetto), si agisce sulla banda **stretta**; se richiede di realizzare plus che pagano imposta, si agisce solo oltre la banda **larga**. In breve: non si paga imposta per correggere un drift troppo piccolo per contare.

⚠️ Se nessuna classe è fuori banda → **raccomandare di NON ribilanciare**. Il ribilanciamento ha senso solo oltre la soglia; ribilanciare per piccoli scostamenti genera costi (fiscali e commissioni) senza beneficio reale. Bias verso il non operare, come in it-tax-optimization. Corollario (Kitces): quando si ribilancia, riportare **a target**, non solo al bordo della banda — così si massimizza il tempo fino al prossimo intervento.

### Step 3: Costruisci il piano tax-aware (gerarchia delle leve)

Applicare le leve in ordine, accumulando la correzione:

```
gap_da_correggere = {asset_class sottopesate: importo da aggiungere}
                    {asset_class sovrappesate: importo da ridurre}

# LEVA 1: nuovi versamenti
se nuovi_versamenti_disponibili > 0:
    alloca i nuovi versamenti alle classi sottopesate (in ordine di drift)
    aggiorna gap_da_correggere
    → costo fiscale: ZERO

# LEVA 2: flussi in entrata
se flussi_attesi > 0:
    redirigi dividendi/cedole verso classi sottopesate
    aggiorna gap_da_correggere
    → costo fiscale: ZERO (la tassazione sul flusso è dovuta comunque)

# Se gap residuo dopo Leve 1-2:
# LEVA 3: vendita posizioni in MINUS tra le sovrappesate
per posizione in (sovrappesate AND plus_latente < 0):
    vendere (parzialmente o totalmente) per correggere il sovrappeso
    la minus realizzata → coordinare con it-tax-optimization
    → costo fiscale: ZERO o NEGATIVO (genera zainetto / compensa plus)

# LEVA 4 (ultima risorsa): vendita posizioni in PLUS
per posizione in (sovrappesate AND plus_latente > 0):
    # Ottimizzazione DOPPIA: broker × tipo fiscale (vedi ribilanciamento-multibroker.md)
    # La compensazione NON attraversa i broker: lo zainetto del broker A azzera
    # solo plus realizzate al broker A, e solo su strumenti reddito_diverso.
    priorità 1: vendere reddito_diverso PRESSO un broker che ha zainetto capiente
                (la plus viene assorbita → costo netto ≈ zero)
    priorità 2: vendere posizioni con plus latente minore in proporzione al valore (sul PMC)
    priorità 3: per ultime le posizioni reddito_capitale (ETF UCITS: plus MAI
                compensabile) o presso broker senza zainetto (plus tassata piena)
    # gate cost-aware (banda dinamica): una vendita che lascia imposta NETTA
    # si esegue solo se |drift| della classe supera la banda larga; altrimenti
    # si attende (correggere costerebbe imposta sproporzionata al beneficio)
    calcola tassa = (plus_realizzata − compensazione_zainetto_stesso_broker) × aliquota
    → costo fiscale: POSITIVO, da minimizzare con la scelta broker × tipo
```

Per il caso multi-broker, lo script `assets/ribilanciamento-multibroker.py` esegue questa ottimizzazione automaticamente: dato il portafoglio (con broker, tipo fiscale e plus/minus per posizione), lo zainetto per broker e il target, produce il piano di vendite ottimizzato, il costo fiscale e lo zainetto residuo. È il modo più affidabile di gestire la Leva 4 quando i conti sono più di uno.

Lo stesso script **genera anche gli ordini da eseguire**, un **CSV per broker** (parametro `GENERA_CSV`). La parte interessante è l'**instradamento della cassa**: gli acquisti delle classi sottopesate vengono finanziati dalla liquidità presente su ciascun broker — le vendite realizzate lì più gli eventuali versamenti che vi atterrano — così ogni broker resta a saldo e i suoi ordini sono eseguibili senza spostare cassa tra intermediari (operazione che richiederebbe giorni). Ogni riga porta con sé l'annotazione fiscale (plus/minus realizzata, imposta, compensazione da zainetto) e una colonna `strumento_ISIN` da compilare a mano: il piano ragiona per classe, è l'utente a scegliere lo strumento specifico. ⚠️ I broker italiani non hanno un formato standard di import ordini, quindi i CSV sono una **checklist di esecuzione** e una traccia di audit, non file caricabili in un click.

### Step 4: Quantifica e presenta

Per ogni mossa proposta, calcolare:
- Importo da spostare
- Plus/minus realizzata (se vendita)
- Compensazione con zainetto (se applicabile)
- Tassa netta dovuta
- Commissioni stimate + Tobin tax (se azioni IT)
- Allocazione risultante post-mossa

Mostrare il **costo fiscale totale** del piano e l'allocazione finale rispetto al target.

## Formato output

Report markdown in sezioni:

### 1. Drift attuale

| Asset class | Effettivo | Target | Drift | Stato |
|---|---|---|---|---|
| Azionario globale | 68% | 60% | +8% | 🔴 sovrappeso |
| Obbligazionario | 24% | 30% | -6% | 🔴 sottopeso |
| Monetario | 8% | 10% | -2% | 🟢 in banda |

### 2. Piano di ribilanciamento (per leva)

Descrizione delle mosse, leva per leva, con costo fiscale di ciascuna. Esplicitare quali gap sono coperti a costo zero (Leve 1-2) e quali richiedono realizzo (Leve 3-4).

### 3. Impatto fiscale totale

- Plusvalenze realizzate totali
- Minusvalenze realizzate / zainetto consumato
- Tassa netta dovuta
- Commissioni + Tobin tax stimate
- **Costo totale del ribilanciamento**

### 4. Allocazione risultante

Tabella allocazione post-ribilanciamento vs target, per verificare che il piano riporti effettivamente entro banda.

### 5. Raccomandazioni e alternative

- Se il drift è correggibile con sole Leve 1-2 → raccomandare quella via (costo zero)
- Se serve vendere → indicare la sequenza fiscalmente ottimale
- Se il costo fiscale supera il beneficio del ribilanciamento → valutare ribilanciamento parziale (solo riportare in banda, non esattamente a target) o attesa
- Coordinamento di fine anno: se ci sono minus in scadenza (31/12 del 4° anno), il ribilanciamento può essere il momento per realizzare plus compensabili

### Disclaimer (obbligatorio in fondo)

> **Disclaimer**: questo report ha finalità informative di pianificazione personale. Non costituisce consulenza di investimento, finanziaria o fiscale professionale. La skill NON raccomanda quale asset allocation adottare: l'allocazione target è fornita dall'utente. Le strategie sono di efficienza fiscale e operativa del ribilanciamento, non di selezione titoli. I calcoli si basano sui dati forniti e sulle regole del regime amministrato vigenti. Verificare sempre saldi, prezzo medio di carico e zainetto fiscale sul portale del proprio intermediario prima di operare. Per la definizione della strategia di portafoglio e per casi specifici consultare un consulente finanziario abilitato.

## Anti-pattern (NON FARE MAI)

- ❌ Raccomandare quale asset allocation scegliere. La skill prende il target come input; non è un robo-advisor.
- ❌ Proporre vendite (Leve 3-4) prima di aver esaurito nuovi versamenti e flussi (Leve 1-2). La vendita è l'ultima risorsa, non la prima.
- ❌ Trattare il ribilanciamento come fiscalmente neutro: ogni vendita in Italia è un evento fiscale. Mai dimenticarlo (errore tipico di chi ragiona col modello USA tax-deferred).
- ❌ Simulare le vendite lotto per lotto: in amministrato la plus si calcola sul costo medio ponderato e il lotto non si sceglie (il LIFO vale solo in dichiarativo).
- ❌ Vendere ETF UCITS armonizzati in plus quando si potrebbero vendere azioni dirette compensabili con zainetto: si butta via la possibilità di compensazione.
- ❌ Trattare un ETF non armonizzato (es. domiciliato USA) come compensabile: la plus è reddito di capitale, spesso a IRPEF progressiva, e lo zainetto resta intatto.
- ❌ Ribilanciare per scostamenti dentro la banda di tolleranza: genera costi senza beneficio.
- ❌ Sovrastimare la Tobin tax sul ribilanciamento: per portafogli in ETF è zero (esenti).
- ❌ Suggerire ribilanciamenti cross-broker assumendo compensazione automatica dello zainetto: lo zainetto è per-intermediario. La skill ora **ottimizza intorno a questo vincolo** scegliendo dove realizzare le plus (broker × tipo fiscale, vedi `ribilanciamento-multibroker.md`), ma non bisogna mai dare per scontata una compensazione che attraversa i broker.
- ❌ Ribilanciare "a target esatto" quando "riportare in banda" costa meno: l'over-precision genera vendite extra non necessarie.
- ❌ Dimenticare di coordinare con minus in scadenza: il ribilanciamento di fine anno è l'occasione per usare zainetto che altrimenti evapora.

## Sinergia con le altre skill del plugin

`it-rebalance` è il tassello che **connette le due skill esistenti** in un workflow operativo:

- **Con `it-tax-optimization`**: il ribilanciamento genera eventi fiscali (realizzo plus/minus). La Leva 3 (vendita posizioni in minus) crea zainetto; la Leva 4 (vendita posizioni in plus) può consumare zainetto in scadenza. Quando l'utente ribilancia a fine anno, le due skill vanno usate insieme: prima `it-tax-optimization` identifica lo zainetto disponibile e le minus in scadenza, poi `it-rebalance` sequenzia le vendite per sfruttare la compensazione. Vedi `references/coordinamento-zainetto.md`.

- **Con `it-pianificazione`**: il ribilanciamento del dossier titoli ordinario è distinto dal ribilanciamento del comparto del fondo pensione (che ha regole proprie, no eventi fiscali sul cambio comparto). Se l'utente ha entrambi, la skill chiarisce che sono due processi separati. Il fondo pensione si ribilancia "gratis" (switch comparto senza tassazione), il dossier no.

## Riferimenti

- `references/gerarchia-leve.md` — approfondimento sulle 4 leve con esempi numerici completi (accumulo vs decumulo)
- `references/coordinamento-zainetto.md` — protocollo di coordinamento con it-tax-optimization per il ribilanciamento di fine anno
- `references/ribilanciamento-multibroker.md` — l'ottimizzazione globale dello zainetto quando il portafoglio è su più broker: il vincolo che la compensazione non attraversa i broker, e la doppia ottimizzazione broker × tipo fiscale per scegliere DOVE realizzare le plus
- `references/bande-dinamiche.md` — le bande di tolleranza dinamiche (regola 5/25 + modulazione per volatilità + allargamento cost-aware): quando ribilanciare, perché scalare la soglia con la volatilità della classe (con la tensione teorica trattata onestamente), e perché non pagare imposta per correggere un drift troppo piccolo
- `references/sequenza-liquidazione.md` — la sequenza di liquidazione fiscalmente efficiente in **decumulo**: da dove prelevare per pagare meno imposta (liquidità → flussi → vendite tax-aware → fondo pensione agevolato 9-15%), e come il prelievo annuo diventa anche l'occasione per ribilanciare
- `assets/ribilanciamento-multibroker.py` — strumento che esegue l'ottimizzazione multi-broker e le bande dinamiche su un portafoglio reale, e **genera gli ordini come CSV per broker** con instradamento della cassa (parametri editabili in testa; output: drift, piano di vendite ottimizzato per broker/tipo, costo fiscale, zainetto residuo, allocazione risultante, e un CSV di ordini eseguibili per ciascun broker)
- **Vedi anche** `it-tax-optimization/SKILL.md` per le regole di compensazione minus/plus e `it-tax-optimization/references/multi-intermediario.md` per la frammentazione su più broker, e `it-pianificazione/references/integrazione-fiscale-joint.md` per l'interazione con l'IRPEF
- **A monte** c'è `it-pianificazione-obiettivi`: definisce l'allocazione-target **aggregando i secchielli per obiettivo** (ciascuno pesato per il suo capitale) nell'asset allocation complessiva del portafoglio, più il **calendario di glide path** generato da `glidepath-obiettivi.py` (la quota azionaria target di ogni secchiello anno per anno). È quell'aggregato e quel calendario — non target scelti a mano — la fonte delle allocazioni che questa skill riceve in input, mantiene nel tempo, e de-riska progressivamente eseguendo gli spostamenti annuali (con attenzione agli eventi fiscali di ogni vendita).

## Note per l'iterazione

Questa è la versione 0.5 della skill (introdotta in v0.5 del plugin, estesa in v0.8.12).

In quest'iterazione (v0.5):
- **Modulazione della banda per la volatilità della classe**: la banda 5/25 ora si scala con la volatilità del comparto, perché una soglia fissa rappresenta un segnale/rumore diverso tra classi (cinque punti su un azionario capitano per rumore, su un obbligazionario sono un movimento raro). Trattata con onestà la **tensione teorica** — la visione "più volatile → banda più larga" (efficienza di trading) contro il controllo ottimo alla Leland "più volatile → banda più stretta" (la deviazione è più rischiosa): non è una legge, è un trade-off. Implementazione deliberatamente modesta (fattore `(σ/σ_rif)^β` clampato in un intervallo stretto, spegnibile per tornare alla pura 5/25). Validato: azionario si allarga, classi stabili al clamp, retro-compatibilità con modulazione spenta. Vedi `references/bande-dinamiche.md`.

In quest'iterazione (v0.4):
- **Generatore di ordini CSV per broker**: lo script di ribilanciamento ora esporta gli ordini da eseguire, un CSV per broker, con instradamento della cassa (gli acquisti finanziati dalla liquidità presente su ciascun broker, così ogni file è eseguibile senza trasferimenti tra intermediari) e l'annotazione fiscale per riga. Chiude la voce v0.4 della roadmap. Validato su scenario mono e multi-broker (invariante: per ogni broker, acquisti ≤ cassa disponibile lì).

In quest'iterazione (v0.3):
- **Sequenza di liquidazione fiscale in decumulo** (`references/sequenza-liquidazione.md`): da dove prelevare per minimizzare l'imposta (liquidità → flussi già tassati → vendite tax-aware con la gerarchia delle leve → fondo pensione agevolato 9-15% in erogazione), riusando l'ottimizzazione multi-broker; e il prelievo annuo che diventa anche l'occasione per ribilanciare. Chiude la voce v0.4 della roadmap. La sostenibilità del prelievo (quanto, non come) è in `it-pianificazione-obiettivi/references/decumulo.md`.

In quest'iterazione (v0.2):
- **Ottimizzazione globale dello zainetto multi-broker**: la compensazione non attraversa i broker, quindi la scelta di DOVE realizzare le plus (broker × tipo fiscale) determina il costo. Reference `ribilanciamento-multibroker.md` + script `assets/ribilanciamento-multibroker.py` (primo asset della skill, validato su tre scenari).
- **Bande di tolleranza dinamiche** (regola 5/25 + allargamento cost-aware): si ribilancia a soglia, non a calendario; la banda si allarga quando correggere costa imposta netta. Reference `bande-dinamiche.md`, integrata nello script.

Versioni precedenti (v0.1): regime amministrato, dossier titoli ordinario, allocazione target come input utente (no robo-advisory), proiezione deterministica del drift, gerarchia delle quattro leve, coordinamento di fine anno con lo zainetto.

Roadmap:
- ✅ Generatore di ordini esportabile (CSV per broker): fatto in v0.4, con instradamento della cassa per broker
- ✅ Decumulo con prelievi tax-efficient: coperto in `references/sequenza-liquidazione.md` (sequenza di liquidazione fiscale), in coppia con la sostenibilità del prelievo in `it-pianificazione-obiettivi/references/decumulo.md`
- ✅ Modulazione della banda per la volatilità della classe: fatta in v0.5 (fattore clampato sulla 5/25, con la tensione teorica documentata onestamente), oltre l'allargamento cost-aware
