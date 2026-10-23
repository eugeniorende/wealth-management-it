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

Un ETF UCITS armonizzato che investe in titoli di Stato whitelist NON è tassato uniformemente al 12,5%. I proventi si considerano riferibili ai titoli di Stato italiani ed equiparati e a quelli degli Stati white list in proporzione alla **percentuale media dell'attivo** del fondo investita in quei titoli (DM 13/12/2011, art. 1 cc. 1-2), e quella parte è tassata al 26% nel limite del 48,08%, cioè al netto del 51,92% (circ. AdE 19/E/2014, par. 5.1; il DM, scritto per l'aliquota del 20%, indica ancora il 62,5%). In pratica:

- Quota whitelist dei proventi → tassata al 12,5%
- Quota non-whitelist → tassata al 26%
- Aliquota effettiva = 12,5% × p + 26% × (1 − p), con p la percentuale media

Questo vale sia per le **distribuzioni** sia per le **plusvalenze** all'uscita (entrambe sono reddito di capitale, ricordiamolo — non compensano minus pregresse).

Vale anche per le **perdite** (DM 13/12/2011, art. 1 c. 4): la minus da rimborso o cessione delle quote è un reddito diverso e va nello zainetto, ma la parte riferibile ai titoli di Stato vi entra ridotta del 51,92% (circ. AdE 19/E/2014, par. 5.1, «per un importo ridotto del 51,92»; il 62,5% dell'art. 1 c. 5 del DM è la misura del regime al 20%). Una minus di €1.000 su un fondo con p = 60% vale €1.000 × (1 − 0,5192 × 0,6) = €688,5 di zainetto, cioè la minus × aliquota effettiva / 26% (17,9% / 26% = 68,85%).

**Da dove viene p.** Non dal KID, che non la riporta: la comunica l'emittente agli intermediari ogni semestre (molti la pubblicano sul sito, nei documenti fiscali), rilevata sugli ultimi due prospetti semestrali o annuali redatti entro il semestre solare anteriore alla data della distribuzione, del rimborso o della cessione (DM 13/12/2011, art. 1 c. 3). Quindi p cambia ogni sei mesi e conta quella valida per il semestre della vendita. Le certificazioni escono prima del semestre a cui si applicano e ne indicano il periodo: per una vendita va usata quella del semestre della vendita, che non è sempre l'ultima pubblicata.

Esempio della circolare (circ. 19/E/2014, par. 5.1): reddito di capitale da rimborso 300, percentuale media 26,5% → quota riferibile ai titoli pubblici 79,50; base imponibile 300 − 79,50 × 0,5192 = 258,72; ritenuta del 26% = 67,27 (aliquota effettiva 22,4%).

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

Riferimento normativo: i redditi diversi dei titoli di Stato ed equiparati, e delle obbligazioni degli Stati white list e dei loro enti territoriali, «sono computati nella misura del 48,08 per cento dell'ammontare realizzato». Lo prevedono l'art. 6 c. 1 D.Lgs. 461/97 per l'amministrato e l'art. 5 c. 2 per il dichiarativo, nel testo introdotto dall'art. 3 c. 5 DL 66/2014 (conv. L. 89/2014); dal 2027 artt. 306 c. 1 e 304 c. 1 TU D.Lgs. 117/2026. Il 48,08% è 12,5/26 arrotondato: qui si usa 0,48077.

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
- Hai €1.500 di plus latente su BTP (12,5%) che pensi di vendere, già al netto di ratei e scarto di emissione maturati (vedi Esempio D)

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

### Esempio D: BOT o zero coupon, lo scarto di emissione

Lo **scarto di emissione** (differenza tra prezzo di emissione e valore di rimborso) è reddito di capitale (art. 44 c. 1 lett. b e art. 45 c. 1 TUIR → artt. 46 e 47 TU 2027), tassato al 12,5% sui titoli di Stato e **mai compensabile** con lo zainetto. Il reddito diverso è solo la differenza tra corrispettivo (o rimborso) e costo d'acquisto, entrambi al netto dei redditi di capitale maturati (art. 68 c. 7 lett. a TUIR → art. 77 c. 8 TU 2027).

- **Sottoscritto all'asta e tenuto a scadenza**: BOT a 12 mesi, nominale €10.000, prezzo di emissione 96,50. Al rimborso a 100 lo scarto di emissione è €350, reddito di capitale: imposta €350 × 12,5% = €43,75 (per i BOT la trattiene l'intermediario già alla sottoscrizione). Reddito diverso: zero. Lo zainetto non viene toccato.
- **Comprato sul secondario a metà vita**: lo stesso BOT comprato dopo 6 mesi a 97,80. Lo scarto maturato all'acquisto, ripartito in modo lineare, è 3,50 × 6/12 = 1,75: il "valore teorico" del titolo è 96,50 + 1,75 = 98,25. A scadenza il reddito diverso è (100 − 3,50) − (97,80 − 1,75) = 0,45 per 100 di nominale, cioè €45 di plus compensabile su €10.000. Il resto del guadagno, €175 di scarto maturato nei 6 mesi di possesso, è reddito di capitale. Pagato 98,60, sopra il valore teorico, lo stesso BOT darebbe una minus di €35.
- **BTP con cedola emesso vicino alla pari**: lo scarto è piccolo, quindi lo sconto da secondario (per esempio un BTP emesso a 99,80 e comprato a 85) è quasi tutto reddito diverso; i ratei di cedola maturati restano reddito di capitale.

Il calcolo esatto lo fa l'intermediario in amministrato; in dichiarativo va ricostruito con il prezzo di emissione del titolo. Per i titoli emessi in più tranche, quale prezzo di emissione usare è da verificare con l'intermediario.

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
4. Per ETF UCITS che dichiarano esposizione titoli di Stato, NON applicare 12,5% — sono comunque reddito di capitale ad aliquota mista 12,5% × p + 26% × (1 − p), con p dalla certificazione dell'emittente valida per il semestre della vendita; le loro minus entrano nello zainetto per aliquota mista / 26%
5. Quando si propone uno scenario cross-rate, mostrare esplicitamente la conversione (l'utente non deve fidarsi: deve poter verificare il calcolo)

---
*Dati normativi (aliquote 26% / 12,5%) — Verificato: 2026-06.*
*ETF e fondi su titoli di Stato: percentuale media, aliquota mista e perdite ridotte del 51,92% (DM 13/12/2011, art. 1; circ. AdE 19/E/2014, par. 5.1) — Verificato: 2026-10.*
*Coefficiente 48,08% (art. 3 c. 5 DL 66/2014; artt. 5 c. 2 e 6 c. 1 D.Lgs. 461/97; artt. 304 c. 1 e 306 c. 1 D.Lgs. 117/2026) e scarto di emissione (artt. 44, 45 e 68 c. 7 TUIR; artt. 46, 47 e 77 D.Lgs. 117/2026) — Verificato: 2026-10.*
