---
name: it-pianificazione-autonomi
description: Pianificazione pensionistica per lavoratori autonomi e partite IVA italiane (regime forfettario e ordinario), iscritti alla Gestione Separata INPS o a casse professionali. Usa questa skill quando l'utente è un libero professionista, freelance, consulente, sviluppatore software con P.IVA, partita IVA forfettaria, autonomo senza cassa, o un professionista iscritto a un albo con cassa (ingegnere/architetto in Inarcassa, avvocato in Cassa Forense, medico in ENPAM, commercialista in CNPADC, psicologo in ENPAP, geometra in CIPAG, ecc.), e parla di: pensione da autonomo, Gestione Separata INPS, casse professionali, contributo soggettivo e integrativo, contributi minimi e massimale, deducibilità dei contributi cassa (anche in forfettario), contributi previdenziali partita IVA, coefficiente di redditività, imposta sostitutiva 15% o 5%, deducibilità contributi forfettario, fondo pensione per autonomi, "conviene il fondo pensione se sono forfettario?", quanto prenderò di pensione da freelance o da professionista, gap previdenziale autonomi. Trigger anche su confronto regime forfettario vs ordinario ai fini previdenziali. ATTENZIONE: per i forfettari il contributo volontario al fondo pensione NON è deducibile (regime sostitutivo, non IRPEF), mentre il contributo obbligatorio alla cassa o alla Gestione Separata SÌ — questo inverte la logica valida per i dipendenti. NON copre dipendenti privati (skill `it-pianificazione`) né dipendenti pubblici. NON sostituisce un commercialista o consulente previdenziale abilitato.
---

# it-pianificazione-autonomi

Skill per la pianificazione pensionistica di un lavoratore **autonomo / partita IVA** italiano. È la skill gemella di `it-pianificazione` (che copre i dipendenti privati), ma il regime previdenziale e fiscale è **strutturalmente diverso**, al punto che alcuni consigli validi per i dipendenti sono **invertiti** per gli autonomi.

## Il punto che cambia tutto: il fondo pensione per i forfettari

⚠️ **Questo è l'insight più importante e più frainteso dell'intera skill.**

Per un **dipendente** (skill `it-pianificazione`), versare al fondo pensione è quasi sempre conveniente perché il contributo volontario **deduce dall'IRPEF** (fino a €5.300/anno), generando un risparmio fiscale pari all'aliquota marginale (23-43%).

Per un **forfettario puro**, questo beneficio **NON esiste**. Il motivo:
- Il reddito forfettario è tassato con **imposta sostitutiva** (15%, o 5% i primi 5 anni), NON con IRPEF
- Il reddito forfettario **non concorre a formare il reddito complessivo IRPEF**
- La deduzione del fondo pensione (art. 10 TUIR) opera **solo** sul reddito complessivo IRPEF
- Quindi: un forfettario senza altri redditi IRPEF che versa €5.000 al fondo pensione ottiene **€0 di risparmio fiscale** dalla deduzione

Fonte: Modello Redditi PF 2026, quadro LM — i contributi versati volontariamente a un fondo pensione **non sono deducibili** per i forfettari (a differenza dei contributi INPS obbligatori, che invece lo sono).

**Implicazione pratica**:
- Il fondo pensione per un forfettario puro resta utile per la **capitalizzazione** e per la **tassazione agevolata della prestazione finale** (15→9%), ma perde il vantaggio della deduzione in ingresso — che è il motore principale della convenienza per i dipendenti.
- Per un forfettario, prima di versare al fondo pensione, va valutato se non sia altrettanto (o più) efficiente un investimento in un PAC di ETF sul dossier titoli ordinario, che ha più liquidità e flessibilità.

**Eccezione**: il forfettario che ha **anche altri redditi IRPEF** (es. affitti tassati IRPEF, un lavoro dipendente part-time, redditi occasionali) può dedurre il contributo al fondo pensione **fino a capienza di quei redditi IRPEF**. In quel caso una parte del vantaggio deduzione torna disponibile.

## Scope esplicito

**Cosa fa:**
1. **Proiezione previdenza obbligatoria** per Gestione Separata INPS (aliquota 26,07%) o casse professionali (struttura a due pilastri, principali casse, deducibilità anche in forfettario)
2. **Calcolo del reddito imponibile** in regime forfettario (coefficiente di redditività, deduzione contributi, imposta sostitutiva)
3. **Valutazione del fondo pensione** per autonomi, con la corretta analisi della (non) deducibilità
4. **Gap analysis tenore di vita**, coerente con la skill dipendenti ma con i parametri degli autonomi
5. **Confronto regime forfettario vs ordinario** ai fini previdenziali e fiscali

**Cosa NON fa:**
- ❌ Non copre lavoratori dipendenti privati → usa `it-pianificazione`
- ❌ Non copre dipendenti pubblici
- ❌ Non sostituisce il regolamento della singola cassa: dà il framework comune, i dati indicativi 2026 delle principali (Inarcassa, Cassa Forense, ENPAM, CNPADC, ENPAP, CIPAG) e le leve di pianificazione, ma coefficienti di trasformazione, riscatti, ricongiunzioni e casi particolari (STP, doppia iscrizione) vanno verificati con la cassa e un consulente
- ❌ Non fa la dichiarazione dei redditi né il calcolo definitivo dell'imposta: stima a fini di pianificazione
- ❌ Non sostituisce commercialista o consulente previdenziale

## I due mondi previdenziali dell'autonomo

### Mondo 1: Gestione Separata INPS

Per i professionisti **senza un albo con cassa propria**: consulenti, freelance, sviluppatori software, grafici, formatori, copywriter, e in generale tutte le P.IVA "senza cassa". È il caso più comune nel mondo tech/digitale.

**Parametri 2026** (Circolare INPS n. 8 del 3/02/2026):
- **Aliquota professionisti senza altra copertura: 26,07%** (25% IVS + 0,72% assistenziali + 0,35% ISCRO)
- Aliquota ridotta **24%** per chi è già pensionato o ha altra copertura previdenziale obbligatoria (es. P.IVA + lavoro dipendente)
- **Massimale 2026: €122.295** (oltre, non si versano contributi e non si matura ulteriore montante)
- **Minimale: €18.808** (sotto questa soglia di reddito non si accredita l'intero anno, ma mesi proporzionali)
- **Nessun contributo minimo fisso**: si paga solo sul reddito effettivo (differenza chiave rispetto ad artigiani/commercianti). Se il reddito è zero, i contributi sono zero.
- Base di calcolo: reddito professionale (per i forfettari, ricavi × coefficiente di redditività)
- Versamento: a carico del professionista, scadenze fiscali (saldo + acconti), codice tributo F24 1299

Il sistema è **contributivo puro**, identico a quello dei dipendenti: montante × coefficiente di trasformazione. La differenza sta nell'aliquota di accantonamento (26,07% vs 33% dei dipendenti) e nell'assenza del TFR.

### Mondo 2: Casse professionali

Per i professionisti **iscritti a un albo con cassa**: ingegneri/architetti (Inarcassa), avvocati (Cassa Forense), medici (ENPAM), commercialisti (CNPADC), psicologi (ENPAP), geometri (CIPAG), notai, veterinari, periti industriali, biologi, infermieri, ecc.

Struttura comune a (quasi) tutte le casse — due pilastri più un piccolo contributo di maternità:
- **Contributo soggettivo**: % sul reddito professionale netto, a carico del professionista, costruisce la pensione (montante). Ha un **minimo** dovuto anche con reddito basso/nullo e spesso un **massimale** di reddito. **È deducibile** (art. 10 TUIR), **anche in forfettario**.
- **Contributo integrativo**: tipicamente **4%** sul volume d'affari IVA, **addebitato in fattura al cliente** (pass-through): il professionista lo incassa e lo riversa, non incide sul suo netto, e **non è deducibile** (non è un suo costo). Dal 2013 molte casse ne accreditano una quota sul montante.

⚠️ **Il punto che si collega al forfettario**: il contributo *obbligatorio* alla cassa (soggettivo) è deducibile **anche in forfettario** (abbatte la base dell'imposta sostitutiva 5%/15%), a differenza del contributo *volontario* al fondo pensione complementare, che per il forfettario NON è deducibile. Sono due piani diversi (previdenza obbligatoria vs complementare).

Aliquote 2026 (indicative): Inarcassa 14,5% soggettivo + 4% integrativo; Cassa Forense 17% (18% dal 2027) + 4%; CNPADC dal 12% al 100% (a scelta) + 4%; ENPAM Quota A fissa + Quota B proporzionale (la più complessa). Diverse casse permettono di **versare di più** (aliquota volontaria) per costruire un montante maggiore — anch'esso deducibile. Le cifre cambiano ogni anno e vanno verificate sul sito della cassa.

Per il dettaglio (le due cornici normative 509/1994 e 103/1996, la tabella delle casse principali, il calcolo contributivo con montante e coefficiente, deroghe e agevolazioni under 35, le leve di pianificazione) vedi `references/casse-professionali.md`. Per i casi specifici (coefficienti, riscatti, ricongiunzioni, STP) resta il rinvio al regolamento della cassa e a un consulente.

## La fiscalità del forfettario (e perché conta per la pensione)

Il regime forfettario (L. 190/2014) determina il reddito così:

```
reddito_lordo_forfettario = ricavi_incassati × coefficiente_redditività
reddito_imponibile = reddito_lordo_forfettario − contributi_INPS_versati_nell'anno
imposta_sostitutiva = reddito_imponibile × aliquota (15% ordinaria, 5% primi 5 anni)
```

**Coefficiente di redditività** (per codice ATECO):
- Attività professionali, scientifiche, tecniche (include sviluppo software, consulenza IT, ATECO 62.x e 70-74): **78%**
- Commercio al dettaglio: 40%
- Commercio ingrosso: 40%
- Industrie alimentari: 40%
- Intermediari del commercio: 62%
- Servizi di alloggio e ristorazione: 40%
- Altre attività: 67%

Per un developer/consulente, il coefficiente tipico è **78%**: significa che il 78% dei ricavi è considerato reddito, il 22% è abbattimento forfettario per spese.

**Requisiti forfettario 2026:**
- Ricavi/compensi anno precedente ≤ **€85.000** (uscita immediata se si superano €100.000 in corso d'anno)
- Reddito da lavoro dipendente/pensione anno precedente ≤ **€35.000** (causa ostativa)
- Imposta sostitutiva **5%** i primi 5 anni se: nessuna attività nei 3 anni precedenti, non mera prosecuzione di lavoro dipendente/autonomo precedente

**Punti chiave per la pensione:**
1. I **contributi INPS obbligatori sono deducibili** dal reddito forfettario (unica deduzione ammessa) → ridurre l'imposta sostitutiva. Dimenticarli costa il 15% del loro ammontare in imposta non risparmiata.
2. Il **contributo volontario al fondo pensione NON è deducibile** (vedi sopra). Indicato erroneamente come deducibile è uno degli errori più comuni.
3. Il reddito forfettario **rileva** per i requisiti pensionistici (anzianità contributiva matura normalmente).

Vedi `references/fiscalita-forfettario.md` per esempi numerici completi e il confronto forfettario vs ordinario.

## Workflow operativo

### Step 1: Ingestion

Raccogliere:

**Profilo professionale:**
- `tipo_cassa` — Gestione Separata / cassa professionale (quale) / artigiani-commercianti
- `regime_fiscale` — forfettario / ordinario / forfettario 5% (primi 5 anni)
- `codice_ateco` o tipo attività (per il coefficiente di redditività)
- `coefficiente_redditivita` (se noto, altrimenti dedurre da attività: 78% per IT/professioni)

**Dati economici:**
- `ricavi_annui` (incassati, non fatturato)
- `crescita_ricavi_attesa` (default 2%/anno)
- `eta_corrente`, `eta_target_pensionamento` (default 67)
- `anni_anzianita_contributiva_correnti`
- `altri_redditi_irpef` (affitti IRPEF, lavoro dipendente part-time, ecc.) — **rilevante per la deducibilità del fondo pensione**

**Fondo pensione (se presente o in valutazione):**
- `montante_fondo_accumulato`
- `contributo_volontario_annuo` (valutandone la NON deducibilità se forfettario puro)
- `comparto`, `rendimento_netto`, `anni_partecipazione`

**Spese e obiettivi:**
- `spese_mensili_attuali`
- `fattore_riduzione_spesa` (default 0,78)

Se mancano dati critici (ricavi, tipo cassa, regime) → CHIEDERE, non inventare.

### Step 2: Calcolo previdenza obbligatoria (Gestione Separata)

```
# Base contributiva
se forfettario:
    reddito_lordo = ricavi × coefficiente_redditività
altrimenti (ordinario):
    reddito_lordo = ricavi − costi_effettivi

base_contributiva = min(reddito_lordo, massimale_122295)
contributi_annui = base_contributiva × 0,2607   # aliquota 26,07%

# Montante e proiezione (identico al sistema dei dipendenti)
montante_attuale ≈ anzianità × reddito_medio_storico × 0,2607
contributi_futuri = Σ proiezione fino a pensionamento
montante_finale = capitalizza con rivalutazione PIL
pensione_lorda = montante_finale × coefficiente_trasformazione(età)
```

⚠️ **Differenza chiave vs dipendenti**: l'aliquota di accantonamento è 26,07% invece di 33%. A parità di reddito, l'autonomo accantona **meno** del dipendente (≈21% in meno di montante), quindi a parità di reddito avrà una **pensione pubblica più bassa**. Questo rende la previdenza complementare ancora più importante per gli autonomi — ma senza il vantaggio fiscale della deduzione (per i forfettari).

### Step 3: Valutazione previdenza complementare (con la corretta analisi fiscale)

Per la meccanica generale dei fondi pensione (forme, comparti, tassazione finale 15→9%, anticipazioni) vale tutto ciò che è in `it-pianificazione/references/previdenza-complementare.md`. La **differenza cruciale** per gli autonomi:

```
beneficio_deduzione = contributo_volontario × aliquota_deduzione

dove aliquota_deduzione =
    se forfettario puro (no altri redditi IRPEF): 0%        ← NESSUN beneficio
    se forfettario + redditi IRPEF: aliquota IRPEF marginale, fino a capienza
    se regime ordinario: aliquota IRPEF marginale piena
```

Per il forfettario puro, il fondo pensione va valutato **solo** su:
- Capitalizzazione (rendimento netto del comparto, tassato 20%/12,5% come per tutti)
- Tassazione agevolata della prestazione finale (15→9%)
- Protezione patrimoniale e impignorabilità relativa

E confrontato onestamente con l'alternativa (PAC di ETF su dossier ordinario), che offre più liquidità. Vedi `references/fiscalita-forfettario.md` per il confronto numerico fondo pensione vs ETF per un forfettario.

### Step 4: Gap analysis tenore di vita

Identica metodologia di `it-pianificazione/references/proiezione-tenore-vita.md`. L'unica differenza è che il tasso di sostituzione pubblico dell'autonomo è strutturalmente più basso (per via dell'aliquota 26,07% vs 33%), quindi il gap tende a essere più ampio.

### Step 5: Raccomandazioni

Pattern specifici per autonomi:

- **Pattern A1 — Versare i contributi INPS regolarmente e per intero**: sono deducibili dal forfettario e costruiscono pensione. Non saltarli quando il fatturato cala (in Gestione Separata non c'è minimo, ma versare poco = montante basso).
- **Pattern A2 — Valutare onestamente il fondo pensione SENZA il falso mito della deduzione**: per il forfettario puro, confrontare fondo vs ETF/PAC a parità di importo, considerando liquidità, tassazione finale, costi.
- **Pattern A3 — Sfruttare i redditi IRPEF collaterali per la deduzione**: se l'autonomo ha affitti o altri redditi IRPEF, il fondo pensione deduce fino a capienza di quelli.
- **Pattern A4 — Considerare il passaggio a ordinario se conviene**: in alcuni casi (costi reali alti, necessità di dedurre), il regime ordinario può essere più efficiente — ma è una valutazione fiscale complessa, da fare con un commercialista.
- **Pattern A5 — Massimizzare la complementare proprio perché la pubblica è più magra**: l'autonomo ha più bisogno della complementare del dipendente, anche senza il vantaggio deduzione.

## Strumento operativo: il foglio di proiezione

`assets/proiezione-pensione-autonomi.xlsx` è il foglio di proiezione dedicato agli autonomi, analogo a quello dei dipendenti ma con le differenze del mondo autonomo. Sei fogli:

- **Input**: parametri (celle blu). Tipo di previdenza (Gestione Separata o cassa) e **aliquota contributiva** editabile — 26,07% per la Gestione Separata, o l'aliquota soggettiva della cassa (es. Inarcassa 14,5%, Forense 17%). Regime fiscale (forfettario/ordinario), coefficiente di redditività, fatturato, montante già accumulato, parametri del fondo pensione complementare. **Nessun TFR**.
- **Coefficienti**: tabella ufficiale DM 20/11/2024, con la nota che le casse possono usare coefficienti propri.
- **Previdenza**: proiezione del montante contributivo anno per anno → pensione obbligatoria lorda e tasso di sostituzione. Usa il coefficiente **proiettato** all'anno di pensionamento.
- **Fiscalità**: confronto **forfettario vs ordinario** dell'anno corrente, che rende esplicita la deducibilità: i **contributi obbligatori** si deducono in entrambi i regimi; il **versamento al fondo pensione** è deducibile **solo in ordinario** (in forfettario il risparmio fiscale in ingresso è ~zero, evidenziato in una riga dedicata).
- **Complementare**: accumulo del fondo pensione (rendimento netto dell'ISC), tassazione finale 15→9%, rendita stimata.
- **Riepilogo**: pensione obbligatoria + complementare, tasso di sostituzione totale, gap annuo/mensile, scenari.

Validare con `python /mnt/skills/public/xlsx/scripts/recalc.py <file>` (atteso `total_errors: 0`). Tutto in termini reali (euro di oggi). Il foglio Fiscalità è il punto in cui la regola centrale della skill — la deducibilità dei contributi obbligatori ma non del fondo pensione per il forfettario — diventa un numero che l'utente vede.

## Formato output

Report markdown in 5 sezioni (analogo a `it-pianificazione`):

1. **Stato attuale**: profilo professionale, regime, ricavi, reddito imponibile, contributi, anzianità
2. **Proiezione previdenza obbligatoria**: pensione lorda/netta attesa, tasso di sostituzione (evidenziare che è più basso per via dell'aliquota 26,07%)
3. **Valutazione previdenza complementare**: con l'analisi corretta della deducibilità (zero per forfettario puro), confronto fondo vs ETF
4. **Gap analysis tenore di vita**: con scenari conservativo/base/ottimistico
5. **Raccomandazioni**: pattern A1-A5 quantificati

### Disclaimer (obbligatorio in fondo)

> **Disclaimer**: questo report ha finalità informative di pianificazione personale. Non costituisce consulenza previdenziale, fiscale o di investimento professionale. Il regime forfettario, le aliquote della Gestione Separata, i coefficienti di redditività e la disciplina della deducibilità sono soggetti a modifiche con le Leggi di Bilancio annuali. Le regole delle casse professionali variano per ogni cassa e vanno verificate direttamente. La (non) deducibilità del fondo pensione dipende dalla situazione reddituale complessiva del contribuente e va verificata caso per caso. Per la dichiarazione dei redditi, la scelta del regime, l'iscrizione alla gestione corretta e i casi specifici, consultare un commercialista o consulente previdenziale abilitato.

## Anti-pattern (NON FARE MAI)

- ❌ **Dire a un forfettario che il fondo pensione "fa risparmiare tasse grazie alla deduzione"**: è FALSO per il forfettario puro. È l'errore più grave e comune. La deduzione opera sull'IRPEF, che il forfettario non paga.
- ❌ Applicare l'aliquota contributiva dei dipendenti (33%) agli autonomi: la Gestione Separata è 26,07%.
- ❌ Assumere il TFR per gli autonomi: non esiste. Il TFR è dei lavoratori dipendenti.
- ❌ Trattare tutte le casse professionali come la Gestione Separata: hanno regole proprie (alcune con quote retributive, minimi, contributo integrativo).
- ❌ Dimenticare che i contributi INPS obbligatori SONO deducibili dal forfettario (l'unica deduzione ammessa): non dedurli costa il 15% del loro ammontare.
- ❌ Assumere un contributo minimo per la Gestione Separata: non c'è (a differenza di artigiani/commercianti). Si paga solo sul reddito.
- ❌ Ignorare il massimale €122.295: oltre quella soglia non si versa né si matura montante. Per redditi alti, la pubblica si appiattisce e la complementare diventa critica.
- ❌ Promettere pensioni in valore nominale a 30+ anni come certezze: vale lo stesso disclaimer dei dipendenti, con incertezza aggiuntiva sulla continuità del reddito autonomo.
- ❌ Confondere ricavi e fatturato: i ricavi forfettari sono gli incassi effettivi (criterio di cassa), non il fatturato.
- ❌ Consigliare il regime ordinario o forfettario senza rinviare al commercialista: la scelta del regime è una valutazione fiscale complessa che dipende da costi reali, redditi collaterali, prospettive.

## Riferimenti

- `references/previdenza-gestione-separata.md` — Gestione Separata INPS in dettaglio, confronto con casse professionali, requisiti pensionistici per autonomi
- `references/casse-professionali.md` — le casse di previdenza dei professionisti: le due cornici (509/1994, 103/1996), i due pilastri (soggettivo deducibile + integrativo pass-through), la deducibilità del soggettivo anche in forfettario, minimi/massimali/deroghe, il calcolo contributivo (montante + coefficiente), la tabella delle principali casse con dati 2026, e le leve di pianificazione
- `references/fiscalita-forfettario.md` — regime forfettario, coefficienti, deducibilità contributi, la (non) deducibilità del fondo pensione, confronto fondo vs ETF per forfettari, esempi numerici
- `assets/proiezione-pensione-autonomi.xlsx` — foglio di proiezione previdenziale per autonomi (6 fogli: Input, Coefficienti, Previdenza, Fiscalità, Complementare, Riepilogo); aliquota 26,07%/cassa, no TFR, confronto forfettario vs ordinario con la deducibilità corretta
- **Riusa** (non duplica) le reference condivise di `it-pianificazione`:
  - `it-pianificazione/references/previdenza-complementare.md` — meccanica fondi pensione (forme, comparti, tassazione finale, anticipazioni): valida per tutti, autonomi inclusi
  - `it-pianificazione/references/proiezione-tenore-vita.md` — metodologia gap analysis e scenari: valida per tutti
- **Vedi anche** `it-pianificazione/references/integrazione-fiscale-joint.md` per l'interazione con eventuali redditi finanziari, e `it-tax-optimization` se l'autonomo ha un dossier titoli

## Note per l'iterazione

Questa è la versione 0.3 della skill (introdotta in v0.6 del plugin, estesa in v0.7.13).

In quest'iterazione:
- Focus su Gestione Separata (la maggioranza dei freelance tech/digitali)
- Regime forfettario e ordinario (cenni)
- Casse professionali trattate in dettaglio (`references/casse-professionali.md`)
- **Foglio Excel di proiezione dedicato agli autonomi** (`assets/proiezione-pensione-autonomi.xlsx`): aliquota 26,07%/cassa, no TFR, foglio Fiscalità con il confronto forfettario vs ordinario e la deducibilità corretta del fondo pensione

Roadmap:
- v0.4: gestione artigiani/commercianti (contributi fissi + variabili, riduzioni)
- v0.5: simulatore numerico del confronto forfettario vs ordinario ai fini previdenziali (oltre alla fotografia annua già nel foglio Excel)
- Possibile: dettaglio per singola cassa con i coefficienti di trasformazione e le regole di rivalutazione specifiche (ENPAM Quota A/B, casse 103/1996)
