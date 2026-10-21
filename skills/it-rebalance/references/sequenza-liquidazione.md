# Sequenza di liquidazione fiscalmente efficiente (decumulo)

Quando si è in decumulo, ogni anno serve liquidare €X per viverci. **Da dove prenderli, per pagare meno imposta possibile?** È la dimensione fiscale del decumulo: `it-pianificazione-obiettivi/references/decumulo.md` dice *quanto* è sostenibile prelevare, questa reference dice *come* prelevarlo. Vale solo in regime amministrato; non è consulenza.

## La gerarchia delle fonti (per imposta crescente)

Per finanziare il prelievo annuo, attingere in quest'ordine:

**1. Liquidità e buffer — imposta zero.** Spendere la liquidità (conto corrente, e il buffer di liquidità della strategia bucket) non realizza nulla: nessuna imposta. È la prima fonte, e in particolare la fonte degli **anni negativi** — attingere al buffer invece di vendere il rischioso in perdita è la difesa dal rischio di sequenza (vedi `decumulo.md`).

**2. Flussi già incassati — imposta già assolta.** Dividendi e cedole sono già tassati alla fonte (26%, o 12,5% per i titoli di Stato). Se sono già stati incassati, **spenderli** invece di reinvestirli e poi vendere altro: si evita un realizzo aggiuntivo.

**3. Vendite dal dossier titoli — imposta sui realizzi (26%), da minimizzare.** Quando le prime due fonti non bastano, si vende. Qui si applica la **stessa gerarchia delle leve** del ribilanciamento, perché il problema è identico (scegliere cosa e dove vendere per minimizzare la plus tassata):
   - prima le posizioni in **minus** (Leva 3): zero/negativo, alimentano lo zainetto;
   - poi le posizioni a **plus latente minore** in proporzione al valore (sul prezzo medio di carico);
   - usando lo **zainetto** per compensare le plus, con l'ottimizzazione **broker × tipo fiscale** (vendere reddito diverso presso il broker con zainetto, mai dare per scontata la compensazione cross-broker — vedi `ribilanciamento-multibroker.md`).
   Lo strumento `assets/ribilanciamento-multibroker.py` calcola direttamente questa sequenza: basta impostare la "riduzione" richiesta pari all'importo da liquidare.

**4. Fondo pensione — solo in pensione, ma fiscalmente agevolato.** In fase di erogazione la prestazione del fondo pensione è tassata al **15% scendente fino al 9%** (`max(9%, 15% − 0,30% × (anni − 15))`), e **solo sulla parte di capitale** — i rendimenti già tassati durante l'accumulo non si tassano di nuovo (vedi `it-pianificazione/references/previdenza-complementare.md`). Questa aliquota (9-15%) è **molto più bassa del 26%** che si paga realizzando plus sul dossier: ai fini fiscali, in pensione, attingere al fondo pensione è più efficiente che vendere il dossier in plus. Il vincolo è che il fondo pensione **non è liquidabile liberamente**: almeno il 50% va in rendita vitalizia, al massimo il 50% in capitale, ed è bloccato fino al pensionamento. Quindi è una fonte agevolata ma **strutturata**, non a chiamata.

## La dimensione che cambia tutto: il prelievo è ricorrente

A differenza di un ribilanciamento una tantum, in decumulo si vende **ogni anno**. Due conseguenze:

- **Spalmare i realizzi nel tempo.** Lo zainetto è una risorsa che si rinnova su 4 anni: bruciarlo tutto nel primo anno lascia scoperti gli anni successivi. Conviene dosare le vendite di plus compensabili negli anni, non concentrarle.
- **Il prelievo annuo è anche l'occasione di ribilanciare.** Invece di vendere pro-quota, si finanzia il prelievo vendendo la **classe sovrappesata**: così un'unica operazione preleva *e* ribilancia (come il coordinamento di fine anno di `coordinamento-zainetto.md`, ma ricorrente). Negli **anni positivi** si vende il rischioso cresciuto (ribilancia, finanzia il prelievo, rifornisce il buffer); negli **anni negativi** si attinge al buffer (non si vende in perdita). È il decumulo e il ribilanciamento che diventano lo stesso atto.

## Un pattern tipico in pensione: due fonti complementari

Il fondo pensione (agevolato ma rigido) e il dossier (flessibile ma tassato al 26% sui realizzi) si completano: usare la **rendita del fondo pensione come reddito di base** stabile, e il **dossier come integrazione flessibile** — attingendovi tax-efficient con la gerarchia sopra, e modulandolo negli anni (di più quando i mercati vanno bene, attingendo al buffer quando vanno male). La rigidità dell'uno è compensata dalla flessibilità dell'altro.

## Caveat

I realizzi parziali sono calcolati pro-rata sul prezzo medio di carico, che in amministrato è la base fiscale effettiva (art. 6 c. 4 D.Lgs. 461/97 → art. 306 c. 5 TU 2027). Lo zainetto va verificato per broker, con l'anno di formazione, sul portale dell'intermediario. E le aliquote del fondo pensione e i vincoli capitale/rendita vanno verificati al momento del pensionamento (cambiano con le riforme). La sostenibilità complessiva del prelievo — quanto, non come — è in `it-pianificazione-obiettivi/references/decumulo.md`.
