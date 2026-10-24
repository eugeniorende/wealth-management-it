---
name: it-revisione
description: Revisione periodica personale della propria situazione finanziaria complessiva — il livello di sintesi che tiene insieme pensione, obiettivi, fiscalità e allocazione. Usa questa skill quando l'utente vuole "fare il punto", chiede una revisione annuale o di fine anno, dice "come sta andando il mio piano", "rivediamo il portafoglio / la mia situazione / i miei obiettivi", "controllo annuale", "check-up finanziario", "tiriamo le somme", oppure quando a fine anno fiscale (novembre-dicembre) vuole una verifica complessiva prima del 31/12. È la skill di orchestrazione: non ricalcola le proiezioni delle altre, le richiama e le sintetizza in un quadro unico con azioni prioritizzate e un report. Si appoggia a `it-pianificazione` e `it-pianificazione-autonomi` (gap previdenziale), `it-pianificazione-obiettivi` (avanzamento obiettivi), `it-tax-optimization` (minusvalenze e harvesting di fine anno) e `it-rebalance` (deriva dell'allocazione). Per un risparmiatore italiano che gestisce i propri soldi. NON è consulenza finanziaria, fiscale o previdenziale: rinvia a un professionista abilitato per le decisioni.
---

# Revisione periodica personale

Questa è la skill di **sintesi** del plugin: il direttore d'orchestra. Le altre cinque skill sono motori analitici, ognuno bravissimo a rispondere a **una** domanda (quanto prenderò di pensione, come sto sugli obiettivi, dove compensare le minusvalenze, come ribilanciare). Questa skill risponde alla domanda che le tiene insieme: **"alla luce dell'insieme, cosa faccio adesso?"**.

È l'adattamento, per chi gestisce i propri soldi, del workflow di revisione periodica del cliente (la `client-review` del plugin upstream): non si prepara un meeting con un consulente, si fa il punto della propria situazione.

Postura: **personale ed educativa**. Non è consulenza. La revisione mette ordine e propone azioni; le decisioni e i casi specifici restano da verificare con un professionista (commercialista, consulente OCF).

## Quando si attiva

- L'utente vuole **fare il punto** complessivo: "rivediamo la mia situazione", "come sta andando il piano", "check-up annuale", "tiriamo le somme".
- È **fine anno fiscale** (novembre-dicembre) e vuole una verifica prima del 31/12 (qui la fiscalità ha priorità per via delle scadenze).
- Un **evento della vita** cambia il quadro (nuovo reddito, figlio, casa, eredità, passaggio dipendente↔P.IVA) e l'utente vuole rivedere tutto.

NON è il posto per una singola analisi verticale: se l'utente chiede solo "quanto prenderò di pensione" o solo "come ribilancio", usa la skill specifica. Questa entra quando serve la **visione d'insieme**.

## Il workflow della revisione

La revisione segue un'agenda in cinque passi. Ai passi 1-2 fotografa; al passo 3 **richiama le altre skill** (non ne duplica la logica); ai passi 4-5 sintetizza e produce il report. Lo strumento `assets/cruscotto-patrimoniale.xlsx` raccoglie la parte quantitativa.

### 1. Fotografia (dove sono)
Patrimonio netto (attività per contenitore fiscale − passività), composizione, e allocazione complessiva per classe. Il cruscotto (fogli **Patrimonio** e **Allocazione**) la raccoglie. I contenitori fiscali richiamano `it-pianificazione-obiettivi/references/asset-location.md`.

### 2. Cosa è cambiato (dall'ultima volta)
Versamenti effettuati vs pianificati; andamento del periodo **separando il rendimento di mercato dai versamenti** (foglio **Andamento** del cruscotto — è l'errore più comune del fai-da-te, vedi `references/metodo-revisione.md`); eventi della vita; cambiamenti normativi rilevanti (es. nuova Legge di Bilancio).

### 3. Avanzamento per dominio (richiamando le altre skill)
- **Pensione** → `it-pianificazione` (dipendenti) o `it-pianificazione-autonomi` (P.IVA): il tasso di sostituzione proiettato è ancora in linea con l'obiettivo? C'è un **gap previdenziale**? Va aumentato il versamento al fondo pensione (verificando la deducibilità nel proprio regime)? Per il dipendente, qual è lo **spazio deducibile residuo** dell'anno: max(0, €5.300 − datore − dovuto − volontari già versati nell'anno), con il contributo del datore e quello minimo del lavoratore (il TFR non conta)? È il tetto fiscale dei volontari da versare ancora entro il 31/12, non un importo consigliato (foglio Complementare dell'Excel di `it-pianificazione`); per il forfettario la deduzione arriva solo fino agli altri redditi IRPEF (`it-pianificazione-autonomi`). Ciò che supera il plafond, o che il forfettario non deduce, va comunicato al fondo come non dedotto entro il 31/12 dell'anno dopo: senza comunicazione in uscita è tassato di nuovo, con una perdita del 9-15% su quella parte (23% se la posizione esce con un'anticipazione non sanitaria o un riscatto per altre cause).
- **Obiettivi** → `it-pianificazione-obiettivi`: ogni obiettivo è **on track**? La **probabilità di successo** (Monte Carlo) è ancora adeguata? Il **glide path** richiede de-risking quest'anno? Va aggiustato il versamento mensile?
- **Fiscalità** → `it-tax-optimization`: ci sono **minusvalenze in scadenza** (finestra 4 anni) da usare entro il 31/12? Plusvalenze da compensare? Opportunità di **harvesting**? (A fine anno questo passo ha priorità per via delle scadenze.)
- **Allocazione** → `it-rebalance`: quanto è il **drift** rispetto al target? Va ribilanciato? Si può ribilanciare sfruttando le **minus in scadenza** per compensare le plus da vendita (coordinamento fiscale)?

### 4. Azioni prioritizzate
Si raccolgono le azioni emerse e si **ordinano**, secondo la logica di `references/metodo-revisione.md`:
1. **Scadenza** prima di tutto (minus in scadenza al 31/12, versamento fondo pensione entro il 31/12 per la deduzione, comunicazione al fondo dei contributi non dedotti dell'anno precedente entro il 31/12).
2. **Impatto strutturale** poi (gap previdenziale, obiettivo a rischio): agire presto vale più che agire tanto.
3. **Manutenzione** infine (ribilanciamento entro le bande, de-risking del glide path).

Il valore della sintesi sono le **azioni cross-dominio** che risolvono più cose insieme: ribilanciare a fine anno usando le minus in scadenza; indirizzare il versamento annuale dove rende di più (fondo pensione deducibile se c'è gap, o classe sottopesata per ribilanciare tramite i flussi senza realizzare plus); coordinare il de-risking di un obiettivo con l'harvesting. Vedi `references/metodo-revisione.md` per gli esempi.

### 5. Report
Si produce il **report della revisione** come deliverable (vedi Formato output). È il pezzo che nessuna singola skill produce: la fotografia, i progressi e le azioni in un documento unico.

## Formato output

Report in markdown, cinque sezioni che ricalcano il workflow. C'è un **template precompilato** pronto da riempire in `assets/template-revisione.md`: usarlo come scheletro garantisce che il report sia completo e coerente di anno in anno.

1. **Fotografia**: patrimonio netto, composizione per contenitore, allocazione per classe, rendimento del periodo (con la decomposizione mercato/versamenti, in termini reali).
2. **Cosa è cambiato**: versamenti vs piano, drift, eventi, novità normative.
3. **Avanzamento per dominio**: pensione (gap), obiettivi (on track / probabilità), fiscalità (minus in scadenza), allocazione (drift) — sintetizzati, ciascuno con il rinvio alla skill di dettaglio.
4. **Azioni prioritizzate**: lista ordinata (scadenza → impatto → manutenzione), evidenziando le azioni cross-dominio. Per ciascuna: cosa, perché, entro quando. Riportarle anche nel foglio **Azioni** del cruscotto (tracker).
5. **Prossima revisione**: quando rifare il punto (annuale + mini-revisione fiscale di fine anno).

### Disclaimer (obbligatorio in fondo)

> **Disclaimer**: questa revisione ha finalità informative di organizzazione personale. Non costituisce consulenza finanziaria, fiscale o previdenziale. Sintetizza le proiezioni degli strumenti del piano, che dipendono dalle ipotesi inserite e non sono garanzie. Le aliquote, le regole previdenziali e fiscali e i coefficienti cambiano con le Leggi di Bilancio annuali. Per le decisioni di investimento, la dichiarazione dei redditi e i casi specifici, consultare un professionista abilitato (commercialista, consulente finanziario OCF).

## Lo strumento: il cruscotto patrimoniale

`assets/cruscotto-patrimoniale.xlsx` raccoglie la parte quantitativa della revisione. Un foglio Leggimi con istruzioni e limiti, poi sei fogli:

- **Patrimonio**: attività per contenitore fiscale (dossier, fondo pensione, conto deposito, liquidità, polizze, immobili, cripto) meno passività → patrimonio netto e composizione.
- **Allocazione**: per classe (azionario, obbligazionario, liquidità, immobiliare, alternativi), % attuale vs target, **drift** e segnale di ribilanciamento oltre la soglia della **regola 5/25** (la minore tra la banda assoluta e il 25% del target della classe, come in `it-rebalance`).
- **Andamento**: la decomposizione del periodo — **rendimento di mercato separato dai versamenti**, rendimento money-weighted semplificato (Dietz) e rendimento **reale** al netto dell'inflazione. È il foglio che impedisce di scambiare i versamenti per rendimento. Sotto, i **costi dell'anno** (bollo, commissioni e Tobin tax, TER medio ponderato, ISC del fondo pensione) a scopo di confronto: il rendimento calcolato sui valori di mercato li incorpora già, quindi non vanno sottratti di nuovo.
- **Sintesi**: avanzamento di obiettivi (capitale attuale vs target, probabilità Monte Carlo, **priorità** e stato rispetto alla soglia della priorità: 85% essenziali, 75% importanti, 60% desiderabili) e pensione (tasso di sostituzione proiettato vs obiettivo, gap), da compilare tirando i numeri dagli strumenti dedicati.
- **Azioni**: il tracker delle azioni emerse dalla revisione (azione, dominio, priorità, scadenza, stato), con la legenda della logica di prioritizzazione. È il ponte tra il report e l'esecuzione.
- **Rendimento TWR**: il **time-weighted return** della strategia (rendimenti dei sotto-periodi tra un flusso e l'altro, incatenati), affiancato al **money-weighted esatto** (XIRR) sugli stessi dati. La differenza tra i due è l'effetto del timing dei versamenti; il TWR è il numero da confrontare con un benchmark. Si compila una riga per data di rilevazione (valore + flusso netto), dall'alto e senza righe vuote, fino a 120 righe: il riepilogo legge da solo l'ultima.

Excel e LibreOffice ricalcolano all'apertura: per controllare un file compilato basta aprirlo; dal repository del plugin, `python scripts/ricalcola-excel.py <file>` lo ricalcola in locale italiano e segnala le celle in errore. Il cruscotto **non ricalcola** le proiezioni: le sintetizza in un quadro unico.

### Contratto di input: da dove viene ogni numero

Ogni cella di input del cruscotto ha una fonte precisa. Dove la fonte è uno script, lanciarlo con `--json FILE` dalla cartella di lavoro e leggere dal file i campi indicati; il resto viene dagli estratti. Le celle sono quelle del foglio consegnato.

| Dominio | Fonte (skill) | Campo del JSON o dell'estratto | Cella del cruscotto |
|---|---|---|---|
| Patrimonio | estratti di broker, fondo e banca (nessuno script) | saldi a oggi per contenitore; debiti residui | `Patrimonio!B6:B13`; `B17:B18` |
| Allocazione attuale | `importa-estratto-broker.py --json` (it-tax-optimization), più fondo e liquidità | `posizioni[].valore`, sommati per classe (lo script dà la categoria fiscale, la classe la assegni tu) | `Allocazione!B5:B9` |
| Allocazione target | `allocatore-capitale.py --json` (it-pianificazione-obiettivi) | `aggregato.azioni`, `.obbligazioni`, `.liquidita` diviso `aggregato.totale` | `Allocazione!D5:D7` (`D8:D9` a mano) |
| Glide path | `glidepath-obiettivi.py --json` (it-pianificazione-obiettivi) | `portafoglio[anno]`, la quota azionaria aggregata dell'anno del piano | `Allocazione!D5`, se il target segue il calendario |
| Andamento | estratti (nessuno script) | saldo iniziale e finale, versamenti netti; inflazione del periodo | `Andamento!B4:B6`; `B14` |
| Obiettivi | `montecarlo-obiettivi.py --json` (it-pianificazione-obiettivi) | `obiettivi[].probabilita_successo`; `obiettivi[].gia` e `obiettivi[].target_oggi` (o le colonne F e B del pianificatore); `obiettivi[].priorita` | `Sintesi!E6:E9`; `B6:B9` e `C6:C9`; `G6:G9` |
| Pensione, dipendenti | `proiezione-inps.py --json` → `montecarlo-pensione.py --from --json` → `netto-pensione.py --from --json` (it-pianificazione) | `tasso_sostituzione_lordo_vs_ral_finale` dalla proiezione, oppure `scenari[].tasso_sostituzione_netto` del netto (è il netto che misura il tenore di vita: dirlo nel report) | `Sintesi!B12`; l'obiettivo `B13` a mano |
| Pensione, autonomi | `proiezione-pensione-autonomi.xlsx`, foglio Riepilogo (nessuno script) | tasso di sostituzione | `Sintesi!B12` |
| Fiscalità | `importa-estratto-broker.py --json` | `analisi.per_broker[broker].zainetto_in_scadenza` e `.plus_realizzabili_a_costo_zero` | foglio `Azioni`, righe di scadenza al 31/12 (nessuna cella numerica) |

Le chiavi dei JSON sono quelle scritte dagli script alla data di questa versione; `--help` di ogni script elenca anche le chiavi che legge con `--from`.

## Anti-pattern (NON FARE MAI)

- ❌ **Ricalcolare da zero** ciò che fanno le altre skill: la revisione le **richiama** e sintetizza. Per la proiezione pensionistica si usa `it-pianificazione`, non si rifà il calcolo qui.
- ❌ **Confondere versamenti e rendimento**: se il saldo è salito di €18.000 ma hai versato €9.000, non hai reso €18.000. Sempre la decomposizione (foglio Andamento).
- ❌ **Spingere a intervenire su un calo di mercato**: i cali fanno parte del piano. La revisione corregge la rotta su scadenze, gap e drift, non insegue il mercato. Una revisione settimanale è un anti-pattern.
- ❌ **Trattare i quattro domini come liste separate**: il valore è nelle azioni cross-dominio (ribilanciare usando le minus, versare dove rende di più). Cercarle sempre.
- ❌ **Ignorare le scadenze di fine anno**: a novembre-dicembre le minus in scadenza, il versamento al fondo pensione e la comunicazione dei contributi non dedotti hanno priorità operativa, vanno prima dell'impatto strutturale.
- ❌ **Promettere risultati o dare raccomandazioni di investimento personalizzate**: la revisione mette ordine e propone, ma rinvia al professionista per le decisioni.

## Riferimenti

- `references/metodo-revisione.md` — la cadenza (annuale + finestra fiscale di fine anno + revisione straordinaria per eventi), come misurare il rendimento senza ingannarsi (decomposizione mercato/versamenti, money-weighted vs time-weighted, rendimento reale), la logica di prioritizzazione e le azioni cross-dominio
- `references/investment-policy-statement.md` — l'**IPS personale**: la "costituzione" del portafoglio (obiettivi, profilo di rischio, allocazione target, bande di ribilanciamento, **regole nei drawdown**, politica di versamento e prelievo, vincoli fiscali, cadenza), con scheletro compilabile. È il riferimento da cui la revisione misura gli scostamenti
- `assets/investment-policy-statement.xlsx` — l'IPS come **foglio compilabile**: le nove sezioni con celle da riempire, le **bande di ribilanciamento calcolate da sé** dai target con la regola 5/25, il controllo che i target sommino a 100%, e drawdown/vincoli fiscali precompilati con default
- `assets/cruscotto-patrimoniale.xlsx` — il cruscotto quantitativo (Patrimonio, Allocazione, Andamento, Sintesi, Azioni, Rendimento TWR)
- `assets/template-revisione.md` — il **template del report** di revisione, scheletro markdown precompilato da riempire (le cinque sezioni + disclaimer)
- **Orchestra** (non duplica) le altre skill del plugin:
  - `it-pianificazione` / `it-pianificazione-autonomi` — il gap previdenziale e il fondo pensione
  - `it-pianificazione-obiettivi` — avanzamento, probabilità (Monte Carlo) e glide path degli obiettivi
  - `it-tax-optimization` — minusvalenze in scadenza, harvesting, il coordinamento di fine anno
  - `it-rebalance` — deriva dell'allocazione e ribilanciamento tax-aware (e `coordinamento-zainetto.md` per l'integrazione con la fiscalità)

## Note per l'iterazione

Questa è la versione 0.6 della skill (introdotta in v0.8 del plugin, estesa in v0.9.2).

In quest'iterazione (v0.6):
- **`tracker-secchielli.xlsx`** — il foglio operativo del monitoraggio goals-based: si definiscono i secchielli e l'anno del piano (Impostazioni), si incolla il calendario del glide path (Glide), si assegnano le posizioni a secchielli e classi con tendine (Posizioni), e il foglio Controllo mostra effettivo vs target per secchiello e aggregato con **semaforo automatico sulle bande 5/25** (formattazione condizionale OK/VICINO/RIBILANCIA). Il target % azioni "di oggi" si aggiorna da solo cambiando l'anno del piano (INDEX sul calendario Glide). Registro Versamenti con totali per secchiello e anno corrente. 145 formule, recalc 0 errori; dati precompilati d'esempio da sostituire. Completa il ciclo: pianifica (it-pianificazione-obiettivi) → esegui → monitora qui.

In quest'iterazione (v0.5):
- **`genera-ips.py`** — il generatore dell'Investment Policy Statement come documento Word (python-docx): copertina, 12 sezioni (profilo, obiettivi, allocazione, glide path, ribilanciamento, versamenti, strumenti, fiscalità, previdenza, guardrail, revisione), Appendice A con checklist a caselle e Appendice B broker opzionale. I dati del caso si compilano in un unico blocco `DATI`; i testi di policy (bande 5/25, trappola ETF, guardrail, checklist) sono default sovrascrivibili, quindi il documento esce completo anche da un dict minimo. **Onestà incorporata**: la nota di rischio è calcolata dalla quota azionaria aggregata (drawdown atteso in un orso ≈ metà della quota), e lo script valida allocazione=100% e capitali=totale, avvisando senza bloccare. Uso: `python genera-ips.py [output.docx]`. Dipendenza: python-docx. Codifica il deliverable finale del flusso, prima costruito a mano.

In quest'iterazione (v0.4):
- **Excel dedicato all'IPS** (`assets/investment-policy-statement.xlsx`): lo scheletro dell'Investment Policy Statement come foglio compilabile, con le **bande di ribilanciamento calcolate da sé** dai target (regola 5/25 → soglie operative per classe), il controllo che i target sommino a 100%, e drawdown/vincoli fiscali precompilati. Quinto Excel del plugin. Validato (bande corrette, check 100% funzionante, 0 errori).

In quest'iterazione (v0.3):
- **Time-weighted return** nel cruscotto (foglio Rendimento TWR): il rendimento della strategia neutralizzato dai flussi, da confrontare con un benchmark, affiancato al money-weighted **esatto** (XIRR) sugli stessi dati. La differenza tra i due misura l'effetto del timing dei versamenti. Cruscotto a sei fogli.

In quest'iterazione (v0.2):
- **Template del report** (`assets/template-revisione.md`): scheletro markdown precompilato delle cinque sezioni, da riempire — rende il report completo e coerente di anno in anno.
- **Foglio "Azioni"** nel cruscotto: tracker delle azioni emerse (azione, dominio, priorità, scadenza, stato) con la legenda di prioritizzazione; il ponte tra report ed esecuzione.
- **Investment Policy Statement personale** (`references/investment-policy-statement.md`): la "costituzione" del portafoglio, con scheletro compilabile e il cuore comportamentale (le regole nei drawdown scritte prima del crollo). Formalizza in policy ciò che le altre skill producono come numeri; la revisione ne misura l'aderenza.

Versione precedente (v0.1): la skill di sintesi/orchestrazione — workflow in cinque passi, logica di prioritizzazione (scadenza → impatto → manutenzione), azioni cross-dominio, report come deliverable, e il cruscotto patrimoniale.

Roadmap:
- ✅ Calcolo del **time-weighted return**: fatto in v0.3 (foglio Rendimento TWR, con MWR esatto via XIRR per il confronto)
- ✅ Excel dedicato all'**IPS**: fatto in v0.4 (`assets/investment-policy-statement.xlsx`, con bande auto-calcolate)
