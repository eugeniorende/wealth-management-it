# Cruscotto grafico del piano, pubblicabile come Artifact (design)

Stato: spec da rivedere, 25/10/2026. Nasce dal brainstorming con il proprietario sulla richiesta: «integrare nel plugin la possibilità di sfruttare la creazione di artefatti di Claude e rendere consultabile in maniera graficata il risultato della pianificazione». Tema di ROADMAP: **T17**.

> ⚠️ Come il resto del plugin: strumento di pianificazione personale, non consulenza finanziaria o fiscale.

## 1. Obiettivo e perimetro

**Cosa si vuole.** Una pagina unica che mostri in grafici il risultato della pianificazione: allocazione, obiettivi, glide path, pensione, capitale umano, fiscalità e ribilanciamento. I numeri vengono **solo** dai JSON che gli script già scrivono con `--json`: la pagina li disegna, non li ricalcola e Claude non li riscrive. La pagina è un file HTML autosufficiente nella cartella di lavoro; su richiesta esplicita dell'utente Claude la pubblica come Artifact su claude.ai.

**Decisioni prese nel brainstorming:**

| # | Decisione | Scelta |
|---|---|---|
| D1 | Ambienti | Tutti e tre: Claude Code (CLI e desktop), Cowork, claude.ai. Il formato comune è un file HTML autosufficiente |
| D2 | Perimetro | Cruscotto unico del piano (non una vista per skill), con le sezioni che compaiono solo se c'è il JSON |
| D3 | Pubblicazione | Il file HTML si genera sempre in locale; la pubblicazione come Artifact si propone e si fa **solo se l'utente dice sì**, ogni volta |
| D4 | Rendering | Approccio B: template HTML + CSS + JavaScript vanilla fisso nel plugin, a cui lo script inietta i dati; i grafici li disegna il browser in SVG |
| D5 | Sezioni | Già nella prima versione anche fiscalità (zainetto per broker e scadenza) e ribilanciamento (drift contro bande, ordini) |
| D6 | Dove vive | `it-revisione` (è il livello di sintesi), con il nuovo comando `/cruscotto` |
| D7 | Test del rendering | Chromium e Playwright: saltato in locale se mancano, obbligatorio in CI con `RICHIEDI_BROWSER=1` |

**Fuori perimetro (YAGNI):** cruscotto in forma anonimizzata (D3 lo copre con la conferma); viste separate per skill; storico di più revisioni a confronto; ponte pensione e riscatto della laurea (i loro JSON si riconoscono e si ignorano, §3.2); stato condiviso o database dell'Artifact; interattività oltre ai tooltip e al tema; esportazione in PDF o immagine; librerie di grafici.

## 2. Componenti

| File | Cosa fa |
|---|---|
| `skills/it-revisione/assets/cruscotto.html` | Template fisso: HTML, CSS e JS vanilla in un solo file, nessuna risorsa esterna. Contiene **esattamente una volta** il segnaposto `__DATI_CRUSCOTTO__` dentro `<script id="dati" type="application/json">`. Legge quel blocco, disegna le sezioni presenti, nasconde le altre |
| `skills/it-revisione/assets/genera-cruscotto.py` | Riconosce i JSON passati con `--from`, ne estrae i campi usati in un unico oggetto (il «bundle», §4), lo incorpora nel template e scrive `cruscotto.html` |
| `skills/it-rebalance/assets/ribilanciamento-multibroker.py` | Nuova opzione `--json FILE`: il piano in JSON (§3.3). Oggi lo script stampa il piano e scrive i CSV degli ordini, ma non ha un `--json` |
| `commands/cruscotto.md` | Alias su `it-revisione`, passo «Cruscotto grafico», con il disclaimer |

### 2.1 `genera-cruscotto.py`: interfaccia

```
python "${CLAUDE_SKILL_DIR}/assets/genera-cruscotto.py" --from alloc.json --from glide.json \
    --from mc-obiettivi.json --from inps.json --from mc.json --from netto.json \
    --from capitale-umano-out.json --from broker.json --from ribilancia.json \
    [-o cruscotto.html] [--json bundle.json] [--data AAAA-MM-GG]
```

- `--from FILE` ripetibile, almeno uno; l'ordine non conta.
- `-o FILE`: l'HTML (default `cruscotto.html` nella cartella corrente).
- `--json FILE`: scrive anche il bundle normalizzato (per i test e per chi vuole ispezionare cosa finisce nella pagina).
- `--data AAAA-MM-GG`: la data in testata (default oggi); serve ai test per un output riproducibile.
- Interfaccia comune degli script (T9): `--help`; exit 0 riuscito, 1 errore nei dati con messaggio `ERRORE:` su stderr, 2 riga di comando errata; output UTF-8 su qualunque console. A fine esecuzione stampa il percorso dell'HTML, le sezioni incluse e, per ogni `--from`, il tipo riconosciuto.

### 2.2 Il template: regole

- **Autosufficiente**: nessun `http://`, `https://`, `//` in `src`/`href`, `@import`, font esterni. Funziona aperto dal disco, offline, e dentro un Artifact.
- **Sicuro con i dati**: tutto ciò che viene dal bundle si scrive nel DOM con `textContent` o con attributi SVG impostati da `setAttribute`, **mai** con `innerHTML`. Lo script Python, incorporando il JSON, sostituisce `<` con `<` (così nessuna stringa può chiudere il tag `<script>`).
- **Numeri in formato italiano** con `Intl.NumberFormat('it-IT')`: `€ 36.000`, `51,4%`, come gli script.
- **Tema** chiaro e scuro: colori come variabili su `:root`, ridefinite in `@media (prefers-color-scheme: dark)`; `body` con sfondo esplicito.
- **Larghezza da telefono**: a 375px nessuno scroll orizzontale della pagina; i grafici si ridimensionano con `viewBox`; le tabelle larghe scorrono dentro il loro contenitore.
- **Grafici**: SVG costruiti dal JS con poche funzioni riusabili (barre orizzontali, barre con fascia P10–P90, linee nel tempo con area di fascia, barre impilate). Tooltip con l'elemento `<title>` dell'SVG. Ogni grafico ha anche il dato in testo vicino (etichette o tabella), così la pagina si legge senza passare il mouse.
- **Senza dati**: una sezione senza dati non c'è (nemmeno il titolo); se il bundle non ha nessuna sezione la pagina lo dice.
- **Disclaimer** sempre in fondo, e l'avviso «bozza educativa» in testata.

## 3. I JSON in ingresso

### 3.1 Riconoscimento dalle chiavi

Il tipo di un file si riconosce dalle chiavi di primo livello (i JSON di oggi non hanno un campo «tipo»). Firme, verificate sugli output degli script sugli esempi del plugin il 25/10/2026:

| Tipo | Script | Firma (chiavi presenti) |
|---|---|---|
| `allocatore` | `allocatore-capitale.py --json` | `aggregato`, `capitale`, `obiettivi[].allocato` |
| `glide_path` | `glidepath-obiettivi.py --json` | `anni`, `portafoglio`, `finestra`, `obiettivi[].quota_azionaria` |
| `mc_obiettivi` | `montecarlo-obiettivi.py --json` | `n_sim`, `obiettivi[].probabilita_successo` |
| `inps` | `proiezione-inps.py --json` | `pensione_inps_lorda_annua`, `coefficiente_trasformazione` |
| `mc_pensione` | `montecarlo-pensione.py --json` | `tasso_sostituzione_lordo` (oggetto con `p10`, `mediana`, `p90`), `montante_fp` |
| `netto_pensione` | `netto-pensione.py --json` | `scenari`, `netto_pensione_inps` |
| `capitale_umano` | `capitale-umano.py --json` | `bilancio`, `proiezione`, `esposizione_totale` |
| `broker` | `importa-estratto-broker.py --json` | `posizioni`, `zainetto`, `analisi.per_broker` |
| `ribilanciamento` | `ribilanciamento-multibroker.py --json` (nuovo) | `drift`, `risultante`, `ordini` |

Le firme vivono in una tabella in testa allo script, una riga per tipo: la funzione di riconoscimento è una sola. Un file che soddisfa due firme è un errore dello script (un test lo esclude sugli output reali).

### 3.2 Casi d'errore

- File mancante, non JSON o non un oggetto → `ERRORE:` con il nome del file, exit 1.
- File che non corrisponde a nessuna firma → `ERRORE: «x.json» non è un output riconosciuto` con l'elenco dei tipi accettati, exit 1.
- JSON noti ma non usati dal cruscotto (`importa-previdenza.py`, `ponte-pensione.py`, `riscatto-laurea.py`): riconosciuti da una firma, segnalati con `ℹ … ignorato: il cruscotto non lo usa` e saltati. Così la catena previdenziale si può passare intera.
- Due file dello stesso tipo (es. `mc.json` e `mc-uscita.json`) → `ERRORE:` con i due nomi: il cruscotto non sceglie al posto dell'utente.
- Un campo usato mancante o del tipo sbagliato in un file riconosciuto → `ERRORE:` con file e chiave (es. `«mc.json»: manca tasso_sostituzione_lordo.p90`).
- Il template senza il segnaposto, o con il segnaposto più di una volta → `ERRORE:` (protegge da un template rotto).

### 3.3 `--json` del ribilanciamento

Il nuovo `--json FILE` di `ribilanciamento-multibroker.py` scrive, dal dict restituito dal piano e dagli ordini già calcolati (nessun calcolo nuovo):

- `totale`, `totale_post`, `imposta`, `prelievo`, `entrate`, `liquidato`;
- `drift`: per classe `peso`, `target`, `drift`, `tight` (banda stretta), `wide` (banda larga), `fuori_banda`, `esito`, `motivo`;
- `risultante`: il peso per classe dopo il piano;
- `zainetto`: l'uso dello zainetto per broker come già lo restituisce il piano;
- `ordini`: la lista degli ordini eseguibili, gli stessi dei CSV.

I nomi delle chiavi restano quelli interni del piano; la skill `it-rebalance` li documenta in «Formato output». Con `--json` i CSV si scrivono come prima.

## 4. Il bundle e le sezioni

Il bundle contiene **solo i campi che la pagina mostra**: è anche una misura di privacy, perché ciò che non serve al grafico non finisce nell'Artifact. In particolare le singole posizioni dell'estratto (ISIN, descrizioni, quantità) **non** entrano: dalla fiscalità passano gli aggregati per broker e le righe dello zainetto. Gli ordini del ribilanciamento entrano con broker, operazione, classe, categoria fiscale, importo e imposta, perché sono il risultato da leggere (gli ordini dello script non hanno uno strumento: la colonna ISIN dei CSV la compila l'utente).

```
{
  "versione": 1,
  "generato_il": "2026-10-25",
  "plugin": "0.11.0",            // da .claude-plugin/plugin.json; "?" se non trovato
  "fonti": [{"file": "mc.json", "tipo": "mc_pensione"}, ...],
  "indicatori": {...},            // §4.1
  "allocazione": {...} | null,
  "obiettivi": {...} | null,
  "glide_path": {...} | null,
  "pensione": {...} | null,
  "capitale_umano": {...} | null,
  "fiscalita": {...} | null,
  "ribilanciamento": {...} | null
}
```

Le sezioni, nell'ordine della pagina, con la fonte di ogni dato:

### 4.1 Testata e indicatori

Data, versione del plugin, file di origine, avviso «bozza educativa». Una riga di indicatori, ognuno presente solo se c'è la sua fonte e sempre con l'etichetta della fonte:

| Indicatore | Fonte |
|---|---|
| Capitale allocato | `allocatore.capitale` |
| Valore in portafoglio | `broker.analisi.totale_valore` |
| Probabilità minima tra gli obiettivi essenziali | `mc_obiettivi.obiettivi[priorita="essenziale"].probabilita_successo`, il minimo, con il nome dell'obiettivo |
| Tasso di sostituzione netto (mediana) | `netto_pensione.scenari[nome="mediana"].tasso_sostituzione_netto` |
| Zainetto in scadenza al 31/12 | `broker.analisi.zainetto_in_scadenza` |

### 4.2 Allocazione

- Con il ribilanciamento: per classe una barra orizzontale col peso attuale, il segno del target e la banda stretta attorno al target (da `drift`), più il peso risultante dopo il piano (`risultante`). Le classi fuori banda sono evidenziate.
- Senza ribilanciamento, con l'allocatore: solo il target aggregato (`aggregato.azioni`, `.obbligazioni`, `.liquidita` su `.totale`), e per obiettivo il capitale allocato e il profilo.

### 4.3 Obiettivi (`mc_obiettivi`)

Per obiettivo: la probabilità di successo come barra contro la soglia `confidenza`; la fascia P10–mediana–P90 di `capitale_finale` con il segno di `target_nominale`; in testo priorità, anni, versamento deterministico e «di confidenza». Gli obiettivi sono nell'ordine del JSON.

### 4.4 Glide path (`glide_path`)

Linee nel tempo (`anni`): la quota azionaria aggregata (`portafoglio`) e quella di ogni obiettivo (`obiettivi[].quota_azionaria`); sotto, il capitale proiettato per obiettivo (`obiettivi[].capitale_proiettato`) come barre impilate per anno.

### 4.5 Pensione (`inps`, `mc_pensione`, `netto_pensione`: ognuno facoltativo)

- Tasso di sostituzione lordo P10–mediana–P90 con il segno del `target` (`mc_pensione`), e la probabilità di raggiungerlo (`prob_target`).
- Netto per scenario: `pensione_netta_totale` e `tasso_sostituzione_netto` di ogni elemento di `scenari`, contro `netto_ultimo_stipendio`.
- In testo: pensione INPS lorda annua, età e anni al pensionamento, montante del fondo P10–mediana–P90.
- Come nella skill `it-revisione`: il tasso lordo si confronta col target lordo, il netto si legge come tenore di vita e non si confronta con un target lordo.

### 4.6 Capitale umano (`capitale_umano`)

- Bilancio totale: barre impilate delle voci di `bilancio.voci` (portafoglio, fondo, TFR, capitale umano, capitale pensionistico…).
- Esposizione azionaria finanziaria contro totale (`esposizione_finanziaria`, `esposizione_totale`).
- Nel tempo: la linea `proiezione[].esposizione` con la fascia `p10`–`p90` per età, il segno dell'età del sorpasso (`eta_sorpasso`) con la frase che corrisponde a `stato_sorpasso`.
- Se c'è `settore`: quota del settore nel portafoglio contro il peso nel mondo, e l'avviso di sovrappeso.
- È una lente, non un target: la sezione lo dice, come la skill.

### 4.7 Fiscalità (`broker`)

Per broker barre dello zainetto per anno di scadenza (`zainetto[]`: `scade_il`, `importo_26_equivalente`, `stato`), con le scadute distinte; per broker in testo `plus_latenti_compensabili`, `plus_realizzabili_a_costo_zero`, `imposta_risparmiabile`; in testa i totali di `analisi`. Gli `avvisi` dell'importatore compaiono come elenco.

### 4.8 Ribilanciamento (`ribilanciamento`)

Il drift per classe contro le due bande (barra divergente centrata sullo zero), l'esito e il motivo in testo, l'imposta del piano, la tabella degli ordini.

### 4.9 Disclaimer

Lo stesso testo dei report del plugin: bozza di analisi personale, non consulenza fiscale, finanziaria o di investimento; verificare con un professionista abilitato e con l'intermediario.

## 5. Flusso nelle skill e pubblicazione

**Nuovo passo in `it-revisione/SKILL.md`, «Cruscotto grafico»**, dopo il report:

1. Claude lancia `genera-cruscotto.py` dalla cartella di lavoro sui JSON già prodotti nella revisione (quelli del «Contratto di input» più il ribilanciamento). Se ne manca qualcuno lo dice, e genera il cruscotto con quello che c'è.
2. Comunica il percorso del file e le sezioni incluse.
3. **Chiede sempre** se pubblicarlo come Artifact, con questa informazione: la pagina va su claude.ai e contiene importi, età e proiezioni; resta privata finché l'utente non la condivide; si può cancellare. Senza un sì esplicito non pubblica.
4. Se sì:
   - **Claude Code**: lo strumento Artifact sul file `cruscotto.html`, così com'è (nessuna riscrittura dei dati);
   - **claude.ai e Cowork**: un artifact HTML con il contenuto del file, copiato senza modifiche;
   - se l'ambiente non ha un modo di creare artifact, lo dice e lascia il file locale.
5. Se no: il file si apre nel browser dal disco.

Una regola nel blocco «Anti-pattern» della skill: mai pubblicare senza conferma, mai scrivere a mano numeri nel cruscotto, mai modificare il template nel plugin (si rigenera).

**`/cruscotto`** (`commands/cruscotto.md`): esegue `it-revisione` dal passo «Cruscotto grafico», sui JSON nella cartella di lavoro o su quelli passati come argomenti; se non ce ne sono, indica quali script lanciare. Disclaimer in fondo, come gli altri comandi (il test di igiene lo verifica).

**Le altre skill**: `it-pianificazione-obiettivi`, `it-pianificazione` e `it-rebalance` aggiungono una riga a fine workflow: i JSON prodotti si possono vedere in grafico con `/cruscotto`. Nessuna di loro pubblica da sola.

**README**: `/cruscotto` nell'elenco dei comandi; nella sezione «Dove vanno i tuoi dati» un punto sul cruscotto: il file resta locale, la pubblicazione come Artifact manda la pagina su claude.ai e si fa solo su conferma; il bundle esclude le posizioni singole.

## 6. File

| File | Cambio |
|---|---|
| `skills/it-revisione/assets/cruscotto.html` | nuovo |
| `skills/it-revisione/assets/genera-cruscotto.py` | nuovo |
| `skills/it-revisione/SKILL.md` | passo «Cruscotto grafico», anti-pattern, elenco degli asset; versione 0.7 → 0.8 |
| `skills/it-rebalance/assets/ribilanciamento-multibroker.py` | `--json FILE` |
| `skills/it-rebalance/SKILL.md` | `--json` in workflow e «Formato output», riga su `/cruscotto`; versione 0.7 → 0.8 |
| `skills/it-pianificazione-obiettivi/SKILL.md`, `skills/it-pianificazione/SKILL.md` | riga su `/cruscotto` a fine workflow; versione invariata (nessun cambio di comportamento della skill), voce nella «Storia delle skill» del CHANGELOG solo per le skill che cambiano versione |
| `commands/cruscotto.md` | nuovo |
| `tests/run_tests.py` | test del §7; costanti e helper per i JSON d'esempio |
| `.github/workflows/tests.yml` | installazione di Playwright e Chromium nel job Ubuntu, `RICHIEDI_BROWSER=1` |
| `README.md` | comando, «Dove vanno i tuoi dati», conteggio dei test, tabella di copertura rigenerata, tabella delle versioni delle skill, conteggio in «Convenzioni degli script» (oggi «13 script») aumentato di uno |
| `CHANGELOG.md` | «Non rilasciato» |
| `ROADMAP.md` | tema T17 |
| `scripts/pacchetto.py` | nulla se lo zip prende già tutto `skills/` e `commands/` (da verificare nel piano) |

## 7. Test (TDD, prima del codice)

**In Python, senza browser** (girano ovunque, anche sul job Windows):

1. **Riconoscimento sugli output reali**: il test lancia gli script sugli esempi del plugin (pianificatore, esempio del capitale umano, fixture INPS e fondo, fixture multi-broker, esempio del ribilanciamento) e verifica che ogni JSON sia riconosciuto con il tipo giusto e che nessuno soddisfi due firme.
2. **Valori vincolati**: nel bundle `--json`, campione di valori uguali a quelli dei JSON di origine (probabilità di un obiettivo, mediana del tasso lordo, netto dello scenario mediana, `eta_sorpasso`, zainetto in scadenza, drift di una classe, numero degli ordini).
3. **Minimizzazione**: nessun ISIN né descrizione delle posizioni dell'estratto nel bundle né nell'HTML.
4. **Sezioni assenti**: con il solo JSON dell'allocatore il bundle ha `null` in tutte le altre sezioni e l'indicatore della pensione manca.
5. **Errori**: file inesistente, non JSON, non riconosciuto, due dello stesso tipo, campo mancante → exit 1 con `ERRORE:`; nessun `--from` o opzione ignota → exit 2. JSON noto e ignorato (`dati.json` di `importa-previdenza.py`) → `ℹ`, exit 0.
6. **HTML autosufficiente**: nessuna URL esterna nell'HTML generato e nel template; segnaposto presente una sola volta nel template e assente nell'output.
7. **Iniezione**: un nome d'obiettivo `</script><img src=x onerror=alert(1)>` nel JSON → nell'HTML non compare la sequenza `</script><img`; il template non usa `innerHTML` (ricerca nel sorgente).
8. **`--json` del ribilanciamento**: sull'esempio dello script il file esiste, ha le chiavi del §3.3, gli ordini coincidono con le righe dei CSV scritti nello stesso run, e l'output a video non cambia rispetto a senza `--json`.
9. **Interfaccia comune** (i test T9 esistenti): il nuovo script entra nell'elenco degli script che quei test percorrono (`--help`, exit 2, UTF-8).

**Con il browser** (Playwright e Chromium; saltati se mancano, obbligatori con `RICHIEDI_BROWSER=1`):

10. **Rendering completo**: la pagina generata con tutti i JSON d'esempio si apre da `file://` senza errori né eccezioni in console; ogni sezione presente contiene almeno un `<svg>`; le sezioni assenti non esistono nel DOM.
11. **Numeri visibili**: alcuni testi della pagina coincidono con i valori del bundle formattati all'italiana (es. la probabilità di un obiettivo, il tasso netto mediano).
12. **Tema scuro**: con `color_scheme="dark"` lo sfondo di `body` cambia.
13. **Telefono**: a 375px di larghezza `document.documentElement.scrollWidth <= 375`.
14. **Nessuna richiesta di rete**: durante il caricamento la pagina non fa richieste fuori da `file://`.

**Igiene**: README (conteggio, tabella di copertura, versioni delle skill), comando con disclaimer, CHANGELOG — tutti già coperti dai test esistenti una volta aggiornati i file.

## 8. ROADMAP

Nuovo tema **T17 Cruscotto grafico e Artifact** (P2, M): spec questo file, piano `docs/sviluppo/piani/2026-10-25-cruscotto-grafico.md`. Sviluppi futuri annotati nel tema: confronto tra due revisioni; ponte pensione e riscatto nel cruscotto; versione anonimizzata per la condivisione.

## 9. Limiti dichiarati

- Il percorso di pubblicazione si collauda solo in Claude Code. Per claude.ai e Cowork la spec dà le istruzioni alla skill, ma non c'è un test automatico: lo si prova a mano alla prima release.
- In claude.ai e Cowork l'artifact si crea copiando il contenuto del file: con molti obiettivi e ordini il file cresce (template di qualche decina di KB più i dati). Il bundle minimo (§4) lo tiene contenuto.
- Il cruscotto mostra lo stato dei JSON al momento in cui sono stati generati: non si aggiorna da solo. Per aggiornarlo si rilanciano gli script e il generatore, e si ripubblica sullo stesso Artifact.
- Le firme del §3.1 dipendono dalle chiavi dei JSON di oggi: se uno script cambia le sue chiavi, il test 1 fallisce e la tabella va aggiornata.
