---
name: it-revisione
description: "Revisione periodica personale della situazione finanziaria complessiva: il livello di sintesi che tiene insieme pensione, obiettivi, fiscalità e allocazione. Usa questa skill quando l'utente vuole «fare il punto», chiede una revisione annuale o di fine anno, dice «come sta andando il mio piano», «rivediamo il portafoglio», «check-up finanziario», «tiriamo le somme», o a novembre-dicembre vuole una verifica complessiva prima del 31/12; anche per l'Investment Policy Statement (IPS), il cruscotto patrimoniale e quello grafico del piano. È la skill di orchestrazione: non ricalcola le proiezioni delle altre, le richiama e le sintetizza in un quadro unico con azioni prioritizzate e un report. Si appoggia a `it-pianificazione` e `it-pianificazione-autonomi` (gap previdenziale), `it-pianificazione-obiettivi` (avanzamento), `it-tax-optimization` (minusvalenze di fine anno) e `it-rebalance` (deriva dell'allocazione). NON è consulenza finanziaria, fiscale o previdenziale: rinvia a un professionista abilitato."
metadata:
  version: "0.8"
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

## Dove lavorare

I dati personali e i file compilati vivono nella **cartella di lavoro** dell'utente (per esempio `~/piano-finanziario/`; se il plugin è stato installato con Claude Code, è quella scelta all'installazione: `${user_config.cartella_lavoro}`; se il segnaposto qui sopra non è stato sostituito, chiedila all'utente), mai dentro il plugin: la copia installata si sovrascrive a ogni aggiornamento. Regole:

- i modelli Excel si **copiano** nella cartella di lavoro e si compilano lì, mai in `assets/`: `${CLAUDE_SKILL_DIR}/assets/cruscotto-patrimoniale.xlsx`, `${CLAUDE_SKILL_DIR}/assets/tracker-secchielli.xlsx`, `${CLAUDE_SKILL_DIR}/assets/investment-policy-statement.xlsx`;
- gli script si lanciano dalla cartella di lavoro con il loro percorso nel plugin, e il file da leggere si passa sempre come argomento (`--help` elenca argomenti e opzioni): `python "${CLAUDE_SKILL_DIR}/assets/genera-ips.py" ips.docx --dati ips.json`, `python "${CLAUDE_SKILL_DIR}/assets/genera-cruscotto.py" --from alloc.json --from mc.json -o cruscotto.html`;
- gli output (JSON, CSV degli ordini, documenti) finiscono nella cartella di lavoro, mai nel plugin.

`${CLAUDE_SKILL_DIR}` è la cartella di questa skill: Claude Code lo sostituisce con il percorso reale quando carica la skill (anche quando la skill la carica un comando: i comandi sono alias e non lanciano script). Dipendenze degli script: Python 3.11 o successivo; `genera-ips.py` vuole python-docx (`pip install python-docx`), `genera-cruscotto.py` solo la libreria standard.

## Il workflow della revisione

La revisione segue un'agenda in cinque passi più uno facoltativo. Ai passi 1-2 fotografa; al passo 3 **richiama le altre skill** (non ne duplica la logica); ai passi 4-5 sintetizza e produce il report; al passo 6, se l'utente lo vuole, disegna il piano in un cruscotto grafico. Lo strumento `assets/cruscotto-patrimoniale.xlsx` raccoglie la parte quantitativa.

### 1. Fotografia (dove sono)
Patrimonio netto (attività per contenitore fiscale − passività), composizione, e allocazione complessiva per classe. Il cruscotto (fogli **Patrimonio** e **Allocazione**) la raccoglie. I contenitori fiscali richiamano `it-pianificazione-obiettivi/references/asset-location.md`.

### 2. Cosa è cambiato (dall'ultima volta)
Versamenti effettuati vs pianificati; andamento del periodo **separando il rendimento di mercato dai versamenti** (foglio **Andamento** del cruscotto — è l'errore più comune del fai-da-te, vedi `references/metodo-revisione.md`); eventi della vita; cambiamenti normativi rilevanti (es. nuova Legge di Bilancio).

### 3. Avanzamento per dominio (richiamando le altre skill)
- **Pensione** → `it-pianificazione` (dipendenti) o `it-pianificazione-autonomi` (P.IVA): il tasso di sostituzione proiettato è ancora in linea con l'obiettivo? C'è un **gap previdenziale**? Va aumentato il versamento al fondo pensione (verificando la deducibilità nel proprio regime)? Per il dipendente, qual è lo **spazio deducibile residuo** dell'anno: max(0, €5.300 − datore − dovuto − volontari già versati nell'anno), con il contributo del datore e quello minimo del lavoratore (il TFR non conta)? È il tetto fiscale dei volontari da versare ancora entro il 31/12, non un importo consigliato (foglio Complementare dell'Excel di `it-pianificazione`); per il forfettario la deduzione arriva solo fino agli altri redditi IRPEF (`it-pianificazione-autonomi`). Ciò che supera il plafond, o che il forfettario non deduce, va comunicato al fondo come non dedotto entro il 31/12 dell'anno dopo: senza comunicazione in uscita è tassato di nuovo, con una perdita del 9-15% su quella parte (23% se la posizione esce con un'anticipazione non sanitaria o un riscatto per altre cause).
- **Obiettivi** → `it-pianificazione-obiettivi`: ogni obiettivo è **on track**? La **probabilità di successo** (Monte Carlo) è ancora adeguata? Il **glide path** richiede de-risking quest'anno? Va aggiustato il versamento mensile? La deriva per obiettivo si legge nel `tracker-secchielli.xlsx`, se l'utente lo tiene.
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

### 6. Cruscotto grafico
Una pagina HTML con i grafici del piano: allocazione attuale contro target con le bande, probabilità e capitale finale degli obiettivi, glide path, pensione lorda e netta, capitale umano, zainetto per scadenza, drift e ordini del ribilanciamento. I numeri vengono **solo** dai JSON che gli script scrivono con `--json` (quelli del «Contratto di input» più `ribilanciamento-multibroker.py --json`): la pagina li disegna, non li ricalcola, e tu non li riscrivi.

1. Dalla cartella di lavoro, lancia il generatore sui JSON **scritti dagli script con `--json`** (`--from` ripetibile, l'ordine non conta; quelli di `importa-previdenza.py`, `ponte-pensione.py` e `riscatto-laurea.py` si riconoscono e si saltano). Non passare i file di **input** che stanno nella stessa cartella: `piano.json` (il `--dati` del ribilanciamento), `capitale-umano.json` (il `--dati` del capitale umano), `ips.json` (il `--dati` dell'IPS):
   ```bash
   python "${CLAUDE_SKILL_DIR}/assets/genera-cruscotto.py" --from alloc.json --from glide.json --from mco.json \
       --from inps.json --from mc.json --from netto.json --from capitale-umano-out.json \
       --from broker.json --from ribilancia.json -o cruscotto.html
   ```
   Se un JSON manca, dillo e genera il cruscotto con quelli che ci sono: le sezioni senza dati non compaiono. Gli errori fermano lo script con `ERRORE:`; secondo il messaggio:
   - «non è un output riconosciuto»: è un file di input o di un altro programma, toglilo dai `--from`;
   - «sono dello stesso tipo»: due file dello stesso script (per esempio `mc.json` al pensionamento e `mc-uscita.json` all'uscita anticipata): chiedi all'utente quale usare, non scegliere tu;
   - «manca …»: il JSON viene da una versione precedente dello script; rigeneralo con lo script, non correggerlo a mano.
2. Comunica il percorso del file e le sezioni incluse (le stampa lo script). Il file resta nella cartella di lavoro e si apre nel browser con un doppio clic, anche offline.
3. **Chiedi sempre** se pubblicarlo come Artifact, con questa informazione: la pagina va su claude.ai e contiene importi, età e proiezioni del piano; resta privata finché l'utente non la condivide; si può cancellare. Le singole posizioni dell'estratto (ISIN, descrizioni) non ci sono. **Senza un sì esplicito non pubblicare.**
4. Se l'utente dice sì:
   - in **Claude Code**, pubblica con lo strumento Artifact il file `cruscotto.html` così com'è, senza riscriverlo;
   - in **claude.ai** e in **Cowork**, crea un artifact HTML con il contenuto del file, copiato senza modifiche;
   - se l'ambiente non ha un modo di creare artifact, dillo e lascia il file locale.
   Per aggiornare il cruscotto dopo una nuova revisione si rilanciano gli script e il generatore, e si ripubblica sullo stesso Artifact.
5. Se l'utente dice no, basta il file locale.

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

Excel e LibreOffice ricalcolano all'apertura: per controllare un file compilato basta aprirlo e cercare celle in errore (`#RIF!`, `#VALORE!`). Chi ha installato il plugin da marketplace o dal repository (non lo zip per Cowork, che non contiene `scripts/`) può anche ricalcolarlo da riga di comando con `python "${CLAUDE_PLUGIN_ROOT}/scripts/ricalcola-excel.py" <file>`, in locale italiano e con l'elenco delle celle in errore; serve LibreOffice. Il cruscotto **non ricalcola** le proiezioni: le sintetizza in un quadro unico.

### I dati dell'IPS: `--dati ips.json`

`genera-ips.py` prende i dati del caso da un JSON nella cartella di lavoro (`--dati ips.json`), mai dal blocco `DATI` dentro lo script, che resta l'esempio; senza `--dati` lo script genera l'esempio e avvisa. Il JSON è un oggetto con le stesse chiavi del blocco `DATI` (le liste al posto delle tuple). Le chiavi del caso sono **obbligatorie** e vengono tutte dal JSON, mai dall'esempio: se ne manca una, o ha la forma sbagliata (un importo scritto come testo, una riga con un elemento in meno), lo script si ferma con `ERRORE:` e il nome della chiave. Sono facoltative solo le note, il broker e i testi di policy, che senza il JSON usano i default del plugin; una chiave ignota è un errore. Le chiavi:

| Chiave | Forma | Da dove |
|---|---|---|
| `investitore`, `capitale` (obbligatorie) | testo, numero | l'utente |
| `data`, `sottotitolo` | testo (vuoto = mese corrente), testo | facoltative |
| `profilo` (obbligatoria) | lista di `[etichetta, valore]` | l'utente (età, reddito, tolleranza, capacità di risparmio) |
| `obiettivi` (obbligatoria) | lista di `[nome, "orizzonte · tipo", "Profilo (% azioni)", target, capitale assegnato]` | pianificatore e `allocatore-capitale.py --json` (`obiettivi[].allocato`) |
| `obiettivi_nota`, `allocazione_nota` | testo | facoltative |
| `allocazione` (obbligatoria) | lista di `[classe, importo, quota %]` | `allocatore-capitale.py --json` (`aggregato`) |
| `glide_path` (obbligatoria) | lista di `[fase, anni, "da → a %", cosa succede]` | `glidepath-obiettivi.py --json` (`portafoglio`) |
| `versamenti`, `strumenti`, `previdenza` (obbligatorie) | liste di testi, o di `[classe, testo]` per gli strumenti | l'utente; la proiezione pensione per `previdenza` |
| `ribilanciamento`, `guardrail`, `revisione`, `fiscalita`, `checklist` | liste di testi | facoltative: senza, i default di policy del plugin |
| `broker` | `null` oppure `{"nome": …, "sezioni": [[titolo, testo], …]}` | facoltativa, Appendice B |

### Contratto di input: da dove viene ogni numero

Ogni cella di input del cruscotto ha una fonte precisa. Dove la fonte è uno script, lanciarlo con `--json FILE` dalla cartella di lavoro e leggere dal file i campi indicati; il resto viene dagli estratti. Le celle sono quelle del foglio consegnato.

| Dominio | Fonte (skill) | Campo del JSON o dell'estratto | Cella del cruscotto |
|---|---|---|---|
| Patrimonio | estratti di broker, fondo e banca (nessuno script) | saldi a oggi per contenitore; debiti residui | `Patrimonio!B6:B13`; `B17:B18` |
| Allocazione attuale | `importa-estratto-broker.py --json` (it-tax-optimization), più fondo e liquidità | `posizioni[].valore`, sommati per classe (lo script dà la categoria fiscale, la classe la assegni tu) | `Allocazione!B5:B9` |
| Allocazione target | `allocatore-capitale.py --json` (it-pianificazione-obiettivi) | `aggregato.azioni`, `.obbligazioni`, `.liquidita` diviso `aggregato.totale` | `Allocazione!D5:D7` (`D8:D9` a mano) |
| Glide path | `glidepath-obiettivi.py --json` (it-pianificazione-obiettivi) | `portafoglio[anno]`, la quota azionaria aggregata dell'anno del piano | `Allocazione!D5`, se il target segue il calendario; `D6:D7` si riproporzionano sulle quote dell'allocatore perché il totale `D10` resti 100% |
| Andamento | estratti (nessuno script) | saldo iniziale e finale, versamenti netti; inflazione del periodo | `Andamento!B4:B6`; `B14` |
| Obiettivi | `montecarlo-obiettivi.py --json` (it-pianificazione-obiettivi) | `obiettivi[].probabilita_successo`; `obiettivi[].gia` e `obiettivi[].target_oggi` (o le colonne F e B del pianificatore); `obiettivi[].priorita` | `Sintesi!E6:E9`; `B6:B9` e `C6:C9`; `G6:G9` |
| Pensione, dipendenti | `proiezione-inps.py --json` → `montecarlo-pensione.py --from --json` → `netto-pensione.py --from --json` (it-pianificazione) | `tasso_sostituzione_lordo.mediana` del Monte Carlo: INPS più fondo, lordo sulla RAL finale. L'obiettivo è il `target` dello stesso JSON, sulla stessa base lorda (per un obiettivo diverso si rilancia con `--set TASSO_SOSTITUZIONE_TARGET=…`). Il netto (`scenari[nome="mediana"].tasso_sostituzione_netto`, e `P10` per la lettura prudente) va nel report come misura del tenore di vita, mai in B12 contro un obiettivo lordo; `tasso_sostituzione_lordo_vs_ral_finale` della proiezione è la sola quota pubblica e non va in B12 | `Sintesi!B12`; `B13` |
| Pensione, autonomi | `proiezione-pensione-autonomi.xlsx`, foglio Riepilogo (nessuno script) | `Riepilogo!B13`, «Tasso di sostituzione — totale» (non la B12, che è la sola obbligatoria), lordo; l'obiettivo sulla stessa base | `Sintesi!B12`; `B13` |
| Fiscalità | `importa-estratto-broker.py --json` | `analisi.per_broker[broker].zainetto_in_scadenza` e `.plus_realizzabili_a_costo_zero` | foglio `Azioni`, righe di scadenza al 31/12 (nessuna cella numerica) |
| Capitale umano | `capitale-umano.py --json` (it-pianificazione-obiettivi), con `--composizione` per il settore | `esposizione_finanziaria` contro `esposizione_totale`; `settore.quota_settore_fin` e `settore.sovrappeso` se c'è la composizione; `eta_sorpasso` con `stato_sorpasso` (`gia_superato`, `entro_la_proiezione`, `non_prima_della_fine`) | report, nessuna cella: è una lente, non un target |

Le chiavi dei JSON sono quelle scritte dagli script alla data di questa versione; `--help` di ogni script elenca anche le chiavi che legge con `--from`.

## Anti-pattern (NON FARE MAI)

- ❌ **Ricalcolare da zero** ciò che fanno le altre skill: la revisione le **richiama** e sintetizza. Per la proiezione pensionistica si usa `it-pianificazione`, non si rifà il calcolo qui.
- ❌ **Confondere versamenti e rendimento**: se il saldo è salito di €18.000 ma hai versato €9.000, non hai reso €18.000. Sempre la decomposizione (foglio Andamento).
- ❌ **Spingere a intervenire su un calo di mercato**: i cali fanno parte del piano. La revisione corregge la rotta su scadenze, gap e drift, non insegue il mercato. Una revisione settimanale è un anti-pattern.
- ❌ **Trattare i quattro domini come liste separate**: il valore è nelle azioni cross-dominio (ribilanciare usando le minus, versare dove rende di più). Cercarle sempre.
- ❌ **Ignorare le scadenze di fine anno**: a novembre-dicembre le minus in scadenza, il versamento al fondo pensione e la comunicazione dei contributi non dedotti hanno priorità operativa, vanno prima dell'impatto strutturale.
- ❌ **Promettere risultati o dare raccomandazioni di investimento personalizzate**: la revisione mette ordine e propone, ma rinvia al professionista per le decisioni.
- ❌ **Pubblicare il cruscotto senza conferma**: un Artifact porta i dati del piano su claude.ai; si pubblica solo dopo un sì esplicito, ogni volta.
- ❌ **Scrivere a mano numeri nel cruscotto o modificare il template nel plugin**: i numeri vengono dai JSON degli script; se uno è sbagliato si rilancia lo script, e `cruscotto.html` si rigenera, non si edita.

## Riferimenti

- `references/metodo-revisione.md` — la cadenza (annuale + finestra fiscale di fine anno + revisione straordinaria per eventi), come misurare il rendimento senza ingannarsi (decomposizione mercato/versamenti, money-weighted vs time-weighted, rendimento reale), la logica di prioritizzazione e le azioni cross-dominio
- `references/investment-policy-statement.md` — l'**IPS personale**: la "costituzione" del portafoglio (obiettivi, profilo di rischio, allocazione target, bande di ribilanciamento, **regole nei drawdown**, politica di versamento e prelievo, vincoli fiscali, cadenza), con scheletro compilabile. È il riferimento da cui la revisione misura gli scostamenti
- `assets/investment-policy-statement.xlsx` — l'IPS come **foglio compilabile**: le nove sezioni con celle da riempire, le **bande di ribilanciamento calcolate da sé** dai target con la regola 5/25, il controllo che i target sommino a 100%, e drawdown/vincoli fiscali precompilati con default
- `assets/cruscotto-patrimoniale.xlsx` — il cruscotto quantitativo (Patrimonio, Allocazione, Andamento, Sintesi, Azioni, Rendimento TWR)
- `assets/tracker-secchielli.xlsx` — il monitoraggio goals-based: secchielli e anno del piano (Impostazioni), calendario del glide path incollato da `glidepath-obiettivi.py` (Glide), posizioni assegnate a secchiello e classe con tendine (Posizioni), effettivo contro target per secchiello e aggregato con semaforo sulle bande 5/25 (Controllo), registro dei versamenti; si compila nella cartella di lavoro e si rilegge al passo 3
- `assets/genera-ips.py` — l'IPS in Word: copertina, 12 sezioni, appendici con la checklist e il broker; la nota di rischio viene dalla quota azionaria; i dati del caso arrivano da `--dati ips.json` (vedi «I dati dell'IPS»), senza il documento è l'esempio e lo dice in copertina
- `assets/genera-cruscotto.py` — il **cruscotto grafico**: legge i `--json` degli script del piano (`--from`, ripetibile), ne riconosce il tipo dalle chiavi e scrive una pagina HTML autosufficiente con i grafici; `--json` scrive anche i dati che finiscono nella pagina (vedi «Cruscotto grafico»)
- `assets/cruscotto.html` — il template della pagina, fisso: HTML, CSS e JavaScript senza risorse esterne; non si modifica, lo usa `genera-cruscotto.py`
- `assets/template-revisione.md` — il **template del report** di revisione, scheletro markdown precompilato da riempire (le cinque sezioni + disclaimer)
- **Orchestra** (non duplica) le altre skill del plugin:
  - `it-pianificazione` / `it-pianificazione-autonomi` — il gap previdenziale e il fondo pensione
  - `it-pianificazione-obiettivi` — avanzamento, probabilità (Monte Carlo) e glide path degli obiettivi
  - `it-tax-optimization` — minusvalenze in scadenza, harvesting, il coordinamento di fine anno
  - `it-rebalance` — deriva dell'allocazione e ribilanciamento tax-aware (e `coordinamento-zainetto.md` per l'integrazione con la fiscalità)
