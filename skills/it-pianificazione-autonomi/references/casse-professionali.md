# Casse professionali (previdenza privata dei professionisti)

Reference sulla previdenza obbligatoria dei professionisti iscritti a un albo con cassa propria — il "Mondo 2" della pianificazione da autonomo, alternativo alla Gestione Separata INPS. Le casse variano molto tra loro e le cifre cambiano ogni anno: questa reference dà il **framework comune** e i dati 2026 delle principali, ma il regolamento della singola cassa e un commercialista restano il riferimento ultimo. Non è consulenza.

## Chi è in una cassa (e chi no)

Chi esercita una professione iscritta a un **albo dotato di cassa** versa alla propria cassa, non all'INPS: ingegneri e architetti (Inarcassa), avvocati (Cassa Forense), medici e odontoiatri (ENPAM), dottori commercialisti (CNPADC), psicologi (ENPAP), geometri (CIPAG), consulenti del lavoro (ENPACL), notai, veterinari (ENPAV), periti industriali (EPPI), biologi (ENPAB), infermieri (ENPAPI), farmacisti (ENPAF), e i pluricategoriali (EPAP: agronomi, chimici, geologi, attuari). Chi non ha un albo con cassa — consulenti, freelance, sviluppatori, grafici, formatori — sta in **Gestione Separata** (vedi `previdenza-gestione-separata.md`): è il caso più comune nel mondo tech/digitale.

Due cornici normative:
- **D.Lgs. 509/1994**: le casse "storiche", privatizzate nel 1994 (Inarcassa, Forense, ENPAM, CNPADC, Notariato…). Tipicamente sistema misto retributivo/contributivo con pro-rata per chi ha anzianità.
- **D.Lgs. 103/1996**: le casse delle professioni che hanno avuto copertura obbligatoria nel 1996 (ENPAP, ENPAPI, EPAP, EPPI, ENPAB…). Sistema **interamente contributivo** dall'origine.

## I due pilastri del contributo

Quasi tutte le casse hanno la stessa struttura a due componenti (più un piccolo contributo di maternità/paternità fisso):

1. **Contributo soggettivo** — è il contributo previdenziale vero e proprio, **a carico del professionista**, calcolato in percentuale sul **reddito professionale netto**. È quello che costruisce la pensione (alimenta il montante contributivo). Esiste sempre un **minimo** dovuto anche con reddito basso o nullo, e spesso un **massimale** di reddito oltre il quale l'aliquota piena non si applica.
2. **Contributo integrativo** — una percentuale (tipicamente **4%**; 2% ENPAP, 5% CIPAG) applicata sul **volume d'affari IVA** e **addebitata in fattura al cliente** (la riga "cassa 4%" che si vede nelle parcelle). È un *pass-through*: il professionista lo incassa dal cliente e lo riversa alla cassa, quindi non incide sul suo netto. Storicamente finanziava la solidarietà/assistenza; dal 2013 molte casse ne accreditano **una quota sul montante individuale** del professionista (es. CNPADC riconosce il 37,5% dell'integrativo dal 2023).

## La deducibilità (il punto che conta per il forfettario)

Questo è il legame con il tema centrale della skill autonomi:

- Il **contributo soggettivo** (obbligatorio e anche quello volontario/facoltativo) è un **onere deducibile** dal reddito (art. 10 TUIR), come tutti i contributi previdenziali obbligatori. **È deducibile anche nel regime forfettario**: si sottrae dal reddito imponibile determinato con il coefficiente di redditività, *prima* di applicare l'imposta sostitutiva (5%/15%).
- Il **contributo integrativo NON è deducibile**: non è un costo del professionista (lo paga il cliente), quindi non riduce il suo reddito.

⚠️ **Distinzione cruciale rispetto al fondo pensione complementare**: per un forfettario, il contributo *volontario* al **fondo pensione** (pilastro 3) NON è deducibile (la deduzione opera sull'IRPEF, che il forfettario non paga su quel reddito — vedi il punto centrale della skill). Ma il contributo *obbligatorio* alla **cassa** (pilastro 1) **è** deducibile anche in forfettario. Sono due cose diverse: la cassa è previdenza obbligatoria e deducibile sempre; il fondo pensione è previdenza complementare volontaria, deducibile solo a fronte di reddito IRPEF. Il risparmio in forfettario è pari al contributo × aliquota sostitutiva (es. €10.000 di soggettivo × 15% = €1.500 di imposta in meno; o × 5% nei primi 5 anni).

## Minimo, massimale e l'opzione "versare di più"

- **Contributo minimo**: dovuto a prescindere dal reddito. Nel 2026 soggettivo più integrativo minimi valgono circa €920 per ENPAP, €3.145 per Cassa Forense, €3.635 per Inarcassa, €4.134 per CNPADC e €6.195 per CIPAG, più il contributo di maternità. Molte casse prevedono **deroghe** al minimo per redditi bassi (si versa la sola percentuale sul reddito effettivo, ma si riduce l'anzianità riconosciuta) e forti **riduzioni per gli under 35** nei primi anni (spesso esonero dai minimi per 5 anni).
- **Massimale di reddito**: l'aliquota piena del soggettivo si applica fino a un tetto, diverso per cassa: nel 2026 €147.300 per Inarcassa (oltre non si versa nulla), €131.800 per Cassa Forense (oltre il 3%), €209.300 per CNPADC, €183.550 per CIPAG (oltre il 3,5%); ENPAP usa il tetto della L. 335/1995. Nel foglio Excel il massimale è un tetto secco: per le casse con aliquota ridotta oltre il tetto è un'approssimazione.
- **Versare di più (leva di pianificazione)**: diverse casse permettono di **scegliere un'aliquota soggettiva più alta** per costruire un montante maggiore — CNPADC dal 12% al 100% del reddito, Cassa Forense un volontario aggiuntivo dall'1% al 20%, Inarcassa un facoltativo modulare dall'1% all'8,5%, ENPAP un'aliquota fino al 30%. Questo contributo extra è anch'esso **deducibile**. Per chi ha capacità di risparmio ed è in un regime dove la deduzione vale (ordinario, o forfettario con il beneficio al 5-15%), saturare l'aliquota può essere una leva previdenziale e fiscale insieme.

## Come si calcola la pensione

Per le casse 103/1996 e per le quote contributive delle 509/1994, la pensione segue il **metodo contributivo**: i contributi soggettivi versati si capitalizzano in un **montante**, rivalutato anno per anno (ogni cassa ha la propria regola di rivalutazione, spesso legata ai rendimenti del patrimonio o a indici come il PIL), e al pensionamento il montante viene moltiplicato per un **coefficiente di trasformazione** (che ogni cassa fissa autonomamente, e che decresce con l'aspettativa di vita — come per l'INPS). Alcune casse aggiungono **premialità**: accreditano sul montante un'aliquota "di computo" superiore a quella "di finanziamento" effettivamente versata (es. CNPADC).

Per chi ha anzianità nelle casse 509/1994 c'è una quota **retributiva** (pensione legata alla media dei redditi), in via di esaurimento con il pro-rata verso il contributivo. La sostenibilità di lungo periodo è una pressione reale: diverse casse stanno **alzando le aliquote** (es. Cassa Forense 16%→17%→18% tra 2025 e 2027) per garantire l'adeguatezza.

## Le principali casse — dati 2026 (verificati sui siti delle casse, ottobre 2026)

| Cassa | Professione | Soggettivo | Integrativo | Note |
|---|---|---|---|---|
| **Inarcassa** | ingegneri, architetti | **14,5%** fino a €145.550 sui redditi 2025 (€147.300 sui redditi 2026), niente oltre; min. €2.785 | **4%** sul volume d'affari (min. €850) | + facoltativo modulare dall'1% all'8,5%; chi si iscrive prima dei 35 anni, per 5 anni solari e comunque non oltre i 35, se il reddito non supera il reddito medio degli iscritti del biennio precedente (€46.306 per il 2025): soggettivo al 7,25% e minimi a un terzo (RGP art. 4.4, [regolamento](https://www.inarcassa.it/sites/default/files/legacy/documents/2024-12/Inarcassa_RGP.pdf)); maternità €65,50 (provvisoria). Verificato: 2026-10 ([inarcassa.it](https://www.inarcassa.it/articoli/contributi-gli-iscritti)) |
| **Cassa Forense** | avvocati | **17%** sui redditi 2026 (16% sui 2025, 18% dal 2027), fino a €131.800; 3% oltre; min. €2.790 | **4%** (min. €355) | + volontario dall'1% al 20%; minimi a metà nei primi 6 anni per chi si iscrive prima dei 35. Verificato: 2026-10 ([cassaforense.it](https://www.cassaforense.it/media/pkxmzmvw/tabella-contributi-minimi.pdf)) |
| **ENPAM** | medici, odontoiatri | Quota A **fissa** per età (2026: €304,73 sotto i 30 anni, €591,47 da 30 a 35, €1.109,92 da 35 a 40, €2.049,83 dai 40) + Quota B sul reddito libero-professionale: **19,5%** fino a €150.000, 1% oltre | incluso nella struttura | Quota B al 9,75% su richiesta (entro il 31/7) per convenzionati, iscritti INPS e pensionati di altri enti, automatica per i pensionati del Fondo generale; 2% per corsisti di medicina generale e intramoenia. Verificato: 2026-10 ([enpam.it](https://www.enpam.it/comefareper/pagare-i-contributi/contributi-per-la-libera-professione/aliquota-intera-quota-b/)) |
| **CNPADC** | dottori commercialisti | a scelta **dal 12% al 100%** del reddito, fino a €209.300; min. €3.180 | **4%** (min. €954) | 37,5% dell'integrativo a montante dal 2023 (25% dal 2013 al 2022); maternità €79,09. Verificato: 2026-10 ([cnpadc.it](https://www.cnpadc.it/la-cassa-per-me/contribuzione/quanto-quando-e-come-versare-i-contributi.html)) |
| **ENPAP** | psicologi | **10%**, a scelta fino al 30%; fino al tetto della L. 335/1995 (€120.607 sui redditi 2025); min. €856 | **2%** (min. €66) | cassa 103/1996, interamente contributiva; l'integrativo al 4% dal 2027 è deliberato ma non ancora approvato dai Ministeri. Verificato: 2026-10 ([enpap.it](https://www.enpap.it/come-fare-per/versare-i-contributi/)) |
| **CIPAG** | geometri | **20%** (2025-2026), 22% dal 2027, fino a €183.550; 3,5% oltre; min. €4.240 | **5%**, anche verso la PA (min. €1.955) | il 4% verso la PA valeva solo per le fatture 2015-2020; maternità €9. Verificato: 2026-10 ([cassageometri.it](https://www.cassageometri.it/contribuzione)) |

Le aliquote, i minimi, i massimali e i coefficienti **cambiano ogni anno** e sono fissati dalle singole casse: questi valori sono stati verificati a ottobre 2026 sulle pagine indicate in tabella e vanno **riverificati sul sito della cassa** ogni anno. Attenzione all'anno: alcune casse riferiscono aliquote e tetti all'anno in cui il reddito è prodotto, altre a quello in cui si versa. CNPADC (dottori commercialisti, Sez. A dell'albo) è cosa diversa da CNPR (ragionieri e periti commerciali). Per ENPAM in particolare la struttura Quota A + Quota B è complessa e va verificata caso per caso.

## Implicazioni di pianificazione

- **In forfettario**, ricordare la doppia logica: la **cassa** (soggettivo obbligatorio) è deducibile e abbatte l'imposta sostitutiva; il **fondo pensione** complementare no (salvo altri redditi IRPEF). Prima di versare al fondo pensione, un forfettario in cassa valuti se non sia più efficiente saturare l'aliquota soggettiva volontaria della cassa (deducibile) o investire in un PAC di ETF sul dossier (liquido e flessibile).
- **Il fondo pensione complementare resta possibile in aggiunta** alla cassa, per chi vuole un terzo pilastro: la sua deducibilità segue la regola IRPEF generale (fino a €5.300/anno, vedi `it-pianificazione/references/previdenza-complementare.md`), quindi conviene in regime ordinario, molto meno in forfettario puro.
- **Il gap previdenziale** dipende dalla cassa: chi versa solo i minimi per anni costruisce un montante modesto. Stimare la pensione attesa con la propria cassa e, se serve, integrare con l'aliquota volontaria o un fondo pensione è il cuore della pianificazione per un iscritto a cassa.
- **L'integrativo non è un costo né un risparmio**: è denaro del cliente che transita. Non va contato nel calcolo del proprio netto né tra i versamenti previdenziali "propri" (salvo la quota eventualmente accreditata a montante).

## Cosa rimane fuori / da verificare col commercialista

La skill dà i **principi comuni** e i dati 2026 verificati a ottobre 2026; non sostituisce il regolamento della singola cassa. Vanno verificati con la cassa e un consulente: gli importi esatti di minimi/massimali dell'anno, i coefficienti di trasformazione e le regole di rivalutazione specifiche, le agevolazioni under 35 e le deroghe, i riscatti (laurea, militare) e le ricongiunzioni tra gestioni diverse, la posizione di chi è **contemporaneamente** in cassa e Gestione Separata o lavoro dipendente, e i casi delle società tra professionisti (STP/STA). La pianificazione resta in postura personale/educativa, con rinvio al commercialista e a un consulente previdenziale.

Cross-reference: `previdenza-gestione-separata.md` (l'alternativa per chi non ha cassa), `fiscalita-forfettario.md` (come il reddito imponibile forfettario si calcola e dove entra la deduzione dei contributi), `it-pianificazione/references/previdenza-complementare.md` (il fondo pensione come terzo pilastro sopra la cassa), e la skill `it-pianificazione-obiettivi` per impostare la pensione come obiettivo dentro il piano complessivo.
