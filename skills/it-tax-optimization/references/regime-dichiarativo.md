# Regime dichiarativo: broker esteri, quadro RT e RW, IVAFE

Tutto il resto della skill assume il regime **amministrato**, dove l'intermediario italiano fa da sostituto d'imposta: trattiene il 26% a ogni realizzo, gestisce lo zainetto, e tu non dichiari nulla. Ma chi usa un **broker estero** senza sostituto d'imposta italiano (Interactive Brokers, Degiro) finisce nel regime **dichiarativo**: deve fare tutto da sé in dichiarazione. Trade Republic fa da sostituto d'imposta dal 30/1/2025 e Scalable Capital offre il regime amministrato in opzione dal 1/9/2026: verificare il regime attivo sul proprio conto (le cripto detenute su Trade Republic restano comunque da dichiarare). Questa reference copre quel caso — ed è importante perché cambia la logica stessa della compensazione minus/plus. Non è consulenza; per la compilazione effettiva serve un commercialista.

## I tre regimi a confronto

L'investitore italiano può trovarsi in uno di tre regimi:

- **Amministrato** (il default di questa skill): l'intermediario italiano trattiene l'imposta a ogni realizzo e gestisce lo zainetto. Comodo (zero adempimenti) ma con due limiti: lo zainetto è **per-intermediario** (non si compensa tra broker, vedi `multi-intermediario.md`) e l'imposta si paga **subito**, a ogni vendita.
- **Dichiarativo**: l'investitore calcola e dichiara plus/minus da sé nel **quadro RT** del Modello Redditi PF, e versa l'imposta con la dichiarazione. È obbligatorio con i broker esteri (nessun sostituto italiano) e opzionale con alcuni broker italiani.
- **Gestito** (risparmio gestito): per le gestioni patrimoniali, l'imposta si applica sul **risultato maturato** annuo (la variazione di valore del portafoglio, realizzata o no), non sul realizzato. Raro per il fai-da-te; lo si incontra con le gestioni patrimoniali bancarie. Qui le minus maturate compensano automaticamente all'interno della gestione.

## Il dichiarativo in pratica: due quadri

Chi è in dichiarativo ha **due adempimenti distinti**, entrambi a suo carico:

**Quadro RT — le plusvalenze (l'imposta sul reddito).** Si riportano le plus e minus realizzate nell'anno, si applicano le aliquote (26% ordinaria, 12,5% sui titoli di Stato white list) e si versa l'imposta. Le minus si compensano con le plus **all'interno del quadro**, e l'eccedenza si riporta avanti **4 anni** (come in amministrato), ma è il contribuente a tenerne traccia di anno in anno nel quadro RT. Aliquote, coefficiente 12,5/26 per le aliquote miste (vedi `aliquote-12-5-26.md`) e distinzione reddito diverso / reddito di capitale sono le stesse dell'amministrato (le distribuzioni degli ETF armonizzati restano reddito di capitale non compensabile, vedi `etf-trap-redditi-capitale.md`). Cambiano invece il metodo del costo, che in dichiarativo è il LIFO e non il costo medio ponderato dell'amministrato (vedi sotto), e *chi* fa il calcolo.

**Quadro RW — il monitoraggio e l'imposta patrimoniale.** Le attività finanziarie detenute all'estero vanno dichiarate nel quadro RW (o quadro W del 730, dal 2024) per il **monitoraggio fiscale** (art. 4 DL 167/1990). Per titoli, ETF, fondi e cripto presso un intermediario non residente l'obbligo vale **qualunque sia l'importo**. L'esonero sotto **€15.000** riguarda solo **depositi e conti correnti** esteri il cui valore massimo complessivo nel periodo d'imposta non supera la soglia, e anche allora il quadro va compilato se è dovuta l'IVAFE. Restano fuori i titoli tenuti tramite un intermediario residente che applica ritenute o imposte sostitutive. Dal 1/1/2027 la disciplina passa all'art. 58 del testo unico adempimenti e accertamento (D.Lgs. 141/2026), con la stessa soglia e la stessa esclusione. Sul valore si paga l'**IVAFE** (Imposta sul Valore delle Attività Finanziarie Estere), l'equivalente estero dell'imposta di bollo:
- aliquota ordinaria **0,2%** (2 per mille) sul valore di mercato al 31/12;
- maggiorata allo **0,4%** per attività detenute in Paesi **black list** (paradisi fiscali, DM 4.5.1999; la Svizzera è esclusa dal 2024);
- conti correnti esteri: imposta fissa **€34,20** se la giacenza media supera €5.000 (sotto, esente).

Punto chiave: l'IVAFE replica fedelmente l'imposta di bollo domestica (anch'essa 0,2%), quindi **usare un broker estero non comporta una patrimoniale più alta** — il carico è equivalente, cambia solo chi versa (tu via F24, non il broker). L'unica eccezione è il black list allo 0,4%. E l'IVAFE **non è dovuta** se un intermediario italiano fa comunque da sostituto (es. titoli esteri tenuti tramite banca italiana o fiduciaria residente): in quel caso si applica il bollo ordinario, e i due prelievi sono mutuamente esclusivi.

## Quali titoli si considerano venduti in dichiarativo: LIFO

Qui non c'è il costo medio ponderato dell'amministrato. In dichiarativo, per le plusvalenze delle lettere c), c-bis) e c-ter) dell'art. 67 TUIR (partecipazioni, titoli, quote di OICR, valute) «si considerano cedute per prime» le attività «acquisite in data più recente»: è il **LIFO** dell'art. 67 c. 1-bis TUIR (→ art. 76 c. 2 TU 2027), e le istruzioni del quadro RT chiedono il costo «calcolato sulla base del criterio L.I.F.O.». Servono quindi i lotti di ogni titolo, con data, quantità e prezzo. Esempio: 100 azioni comprate a €50 nel 2023 e 100 a €80 nel 2025; vendendone 100 a €90 nel 2026 si considerano cedute quelle del 2025, quindi la plus è €1.000. In amministrato, sul costo medio di €65, la stessa vendita darebbe €2.500. Per le cripto-attività (lettera c-sexies), che il comma 1-bis non richiama, il LIFO in dichiarativo lo prescrive la Circ. 30/E/2023, par. 3.2.1: vedi `criptovalute.md`.

## Il vero motivo per cui il dichiarativo conta nell'ottimizzazione: zainetto unificato

L'aspetto che interessa questa skill non è l'adempimento, è la **compensazione**. In amministrato lo zainetto è frammentato per intermediario: una minus al broker A non compensa una plus al broker B. In **dichiarativo la compensazione è unificata a livello di contribuente**: tutte le plus e le minus di natura "reddito diverso" confluiscono nello stesso quadro RT e si compensano tra loro, **a prescindere da dove sono state realizzate**.

Questo ribalta il problema multi-broker. La doppia ottimizzazione "dove realizzare la plus" di `multi-intermediario.md` e di `it-rebalance` (quale broker, quale tipo fiscale) serve proprio perché in amministrato la compensazione non attraversa i conti. In dichiarativo quel problema **sparisce**: una minus realizzata ovunque compensa una plus realizzata ovunque. Per chi ha il portafoglio sparso su più broker con zainetti incagliati, è la leva più potente — ed è esattamente il "delta vs amministrato" che la skill stima nell'aggregazione cross-broker.

Secondo vantaggio, minore: il **timing del pagamento**. In amministrato paghi a ogni realizzo; in dichiarativo paghi a saldo con la dichiarazione (giugno dell'anno successivo), quindi trattieni la liquidità nel frattempo e hai più controllo su *quando* l'imposta diventa dovuta nell'arco dell'anno.

## Quando conviene scegliere il dichiarativo

Non è una scelta libera per tutti: con i broker esteri è **obbligatorio**, con molti broker italiani non è nemmeno offerto. Dove è una scelta, i fattori a favore:

- **Portafoglio multi-broker con zainetti frammentati**: se hai minus incagliate presso un broker e plus tassabili presso un altro, il dichiarativo le fa compensare. È il caso d'uso principale (il "Pattern D" della skill). L'opzione vale dall'anno successivo, quindi non salva le minus che scadono nell'anno in corso: per quelle c'è la certificazione alla chiusura del rapporto (vedi `multi-intermediario.md`).
- **Già su broker esteri**: se usi Interactive Brokers o simili sei comunque in dichiarativo, tanto vale sfruttarne la compensazione unificata consolidando lì.

A sfavore: l'**onere dichiarativo** (calcolo di plus/minus operazione per operazione, cambi valuta, compilazione RT/RW) è reale e cresce con il numero di operazioni e di exchange — su storici complessi serve un commercialista o un software dedicato. E l'omissione del quadro RW ha **sanzioni** pesanti (dal 3% al 15% degli importi non dichiarati, raddoppiate per i black list), quindi il monitoraggio non è opzionale. Da considerare anche che il passaggio amministrato↔dichiarativo si esercita per intero e ha effetto sull'anno: va deciso con anticipo, non a fine anno.

## Cripto e quadro RW

Le cripto vanno nel **quadro RW** qualunque sia l'importo, perché l'art. 4 DL 167/1990 le nomina espressamente e la soglia di €15.000 vale solo per i conti: se detenute su exchange esteri o su wallet personali (non presso un intermediario italiano che applichi il bollo), si dichiarano e scontano l'**imposta sul valore delle cripto-attività** (ICA/IVCA), anch'essa **0,2%**, mutuamente esclusiva col bollo. Le plusvalenze cripto restano un compartimento separato a sé (33% dal 2026, vedi `criptovalute.md`): il dichiarativo non le fa compensare con azioni o ETF, neanche a zainetto unificato. Il ravvedimento per RW cripto omessi negli anni passati è in `criptovalute-avanzate.md`.

## In sintesi

Il dichiarativo è il regime di chi usa broker esteri, e il suo vantaggio fiscale vero è la **compensazione unificata** (lo zainetto non è più prigioniero del singolo broker), al prezzo di doversi gestire RT, RW e IVAFE da sé. La patrimoniale (IVAFE 0,2%) è equivalente al bollo italiano, salvo il black list allo 0,4%. Per il resto le regole sostanziali — aliquote, compensazione a 4 anni, reddito diverso vs capitale — sono quelle del regime amministrato trattate nel resto della skill, salvo il metodo del costo, che in dichiarativo è il LIFO e non il costo medio ponderato.

---
*Dati normativi (regole del regime dichiarativo e zainetto fiscale) — Verificato: 2026-06.*
*LIFO in dichiarativo (art. 67 c. 1-bis TUIR, art. 76 c. 2 D.Lgs. 117/2026; istruzioni del quadro RT, Redditi PF 2026; per le cripto Circ. 30/E/2023 par. 3.2.1) — Verificato: 2026-10.*
*Quadro RW: obbligo per titoli e cripto senza soglia, esonero dei soli conti fino a €15.000, IVAFE e sanzioni (art. 4-5 DL 167/1990, istruzioni Redditi PF 2026 e 730/2026) — Verificato: 2026-10.*
