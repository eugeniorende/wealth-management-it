---
name: minusvalenze
description: Analizza minusvalenze e plusvalenze del portafoglio italiano (regime amministrato) e genera un piano di ottimizzazione fiscale con calendario d'azione e scadenze.
---

Esegui l'analisi fiscale completa seguendo la skill `it-tax-optimization`.

Workflow:

1. **Ingestion**: chiedere all'utente (se non già fornito):
   - Snapshot portafoglio: ISIN/ticker, descrizione, quantità, PMC (in amministrato è la base fiscale; i lotti servono solo per i conti in dichiarativo), prezzo corrente, categoria fiscale se nota
   - Stato zainetto fiscale: anno realizzo + importo residuo + aliquota per ciascuna minus pregressa
   - Intermediario (per cut-off operativi; lo zainetto è per broker)

   Se l'utente fornisce l'estratto del broker in CSV (ed eventualmente lo zainetto in un secondo CSV), lanciare l'importatore della skill invece di ricopiare i dati a mano: `python3 skills/it-tax-optimization/assets/importa-estratto-broker.py estratto.csv [zainetto.csv] --anno AAAA --json risultato.json` (percorso relativo alla cartella del plugin; `--broker NOME` se il file è di un solo broker e non ha la colonna). Leggere il JSON: le posizioni «da classificare» vanno chiarite con l'utente prima dell'analisi, e gli avvisi (righe scartate, minus scadute, formato dei numeri) vanno riportati.

2. **Analisi**: calcolare plus/minus latente per posizione sul PMC, classificare per categoria fiscale (reddito diverso; reddito di capitale per ETF e fondi; a IRPEF per gli OICR non armonizzati fuori UE/SEE), aggregare zainetto per broker e anno di scadenza, escludendo le minus scadute.

3. **Simulazione**: per ogni minus in scadenza nei 12 mesi, proporre trade candidati di realizzo plus compensabili. Per posizioni in perdita su strumenti che generano reddito diverso, proporre realizzo per creazione zainetto. Quantificare risparmio fiscale e costi (commissioni, Tobin tax, riacquisto). Con più broker e minus incagliate, confrontare la chiusura del rapporto con certificazione delle minus (Pattern E) e il passaggio al dichiarativo (Pattern D).

4. **Calendario**: produrre timeline ordinata con scadenze critiche (zainetto in evaporazione, deadline 31/12 con T+2 settlement, eventuali cut-off broker).

Output: report markdown in tre sezioni (Stato attuale / Opportunità / Calendario d'azione). Disclaimer obbligatorio in fondo: non è consulenza fiscale; prima di operare verificare saldi e zainetto sul portale del broker, e per i casi specifici rinviare a un commercialista.

Se mancano dati essenziali, chiedere prima di procedere. Non inventare numeri.
