---
name: pensione
description: Pianificazione pensionistica integrata (previdenza obbligatoria INPS + complementare + proiezione tenore di vita post-pensionamento) per lavoratori dipendenti italiani.
---

Esegui la pianificazione pensionistica completa seguendo la skill `it-pianificazione`.

Workflow:

1. **Ingestion**: chiedere all'utente (se non già nel contesto):
   - Anagrafica: data di nascita, sesso, età pensionamento target (default: vecchiaia 67)
   - Lavoro: RAL attuale, anni di anzianità INPS, contratto (tempo indeterminato/determinato), crescita retributiva attesa
   - TFR: conferito (a quale fondo) o ancora in azienda (saldo accumulato)
   - Fondo pensione esistente: forma (negoziale/aperto/PIP), montante accumulato, contributi annui (lavoratore + datore), comparto scelto
   - Spese mensili attuali (con breakdown grossolano se possibile)
   - Aspettative su spese post-pensione (se note)
   - Altri redditi (locazioni, finanziari, ecc.) — opzionali

2. **Calcolo previdenza obbligatoria**: montante contributivo proiettato × coefficiente di trasformazione all'età target. Stimare pensione lorda e netta, tasso di sostituzione.

3. **Calcolo previdenza complementare**: proiezione montante a pensionamento (capitalizzazione contributi + rendimenti), tassazione finale 15→9%, beneficio fiscale cumulato dalle deduzioni.

4. **Confronto TFR azienda vs fondo**: simulazione comparativa con tassazione separata vs aliquota fondo. Quasi sempre il fondo vince, ma quantificare di quanto.

5. **Proiezione tenore di vita**: gap analysis tra pensione totale attesa e spesa proiettata. Identificare il gap in valore assoluto e in % del tenore desiderato.

6. **Leve da valutare**: pattern di copertura del gap (aumentare contributo, cambiare comparto, ritardare pensionamento, conferire TFR se non già fatto, risparmio non previdenziale), presentati come scenari quantificati: la scelta resta all'utente.

Output: report markdown strutturato + (opzionale, se richiesto) Excel di proiezione editabile con scenari conservativo/base/ottimistico.

Se mancano dati essenziali, chiedere prima di procedere. Non inventare RAL o anzianità contributiva. Disclaimer obbligatorio in fondo: è una stima educativa, non consulenza previdenziale, fiscale o di investimento; per adesioni, riscatti, uscite anticipate e casi specifici rinviare a un patronato o a un consulente previdenziale abilitato.
