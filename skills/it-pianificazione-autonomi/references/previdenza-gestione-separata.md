# Previdenza obbligatoria per autonomi: Gestione Separata e casse

## La Gestione Separata INPS

Istituita dalla Legge 335/1995 (riforma Dini), è la gestione previdenziale per i lavoratori autonomi e parasubordinati **privi di una cassa professionale di categoria**. Copre la maggioranza dei freelance moderni: consulenti, sviluppatori software, grafici, formatori, copywriter, project manager, e in generale ogni P.IVA "senza albo con cassa".

### Chi deve iscriversi

- Professionisti con P.IVA **non iscritti ad albi con cassa propria** (consulenti, sviluppatori software, grafici, formatori, psicologi non iscritti ad albo, ecc.)
- Co.co.co. e figure assimilate (amministratori di società, sindaci, revisori)
- Lavoratori autonomi occasionali con compensi > €5.000/anno
- Professionisti iscritti ad albo ma **non iscrivibili alla cassa** o non tenuti al versamento (es. ingegnere che fa anche altro)

I **forfettari senza cassa** si iscrivono alla Gestione Separata e versano con le sue aliquote.

### Parametri 2026 (Circolare INPS n. 8 del 3/02/2026)

| Categoria | Aliquota 2026 |
|---|---|
| Professionisti senza altra copertura | **26,07%** (25% IVS + 0,72% assistenziali + 0,35% ISCRO) |
| Professionisti pensionati o con altra copertura | **24%** (solo IVS) |
| Co.co.co. senza altra copertura (con DIS-COLL) | 35,03% |
| Co.co.co. senza altra copertura (senza DIS-COLL) | 33,72% |

- **Massimale 2026**: €122.295 (era €120.607 nel 2025; cresce ogni anno con ISTAT). Oltre questa soglia di reddito non si versano contributi e non si matura ulteriore montante.
- **Minimale 2026**: €18.808. Sotto questa soglia di reddito non si accredita l'intero anno contributivo, ma un numero di mesi proporzionale ai contributi versati.
- **Nessun contributo minimo fisso**: si paga solo sul reddito effettivo. Se il reddito è zero, i contributi sono zero. Questa è una differenza fondamentale rispetto ad artigiani e commercianti (che hanno contributi fissi dovuti a prescindere).
- **Codice tributo F24**: 1299 (professionisti senza cassa)
- **Versamento**: integralmente a carico del professionista, con saldo e acconti alle scadenze fiscali (per il 2026 prorogate al 20 luglio con D.L. 89/2026)

### Base di calcolo dei contributi

```
se forfettario:
    base_contributiva = ricavi_incassati × coefficiente_redditività
se ordinario:
    base_contributiva = ricavi − costi_deducibili

contributi = min(base_contributiva, 122.295) × 0,2607
```

⚠️ I contributi della Gestione Separata si calcolano sul **reddito** (ricavi × coefficiente per i forfettari), non sul fatturato lordo. Un consulente che fattura €50.000 con coefficiente 78% versa sui €39.000 di reddito, non sui €50.000.

### Il sistema è contributivo puro

La pensione si calcola esattamente come per i dipendenti privati post-1995:

```
montante_contributivo = Σ (reddito_anno × 0,25) rivalutato (media PIL 5 anni)
# a montante va l'aliquota di computo, il 25% di IVS: lo 0,72% e lo 0,35% ISCRO
# del 26,07% versato finanziano altre prestazioni (Circ. INPS 8/2026)
pensione_lorda_annua = montante × coefficiente_trasformazione(età)
```

Per legge la rivalutazione segue il PIL nominale. In una proiezione in euro di oggi si usa il PIL reale (~0,5%), e il contributo dell'anno si rivaluta solo dall'anno dopo, come in `it-pianificazione/references/previdenza-obbligatoria.md`.

I **coefficienti di trasformazione sono gli stessi** dei dipendenti (sono fissati per legge a livello di sistema, non per categoria). Vedi la tabella ufficiale completa DM 20/11/2024 in `it-pianificazione/references/previdenza-obbligatoria.md`. A 67 anni = 5,608% per il biennio 2025-2026.

### La differenza che conta: aliquota di computo 25% vs 33%

Il dipendente accantona il **33%** del reddito (di cui la maggior parte a carico azienda). L'autonomo in Gestione Separata versa il **26,07%** (tutto a suo carico), di cui va a montante il **25%** di IVS.

A parità di reddito, l'autonomo accumula un montante **circa il 24% più basso** del dipendente (25/33 = 0,76). Questo si traduce in una **pensione pubblica strutturalmente più bassa** a parità di reddito.

Esempio: reddito €40.000/anno per 35 anni.
- Dipendente (33%): contributo annuo €13.200 → montante e pensione più alti
- Autonomo (26,07%): contributo annuo €10.428, di cui €10.000 a montante → montante ~24% più basso → pensione ~24% più bassa

**Conseguenza**: per l'autonomo la previdenza complementare è ancora più necessaria che per il dipendente. Ma — paradosso del forfettario — senza il vantaggio fiscale della deduzione (vedi `fiscalita-forfettario.md`).

### Requisiti di accesso pensione (autonomi Gestione Separata)

Gli stessi dei dipendenti contributivi puri:
- **Vecchiaia**: 67 anni + 20 anni di contributi + importo soglia di 1× l'assegno sociale dal 2024 (€546,24 al mese nel 2026)
- **Anticipata contributiva**: 64 anni + 20 anni di contribuzione effettiva + pensione ≥ 3 volte l'assegno sociale (€1.638,72 al mese nel 2026; 2,8 volte per le donne con un figlio, 2,6 con due o più)
- **Anticipata ordinaria**: a qualunque età, con 42 anni e 10 mesi di contributi (uomini) o 41 anni e 10 mesi (donne)
- Adeguamenti alla speranza di vita: nel 2027 vecchiaia a 67 anni e 1 mese, anticipata contributiva a 64 anni e 1 mese con 20 anni e 1 mese di contribuzione effettiva, anticipata ordinaria a 42 anni e 11 mesi (41 anni e 11 mesi per le donne); dal 2028 vecchiaia a 67 anni e 3 mesi, anticipata contributiva a 64 anni e 3 mesi con 20 anni e 3 mesi, anticipata ordinaria a 43 anni e 1 mese (42 anni e 1 mese per le donne) (Circ. INPS 28/2026, All. 2). Le anticipate decorrono tre mesi dopo la maturazione dei requisiti

⚠️ Per i contributivi puri (tutti gli autonomi iscritti dal 1996) l'anticipata a 64 anni richiede che la pensione maturata superi 3 volte l'assegno sociale. La L. 207/2024 aveva permesso di contare anche la rendita della previdenza complementare per raggiungere la soglia, ma la L. 199/2025 ha abrogato questa possibilità (Circ. INPS 19/2026): non è più un argomento a favore del fondo pensione. *(Requisiti 2026-2028 — Verificato: 2026-10.)*

## Le casse professionali (cenni)

Per i professionisti **iscritti a un albo con cassa**: ingegneri/architetti (Inarcassa), avvocati (Cassa Forense), medici/odontoiatri (ENPAM), commercialisti (CNPADC), consulenti del lavoro (ENPACL), geometri (CIPAG), notai, veterinari, farmacisti, ecc.

Ogni cassa ha struttura propria, ma in genere:
- **Contributo soggettivo**: percentuale sul reddito professionale, con un minimo annuo dovuto a prescindere
- **Contributo integrativo**: percentuale applicata in fattura (tipicamente 2-5%) e ribaltata sul cliente, destinata alla cassa
- **Contributo di maternità** e altri contributi minori
- **Sistema di calcolo della pensione**: variabile per cassa. Alcune sono passate al contributivo, altre mantengono quote retributive o sistemi misti/reddituali. NON è automaticamente il contributivo INPS.

⚠️ **La skill v0.1 non modella le singole casse in dettaglio.** Le regole, i minimi, i coefficienti e i sistemi di calcolo sono specifici di ogni cassa e cambiano nel tempo. Per un iscritto a cassa:
1. Fornire i principi generali (soggettivo + integrativo + sistema di calcolo proprio)
2. Rinviare al regolamento della cassa specifica e al sito della cassa
3. Suggerire una simulazione sul portale della cassa (molte offrono simulatori)
4. Rinviare a un consulente previdenziale per i casi specifici

Il focus della skill è la **Gestione Separata**, che copre la maggioranza dei freelance tech/digitali (sviluppo software e consulenza informatica non hanno un albo con cassa, quindi vanno in Gestione Separata).

## Il caso del doppio reddito (P.IVA + dipendente)

Frequente nel mondo tech: dipendente che ha anche una P.IVA per attività extra (consulenze, progetti personali).

- Se il dipendente apre P.IVA in Gestione Separata, e ha **già copertura come dipendente**, l'aliquota Gestione Separata scende al **24%** (no quota IVS piena, perché già coperto)
- I due montanti (FPLD da dipendente + Gestione Separata da P.IVA) si **cumulano** ai fini pensionistici (totalizzazione/cumulo gratuito)
- ⚠️ Attenzione alla **causa ostativa forfettario**: se il reddito da lavoro dipendente supera €35.000, non si può accedere al regime forfettario per la P.IVA
- Per la deducibilità del fondo pensione: avendo redditi IRPEF da lavoro dipendente, il contributo al fondo **torna deducibile** fino a capienza di quei redditi (vedi `fiscalita-forfettario.md`)

## Heuristic per la skill

1. **Identificare correttamente la gestione**: developer/consulente IT senza albo → Gestione Separata 26,07%. Avvocato/ingegnere/medico → cassa professionale (rinviare ai principi + cassa specifica).
2. **Aliquota corretta**: 26,07% per professionista senza altra copertura; 24% se ha altra copertura (es. anche dipendente) o è pensionato.
3. **Ricordare il massimale**: €122.295. Per redditi alti, la pubblica si appiattisce; segnalare che oltre il massimale serve la complementare.
4. **Nessun contributo minimo**: non assumere minimi per la Gestione Separata (a differenza di artigiani/commercianti).
5. **Coefficienti di trasformazione**: stessi dei dipendenti (tabella DM 20/11/2024 in `it-pianificazione/references/previdenza-obbligatoria.md`). Non duplicare, rinviare.
6. **Tasso di sostituzione più basso**: per via dell'aliquota di computo del 25%, evidenziare che l'autonomo ha una pensione pubblica più magra a parità di reddito → la complementare è più necessaria.
7. **Anzianità contributiva**: l'autonomo la verifica sull'estratto conto INPS (www.inps.it, area riservata con SPID, CIE o CNS: servizio "Estratto conto contributivo"). Se non disponibile, stimare ma flaggare.
8. **Rinvio al patronato/consulente**: per ricostruzione posizione, cumulo, totalizzazione, casse, sempre rinviare a professionista abilitato (servizi spesso gratuiti via patronato).
