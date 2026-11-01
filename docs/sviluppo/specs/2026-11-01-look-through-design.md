# Look-through del portafoglio (design)

Stato: spec scritta l'1/11/2026, dopo la revisione del repository con il proprietario e la decisione di seguire il ciclo 0.12.0 nell'ordine: igiene documentale, look-through, ponte e riscatto nel cruscotto, lingue tedesca e francese. È l'evolutiva **C** annotata nella spec dell'importatore della composizione (`2026-10-25-composizione-etf-design.md`, §8) e in ROADMAP sotto **T16 Fonti dati esterne e connettori**.

> ⚠️ Come il resto del plugin: strumento di pianificazione personale, non consulenza finanziaria o fiscale.

## 1. Obiettivo e perimetro

**Cosa si vuole.** Oggi `composizione.csv` descrive ogni ETF per settore GICS e paese, ma nessuno script risponde alla domanda «**cosa possiedo davvero, sommando tutti gli ETF?**». Il look-through aggrega settori, paesi e primi titoli di tutti gli ETF posseduti, **pesati per controvalore**, e scrive un `--json` che `it-revisione` riporta e il cruscotto (T17) disegna. Lo script resta offline, come da principio di T16: il dato si procura a parte (importatore su file), lo script legge file locali.

**Decisioni prese (dal proprietario l'ordine del ciclo; il resto dal progettista, da rivedere nella revisione finale):**

| # | Decisione | Scelta |
|---|---|---|
| D1 | Chiave tra posizione e composizione | L'**ISIN**: `--strumento` dell'importatore accetta l'ISIN (alias `--isin`), e il campo `strumento` del CSV lo contiene. Le posizioni dell'estratto del broker hanno già `isin`; quelle del capitale umano imparano il campo `isin`. Il nome resta una chiave valida, per chi ha già importato con i nomi e per le righe compilate a mano |
| D2 | Primi titoli | L'importatore scrive i primi `N_TITOLI` (10) titoli di ogni ETF per peso come righe `dimensione=titolo` di `composizione.csv`, con il **peso nel fondo** (non rinormalizzato), e li mette nel `--json`. Nessun cambio di formato del CSV: la colonna `dimensione` prende il terzo valore |
| D3 | Fonte delle posizioni | Il JSON di `importa-estratto-broker.py --json` (`--posizioni`, ripetibile: un file per broker), oppure il `--dati` del capitale umano, che ha la stessa lista `posizioni`. Lo script distingue le due forme dalle chiavi, non chiede all'utente |
| D4 | Aggregazione | Per ogni dimensione (settori, paesi, titoli) contano solo le posizioni che la hanno nel CSV; i pesi si rinormalizzano sulla **parte coperta** e la **copertura** (quota del controvalore totale) si scrive accanto. Mai un «altro» inventato |
| D5 | Titoli tra ETF diversi | Lo stesso titolo si somma con una **chiave normalizzata** del nome (maiuscole, senza punteggiatura, senza suffissi societari e classi di azioni). L'ISIN del titolo, quando il file dell'emittente lo ha, va nel JSON dell'importatore ma non nel CSV. Il limite è dichiarato |
| D6 | Dove vive lo script | `it-pianificazione-obiettivi/assets/look-through-portafoglio.py`, accanto all'importatore e al capitale umano, con il motore (`cli()`, formati italiani). `it-revisione` lo richiama, come per gli altri script |
| D7 | Cruscotto | Nuova sezione «Look-through» tra Allocazione e Obiettivi: settori, primi dieci paesi e primi dieci titoli con la copertura. Nessuna posizione dell'utente nella pagina (né nomi né ISIN): solo aggregati e il numero di posizioni senza composizione |
| D8 | Comando | Nessun comando nuovo: i comandi sono alias uno a uno delle skill (T14). Il look-through è nello Step 8 di `it-pianificazione-obiettivi` e nel passo 3 di `it-revisione` |

**Fuori perimetro (YAGNI):** regioni (Nord America, Europa…) come dimensione; valuta; conversione ICB → GICS; HHI o numero effettivo di titoli; look-through del fondo pensione (composizione non disponibile); download dei file; posizioni dirette classificate da sole (si compilano a mano, §3.3); confronto tra due date; lingue tedesca e francese (tema a parte del ciclo).

## 2. Componenti

| File | Cosa fa |
|---|---|
| `skills/it-pianificazione-obiettivi/assets/look-through-portafoglio.py` | Nuovo. Legge `composizione.csv` e una o più liste di posizioni, aggrega per controvalore, stampa il report, `--json` |
| `skills/it-pianificazione-obiettivi/assets/importa-composizione-etf.py` | Scrive le righe `titolo` (D2); `--isin` alias di `--strumento` (D1); colonna `isin` del titolo riconosciuta; `titoli` nel `--json`; `N_TITOLI` sovrascrivibile con `--set` |
| `skills/it-pianificazione-obiettivi/assets/capitale-umano.py` | `leggi_composizione()` ignora le righe `titolo`; le posizioni possono avere `isin`, che si confronta per primo; `mancanti` nomina la posizione come la nomina l'utente |
| `skills/it-pianificazione-obiettivi/assets/esempio-capitale-umano.json` | Le posizioni d'esempio prendono un `isin` (ISIN d'esempio dichiarati tali) |
| `skills/it-revisione/assets/genera-cruscotto.py`, `cruscotto.html` | Firma `look_through`, sezione «Look-through» (D7) |
| `skills/it-pianificazione-obiettivi/references/composizione-etf.md` | Sezione «Il look-through del portafoglio»: chiave ISIN, righe `titolo`, posizioni dirette a mano, limiti |
| `skills/it-pianificazione-obiettivi/SKILL.md`, `skills/it-revisione/SKILL.md` | Step 8 e passo 3, contratto di input, passo 6 (il JSON in più) |
| `tests/run_tests.py`, `tests/fixtures/` | Test del §7; fixture `estratto-look-through.csv` e `composizione-look-through.csv` |

### 2.1 Interfaccia

```
python "${CLAUDE_SKILL_DIR}/assets/look-through-portafoglio.py" \
    --composizione composizione.csv \
    --posizioni broker.json [--posizioni broker-2.json ...] \
    [--json FILE|-] [--set N_TITOLI_REPORT=10]
```

- `--composizione FILE` obbligatorio: il CSV dell'importatore (formato `strumento;dimensione;voce;peso`), anche con righe compilate a mano; il vecchio formato `strumento;settore;peso` si legge come solo settori.
- `--posizioni FILE` obbligatorio, ripetibile. Un JSON con la lista `posizioni`; ogni posizione ha `valore` (controvalore in euro) e almeno uno tra `isin` e `descrizione` (estratto del broker) o `strumento` (capitale umano). Due file con la stessa posizione (stesso ISIN su due broker) si sommano: è la stessa esposizione.
- `--json FILE|-`: il risultato strutturato (§3.2). Con `-` solo il JSON su stdout.
- Interfaccia comune degli script (T9): `--help`, exit 0/1/2, UTF-8, formati italiani, `--set` sulle costanti in testa (`N_TITOLI_REPORT`, `SUFFISSI_SOCIETARI`).
- Errori con `ERRORE:` e rc 1: file mancanti; CSV con colonne non riconosciute; JSON senza `posizioni`; posizione senza `valore` numerico non negativo; **nessuna posizione con una composizione** (il report non avrebbe senso); controvalore totale zero.

## 3. Formati

### 3.1 Le righe `titolo` di `composizione.csv`

```
# IE00B4L5Y983: iShares, swda.csv, posizioni al 30/09/2026, importato il 01/11/2026; esclusi liquidità e derivati 0,40%
strumento;dimensione;voce;peso
IE00B4L5Y983;settore;Information Technology;26,84
IE00B4L5Y983;paese;US;71,20
IE00B4L5Y983;titolo;NVIDIA CORP;5,12
IE00B4L5Y983;titolo;APPLE INC;4,60
```

- `voce` è il nome del titolo **come nel file**, solo con gli spazi ai bordi tolti; `peso` è la quota del fondo in percento con due decimali, **non rinormalizzata** (è il dato dell'emittente; sommando le righe `titolo` si ottiene la quota del fondo coperta dai primi N).
- Si scrivono i primi `N_TITOLI = 10` per peso tra le righe **non escluse** (niente liquidità, derivati, pesi negativi; le obbligazioni restano: in un ETF obbligazionario i primi titoli sono BTP e Bund).
- Un file con meno di N titoli ne scrive meno; se la colonna del nome manca, nessuna riga `titolo` e un avviso.
- Lettori: `capitale-umano.py` salta le righe `titolo` (prima le respingeva come dimensione sconosciuta: resta l'errore per ogni altro valore); `leggi_out()` dell'importatore non le distingue e le conserva come ogni altra riga dello strumento.
- `--json` dell'importatore: per strumento la lista `titoli: [{nome, isin, peso}]`, `isin` `null` se il file non ha la colonna (sinonimi `isin`, `codice isin`, `isin code`).

### 3.2 `--json` del look-through

```json
{
  "controvalore_totale": 36750.0,
  "posizioni": [
    {"chiave": "IE00B4L5Y983", "nome": "iShares Core MSCI World", "valore": 9200.0, "quota": 0.2503,
     "settori": true, "paesi": true, "titoli": true},
    {"chiave": "IT0005454241", "nome": "BTP Futura 2037", "valore": 2850.0, "quota": 0.0776,
     "settori": false, "paesi": true, "titoli": false}
  ],
  "senza_composizione": [{"chiave": "DE0007164600", "nome": "SAP SE", "valore": 1500.0, "quota": 0.0408}],
  "copertura": {"settori": 0.8816, "paesi": 0.9592, "titoli": 0.8816},
  "settori": [{"voce": "Information Technology", "nome": "Tecnologia dell'informazione", "peso": 0.2731}, "…"],
  "paesi": [{"voce": "US", "nome": "Stati Uniti", "peso": 0.6512}, "…"],
  "titoli": [{"nome": "NVIDIA CORP", "peso": 0.0438, "da": ["IE00B4L5Y983", "IE00B5BMR087"]}, "…"],
  "quota_primi_titoli": 0.1850,
  "n_titoli_aggregati": 17,
  "avvisi": []
}
```

- `quota` di una posizione è sul controvalore totale; i `peso` di settori, paesi e titoli sono sulla **parte coperta** di quella dimensione (sommano a 1 per settori e paesi; per i titoli sommano alla quota coperta dai primi N di ogni ETF, che è un **minimo** della concentrazione vera).
- `quota_primi_titoli`: somma dei pesi dei primi `N_TITOLI_REPORT` titoli aggregati.
- `titoli[].da`: le chiavi degli strumenti che contribuiscono (per capire da dove viene una concentrazione); `nome` è quello dello strumento che contribuisce di più.
- `senza_composizione` e `posizioni` portano nomi e ISIN: servono al report e a `it-revisione`, **non** entrano nel cruscotto (§4).
- Chiavi di primo livello che fanno da firma per il cruscotto: `copertura`, `settori`, `paesi`, `titoli`, `controvalore_totale`.

### 3.3 Lettura delle posizioni

- Il JSON dell'estratto del broker (`importa-estratto-broker.py --json`): `posizioni[].isin`, `.descrizione`, `.valore`. Si riconosce da `analisi` e `zainetto`.
- Il `--dati` del capitale umano: `posizioni[].strumento`, `.isin` (nuovo, facoltativo), `.valore`. Si riconosce da `persona`.
- Qualsiasi altro JSON con una lista `posizioni` dalle stesse chiavi è accettato; senza `posizioni` è un errore.
- Chiave di confronto con `composizione.csv`, nell'ordine: `isin` uguale al campo `strumento` del CSV; poi `descrizione` o `strumento` uguale (spazi ai bordi tolti, maiuscole rispettate, come `capitale-umano.py`). Senza riscontro la posizione va in `senza_composizione`, con il nome che l'utente vede, così sa cosa importare o compilare.
- **Posizioni dirette** (una singola azione, un BTP): non hanno un file delle posizioni. Si compilano a mano nel CSV con la chiave dell'ISIN: `IT0005454241;paese;IT;100` e, se si vuole il titolo tra i primi, `IT0005454241;titolo;BTP Futura 2037;100`. La reference lo spiega con l'esempio.
- Posizioni con `valore` zero sono ignorate con un avviso; negative sono un errore.

### 3.4 Aggregazione

Per dimensione `d` ∈ {settori, paesi, titoli}:

- `C_d` = insieme delle posizioni con almeno una riga di `d`; `V_d` = somma dei loro `valore`; `copertura_d = V_d / V_tot`.
- Per ogni voce `v`: `peso_v = Σ_{p ∈ C_d} valore_p × peso_{p,v} / V_d`, con `peso_{p,v}` la frazione nel CSV (percento / 100).
- Per i titoli la chiave di somma è `chiave_titolo(nome)`: maiuscole, senza accenti e punteggiatura, senza i suffissi di `SUFFISSI_SOCIETARI` (`INC`, `CORP`, `CORPORATION`, `CO`, `LTD`, `LIMITED`, `PLC`, `SA`, `SPA`, `AG`, `SE`, `NV`, `AB`, `ASA`, `OYJ`, `KK`, `HOLDINGS`, `HOLDING`, `GROUP`) e delle classi (`CLASS A`, `CLASS B`, `CLASS C`, `CL A`, `ORD`, `ADR`, `REIT`), spazi compressi. `APPLE INC` e `Apple Inc.` si sommano; `ALPHABET INC CLASS A` e `ALPHABET INC CLASS C` pure (stessa società, due classi di azioni: è l'esposizione che interessa). Il limite dichiarato: nomi scritti in modo diverso da due emittenti possono restare separati; il report mostra `da` per accorgersene.
- Ordinamento: peso decrescente; nel report i primi `N_TITOLI_REPORT` titoli, i primi 10 paesi con «altri N paesi X%», tutti i settori (sono 11).

### 3.5 Report a terminale

```
LOOK-THROUGH DEL PORTAFOGLIO — cosa possiedi sommando gli ETF (pesato per controvalore)
   Controvalore: €36.750 su 4 posizioni; con composizione: 3 (€35.250, 95,9%)
   Senza composizione (importa il file delle posizioni, o compila le righe a mano): SAP SE (DE0007164600) €1.500, 4,1%

1. SETTORI (copertura 88,2% del controvalore)
   Tecnologia dell'informazione 27,3% · Finanza 16,1% · …
2. PAESI (copertura 95,9%)
   Stati Uniti 65,1% · Giappone 5,8% · … · altri 12 paesi 4,0%
3. PRIMI TITOLI (copertura 88,2%; i primi 10 di ogni ETF, quindi un minimo della concentrazione)
   NVIDIA CORP 4,4% (da IE00B4L5Y983, IE00B5BMR087) · APPLE INC 4,1% · …
   I primi 10 titoli pesano il 18,5% della parte coperta.

Non è consulenza: è la fotografia delle composizioni alla data dei file degli emittenti, da riguardare a ogni revisione.
```

Tutti i numeri con `numero()`, `euro()`, `pct()` del motore. Gli avvisi (posizioni a valore zero, titoli senza riga `titolo` in uno strumento che ha i settori) dopo la testata con «⚠️».

## 4. Cruscotto

- Firma in `FIRME`: `("look_through", lambda d: _ha(d, "copertura", "settori", "paesi", "titoli", "controvalore_totale"))`. In `ORDINE` dopo `allocatore`.
- Bundle `look_through`: `{copertura {settori, paesi, titoli}, settori [{nome, peso}], paesi [{nome, peso}] (i primi 10 più «altri» con la somma, se ci sono), titoli [{nome, peso}] (i primi 10), quota_primi_titoli, n_posizioni, n_senza_composizione, quota_senza_composizione}`. **Niente** `posizioni`, `senza_composizione` né chiavi ISIN: il test del bundle (`T17 cruscotto: … nessuna posizione dell'estratto`) resta vero anche con il look-through. I nomi dei titoli sottostanti (NVIDIA, Apple) non sono posizioni dell'utente e restano.
- Sezione «Look-through» in `cruscotto.html` tra Allocazione e Obiettivi: due grafici a barre orizzontali (settori con il nome italiano; paesi) e una tabella dei primi titoli con il peso; sotto ogni grafico la copertura; una riga «N posizioni senza composizione (X% del controvalore)» quando c'è. Stessi helper `barre()`, `tabella()`, `sezione()` e stesso test del browser (SVG presente, numeri italiani, 375 px, tema scuro).
- Indicatori in testata: nessuno nuovo (la copertura varia troppo per stare in testata senza contesto).

## 5. Flusso nelle skill

**it-pianificazione-obiettivi, Step 8**: dopo l'importatore, il paragrafo «Look-through del portafoglio» con il comando; si consiglia l'ISIN come `--strumento` quando le posizioni vengono dall'estratto del broker (`importa-estratto-broker.py --json`). Il look-through legge e riporta; non cambia i target. Versione della skill 0.24.

**it-revisione**: nel passo 3, dominio «Allocazione», una riga: con `composizione.csv` e il JSON dell'estratto, `look-through-portafoglio.py --json` dice settori, paesi e primi titoli aggregati, con la copertura; si riportano nel report i primi tre settori e paesi, la quota dei primi dieci titoli e le posizioni senza composizione. Contratto di input: riga «Look-through» (script, campi `settori[]`, `paesi[]`, `titoli[]`, `copertura`, `senza_composizione[]`; nessuna cella). Passo 6: il JSON del look-through tra i `--from`. Versione 0.9.

**Claude**: non scarica niente e non compila nomi al posto dell'utente; se una posizione è senza composizione, dice quale file importare o quali righe aggiungere.

## 6. File

Nuovi: `look-through-portafoglio.py`; `tests/fixtures/estratto-look-through.csv` (due ETF e due posizioni dirette, ISIN d'esempio) e `tests/fixtures/composizione-look-through.csv` (settori, paesi e titoli dei due ETF con la chiave ISIN, e un BTP a mano con il solo paese); spec e piano.

Modificati: `importa-composizione-etf.py`, `capitale-umano.py`, `esempio-capitale-umano.json`, `esempio-composizione.csv` (invariato nel vecchio formato: prova che il vecchio formato vive), `genera-cruscotto.py`, `cruscotto.html`, `composizione-etf.md`, `capitale-umano.md` (il campo `isin`), i due `SKILL.md`, `tests/run_tests.py`, README (conteggio dei test, «Tutti i 18 script», tabella strumenti ↔ test, «Dove vanno i tuoi dati»), CHANGELOG, ROADMAP.

## 7. Test (TDD, prima del codice)

1. **Importatore, righe `titolo`**: sulla fixture iShares i primi N titoli nell'ordine del peso, pesi nel fondo non rinormalizzati (30,00; 20,00; …), liquidità e future esclusi; `--set N_TITOLI=2` ne scrive due; `--isin` equivale a `--strumento`; `--json` con `titoli[].isin` da un XLSX Xtrackers (che ha la colonna) e `null` da iShares; un reimport di un altro strumento conserva le righe `titolo` del primo.
2. **Capitale umano**: le righe `titolo` non fermano `leggi_composizione()`; una posizione con `isin` e senza `strumento` trova la composizione; `mancanti` nomina `strumento` o, in mancanza, `isin`; una dimensione sconosciuta (`valuta`) resta un errore.
3. **Look-through, valori chiusi**: sulle due fixture, controvalore, coperture, pesi di settori, paesi e titoli calcolati a mano nel test (tolleranza 1e-9 sulle frazioni), `quota_primi_titoli`, `da` dei titoli presenti in due ETF, il BTP solo nei paesi, la posizione senza composizione; `--posizioni` ripetuto somma la stessa posizione; il `--dati` del capitale umano come sorgente; stdout con i formati italiani e la frase «minimo della concentrazione».
4. **Look-through, chiave dei titoli**: `chiave_titolo()` su una tabella di coppie (`Apple Inc.` ↔ `APPLE INC`, `ALPHABET INC CLASS A` ↔ `Alphabet Inc Class C`, `Microsoft Corp` ↔ `MICROSOFT CORPORATION`, `Nestlé SA` ↔ `NESTLE S.A.`) e di non-coppie (`Bank of America` ≠ `Bank of Montreal`).
5. **Look-through, errori**: CSV mancante o con colonne sbagliate, JSON senza `posizioni`, nessuna posizione con composizione, valore negativo, controvalore zero → rc 1 con il messaggio; `--help` → 0; flag ignoto → 2 (entra in `t_cli_help` e `t_formati_italiani` come gli altri script).
6. **Cruscotto**: il JSON del look-through è riconosciuto (`t_t17_riconosci`, con il look-through tra i lanci di `_json_esempio()` sulle fixture); il bundle non porta `posizioni` né ISIN; la sezione `#sez-look_through` ha i suoi SVG nel browser; «senza composizione» in pagina quando c'è; la pagina resta entro 375 px.
7. **Documentazione**: Step 8 con il comando e `--isin`; passo 3 e contratto di input di it-revisione; reference con «titolo», «ISIN», «a mano»; README con `look-through-portafoglio.py` e «Tutti i 18 script»; CHANGELOG; ROADMAP con la voce spuntata.

## 8. ROADMAP

Sotto T16 la voce «Look-through del portafoglio» diventa spuntata, con spec e piano; resta aperta la voce delle lingue (tema successivo del ciclo). Sviluppi successivi, da decidere: regioni come dimensione; ISIN dei titoli nel CSV per sommare senza la chiave del nome; valuta di denominazione.

## 9. Limiti dichiarati

- **Primi N titoli, non tutti**: la concentrazione sui titoli è un minimo; i settori e i paesi invece coprono tutto il fondo.
- **Nomi, non ISIN, per sommare i titoli**: due emittenti possono scrivere la stessa società in modi diversi; la chiave normalizzata ne cattura la maggior parte, `da` mostra il resto.
- **Copertura parziale**: i pesi sono sulla parte coperta; la copertura sta sempre accanto al numero.
- **Fotografia a più date**: ogni ETF ha la data del suo file; il look-through non le allinea e non le mostra (sono nei commenti del CSV).
- **Il fondo pensione non entra**: la sua composizione non è disponibile in forma leggibile.
- **Posizioni dirette a mano**: una singola azione o un BTP si descrivono con le righe compilate dall'utente; lo script non deduce il paese dall'ISIN, per non indovinare (un ISIN IE può essere un ETF domiciliato in Irlanda con titoli americani).
