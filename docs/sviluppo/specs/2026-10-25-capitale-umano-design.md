# Capitale umano nell'allocazione: lente diagnostica (design)

Stato: spec da rivedere, 25/10/2026. Nasce dal brainstorming con il proprietario sulla richiesta: «considerare nel quadro totale dell'allocazione anche i flussi di cassa futuri del capitale umano». Tema di ROADMAP: **T15** (questa spec) e **T16** (fonti dati e connettori, solo pianificato).

> ⚠️ Come il resto del plugin: strumento di pianificazione personale, non consulenza finanziaria.

## 1. Obiettivo e perimetro

**Cosa si vuole.** Vedere il portafoglio finanziario dentro la **ricchezza totale** (finanziario + capitale umano + capitale pensionistico), per capire se il portafoglio *compensa* il capitale umano o lo *duplica*. È una **lente diagnostica** (opzione A del brainstorming): non modifica l'allocazione target degli obiettivi né quella che `it-rebalance` mantiene.

**Decisioni prese nel brainstorming:**

| # | Decisione | Scelta |
|---|---|---|
| D1 | Cosa produce | Lente diagnostica (A). L'aggiustamento dei target (B), l'ottimizzatore di ciclo di vita (C) e la polizza vita (D) restano sviluppi futuri |
| D2 | Di chi | Una persona (C): un reddito da lavoro più la sua pensione, con la struttura dati pronta per un secondo reddito del nucleo |
| D3 | Rischio del capitale umano | Profili predefiniti sovrascrivibili (A). La volatilità stimata dall'estratto INPS è uno sviluppo futuro |
| D4 | Diagnosi | Tutte e cinque: bilancio totale, esposizione azionaria, proiezione, sovrapposizione settoriale, sensibilità |
| D5 | Riga di equivalenza | Inclusa, facoltativa, attivata dall'utente, presentata come «calcolo, non target» |
| D6 | Dove vive | Approccio 1: script e reference dentro `it-pianificazione-obiettivi`, comando `/capitale-umano` |
| D7 | Divisione azioni/obbligazioni | Quota azionaria **esplicita** per profilo (`quota_azionaria_hc`), non derivata da β = ρ·σ_h/σ_S |
| D8 | Pensione INPS | Blocco a sé (capitale pensionistico), 100% obbligazionario |
| D9 | Precari e contratti a termine | `privato_ciclico` con `p_u` più alto (override), nessun profilo dedicato |
| D10 | Dati esterni | Gli script di calcolo restano **offline**: i dati si procurano a parte (importatore su file o fetch di Claude) e lo script legge un file locale |

**Caso guida.** Il proprietario: sviluppatore mobile, dipendente nel settore privato. Profilo `privato_ciclico`, settore GICS `Information Technology`. L'esempio del plugin è costruito su un caso analogo e anonimo.

**Fuori perimetro (YAGNI):** casa e altri immobili (solo una riga facoltativa «altri attivi», esclusa dall'esposizione); probabilità di sopravvivenza prima della pensione; polizza vita; fiscalità dettagliata del TFR (entra al lordo, con nota); ottimizzazione CRRA; modifica dei target; Excel.

## 2. Basi bibliografiche

Verificate sulle fonti il 25/10/2026: per Ibbotson et al. (2007) e Merton (1971) sul testo; per gli altri su NBER, RePEc, editori e pagine degli autori. La reference `capitale-umano.md` riporta questo elenco con i link.

**Teoria**
- Bodie & Samuelson (1989), «Labor Supply Flexibility and Portfolio Choice», NBER WP 3043: la prima versione.
- Bodie, Merton & Samuelson (1992), «Labor Supply Flexibility and Portfolio Choice in a Life-Cycle Model», *JEDC* 16(3-4):427-450; NBER WP 3954. Chi può modulare quanto e fino a quando lavorare regge più rischio in portafoglio.
- Merton (1971), *JET* 3:373-413, §7: un salario certo scontato al tasso privo di rischio si somma alla ricchezza. È il capitale umano come obbligazione.
- Viceira (2001), *JF* 56(2):433-470: con un reddito non correlato, il lavoratore tiene più azioni del pensionato. Volatilità e correlazione del reddito riducono la quota azionaria.
- Benzoni, Collin-Dufresne & Goldstein (2007), *JF* 62(5):2123-2167: con la cointegrazione tra salari e dividendi il capitale umano del giovane è simile a un'azione e la quota azionaria segue una curva a gobba.
- Campbell & Viceira (2002), *Strategic Asset Allocation*, OUP, cap. 6.

**Framework applicativi e valutazione**
- Ibbotson, Milevsky, Chen & Zhu (2007), *Lifetime Financial Advice*, CFA Institute Research Foundation. È la base del modello di questa spec: eq. 2.1 e A.1 (valore), A.6-A.9 (processo del reddito correlato), «stock-like» contro «bond-like», casi di studio del cap. 2.
- Chen, Ibbotson, Milevsky & Zhu (2006), *FAJ* 62(1):97-109: capitale umano e polizza vita (sviluppo futuro).
- Milevsky (2008; ed. riveduta 2013), *Are You a Stock or a Bond?*, FT Press: la cornice divulgativa della quota azionaria esplicita.
- Huggett & Kaplan (2016), *Review of Economic Dynamics* 22:21-51: il capitale umano vale molto meno del reddito scontato a r_f e la sua componente azionaria è di solito sotto il 35%.
- Bodie, Treussard & Willen (2007), «The Theory of Life-Cycle Saving and Investing», Boston Fed PPDP 07-3.

**Calibrazione**
- Davis & Willen (2000; *Quarterly Journal of Finance* 2013): correlazione tra reddito per professione e borsa circa da −0,2 a 0,1.
- Heaton & Lucas (2000), *JF* 55(3):1163-1198: un reddito d'impresa volatile riduce la quota azionaria. È la base dei profili `autonomo` e `imprenditore`.
- Guiso, Jappelli & Terlizzese (1996), *AER* 86(1):158-172: dati SHIW italiani, il rischio non assicurabile sul reddito riduce la quota rischiosa.
- Cocco, Gomes & Maenhout (2005), *RFS* 18(2):491-533. Testo non letto: citare solo la conclusione qualitativa.

**Applicati**
- Bagliano, Fugazza & Nicodano (2014), *Review of Finance* 18(6):2283-2323: lavoratori eterogenei; trattarli tutti allo stesso modo costa il 15-30% del consumo.
- Gomes (2020), *Annual Review of Financial Economics* 12:277-304: la rassegna.
- Duarte, Fonseca, Goodman & Parker (2021), NBER WP 29559: le regole semplici (target-date) seguono la media ma costano il 2-3% del consumo.
- Catherine (2022), *RFS*: il rischio sul reddito che peggiora nelle recessioni.

## 3. Modello di valutazione

**Convenzioni.** Euro di oggi e termini reali, come `proiezione-inps.py`. Redditi **netti**: i contributi tornano come pensione, valutata a parte, così nulla si conta due volte.

### 3.1 Capitale umano

```
HC = Σ_{t=1..N} E[h_t] / (1 + r_f + ν)^t                              (Ibbotson et al., eq. 2.1)

h_t    = (netto_annuo + tfr_annuo + contributo_datore_fp) × (1 + g)^t
E[h_t] = h_t × (1 − p_u × durata_anni × (1 − sostituzione_naspi))
N      = eta_pensione − eta                                            (anni interi; 0 se già in pensione)
```

- `r_f`: tasso reale privo di rischio, costante `R_F`, default 1%.
- `ν`: premio di illiquidità e rischio specifico, dal profilo. Huggett & Kaplan: scontare al solo r_f sopravvaluta il capitale umano.
- `p_u`, `durata_anni`, `sostituzione_naspi`: dal profilo, con override. Il prodotto `p_u × durata_anni` è la frazione d'anno attesa senza lavoro; è un'approssimazione dichiarata (niente decalage né tetto della NASpI nel calcolo, solo nella reference).
- `g`: crescita reale del reddito, da `persona.crescita_reale`, default 1%. Il JSON di `proiezione-inps.py` non la riporta (verificato il 25/10/2026): va passata a mano, con lo stesso valore usato in `--set CRESCITA_REALE_RAL`.
- `quota_reddito_azioni_datore` (frazione di h_t pagata in azioni del datore): quella parte di HC conta al 100% come azionaria, nel settore del datore.

### 3.2 Divisione azioni/obbligazioni (D7)

```
s_eff = quota_reddito_azioni_datore + (1 − quota_reddito_azioni_datore) × quota_azionaria_hc
HC_az = s_eff × HC          HC_obb = (1 − s_eff) × HC
```

La formula alternativa β = ρ·σ_h/σ_S (Ibbotson, eq. A.11) con le correlazioni di breve di Davis & Willen dà il 2-6% per quasi tutti, contro la componente di lungo periodo misurata da Benzoni et al. e da Huggett & Kaplan. Per questo la quota è un parametro esplicito del profilo; ρ e σ_h servono solo alla sensibilità (§5.5) e alla fascia della proiezione (§5.3). La reference spiega la scelta.

### 3.3 Capitale pensionistico (D8)

```
PP_oggi = Σ_{t=N+1..T} pensione_netta / (1 + r_f + ν_pens)^t          T = eta_fine − eta
```

- `pensione_netta`: annua, in euro di oggi, dal JSON di `netto-pensione.py` (`netto_pensione_inps`) o da `--dati`.
- `ν_pens`: rischio normativo, costante `NU_PENSIONE`, default 0,75%.
- `eta_fine`: default 90, sovrascrivibile.
- 100% obbligazionario. Il legame del montante con il PIL nominale (rivalutazione contributiva) va spiegato nella reference, non modellato.

### 3.4 Capitale finanziario e totale

```
F    = Σ posizioni + fondo_pensione.valore + tfr_maturato_azienda + liquidità
F_az = Σ posizioni azionarie + fondo_pensione.valore × fondo_pensione.quota_azionaria
W    = F + HC + PP           (+ altri_attivi solo in tabella, fuori da W ai fini dell'esposizione)

esposizione_finanziaria = F_az / F
esposizione_totale      = (F_az + HC_az) / W
```

Il TFR maturato in azienda è obbligazionario (rivalutazione 1,5% + 75% dell'inflazione). Le posizioni usano le `asset_class` di `it-rebalance`: `azionario` è azionario, `obbligazionario` e `monetario` no.

## 4. Profili (`assets/profili-capitale-umano.csv`)

Colonne: `profilo;quota_azionaria_hc;nu;rho;sigma_h;p_u;durata_anni;sostituzione_naspi;settore_default;fonte;natura`. Separatore `;` e virgola decimale come gli altri CSV del plugin. `natura` vale `letteratura` (valore ancorato a un paper) o `giudizio` (calibrazione da verificare), campo per campo dove serve (per esempio `s:letteratura; nu:giudizio; p_u:giudizio`).

| Profilo | s | ν | ρ | σ_h | p_u | durata | NASpI | Settore default | Ancoraggio |
|---|---|---|---|---|---|---|---|---|---|
| `pubblico` | 0,05 | 0,01 | 0,0 | 0,02 | 0,005 | 0,5 | 0,0 | — | Ibbotson (professore di ruolo); Merton §7 |
| `privato_stabile` | 0,15 | 0,02 | 0,1 | 0,05 | 0,03 | 0,5 | 0,6 | — | Davis & Willen; Ibbotson caso 3 |
| `privato_ciclico` | 0,30 | 0,03 | 0,3 | 0,10 | 0,05 | 0,5 | 0,6 | — | Huggett & Kaplan; Catherine 2022 |
| `finanza` | 0,50 | 0,03 | 0,5 | 0,15 | 0,04 | 0,5 | 0,6 | Financials | Ibbotson scenario 1; l'esempio del broker |
| `autonomo` | 0,30 | 0,04 | 0,2 | 0,20 | 0,0 | 0,0 | 0,0 | — | Heaton & Lucas 2000 |
| `imprenditore` | 0,60 | 0,05 | 0,4 | 0,25 | 0,0 | 0,0 | 0,0 | — | Heaton & Lucas 2000 |

- Per `autonomo` e `imprenditore` il rischio di reddito sta in `sigma_h` e in `nu`, non in `p_u` (non c'è un «posto» da perdere né la NASpI).
- Precari e contratti a termine (D9): `privato_ciclico` con `override.p_u` più alto; la reference indica come sceglierlo.
- `p_u` e la sostituzione NASpI sono **punti di partenza**: nell'implementazione si verificano su ISTAT (flussi delle forze di lavoro) e sulla circolare INPS, e la reference porta il marcatore `Verificato: AAAA-MM` sui valori NASpI. Il ν è giudizio dichiarato: la letteratura ne dà l'ordine di grandezza.
- `settore` usa la classificazione **GICS** (11 settori), la stessa dei file delle posizioni degli emittenti di ETF.

## 5. Le diagnosi

### Input

Un JSON passato con `--dati` (esempio in `assets/esempio-capitale-umano.json`; senza `--dati` lo script gira sull'esempio e lo dichiara):

```json
{
  "persona": {"profilo": "privato_ciclico", "settore": "Information Technology",
              "eta": 35, "eta_pensione": 67, "netto_annuo": 32000, "crescita_reale": 0.01,
              "tfr_annuo": 3000, "contributo_datore_fp": 0, "quota_reddito_azioni_datore": 0,
              "override": {"p_u": 0.08}},
  "pensione": {"netta_annua": 18000, "eta_fine": 90},
  "posizioni": [{"asset_class": "azionario", "valore": 60000, "strumento": "ETF MSCI World"}],
  "fondo_pensione": {"valore": 15000, "quota_azionaria": 0.6},
  "tfr_maturato_azienda": 8000,
  "liquidita": 10000,
  "risparmio_annuo": 9000,
  "esposizione_totale_desiderata": null,
  "altri_attivi": 0
}
```

- `posizioni` segue lo schema di `it-rebalance` (`asset_class`, `valore`; le altre chiavi sono ignorate), con `strumento` facoltativo per la diagnosi 4: le posizioni si copiano dal JSON del ribilanciamento così come sono.
- `persona` è un oggetto; la struttura dati prevede in futuro una lista `persone` per il secondo reddito del nucleo (D2), ma lo script ora accetta solo `persona` e rifiuta `persone` con un messaggio chiaro.
- `--from FILE` (ripetibile, `--set` prevale), con le chiavi verificate il 25/10/2026:
  - `proiezione-inps.py`: `eta_pensionamento` → `ETA_PENSIONE`;
  - `netto-pensione.py`: `netto_pensione_inps` → `PENSIONE_NETTA`;
  - `glidepath-obiettivi.py`: `portafoglio` (quota azionaria aggregata per anno) e `anni` → percorso dell'allocazione per la diagnosi 3.
  - L'ordine di precedenza è: `--set` > `--dati` > `--from` > costanti dello script.
- `--composizione FILE`: CSV `strumento;settore;peso` (pesi in frazione o in percento, normalizzati per strumento), compilato dalle schede degli emittenti. Attiva la diagnosi 4.

### 5.1 Bilancio patrimoniale totale

Tabella con valore, peso su W e quota azionaria di: portafoglio, fondo pensione, TFR maturato, liquidità, capitale umano (riga azionaria e riga obbligazionaria), capitale pensionistico; totale; «altri attivi» sotto la riga del totale, se presenti.

### 5.2 Esposizione azionaria

`esposizione_finanziaria` contro `esposizione_totale`, con una frase generata che spiega lo scarto (peso del capitale umano su W e sua quota azionaria).

**Riga di equivalenza (D5)**, solo se c'è `esposizione_totale_desiderata` = T:

```
X = (T × W − HC_az − F_az_non_portafoglio) / F_portafoglio
```

dove `F_az_non_portafoglio` è la parte azionaria del fondo pensione (si assume fissa) e `F_portafoglio` = posizioni + liquidità. X è limitato tra 0 e 1; se il limite scatta lo script lo dice («anche al 100% in azioni l'esposizione totale resta al Y%», o l'opposto). Etichetta fissa: «calcolo, non target: non modifica l'allocazione degli obiettivi né quella di it-rebalance».

### 5.3 Proiezione nel tempo

Anno per anno dall'età attuale a `eta_pensione + 5`:

- `HC_t` ricalcolato con gli anni residui; `PP_t` con lo sconto che si accorcia;
- `F_{t+1} = F_t × (1 + r_port_t) + risparmio_annuo`, con `r_port_t` = rendimento atteso reale della quota azionaria dell'anno: quella attuale costante oppure, con `--from` del glide path, quella dell'anno. Rendimenti attesi **reali, annualizzati (composti) e netti di costi e imposte**: costanti `REND_AZ_REALE` (default 3%: il 5,2% reale lordo mondiale DMS portato al netto con i passi di `mercati-e-correlazione.md`) e `REND_OBB_REALE` (default 0,5%). Il percorso deterministico usa questi tassi; nel Monte Carlo la deriva lognormale è fissata in modo che la mediana coincida con essi. Dopo la pensione il risparmio è 0;
- **fascia P10-P90**: Monte Carlo con `N_SIM` (default 2.000) e `SEED` fisso. Shock di borsa lognormali (μ, σ_S = 18%) e shock di reddito correlati (eq. A.6-A.9: `Z_h = ρ Z_S + √(1−ρ²) Z`), con ρ e σ_h del profilo. Il reddito simulato cambia il risparmio (in proporzione) e il valore di HC; ne escono P10, P50 e P90 dell'esposizione totale.

Output: tabella ogni 5 anni (età, F, HC, PP, HC/W, esposizione totale P10/P50/P90) e l'età in cui F supera HC.

### 5.4 Sovrapposizione settoriale

Con `--composizione`:

```
quota_settore_fin  = Σ_posizioni_az (valore × peso_settore_strumento) / Σ valore_az
esposizione_comb   = (F_az × quota_settore_fin + HC_az) / (F_az + HC_az)
```

Si assume che `HC_az` stia tutta nel settore dell'utente: è un'ipotesi dichiarata e conservativa. Il confronto è con il peso del settore nel mercato mondiale, costante `PESI_MONDO` (dizionario GICS → peso, con data e fonte in commento; da riverificare a ogni release). Avviso se `quota_settore_fin` > 2 × peso mondiale. Gli strumenti senza riga nel CSV sono elencati come «composizione mancante» ed esclusi, dicendolo. Il fondo pensione non entra nella diagnosi (composizione non disponibile), e la nota lo dice.

### 5.5 Sensibilità

Un parametro alla volta, rispetto al caso base: `s` ±0,10; `ν` ±0,015; `g` a 0 e a 0,02; `p_u` × 2; `r_f` ±0,01. Per ognuno, HC e esposizione totale. Ordinamento «tornado» per ampiezza dell'effetto sull'esposizione totale.

### Output

Report su stdout (formati italiani via `numero()`, `euro()`, `pct()`; UTF-8 forzato) e `--json FILE` con le chiavi: `bilancio`, `esposizione_finanziaria`, `esposizione_totale`, `equivalenza` (null se non richiesta), `proiezione` (lista per anno), `eta_sorpasso`, `settore` (null senza `--composizione`), `sensibilita`, `profilo_usato` (con gli override). Codici d'uscita: 0 riuscito, 1 dati incoerenti (con `ERRORE:` su stderr), 2 riga di comando errata.

**Controlli sui dati (rc 1):** profilo sconosciuto; `eta ≥ eta_fine`; `eta_pensione < eta` con reddito > 0 (si accetta `eta_pensione == eta`: HC = 0); quote fuori da [0, 1]; valori negativi; `--composizione` con pesi che non sommano a circa 1 per strumento (tolleranza 2%); `persone` al posto di `persona`.

## 6. File

**Nuovi** (`skills/it-pianificazione-obiettivi/`):
- `assets/capitale-umano.py`, con l'interfaccia comune di `motore_bootstrap.cli`;
- `assets/profili-capitale-umano.csv`;
- `assets/esempio-capitale-umano.json` e `assets/esempio-composizione.csv`;
- `references/capitale-umano.md`: metodo, bibliografia, limiti, esempio svolto, `Verificato:` sui valori NASpI, indice (supera le 100 righe);
- `commands/capitale-umano.md` (alla radice, accanto agli altri comandi), alias della skill con il disclaimer.

**Modificati:**
- `skills/it-pianificazione-obiettivi/SKILL.md`: «Step 7 (facoltativo): la lente del capitale umano», parole chiave nella `description` (entro i 1.024 caratteri), `metadata.version` incrementata;
- `skills/it-revisione/assets/template-revisione.md` e `SKILL.md`: sezione che riporta le diagnosi 2 e 4 dal `--json`;
- `tests/run_tests.py`: i test della §7;
- `README.md`: tabella degli strumenti, conteggio dei test, architettura; `CHANGELOG.md`; `ROADMAP.md` (§8).

## 7. Test (TDD, prima del codice)

**Valori chiusi**
1. Con g = 0, p_u = 0, ν = 0, contributi e TFR a 0: HC = netto × (1 − (1+r_f)^−N) / r_f.
2. Bilancio dell'esempio: HC, PP, W, esposizione finanziaria e totale a valori fissi (calcolati a mano nella reference).
3. Sovrapposizione su un CSV di test: percentuali esatte.
4. Equivalenza su un caso interno e su due casi che toccano i limiti 0 e 1, con il messaggio.

**Invarianti**
5. HC decresce con ν e con p_u, cresce con g.
6. s = 0 e portafoglio con azioni: esposizione totale < esposizione finanziaria.
7. Nella proiezione HC scende e vale 0 all'età di pensione e oltre; PP cresce fino alla pensione (sconto più corto) e poi scende.
8. Con ρ = σ_h = 0 il percorso simulato di HC è identico in tutte le simulazioni; con anche σ_S = 0 P10 = P50 = P90 e coincidono con il percorso deterministico. Con lo stesso `SEED` due esecuzioni danno lo stesso JSON.
9. `quota_reddito_azioni_datore` = 1 dà s_eff = 1.

**Ricostruzione di Ibbotson**
10. Con il caso di Ibbotson (reddito certo, 25 anni, 50.000 di reddito, 50.000 di patrimonio, pensione pubblica di 10.000 l'anno dai 65; tasso reale 2% = 5% − 3% della tab. 2.1; sconto aggiuntivo da fissare nel piano): (HC + PP)/W intorno al 94%, perché Ibbotson include la pensione nel capitale umano. Tolleranza larga: il riferimento è letto da un grafico (fig. 2.3).

**Profili e interfaccia**
11. Ogni riga del CSV ha `fonte` e `natura`, valori negli intervalli plausibili, nessun profilo duplicato.
12. Lo script entra in `SCRIPT_CLI` (da 14 a 15, assert compreso): `--help`, argomento ignoto con rc 2, `ERRORE:` pulito su file mancante e su `--set` sconosciuta, console cp1252, formati italiani.
13. Errori sui dati della §5 (rc 1), uno per controllo.
14. Catena: `proiezione-inps.py --json` e `netto-pensione.py --json` → `capitale-umano.py --from ... --from ...` girano e i valori arrivano (età di pensione e pensione netta nel `profilo_usato`/bilancio).
15. Freshness: `references/capitale-umano.md` in `OBBLIGATI_FRESHNESS`; il test di igiene sui commands trova il disclaimer in `capitale-umano.md`.
16. README: tabella dei test rigenerata con `--tabella-test` e conteggio aggiornato (i test di igiene esistenti lo verificano).

Dipendenze: Python 3.11 e numpy, già richieste. Nessun pacchetto nuovo, nessuna chiamata di rete.

## 8. ROADMAP

Sotto «Dopo — da decidere»:

**T15 Capitale umano, lente diagnostica** (P2, L), questa spec:
- [ ] script, profili, esempi, reference, comando, Step 7;
- [ ] diagnosi 1-5 con la riga di equivalenza;
- [ ] integrazione in `it-revisione`;
- [ ] test della §7.
- Sviluppi successivi, da decidere: secondo reddito del nucleo; volatilità personale dall'estratto INPS (`importa-previdenza.py`); aggiustamento dei target (opzione B); polizza vita (Ibbotson cap. 3; Chen et al. 2006).

**T16 Fonti dati esterne e connettori** (P2), con il principio D10 (script di calcolo offline; importatore su file o fetch di Claude nella cartella di lavoro):

| Priorità | Dato | Serve per | Fonte | Forma |
|---|---|---|---|---|
| Alta | Composizione degli ETF per settore e paese | Diagnosi 4; look-through del portafoglio | File delle posizioni di iShares, Xtrackers, Vanguard, Amundi, SPDR | Importatore offline dei formati degli emittenti → `composizione.csv` |
| Media | Tasso reale privo di rischio dell'area euro | `R_F` | BCE Data Portal (curva dei tassi; aspettative d'inflazione SPF); BTP€i/OAT€i | Fetch di Claude o `--set R_F` |
| Media | Perdita del lavoro e durata della disoccupazione per settore e contratto | `p_u`, `durata_anni` | ISTAT (flussi delle forze di lavoro); Osservatorio INPS su precariato e NASpI | Calibrazione annuale con `Verificato:` |
| Media | Parametri NASpI | `sostituzione_naspi` | Circolare INPS annuale | Manuale, in freshness |
| Bassa | Volatilità delle retribuzioni per settore | `sigma_h` | ISTAT (retribuzioni contrattuali); Eurostat SES; Banca d'Italia SHIW | Calibrazione una tantum, citata nel CSV |
| Bassa | Rendimenti azionari europei e mondiali | Correlazioni e bootstrap non solo USA | Kenneth French Data Library (gratuita); MSCI, DMS (a pagamento) | CSV sostitutivo di `rendimenti-storici.csv` |

Per ogni fonte: licenza (quelle a pagamento non si ridistribuiscono nel repository) e mese di verifica.

## 9. Limiti dichiarati (da riportare nella reference e nel report)

- La quota azionaria del capitale umano è una **stima per categoria**, non una misura personale: la sensibilità mostra quanto pesa.
- Il capitale umano non è vendibile né frazionabile: l'esposizione totale è una lente per ragionare, non un portafoglio da replicare.
- La correlazione di lungo periodo (cointegrazione) è catturata solo dalla scelta di `s`, non modellata.
- La pensione INPS è trattata come rendita certa al netto di `ν_pens`; il rischio normativo vero non è quantificabile.
- La sovrapposizione settoriale assume tutto `HC_az` nel settore dell'utente.
- Nessuna fiscalità esplicita sul TFR; nella proiezione costi e imposte sono già dentro i rendimenti reali netti (convenzione dichiarata, coerente con il resto della skill).
