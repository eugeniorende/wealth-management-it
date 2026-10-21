---
name: ribilancia
description: Ribilanciamento di portafoglio tax-aware sotto la fiscalità italiana (regime amministrato). Misura il drift dall'allocazione target e genera un piano che minimizza l'impatto fiscale, privilegiando le leve a costo zero (versamenti, flussi) prima delle vendite.
---

Esegui il ribilanciamento tax-aware del portafoglio seguendo la skill `it-rebalance`.

Workflow:

1. **Ingestion**: chiedere all'utente (se non già nel contesto):
   - Portafoglio attuale: per ogni posizione → broker, ISIN/ticker, descrizione, asset class, tipo fiscale (reddito diverso: azioni, certificates, ETC, obbligazioni e titoli di Stato / reddito capitale: ETF e fondi), aliquota se diversa dal 26% (12,5% per titoli di Stato e equiparati), quantità, PMC (i lotti servono solo a ricostruirlo se il broker non lo mostra), prezzo/controvalore corrente
   - **Allocazione target** (input dell'utente, NON suggerita): peso obiettivo per asset class
   - Eventuali bande di tolleranza diverse dalla regola 5/25 (punto 2)
   - Nuovi versamenti disponibili (per Leva 1) e flussi attesi/dividendi (per Leva 2)
   - Fase: accumulo o decumulo (in decumulo, l'importo netto da prelevare)
   - Zainetto fiscale disponibile per broker, in euro 26%-equivalenti (una minus al 12,5% vale il 48,08%; per coordinamento con it-tax-optimization)

2. **Misura del drift (bande dinamiche)**: confronta allocazione effettiva vs target con la regola **5/25** (soglia = minore tra 5 punti assoluti e 25% del target), non una banda fissa. Identifica le classi fuori banda. Se tutto è in banda → raccomandare di NON ribilanciare. Quando si ribilancia, regola di rientro mista: a target se la correzione è a costo netto zero, fino a metà della banda stretta per la parte che paga imposta (mostrando i due costi). Una sottopesata fuori banda si riempie anche vendendo da classi in banda sopra il target. Vedi `references/bande-dinamiche.md`.

3. **Piano tax-aware (gerarchia leve)**: applica in ordine — Leva 1 (nuovi versamenti, costo zero), Leva 2 (flussi/dividendi, costo zero), Leva 3 (vendita posizioni in minus di tutte le classi, costo zero/negativo, da eseguire prima delle plus), Leva 4 (vendita posizioni in plus, ultima risorsa: prima la quota coperta dallo zainetto, poi per imposta per euro venduto, plus/valore × aliquota). Per la **Leva 4 multi-broker**, ottimizzazione doppia broker × tipo fiscale: vendere reddito_diverso presso il broker con zainetto (plus assorbita), mai dare per scontata la compensazione cross-broker (lo zainetto è per-intermediario). **Allargamento cost-aware**: una vendita che lascia imposta netta si fa solo se il drift supera la banda allargata; la quota vendibile a costo zero si vende comunque, e il residuo rinviato si dichiara. Per portafogli multi-broker, e per il prelievo in decumulo (`PRELIEVO`), usa lo script `assets/ribilanciamento-multibroker.py`.

4. **Coordinamento fine anno**: se ci sono minus in scadenza, sequenzia le vendite di plus compensabili per sfruttarle prima del 31/12 (coordina con it-tax-optimization).

5. **Quantificazione e output**: tabella drift, piano per leva con costo fiscale di ciascuna, impatto fiscale totale, allocazione risultante vs target, raccomandazioni.

La skill NON raccomanda quale asset allocation scegliere (è input utente). Disclaimer obbligatorio in fondo: non è consulenza di investimento; i CSV degli ordini sono una checklist da verificare sul portale del broker, non ordini da eseguire alla cieca. Se mancano dati essenziali (allocazione target, PMC, tipo fiscale), chiedere prima di procedere.
