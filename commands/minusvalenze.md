---
name: minusvalenze
description: Analizza minusvalenze e plusvalenze del portafoglio italiano (regime amministrato) e genera un piano di ottimizzazione fiscale con calendario d'azione e scadenze.
---

Esegui l'analisi fiscale completa seguendo la skill `it-tax-optimization`.

Workflow:

1. **Ingestion**: chiedere all'utente (se non già fornito):
   - Snapshot portafoglio: ISIN/ticker, quantità, PMC o lotti, prezzo corrente, categoria fiscale se nota
   - Stato zainetto fiscale: anno realizzo + importo residuo per ciascuna minus pregressa
   - Intermediario (per cut-off operativi)

2. **Analisi**: calcolare plus/minus latente per posizione, classificare per categoria fiscale (reddito diverso vs reddito di capitale), aggregare zainetto per anno scadenza.

3. **Simulazione**: per ogni minus in scadenza nei 12 mesi, proporre trade candidati di realizzo plus compensabili. Per posizioni in perdita su strumenti che generano reddito diverso, proporre realizzo per creazione zainetto. Quantificare risparmio fiscale e costi (commissioni, Tobin tax, riacquisto).

4. **Calendario**: produrre timeline ordinata con scadenze critiche (zainetto in evaporazione, deadline 31/12 con T+2 settlement, eventuali cut-off broker).

Output: report markdown in tre sezioni (Stato attuale / Opportunità / Calendario d'azione). Disclaimer obbligatorio in fondo: non è consulenza fiscale; prima di operare verificare saldi e zainetto sul portale del broker, e per i casi specifici rinviare a un commercialista.

Se mancano dati essenziali, chiedere prima di procedere. Non inventare numeri.
