# Dividendi esteri e doppia imposizione

Un dividendo pagato da una società estera viene tassato due volte: prima nello Stato della società, con una ritenuta alla fonte, poi in Italia. Questa reference spiega quanto resta in tasca all'investitore persona fisica residente, che detiene partecipazioni non qualificate fuori da un'attività d'impresa, e cosa si può recuperare. Riguarda soprattutto chi possiede azioni estere singole: per chi investe in ETF UCITS ad accumulazione il problema esiste, ma resta dentro il fondo (vedi più avanti). Non è consulenza: per i casi concreti serve un commercialista.

## Il meccanismo in due passaggi

1. **Ritenuta estera.** Lo Stato della società trattiene un'imposta alla fonte con la propria aliquota interna. La convenzione contro le doppie imposizioni con l'Italia fissa un tetto più basso (di solito il 15% per l'investitore privato), ma il tetto si ottiene solo con la documentazione richiesta da quello Stato: un modulo prima del pagamento oppure una domanda di rimborso dopo.
2. **Imposta italiana.** Se nella riscossione interviene un intermediario italiano (il caso tipico del dossier presso una banca o un broker italiano), questo applica la ritenuta del 26% a titolo d'imposta **sul netto frontiera**, cioè sull'importo già ridotto dalla ritenuta estera: «Le ritenute del comma 4 sono operate al netto delle ritenute applicate dallo Stato estero» (art. 27 c. 4 e 4-bis DPR 600/73). Il testo del comma 4 riporta ancora «12,50 per cento», ma l'aliquota oggi applicabile è il 26%, come ricorda la stessa Agenzia (risposta 111/2020). Dal 1° gennaio 2027 la regola passa all'art. 55, commi 6 e 7, del testo unico versamenti e riscossione (allegato al D.Lgs. 33/2025), che scrive direttamente 26% e mantiene il netto frontiera.

Il prelievo complessivo, con una ritenuta estera *r*, è quindi:

```
prelievo totale = r + 26% × (1 − r)
```

Il dividendo estero resta **reddito di capitale**: non compensa le minusvalenze dello zainetto (vedi `etf-trap-redditi-capitale.md`).

## Le ritenute nei principali Paesi

Valori per una persona fisica residente in Italia, con una partecipazione di portafoglio. Il prelievo totale è calcolato in regime amministrato con la formula sopra.

| Paese | Ritenuta interna | Tetto della convenzione con l'Italia | Prelievo totale senza rimborso | Prelievo totale con rimborso dell'eccedenza (*) | Come si ottiene il tetto |
|---|---|---|---|---|---|
| Stati Uniti | 30% | 15% | 37,1% con W-8BEN; 48,2% senza | 37,1% | Modulo W-8BEN consegnato all'intermediario prima del pagamento; dopo, solo con una dichiarazione fiscale USA (Form 1040-NR) |
| Francia | 12,8% per le persone fisiche | 15% | 35,5% | non serve: la ritenuta interna è già sotto il tetto | Di norma nessuna pratica, se l'intermediario ti identifica come persona fisica. Se in estratto conto compare il 25% (aliquota per chi non è documentato come persona fisica), chiedere all'intermediario di correggere la documentazione; per l'eccedenza già trattenuta serve una domanda di rimborso all'amministrazione francese |
| Germania | 26,375% (25% più il 5,5% di contributo di solidarietà) | 15% | 45,5% | 37,1% | Domanda di rimborso di 11,375 punti al BZSt, solo online, entro quattro anni dalla fine dell'anno d'incasso |
| Svizzera | 35% | 15% | 51,9% | 37,1% | Domanda di rimborso di 20 punti all'ESTV, modulo 95 per i residenti in Italia |
| Irlanda | 25% | 15%, ma la legge irlandese esenta i residenti UE | 44,5% | 26,0% | Modulo V2A certificato dall'Agenzia delle Entrate, consegnato alla società o all'intermediario; se la ritenuta è già stata applicata, domanda di rimborso |
| Paesi Bassi | 15% | 15% | 37,1% | non serve | Nessuna pratica |
| Regno Unito | Nessuna imposta per la generalità dei non residenti | 15% (non rilevante) | 26,0% | non serve | Nessuna pratica |

(*) Ipotesi: anche la somma rimborsata dallo Stato estero sconta il 26% italiano, come in linea di principio dovrebbe, perché è parte del dividendo. Come dichiararla o farla tassare va verificato con l'intermediario o il commercialista. Con questa ipotesi i Paesi in cui la ritenuta effettiva resta al 15% (Stati Uniti con W-8BEN, Germania e Svizzera dopo il rimborso, Paesi Bassi) convergono al 37,1%. La Francia si ferma al 35,5% perché la ritenuta interna è sotto il tetto; Irlanda (con V2A) e Regno Unito al 26,0%, perché la ritenuta estera si azzera.

Fonti delle aliquote:
- **Stati Uniti**: 30% o aliquota di trattato con W-8BEN (IRS); tetto del 15% nell'art. 10 par. 2 lett. b della convenzione del 1999 (L. 20/2009). Il W-8BEN si consegna a chi lo richiede, non all'IRS, e vale fino alla fine del terzo anno solare successivo alla firma.
- **Francia**: 12,8% (art. 187 CGI, BOFiP); tetto del 15% nell'art. 10 della convenzione del 1989 (L. 20/1992).
- **Germania**: 25% (§ 43a EStG) e 5,5% di solidarietà (§ 4 SolZG); tetto del 15% nell'art. 10 della convenzione del 1989 (L. 459/1992); procedura di rimborso del BZSt.
- **Svizzera**: 35% (ESTV); tetto del 15% nell'art. 10 della convenzione del 1976 (testo Fedlex aggiornato al 17 luglio 2023).
- **Irlanda**: 25% e modulo V2A (Revenue); tetto del 15% nell'art. 9 della convenzione del 1971 (L. 583/1974).
- **Paesi Bassi**: 15% (Belastingdienst); tetto del 15% nell'art. 10 della convenzione del 1990 (L. 305/1993).
- **Regno Unito**: «UK dividend income remains non-taxable on the majority of non-UK residents» (HMRC, SAIM5120).

L'attestazione di residenza fiscale italiana richiesta dai moduli esteri si fa firmare e timbrare da una Direzione provinciale dell'Agenzia delle Entrate; se lo Stato estero ha un proprio modello, si usa quello (scheda AdE sui rimborsi convenzionali). Le pratiche di rimborso hanno un costo, in tempo e talvolta in commissioni dell'intermediario: per importi piccoli possono non valere la pena.

## Esempio: €1.000 di dividendo USA in regime amministrato

```
                                   Con W-8BEN    Senza W-8BEN
Dividendo lordo                      1.000,00        1.000,00
Ritenuta USA                          −150,00 (15%)   −300,00 (30%)
Netto frontiera                        850,00          700,00
Ritenuta italiana 26% sul netto       −221,00         −182,00
Netto accreditato                      629,00          518,00
Prelievo totale                        371,00 (37,1%)  482,00 (48,2%)
```

Senza W-8BEN si perdono €111 ogni €1.000 di dividendo lordo. Non sono €150 perché il netto frontiera attutisce: la ritenuta italiana si calcola su una base più piccola. Il W-8BEN è il primo controllo da fare su qualsiasi dossier con azioni USA.

Per confronto, lo stesso dividendo incassato tramite un broker estero che non fa da sostituto d'imposta (regime dichiarativo). Secondo l'Agenzia, l'imposta sostitutiva del 26% (art. 18 TUIR, dal 2027 art. 20 D.Lgs. 117/2026) si calcola sul **lordo** (risposta 111/2020). Le istruzioni del Modello Redditi PF 2026 chiedono di indicare nel rigo RM31 l'importo «al lordo di eventuali ritenute subìte nello Stato estero»:

```
Dividendo lordo                      1.000,00
Ritenuta USA con W-8BEN               −150,00
Incassato                              850,00
Imposta sostitutiva 26% sul lordo     −260,00
Netto                                  590,00   prelievo totale 41,0%
```

## Il credito per le imposte estere: posizione dell'Agenzia e giurisprudenza

L'art. 165 TUIR (dal 2027 art. 185 D.Lgs. 117/2026) ammette in detrazione le imposte pagate all'estero solo «se alla formazione del reddito complessivo concorrono redditi prodotti all'estero». I dividendi da partecipazioni non qualificate non entrano nel reddito complessivo: sono tassati con ritenuta a titolo d'imposta o con imposta sostitutiva, e il contribuente non può scegliere la tassazione ordinaria (istruzioni Redditi PF 2026, quadro RM). Per questo l'Agenzia delle Entrate ritiene che **il credito non spetti** (risposta 111/2020). In amministrato l'intermediario non applica alcun credito: l'unico sollievo è il netto frontiera.

La Cassazione ha preso una strada diversa in due sentenze (Sez. V, n. 25698/2022 e n. 10204/2024), relative a dividendi e redditi USA incassati direttamente. La convenzione Italia-USA esclude la detrazione solo quando l'imposizione mediante ritenuta a titolo d'imposta avviene «su richiesta del beneficiario». La Corte ne ha dedotto che, se la tassazione sostitutiva è obbligatoria, la convenzione prevale e l'imposta pagata negli USA va riconosciuta. Altre convenzioni (Cipro, Malta, Singapore e altre citate nelle sentenze) escludono invece il credito «anche su richiesta» del contribuente, cioè sempre. La formula «su richiesta» senza «anche» si ritrova nei testi pubblicati dal MEF e su Fedlex delle convenzioni con Svizzera, Francia, Germania e Paesi Bassi.

Sono **aperture giurisprudenziali, non una regola**. Farle valere richiede un'istanza di rimborso all'Agenzia, con probabile contenzioso, e un commercialista che valuti la convenzione del singolo Paese. Se il credito fosse riconosciuto, nel caso dichiarativo dell'esempio il prelievo complessivo scenderebbe verso il 26%: è questa la posta in gioco.

Dal 1° gennaio 2027 l'art. 165 TUIR diventa l'art. 185 del nuovo testo unico delle imposte sui redditi (D.Lgs. 117/2026), con lo stesso comma 1. L'art. 18 TUIR diventa l'art. 20.

## ETF ad accumulazione, ETF a distribuzione e azioni dirette

**Dentro un ETF la ritenuta estera non si recupera.** Un ETF UCITS incassa i dividendi delle società in portafoglio e subisce le ritenute dei rispettivi Stati, alle aliquote che spettano al fondo secondo il suo domicilio (per la ritenuta USA sugli ETF irlandesi vedi `it-pianificazione-obiettivi/references/selezione-strumenti.md`). Il beneficiario del dividendo è il fondo, non l'investitore. L'investitore non può quindi presentare un W-8BEN, chiedere un rimborso o far valere un credito. La ritenuta non passa dal suo estratto conto: è già dentro il rendimento del fondo.

**Accumulazione o distribuzione non cambia la ritenuta estera, cambia quando si paga il 26% italiano.**
- ETF **a distribuzione**: ogni provento distribuito è reddito di capitale tassato al 26% (art. 10-ter L. 77/1983; dal 2027 art. 59 dell'allegato al D.Lgs. 33/2025). Per un ETF irlandese la distribuzione all'investitore non residente arriva di norma senza imposta irlandese, grazie alla dichiarazione di non residenza o alle «equivalent measures» del fondo (Revenue, Tax and Duty Manual 27-01a-02).
- ETF **ad accumulazione**: la stessa ritenuta estera a livello di fondo, ma il 26% italiano si paga solo alla vendita. Nel frattempo l'imposta differita continua a rendere.

**Con le azioni dirette la ritenuta la subisci tu, e qualcosa si può fare.** W-8BEN per gli USA (37,1% invece di 48,2%), domanda di rimborso per Germania e Svizzera (37,1% invece di 45,5% e 51,9%), V2A per l'Irlanda (26% invece di 44,5%). Un titolo svizzero ad alto dividendo, tenuto in amministrato senza chiedere il rimborso, lascia all'investitore meno della metà del dividendo lordo.

Come per la Tobin tax, l'impatto non va sovrastimato. Il profilo tipico del plugin, un ETF UCITS irlandese ad accumulazione, non richiede pratiche: il costo delle ritenute estere è già nel rendimento del fondo. Il tema conta per chi tiene azioni estere singole con dividendi rilevanti, soprattutto svizzere, tedesche o USA senza W-8BEN.

## Cosa resta da verificare col commercialista

- Il trattamento in Italia delle somme rimborsate dallo Stato estero (ritenuta dell'intermediario o dichiarazione).
- In dichiarativo, se la base del 26% sia il lordo, come ritiene l'Agenzia (rigo RM31), o il netto frontiera, come in amministrato: sul dividendo USA la differenza è di 3,9 punti (41,0% contro 37,1%).
- Le aliquote e i moduli dei Paesi che non sono in tabella. Per i dividendi da Stati a fiscalità privilegiata valgono regole diverse (art. 27 c. 4 lett. b DPR 600/73).
- L'istanza di rimborso basata sulla giurisprudenza della Cassazione: requisiti, termini e probabilità di successo per la convenzione del singolo Paese.
- I casi particolari: dividendi in azioni o in natura, REIT e fondi esteri quotati, ADR, partecipazioni qualificate.
- Le cedole di obbligazioni estere: seguono un meccanismo diverso, non trattato in questa reference.

*Ritenuta del 26% sul netto frontiera in amministrato (art. 27 c. 4 e 4-bis DPR 600/73; dal 2027 art. 55 c. 6-7 dell'all. al D.Lgs. 33/2025), lordo in dichiarativo e niente credito art. 165 secondo l'AdE (risp. 111/2020; istr. Redditi PF 2026, rigo RM31), Cass. 25698/2022 e 10204/2024, art. 165 TUIR (dal 2027 art. 185 D.Lgs. 117/2026), tetti convenzionali (convenzioni con USA, Francia, Germania, Svizzera, Irlanda, Paesi Bassi; testi MEF e Fedlex) e ritenute interne (IRS, BOFiP, EStG/SolZG e BZSt, ESTV, Revenue, Belastingdienst, HMRC) — Verificato: 2026-10.*
