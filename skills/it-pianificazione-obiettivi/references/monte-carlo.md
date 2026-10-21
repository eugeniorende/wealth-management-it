# Monte Carlo per la pianificazione obiettivi

Questa reference spiega il senso, il modello e soprattutto i **limiti** della simulazione Monte Carlo applicata agli obiettivi. Lo strumento è `assets/montecarlo-obiettivi.py`.

## Perché il deterministico non basta

Il pianificatore Excel calcola il versamento mensile usando il rendimento atteso **medio** del profilo. Questo centra la media della distribuzione dei risultati — ma la media non è il risultato "probabile". Per due ragioni:

1. **Il versamento deterministico dà ~50% di probabilità (o meno)**. Se punti alla media, hai circa una probabilità su due di superarla e una su due di restare sotto. Per un obiettivo essenziale (il fondo di emergenza, l'anticipo della casa) un testa-o-croce non è accettabile: vuoi confidenza alta.

2. **Il "volatility drag" spinge la mediana sotto la media**. Quando i rendimenti oscillano, la crescita composta realizzata è inferiore alla media aritmetica (di circa σ²/2 all'anno). Più lungo l'orizzonte e più alta la volatilità, più la mediana scende sotto il target deterministico. Per questo, nell'esempio del plugin, l'obiettivo a 20 anni con profilo Crescita ha solo il ~42% di probabilità di successo col versamento deterministico, mentre il fondo di emergenza (bassa volatilità) sta vicino al 49%. Il divario dipende dalla convenzione: il rendimento del profilo è una **media aritmetica** (vedi sotto); se lo si leggesse come rendimento annualizzato, il versamento deterministico tornerebbe intorno al 50%.

Il Monte Carlo rende esplicito tutto questo: invece di un numero ("ti serve €500/mese"), dà una **probabilità** (con €500/mese hai il 45% di arrivarci; per l'85% te ne servono €547). I numeri sono quelli dell'anticipo casa del pianificatore d'esempio, col glide path.

## Il modello

Per ciascun obiettivo, lo script simula migliaia di percorsi di accumulo (default 20.000):

```
Per ogni percorso:
  saldo = già_accantonato
  per ogni anno fino all'orizzonte:
      (media, volatilità) dell'anno: quelle del profilo, o lungo il glide path
      per ogni mese:
          r = estrazione casuale da Normale(media_mensile, volatilità_mensile)
          saldo = saldo × (1 + r) + versamento_mensile
  registra il saldo finale

Probabilità di successo = frazione di percorsi con saldo_finale ≥ target_nominale
```

Dove:
- **media mensile** = (1 + rendimento_annuo)^(1/12) − 1: la media mensile tale che il rendimento annuo **atteso** (la media aritmetica dei rendimenti annui) sia il rendimento del profilo. La crescita composta **mediana** resta sotto di circa σ²/2: con la Crescita (5,5%, volatilità 13%) è circa 4,65%
- **volatilità mensile** = volatilità_annua / √12 (scaling radice-tempo, ipotesi i.i.d.)
- **target nominale** = target di oggi × (1 + inflazione)^anni (coerente col foglio Excel)

**Convenzione del rendimento: media aritmetica.** Il versamento deterministico (foglio, colonna I) capitalizza il rendimento del profilo anno per anno; nel modello quel rendimento è la media attesa di ciascun anno, quindi il deterministico centra la **media** del capitale finale (con volatilità quasi nulla la probabilità tende al 50%). Le fonti di lungo periodo come il Global Investment Returns Yearbook danno invece rendimenti **annualizzati** (geometrici): per tarare un profilo su quelle cifre si aggiunge σ²/2 (4,65% netto annualizzato con volatilità 13% ↔ 5,5% del foglio). Vedi `mercati-e-correlazione.md`.

**Glide path (default, `GLIDE = True`).** Gli obiettivi **terminanti** seguono il calendario di `glidepath-obiettivi.py`: quota del profilo finché mancano più di `FINESTRA_DERISK` anni (Parametri!B7, 7 nell'esempio), poi riduzione anno per anno fino a 0% azionario alla scadenza. Durante la rampa il secchiello è una miscela del portafoglio del profilo e di quello di atterraggio (Preservazione): rendimento e volatilità dell'anno sono lineari nella quota. Il versamento deterministico è quello del foglio, che tiene conto del de-risking (`matematica-accumulo.md`); se si cambiano `ATTERRAGGIO_AZ`, `CURVATURA` o la finestra, o il pianificatore è precedente alla 0.10.0, non lo è più e lo script lo segnala. I **permanenti** tengono la quota del profilo. Con `--set GLIDE=False` si torna alla quota fissa fino alla scadenza, nel versamento e nella simulazione.

Lo script riporta, per ogni obiettivo: la probabilità di successo col versamento deterministico, i percentili del capitale finale (10°/50°/90°), e il **versamento che servirebbe per una confidenza-obiettivo** (default 85%, calcolato per bisezione).

## Le volatilità per profilo

Sono nella tabella del foglio Parametri (colonna "Volatilità attesa"), editabili. Valori di default (volatilità annua nominale):

| Profilo | Rendimento | Volatilità | Razionale |
|---|---|---|---|
| Preservazione | 1,5% | 1,5% | Liquidità: oscillazioni minime |
| Conservativo | 2,5% | 4,5% | Obbligazionario breve/medio, ~10% azionario |
| Moderato | 4,0% | 8,5% | Bilanciato ~40% azionario |
| Crescita | 5,5% | 13,0% | ~65% azionario |
| Crescita massima | 6,5% | 16,5% | ~90% azionario |
| Azionario totale | 6,9% | 18,0% | 100% azionario, obiettivi a orizzonte perpetuo (eredità) |

Sono ordini di grandezza coerenti con le volatilità storiche di lungo periodo delle rispettive classi. Editabili se si vogliono ipotesi diverse.

## Come interpretare la probabilità di successo

Il punto NON è massimizzare la probabilità su ogni obiettivo (servirebbe versare moltissimo). È **calibrare la confidenza alla criticità dell'obiettivo**:

- **Obiettivi essenziali** (fondo di emergenza, spese irrinunciabili): confidenza alta, 85-95%. Qui un fallimento fa male, si versa di più del deterministico.
- **Obiettivi importanti** (anticipo casa): confidenza media-alta, 75-85%.
- **Obiettivi desiderabili** (libertà finanziaria, extra): si può accettare confidenza più bassa, 50-70%, e lasciare che sia il mercato a decidere se si fa di più. Se va male, si rimanda; se va bene, si arriva prima.

Questo permette di **allocare la capacità di risparmio in modo intelligente**: alta confidenza dove serve, più rischio (e meno versamento) dove ci si può permettere di "lasciar correre".

## Sequence-of-returns risk

La simulazione genera percorsi completi, quindi cattura il **rischio di sequenza**: l'ordine dei rendimenti conta, non solo la media. In fase di accumulo l'effetto è moderato (i versamenti continui mediano i prezzi), ma esiste: una brutta sequenza proprio prima della scadenza può mancare l'obiettivo anche se la media di lungo periodo era buona. È il motivo del glide path (de-risking all'avvicinarsi dell'obiettivo, vedi `glide-path.md`), che la simulazione include: riduce l'esposizione proprio quando una sequenza avversa farebbe più danni. In fase di decumulo il rischio di sequenza è molto più grave: vedi `decumulo.md`.

## Due modelli dei rendimenti: Normale e bootstrap storico

Lo script ha un parametro `MODELLO`:

- **`"normale"`** (default): rendimenti estratti da una Normale i.i.d. con la media e la volatilità del profilo. Veloce, semplice, ma con i limiti sotto (niente code grasse, niente correlazioni, niente mean reversion).
- **`"bootstrap"`**: ricampiona da una **serie storica** (`assets/rendimenti-storici.csv`: S&P 500 e T-Bond decennale, 1928-2025, fonte Damodaran/NYU Stern; rendimenti **nominali in dollari**). Per ogni obiettivo costruisce la serie storica del portafoglio secondo il **% azionario del profilo** (`peso·azionario + (1−peso)·obbligazionario`), e campiona **blocchi di anni consecutivi** (default 5) per preservare la sequenza storica. Cattura ciò che la Normale ignora: code grasse, asimmetria (i crash sono più profondi dei rally), la **correlazione storica azionario/obbligazionario** (le obbligazioni spesso salgono quando le azioni crollano — ma non sempre: nel 2022 sono crollate insieme), e la **mean reversion** dei blocchi pluriennali. Col glide path la quota de-riskata rende il rendimento dell'atterraggio.

**Ricentratura della media** (`RICENTRA_MEDIA`, default attivo): la media storica di un portafoglio 65/35 come quello della Crescita (~9,4% nominale lordo, media aritmetica 1928-2025) è molto più alta del rendimento del profilo (5,5% netto, cioè circa il 7,8% lordo con la conversione inversa di `asset-location-optimizer.py`). Per coerenza con il resto dello strumento, il bootstrap **ricentra la media** della serie sul rendimento atteso del profilo, mantenendo *forma, volatilità, asimmetria e code* della storia. In altre parole: la tua ipotesi di rendimento guida la tendenza centrale, la storia guida la forma della distribuzione. Per questo una serie nominale in dollari va bene qui: se ne usa la forma, non il livello. Disattivabile per usare le medie storiche grezze (che però sono nominali in dollari, non confrontabili con target in euro).

**Cosa aspettarsi**: contro-intuitivamente, su orizzonti lunghi il bootstrap può dare una distribuzione *più stretta* della Normale, non più larga. Il random walk i.i.d. fa crescere la varianza linearmente nel tempo; i mercati reali, grazie alla mean reversion e alla diversificazione azionario/obbligazionario, disperdono meno nel lungo periodo. La Normale quindi **sovrastima** la dispersione di lungo termine. Su orizzonti brevi, invece, un singolo anno-crash storico (es. −37% nel 2008) può rendere le code più estreme di quanto la Normale mensile aggregata mostri.

## Le tre strade per colmare un gap (e perché il rischio è a doppio taglio)

Quando il versamento per la confidenza-obiettivo supera la capacità, ci sono tre leve, non una: **versare di più**, **alzare il rischio**, **aggiustare l'obiettivo** (ridurre il target o allungare l'orizzonte). Lo strumento ha sempre mostrato la prima (il versamento per l'85%); ora mostra anche la **seconda strada** — alzare la quota azionaria a parità di versamento — perché quando i fondi mensili non si possono aumentare, è l'unica leva finanziaria rimasta oltre al ritoccare l'obiettivo.

Ma il rischio **non è un sostituto pulito** del versamento, e lo strumento lo dice apertamente invece di venderlo come gratis. Più azionario alza il rendimento atteso *e* la volatilità: la **mediana sale, ma la distribuzione si allarga**, e il caso brutto (10° percentile) può **peggiorare**. Siccome è proprio la coda sinistra a determinare la confidenza, alzare il rischio può comprare pochi punti di probabilità al prezzo di un worst case molto più severo. Per questo lo sweep riporta la **distribuzione intera** (P10/P50/P90), non solo la probabilità: si vede il prezzo, non solo il premio.

C'è anche un punto controintuitivo: la relazione **non è monotòna** né lineare. Oltre una certa quota azionaria il *volatility drag* (la mediana geometrica è la media meno σ²/2, e σ² cresce in fretta) frena la probabilità di centrare un target: la curva si appiattisce o scende, quindi il guadagno delle ultime quote è spesso rumore. Lo sweep sceglie il punto migliore della griglia, fino al 100%.

Su un obiettivo terminante la leva alza la quota **di partenza**: negli ultimi anni il glide path la riporta comunque verso l'atterraggio. Accanto all'OPZIONE lo strumento mostra entrambi i numeri, a parità di versamento: la probabilità **sul percorso glide** (il piano che `it-rebalance` esegue, quello che conta) e quella **a quota fissa fino alla scadenza**, più alta perché ignora il de-risking. Prima si mostrava solo la seconda, che prometteva più di quanto il piano avrebbe reso.

Quando la leva ha senso e quando no, lo strumento lo segnala:
- **Inadatta** per un obiettivo **essenziale**: mancare ciò che non puoi permetterti di mancare non è un'opzione, e più rischio allarga proprio quella coda. Meglio versare di più o ridurre il target.
- **Inadatta** per un obiettivo **importante**: la leva è riservata ai desiderabili, dove mancare il target ha un costo che si può reggere.
- **Inadatta** **entro la finestra di de-risking** (`FINESTRA_DERISK`, dal foglio: Parametri!B7, la stessa del glide path): in quegli anni il glide path porta la quota azionaria verso l'atterraggio, quindi alzarla contraddirebbe il piano; e su pochi anni la volatilità domina il rendimento atteso, quindi più rischio è quasi solo downside.
- **Controproducente** se sei **già in linea** (probabilità alta): aggiungi un downside che non ti serve — "quando hai vinto la partita, smetti di giocare" (Bernstein).
- **Opzione reale** solo se sei **sotto-finanziato, con orizzonte lungo, su un obiettivo discrezionale**: lì il maggior rendimento atteso ha il tempo di dominare, e l'aumento di probabilità è significativo. Anche allora, lo strumento mostra di quanto peggiora il caso brutto, e lascia la scelta a chi quel downside lo deve reggere.

L'entità dell'aiuto scala con la distanza dal target: su un obiettivo vicino al bersaglio (es. già finanziato alla mediana) la leva aggiunge pochi punti di probabilità ma peggiora sensibilmente il 10° percentile — un rilancio quasi tutto coda sinistra; su un obiettivo lontano dal target e a lungo orizzonte, può aggiungere molti punti. Nota di metodo: trattare l'allocazione come una **leva** (con il suo costo esplicito sul downside), e non come un parametro fisso dato a priori, è ciò che rende questo modello più onesto del trattare il portafoglio come un 60/40 immutabile.

## I limiti del modello (importante)

Un Monte Carlo è uno strumento per **ragionare sul rischio**, non una previsione. I suoi limiti vanno comunicati sempre:

1. **Con la Normale, niente code grasse**. Il modello `"normale"` estrae da una distribuzione Normale; i mercati reali hanno eventi estremi più frequenti (le code sono "grasse"), quindi **sottostima gli scenari peggiori** a breve. Il modello `"bootstrap"` mitiga questo limite usando i rendimenti storici (che le code grasse le contengono).

2. **Con la Normale, rendimenti i.i.d.**: ogni anno indipendente e identico al precedente, mentre la realtà ha autocorrelazione e mean reversion. Il `"bootstrap"` a blocchi preserva in parte la sequenza storica, ma resta vincolato al campione disponibile.

3. **Il passato non predice il futuro, e la serie è americana**: il bootstrap usa dati USA 1928-2025, nominali in dollari, di un investitore USA (il mercato con la serie più lunga e i rendimenti più favorevoli — *survivorship/success bias* — e nessuna componente di cambio per chi investe in euro). La ricentratura della media riduce questo bias sulla tendenza centrale, ma la *forma* resta quella della storia americana, che potrebbe non ripetersi. Si può sostituire il CSV con una propria serie.

4. **Volatilità e rendimenti attesi sono ipotesi**: cambiarli (tabella Parametri, o il CSV) cambia i risultati; sono il principale punto di incertezza.

5. **Correlazione tra obiettivi solo nel bootstrap**: nel modello normale ogni obiettivo è simulato per conto suo. Col bootstrap la sezione **rischio sistemico** simula gli obiettivi su un unico percorso di mercato condiviso (`mercati-e-correlazione.md`).

6. **Niente costi di transazione né tasse sulle vendite del de-risking**: il glide path è simulato, ma le vendite che lo eseguono, e i loro eventi fiscali, no. Anche la rampa è una semplificazione: la quota cambia una volta l'anno.

In sintesi: i numeri sono **ordini di grandezza per calibrare il rischio e i versamenti**, non garanzie né previsioni precise. Trattarli come tali. Confrontare i due modelli (Normale vs bootstrap) è un buon modo per vedere quanto le conclusioni dipendono dalle ipotesi distributive.

## Come eseguirlo

```bash
pip install numpy openpyxl
python montecarlo-obiettivi.py [percorso/pianificatore-obiettivi.xlsx]
```

Lo script legge gli obiettivi e i parametri dal foglio Excel (singola fonte di verità: si compila l'Excel, si lancia lo script). Senza argomenti, cerca `pianificatore-obiettivi.xlsx` nella stessa cartella. I parametri della simulazione (numero di percorsi, confidenza-obiettivo, seed, glide path) sono in cima allo script, editabili o sovrascrivibili con `--set` (es. `--set MODELLO=bootstrap`, `--set GLIDE=False`).

## Heuristic per la skill

1. **Usare il Monte Carlo per smontare la falsa precisione del deterministico**: il versamento "esatto" del foglio dà ~50%. Dirlo chiaramente.
2. **Calibrare la confidenza alla criticità**: alta sugli essenziali, accettabile più bassa sui desiderabili. Non massimizzare ovunque.
3. **Il volatility drag penalizza gli orizzonti lunghi ad alta volatilità**: l'obiettivo "tra 20 anni in azionario" ha bisogno di più rincalzo di quanto il deterministico suggerisca.
4. **Comunicare sempre i limiti**: code grasse, i.i.d., parametri ipotetici. Il MC è per ragionare sul rischio, non una previsione.
5. **Collegare al glide path**: il rischio di sequenza motiva il de-risking all'avvicinarsi dell'obiettivo, e il de-risking alza il versamento necessario.

## Due correzioni di onestà

Il modello ha due ipotesi nascoste che lo rendono più ottimista del dovuto, trattate in `mercati-e-correlazione.md`: (1) la serie storica è **USA** — il mercato più fortunato al mondo — e va de-ratata o calibrata su aspettative globali (azionario mondiale ~5,2% reale annuo dal 1900, contro il ~6,8% reale dell'S&P 500 nella serie del plugin, 1928-2025); (2) gli obiettivi sono simulati come **indipendenti**, ma condividono lo stesso mercato — la simulazione congiunta mostra che l'indipendenza sottostima il rischio che falliscano tutti nello stesso scenario. Entrambe spostano le conclusioni verso il prudente.
