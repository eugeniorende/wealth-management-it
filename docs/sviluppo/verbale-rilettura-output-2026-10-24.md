# Verbale: rilettura degli output operativi (decisione 4)

Data: 24/10/2026. Branch: `feature/prepubblicazione-verifiche`, sopra T14. Voce di `ROADMAP.md` «Rilettura degli output operativi rispetto alla postura "educativa" (decisione 4)» e § 2.6 di `docs/sviluppo/HANDOFF.md`.

La decisione 4 dice: «La OPZIONE sulla leva di rischio, il "versa fino a €5.300" e il CSV degli ordini restano, ma solo quando le condizioni sono rispettate. Il disclaimer va anche nei commands e nel CSV.» La rilettura ha guardato ogni output che un utente può portarsi via (stdout, CSV, Word, Excel) e le sezioni «Formato output» delle sei skill, chiedendosi due cose: l'output operativo compare solo quando il suo gate è soddisfatto? Chi legge l'output da solo, senza la conversazione, capisce che è educativo e su quali dati è costruito?

## Cosa è stato eseguito

```bash
python skills/it-pianificazione-obiettivi/assets/montecarlo-obiettivi.py skills/it-pianificazione-obiettivi/assets/pianificatore-obiettivi.xlsx
python skills/it-rebalance/assets/ribilanciamento-multibroker.py --out <cartella>
python skills/it-tax-optimization/assets/importa-estratto-broker.py tests/fixtures/estratto-broker-test.csv tests/fixtures/zainetto-anomalie.csv --anno 2026
python skills/it-revisione/assets/genera-ips.py <cartella>/ips.docx
```

Più la lettura delle stringhe e delle formule dei sei Excel (sharedStrings e celle con testo) e delle sezioni «Formato output», «Step 5» e «Anti-pattern» delle sei SKILL.md.

## Esiti

| Output | Gate e postura | Esito |
|---|---|---|
| OPZIONE sulla leva di rischio (`montecarlo-obiettivi.py`) | Compare solo per un obiettivo desiderabile, fuori dalla finestra di de-risking e non già in linea; altrimenti stampa INADATTA o CONTROPRODUCENTE con il motivo. Quando compare mostra il costo sul 10° percentile e chiude con «Ha senso solo se reggi quel downside». | Conforme, nessuna modifica |
| «versa fino a €5.300» (Excel `proiezione-pensione.xlsx`) | La cella dello spazio residuo dice «un tetto fiscale, non un importo consigliato» (PR #28). | Conforme |
| Lo stesso tetto nella skill `it-pianificazione` (Pattern P1) | Il pattern si chiamava «Massimizzare contributo deducibile», senza la riserva dell'Excel. | Corretto: «Usare lo spazio deducibile», con la stessa frase dell'Excel |
| CSV degli ordini (`ribilanciamento-multibroker.py`) | Gate della Leva 4 (banda larga, rientro a metà banda), NOTA con il disclaimer in ultima riga, nessun CSV senza ordini. | Gate conforme. Tre difetti corretti, sotto |
| Stdout dell'importatore broker | Disclaimer in fondo, «OCCASIONE» descrittiva (quanto si potrebbe realizzare a imposta zero). L'intestazione delle minus latenti diceva «vendere per caricare lo zainetto», un'istruzione. | Corretto: «venderle caricherebbe lo zainetto» |
| IPS in Word (`genera-ips.py`) | Disclaimer in copertina e nota finale; titolo e lingua dal T14. Senza `--dati` il documento era quello di «Mario Rossi» senza dirlo: l'avviso stava solo sullo stdout. | Corretto: avviso «DATI DI ESEMPIO» in copertina |
| «Formato output» di `it-pianificazione` e `it-pianificazione-autonomi` | La postura «leve come scenari quantificati, non raccomandazioni personali» stava solo nei comandi `/pensione` e `/pensione-autonomi`, diventati alias con il T14. Le skill intitolavano il passo «Raccomandazioni d'azione» con la voce «Cosa fare». | Corretto: «Leve da valutare (scenari, non raccomandazioni)», «Cosa cambia», la scelta resta all'utente |
| «Formato output» di `it-rebalance` | «Raccomandazioni e alternative» riguarda il piano fiscale sull'allocazione target scelta dall'utente, con il gate della Leva 4: è l'uscita operativa che la decisione 4 tiene. La skill dichiara di non raccomandare l'allocazione. | Conforme |
| `it-tax-optimization`, Pattern D | «Raccomandazione + scadenza per l'opzione» riguarda la scelta del regime (amministrato o dichiarativo), con il rinvio al commercialista. | Conforme |
| `it-pianificazione-obiettivi`, `it-revisione` | Allocazioni-tipo dichiarate «non raccomandazioni»; la revisione propone azioni ma rinvia al professionista (anti-pattern esplicito). | Conformi |
| Excel di autonomi, cruscotto, tracker, IPS | Deducibilità descritta come regola fiscale; «cadenza consigliata» del tracker riguarda la manutenzione del foglio. | Conformi |

I tre difetti del CSV degli ordini:

1. la colonna `categoria_fiscale` conteneva la forma breve interna (`diverso`) invece del valore del vocabolario (`reddito_diverso`), contro il glossario del README e lo schema di input della stessa skill;
2. senza `--dati` il CSV era costruito sui dati d'esempio senza dirlo: ora la riga NOTA comincia con «DATI DI ESEMPIO»;
3. con `--out` assoluto l'intestazione della sezione 5 stampava `.//percorso/`.

## Test che vincolano gli esiti

- `t_dati_ribilanciamento`: `categoria_fiscale` uguale a `reddito_diverso`, NOTA senza «esempio» con `--dati` e con «DATI DI ESEMPIO» senza, intestazione con il percorso di `--out`.
- `t_csv_italiano`: la riga di vendita con `reddito_diverso`.
- `t_dati_ips`: «DATI DI ESEMPIO» in copertina solo senza `--dati`.

Ogni test è stato visto fallire sul codice di prima e passare dopo la correzione.

## Fuori da questa rilettura

Restano da guardare con un utente vero, non con i dati d'esempio, la lunghezza e il tono dei report prodotti dalle skill in chat: dipendono dal modello e non da un output degli script.
