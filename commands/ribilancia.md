---
name: ribilancia
description: Ribilanciamento di portafoglio tax-aware sotto la fiscalità italiana (regime amministrato). Misura il drift dall'allocazione target e genera un piano che minimizza l'impatto fiscale, privilegiando le leve a costo zero (versamenti, flussi) prima delle vendite.
---

Esegui il ribilanciamento tax-aware del portafoglio seguendo la skill `it-rebalance`.

Workflow:

1. **Ingestion**: chiedere all'utente (se non già nel contesto):
   - Portafoglio attuale: per ogni posizione → broker, ISIN/ticker, descrizione, asset class, tipo fiscale (reddito diverso / reddito capitale), quantità, PMC (o lotti), prezzo/controvalore corrente
   - **Allocazione target** (input dell'utente, NON suggerita): peso obiettivo per asset class
   - Eventuali bande di tolleranza diverse dalla regola 5/25 (punto 2)
   - Nuovi versamenti disponibili (per Leva 1) e flussi attesi/dividendi (per Leva 2)
   - Fase: accumulo o decumulo
   - Zainetto fiscale disponibile per broker (per coordinamento con it-tax-optimization)

2. **Misura del drift (bande dinamiche)**: confronta allocazione effettiva vs target con la regola **5/25** (soglia = minore tra 5 punti assoluti e 25% del target), non una banda fissa. Identifica le classi fuori banda. Se tutto è in banda → raccomandare di NON ribilanciare. Quando si ribilancia, riportare a target (non solo al bordo della banda). Vedi `references/bande-dinamiche.md`.

3. **Piano tax-aware (gerarchia leve)**: applica in ordine — Leva 1 (nuovi versamenti, costo zero), Leva 2 (flussi/dividendi, costo zero), Leva 3 (vendita posizioni in minus, costo zero/negativo), Leva 4 (vendita posizioni in plus, ultima risorsa). Per la **Leva 4 multi-broker**, ottimizzazione doppia broker × tipo fiscale: vendere reddito_diverso presso il broker con zainetto (plus assorbita), mai dare per scontata la compensazione cross-broker (lo zainetto è per-intermediario). **Allargamento cost-aware**: una vendita che lascia imposta netta si fa solo se il drift supera la banda allargata. Per portafogli multi-broker usa lo script `assets/ribilanciamento-multibroker.py`.

4. **Coordinamento fine anno**: se ci sono minus in scadenza, sequenzia le vendite di plus compensabili per sfruttarle prima del 31/12 (coordina con it-tax-optimization).

5. **Quantificazione e output**: tabella drift, piano per leva con costo fiscale di ciascuna, impatto fiscale totale, allocazione risultante vs target, raccomandazioni.

La skill NON raccomanda quale asset allocation scegliere (è input utente). Disclaimer obbligatorio in fondo: non è consulenza di investimento; i CSV degli ordini sono una checklist da verificare sul portale del broker, non ordini da eseguire alla cieca. Se mancano dati essenziali (allocazione target, PMC, tipo fiscale), chiedere prima di procedere.
