# Sequenza di liquidazione fiscalmente efficiente (decumulo)

Quando si è in decumulo, ogni anno serve liquidare €X per viverci. **Da dove prenderli, per pagare meno imposta possibile?** È la dimensione fiscale del decumulo: `it-pianificazione-obiettivi/references/decumulo.md` dice *quanto* è sostenibile prelevare, questa reference dice *come* prelevarlo. Vale solo in regime amministrato; non è consulenza.

## La gerarchia delle fonti (per imposta crescente)

Per finanziare il prelievo annuo, attingere in quest'ordine:

**1. Liquidità e buffer — imposta zero.** Spendere la liquidità (conto corrente, e il buffer di liquidità della strategia bucket) non realizza nulla: nessuna imposta. È la prima fonte, e in particolare la fonte degli **anni negativi** — attingere al buffer invece di vendere il rischioso in perdita è la difesa dal rischio di sequenza (vedi `decumulo.md`).

**2. Flussi già incassati — imposta già assolta.** Dividendi e cedole sono già tassati alla fonte (26%, o 12,5% per i titoli di Stato). Se sono già stati incassati, **spenderli** invece di reinvestirli e poi vendere altro: si evita un realizzo aggiuntivo. Per i dividendi esteri il netto incassato sconta anche la ritenuta dello Stato estero, e il 26% italiano si applica sul netto frontiera. L'eventuale eccedenza rispetto alla convenzione si recupera solo con le pratiche estere (W-8BEN, rimborsi): vedi `it-tax-optimization/references/dividendi-esteri.md`.

**3. Vendite dal dossier titoli — imposta sui realizzi (26%), da minimizzare.** Quando le prime due fonti non bastano, si vende. Qui si applica la **stessa gerarchia delle leve** del ribilanciamento, perché il problema è identico (scegliere cosa e dove vendere per minimizzare la plus tassata):
   - prima le posizioni in **minus** (Leva 3): zero/negativo, alimentano lo zainetto;
   - poi le posizioni a **plus latente minore** in proporzione al valore (sul prezzo medio di carico);
   - usando lo **zainetto** per compensare le plus, con l'ottimizzazione **broker × tipo fiscale** (vendere reddito diverso presso il broker con zainetto, mai dare per scontata la compensazione cross-broker — vedi `ribilanciamento-multibroker.md`).
   Lo strumento `assets/ribilanciamento-multibroker.py` calcola direttamente questa sequenza: basta impostare la "riduzione" richiesta pari all'importo da liquidare.

   **Finalità successoria.** Per azioni e obbligazioni detenute direttamente gli eredi ricevono come costo il valore di successione: la plusvalenza latente si azzera. Se una parte del dossier è destinata agli eredi, le posizioni dirette con la plusvalenza latente più alta sono le ultime da vendere. Per fondi ed ETF il testo vigente tratta l'intestazione agli eredi come una cessione: da verificare. Vedi `it-tax-optimization/references/successione-donazione.md`.

**4. Fondo pensione — solo in pensione, ma fiscalmente agevolato.** In fase di erogazione la prestazione del fondo pensione è tassata al **15% scendente fino al 9%** (`max(9%, 15% − 0,30% × (anni − 15))`), e **solo sul TFR conferito e sui contributi dedotti**: i rendimenti già tassati durante l'accumulo e i contributi non dedotti comunicati al fondo non si tassano di nuovo (art. 11 c. 6 D.Lgs. 252/2005; dal 2027 art. 258 c. 4 D.Lgs. 117/2026; vedi `it-pianificazione/references/previdenza-complementare.md`). Questa aliquota (9-15%; 15-20% per l'erogazione frazionata) è **più bassa del 26%** che si paga realizzando plus sul dossier: ai fini fiscali, in pensione, attingere al fondo pensione è più efficiente che vendere il dossier in plus. Il vincolo è che il fondo resta **bloccato fino al pensionamento** e al massimo il 50% si prende in capitale (art. 11 c. 3). Il resto va in rendita vitalizia oppure, dal 1/7/2026, in rendita a durata definita o in prelievi liberamente determinabili, ma solo entro le rate maturate di una rendita teorica (c. 3-bis e 3-quater); dal 31/10/2026 anche in erogazione frazionata in almeno 5 anni. La scelta è irrevocabile, salvo la conversione in vitalizia, e fino al 31/12/2026 vale il periodo transitorio COVIP. Quindi è una fonte agevolata ma **strutturata**: più modulabile di prima, ma non liquidabile a piacere.

## La dimensione che cambia tutto: il prelievo è ricorrente

A differenza di un ribilanciamento una tantum, in decumulo si vende **ogni anno**. Due conseguenze:

- **Spalmare i realizzi nel tempo.** Lo zainetto è una risorsa che si rinnova su 4 anni: bruciarlo tutto nel primo anno lascia scoperti gli anni successivi. Conviene dosare le vendite di plus compensabili negli anni, non concentrarle.
- **Il prelievo annuo è anche l'occasione di ribilanciare.** Invece di vendere pro-quota, si finanzia il prelievo vendendo la **classe sovrappesata**: così un'unica operazione preleva *e* ribilancia (come il coordinamento di fine anno di `coordinamento-zainetto.md`, ma ricorrente). Negli **anni positivi** si vende il rischioso cresciuto (ribilancia, finanzia il prelievo, rifornisce il buffer); negli **anni negativi** si attinge al buffer (non si vende in perdita). È il decumulo e il ribilanciamento che diventano lo stesso atto.

## Un pattern tipico in pensione: due fonti complementari

Il fondo pensione (agevolato, meno rigido dal 2026 ma vincolato) e il dossier (flessibile ma tassato al 26% sui realizzi) si completano: usare la **rendita del fondo pensione come reddito di base** stabile, e il **dossier come integrazione flessibile** — attingendovi tax-efficient con la gerarchia sopra, e modulandolo negli anni (di più quando i mercati vanno bene, attingendo al buffer quando vanno male). La rigidità dell'uno è compensata dalla flessibilità dell'altro.

## Caveat

I realizzi parziali sono calcolati pro-rata sul prezzo medio di carico, che in amministrato è la base fiscale effettiva (art. 6 c. 4 D.Lgs. 461/97 → art. 306 c. 5 TU 2027). Lo zainetto va verificato per broker, con l'anno di formazione, sul portale dell'intermediario. E le aliquote del fondo pensione e i vincoli capitale/rendita vanno verificati al momento del pensionamento (cambiano con le riforme). La sostenibilità complessiva del prelievo — quanto, non come — è in `it-pianificazione-obiettivi/references/decumulo.md`.
