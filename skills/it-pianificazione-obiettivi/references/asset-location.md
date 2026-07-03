# Asset location avanzato (in quale contenitore fiscale)

Questa reference affronta l'**asset location**: non *cosa* comprare (quello è `selezione-strumenti.md`) né *quanto* azionario (quello è `orizzonte-allocazione.md`), ma in **quale contenitore fiscale** mettere ciascun obiettivo per minimizzare le tasse. È materiale didattico per uso personale; non è consulenza.

## Location ≠ allocation

L'asset allocation decide il mix azionario/obbligazionario di un obiettivo. L'asset location decide il *wrapper* in cui quel mix vive — e in Italia il wrapper cambia la fiscalità in modo sostanziale: stesso ETF azionario può essere tassato al 26%, allo 0%, o al 20% a seconda del contenitore.

## La peculiarità italiana: spazio agevolato scarso e vincolato

Negli USA l'asset location è ricca perché esistono conti tax-deferred (401k) e tax-free (Roth) in cui puoi mettere *qualsiasi* asset. In Italia **non esiste un conto tax-deferred generico**: lo spazio fiscalmente agevolato è poco e legato a uno scopo preciso.

- L'unico contenitore ampiamente agevolato (**fondo pensione**) è vincolato alla pensione.
- L'unico esente da imposta (**PIR**) impone una forte concentrazione su PMI italiane.
- Tutto il resto vive nel **dossier ordinario** al 26%/12,5%.

Quindi l'asset location in Italia non è "distribuisci gli asset tra i conti agevolati", ma poche decisioni mirate: massimizzare il fondo pensione per la pensione, usare bene il dossier per tutto il resto, e ricorrere a PIR/polizze solo quando i loro vincoli specifici coincidono con l'obiettivo.

## I contenitori e la loro fiscalità

### Dossier titoli in regime amministrato (il default)
- Plusvalenze al **26%** (12,5% titoli di Stato e white list), tassate alla realizzazione, broker sostituto d'imposta.
- ⚠️ **Asimmetria** (vedi `it-tax-optimization`): su ETF UCITS armonizzati la plus è reddito di capitale (NON compensabile), la minus è reddito diverso (compensabile).
- Imposta di bollo 0,2%/anno sul controvalore.
- **Massima flessibilità e liquidità, nessun vincolo temporale.** È il contenitore giusto per tutto ciò che non ha una ragione specifica per stare altrove.

### Fondo pensione (il contenitore agevolato per la PENSIONE)
- Contributi **deducibili dall'IRPEF** (fino a €5.300/anno, vedi `it-pianificazione`), rendimenti tassati al **20%** (12,5% titoli di Stato), prestazione finale al **15%→9%**.
- ⚠️ **Vincolato fino alla pensione** (con eccezioni: anticipo prima casa dopo 8 anni, spese sanitarie, RITA, ecc.).
- È il contenitore **dominante per l'obiettivo pensione** (la deduzione + l'aliquota ridotta sui rendimenti + la tassazione agevolata della prestazione battono il dossier), ma proprio per il vincolo **non** è utilizzabile per obiettivi che si spendono prima (casa, università). Per i forfettari la deduzione non c'è (vedi `it-pianificazione-autonomi`).

### PIR ordinario (il contenitore ESENTE, ma vincolato)
- **Esenzione totale** da imposta su plusvalenze, dividendi e interessi (0% invece di 26%), **e dall'imposta di successione**, se gli strumenti restano nel piano almeno **5 anni** (i 5 anni decorrono da *ogni* versamento).
- Limiti: da €500 a **€40.000/anno**, massimo **€200.000** complessivi; un solo PIR ordinario a persona.
- Vincolo di composizione **70/25/5**: almeno il 70% in strumenti di imprese italiane (o UE con stabile organizzazione in Italia); di quel 70%, almeno il 25% in società fuori dal FTSE MIB e il 5% in micro-imprese; massimo 10% su un singolo emittente.
- ⚠️ **Il prezzo dell'esenzione è la concentrazione**: l'Italia vale circa il 2% del mercato azionario mondiale, e il PIR ti obbliga a sovrappesare PMI italiane, rinunciando alla diversificazione globale. I costi di gestione dei prodotti PIR (tipicamente 1,2–1,35%/anno) possono **erodere o annullare** il vantaggio fiscale. Vendere prima dei 5 anni fa decadere il beneficio (salvo reinvestire entro 90 giorni in strumenti PIR-compliant).
- **Quando ha senso**: per una *quota* del portafoglio di lungo termine, se si accetta consapevolmente la concentrazione italiana e i costi, in cambio dello 0% di tasse. Mai una fetta dominante del patrimonio. I PIR alternativi (€300k/anno, 1,5M totale, illiquidi) sono per investitori esperti con patrimoni elevati — fuori scope retail.

### Polizze vita (Ramo I/III): differimento e successione
- **Differimento**: i rendimenti sono tassati solo al riscatto (non annualmente), quindi compongono al lordo. Ramo I (gestione separata) offre garanzia del capitale e consolidamento; Ramo III (unit/index linked) è esposto al mercato.
- **Successione**: la prestazione caso morte è **fuori dall'asse ereditario** (esente da imposta di successione) ed esente IRPEF per il beneficiario. È un vantaggio reale di pianificazione successoria.
- ⚠️ **Costi tipicamente alti** (caricamenti, commissioni) che spesso mangiano il vantaggio fiscale. Strumento più di *estate planning* che di investimento puro: ha senso quando la finalità successoria è prioritaria, non come wrapper di rendimento.

### Conto deposito (liquidità)
- Interessi al 26%, bollo 0,2%, garanzia FITD €100k. Il contenitore per il fondo di emergenza e gli obiettivi a brevissimo. Nessun azionario qui.

### Nota: titoli di Stato (BTP)
Anche tenuti nel dossier, i titoli di Stato hanno aliquota **12,5%** ed **esenzione dall'imposta di successione**. È una mini-vittoria di location *dentro* il dossier (vedi `orizzonte-allocazione.md`): la parte sicura degli obiettivi a medio termine in BTP costa meno fiscalmente.

## Il framework: quale contenitore per quale obiettivo

| Obiettivo | Contenitore di default | Quando deviare |
|---|---|---|
| **Pensione integrativa** | Fondo pensione | È dominante; instradato a `it-pianificazione`/`-autonomi`. Per forfettari valutare (no deduzione) |
| **Fondo emergenza / breve** | Conto deposito | Mai investito; liquidità e certezza |
| **Medio termine (parte sicura)** | BTP nel dossier (12,5%) | — |
| **Lungo termine (crescita)** | Dossier amministrato, ETF accumulazione | Una *quota* in PIR se si accetta concentrazione IT + lock 5 anni per lo 0% |
| **Obiettivo con data fissa vicina** | Dossier (flessibilità) → conto deposito avvicinandosi | No fondo pensione (vincolato), cautela su PIR (concentrazione su goal rigido) |
| **Trasferimento generazionale** | Polizza vita / BTP / PIR (esenti successione) | Solo se la finalità successoria è prioritaria e i costi sono accettabili |

Principio guida: **il dossier amministrato è il default flessibile**; si devia verso un contenitore vincolato (fondo pensione, PIR, polizza) **solo quando il vincolo di quel contenitore coincide con la natura dell'obiettivo** e il vantaggio fiscale supera costi e perdita di flessibilità/diversificazione.

## Le tensioni da comunicare sempre

1. **Fondo pensione: dominante per la pensione, inutilizzabile per altro.** Il vincolo è il punto: ottimo per la pensione (denaro comunque "bloccato per scopo"), ma non puoi usarlo per la casa o l'università. Non forzare obiettivi a breve/medio dentro il fondo pensione.
2. **PIR: lo 0% ha un costo reale.** La concentrazione su PMI italiane (Italia ≈ 2% del mondo) è un costo di diversificazione, e i costi dei prodotti possono annullare il beneficio. Solo una quota, solo se consapevoli.
3. **Polizze: il vantaggio successorio spesso lo mangiano i costi.** Valutare il costo totale contro il beneficio fiscale/successorio effettivo, non sottoscrivere per il solo wrapper.
4. **Il 12,5% dei titoli di Stato è location gratis.** Nessun vincolo aggiuntivo rispetto al dossier, solo aliquota più bassa: sfruttarlo per la parte sicura.

## Applicato agli obiettivi tipici

- **Fondo emergenza** → conto deposito (liquidità, FITD). Nessuna ottimizzazione fiscale da cercare: serve sicurezza.
- **Università (data fissa, si spende)** → dossier amministrato con ETF ad accumulazione. NON fondo pensione (vincolato fino alla pensione, non disponibile per la retta). PIR possibile in teoria su 19 anni, ma la concentrazione italiana su un obiettivo che *devi* centrare a una data precisa è un rischio mal posto: al più una quota minoritaria, con cautela. La parte sicura, avvicinandosi, in BTP/conto deposito.
- **Pensione** → fondo pensione, il contenitore dominante (vedi `it-pianificazione`).
- **Patrimonio di lungo periodo senza data** → dossier come base; una quota in PIR è più difendibile qui (orizzonte lungo, nessuna data rigida, si tollera la concentrazione per lo 0%); polizza solo se la finalità è successoria.

## Interazione con le altre skill

- **`it-pianificazione` / `-autonomi`**: il fondo pensione (il contenitore della pensione) è trattato lì, con deducibilità e tassazione. L'asset location qui spiega *perché* è il contenitore giusto per quell'obiettivo e perché non per altri.
- **`it-tax-optimization`**: l'asimmetria reddito diverso/capitale e le aliquote (26%/12,5%) governano la fiscalità *dentro* il dossier; la location decide *quale* wrapper, la tax-optimization come gestirlo una volta dentro.
- **`selezione-strumenti.md`**: la scelta dello strumento (ETF UCITS, accumulazione, domicilio) avviene *dentro* il contenitore scelto. Location e selezione sono complementari: prima il wrapper, poi lo strumento nel wrapper.
- **`it-rebalance`**: spostamenti tra contenitori diversi possono avere costi e vincoli (es. uscire da un PIR prima dei 5 anni fa decadere il beneficio); il ribilanciamento ne tiene conto.

## Heuristic per la skill

1. **Dossier amministrato come default**: flessibile, liquido, nessun vincolo. Si devia solo con una ragione precisa.
2. **Pensione → fondo pensione, e basta lì**: dominante per la pensione, vincolato e quindi inadatto ad altri obiettivi.
3. **PIR solo per una quota e solo consapevolmente**: lo 0% costa concentrazione italiana e commissioni; mai una fetta dominante, mai su un obiettivo a data rigida.
4. **Sfruttare il 12,5% dei titoli di Stato**: location vantaggiosa senza vincoli aggiuntivi.
5. **Polizze solo per finalità successoria reale**: valutare i costi, non sottoscrivere per il wrapper.
6. **Non è consulenza**: i contenitori hanno vincoli legali e costi variabili; le scelte concrete (e l'adeguatezza) vanno verificate con un consulente abilitato e un commercialista.
