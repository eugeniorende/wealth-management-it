---
name: it-tax-optimization
description: Ottimizzazione fiscale di minusvalenze e plusvalenze sotto la normativa italiana (regime amministrato). Usa questa skill ogni volta che l'utente parla di minusvalenze, plusvalenze, ottimizzazione fiscale italiana, compensazione minus/plus, zainetto fiscale, scadenza minus a 4 anni, harvesting fiscale su broker italiani (Directa, Fineco, Banca Sella, ecc.) ed esteri (Interactive Brokers e Degiro in regime dichiarativo, nei principi, con quadri RT/RW e IVAFE; Trade Republic e Scalable possono essere in amministrato), tassazione ETF UCITS armonizzati, regime amministrato come sostituto d'imposta, articolo 67 vs articolo 44 TUIR, Tobin tax / imposta sulle transazioni finanziarie (ITF) su azioni italiane, imposta di bollo sul dossier titoli, dividendi esteri e W-8BEN, successione e donazione del dossier. Usa questa skill anche per la tassazione delle criptovalute / cripto-attività (Bitcoin, Ethereum, altcoin, NFT, stablecoin): aliquota 33% dal 2026 e 26% per gli e-money token in euro MiCA, compartimento separato delle minusvalenze cripto, eventi tassabili e permuta cripto-cripto, metodo del costo di carico, monitoraggio fiscale quadro RW/W, imposta sul valore delle cripto-attività 0,2%, regime amministrato cripto, rivalutazione del costo di carico. Copre anche i temi cripto avanzati: DeFi (staking, lending, yield, liquidity pool, LP token, impermanent loss), airdrop e fork, mining occasionale vs professionale, NFT secondo il ruolo (investitore vs artista/creatore), e il ravvedimento operoso per regolarizzare cripto non dichiarate negli anni passati (quadro RW omesso, sanzioni, DAC8). Copre inoltre i casi di confine: trasferimenti tra wallet, bridge cross-chain e wrapping (WBTC, stETH), cripto detenute in attività d'impresa o partita IVA (IRES, IVA, forfettario che investe in cripto), cripto ricevuta come stipendio o compenso, neo-residenti e flat tax €100.000 sui redditi esteri, e successione/donazione di criptovalute (eredità, costo di carico per gli eredi, territorialità). Trigger anche su domande di fine anno fiscale (novembre-dicembre) relative a portafogli italiani. NON usare per fiscalità USA (wash sale, HIFO, Roth IRA) — quella è coperta dalla skill upstream `tax-loss-harvesting`. NON sostituisce consulenza di un commercialista abilitato.
---

# it-tax-optimization

Skill per l'ottimizzazione di minusvalenze e plusvalenze sotto il regime fiscale italiano "amministrato", dove l'intermediario (banca/broker) funge da sostituto d'imposta e gestisce lo "zainetto fiscale" del cliente.

## Scope esplicito

**Cosa fa:**
1. **Analisi** — legge un portafoglio e classifica plus/minus latenti per categoria fiscale
2. **Simulazione** — calcola l'impatto fiscale di trade ipotetici di realizzo
3. **Calendario** — genera piano d'azione con scadenze (zainetto in evaporazione, deadline fine anno)

**Cosa NON fa:**
- ❌ Non dà consigli di investimento. Le strategie sono *fiscali*, non orientate a rendimento/rischio.
- ❌ Non sostituisce un commercialista. Casi limite (successioni, residenza estera, partecipazioni qualificate, conferimento fondi pensione, trasferimento dossier inter-intermediario) richiedono parere professionale. Per successioni e donazioni del dossier i principi sono in `references/successione-donazione.md`; valori da dichiarare, fondi ed ETF e casi concreti restano da notaio o commercialista.
- ⚠️ Il calcolo automatico assume il regime amministrato. Il regime **dichiarativo** (broker senza sostituto d'imposta italiano, come Interactive Brokers e Degiro) è ora coperto a livello di principi, adempimenti e implicazioni sulla compensazione (`references/regime-dichiarativo.md`: stato dei broker esteri, quadri RT, RM e RW, IVAFE, LIFO, cambio del giorno, liquidità in valuta, zainetto unificato), ma la compilazione effettiva del Modello Redditi PF e il calcolo operazione-per-operazione richiedono un commercialista.
- ❌ Non gestisce: derivati OTC, immobili, partecipazioni qualificate, fondi pensione (regime sostitutivo distinto). Le **criptovalute** sono ora coperte a livello di principi e adempimenti (`references/criptovalute.md`), ma il calcolo su portafogli con molte operazioni o storici multi-exchange richiede comunque un commercialista o un software dedicato.

## Regole fiscali fondamentali (vigenti 2026)

### L'asimmetria redditi diversi vs redditi di capitale

Questo è il vincolo strutturale del sistema italiano e la fonte degli errori più costosi. Memorizzare la tabella:

| Categoria fiscale | Tipo provento | Compensabile con minus pregresse? |
|---|---|---|
| **Reddito diverso** (art. 67 TUIR, lett. c-bis, c-ter) | Plusvalenze da: azioni, certificates, ETC/ETN, obbligazioni (solo la differenza di prezzo, al netto di cedole, ratei e scarto di emissione), warrant, opzioni quotate | **SÌ** (tra redditi diversi "tradizionali") |
| **Reddito di capitale** (art. 44 TUIR) | Dividendi azionari, cedole obbligazionarie, scarto di emissione (BOT, CTZ, zero coupon), plusvalenze di ETF e fondi (UCITS armonizzati e non armonizzati), proventi distribuiti da fondi, interessi su conti deposito | **NO** |
| **Reddito diverso "cripto"** (art. 67 TUIR, lett. **c-sexies**) | Plus/minus su cripto-attività (Bitcoin, Ethereum, altcoin, NFT, stablecoin) | **SÌ ma SOLO con altre cripto** (compartimento separato) |

⚠️ **Trappola ETF UCITS armonizzati**: la *perdita* sulla vendita di un ETF UCITS è reddito diverso (genera minus utilizzabile). La *plusvalenza* sulla vendita futura dello stesso tipo di ETF è reddito di capitale (non compensabile). Vedi `references/etf-trap-redditi-capitale.md` per esempi numerici.

⚠️ **ETF e fondi non armonizzati** (non UCITS, per esempio ETF domiciliati negli USA): la plusvalenza è reddito di capitale e non compensa mai lo zainetto; la minus è reddito diverso. Cambia il regime: 26% a titolo d'imposta solo se l'OICR è istituito in UE/SEE white list e ha un gestore vigilato AIFMD; altrimenti la plus concorre al reddito complessivo IRPEF, con ritenuta del 26% a titolo d'acconto, e va dichiarata nel quadro RL anche in regime amministrato (art. 10-ter cc. 6-7 L. 77/1983, vigente fino al 31/12/2026; dal 2027 art. 59 cc. 9-10 dell'All. 1 al D.Lgs. 33/2025; aliquota del 26% dall'art. 3 c. 1 DL 66/2014).

⚠️ **Le cripto sono un terzo compartimento**: sono redditi diversi (art. 67 c-sexies), ma le minusvalenze cripto compensano **solo** plusvalenze cripto — non azioni, ETF o derivati, né viceversa. Aliquota **33%** dal 2026 (26% solo per gli e-money token in euro MiCA). Vedi `references/criptovalute.md`.

Le minus possono compensare solo plus della stessa categoria (redditi diversi "tradizionali" tra loro; cripto solo con cripto). Non c'è cross-category compensation.

### Le minus durano 4 anni

Minusvalenza realizzata nell'anno N → utilizzabile per compensare plusvalenze fino al **31/12 dell'anno N+4 incluso**. Dal 1/1 dell'anno N+5 evapora. Il termine è lo stesso in dichiarativo (art. 68 c. 5 TUIR → art. 77 c. 6 TU 2027), dove la minus va indicata nel quadro RT dell'anno di realizzo, anche senza imposta dovuta, per poterla riportare. Chiudere il rapporto non la fa sparire: l'intermediario la certifica e resta utilizzabile altrove fino alla stessa scadenza (Pattern E).

Esempio pratico:
- Minus realizzata 15/03/2022 → finestra di utilizzo fino al 31/12/2026
- Stessa minus, dal 01/01/2027 → persa

### Metodo del costo: costo medio ponderato in amministrato, LIFO in dichiarativo

- **Amministrato**: l'intermediario assume come costo il **costo medio ponderato** di ciascuna categoria omogenea, cioè dello stesso titolo nello stesso rapporto (art. 6 c. 4 D.Lgs. 461/97 → art. 306 c. 5 TU 2027). La plus o minus di una vendita parziale è (prezzo − PMC) × quantità venduta: l'ordine dei lotti non conta e dopo la vendita il PMC residuo resta uguale. È il numero che il broker applica e certifica, quindi le simulazioni si fanno sul PMC.
- **Dichiarativo**: si considerano cedute per prime le attività acquistate più di recente (**LIFO**, art. 67 c. 1-bis TUIR → art. 76 c. 2 TU 2027; le istruzioni del quadro RT chiedono il costo «calcolato sulla base del criterio L.I.F.O.»). Servono i lotti con data, quantità e prezzo: vedi `references/regime-dichiarativo.md`.
- In nessuno dei due regimi l'investitore sceglie il lotto: niente HIFO o Specific ID come negli USA.

*Metodo del costo (art. 6 c. 4 D.Lgs. 461/97, art. 67 c. 1-bis TUIR, istruzioni Redditi PF 2026 fasc. 2, D.Lgs. 117/2026) — Verificato: 2026-10.*

### Aliquote: 26% e 12,5% con coefficiente di abbattimento

Due aliquote in vigore:

- **26%**: aliquota standard sui redditi di natura finanziaria (azioni, ETF, fondi, obbligazioni corporate)
- **12,5%**: titoli di Stato italiani (BTP/BOT/CCT/CTZ), enti pubblici territoriali italiani, organismi internazionali (BEI/BERS/IBRD/IADB/AIIB ecc.), titoli di Stato di paesi "white list" (DM 4/9/1996 e aggiornamenti)

Quando minus e plus hanno aliquote diverse, si applica il **coefficiente di abbattimento 12,5/26 = 0,48077**: l'importo a 12,5% viene "scalato" al riferimento 26%. Conseguenza pratica:

| Minus aliquota | Plus aliquota | Plus assorbibile per €100 di minus |
|---|---|---|
| 26% | 26% | €100 (1:1) |
| 26% | 12,5% | €208 (vantaggioso: minus 26% "pesa di più") |
| 12,5% | 12,5% | €100 (1:1) |
| 12,5% | 26% | €48 (svantaggioso: minus 12,5% "pesa di meno") |

⚠️ **ETF UCITS che investono in titoli di Stato NON sono al 12,5%**: l'intermediario applica un'aliquota *mista* in base alla quota di NAV whitelist. Detenere BTP direttamente ≠ detenerli via ETF UCITS. Inoltre la plus su ETF UCITS resta sempre reddito di capitale (non compensabile con minus pregresse), indipendentemente dalla composizione.

Per dettagli normativi, esempi numerici e edge case (ETF "Government Bond" misti, edge case fondi), consultare `references/aliquote-12-5-26.md`.

### Niente wash sale

A differenza degli USA, vendita e riacquisto immediato (anche stesso giorno) dello stesso titolo è legittimo per realizzare una minus. Nessuna penalità o disallineamento temporale richiesto. Questo cambia radicalmente la strategia di "harvesting" rispetto al modello USA.

### Costi fiscali non compensabili

Sono costi del dossier che NON entrano nel calcolo minus/plus ma incidono sul rendimento netto. Vanno menzionati nei report:

- **Imposta di bollo**: 0,2% annuo sul controvalore del dossier al 31/12, applicata d'ufficio dall'intermediario italiano. Per le **persone fisiche non c'è tetto** (l'imposta cresce linearmente col valore); il tetto di €14.000/anno vale solo per i soggetti **diversi** dalle persone fisiche (società ed enti). L'equivalente estero è l'IVAFE, anch'essa 0,2% (vedi `references/regime-dichiarativo.md`).
- **Tobin tax (ITF)**: dal 1° gennaio 2026 (L. 199/2025, art. 1 commi 29-31) le aliquote sulle azioni sono **raddoppiate**:
  - **0,20%** all'acquisto su mercato regolamentato / sistema multilaterale (era 0,10% fino al 31/12/2025), calcolata sul saldo netto positivo di fine giornata per ciascun titolo
  - **0,40%** per acquisti OTC / fuori mercato (era 0,20%), su ogni singolo trasferimento
  - Si applica **solo** alle azioni e strumenti partecipativi di società **italiane con capitalizzazione > €500M** (lista Consob aggiornata a novembre dell'anno precedente)
  - Derivati su quei titoli: imposta in **misura fissa** a scaglioni (da €0,01875 a €200 per operazione), **NON raddoppiata**, ridotta a 1/5 su mercati regolamentati (Idem)
  - A carico dell'acquirente, versata d'ufficio dall'intermediario italiano (codice tributo F24: 4058 per chi opera con broker esteri senza sostituto)
  - **ESENTI**: ETF, fondi comuni, SICAV, ETC, obbligazioni, titoli di Stato, valute/Forex; operazioni intraday a saldo netto zero; azioni di società < €500M cap
- **Commissioni di negoziazione**: variabili per broker; entrano nel costo di carico (riducono plus o aumentano minus).
- **Ritenute estere sui dividendi** di azioni estere detenute direttamente: in amministrato il 26% italiano si applica sul netto frontiera, e il prelievo totale va dal 37,1% (USA con W-8BEN) al 51,9% (Svizzera senza rimborso). Non compensano nulla; il W-8BEN e le domande di rimborso le riducono. Per un ETF UCITS sono già nel rendimento del fondo. Vedi `references/dividendi-esteri.md`.

⚠️ **Implicazione per il retail**: un portafoglio diversificato basato su **ETF è sostanzialmente esente** da Tobin tax (ETF, fondi, obbligazioni, titoli di Stato sono tutti esclusi). La Tobin tax morde solo su **azioni italiane large-cap detenute direttamente**. Non sovrastimarne l'impatto: per il tipico investitore in ETF UCITS l'imposta è zero. Il raddoppio 2026 è rilevante solo per chi fa stock picking su singole azioni italiane di grandi società (es. Enel, Eni, Generali, Intesa, UniCredit, Ferrari, ecc.).

## Workflow operativo

### Step 1: Ingestion

Chiedere all'utente (se non già nel contesto):

**Snapshot portafoglio** in CSV o testo strutturato. Schema minimo per riga:
- `broker` — nome intermediario (Directa, Fineco, BG Saxo, ecc.). **Obbligatorio**, anche se c'è un solo broker
- `isin` o `ticker`
- `descrizione` (es. "iShares Core MSCI World UCITS ETF")
- `quantita`
- `pmc` (prezzo medio di carico): in amministrato è la base fiscale, quella che il broker espone. Il dettaglio dei lotti (`data_acquisto`, `quantita`, `prezzo`) serve solo per i conti in dichiarativo (LIFO) o per ricostruire il PMC se il broker non lo mostra
- `prezzo_corrente`
- `categoria_fiscale` (opzionale, se nota): `reddito_diverso`, `reddito_capitale` (plus al 26% a titolo d'imposta) o `reddito_capitale_irpef` (OICR non armonizzati fuori UE/SEE o senza gestore vigilato: la plus va a IRPEF progressiva); `da_classificare` se non si sa
- `aliquota` (opzionale: `26` o `12,5`; se non fornita, dedurre da tipo strumento)

Se `categoria_fiscale` non fornita, dedurla:
- ETF UCITS armonizzato → `reddito_capitale` (plus). Vendita in perdita: la *minus* è comunque reddito diverso.
- Azione singola, certificate, ETC/ETN → `reddito_diverso`
- ETF o fondo non armonizzato (non UCITS) → `reddito_capitale` se istituito in UE/SEE white list con gestore vigilato, altrimenti (per esempio ETF domiciliati negli USA) `reddito_capitale_irpef`: la plus concorre al reddito complessivo e va nel quadro RL anche in amministrato. Vendita in perdita: la *minus* è reddito diverso.
- Nessun indizio dalla descrizione (né ETF o fondo, né azione, né obbligazione) → `da_classificare`: chiedere, non assumere `reddito_diverso`
- Obbligazioni e titoli di Stato: cedole, ratei e scarto di emissione (differenza tra prezzo di emissione e rimborso, maturata pro rata) = `reddito_capitale`; `reddito_diverso` solo la differenza tra corrispettivo o rimborso e costo d'acquisto, al netto dei redditi di capitale maturati. Un BOT, un CTZ o uno zero coupon sottoscritto all'emissione e tenuto a scadenza non genera reddito diverso e non consuma zainetto.
- ETC fisico (materie prime) → `reddito_diverso` come gli altri ETC; se dalla descrizione non si capisce se è un ETC o un ETF (solo il nome dell'emittente, per esempio «WisdomTree Gold») → `da_classificare`, chiedere

Se `aliquota` non fornita, dedurla:
- ISIN che inizia con `IT000` + titolo di Stato/ente pubblico → 12,5%
- BTP/BOT/CCT/CTZ identificati per descrizione → 12,5%
- Titoli di Stato esteri (Treasury USA, Bund, OAT, Gilt, JGB) → 12,5% (whitelist)
- Organismi internazionali (BEI, BERS, BIRS…) ed enti territoriali di Stati white list → 12,5%. L'importatore riconosce per nome solo i casi più comuni: per le altre obbligazioni estere assume il 26% e lo segnala, e l'aliquota va indicata nella colonna
- Tutto il resto → 26%
- ETF UCITS su titoli di Stato: NON 12,5% pulito → 26% di default con caveat (vedi `references/aliquote-12-5-26.md`)

**Stato zainetto fiscale** (può essere scaricato da quasi tutti i broker italiani come "rendiconto fiscale annuale" o "estratto plus/minus"). Schema:
- `broker` — **obbligatorio** (zainetto è per-intermediario in amministrato)
- per i conti in dichiarativo, invece, le **minus riportabili dal quadro RT** delle dichiarazioni precedenti, per anno e aliquota, non per broker: sono del contribuente e valgono per tutti quei conti
- `anno_realizzo`
- `importo_residuo` (€)
- `aliquota` (26% o 12,5%)

**Contesto operativo**:
- Numero di intermediari coinvolti (se >1: applicare workflow multi-broker, vedi `references/multi-intermediario.md`)
- Regime per ciascun broker: amministrato (default) o dichiarativo. Trade Republic e Scalable Capital possono essere in amministrato con la succursale italiana, Interactive Brokers e Degiro sono in dichiarativo: vedi la tabella in `references/regime-dichiarativo.md`
- Cut-off operativi specifici del broker (Directa e Sella di solito chiudono prima del 31/12)

Se mancano dati essenziali → CHIEDERE, NON INVENTARE. Esempio: se l'utente fornisce solo controvalore totale senza ISIN, non si può fare analisi. Se non specifica i broker quando ne ha più di uno, l'analisi è inattendibile.

### Step 2: Analisi

Per ogni posizione, calcolare:

```
plus_minus_latente = (prezzo_corrente - pmc) × quantita
tassazione_se_realizzato = plus_latente × aliquota  (se plus_latente > 0)
contributo_zainetto = abs(plus_latente)              (se plus_latente < 0, è creazione minus)
```

**Aggregazione PER-BROKER** (importante: lo zainetto non si comunica cross-broker in amministrato):

Per ciascun intermediario separatamente:
1. **Tabella zainetto per anno scadenza** — quanto sta scadendo quando, suddiviso per aliquota (26% e 12,5%)
2. **Plus latenti compensabili** (categoria `reddito_diverso`) — totale e per posizione, suddiviso per aliquota
3. **Plus latenti NON compensabili** (`reddito_capitale` e `reddito_capitale_irpef`) — flaggate con avviso; per `reddito_capitale_irpef` ricordare l'IRPEF marginale e il quadro RL
4. **Minus latenti** — potenziali nuovi contributi a zainetto se realizzate

**Broker in dichiarativo** (Interactive Brokers, Degiro, o un conto per cui l'utente ha scelto il dichiarativo): il calcolo sul PMC e lo zainetto per broker non valgono.
- Plus e minus si calcolano sui **lotti** (data, quantità, prezzo e cambio del giorno di ogni acquisto), in euro (art. 9 c. 2 TUIR) e con il LIFO del dichiarativo. Il prezzo medio in valuta mostrato dal broker non basta: il cambio può invertire il segno della plus. Senza i lotti non calcolare plus e minus di quei conti: dirlo all'utente e rinviare al commercialista.
- Le minus del quadro RT degli anni precedenti sono del contribuente e valgono per tutti i conti in dichiarativo: tra due conti in dichiarativo il Pattern A è cross-broker.
- Il Pattern D si valuta solo per i rapporti in amministrato. Tra un conto in amministrato con minus e uno in dichiarativo con plus si confrontano il Pattern D (revoca dell'amministrato sul conto con le minus: resta aperto, le minus certificate vanno nel quadro RT e da lì compensano le plus del conto in dichiarativo) e il Pattern E (chiusura del rapporto, con la stessa certificazione).
- L'output aggiunge la sezione «Adempimenti del dichiarativo» (sezione 5).

**Aggregazione CROSS-BROKER** (per il confronto tra amministrato, chiusura con certificazione e dichiarativo):

Calcolare anche lo scenario "consolidato" come se tutti i broker fossero in dichiarativo unificato. L'opzione vale dal 1/1 dell'anno successivo, quindi lo scenario conta solo le minus che a quella data sono ancora vive:
- Zainetto consolidato utile al dichiarativo: somma cross-broker delle minus con scadenza successiva al 31/12 dell'anno corrente, distinta per aliquota. Quelle che scadono quest'anno restano fuori: vanno consumate in loco (Pattern A) o certificate chiudendo il rapporto (Pattern E)
- Plus latenti compensabili totali (somma cross-broker)
- Compensazione massima teorica in dichiarativo, su quello zainetto
- **Delta vs amministrato**: quanto risparmio fiscale extra dà il dichiarativo rispetto a quello che ogni broker compensa da sé con le stesse minus

Conservare entrambi gli aggregati per la simulazione e l'output.

**Quando applicare il coefficiente di abbattimento**:

Se nell'analisi compaiono posizioni con aliquote miste (26% + 12,5%), applicare le formule di conversione (vedi `references/aliquote-12-5-26.md` per dettagli):
- Minus 26% può assorbire plus 12,5% al ratio 1:2,08 (favorevole)
- Minus 12,5% può assorbire plus 26% al ratio 0,48:1 (sfavorevole)
- Stessa aliquota → 1:1 nominale

Esplicitare sempre il calcolo nel report: l'utente deve poter verificare.

### Step 3: Simulazione

**Pattern A — Consumare zainetto in scadenza (within broker)**: per ogni anno di zainetto in scadenza prossima (es. minus 2021 che scadono 31/12/2025), identificare plus latenti in `reddito_diverso` **dello stesso broker** che potrebbero essere realizzate per assorbire.

```
per ciascun broker:
    per minus_in_scadenza in zainetto[broker]:
        candidati = posizioni[broker] con plus_latente > 0 AND categoria = reddito_diverso
        per candidato in candidati (ordinati per fit):
            # Applica coefficiente se aliquote diverse
            se aliquota(minus) == aliquota(candidato):
                compensazione_nominale = min(minus.importo_residuo, plus_latente)
                risparmio_fiscale = compensazione_nominale × aliquota(plus)
            altrimenti:
                # Vedi references/aliquote-12-5-26.md per formule complete
                applica coefficiente 0,48077 nella direzione appropriata
            costo_operativo = commissioni + (Tobin 0,20% se azione IT > €500M cap su mercato regolamentato; 0 se ETF/fondo/obbligazione)
            impatto_netto = risparmio_fiscale - costo_operativo
            proporre se impatto_netto > soglia_minima
```

**Pattern B — Creare zainetto da posizioni in perdita**: per ogni posizione con plus_latente < 0 in `reddito_diverso`, valutare realizzo + (eventuale) riacquisto.

⚠️ Se la posizione in perdita è un ETF UCITS armonizzato, applicare avviso speciale: la minus è generata, ma il riacquisto dello stesso ETF (o di un sostituto UCITS armonizzato) creerà plus future *non compensabili* con la minus appena creata. Quindi la creazione di zainetto da ETF armonizzati ha senso solo se l'utente ha (o avrà) plus su strumenti reddito diverso.

**Pattern C — Non fare niente è una scelta**: se i costi operativi superano i risparmi fiscali, segnalarlo chiaramente e raccomandare di non operare. Bias verso il consigliare di NON fare trade è preferibile al contrario.

**Pattern D — Passaggio a regime dichiarativo (solo se multi-broker)**: se l'analisi rileva minus inutilizzabili presso un broker e plus tassabili presso un altro (situazione cross-broker), valutare se conviene optare per dichiarativo per l'anno successivo.

```
se numero_broker > 1:
    # l'opzione vale dal 1/1 dell'anno successivo: le minus che scadono quest'anno non contano
    zainetto_utile = minus con anno_scadenza > anno_corrente (somma cross-broker, per aliquota)
    compensazione_amministrato = parte di zainetto_utile che ogni broker compensa da sé (Pattern A)
    compensazione_consolidata = min(zainetto_utile, plus_compensabili_cross_broker)   # 0,48077 se aliquote diverse
    delta_risparmio_dichiarativo = (compensazione_consolidata - compensazione_amministrato) × aliquota
    costo_dichiarativo = costo_commercialista_stimato (~€200-500) + onere_personale
    se delta_risparmio_dichiarativo > costo_dichiarativo + soglia_sicurezza (~€500):
        proporre il dichiarativo nel confronto a tre con il Pattern E (sezione 4 dell'output), non come automatismo
        ricordare scadenza opzione (di solito 31/12 anno precedente)
        verificare che l'intermediario accetti il regime dichiarativo
        ricordare irrevocabilità per anno
```

L'opzione per il dichiarativo, come la revoca dell'amministrato, ha effetto dal periodo d'imposta successivo (art. 6 c. 2 D.Lgs. 461/97 → art. 306 c. 3 TU 2027): le minus che scadono il 31/12 dell'anno in corso non si salvano così. Per quelle, e quando un broker non ha più ragione di restare aperto, confrontare il Pattern E. Nel costo del dichiarativo va messo anche il calcolo operazione per operazione, con il LIFO e i cambi del giorno. Il cambio in sé non è un costo del dichiarativo: la plus fiscale si calcola in euro al cambio del giorno di acquisto e di vendita (art. 9 c. 2 TUIR) in entrambi i regimi, e in dichiarativo cambia solo chi la calcola. Con liquidità in valuta oltre €51.645,69 per almeno sette giorni lavorativi continui diventano tassabili anche gli utili su cambi (art. 67 c. 1-ter TUIR, dal 2027 nell'art. 76 D.Lgs. 117/2026; vedi `references/regime-dichiarativo.md`).

**Pattern E — Consolidamento via certificazione (chiusura del rapporto)**: se un broker ha minus che lì non troveranno plus compensabili (tipico: un dossier fermo, senza posizioni in plus), chiudere il rapporto le sposta invece di lasciarle evaporare. Alla chiusura del rapporto, o alla revoca dell'opzione per l'amministrato, l'intermediario rilascia una **certificazione** delle minus residue (art. 6 c. 5 D.Lgs. 461/97 → art. 306 c. 6 TU 2027). Le minus certificate si usano:
- su **un altro rapporto in amministrato intestato agli stessi soggetti** (con le cointestazioni gli intestatari devono coincidere), consegnando la certificazione al nuovo intermediario;
- oppure in dichiarazione, nel quadro RT (righi delle «eccedenze di minusvalenze certificate dagli intermediari»).

La scadenza resta quella originaria, il quarto anno successivo a quello di realizzo: la certificazione non azzera il contatore.

```
per broker_destinazione (stessi intestatari) con plus latenti reddito_diverso:
    capienza = max(0, plus_compensabili_destinazione − zainetto_destinazione)   # plus non già coperte dal suo zainetto
    per broker_origine in ordine di scadenza delle minus (prima quelle che scadono prima):
        residuo_origine = minus che lì non troveranno plus entro la scadenza (dopo il consumo in loco, Pattern A)
        recuperabile = min(residuo_origine, capienza)   # 0,48077 se aliquote diverse
        risparmio = recuperabile × aliquota
        costo = chiusura e trasferimento titoli + stop dell'operatività + tempi di rilascio e caricamento
        se risparmio > costo e i tempi stanno nella scadenza (a fine anno spesso no):
            proporre la chiusura
            capienza −= recuperabile
```

Se più origini puntano alla stessa destinazione, le sue plus si dividono tra loro e non si contano due volte. Togliere dalla capienza lo zainetto che la destinazione ha già dà il recupero certo dell'anno: il resto dipende dalle plus future della destinazione.

Rispetto al Pattern D la certificazione, se la destinazione è un altro rapporto in amministrato, resta in amministrato (niente quadro RT, niente commercialista) ma richiede di chiudere un rapporto; il dichiarativo consolida senza chiudere nulla, ma vale dall'anno successivo e costa adempimenti. Il Pattern D resta la via quando non si vuole chiudere alcun rapporto. Prima di proporre la chiusura verificare con entrambi gli intermediari tempi e modalità di rilascio e di accettazione della certificazione. Confronto a tre su un caso pratico in `references/multi-intermediario.md`.

*Certificazione delle minus alla chiusura del rapporto (art. 6 c. 2 e c. 5 D.Lgs. 461/97 → art. 306 c. 3 e c. 6 D.Lgs. 117/2026; righi RT4, RT14, RT44 delle istruzioni Redditi PF 2026) — Verificato: 2026-10.*

Vedi `references/multi-intermediario.md` per dettagli, esempio numerico completo e checklist decisionale.

### Step 4: Calendario

Tabella scadenze ordinata cronologicamente:

| Data | Tipo | Importo/Posizione | Priorità | Note operative |
|---|---|---|---|---|
| 31/12/{anno corrente} | Deadline operativa | Tutti i trade dell'anno fiscale | Alta se zainetto in scadenza | T+2: ultima esecuzione utile ~27/12 (verificare con broker) |
| 31/12/{anno+0..4} | Scadenza zainetto | Importo specifico | Alta se anno corrente, decrescente | Da 1/1 successivo evapora |
| 30/6, 30/9 o 31/10 e 30/11 dell'anno dopo | Solo con un conto in dichiarativo | 30/6 (30/7 con +0,40%): saldo dell'imposta del quadro RT, senza acconti, e saldo e primo acconto IVAFE; invio del 730 (quadri T, M e W) entro il 30/9 o del Redditi PF (RT, RM e RW) entro il 31/10; 30/11: secondo acconto IVAFE | Alta | IVAFE con F24: 4043 il saldo, 4047 e 4048 gli acconti; il 31/10 slitta al primo giorno lavorativo |

Note operative da includere sempre:
- Settlement T+2 per la maggior parte degli strumenti: operare con almeno 2 giorni lavorativi di anticipo sul 31/12
- Cut-off broker: alcuni intermediari chiudono ordini prima del 31/12 (verificare comunicazioni cliente)
- Bollo titoli si calcola sul controvalore al 31/12: vendite tattiche di fine anno possono ridurre la base imponibile bollo (ma il ribasso intra-anno è minimo, raramente determinante)

## Formato output

Report in markdown, tre sezioni + (se applicabili) le sezioni 4 e 5 sul dichiarativo + disclaimer.

### 1. Stato attuale

**Per ciascun broker, tabella separata**:

`Broker: [nome]`

| ISIN | Descrizione | Q.tà | PMC | Prezzo | Plus/Minus latente | Categoria | Aliquota | Note |

**Zainetto fiscale per broker**:

| Broker | Anno realizzo | Importo residuo | Aliquota | Scade il | Urgenza |

**Riepilogo cross-broker** (se >1 broker):

| Metrica | Totale consolidato |
|---|---|
| Zainetto totale (26%) | €... |
| Zainetto totale (12,5%) | €... |
| Plus latenti compensabili (totale) | €... |
| Plus latenti non compensabili (cap) | €... |

### 2. Opportunità identificate

Suddivise per Pattern (A, B, C, D, E). Per ogni opportunità:

- **Pattern**: A (consumo zainetto), B (creazione zainetto), C (non operare), D (passaggio dichiarativo), E (chiusura con certificazione)
- **Broker**: quale intermediario coinvolto
- **Azione proposta**: trade specifico
- **Razionale fiscale**: cosa compensa cosa, applicazione coefficiente se cross-rate
- **Calcolo esplicito**: numeri verificabili dall'utente
- **Stima impatto netto**: risparmio fiscale − costi operativi
- **Caveat**: rischi specifici (T+2, ETF UCITS trap, cut-off broker)

### 3. Calendario d'azione

Tabella scadenze come sopra. Aggiungere riepilogo testuale del prossimo intervento critico ("La prossima scadenza è X il giorno Y, riguarda Z").

### 4. (Solo se multi-broker, con almeno un rapporto in amministrato) Decisione regime per anno prossimo

Sezione dedicata al confronto tra amministrato, chiusura con certificazione e dichiarativo:

| Scenario | Risparmio fiscale | Costi | Netto |
|---|---|---|---|
| Status quo (amministrato) | €... | €... | €... |
| Chiusura con certificazione (Pattern E) | €... | €... | €... |
| Passaggio dichiarativo | €... | €... | €... |
| **Delta** | | | **€...** |

Raccomandazione + scadenza per l'opzione (di solito 31/12 anno corrente per applicazione anno successivo).

### 5. (Solo con conti in dichiarativo) Adempimenti del dichiarativo

La checklist di `references/regime-dichiarativo.md` applicata ai conti dell'utente: quadri RT, RM e RW (o T, M e W nel 730), minus da indicare nell'anno di realizzo, IVAFE, scadenze. Plus e minus dei conti in dichiarativo sono indicative (LIFO e cambi del giorno da ricostruire).

### Disclaimer (obbligatorio in fondo)

> **Disclaimer**: questo report ha finalità informative e di pianificazione fiscale personale. Non costituisce consulenza fiscale, finanziaria o di investimento professionale. I calcoli sono basati sui dati forniti dall'utente e su regole fiscali generali del regime amministrato italiano vigenti alla data di redazione; per i conti in regime dichiarativo i numeri sono indicativi e la dichiarazione va verificata con un commercialista. Per situazioni specifiche (successioni, donazioni, residenza estera, partecipazioni qualificate, conferimento fondi pensione, trasferimento dossier inter-intermediario, regime impatriati, etc.) consultare un commercialista o consulente fiscale abilitato. Verificare sempre saldi, zainetto fiscale e cut-off operativi sul portale del proprio intermediario prima di operare. L'autore di questa skill e Anthropic non si assumono responsabilità per decisioni operative basate sull'output di questa skill.

## Anti-pattern (NON FARE MAI)

- ❌ Compensare cedole obbligazionarie o dividendi azionari con minus pregresse: **non si può** (categoria fiscale diversa).
- ❌ Compensare plus su ETF e fondi, armonizzati o no, con minus pregresse: **non si può** (la plus è reddito di capitale; per i non armonizzati extra UE/SEE va anche a IRPEF progressiva).
- ❌ Applicare regole wash sale (vincolo 30 giorni dal riacquisto): è normativa USA, **non esiste in Italia**.
- ❌ Assumere HIFO o Specific ID, o simulare sui lotti una vendita parziale in amministrato: la base è il **costo medio ponderato** (il LIFO vale solo in dichiarativo).
- ❌ Dimenticare il bollo titoli quando si valuta il rendimento netto di una strategia.
- ❌ Dare consigli su quale azione/ETF acquistare o vendere per ragioni di rendimento/rischio: la skill è **puramente fiscale**.
- ❌ Inventare numeri quando i dati non sono completi: chiedere all'utente.
- ❌ Trattare i broker come fungibili in amministrato: lo zainetto è **per-intermediario**. Mai proporre compensazioni cross-broker assumendo che avvengano automaticamente.
- ❌ Suggerire trasferimenti titoli pensando di "spostare anche lo zainetto" — il PMC si sposta, lo zainetto **resta sul broker originario** finché quel rapporto non viene chiuso (Pattern E).
- ❌ Dire che chiudendo il rapporto lo zainetto va perso: si chiede la **certificazione** (art. 6 c. 5 D.Lgs. 461/97 → art. 306 c. 6 TU 2027) e le minus restano utilizzabili su un altro rapporto con gli stessi intestatari, o in dichiarazione, fino alla scadenza originaria. Ma non proporre la chiusura senza aver verificato tempi, costi e accettazione della certificazione da parte del broker ricevente.
- ❌ Trattare gli ETF UCITS su titoli di Stato come "tassati al 12,5%": l'aliquota effettiva è **mista** (dipende dalla quota di NAV whitelist).
- ❌ Applicare il coefficiente di abbattimento 12,5/26 senza esplicitare il calcolo: l'utente deve poter verificare.
- ❌ Raccomandare il passaggio a dichiarativo senza quantificare il delta vs costi (commercialista, onere amministrativo).

## Riferimenti

- `references/etf-trap-redditi-capitale.md` — approfondimento con esempi numerici sulla trappola ETF UCITS armonizzati (asimmetria redditi diversi vs redditi di capitale)
- `references/aliquote-12-5-26.md` — gestione cross-rate, coefficiente di abbattimento 12,5/26, edge case ETF su titoli di Stato
- `references/multi-intermediario.md` — zainetto per intermediario, certificazione delle minus alla chiusura del rapporto, regime dichiarativo, confronto a tre su un caso pratico
- `references/regime-dichiarativo.md` — il regime **dichiarativo** per chi usa broker senza sostituto d'imposta italiano: lo stato dei broker esteri a ottobre 2026, i tre regimi a confronto (amministrato / dichiarativo / gestito), i quadri **RT** (plusvalenze, con il LIFO), **RM** (proventi di ETF esteri) e **RW** (monitoraggio + **IVAFE** 0,2%, 0,4% black list), il cambio del giorno e la soglia di €51.645,69 sulla liquidità in valuta, una checklist degli adempimenti, e soprattutto la **compensazione unificata** a livello di contribuente — che fa sparire la frammentazione dello zainetto per broker — più i criteri per scegliere il regime e gli adempimenti cripto (RW + IVCA)
- `references/import-dati-broker.md` — come portare i **dati reali** nella skill: perché un MCP "live" sui broker (Directa/Fineco/Trade Republic) è stato valutato e **scartato** (le API non danno lo zainetto, e darebbero credenziali a un tool), e come usare invece l'importatore dei report esportati. Istruzioni di export per ciascun broker, mappatura tollerante dei formati, limiti onesti del pilota
- `assets/importa-estratto-broker.py` — l'**importatore**: ingerisce un estratto del portafoglio in CSV (che scarichi tu, senza credenziali in giro), calcola le plus/minus **latenti** per posizione, assegna categoria fiscale e aliquota (dalla colonna «tipo fiscale» o dalla descrizione; in dubbio «da classificare», mai reddito diverso per default) e, con un secondo CSV per lo zainetto, esclude le minus scadute, converte 12,5/26 nei due versi e calcola broker per broker quanta plus compensabile si può realizzare a **imposta zero**. `--anno`, `--broker`, `--json` per il JSON completo su file; numeri IT/EN decisi per file; solo libreria standard. Con `assets/esempio-estratto.csv` ed `esempio-zainetto.csv` come template di formato
- `references/dividendi-esteri.md` — dividendi esteri e doppia imposizione: ritenute alla fonte di sette Paesi con il prelievo totale, il 26% sul netto frontiera in amministrato (sul lordo in dichiarativo secondo l'AdE), W-8BEN e rimborsi esteri, il credito per le imposte estere (negato dall'Agenzia, aperture della Cassazione), ETF ad accumulazione o a distribuzione e azioni dirette
- `references/successione-donazione.md` — costo per gli eredi pari al valore di successione e per i donatari pari al costo del donante, fondi ed ETF come caso a parte, zainetto che si estingue col decesso, aliquote e franchigie dopo il D.Lgs. 139/2024, il confronto «vendo in decumulo o lascio in eredità»
- `references/criptovalute.md` — fiscalità delle cripto-attività (2026): aliquota 33% (26% per EMT-euro MiCA), il compartimento separato delle minusvalenze (solo cripto con cripto), eventi tassabili e neutri, costo medio ponderato in amministrato e LIFO in dichiarativo (per le cripto lo indica la Circ. 30/E/2023, non la legge), monitoraggio RW e imposta sul valore 0,2%, il regime amministrato cripto (possibile dal 2023), le leve (rivalutazione, harvesting) e i punti controversi
- `references/criptovalute-avanzate.md` — i temi cripto avanzati e meno consolidati: DeFi (staking/lending/yield: momento impositivo alla percezione, lordo, deposito lending non imponibile), liquidity pool e LP token (ingresso/uscita come permuta potenzialmente imponibile), airdrop e fork (la questione dell'onerosità), mining occasionale vs professionale, NFT secondo il ruolo (investitore 33% vs creatore IRPEF; scambio NFT/NFT), e il **ravvedimento operoso** per regolarizzare il pregresso (due violazioni distinte RW e RT, frazioni di sanzione, anno per anno; la finestra DAC8; la soglia penale €50.000)
- `references/criptovalute-casi-speciali.md` — i casi di confine: trasferimenti, **bridge e wrapping** (trasferimento neutro vs permuta, interpello 135/2025); cripto in **impresa/P.IVA** (art. 110 TUIR per IRES, esenzione IVA Hedqvist, il forfettario che investe in cripto senza cumulo), **mining** e cripto come **compenso**; i **neo-residenti** e la flat tax €100.000 sui redditi esteri (con la questione aperta della fonte delle cripto); **successione e donazione** (territorialità, costo di carico per eredi/donatari, la documentazione che evita il costo zero, l'accesso alle chiavi)
- **Vedi anche** `it-pianificazione/references/integrazione-fiscale-joint.md` — pattern fiscali joint con la pianificazione pensionistica: quando deduzione fondo + realizzo plus si combinano (es. soglia scaglione IRPEF, sterilizzazione redditi alti €200k). Particolarmente rilevante per redditi tra €40k-€100k e per chi è prossimo a una soglia di scaglione 28k/50k/200k.
- **Vedi anche** `it-rebalance/references/coordinamento-zainetto.md` — come il ribilanciamento di fine anno sfrutta lo zainetto in scadenza: vendere posizioni sovrappesate in plus compensabile prima del 31/12 corregge il drift E usa minus che altrimenti evaporano.

## Note per l'iterazione

Questa è la versione 0.10 del PoC.

**v0.10** (corrente):
- **Freshness fiscale**: le reference con dati normativi (aliquote 26/12,5, trappola ETF, regime dichiarativo) portano il marcatore `Verificato: AAAA-MM`, sorvegliato dalla test suite del plugin (fallisce oltre i 12 mesi).

**v0.9**:
- Primo **asset** della skill: l'**importatore di estratti broker** (`assets/importa-estratto-broker.py`), per lavorare sui dati reali del portafoglio. Calcola le plus/minus latenti per posizione, separa le minus latenti (candidate all'harvesting) dalle plus latenti, e incrocia con lo zainetto (secondo CSV) per evidenziare quanta plus si può realizzare a imposta zero. Parser **tollerante ai formati** (sinonimi colonne, numeri IT/EN, delimitatore auto): la sfida non è leggere un formato ma reggere la varietà tra Directa, Fineco e Trade Republic. Validato su due formati diversi più l'incrocio con lo zainetto; bug di collisione colonne trovato e corretto in fase di test.
- **MCP "live" sui broker: valutato ed escluso, con motivazione** (`references/import-dati-broker.md`). Verifica broker per broker: solo Directa ha un'API ufficiale (socket, richiede Darwin aperto in locale) e comunque non espone lo zainetto; Fineco e Trade Republic non hanno API retail. Il dato fiscale vive nei report esportabili, non nelle API — da cui la scelta dell'importatore di report invece del collegamento live (anche per non dare credenziali a un tool).

**v0.8**:
- Aggiunto il **regime dichiarativo** (`references/regime-dichiarativo.md`), il caso di chi usa broker esteri (Interactive Brokers, Degiro): i tre regimi a confronto (amministrato / dichiarativo / gestito), il quadro RT (plusvalenze) e RW (monitoraggio + IVAFE 0,2%, 0,4% black list), e il punto che più conta per l'ottimizzazione — in dichiarativo la **compensazione è unificata** a livello di contribuente, quindi la frammentazione dello zainetto per broker sparisce. Cifre 2026 verificate via web (IVAFE, bollo); la regola del quadro RW è stata poi corretta nella v0.10: nessuna soglia per titoli e cripto presso intermediari esteri, €15.000 solo per i conti. Il limite "non opera in dichiarativo" è stato di conseguenza ammorbidito.
- **Corretto un errore**: l'imposta di bollo sul dossier non ha tetto per le persone fisiche (il tetto di €14.000 vale solo per società ed enti). Allineato all'IVAFE estera (anch'essa 0,2%).

**v0.7**:
- Aggiunti i **casi speciali e soggetti particolari** cripto (`references/criptovalute-casi-speciali.md`), completando la copertura cripto del plugin su tre reference (base, avanzata, casi speciali). Dati 2026 verificati via web. Stessa onestà metodologica: i punti contesi (wrapping come permuta, fonte delle cripto per i neo-residenti) sono segnalati come aperti.
- **Trasferimenti, bridge, wrapping**: il principio dell'interpello 135/2025 (spostare cripto tra propri wallet non è realizzo, se documentato; senza documentazione costo zero); bridge dello stesso token come trasferimento; wrapping (BTC→WBTC, ETH→stETH) come permuta "stessa funzione economica" — tesi prevalente non imponibile, ma token tecnicamente distinto e prassi assente, quindi caveat.
- **Cripto in impresa/P.IVA**: l'art. 110 TUIR (per le società le valutazioni di fine esercizio non concorrono a IRES/IRAP, tassazione al realizzo); l'esenzione IVA del cambio (Hedqvist C-264/14); il punto pratico del forfettario che investe in cripto (redditi diversi nel compartimento separato, nessun cumulo col reddito d'impresa, nessun impatto sul tetto); mining professionale vs occasionale; cripto come stipendio/compenso (reddito di lavoro a IRPEF, poi cessione separata).
- **Neo-residenti**: la flat tax art. 24-bis (€100.000/anno, €200.000 per i trasferimenti post-2024, +€25.000 per familiare), con la **questione aperta** della fonte (estera vs italiana) delle cripto, decisiva per capire se la flat tax le copre.
- **Successione e donazione**: riforma TUS (D.Lgs. 139/2024), cripto come beni mobili nell'attivo ereditario; territorialità (residente in Italia → tutto il patrimonio cripto anche estero); costo di carico per eredi/donatari; il rischio del **costo zero** senza documentazione (da trasmettere agli eredi); l'accesso alle chiavi private come problema di pianificazione. Descrizione YAML aggiornata.

**v0.6**:
- Aggiunti i **temi cripto avanzati** (`references/criptovalute-avanzate.md`): DeFi (staking/lending/yield, liquidity pool/LP token, impermanent loss), airdrop e fork (la questione dell'onerosità), mining occasionale vs professionale, NFT secondo il ruolo (investitore vs creatore), e il **ravvedimento operoso** per regolarizzare il pregresso (due violazioni RW/RT, frazioni di sanzione anno per anno, la finestra DAC8, la soglia penale €50.000).

**v0.5**:
- Aggiunto il **trattamento delle cripto-attività** (`references/criptovalute.md`): aliquota 33% dal 2026 (26% per gli e-money token in euro MiCA), il **compartimento separato** delle minusvalenze cripto (estende la tabella centrale: ora tre compartimenti — redditi di capitale, redditi diversi "tradizionali", redditi diversi "cripto"), eventi tassabili e neutri (con il punto controverso della permuta cripto-cripto trattato onestamente), costo medio ponderato in amministrato e LIFO in dichiarativo, monitoraggio RW e imposta sul valore 0,2%, il regime amministrato cripto (possibile dal 2023), e le leve (rivalutazione al 18%, harvisting intra-compartimento). Cripto rimosse dalle esclusioni.

**v0.4**:
- Aggiornamento Tobin tax 2026 (L. 199/2025): aliquote azioni raddoppiate (0,20% mercato regolamentato, 0,40% OTC); derivati invariati in misura fissa; chiarita l'esenzione ampia per ETF/fondi/obbligazioni che rende il retail in ETF sostanzialmente non impattato
- Aggiunto codice tributo F24 4058 e dettaglio soglia capitalizzazione €500M (lista Consob)

**v0.2-0.3**:
- Gestione aliquota 12,5% con coefficiente di abbattimento, multi-intermediario, regime dichiarativo come escape hatch

Da estendere in iterazioni successive:
- ✅ Modellazione del regime dichiarativo (quadro RT, quadro RW, IVAFE): coperta in `references/regime-dichiarativo.md` (principi, adempimenti, compensazione unificata); la compilazione operativa del Modello Redditi resta da commercialista
- ✅ MCP/collegamento broker: **valutato ed escluso** (le API non danno lo zainetto, richiederebbero credenziali a un tool); fatto invece il **pilota dell'importatore di estratti CSV** (`assets/importa-estratto-broker.py`). Estensione futura: parsing diretto dei PDF di certificazione, e supporto a più formati di export
- Validazione test cases con casi reali AdE
- Lista aggiornata delle principali azioni italiane > €500M cap (per auto-rilevare quando la Tobin tax si applica)
