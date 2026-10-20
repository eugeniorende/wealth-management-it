---
name: pensione-autonomi
description: Pianificazione pensionistica per lavoratori autonomi e partite IVA (regime forfettario o ordinario, Gestione Separata INPS o casse). Analizza la previdenza obbligatoria con l'aliquota 26,07% e valuta la previdenza complementare con la corretta analisi della deducibilità — che per i forfettari puri è zero.
---

Esegui la pianificazione pensionistica per lavoratore autonomo seguendo la skill `it-pianificazione-autonomi`.

⚠️ PUNTO CRITICO: per un forfettario puro il contributo volontario al fondo pensione NON è deducibile (regime sostitutivo, non IRPEF). Questo inverte la logica valida per i dipendenti. Non dire mai a un forfettario che il fondo pensione "fa risparmiare tasse" senza prima verificare se ha altri redditi IRPEF.

Workflow:

1. **Ingestion**: chiedere all'utente (se non già nel contesto):
   - Profilo: tipo cassa (Gestione Separata / cassa professionale; artigiani e commercianti delle gestioni IVS INPS sono fuori perimetro: dirlo subito e rinviare a INPS o al commercialista), regime fiscale (forfettario / ordinario / forfettario 5%), codice ATECO o tipo attività, coefficiente di redditività (78% per IT/professioni)
   - Economici: ricavi annui incassati, crescita attesa, età corrente, età target pensionamento, anzianità contributiva
   - **Altri redditi IRPEF** (affitti IRPEF, lavoro dipendente part-time): rilevante per la deducibilità del fondo pensione
   - Fondo pensione esistente o in valutazione: montante, contributo, comparto, rendimento, anni partecipazione
   - Spese mensili attuali e fattore riduzione post-pensione

2. **Previdenza obbligatoria**: base contributiva (ricavi × coefficiente per forfettari) × 26,07%, fino al massimale €122.295. Proiezione montante → coefficiente trasformazione → pensione lorda/netta. Evidenziare che il tasso di sostituzione è più basso che per i dipendenti (aliquota 26,07% vs 33%).

3. **Previdenza complementare**: analisi CORRETTA della deducibilità (zero per forfettario puro; fino a capienza se ha redditi IRPEF; piena se ordinario). Confronto onesto fondo pensione vs PAC ETF per il forfettario puro.

4. **Gap analysis tenore di vita**: scenari conservativo/base/ottimistico.

5. **Raccomandazioni**: pattern A1-A5 (versare contributi obbligatori, valutare il fondo senza il falso mito della deduzione, sfruttare redditi IRPEF collaterali, valutare ordinario se conviene, massimizzare la complementare).

Se mancano dati essenziali (ricavi, tipo cassa, regime), chiedere prima di procedere. Per casse professionali specifiche e scelta del regime, rinviare al commercialista.
