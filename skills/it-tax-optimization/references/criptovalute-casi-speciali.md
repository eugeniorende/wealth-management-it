# Cripto: casi speciali e soggetti particolari

Terza e ultima reference cripto, sui **casi di confine** del regime base: quando l'asset si muove tra catene (bridge, wrapping), quando esce dal regime della persona fisica investitore (attività d'impresa, cripto come compenso), e quando cambia il soggetto passivo (neo-residente, erede o donatario). Sono situazioni in cui la regola standard di `criptovalute.md` non si applica direttamente, alcune con prassi consolidata e altre ancora aperte. Come sempre: non è consulenza, e questi casi richiedono un commercialista esperto.

## Trasferimenti, bridge e wrapping

Il principio guida, chiarito dalla **risposta a interpello AdE 135/2025**: spostare cripto **non** è di per sé un realizzo. Nel dettaglio:

- **Trasferimento tra propri wallet** (dallo stesso token, es. da Binance al proprio Ledger): **non è cessione imponibile**, a condizione di poter **documentare** che la destinazione è un wallet proprio (self-custodial o presso altro exchange intestato al contribuente). Senza documentazione, nel regime amministrato il costo può essere posto a **zero** e il trasferimento trattato come potenziale cessione. Le **commissioni** di trasferimento vanno tracciate.
- **Bridge cross-chain dello stesso token** (es. USDC da Ethereum ad Arbitrum, dove resta USDC): è concettualmente un trasferimento, non un realizzo.
- **Wrapping** (BTC→WBTC, ETH→stETH/wstETH): tecnicamente si crea un **token distinto** (un ERC-20 separato) che però rappresenta lo stesso sottostante **1:1**. La tesi prevalente — "permuta tra asset con la **stessa funzione economica**", quindi **non imponibile** — è ragionevole perché economicamente non si realizza nulla; ma il token è formalmente diverso e **manca una posizione AdE specifica**, quindi una lettura prudente la segnala come potenzialmente una permuta. La **fee** di wrapping/bridge è un costo. Attenzione: per i wrapper che maturano rendimento (stETH che fa rebasing), la **componente di staking reward** è un provento da detenzione a sé, tassabile (vedi `criptovalute-avanzate.md`), distinto dall'operazione di wrap.

In pratica: documentare ogni movimento (indirizzi di origine e destinazione, prova della proprietà, fee) è ciò che distingue un trasferimento neutro da una cessione presunta.

## Cripto in impresa, P.IVA e come compenso

Il regime dell'art. 67 c-sexies (33%, compartimento separato) vale per la **persona fisica fuori da attività d'impresa**. Fuori da lì cambia tutto:

- **Impresa / società (IRES)**: la riforma ha integrato l'**art. 110 TUIR** — in deroga alla regola generale, i componenti positivi e negativi che risultano dalla **valutazione** delle cripto a fine esercizio **non concorrono** al reddito IRES (e analogamente ai fini **IRAP**), a prescindere dall'imputazione a conto economico. In sostanza: per le società la tassazione segue il **realizzo**, non la rivalutazione di bilancio.
- **IVA**: il cambio fiat↔cripto è **esente IVA** (sentenza CGUE **Hedqvist, C-264/14**). Per un'impresa o un professionista che **accetta cripto come pagamento**, l'IVA segue il **bene o servizio** venduto (con la sua aliquota), mentre la cripto incassata è un mezzo di pagamento esente; la successiva cessione di quella cripto è un'operazione separata. Il ricavo è tassato come reddito d'impresa/lavoro autonomo al **valore in euro** al momento dell'incasso.
- **Forfettario che investe in cripto** (il caso del freelance che compra BTC su un exchange): i guadagni da cripto sono **redditi diversi** nel compartimento separato (33%, quadro RT) e **non fanno cumulo** con il reddito d'impresa forfettario, né concorrono al **tetto** del forfettario. Sono due sfere distinte: l'attività professionale forfettaria da una parte, l'investimento personale in cripto dall'altra.
- **Mining**: occasionale → reddito diverso; professionale/organizzato → **reddito d'impresa** (P.IVA, ATECO tipo 62.09.09, tassato **al momento del mining** e non alla vendita, con il problema del pro-rata IVA per attività esente). Vedi anche `criptovalute-avanzate.md`.
- **Cripto come stipendio o compenso**: il dipendente pagato in cripto (o che la riceve come fringe benefit) ha **reddito di lavoro dipendente** tassato a IRPEF al valore in euro alla percezione; il professionista pagato in cripto ha reddito di lavoro autonomo. In entrambi i casi quel valore diventa il **costo di carico** per la successiva cessione, che è poi operazione separata nel compartimento cripto.

## Neo-residenti: la flat tax sui redditi esteri (art. 24-bis TUIR)

Chi trasferisce la residenza fiscale in Italia non essendo stato residente per **9 dei 10 anni** precedenti può optare per il regime dei **neo-residenti**: un'**imposta sostitutiva forfettaria** su **tutti i redditi di fonte estera**, qualunque sia il loro ammontare, pari a **€100.000/anno** (elevata a **€200.000** per chi ha trasferito la residenza dopo l'aumento dell'estate 2024 — verificare l'importo applicabile al proprio caso), più **€25.000/anno** per ciascun familiare incluso. Vantaggi collegati: **esenzione** dall'imposta di successione e donazione sui beni **esteri**, e **riduzione/esonero** dal monitoraggio (Quadro RW) per i beni esteri coperti.

⚠️ **Punto cruciale e dibattuto per le cripto**: il regime copre i redditi di **fonte estera**, ma stabilire dove sia "**localizzata**" una cripto-attività — e quindi se i relativi proventi siano di fonte estera (coperti dalla flat tax) o italiana (tassati ordinariamente al 33%) — è una **questione aperta**, data la natura intrinsecamente delocalizzata delle cripto. Chi valuta questo regime per un patrimonio cripto rilevante deve farlo con un consulente specializzato proprio sulla qualificazione della fonte: è il fattore che determina se la flat tax si applica davvero ai guadagni cripto.

## Successione e donazione di cripto

La riforma del Testo Unico su successioni e donazioni (**D.Lgs. 139/2024**) ha sistemato la materia: le cripto-attività sono **assimilate ai beni mobili**, concorrono all'**attivo ereditario** e sono soggette all'**imposta di successione e donazione**.

- **Base imponibile**: il valore di mercato in euro alla data di **apertura della successione** o della **donazione**.
- **Territorialità**: se il de cuius o il donante era **residente in Italia**, l'imposta colpisce **tutto** il patrimonio cripto, **anche** quello su exchange esteri o hardware wallet. Se **non residente**, solo i beni riconducibili al territorio italiano — e le cripto su wallet/dispositivi esteri **restano fuori** per il principio di territorialità.
- **Costo di carico per eredi e donatari** (decisivo per le plusvalenze **future**, art. 68 co. 9-bis TUIR): in caso di **successione** il costo è il valore **definito o dichiarato ai fini dell'imposta di successione**; in caso di **donazione** è il **costo sostenuto dal donante** (quello che il donante avrebbe usato cedendo a titolo oneroso).
- ⚠️ **Documentazione = tutto**: se manca la prova del costo (interpello 135/2025), il costo è assunto **pari a zero** e l'**intera** plusvalenza futura è tassata. Conservare la documentazione di acquisto — e **trasmetterla agli eredi** — è ciò che evita di regalare al fisco l'intero controvalore alla successiva vendita.
- **Aliquote** (per grado di parentela): indicativamente 4% per coniuge e figli oltre la franchigia di €1.000.000 ciascuno, 6% per fratelli oltre €100.000, 6% per altri parenti, 8% per estranei. La riforma 2026 ha **abolito il coacervo** (le donazioni in vita non erodono più le franchigie della successione, trattate come comparti separati), introdotto l'**autoliquidazione**, ed escluso esplicitamente le **liberalità d'uso** (regali per matrimoni, compleanni) da tassazione.
- **Problema pratico (self-custody)**: gli eredi devono poter **accedere alle chiavi private**. Per le cripto in autocustodia, senza una pianificazione (un "testamento digitale" con le istruzioni di accesso conservate in modo sicuro), il patrimonio rischia di diventare **irrecuperabile** anche se fiscalmente dichiarato. La pianificazione successoria delle cripto è tanto tecnica quanto fiscale.

## Cosa rimane fuori / da verificare col commercialista

Anche qui la reference dà i principi e segnala le incertezze: la qualificazione della **fonte** per i neo-residenti, l'uso di **trust o holding** per detenere cripto, la **voluntary disclosure** di asset pregressi non dichiarati, il **pro-rata IVA** del mining professionale, le **convenzioni** contro le doppie imposizioni e i casi con elementi di internazionalità. Tutto richiede un professionista abilitato ed esperto del settore. La postura resta personale/educativa, con rinvio al commercialista.

Cross-reference: `criptovalute.md` (il quadro base) e `criptovalute-avanzate.md` (DeFi, NFT, ravvedimento). Insieme, le tre reference coprono la fiscalità cripto della persona fisica residente dal caso ordinario fino ai confini con impresa, internazionalità e passaggio generazionale.
