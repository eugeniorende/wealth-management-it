# Cripto: casi speciali e soggetti particolari

Terza e ultima reference cripto, sui **casi di confine** del regime base: quando l'asset si muove tra catene (bridge, wrapping), quando esce dal regime della persona fisica investitore (attività d'impresa, cripto come compenso), e quando cambia il soggetto passivo (neo-residente, erede o donatario). Sono situazioni in cui la regola standard di `criptovalute.md` non si applica direttamente, alcune con prassi consolidata e altre ancora aperte. Come sempre: non è consulenza, e questi casi richiedono un commercialista esperto.

## Trasferimenti, bridge e wrapping

Il riferimento di prassi è la **risposta a interpello AdE 135/2025**, che riguarda il **regime amministrato**. Spostare cripto tra wallet propri non è di per sé una cessione, ma:

- **Trasferimento tra propri wallet** (stesso token, es. da Binance al proprio Ledger): l'exchange che applica l'amministrato è esonerato dal calcolare la plusvalenza **solo se** il cliente **documenta** che la destinazione è un wallet proprio; una semplice dichiarazione non basta. Il trasferimento verso rapporti intestati a **soggetti diversi** è trattato come **cessione** (art. 6 c. 6 D.Lgs. 461/1997). Per le cripto **in entrata** senza prova del costo, l'intermediario assume un costo **pari a zero** (art. 68 c. 9-bis TUIR). Le **commissioni** di trasferimento vanno tracciate.
- **Bridge cross-chain dello stesso token** (es. USDC da Ethereum ad Arbitrum, dove resta USDC): è concettualmente un trasferimento, non un realizzo. È la lettura prevalente, ma non c'è una fonte di prassi specifica: da verificare col commercialista.
- **Wrapping** (BTC→WBTC, ETH→stETH/wstETH): tecnicamente si crea un **token distinto** (un ERC-20 separato) che però rappresenta lo stesso sottostante **1:1**. Manca una posizione AdE specifica sul wrapping, ma la circ. **30/E/2023** considera non realizzativo lo scambio tra cripto-valute con la stessa funzione economica (es. ETH contro BTC): la tesi della **non imponibilità** è quindi coerente con la prassi. Poiché il token è formalmente diverso, conviene documentarlo e segnalarlo al commercialista. Diverso il caso della permuta cripto ↔ **e-money token**, che per l'AdE è fiscalmente rilevante. La **fee** di wrapping/bridge è un costo. Attenzione: per i wrapper che maturano rendimento (stETH che fa rebasing), la **componente di staking reward** è un provento da detenzione a sé, tassabile (vedi `criptovalute-avanzate.md`), distinto dall'operazione di wrap.

In pratica: documentare ogni movimento (indirizzi di origine e destinazione, prova della proprietà, fee) è ciò che distingue un trasferimento neutro da una cessione presunta.

## Cripto in impresa, P.IVA e come compenso

Il regime dell'art. 67 c-sexies (33%, compartimento separato) vale per la **persona fisica fuori da attività d'impresa**. Fuori da lì cambia tutto:

- **Impresa / società (IRES)**: la riforma ha integrato l'**art. 110 TUIR** (c. 3-bis; dal 2027 art. 119 c. 5 D.Lgs. 117/2026) — in deroga alla regola generale, i componenti positivi e negativi che risultano dalla **valutazione** delle cripto a fine esercizio **non concorrono** al reddito IRES (e analogamente ai fini **IRAP**), a prescindere dall'imputazione a conto economico. In sostanza: per le società la tassazione segue il **realizzo**, non la rivalutazione di bilancio.
- **IVA**: il cambio fiat↔cripto è **esente IVA** (sentenza CGUE **Hedqvist, C-264/14**). Per un'impresa o un professionista che **accetta cripto come pagamento**, l'IVA segue il **bene o servizio** venduto (con la sua aliquota), mentre la cripto incassata è un mezzo di pagamento esente; la successiva cessione di quella cripto è un'operazione separata. Il ricavo è tassato come reddito d'impresa/lavoro autonomo al **valore in euro** al momento dell'incasso.
- **Forfettario che investe in cripto** (il caso del freelance che compra BTC su un exchange): i guadagni da cripto sono **redditi diversi** nel compartimento separato (33%, quadro RT) e **non fanno cumulo** con il reddito d'impresa forfettario, né concorrono al **tetto** del forfettario. Sono due sfere distinte: l'attività professionale forfettaria da una parte, l'investimento personale in cripto dall'altra.
- **Mining**: per l'AdE (risposta **515/2022**, mining in regime d'impresa) è **fuori campo IVA**, perché manca un committente identificabile, e l'IVA sugli acquisti è **indetraibile**. Ai fini delle imposte dirette la ricompensa concorre al **reddito d'impresa** nel periodo in cui è conseguita, al cambio in euro del giorno: si tassa **al momento del mining**, non alla vendita. Per il mining occasionale della persona fisica non c'è una posizione AdE: da verificare col commercialista. Vedi anche `criptovalute-avanzate.md`.
- **Cripto come stipendio o compenso**: il dipendente pagato in cripto (o che la riceve come fringe benefit) ha **reddito di lavoro dipendente** tassato a IRPEF al valore in euro alla percezione; il professionista pagato in cripto ha reddito di lavoro autonomo. In entrambi i casi quel valore dovrebbe diventare il **costo di carico** per la successiva cessione, che è poi operazione separata nel compartimento cripto (interpretazione da verificare col commercialista).

## Neo-residenti: la flat tax sui redditi esteri (art. 24-bis TUIR, dal 2027 art. 246 D.Lgs. 117/2026)

Chi trasferisce la residenza fiscale in Italia non essendo stato residente per **9 dei 10 anni** precedenti può optare per il regime dei **neo-residenti**: un'**imposta sostitutiva forfettaria** su **tutti i redditi di fonte estera**, qualunque sia il loro ammontare, pari a **€100.000/anno** per i trasferimenti fino all'agosto 2024, **€200.000** per quelli successivi al DL 113/2024 e **€300.000** per chi trasferisce la residenza **dal 1° gennaio 2026** (L. 199/2025), più **€25.000/anno** per ciascun familiare incluso (**€50.000** per i trasferimenti dal 2026). Vantaggi collegati: imposta di successione e donazione dovuta **solo sui beni esistenti in Italia** (L. 232/2016, c. 158) ed **esonero** dal quadro RW e da IVIE/IVAFE per gli anni di validità dell'opzione (L. 232/2016, c. 153; la portata dell'esonero secondo la circ. 17/E/2017 è da verificare).

⚠️ **Punto cruciale per le cripto**: la flat tax copre solo i redditi di **fonte estera**. La circ. AdE **30/E/2023** (par. 5) applica anche ai neo-residenti questi criteri di localizzazione:
- reddito di fonte **italiana** se le chiavi sono presso un exchange o wallet provider **residente in Italia** (o una sua stabile organizzazione italiana);
- reddito di fonte **estera** se sono presso un prestatore **non residente**;
- in **autocustodia** conta dove si trova il supporto, che si **presume in Italia** se il titolare è residente: per un neo-residente le cripto in self-custody sono quindi di regola tassate ordinariamente (33%), salvo prova contraria.

Chi valuta il regime per un patrimonio cripto rilevante deve farlo con un consulente specializzato.

## Successione e donazione di cripto

Le cripto-attività rientrano tra i **beni e diritti** soggetti all'**imposta di successione e donazione** e concorrono all'**attivo ereditario** (circ. AdE **30/E/2023**, par. 3.7.4). La riforma del Testo unico (**D.Lgs. 139/2024**, in vigore per successioni e donazioni **dal 1° gennaio 2025**) non contiene norme specifiche sulle cripto.

- **Base imponibile**: il valore di mercato in euro alla data di **apertura della successione** o della **donazione**.
- **Territorialità**: se il de cuius o il donante era **residente in Italia**, l'imposta colpisce **tutto** il patrimonio cripto, **anche** quello su exchange esteri o hardware wallet. Se **non residente**, solo i beni esistenti in Italia: per l'AdE rilevano le cripto presso prestatori di servizi **residenti in Italia** o su supporti che **si trovano in Italia**; quelle su exchange esteri o dispositivi all'estero **restano fuori**.
- **Costo di carico per eredi e donatari** (decisivo per le plusvalenze **future**, art. 68 co. 9-bis TUIR): in caso di **successione** il costo è il valore **definito o dichiarato ai fini dell'imposta di successione**; in caso di **donazione** è il **costo sostenuto dal donante** (quello che il donante avrebbe usato cedendo a titolo oneroso).
- ⚠️ **Documentazione = tutto**: se manca la prova del costo, il costo è assunto **pari a zero** (art. 68 c. 9-bis TUIR; in amministrato anche la risposta AdE 135/2025) e l'**intera** plusvalenza futura è tassata. Conservare la documentazione di acquisto — e **trasmetterla agli eredi** — è ciò che evita di regalare al fisco l'intero controvalore alla successiva vendita.
- **Aliquote** (art. 7 per la successione e art. 56 per la donazione, D.Lgs. 346/1990; dal 2027 artt. 93 e 133 D.Lgs. 123/2025): le stesse di ogni altro bene, con la tabella completa in `successione-donazione.md`:
  - 4% per coniuge e parenti in linea retta oltre la franchigia di €1.000.000 ciascuno;
  - 6% per fratelli e sorelle oltre €100.000;
  - 6%, senza franchigia, per gli altri parenti fino al quarto grado, gli affini in linea retta e gli affini in linea collaterale fino al terzo grado;
  - 8% per gli altri soggetti;
  - franchigia di €1.500.000 per i disabili gravi.

  La riforma in vigore **dal 2025** ha abrogato il **coacervo successorio** (le donazioni in vita non si sommano più all'asse), introdotto l'**autoliquidazione** ed escluso espressamente le **liberalità d'uso** (regali per matrimoni, compleanni). Resta il coacervo **tra donazioni**: quelle precedenti dello stesso donante allo stesso donatario erodono la franchigia delle successive (art. 57).
- **Problema pratico (self-custody)**: gli eredi devono poter **accedere alle chiavi private**. Per le cripto in autocustodia, senza una pianificazione (un "testamento digitale" con le istruzioni di accesso conservate in modo sicuro), il patrimonio rischia di diventare **irrecuperabile** anche se fiscalmente dichiarato. La pianificazione successoria delle cripto è tanto tecnica quanto fiscale.

## Cosa rimane fuori / da verificare col commercialista

Anche qui la reference dà i principi e segnala le incertezze: l'applicazione dei criteri di **localizzazione** al caso concreto dei neo-residenti, l'uso di **trust o holding** per detenere cripto, la **voluntary disclosure** di asset pregressi non dichiarati, il **mining occasionale** della persona fisica, le **convenzioni** contro le doppie imposizioni e i casi con elementi di internazionalità. Tutto richiede un professionista abilitato ed esperto del settore. La postura resta personale/educativa, con rinvio al commercialista.

Cross-reference: `criptovalute.md` (il quadro base) e `criptovalute-avanzate.md` (DeFi, NFT, ravvedimento). Insieme, le tre reference coprono la fiscalità cripto della persona fisica residente dal caso ordinario fino ai confini con impresa, internazionalità e passaggio generazionale.

*Aliquota 33% e compartimento separato (L. 207/2024 c. 24; art. 68 c. 9-bis TUIR; dal 2027 artt. 304 c. 7 e 77 c. 11 D.Lgs. 117/2026), costo di carico e costo zero senza documentazione (art. 68 c. 9-bis TUIR; risp. AdE 135/2025), irrilevanza delle valutazioni IRES/IRAP (art. 110 c. 3-bis TUIR, dal 2027 art. 119 c. 5), IVA sulle cripto e mining (CGUE C-264/14; circ. 30/E/2023; risp. AdE 515/2022), art. 24-bis TUIR 2026 (L. 199/2025 c. 25-26; L. 232/2016 c. 153 e 158), localizzazione e successioni delle cripto (circ. 30/E/2023, par. 3.7.4 e 5; artt. 2, 7 e 56 D.Lgs. 346/1990) — Verificato: 2026-10.*
