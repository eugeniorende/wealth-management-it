# Criptovalute (cripto-attività): fiscalità 2026

Reference sul trattamento fiscale delle cripto-attività per la persona fisica residente in Italia (fuori da attività d'impresa). Le cripto sono **redditi diversi** ma vivono in un **compartimento separato**: è il punto che le collega — e le distingue — dal resto di questa skill. Materiale di supporto; non è consulenza. La normativa è in rapida evoluzione e alcuni punti sono ancora controversi: i casi concreti vanno verificati con un commercialista.

## Inquadramento

Fino al 2022 le cripto erano una zona grigia (l'Agenzia le assimilava alle valute estere). La **Legge di Bilancio 2023 (L. 197/2022)** ha introdotto una disciplina organica, inserendo nell'art. 67 TUIR la lettera **c-sexies)** (dal 2027 art. 76 c. 1 lett. i D.Lgs. 117/2026): rientrano nei redditi diversi "le plusvalenze e gli altri proventi realizzati mediante rimborso o cessione a titolo oneroso, permuta o detenzione di cripto-attività, comunque denominate". La Circolare AdE 30/E/2023 è il principale documento di prassi.

Il percorso non si è stabilizzato: la **L. di Bilancio 2025 (L. 207/2024)** ha eliminato la franchigia di €2.000 e preannunciato l'aumento dell'aliquota; la **L. di Bilancio 2026** ha confermato l'aliquota al 33% ma introdotto un regime agevolato per gli e-money token in euro.

## Le aliquote (2026)

- **33%** sulle plusvalenze e gli altri proventi da cripto-attività generali: Bitcoin, Ethereum, altcoin, NFT, e anche le **stablecoin in dollari** (USDT, USDC) o in valute non euro. Era 26% fino al 31.12.2025.
- **26%** sui proventi da **e-money token (EMT) in euro conformi a MiCA** (stablecoin in euro regolamentate). Attenzione: l'aliquota agevolata vale solo quando l'EMT in euro è l'asset **di partenza**, non quello di arrivo — convertire BTC → stablecoin in euro resta tassato al 33%.
- **Neutralità fiscale** per la mera conversione euro → EMT-euro (e viceversa) e per il rimborso al valore nominale: non genera plus/minus.

⚠️ **L'aliquota si applica al momento del realizzo, a prescindere da quando la plusvalenza è maturata**: chi ha comprato BTC nel 2017 e vende nel 2026 paga il 33% sull'intera plusvalenza (salvo rivalutazione, vedi sotto). Non c'è "grandfathering" per data di acquisto. La franchigia di €2.000 non esiste più: si tassa dal primo euro.

## Gli eventi tassabili (e quelli neutri)

**Tassabili (evento realizzativo):**
- Cessione cripto → euro/fiat (il "cash-out").
- Uso di cripto per acquistare beni o servizi.
- Permuta tra cripto di natura **diversa** (es. utility token → payment token; conversione di una cripto in stablecoin euro EMT).
- Proventi da **staking, lending, yield** (su cripto non EMT-euro): redditi tassati sull'**intero ammontare lordo** ricevuto, senza dedurre commissioni della piattaforma.
- **Airdrop**: il valore alla ricezione è generalmente trattato come reddito tassabile e diventa il costo di carico per la futura cessione. Ma la qualificazione è dibattuta (un airdrop puramente gratuito potrebbe non essere imponibile alla ricezione per mancanza di onerosità): vedi `criptovalute-avanzate.md`.
- Cessione di **NFT**, cashback in cripto, ricompense da mining.

**Neutri (non realizzativi):**
- Permuta tra cripto **aventi medesime caratteristiche e funzioni** (la legge le dichiara fiscalmente irrilevanti).
- Trasferimento tra wallet o exchange **dello stesso soggetto** (purché la titolarità sia documentabile).
- Semplice detenzione (HODL) senza cessione.

⚠️ **Punto controverso — permuta tra cripto diverse.** Cosa siano "medesime caratteristiche e funzioni" non è chiarito in modo netto. Casi pacificamente neutri: ETH ↔ wETH (wrapping), bridge cross-chain dello stesso token, swap tra stablecoin ancorate alla stessa valuta. Caso pacificamente tassabile: scambiare un token di natura diversa (utility ↔ payment). Il caso **BTC ↔ ETH** è dibattuto: l'interpretazione prevalente tra i professionisti tratta lo scambio tra cripto-valute *diverse* come evento realizzativo (si realizza la plus sul bene ceduto), ma alcune fonti lo elencano tra le permute neutre. **In caso di dubbio è prudente considerare ogni scambio tra cripto diverse come potenzialmente tassabile e documentare i valori in euro di ogni operazione.** Verificare con il commercialista.

## Il compartimento separato (il legame con questa skill)

Questa skill ruota attorno all'asimmetria **redditi diversi vs redditi di capitale**. Le cripto aggiungono un **terzo compartimento**. La mappa di compensazione diventa:

| Compartimento | Esempi | Compensabile con… |
|---|---|---|
| Redditi di capitale (art. 44; dal 2027 art. 46) | dividendi, cedole, **plus da ETF armonizzati** | nulla (non compensabili) |
| Redditi diversi "tradizionali" (art. 67 c-bis…c-quinquies; dal 2027 art. 76 c. 1 lett. e…h) | plus/minus su azioni, **minus da ETF**, derivati, valute estere | tra loro |
| Redditi diversi "cripto" (art. 67 **c-sexies**; dal 2027 art. 76 c. 1 lett. i) | plus/minus su cripto-attività | **solo tra loro** |

Il punto pratico: **le minusvalenze cripto compensano esclusivamente plusvalenze cripto** (e gli altri proventi cripto), nello stesso anno o nei **quattro periodi d'imposta successivi**; **non** sono utilizzabili contro plusvalenze su azioni, ETF, derivati — né viceversa. È l'interpretazione prevalente (la lettera c-sexies, dal 2027 lettera i dell'art. 76, è una categoria autonoma; una minoranza di fonti ammette la compensazione con gli altri redditi diversi finanziari, ma è una lettura non consolidata). Conseguenza operativa: per chi ha portafogli misti conviene tenere **rapporti dedicati** alle sole cripto, per non confondere i compartimenti.

Come per le minus tradizionali, le minusvalenze cripto vanno **indicate in dichiarazione nell'anno di realizzo anche se non c'è imposta dovuta**, altrimenti si perde il diritto al riporto quadriennale.

## Calcolo: costo di carico, metodo, documentazione

- **Base imponibile** = corrispettivo percepito (o valore normale della cripto ricevuta in permuta) − costo o valore di acquisto documentato. Plus e minus dell'anno si sommano algebricamente; sul saldo positivo si applica l'imposta sostitutiva.
- **Metodo di valorizzazione**: nel regime amministrato **costo medio ponderato** delle cripto-attività con la medesima denominazione (art. 6 c. 4 D.Lgs. 461/97 → art. 306 c. 5 TU 2027; Circ. 30/E/2023 par. 3.2.2). Nel regime dichiarativo la legge non fissa un criterio: l'art. 67 c. 1-bis TUIR (→ art. 76 c. 2 TU 2027) richiama le lettere c), c-bis) e c-ter), non la c-sexies. Per le cripto-attività con la medesima denominazione l'Agenzia delle Entrate prescrive però, in dichiarativo, il **LIFO** (Circ. 30/E/2023, par. 3.2.1; per le valute virtuali fino al 2022 il LIFO veniva dal c. 1-bis, par. 2.3.1): è il criterio da usare, da tenere coerente negli anni, e discostarsene espone a contestazione. *(Verificato: 2026-10, art. 67 c. 1-bis TUIR → art. 76 c. 2 TU 2027; Circ. 30/E/2023 par. 2.3.1, 3.2.1 e 3.2.2.)*
- **Documentazione critica**: il costo va provato con elementi certi (estratti conto degli exchange, ricevute, report). **Costo non documentato = zero** → si tassa l'intero corrispettivo. Conservare tutto è essenziale, specie con molte operazioni o storici lunghi.
- **Proventi da detenzione** (staking, lending): tassati sull'**intero ammontare lordo**, senza deduzione di costi (art. 68 co. 9-bis, ultimo periodo, TUIR; dal 2027 art. 77 c. 11 D.Lgs. 117/2026). La deducibilità delle commissioni di trading nel costo di carico delle plusvalenze è tecnicamente dibattuta: documentarle e verificare con il commercialista.

## Imposta patrimoniale: l'imposta sul valore delle cripto-attività (IVCA)

- **0,2% annuo** sul valore in euro delle cripto detenute al **31 dicembre** (analoga al bollo sui prodotti finanziari). Versamento tramite F24, stesse scadenze delle imposte sui redditi. Liquidata nel Quadro RW (rigo RW8). Esempio: €50.000 di cripto a fine anno → €100 di imposta.
- Dall'IVCA è deducibile un **credito d'imposta** pari all'eventuale patrimoniale estera versata a titolo definitivo sulle stesse cripto.
- Nota: la L. 207/2024 ha tolto l'IVAFE sulle cripto dal 2025, ma l'IVCA dedicata (0,2%) resta l'imposta patrimoniale operativa.

## Adempimenti dichiarativi

- **Monitoraggio fiscale — Quadro RW (Redditi PF) o Quadro W (730)**: obbligatorio per la **sola detenzione** di cripto-attività, **indipendentemente dall'importo** e anche in assenza di plusvalenze. Vale per exchange italiani ed esteri, **wallet self-custody** (Ledger, MetaMask, ecc.) e qualsiasi forma di cripto — anche se le chiavi private sono su un dispositivo in Italia. Non c'è soglia minima. Confermato da Circ. AdE 30/E/2023 e risposte a interpello 75/2025 e 135/2025.
- **Plusvalenze — Quadro RT (Redditi) o Quadro T (730)**: da compilare se si sono realizzate operazioni rilevanti (cessioni, permute tra cripto diverse, staking). Consigliato anche senza plus, per documentare le minusvalenze riportabili.
- Dal 730/2025 (redditi 2024) i non titolari di P.IVA possono dichiarare cripto (oltre ad azioni/ETF/derivati) direttamente nel 730, con i nuovi Quadri **T** (plus) e **M** (imposte sostitutive), oltre al **W** (monitoraggio, già dal 730/2024) e al **D** (redditi di capitale) — equivalenti a RT, RW, RM, RL del modello Redditi.
- **DAC8**: la cooperazione UE e gli obblighi di comunicazione degli exchange rendono l'Agenzia sempre più informata. Il "tanto non si scopre" non regge.
- **ISEE**: dal 2026 il patrimonio in cripto entra nel calcolo dell'ISEE (riportando il Quadro RW). Rilevante se si chiedono agevolazioni legate all'ISEE.

## Il regime amministrato per le cripto (possibile dal 2023)

Dal 1/1/2023 si può optare per il regime amministrato anche per le cripto (L. 197/2022 c. 128; art. 6 c. 1-bis D.Lgs. 461/1997 → art. 306 c. 2 TU 2027; Circ. AdE 30/E/2023 par. 3.2.2): gli intermediari italiani abilitati (banche, SIM e, con efficacia dal 1/1/2024 secondo la circolare, i prestatori di servizi su cripto iscritti all'OAM) possono fungere da **sostituto d'imposta** anche per le cripto. Nella pratica l'offerta degli exchange è arrivata più tardi: verificare se il proprio intermediario la offre. In amministrato gli intermediari applicano l'imposta sostitutiva al realizzo, gestiscono il riporto delle minusvalenze nei quattro anni, assolvono l'IVCA dello 0,2%. Per le cripto gestite in regime amministrato **non** serve compilare RT/RW e il monitoraggio è semplificato — esattamente come per un dossier titoli tradizionale (il tema centrale di questa skill). Nel regime amministrato si usa il **costo medio ponderato** (per il dichiarativo vedi sopra). *(Regime amministrato cripto e costo medio — Verificato: 2026-10.)* È un cambiamento rilevante: porta le cripto allo stesso livello di semplicità dichiarativa degli strumenti tradizionali, per chi preferisce delegare gli adempimenti.

## Leve di pianificazione

- **Rivalutazione (affrancamento) del costo di carico**: la L. 207/2024 ha consentito di sostituire il valore storico con il valore di mercato al **1° gennaio 2025**, pagando un'imposta sostitutiva del **18%** (in un'unica soluzione entro il 30.11.2025 o in tre rate con interessi al 3%). Logica: con plus future tassate al 33%, un costo di carico più alto riduce l'imponibile. Conviene caso per caso (si paga subito su un guadagno non realizzato). La finestra al 1.1.2025 è scaduta; verificare se ne esistono di nuove per gli anni seguenti.
- **Harvesting nel compartimento cripto**: realizzare minusvalenze cripto entro fine anno per compensare plusvalenze cripto (stesso anno o nei 4 successivi). Vale solo dentro il compartimento cripto. Attenzione a eventuali letture anti-"wash sale".
- **Timing del realizzo**: poiché l'aliquota è quella vigente al realizzo, il momento della cessione conta (es. valutare l'impatto del passaggio 26%→33% sul 2025 vs 2026, già avvenuto).
- **Stablecoin in euro MiCA (EMT)**: i proventi da EMT-euro restano al 26% — ma solo quando l'EMT-euro è l'asset di partenza, e la conversione di una cripto volatile in EMT-euro è comunque tassata al 33%. Non è una scorciatoia per azzerare le tasse.
- **Documentare tutto, sempre**: lo storico dei costi è la leva più importante. Senza documentazione il costo è zero e si tassa l'intero corrispettivo.
- **Esposizione tramite ETN, ETC ed ETP su cripto quotati**: sono strumenti finanziari, non cripto-attività detenute. La Circ. AdE 30/E/2023 (par. 3) esclude dalla lettera c-sexies (dal 2027 art. 76 c. 1 lett. i) i security token che sono strumenti finanziari MiFID e tratta i derivati con sottostante cripto come redditi diversi di natura finanziaria (lettera c-quater, dal 2027 art. 76 c. 1 lett. g) *(Verificato: 2026-10)*. Né ETN ed ETC né ETP sono citati dalla circolare: la prassi degli intermediari li tratta come strumenti finanziari, cioè al 26% invece del 33%, compensabili con lo **zainetto ordinario** (non con le minus cripto) e, in un dossier italiano in amministrato, con il bollo 0,2% al posto di quadro RW e imposta sulle cripto-attività. L'Agenzia non l'ha confermato: da verificare sul prospetto e con l'intermediario prima di contarci. Passare dalle cripto detenute a un ETN realizza la plus al 33% e lascia le minus cripto nel loro compartimento; ed è uno strumento diverso, con rischio emittente e costi propri: la scelta non è solo fiscale.

## Cosa rimane fuori / da verificare col commercialista

- **Punti controversi**: la tassabilità delle permute tra cripto-valute diverse (BTC↔ETH) e la deducibilità delle commissioni nel costo di carico non sono pienamente chiariti. In caso di dubbio, l'approccio prudente (trattare lo scambio come potenzialmente tassabile, documentare i valori in euro) protegge da contestazioni.
- **DeFi, NFT, ravvedimento**: staking/lending/liquidity pool, NFT secondo il ruolo (investitore/creatore), e la regolarizzazione delle posizioni pregresse non dichiarate sono trattati in `criptovalute-avanzate.md`. Sono aree meno consolidate, con questioni aperte da affrontare con il commercialista.
- **Casi che restano comunque fuori**: cripto detenute in attività d'impresa o di lavoro autonomo (P.IVA); residenza estera e neo-residenti (flat tax sui redditi esteri); operazioni cross-chain e bridge. Tutti richiedono parere professionale.
- **Normativa in evoluzione**: aliquote, quadri dichiarativi, regime amministrato cripto e attuazione DAC8 cambiano rapidamente. Verificare sempre le regole vigenti dell'anno d'imposta in corso.

Questa skill resta in postura personale/educativa: nessuna ottimizzazione cripto sostituisce il calcolo di un commercialista esperto in cripto-attività, soprattutto su portafogli con molte operazioni o storici multi-exchange.
