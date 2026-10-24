---
name: it-rebalance
description: "Ribilanciamento di portafoglio tax-aware sotto la fiscalità italiana (regime amministrato). Usa questa skill quando l'utente parla di ribilanciamento, rebalancing, riequilibrio del portafoglio, allocazione target vs effettiva, drift dell'asset allocation, portafoglio sbilanciato («le azioni sono cresciute troppo»), riportare i pesi all'allocazione obiettivo con o senza vendere, ribilanciare con i nuovi versamenti o i dividendi, prelievo in decumulo, ribilanciamento di fine anno coordinato con le minusvalenze. Misura il drift con le bande 5/25 e applica la gerarchia delle leve (versamenti, flussi, vendite in minus, vendite tassate con gate), con il CSV degli ordini per broker. Coordina con `it-tax-optimization`: in Italia ogni vendita è un evento fiscale (plus/minus sul costo medio ponderato, zainetto). NON è consulenza di investimento: non raccomanda quale asset allocation scegliere, che è input dell'utente. NON copre i fondi pensione (vincolati)."
metadata:
  version: "0.7"
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

In regime amministrato la plus o minus di una vendita si calcola sul **costo medio ponderato** del titolo in quel rapporto (art. 6 c. 4 D.Lgs. 461/97 → art. 306 c. 5 TU 2027): (prezzo − PMC) × quantità venduta. Il lotto non si sceglie e l'ordine degli acquisti non conta: una vendita parziale realizza una plus proporzionale e lascia invariato il PMC del residuo. Per ridurre l'imposta si sceglie quale **posizione** vendere (quella con l'imposta per euro venduto più bassa, plus/valore × aliquota), non quale lotto. Il LIFO dell'art. 67 c. 1-bis TUIR (→ art. 76 c. 2 TU 2027) vale solo per i conti in dichiarativo, fuori dallo scope di questa skill. *(Costo medio ponderato in amministrato — Verificato: 2026-10.)*

### L'asimmetria redditi diversi vs capitale (vedi it-tax-optimization)

Quando si vende per ribilanciare:
- Vendita di **azioni dirette, certificates, ETC, obbligazioni e titoli di Stato** (per questi solo la differenza di prezzo, non cedole e scarto di emissione) in plus → reddito diverso → la plus **può** essere compensata con minus pregresse
- Vendita di **ETF UCITS armonizzati** in plus → reddito di capitale → la plus **NON può** essere compensata con minus pregresse
- Vendita di **ETF o fondi non armonizzati** (non UCITS) in plus → reddito di capitale, mai compensabile; se l'OICR non è UE/SEE con gestore vigilato concorre all'IRPEF progressiva → sono le ultime posizioni da vendere in plus

⚠️ **Conseguenza per il ribilanciamento**: se devi vendere asset azionario in plus per ribilanciare, e hai zainetto disponibile, è fiscalmente più efficiente vendere **azioni dirette** (compensabili) piuttosto che ETF, armonizzati o no (non compensabili). A parità di drift da correggere, la scelta dello strumento da vendere cambia il conto fiscale.

### Costi di transazione e Tobin tax (2026)

Ogni vendita/acquisto di ribilanciamento comporta:
- **Commissioni di negoziazione** (variabili per broker)
- **Tobin tax** a carico dell'acquirente di **azioni di società italiane**: **0,4%** fuori mercato, **0,2%** su mercati regolamentati e MTF (aliquote raddoppiate dal 1/1/2026, L. 199/2025); escluse le azioni quotate di società con capitalizzazione media **< €500M**. **ETF, fondi (OICR, comprese le SICAV) e obbligazioni sono esclusi** (DM 21/02/2013, artt. 2 e 15) → per portafogli in ETF la Tobin tax sul ribilanciamento è zero.
- **Imposta di bollo**: 0,2% annuo sul controvalore al 31/12, indipendente dal ribilanciamento (ma vendite di fine anno riducono marginalmente la base)

*Imposta sulle transazioni finanziarie 2026 (art. 1 c. 491-494 L. 228/2012 → artt. 42-45 D.Lgs. 174/2024, mod. L. 199/2025 c. 29-31; esclusione di OICR e obbligazioni, DM 21/02/2013) — Verificato: 2026-10. Dal 2027 la disciplina passa agli artt. 42-50 del D.Lgs. 174/2024 (c. 491 → art. 42, c. 492 → 43, c. 493 → 44, c. 494 → 45).*

Per un portafoglio tipico in ETF UCITS, il costo di transazione del ribilanciamento è essenzialmente solo le commissioni del broker.

## Dove lavorare

I dati personali e i file compilati vivono nella **cartella di lavoro** dell'utente (per esempio `~/piano-finanziario/`; se il plugin è stato installato con Claude Code, è quella scelta all'installazione: `${user_config.cartella_lavoro}`; se il segnaposto qui sopra non è stato sostituito, chiedila all'utente), mai dentro il plugin: la copia installata si sovrascrive a ogni aggiornamento. Regole:

- gli script si lanciano dalla cartella di lavoro con il loro percorso nel plugin, e il file da leggere si passa sempre come argomento (`--help` elenca argomenti e opzioni): `python "${CLAUDE_SKILL_DIR}/assets/ribilanciamento-multibroker.py" --dati piano.json --zainetto importatore.json --out ordini`;
- gli output (JSON, CSV degli ordini, documenti) finiscono nella cartella di lavoro, mai nel plugin.

`${CLAUDE_SKILL_DIR}` è la cartella di questa skill: Claude Code lo sostituisce con il percorso reale quando carica la skill (nei command vale `${CLAUDE_PLUGIN_ROOT}/skills/it-rebalance`). Dipendenze dello script: Python 3.11 o successivo, solo libreria standard.

## Workflow operativo

### Step 1: Ingestion

Raccogliere:

**Portafoglio attuale** (CSV o testo strutturato), per ogni posizione:
- `broker` — intermediario (lo zainetto è per-broker)
- `isin` / `ticker`
- `descrizione` — es. "iShares Core MSCI World UCITS ETF"
- `asset_class` — es. azionario_globale, azionario_EU, obbligazionario_governativo, obbligazionario_corporate, monetario, oro/commodity, ecc.
- `categoria_fiscale` — `reddito_diverso` (azioni dirette, certificates, ETC, obbligazioni e titoli di Stato) o `reddito_capitale` (ETF e fondi UCITS, e i non armonizzati istituiti in UE/SEE white list con gestore vigilato); è il vocabolario del plugin (README, «Glossario»), lo script accetta anche le forme brevi `diverso` e `capitale`. Gli OICR non armonizzati fuori UE/SEE o senza gestore vigilato (per esempio gli ETF domiciliati negli USA) sono `reddito_capitale_irpef`: la plus va a IRPEF progressiva, lo script li rifiuta e si trattano a parte. Se la categoria non è nota, dedurla dalla descrizione con le regole di `it-tax-optimization` (ETF o fondo UCITS → capitale; non UCITS → verificare domicilio e gestore; nessun indizio → `da_classificare`, e chiedere)
- `aliquota` — 26% di default; 12,5% per titoli di Stato italiani e white list, enti territoriali e organismi internazionali (la loro plus consuma lo zainetto al 48,08%, vedi `it-tax-optimization/references/aliquote-12-5-26.md`). ETF e fondi su titoli di Stato (reddito di capitale) hanno un'aliquota mista: si indica `quota_titoli_stato`, la quota media dell'attivo in titoli di Stato e white list che l'emittente certifica ogni semestre (non è nel KID; vale quella del semestre della vendita), e lo script applica 12,5% × quota + 26% × (1 − quota); in alternativa si dà direttamente l'`aliquota` effettiva, tra 12,5% e 26%. Le minus di questi fondi entrano nello zainetto per aliquota / 26%, cioè ridotte del 51,92% per la parte in titoli di Stato (DM 13/12/2011, art. 1; circ. AdE 19/E/2014, par. 5.1)
- `quantita`
- `pmc` (prezzo medio di carico), che in amministrato è la base fiscale delle vendite
- `prezzo_corrente` o `controvalore_attuale`

**Allocazione target** (input utente, NON suggerita dalla skill):
- Peso obiettivo per asset class, es. "60% azionario globale, 30% obbligazionario, 10% monetario"

**Parametri di ribilanciamento:**
- `banda` — soglia oltre cui si ribilancia. Default **dinamico** (regola 5/25 + allargamento cost-aware, vedi `references/bande-dinamiche.md`) invece di una banda fissa: la soglia è il minore tra 5 punti assoluti e 25% del peso target, allargata ×2 quando correggere richiede di pagare imposta. La modulazione per volatilità della classe è opzionale e spenta di default; l'utente può accenderla o forzare una banda fissa.
- `nuovi_versamenti_disponibili` — liquidità in entrata da poter usare per Leva 1 (€, eventualmente ricorrente)
- `flussi_attesi` — dividendi/cedole attesi nei prossimi mesi (per Leva 2)
- `fase` — accumulo (versamenti netti positivi) o decumulo (prelievi netti)
- `prelievo` — in decumulo, gli euro netti da prelevare (parametro `PRELIEVO` dello script: le vendite coprono anche l'imposta, la cassa prelevata non si reinveste)

**Zainetto fiscale** (per coordinamento con it-tax-optimization):
- Minus pregresse disponibili per broker, con anno di formazione (per la scadenza 4 anni), in **euro 26%-equivalenti**: una minus al 12,5% vale il 48,08% (€1.000 di minus da BTP = €480,77 di zainetto). Lo script prende un totale per broker: l'importo 26%-equivalente e la quota che scade quest'anno, da consumare per prima, li dà l'importatore di `it-tax-optimization`

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

Output: tabella asset class con peso effettivo, target, drift, banda stretta/larga, flag fuori/dentro banda. Identificare quali classi sono **sovrappesate** (da ridurre) e **sottopesate** (da aumentare). È il drift di oggi: la decisione di vendere si prende nello Step 3, sul patrimonio dopo versamenti, flussi e prelievo (lo script misura già lì la tabella).

La banda **5/25** corregge il difetto della banda fissa: per le classi a peso piccolo (es. monetario al 10%) la soglia effettiva scende (2,5%), perché un drift assoluto modesto è uno scostamento relativo grande; per le classi grandi domina il 5% assoluto. Vedi `references/bande-dinamiche.md`.

L'**allargamento cost-aware** entra nello Step 3: se correggere un sovrappeso si fa a costo netto zero (flussi, vendita di minus, o plus interamente compensata dallo zainetto), si agisce sulla banda **stretta**; se richiede di realizzare plus che pagano imposta, si agisce solo oltre la banda **larga**. In breve: non si paga imposta per correggere un drift troppo piccolo per contare.

⚠️ Se nessuna classe è fuori banda → **raccomandare di NON ribilanciare**. Il ribilanciamento ha senso solo oltre la soglia; ribilanciare per piccoli scostamenti genera costi (fiscali e commissioni) senza beneficio reale. Bias verso il non operare, come in it-tax-optimization.

**Regola di rientro (una sola)**: quando si ribilancia, si va **a target se la correzione è a costo netto zero** (flussi, minus, plus compensate dallo zainetto), e **fino a metà della banda stretta per la parte che paga imposta**. Non ci si ferma al bordo (la classe ri-sforerebbe presto, Kitces), ma non si paga imposta per l'ultima precisione. Mostrare i due costi, a target e a metà banda; lo script li stampa. `OBIETTIVO_RIENTRO` vale «misto» (default, la regola qui sopra), «target» (anche la parte tassata va a target, sempre solo oltre la banda larga) o «banda» (anche la parte a costo zero si ferma al punto di rientro); `MARGINE_RIENTRO` fissa il punto di rientro, target ± 0,5 × banda stretta di default.

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

# Pesi e gap si misurano sul patrimonio DOPO versamenti, flussi e prelievo: una classe
# sovrappesata oggi può non esserlo più dopo il versamento, e allora non si vende nulla.

# Se gap residuo dopo Leve 1-2:
# LEVA 3: vendita posizioni in MINUS (o senza plus) tra le sovrappesate, di TUTTE le classi
#         prima di qualsiasi vendita in plus
per posizione in (sovrappesate AND plus_latente <= 0):
    vendere (parzialmente o totalmente) per correggere il sovrappeso
    la minus realizzata entra subito nello zainetto di quel broker (per aliquota / 26%:
    al 48,08% se la posizione è al 12,5%, meno del 100% per un fondo ad aliquota mista)
    e compensa solo le plus vendute DOPO sullo stesso broker
    (art. 6 c. 5 D.Lgs. 461/97 → art. 306 c. 6 TU 2027): le vendite in minus si
    eseguono per prime, e i CSV le elencano per prime
    → costo fiscale: ZERO o NEGATIVO (genera zainetto / compensa plus)

# LEVA 4 (ultima risorsa): vendita posizioni in PLUS
per posizione in (sovrappesate AND plus_latente > 0):
    # Ottimizzazione DOPPIA: broker × tipo fiscale (vedi ribilanciamento-multibroker.md)
    # La compensazione NON attraversa i broker: lo zainetto del broker A azzera
    # solo plus realizzate al broker A, e solo su strumenti reddito_diverso.
    priorità 1: la QUOTA A COSTO ZERO: la parte delle posizioni reddito_diverso coperta
                dallo zainetto dello stesso broker (una plus al 12,5% lo consuma al
                48,08%), anche se il resto della posizione pagherebbe imposta
    priorità 2: il resto in ordine crescente di imposta per euro venduto,
                plus/valore × aliquota della posizione (sul PMC), senza distinguere tra
                reddito_capitale e reddito_diverso presso un broker senza zainetto: a
                parità di plus un titolo di Stato al 12,5% costa la metà
    # gate cost-aware (banda dinamica): la parte che lascia imposta NETTA si vende
    # solo se |drift| della classe supera la banda larga, e solo fino a metà banda;
    # altrimenti si rinvia, e il residuo non corretto si dichiara con il suo costo
    calcola tassa = (plus_realizzata − compensazione_zainetto_stesso_broker) × aliquota_posizione
    → costo fiscale: POSITIVO, da minimizzare con la scelta broker × tipo × aliquota

# SOTTOPESATE FUORI BANDA non coperte dalla cassa: si vende dalle classi sopra il
# target anche se in banda, prima a costo zero (Leva 3 e quota coperta dallo zainetto)
# fino al target; con imposta solo se, dopo la cassa, il drift della sottopesata supera
# ancora la banda larga, e solo fino a metà banda
```

Per il caso multi-broker, lo script `assets/ribilanciamento-multibroker.py` esegue questa ottimizzazione automaticamente: dato il portafoglio (con broker, categoria fiscale, aliquota e plus/minus per posizione), lo zainetto per broker e il target, produce il piano di vendite ottimizzato, una riga per posizione nell'ordine di esecuzione (le minus prima delle plus), il costo fiscale, lo zainetto residuo e, per ogni classe non corretta del tutto, il residuo con il motivo e il costo. È il modo più affidabile di gestire la Leva 4 quando i conti sono più di uno.

**I dati dello script** arrivano da un JSON nella cartella di lavoro (`--dati piano.json`); senza, lo script usa l'esempio cablato in testa e lo dice. Lo zainetto può venire dal JSON dell'importatore di `it-tax-optimization` (`--zainetto importatore.json`: legge `analisi.per_broker[].zainetto_26_equivalente`, cioè le minus valide in euro al 26%, con quelle al 12,5% già computate al 48,08%); `--out cartella` sceglie dove scrivere i CSV. Schema di `piano.json`:

```json
{
  "posizioni": [
    {"broker": "Fineco", "asset_class": "azionario", "categoria_fiscale": "reddito_capitale", "valore": 40000, "plus": 10000},
    {"broker": "Fineco", "asset_class": "azionario", "categoria_fiscale": "reddito_diverso", "valore": 10000, "plus": 4000},
    {"broker": "Directa", "asset_class": "obbligazionario", "categoria_fiscale": "reddito_diverso", "valore": 9000, "plus": 0, "aliquota": 0.125}
  ],
  "zainetto": {"Fineco": 5000, "Directa": 0},
  "target": {"azionario": 0.60, "obbligazionario": 0.30, "monetario": 0.10},
  "nuovi_versamenti": 0, "flussi_attesi": 0, "prelievo": 0,
  "obiettivo_rientro": "misto", "broker_versamenti": "Fineco"
}
```

Per posizione: `broker`, `asset_class` (una delle chiavi di `target`), `categoria_fiscale` (`reddito_diverso` o `reddito_capitale`; accettate anche `tipo_fiscale`/`tipo` e le forme brevi), `valore` e `plus` in euro (la minus è una plus negativa), facoltativi `aliquota` (0,125 per i titoli di Stato) o `quota_titoli_stato` per ETF e fondi su titoli di Stato. Dal JSON dell'importatore le posizioni si copiano così come sono, aggiungendo solo la classe (`asset_class` o `classe`, la assegna l'utente): `valore` è `posizioni[].valore`, `plus` è `posizioni[].plus_minus`, la categoria è `categoria_fiscale` e l'aliquota è `posizioni[].aliquota`. L'importatore la scrive in percento (26 o 12,5) e lo script la converte in frazione dicendolo: non va tolta, perché senza il campo un titolo di Stato sarebbe tassato al 26% e consumerebbe lo zainetto per intero invece che al 48,08%. Le chiavi dello zainetto si allineano ai nomi dei broker delle posizioni (maiuscole e spazi a parte), e uno zainetto senza posizioni dello stesso broker viene segnalato come non usato. Le posizioni `reddito_capitale_irpef` e `da_classificare` vanno risolte prima: lo script le rifiuta. Le chiavi facoltative (`nuovi_versamenti`, `flussi_attesi`, `prelievo`, `aliquota_default`, `obiettivo_rientro`, `margine_rientro`, `modula_volatilita`, `genera_csv`, `cartella_output`, `broker_versamenti`) sostituiscono le costanti omonime dello script.

Lo stesso script **genera anche gli ordini da eseguire**, un **CSV per broker** (parametro `GENERA_CSV`), apribile in Excel italiano con un doppio clic: separatore `;`, virgola decimale, UTF-8 con BOM. La parte interessante è l'**instradamento della cassa**: gli acquisti delle classi sottopesate vengono finanziati dalla liquidità presente su ciascun broker — le vendite realizzate lì più gli eventuali versamenti che vi atterrano — così ogni broker resta a saldo e i suoi ordini sono eseguibili senza spostare cassa tra intermediari (operazione che richiederebbe giorni). Ogni riga porta con sé l'annotazione fiscale (`categoria_fiscale` con i valori del vocabolario, `reddito_diverso` o `reddito_capitale`; plus/minus realizzata, imposta, compensazione da zainetto) e una colonna `strumento_ISIN` da compilare a mano; senza `--dati` la riga NOTA in fondo dice che sono dati di esempio: il piano ragiona per classe, è l'utente a scegliere lo strumento specifico. ⚠️ I broker italiani non hanno un formato standard di import ordini, quindi i CSV sono una **checklist di esecuzione** e una traccia di audit, non file caricabili in un click.

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
- Se la correzione paga imposta → regola di rientro: fino a metà banda, non a target, e solo con il drift oltre la banda larga; altrimenti si rinvia, dicendo quanto resta da correggere e quanto costerebbe
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
- ❌ Vendere con imposta fino al target esatto: la parte tassata si ferma a metà banda (regola di rientro). A target si va solo quando costa zero.
- ❌ Dire «nessuna vendita necessaria» quando una classe è fuori banda: se la vendita è rinviata per l'imposta, va detto, con il residuo e il suo costo.
- ❌ Dimenticare di coordinare con minus in scadenza: il ribilanciamento di fine anno è l'occasione per usare zainetto che altrimenti evapora.

## Sinergia con le altre skill del plugin

`it-rebalance` è il tassello che **connette le due skill esistenti** in un workflow operativo:

- **Con `it-tax-optimization`**: il ribilanciamento genera eventi fiscali (realizzo plus/minus). La Leva 3 (vendita posizioni in minus) crea zainetto; la Leva 4 (vendita posizioni in plus) può consumare zainetto in scadenza. Quando l'utente ribilancia a fine anno, le due skill vanno usate insieme: prima `it-tax-optimization` identifica lo zainetto disponibile e le minus in scadenza, poi `it-rebalance` sequenzia le vendite per sfruttare la compensazione. Vedi `references/coordinamento-zainetto.md`.

- **Con `it-pianificazione`**: il ribilanciamento del dossier titoli ordinario è distinto dal ribilanciamento del comparto del fondo pensione (che ha regole proprie, no eventi fiscali sul cambio comparto). Se l'utente ha entrambi, la skill chiarisce che sono due processi separati. Il fondo pensione si ribilancia "gratis" (switch comparto senza tassazione), il dossier no.

## Riferimenti

- `references/gerarchia-leve.md` — approfondimento sulle 4 leve con esempi numerici completi (accumulo vs decumulo)
- `references/coordinamento-zainetto.md` — protocollo di coordinamento con it-tax-optimization per il ribilanciamento di fine anno
- `references/ribilanciamento-multibroker.md` — l'ottimizzazione globale dello zainetto quando il portafoglio è su più broker: il vincolo che la compensazione non attraversa i broker, e la doppia ottimizzazione broker × tipo fiscale per scegliere DOVE realizzare le plus
- `references/bande-dinamiche.md` — le bande di tolleranza dinamiche (regola 5/25 + allargamento cost-aware ×2 + rientro misto; modulazione per volatilità opzionale e spenta di default): quando ribilanciare, fin dove, perché non pagare imposta per correggere un drift troppo piccolo, e la tensione teorica sulla modulazione per volatilità
- `references/sequenza-liquidazione.md` — la sequenza di liquidazione fiscalmente efficiente in **decumulo**: da dove prelevare per pagare meno imposta (liquidità → flussi → vendite tax-aware → fondo pensione agevolato 9-15%), e come il prelievo annuo diventa anche l'occasione per ribilanciare
- `assets/ribilanciamento-multibroker.py` — strumento che esegue l'ottimizzazione multi-broker, le bande dinamiche, la regola di rientro e il prelievo in decumulo (chiave `prelievo` del JSON) su un portafoglio reale, e **genera gli ordini come CSV per broker** con instradamento della cassa (dati da `--dati piano.json`, zainetto anche da `--zainetto`, CSV in `--out`; output: drift, piano di vendite ottimizzato per broker/tipo/aliquota nell'ordine di esecuzione, residui non corretti con motivo e costo, costo fiscale, zainetto residuo, allocazione risultante, e un CSV di ordini eseguibili per ciascun broker, solo se ci sono ordini)
- **Vedi anche** `it-tax-optimization/SKILL.md` per le regole di compensazione minus/plus e `it-tax-optimization/references/multi-intermediario.md` per la frammentazione su più broker, e `it-pianificazione/references/integrazione-fiscale-joint.md` per l'interazione con l'IRPEF
- **A monte** c'è `it-pianificazione-obiettivi`: definisce l'allocazione-target **aggregando i secchielli per obiettivo** (ciascuno pesato per il suo capitale) nell'asset allocation complessiva del portafoglio, più il **calendario di glide path** generato da `glidepath-obiettivi.py` (la quota azionaria target di ogni secchiello anno per anno). È quell'aggregato e quel calendario — non target scelti a mano — la fonte delle allocazioni che questa skill riceve in input, mantiene nel tempo, e de-riska progressivamente eseguendo gli spostamenti annuali (con attenzione agli eventi fiscali di ogni vendita).
