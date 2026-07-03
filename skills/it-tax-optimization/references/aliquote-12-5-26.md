# Gestione dell'aliquota 12,5% e coefficiente di abbattimento

## Quali strumenti rientrano nel 12,5%

L'aliquota agevolata del 12,5% si applica ai proventi finanziari di:

1. **Titoli di Stato italiani** — BTP, BOT, CCT, CTZ, BTPi, BTP Italia, BTP Futura, BTP Valore
2. **Titoli emessi da enti pubblici territoriali italiani** — obbligazioni di Comuni, Province, Regioni
3. **Titoli emessi da organismi internazionali con accordo con l'Italia** — BEI, BERS, IBRD (Banca Mondiale), IADB, ADB, AFDB, AIIB, e simili
4. **Titoli di Stato emessi da paesi "white list"** (DM 4/9/1996 e successivi aggiornamenti)

La white list include la maggior parte degli Stati con accordi di scambio informazioni: UE, UK, USA, Canada, Australia, Giappone, Svizzera, Norvegia, ecc. Esclude paradisi fiscali e alcuni Stati non collaborativi. Lista corrente sul sito MEF (può cambiare con decreti ministeriali).

## Cosa NON è tassato al 12,5% (anche se "sembra")

- ❌ **Obbligazioni corporate italiane** — sono al 26% (Enel, ENI, banche, ecc.)
- ❌ **Obbligazioni bancarie** — al 26%
- ❌ **Obbligazioni di Stati non white list** — al 26%
- ❌ **ETF UCITS sui titoli di Stato** — tassazione *mista* (vedi sotto)
- ❌ **Fondi comuni che investono in BTP** — anch'essi tassazione mista

## L'edge case ETF/fondi sui titoli di Stato

Un ETF UCITS armonizzato che investe in titoli di Stato whitelist NON è tassato uniformemente al 12,5%. L'intermediario calcola un **coefficiente medio** basato sulla quota di NAV investita in strumenti whitelist e applica:

- Quota whitelist del NAV → tassata al 12,5%
- Quota non-whitelist → tassata al 26%

Questo vale sia per le **distribuzioni** sia per le **plusvalenze** all'uscita (entrambe sono reddito di capitale, ricordiamolo — non compensano minus pregresse).

Esempio concreto: un ETF "Government Bond Eurozone" composto al 78% da titoli whitelist (BTP, OAT, Bund, ecc.) e al 22% da non-whitelist. Un dividendo di €100 sarà tassato come:
- €78 al 12,5% = €9,75
- €22 al 26% = €5,72
- **Totale: €15,47** (aliquota effettiva ~15,5%, non 12,5% pulito)

Implicazione strategica: detenere BTP **direttamente** (12,5% pulito) è fiscalmente diverso da detenerli **via ETF UCITS** (12,5%/26% misto + plus non compensabile con minus pregresse). La differenza può essere rilevante per portafogli di una certa dimensione.

## La regola del coefficiente di abbattimento

Quando minus e plus hanno aliquote diverse (una al 26%, l'altra al 12,5%), il legislatore ha previsto la "scala" al riferimento 26% via il coefficiente:

```
coefficiente = 12,5 / 26 = 0,48077
```

Riferimento normativo: art. 68 c. 6 TUIR, art. 7 DLgs 461/97, prassi AdE.

### Formulazione operativa

L'amount a 12,5% viene moltiplicato per 0,48077 per essere "convertito" al riferimento 26%. Quindi:

- **Stesso rate** (26% vs 26%, o 12,5% vs 12,5%): compensazione 1:1 nominale
- **Cross rate** (minus 26% contro plus 12,5%): 100€ di minus assorbono fino a `100 / 0,48077 = 208€` di plus
- **Cross rate inverso** (minus 12,5% contro plus 26%): 100€ di minus assorbono solo `100 × 0,48077 = 48€` di plus

### Tabella riassuntiva (per €100 di minus)

| Minus aliquota | Plus aliquota | Plus assorbibile | Risparmio fiscale equivalente |
|---|---|---|---|
| 26% | 26% | €100 | €26 |
| 26% | 12,5% | €208 | €26 |
| 12,5% | 12,5% | €100 | €12,50 |
| 12,5% | 26% | €48,08 | €12,50 |

Notare: il **risparmio fiscale equivalente** è identico nelle due righe con stessa aliquota di minus. Questo è il principio di equivalenza fiscale.

## Esempi numerici

### Esempio A: minus stock contro plus BTP

- Hai €1.000 di minus pregresse su azione ENEL (26%), realizzate nel 2023
- Hai €1.500 di plus latente su BTP (12,5%) che pensi di vendere

Cosa succede in regime amministrato se vendi i BTP:
1. Tax dovuta lorda: €1.500 × 12,5% = €187,50
2. Compensazione: la minus stock (26%) può coprire fino a €1.000 / 0,48077 = €2.080 di plus BTP. Visto che la plus è solo €1.500, viene azzerata completamente.
3. Minus consumata in valore facciale: €1.500 × 0,48077 = €721,16
4. Minus residua: €1.000 − €721,16 = €278,84

Tax effettiva: €0. Risparmio: €187,50.

### Esempio B: minus BTP contro plus stock

- Hai €1.000 di minus pregresse su BTP (12,5%)
- Hai €1.500 di plus latente su azione ENI (26%)

Cosa succede in regime amministrato se vendi le azioni:
1. Tax dovuta lorda: €1.500 × 26% = €390
2. Compensazione: la minus BTP (12,5%) può coprire fino a €1.000 × 0,48077 = €480,77 di plus stock
3. Plus tassabile residua: €1.500 − €480,77 = €1.019,23
4. Tax effettiva: €1.019,23 × 26% = €265,00

Risparmio fiscale: €390 − €265 = €125,00. (Notare: matematicamente coincide con €1.000 × 12,5% = €125, cioè il fiscal value pieno della minus.)

### Esempio C: stesso rate, semplice

- Minus stock €1.000 (26%) + plus stock €800 (26%)
- Compensazione 1:1: plus completamente azzerata, minus residua €200 (26%)
- Tax: €0, risparmio: €208

## Caveat operativo

L'implementazione del cross-rate varia tra intermediari:

- **Best practice**: l'intermediario applica il coefficiente automaticamente e mantiene zainetto unificato distinguendo per aliquota. La maggior parte dei broker italiani principali (Fineco, Directa, BG Saxo) fa così.
- **Alcune implementazioni più rigide**: zainetti separati per aliquota, compensazione cross-rate non automatica. In questo caso può convenire l'opzione dichiarativo.
- **Casi limite**: per portafogli con esposizione mista significativa (es. >25% in titoli di Stato whitelist), verificare *come* il proprio broker tratta cross-rate prima di pianificare strategie.

Quando in dubbio: chiedere al broker (servizio clienti) o richiedere il rendiconto fiscale dettagliato che mostra zainetto suddiviso per aliquota.

## Heuristic per la skill

1. Se l'utente non specifica aliquote → assumere 26% di default
2. Se compaiono ISIN che iniziano con `IT0` (titoli italiani con codice Banca d'Italia 0001-0006) o equivalenti, flaggare come potenzialmente 12,5%
3. Per portafogli che dichiarano BTP/CCT/BOT, costruire due flussi separati di analisi e usare le formule di conversione sopra
4. Per ETF UCITS che dichiarano esposizione titoli di Stato, NON applicare 12,5% — sono comunque reddito di capitale al rate misto
5. Quando si propone uno scenario cross-rate, mostrare esplicitamente la conversione (l'utente non deve fidarsi: deve poter verificare il calcolo)

---
*Dati normativi (aliquote 26% / 12,5%) — Verificato: 2026-06.*
