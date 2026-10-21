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

3. **Calcolo previdenza complementare**: proiezione montante a pensionamento (capitalizzazione contributi + rendimenti), tassazione finale 15→9% sui soli TFR e contributi dedotti, beneficio fiscale cumulato dalle deduzioni. Il plafond di €5.300 è condiviso con il contributo del datore e con quello dovuto del lavoratore: lo spazio per i volontari è quello che resta. Ricordare la comunicazione al fondo dei contributi non dedotti.

4. **Confronto TFR azienda vs fondo**: blocco «Confronto TFR» del foglio Complementare dell'Excel (rivalutazione 1,5% + 75% dell'inflazione tassata al 17% e tassazione separata, contro 15→9% sulle quote nel fondo). Distinguere il vantaggio fiscale, certo, da quello di rendimento, che dipende dal comparto.

5. **Proiezione tenore di vita**: gap analysis tra pensione totale attesa e spesa proiettata. Identificare il gap in valore assoluto e in % del tenore desiderato.

6. **Leve da valutare**: pattern di copertura del gap (aumentare contributo, cambiare comparto, ritardare pensionamento, conferire TFR se non già fatto, risparmio non previdenziale), presentati come scenari quantificati: la scelta resta all'utente.

Output: report markdown strutturato + (opzionale, se richiesto) Excel di proiezione editabile con scenari conservativo/base/ottimistico.

Se mancano dati essenziali, chiedere prima di procedere. Non inventare RAL o anzianità contributiva. Disclaimer obbligatorio in fondo: è una stima educativa, non consulenza previdenziale, fiscale o di investimento; per adesioni, riscatti, uscite anticipate e casi specifici rinviare a un patronato o a un consulente previdenziale abilitato.
