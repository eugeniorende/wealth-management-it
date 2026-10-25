# Il capitale umano nella ricchezza totale

Il portafoglio di chi lavora non è tutta la sua ricchezza: il bene più grande, per decenni, è il **capitale umano**, cioè il valore attuale dei redditi da lavoro che verranno. Questa reference spiega come lo calcola lo script `assets/capitale-umano.py`, come leggere le sue cinque diagnosi e dove il metodo si ferma. È una **lente**, non un target: non cambia l'allocazione degli obiettivi né quella che `it-rebalance` mantiene. Non è consulenza.

## Indice

- Perché guardare oltre il portafoglio
- Il modello
- Azione o obbligazione: la quota azionaria del capitale umano
- I profili e come sceglierli
- La NASpI nel modello
- Le cinque diagnosi
- Esempio svolto
- I dati e come lanciarlo
- Limiti
- Bibliografia

## Perché guardare oltre il portafoglio

A 35 anni un dipendente con €32.000 netti l'anno ha davanti trent'anni di stipendi: scontati a un tasso prudente valgono circa €700.000, molto più di qualsiasi portafoglio costruito fin lì. Ignorarli porta a due errori opposti:

- chi ha un reddito **stabile** (un dipendente pubblico, un insegnante) possiede già una grossa «obbligazione» indicizzata: un portafoglio prudente lo rende, nel complesso, ancora più prudente di quanto vorrebbe;
- chi ha un reddito **legato ai mercati** (finanza, tecnologia, un'impresa propria) possiede già molta «azione», spesso dello stesso settore: un portafoglio aggressivo raddoppia la scommessa.

L'idea risale a Merton (1971), che somma alla ricchezza il salario scontato al tasso privo di rischio, e a Bodie, Merton e Samuelson (1992), per cui chi può modulare quanto e fino a quando lavorare regge più rischio. La forma pratica usata qui è quella di Ibbotson, Milevsky, Chen e Zhu (2007): il capitale umano va trattato come una classe di attivo, con il suo rischio e la sua correlazione con i mercati.

## Il modello

Tutto in **euro di oggi** e in termini **reali**; i redditi sono **netti**, perché i contributi tornano indietro come pensione e la pensione si valuta a parte.

```
Ricchezza totale W = capitale finanziario F + capitale umano HC + capitale pensionistico PP

HC = Σ_{t=1..N} E[h_t] / (1 + r_f + ν)^t                         (Ibbotson et al. 2007, eq. 2.1)
h_t    = (netto annuo + TFR annuo + contributo del datore al fondo) × (1 + g)^t
E[h_t] = h_t × (1 − p_u × durata × (1 − sostituzione NASpI))
N      = anni alla pensione

PP = Σ_{t=N+1..T} pensione netta / (1 + r_f + ν_pens)^t          T = anni all'età finale (default 90)

F  = posizioni + fondo pensione + TFR maturato in azienda + liquidità
```

- `r_f` è il tasso reale privo di rischio (default 1%, `--set R_F=...`). Il premio `ν` del profilo sconta illiquidità e rischio specifico del lavoro: Huggett e Kaplan (2016) mostrano che scontare i redditi al solo `r_f` sopravvaluta molto il capitale umano. Ibbotson et al. usano un 4% complessivo, che per un 45enne con 20 anni di stipendio vale circa il 25% di sconto.
- `p_u × durata` è la frazione d'anno attesa senza lavoro; la NASpI ne copre una parte (vedi sotto).
- La pensione INPS è un blocco a sé, valutato con un piccolo premio per il rischio normativo (`NU_PENSIONE`, default 0,75%). Il montante contributivo si rivaluta con il PIL nominale, quindi la pensione non è del tutto slegata dall'economia, ma qui si tratta come una rendita indicizzata, cioè un'obbligazione.

## Azione o obbligazione: la quota azionaria del capitale umano

Il capitale umano si divide in una parte che si comporta come un'**azione** e una che si comporta come un'**obbligazione**:

```
s_eff = quota del reddito pagata in azioni del datore + (1 − quella quota) × quota_azionaria_hc
HC_az = s_eff × HC          HC_obb = (1 − s_eff) × HC
Esposizione azionaria totale = (azioni finanziarie + HC_az) / W
```

Ibbotson et al. derivano la quota dal beta del reddito sulla borsa, β = ρ·σ_h/σ_S (eq. A.11). Con le correlazioni di breve periodo misurate da Davis e Willen (circa tra −0,2 e 0,1) quella formula dà il 2-6% a quasi tutti: il capitale umano sarebbe sempre un'obbligazione. Ma nel lungo periodo salari e dividendi si muovono insieme (Benzoni, Collin-Dufresne e Goldstein 2007) e la componente azionaria misurata sui redditi reali arriva al 35% (Huggett e Kaplan 2016). Per questo lo script usa una **quota esplicita per profilo**, nello spirito di Milevsky («sei un'azione o un'obbligazione?»): un solo numero che decide, leggibile senza formule. Correlazione `rho` e volatilità `sigma_h` servono solo alla fascia della proiezione e restano nel profilo.

## I profili e come sceglierli

I sei profili stanno in `assets/profili-capitale-umano.csv`, con la fonte di ogni riga e la natura di ogni valore (letteratura, giudizio, da verificare). Si sceglie quello più vicino e si correggono i singoli valori con `persona.override`.

| Profilo | Quota azionaria | ν | Per chi |
|---|---|---|---|
| `pubblico` | 5% | 1% | Dipendenti pubblici di ruolo: il «professore di ruolo» di Ibbotson, un'obbligazione reale |
| `privato_stabile` | 15% | 2% | Dipendenti privati con contratto collettivo in settori poco ciclici |
| `privato_ciclico` | 30% | 3% | Dipendenti privati in settori ciclici: tecnologia, edilizia, automotive, turismo |
| `finanza` | 50% | 3% | Banca, gestione del risparmio, intermediazione: reddito e bonus seguono i mercati |
| `autonomo` | 30% | 4% | Professionisti e forfettari: niente NASpI, reddito più volatile (Heaton e Lucas 2000) |
| `imprenditore` | 60% | 5% | Chi possiede l'azienda in cui lavora |

- **Precari e contratti a termine**: `privato_ciclico` con una probabilità di perdere il lavoro più alta, indicativamente `"override": {"p_u": 0.12}` (tra 0,10 e 0,15).
- **Stock option, RSU, piani di azionariato**: `quota_reddito_azioni_datore`, la parte della retribuzione pagata in azioni del datore. Conta tutta come azione: è la concentrazione più rischiosa, perché lavoro e risparmio dipendono dalla stessa impresa.
- **Settore**: `persona.settore` con il nome GICS inglese (per esempio `Information Technology`), lo stesso dei file delle posizioni degli ETF. Serve alla diagnosi 4.
- I valori di `p_u` e `ν` sono calibrazioni di giudizio da verificare (fonti candidate in ROADMAP, tema T16): la diagnosi 5 mostra quanto pesano.

## La NASpI nel modello

La NASpI riduce il costo atteso di un periodo senza lavoro. Le regole (art. 4 D.Lgs. 22/2015, testo vigente letto su Normattiva):

- l'importo è il 75% della retribuzione mensile media degli ultimi quattro anni fino alla retribuzione di riferimento, più il 25% della parte che la supera (c. 2);
- per il 2026 la retribuzione di riferimento è **€1.456,72** e l'importo massimo **€1.584,70** al mese (Circ. INPS n. 4 del 28/01/2026, § 6);
- per gli eventi dal 1° gennaio 2022 l'indennità cala del 3% al mese dal sesto mese di fruizione, dall'ottavo per chi ha compiuto 55 anni alla domanda (c. 3).

*(Verificato: 2026-10, art. 4 D.Lgs. 22/2015 su Normattiva e Circ. INPS 4/2026.)*

Il profilo usa una sola `sostituzione_naspi` (default 0,6) come media del periodo: va bene per un reddito medio (circa €2.300 lordi al mese: NASpI di circa €1.300 lordi, poi il calo), ma **sovrastima i redditi alti**, che il tetto di €1.584,70 taglia. Con €32.000 netti l'anno la NASpI copre meno della metà del netto: per un calcolo più fedele `"override": {"sostituzione_naspi": 0.45}`. L'effetto sull'esposizione è piccolo (lo mostra la diagnosi 5), quello sul valore del capitale umano un po' meno.

## Le cinque diagnosi

1. **Bilancio patrimoniale totale.** Valore, peso e quota azionaria di ogni voce: portafoglio, fondo pensione, TFR maturato, liquidità, capitale umano (parte azionaria e obbligazionaria), capitale pensionistico. Gli «altri attivi» (casa e simili) compaiono sotto la tabella ma restano fuori dall'esposizione.
2. **Esposizione azionaria.** Quella del solo patrimonio finanziario contro quella della ricchezza totale. Con `esposizione_totale_desiderata` lo script aggiunge la **riga di equivalenza**: la quota azionaria che il portafoglio (posizioni e liquidità) dovrebbe avere per arrivare a quell'esposizione totale, con fondo pensione e capitale umano fermi, limitata tra 0 e 100%. È un calcolo, non un target: non modifica l'allocazione degli obiettivi né quella di it-rebalance.
3. **Proiezione.** Anno per anno fino a cinque anni dopo la pensione. Il patrimonio cresce con il risparmio e con rendimenti reali netti (default 3% azioni, 0,5% obbligazioni: la calibrazione mondiale di `mercati-e-correlazione.md`), con la quota azionaria di oggi o quella del glide path (`--from` del JSON di `glidepath-obiettivi.py`); il capitale umano si consuma. Un Monte Carlo con shock di borsa e di reddito correlati (Ibbotson et al., eq. A.6-A.9) dà la fascia P10-P90 dell'esposizione totale. La lettura chiave: **a parità di allocazione, l'esposizione totale sale con l'età**, perché la parte obbligazionaria del capitale umano si esaurisce. È la ragione teorica del de-risking nel ciclo di vita.
4. **Sovrapposizione settoriale.** Quanto della parte azionaria del portafoglio sta nel settore del proprio lavoro, contro il suo peso nell'indice MSCI ACWI, e quanto ci sta l'insieme di azioni e capitale umano azionario (che si assume tutto in quel settore). Avvisa oltre 2 volte il peso di mercato. Un ETF globale non è «neutro» per chi lavora nella tecnologia: un terzo dell'indice mondiale è già tecnologia.
5. **Sensibilità.** Un parametro alla volta: quota azionaria ±10 punti, ν ±1,5 punti, crescita del reddito 0% e 2%, probabilità di perdere il lavoro raddoppiata, tasso privo di rischio ±1 punto. Ordinata dal parametro che sposta di più l'esposizione totale.

## Esempio svolto

Il file `assets/esempio-capitale-umano.json`: sviluppatore di 35 anni, dipendente privato nella tecnologia (`privato_ciclico`, con `p_u` a 8%), €32.000 netti e €3.000 di TFR l'anno, crescita reale 1%, pensione a 67 anni con €18.000 netti l'anno; portafoglio di €60.000 in azioni e €20.000 in obbligazioni, €10.000 di liquidità, €15.000 nel fondo pensione (60% azioni), €8.000 di TFR in azienda.

- Frazione lavorata attesa: 1 − 0,08 × 0,5 × (1 − 0,6) = 0,984. Sconto 1% + 3% = 4%.
- Capitale umano: €705.036, di cui €211.511 azionari (30%). Capitale pensionistico: €194.249. Patrimonio finanziario: €113.000. Ricchezza totale: €1.012.285.
- Esposizione azionaria: **61,1%** sul patrimonio finanziario, **27,7%** sulla ricchezza totale.
- Equivalenza: per un'esposizione totale del 25% il portafoglio dovrebbe stare al 36,2% in azioni; per il 50% non basterebbe nemmeno il 100% di azioni.
- Proiezione: con la stessa allocazione l'esposizione totale sale verso il 40% alla pensione; il patrimonio finanziario supera il capitale umano intorno ai 56 anni.
- Sensibilità: domina la quota azionaria del capitale umano (±7 punti di esposizione), poi il tasso privo di rischio.

## I dati e come lanciarlo

```
python "${CLAUDE_SKILL_DIR}/assets/capitale-umano.py" --dati capitale-umano.json --json capitale-umano-out.json
python "${CLAUDE_SKILL_DIR}/assets/capitale-umano.py" --dati capitale-umano.json --composizione composizione.csv
python "${CLAUDE_SKILL_DIR}/assets/capitale-umano.py" --dati capitale-umano.json --from inps.json --from netto.json
```

- Il JSON di `--dati` ha la forma dell'esempio. `posizioni` usa lo schema di `it-rebalance` (`asset_class`: `azionario`, `obbligazionario`, `monetario`; altre classi contano come non azionarie, con un avviso) e si copia da lì; `strumento` serve alla diagnosi 4.
- `--from` legge l'età di pensione dal JSON di `proiezione-inps.py` (`eta_pensionamento`), la pensione netta da quello di `netto-pensione.py` (`netto_pensione_inps`) e la quota azionaria per anno da quello di `glidepath-obiettivi.py` (`portafoglio`). Precedenza: `--set` > `--dati` > `--from` > costanti. La crescita reale del reddito non è nel JSON della proiezione INPS: va scritta in `persona.crescita_reale`, con lo stesso valore usato lì.
- `--composizione` è un CSV `strumento;settore;peso` (pesi in percento o in frazione, virgola o punto) compilato dalla scheda dell'ETF sul sito dell'emittente, sezione dei pesi per settore. Esempio in `assets/esempio-composizione.csv`.
- Il JSON di `--json` porta `bilancio`, `esposizione_finanziaria`, `esposizione_totale`, `equivalenza`, `proiezione`, `eta_sorpasso`, `settore`, `sensibilita` e `profilo_usato`; `it-revisione` ne legge le esposizioni e la sovrapposizione.

## Limiti

- La quota azionaria del capitale umano è una **stima per categoria**, non una misura personale: la diagnosi 5 dice quanto pesa.
- Il capitale umano non si vende né si fraziona: l'esposizione totale è una lente per ragionare, non un portafoglio da replicare. Per questo lo script non tocca i target.
- La correlazione di lungo periodo (cointegrazione) entra solo attraverso la scelta della quota, non è modellata.
- La pensione INPS è trattata come una rendita certa al netto di `NU_PENSIONE`: il rischio normativo vero non è quantificabile.
- La sovrapposizione settoriale assume tutto il capitale umano azionario nel settore del proprio lavoro, ed esclude il fondo pensione.
- Nessuna fiscalità esplicita su TFR e rendimenti: costi e imposte sono nei rendimenti reali netti, come nel resto della skill. Un solo reddito: il secondo reddito del nucleo è uno sviluppo futuro (ROADMAP, T15).

## Bibliografia

Verificata il 25/10/2026 (testo letto per Merton 1971 e Ibbotson et al. 2007; per gli altri schede di NBER, RePEc, editori e autori).

- Bodie e Samuelson (1989), «Labor Supply Flexibility and Portfolio Choice», NBER WP 3043: https://www.nber.org/papers/w3043
- Bodie, Merton e Samuelson (1992), «Labor Supply Flexibility and Portfolio Choice in a Life-Cycle Model», *Journal of Economic Dynamics and Control* 16(3-4):427-450; NBER WP 3954: https://www.nber.org/papers/w3954
- Merton (1971), «Optimum Consumption and Portfolio Rules in a Continuous-Time Model», *Journal of Economic Theory* 3:373-413, § 7.
- Viceira (2001), «Optimal Portfolio Choice for Long-Horizon Investors with Nontradable Labor Income», *Journal of Finance* 56(2):433-470; NBER WP 7409: https://www.nber.org/papers/w7409
- Benzoni, Collin-Dufresne e Goldstein (2007), «Portfolio Choice over the Life-Cycle when the Stock and Labor Markets Are Cointegrated», *Journal of Finance* 62(5):2123-2167.
- Campbell e Viceira (2002), *Strategic Asset Allocation*, Oxford University Press, cap. 6.
- Ibbotson, Milevsky, Chen e Zhu (2007), *Lifetime Financial Advice: Human Capital, Asset Allocation, and Insurance*, CFA Institute Research Foundation: https://rpc.cfainstitute.org/sites/default/files/-/media/documents/book/rf-publication/2007/rf-v2007-n1-4580-pdf.pdf
- Chen, Ibbotson, Milevsky e Zhu (2006), «Human Capital, Asset Allocation, and Life Insurance», *Financial Analysts Journal* 62(1):97-109.
- Milevsky (2008; ed. riveduta 2013), *Are You a Stock or a Bond?*, FT Press.
- Huggett e Kaplan (2016), «How Large Is the Stock Component of Human Capital?», *Review of Economic Dynamics* 22:21-51; NBER WP 21238: https://www.nber.org/papers/w21238
- Bodie, Treussard e Willen (2007), «The Theory of Life-Cycle Saving and Investing», Federal Reserve Bank of Boston, Public Policy Discussion Paper 07-3.
- Davis e Willen (2000), «Occupation-Level Income Shocks and Asset Returns: Their Covariance and Implications for Portfolio Choice», NBER WP 7905: https://www.nber.org/papers/w7905 (versione pubblicata: *Quarterly Journal of Finance*, 2013).
- Heaton e Lucas (2000), «Portfolio Choice and Asset Prices: The Importance of Entrepreneurial Risk», *Journal of Finance* 55(3):1163-1198.
- Guiso, Jappelli e Terlizzese (1996), «Income Risk, Borrowing Constraints, and Portfolio Choice», *American Economic Review* 86(1):158-172: dati italiani dell'indagine della Banca d'Italia sui bilanci delle famiglie.
- Cocco, Gomes e Maenhout (2005), «Consumption and Portfolio Choice over the Life Cycle», *Review of Financial Studies* 18(2):491-533 (citato solo per la conclusione qualitativa: il reddito da lavoro sostituisce le attività sicure).
- Bagliano, Fugazza e Nicodano (2014), «Optimal Life-Cycle Portfolios for Heterogeneous Workers», *Review of Finance* 18(6):2283-2323.
- Gomes (2020), «Portfolio Choice Over the Life Cycle: A Survey», *Annual Review of Financial Economics* 12:277-304.
- Duarte, Fonseca, Goodman e Parker (2021), «Simple Allocation Rules and Optimal Portfolio Choice Over the Lifecycle», NBER WP 29559: https://www.nber.org/papers/w29559
- Catherine (2022), «Countercyclical Labor Income Risk and Portfolio Choices over the Life Cycle», *Review of Financial Studies*.
