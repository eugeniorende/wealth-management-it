# Regime dichiarativo: broker esteri, quadro RT e RW, IVAFE

Tutto il resto della skill assume il regime **amministrato**, dove l'intermediario italiano fa da sostituto d'imposta: trattiene il 26% a ogni realizzo, gestisce lo zainetto, e tu non dichiari nulla. Ma chi usa un **broker estero** senza sostituto d'imposta italiano (Interactive Brokers, Degiro) finisce nel regime **dichiarativo**: deve fare tutto da sé in dichiarazione. Alcuni broker nati esteri hanno aperto una succursale italiana e offrono l'amministrato: lo stato di ciascuno è nella tabella qui sotto. Questa reference copre il dichiarativo a livello di principi e adempimenti: il motore di calcolo della skill (e l'importatore) resta sull'amministrato, e per la compilazione effettiva serve un commercialista. Non è consulenza.

## Indice

- I tre regimi a confronto
- Quali broker sono in dichiarativo (stato a ottobre 2026)
- Il dichiarativo in pratica: i quadri RT, RM e RW
- Quali titoli si considerano venduti in dichiarativo: LIFO
- Titoli in valuta: il cambio del giorno
- Liquidità in valuta: la soglia di €51.645,69
- Le minus vanno indicate nell'anno di realizzo
- Il vero motivo per cui il dichiarativo conta nell'ottimizzazione: zainetto unificato
- Quando conviene scegliere il dichiarativo
- Cripto e quadro RW
- Checklist degli adempimenti con un broker estero
- In sintesi

## I tre regimi a confronto

L'investitore italiano può trovarsi in uno di tre regimi:

- **Amministrato** (il default di questa skill): l'intermediario italiano trattiene l'imposta a ogni realizzo e gestisce lo zainetto. Comodo (zero adempimenti) ma con due limiti: lo zainetto è **per-intermediario** (non si compensa tra broker, salvo certificazione alla chiusura del rapporto: vedi `multi-intermediario.md`) e l'imposta si paga **subito**, a ogni vendita.
- **Dichiarativo**: l'investitore calcola e dichiara plus/minus da sé nel **quadro RT** del Modello Redditi PF (o nel quadro T del 730), e versa l'imposta con la dichiarazione. È obbligatorio con i broker senza sostituto d'imposta italiano (oggi Interactive Brokers e Degiro, vedi la tabella) e opzionale con alcuni intermediari italiani.
- **Gestito** (risparmio gestito): per le gestioni patrimoniali, l'imposta si applica sul **risultato maturato** annuo (la variazione di valore del portafoglio, realizzata o no), non sul realizzato. Raro per il fai-da-te; lo si incontra con le gestioni patrimoniali bancarie. Qui le minus maturate compensano automaticamente all'interno della gestione.

## Quali broker sono in dichiarativo (stato a ottobre 2026)

| Broker | Regime per i residenti in Italia | Da sapere |
|---|---|---|
| Interactive Brokers | Dichiarativo | Nessun sostituto d'imposta italiano: RT, RM, RW e IVAFE a carico tuo |
| Degiro | Dichiarativo | Come sopra |
| Trade Republic | Amministrato per i nuovi clienti dal 30/1/2025, con la succursale italiana e l'IBAN italiano | Chi ha aperto il conto prima verifichi nell'app il regime attivo. Per le cripto detenute su Trade Republic verificare nell'app o nel report fiscale se rientrano nell'amministrato: se no, vanno nei quadri RW e RT |
| Scalable Capital | Amministrato su richiesta dal 1/9/2026, con la succursale di Milano e l'IBAN italiano | Vale dall'attivazione: i periodi precedenti restano da dichiarare. Un cambio di regime successivo ha effetto dal 1° gennaio dell'anno dopo |

Fonti: comunicato stampa di Trade Republic del 30/1/2025 (azioni ed ETF; non dice nulla sulle cripto) e help center di Scalable Capital (ottobre 2026); per Interactive Brokers e Degiro nessun regime amministrato risulta offerto (fonti di settore, da riverificare sul sito del broker). Lo stato cambia: controllarlo sul proprio conto prima di ogni analisi.

Due conseguenze pratiche. In amministrato presso Trade Republic o Scalable lo zainetto è **per intermediario** e, finché il rapporto è aperto, non si compensa con le minus o le plus dichiarate per Interactive Brokers o Degiro; con la revoca dell'amministrato (Pattern D) o la chiusura del rapporto (Pattern E) le minus certificate vanno nei righi RT delle eccedenze certificate e compensano anche le plus dichiarate per quei broker. E le minus maturate in dichiarativo restano nel quadro RT, utilizzabili contro plus dichiarate entro il quarto anno: la norma regola solo il percorso dall'amministrato verso la dichiarazione o un altro rapporto (art. 6 c. 5 D.Lgs. 461/97 → art. 306 c. 6 TU 2027), non il contrario, quindi non entrano nello zainetto del nuovo rapporto in amministrato. Per i casi di passaggio (Scalable nel 2026) verificare con il broker.

**Prima di attivare l'amministrato** su Scalable o Trade Republic, controllare se ci sono minus nel quadro RT ancora riportabili. Dopo l'attivazione si usano solo contro plus dichiarate nel quadro RT, per esempio su un conto Interactive Brokers o Degiro: senza conti in dichiarativo scadono inutilizzate. Si possono consumare prima, realizzando plus compensabili finché il conto è ancora in dichiarativo.

## Il dichiarativo in pratica: i quadri RT, RM e RW

Chi è in dichiarativo ha più adempimenti, tutti a suo carico:

**Quadro RT — le plusvalenze (redditi diversi).** Si riportano le plus e minus realizzate nell'anno su azioni, obbligazioni, ETC ed ETN, derivati e valute, si applicano le aliquote (26% ordinaria, titoli di Stato white list computati al 48,08%) e si versa l'imposta. Le minus si compensano con le plus **all'interno del quadro**, e l'eccedenza si riporta avanti **4 anni** (come in amministrato), ma è il contribuente a tenerne traccia di anno in anno nel quadro RT. Aliquote, coefficiente 12,5/26 per le aliquote miste (vedi `aliquote-12-5-26.md`) e distinzione reddito diverso / reddito di capitale sono le stesse dell'amministrato. Cambiano invece il metodo del costo, che in dichiarativo è il LIFO e non il costo medio ponderato dell'amministrato (vedi sotto), e *chi* fa il calcolo. Nel quadro RT vanno anche le **minus da vendita di ETF e fondi**, che sono redditi diversi, anche se le loro plus vanno nel quadro RM: chi non le indica nell'anno di realizzo perde il riporto.

**Quadro RM — i proventi di ETF e fondi esteri.** Le distribuzioni e le **plusvalenze da vendita** di ETF e fondi UE/SEE armonizzati (o con gestore vigilato) sono reddito di capitale: se il broker estero non applica la ritenuta italiana vanno nel quadro RM, sezione II-A (rigo RM31), con l'imposta sostitutiva del 26%, e **non** compensano le minus del quadro RT (vedi `etf-trap-redditi-capitale.md`). I proventi degli OICR non armonizzati fuori da quelle condizioni vanno invece nel quadro RL e concorrono al reddito complessivo. Nel quadro RM vanno anche i **dividendi di azioni estere** incassati senza ritenuta italiana: secondo l'Agenzia il 26% si calcola sul lordo, non sul netto frontiera dell'amministrato (vedi `dividendi-esteri.md`).

**Quadro RW — il monitoraggio e l'imposta patrimoniale.** Le attività finanziarie detenute all'estero vanno dichiarate nel quadro RW (o quadro W del 730, dal 2024) per il **monitoraggio fiscale** (art. 4 DL 167/1990; dal 2027 art. 58 D.Lgs. 141/2026). Per titoli, ETF, fondi e cripto presso un intermediario non residente l'obbligo vale **qualunque sia l'importo**. L'esonero sotto **€15.000** riguarda solo **depositi e conti correnti** esteri il cui valore massimo complessivo nel periodo d'imposta non supera la soglia, e anche allora il quadro va compilato se è dovuta l'IVAFE. Restano fuori i titoli tenuti tramite un intermediario residente che applica ritenute o imposte sostitutive. Dal 1/1/2027 la disciplina passa all'art. 58 del testo unico adempimenti e accertamento (D.Lgs. 141/2026), con la stessa soglia e la stessa esclusione. Sul valore si paga l'**IVAFE** (Imposta sul Valore delle Attività Finanziarie Estere), l'equivalente estero dell'imposta di bollo:
- aliquota ordinaria **0,2%** (2 per mille) sul valore di mercato al 31/12;
- maggiorata allo **0,4%** per attività detenute in Paesi **black list** (paradisi fiscali, DM 4.5.1999; la Svizzera è esclusa dal 2024);
- conti correnti esteri: imposta fissa **€34,20** se la giacenza media supera €5.000 (sotto, esente).

Punto chiave: l'IVAFE replica fedelmente l'imposta di bollo domestica (anch'essa 0,2%), quindi **usare un broker estero non comporta una patrimoniale più alta** — il carico è equivalente, cambia solo chi versa (tu via F24, codice tributo 4043, non il broker). L'unica eccezione è il black list allo 0,4%. E l'IVAFE **non è dovuta** se un intermediario italiano fa comunque da sostituto (es. titoli esteri tenuti tramite banca italiana o fiduciaria residente): in quel caso si applica il bollo ordinario, e i due prelievi sono mutuamente esclusivi.

## Quali titoli si considerano venduti in dichiarativo: LIFO

Qui non c'è il costo medio ponderato dell'amministrato. In dichiarativo, per le plusvalenze delle lettere c), c-bis) e c-ter) dell'art. 67 TUIR (dal 2027 art. 76 c. 1 lett. d, e, f; partecipazioni, titoli, quote di OICR, valute) «si considerano cedute per prime» le attività «acquisite in data più recente»: è il **LIFO** dell'art. 67 c. 1-bis TUIR (→ art. 76 c. 2 TU 2027), e le istruzioni del quadro RT chiedono il costo «calcolato sulla base del criterio L.I.F.O.». Servono quindi i lotti di ogni titolo, con data, quantità e prezzo. Esempio: 100 azioni comprate a €50 nel 2023 e 100 a €80 nel 2025; vendendone 100 a €90 nel 2026 si considerano cedute quelle del 2025, quindi la plus è €1.000. In amministrato, sul costo medio di €65, la stessa vendita darebbe €2.500. Per le cripto-attività (lettera c-sexies, dal 2027 art. 76 c. 1 lett. i), che il comma 1-bis non richiama, il LIFO in dichiarativo lo prescrive la Circ. 30/E/2023, par. 3.2.1: vedi `criptovalute.md`.

## Titoli in valuta: il cambio del giorno

I corrispettivi e i costi in valuta estera si convertono in euro «secondo il cambio del giorno» in cui sono percepiti o sostenuti, o del giorno precedente più vicino (art. 9 c. 2 TUIR; dal 2027 art. 9 c. 2 D.Lgs. 117/2026): il costo al cambio del giorno di acquisto, il corrispettivo al cambio del giorno di vendita. La plusvalenza fiscale è quella **in euro**, e può avere segno opposto a quella in valuta.

Esempio: 100 azioni comprate a $100 con il cambio EUR/USD a 1,10 (costo €9.090,91) e vendute a $110 con il cambio a 1,25 (corrispettivo €8.800,00). In dollari è un guadagno di $1.000; in euro è una minus di €290,91, che va nel quadro RT. Al contrario, se il dollaro si rafforza si può avere una plus imponibile in euro anche con il prezzo in dollari fermo. Con un portafoglio in valuta il cambio entra quindi nell'imponibile, non solo nel rendimento.

## Liquidità in valuta: la soglia di €51.645,69

Sul broker estero la liquidità resta spesso in dollari. La cessione a pronti di valuta estera presa da depositi e conti correnti, e lo stesso **prelievo**, sono redditi diversi (art. 67 c. 1 lett. c-ter TUIR → art. 76 c. 1 lett. f TU 2027) solo se nel periodo d'imposta la giacenza in valuta di **tutti** i conti e depositi del contribuente, calcolata al cambio di inizio periodo, ha superato **€51.645,69 per almeno sette giorni lavorativi continui** (art. 67 c. 1-ter TUIR; dal 2027 art. 76 c. 3 D.Lgs. 117/2026). Sotto soglia gli utili su cambi della liquidità non sono tassati. Sopra soglia, in dichiarativo il costo della valuta è il cambio storico individuato con il LIFO (istruzioni del quadro RT). Soglia e regola non dipendono dal regime: con un conto in valuta presso un intermediario italiano in amministrato, chiedere all'intermediario se gli utili su cambi li gestisce lui o vanno dichiarati nel quadro RT.

Il giroconto nella stessa valuta tra due conti dello stesso intestatario, senza cambio e senza acquisto di prodotti finanziari, non è un prelievo fiscalmente rilevante (Ris. AdE 60/E del 9/12/2024). Per gli altri usi della valuta, per esempio l'acquisto di titoli in dollari con la liquidità del conto, la qualificazione va verificata con il commercialista.

## Le minus vanno indicate nell'anno di realizzo

In dichiarativo una minus si può riportare nei quattro anni successivi **a condizione che sia indicata nella dichiarazione dell'anno in cui è stata realizzata** (art. 68 c. 5 TUIR → art. 77 c. 6 TU 2027). Vale anche se in quell'anno non ci sono plus né imposta: chi salta il quadro RT dell'anno di realizzo perde il riporto. Lo stesso vale per le cripto (art. 68 c. 9-bis TUIR → art. 77 c. 11 TU 2027, vedi `criptovalute.md`). Le minus certificate da un intermediario italiano alla chiusura del rapporto o alla revoca dell'amministrato si riportano nei righi delle «eccedenze di minusvalenze certificate dagli intermediari» (RT4, RT14 e RT44 nelle istruzioni Redditi PF 2026).

## Il vero motivo per cui il dichiarativo conta nell'ottimizzazione: zainetto unificato

L'aspetto che interessa questa skill non è l'adempimento, è la **compensazione**. In amministrato lo zainetto è frammentato per intermediario: una minus al broker A non compensa una plus al broker B. In **dichiarativo la compensazione è unificata a livello di contribuente**: tutte le plus e le minus di natura "reddito diverso" confluiscono nello stesso quadro RT e si compensano tra loro, **a prescindere da dove sono state realizzate**.

Questo ribalta il problema multi-broker. La doppia ottimizzazione "dove realizzare la plus" di `multi-intermediario.md` e di `it-rebalance` (quale broker, quale tipo fiscale) serve proprio perché in amministrato la compensazione non attraversa i conti. In dichiarativo quel problema **sparisce**: una minus realizzata ovunque compensa una plus realizzata ovunque. Per chi ha il portafoglio sparso su più broker con zainetti incagliati, è una leva potente — ed è il "delta vs amministrato" che la skill stima nell'aggregazione cross-broker, da confrontare con la chiusura del rapporto con certificazione (Pattern E), che consolida restando in amministrato.

Secondo vantaggio, minore: il **timing del pagamento**. In amministrato paghi a ogni realizzo; in dichiarativo paghi a saldo con la dichiarazione (giugno dell'anno successivo), quindi trattieni la liquidità nel frattempo e hai più controllo su *quando* l'imposta diventa dovuta nell'arco dell'anno.

## Quando conviene scegliere il dichiarativo

Non è una scelta libera per tutti: con i broker senza sostituto d'imposta italiano è **obbligatorio**, con molti intermediari italiani non è nemmeno offerto. Dove è una scelta, i fattori a favore:

- **Portafoglio multi-broker con zainetti frammentati**: se hai minus incagliate presso un broker e plus tassabili presso un altro, il dichiarativo le fa compensare. È il caso d'uso principale (il "Pattern D" della skill), quando non si vuole chiudere il rapporto con le minus. L'opzione vale dall'anno successivo, quindi non salva le minus che scadono nell'anno in corso: per quelle c'è la certificazione alla chiusura del rapporto (vedi `multi-intermediario.md`).
- **Già con conti in dichiarativo**: con Interactive Brokers o Degiro le plus e le minus di quei conti si compensano già tra loro nel quadro RT, senza spostare nulla. Per portarci le minus di un rapporto in amministrato serve la certificazione, alla revoca dell'amministrato (Pattern D) o alla chiusura del rapporto (Pattern E).

A sfavore: l'**onere dichiarativo** (calcolo di plus/minus operazione per operazione con il LIFO, cambi del giorno, compilazione di RT, RM e RW) è reale e cresce con il numero di operazioni e di exchange — su storici complessi serve un commercialista o un software dedicato. E l'omissione del quadro RW ha **sanzioni** pesanti (dal 3% al 15% degli importi non dichiarati, raddoppiate per i black list), quindi il monitoraggio non è opzionale. Il passaggio amministrato↔dichiarativo, infine, si comunica entro la fine dell'anno e ha effetto dall'anno successivo (art. 6 c. 2 D.Lgs. 461/97 → art. 306 c. 3 TU 2027): va deciso con anticipo, e non salva le minus che scadono nell'anno in corso.

## Cripto e quadro RW

Le cripto vanno nel **quadro RW** qualunque sia l'importo, perché l'art. 4 DL 167/1990 (dal 2027 art. 58 D.Lgs. 141/2026) le nomina espressamente e la soglia di €15.000 vale solo per i conti: se detenute su exchange esteri o su wallet personali (non presso un intermediario italiano che applichi il bollo), si dichiarano e scontano l'**imposta sul valore delle cripto-attività** (ICA/IVCA), anch'essa **0,2%**, mutuamente esclusiva col bollo. Le plusvalenze cripto restano un compartimento separato a sé (33% dal 2026, vedi `criptovalute.md`): il dichiarativo non le fa compensare con azioni o ETF, neanche a zainetto unificato. Il ravvedimento per RW cripto omessi negli anni passati è in `criptovalute-avanzate.md`.

## Checklist degli adempimenti con un broker estero

- **Durante l'anno**: conservare per ogni operazione data, quantità, prezzo, commissioni e cambio del giorno; tenere separate le cripto.
- **Quale dichiarazione**: il 730 (quadri T, M e W, dal 730/2025) entro il 30/9, oppure il Redditi PF (quadri RT, RM e RW) entro il 31/10. Con il 730 e un sostituto d'imposta saldo e acconti passano dalla busta paga o dalla pensione.
- **Quadro RT** (T nel 730): plus e minus dell'anno, in euro e con il LIFO del dichiarativo, anche se l'anno chiude in perdita, comprese le minus da vendita di ETF e fondi; riporto delle minus dei quattro anni precedenti e di quelle certificate da intermediari italiani.
- **Quadro RM**: proventi e plus da vendita di ETF e fondi UE/SEE incassati senza ritenuta italiana, al 26%; i dividendi esteri.
- **Quadro RL**: proventi degli OICR non armonizzati fuori UE/SEE o senza gestore vigilato, che concorrono al reddito complessivo.
- **Quadro RW**: titoli, ETF, fondi e cripto presso intermediari esteri, qualunque sia l'importo; conti esteri oltre €15.000 di valore massimo o con IVAFE dovuta.
- **IVAFE**: F24 con codice tributo 4043 per il saldo e 4047 e 4048 per la prima e la seconda (o unica) rata d'acconto (Ris. AdE 27/E/2013), alle stesse scadenze dell'IRPEF; non si versa se non supera €12.
- **Scadenze**: entro il 30 giugno dell'anno successivo (30 luglio con lo 0,40% in più) il saldo dell'imposta del quadro RT, senza acconti, e il saldo e il primo acconto dell'IVAFE; entro il 30/11 il secondo acconto dell'IVAFE. Invio del 730 entro il 30 settembre o del Redditi PF entro il 31 ottobre, che nel 2026 slitta al 2 novembre perché il 31 è sabato.

## In sintesi

Il dichiarativo è il regime di chi usa broker senza sostituto d'imposta italiano, e il suo vantaggio fiscale vero è la **compensazione unificata** (lo zainetto non è più prigioniero del singolo broker), al prezzo di doversi gestire RT, RM, RW e IVAFE da sé, con i cambi del giorno. La patrimoniale (IVAFE 0,2%) è equivalente al bollo italiano, salvo il black list allo 0,4%. Per il resto le regole sostanziali — aliquote, compensazione a 4 anni, reddito diverso vs capitale — sono quelle del regime amministrato trattate nel resto della skill, salvo il metodo del costo, che in dichiarativo è il LIFO e non il costo medio ponderato, e la base del 26% sui dividendi esteri, che secondo l'Agenzia è il lordo e non il netto frontiera (vedi `dividendi-esteri.md`).

---
*Dati normativi (regole del regime dichiarativo e zainetto fiscale) — Verificato: 2026-06.*
*LIFO in dichiarativo (art. 67 c. 1-bis TUIR, art. 76 c. 2 D.Lgs. 117/2026; istruzioni del quadro RT, Redditi PF 2026; per le cripto Circ. 30/E/2023 par. 3.2.1) — Verificato: 2026-10.*
*Quadro RW: obbligo per titoli e cripto senza soglia, esonero dei soli conti fino a €15.000, IVAFE e sanzioni (art. 4-5 DL 167/1990, istruzioni Redditi PF 2026 e 730/2026; dal 2027 art. 58 D.Lgs. 141/2026, art. 67 D.Lgs. 173/2024, art. 168 D.Lgs. 123/2025) — Verificato: 2026-10.*
*Cambio del giorno (art. 9 c. 2 TUIR; dal 2027 art. 9 c. 2), valute (art. 67 c. 1 lett. c-ter e c. 1-ter TUIR, dal 2027 art. 76 c. 1 lett. f e c. 3; Ris. AdE 60/E/2024), riporto delle minus (art. 68 c. 5 TUIR, dal 2027 art. 77 c. 6), quadri RM e RT, IVAFE con codice 4043 e scadenze (istruzioni Redditi PF 2026, fasc. 2; scheda AdE sul Redditi PF 2026), passaggio di regime (art. 6 c. 2 e c. 5 D.Lgs. 461/97, dal 2027 art. 306 c. 3 e 6), corrispondenze nel D.Lgs. 117/2026 — Verificato: 2026-10.*
