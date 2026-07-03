# Monte Carlo della pensione: perché i due pilastri vanno trattati diversamente

La proiezione del foglio Excel è **deterministica**: scelto un rendimento per il fondo pensione,
restituisce un montante e un tasso di sostituzione precisi. È utile per ragionare, ma nasconde una
cosa: quel rendimento non è noto. Lo script `assets/montecarlo-pensione.py` aggiunge la dimensione
mancante — la **distribuzione** degli esiti, non un numero solo.

## Il punto: i due pilastri non hanno lo stesso rischio

È qui che un Monte Carlo fatto male inganna, e dove invece sta il valore di farlo bene. La pensione
di un dipendente ha due pilastri con nature di rischio **opposte**:

- La pensione **pubblica** (INPS contributivo) cresce per *rivalutazione*: il montante contributivo
  è rivalutato ogni anno alla media quinquennale del PIL nominale, e poi convertito in rendita col
  coefficiente di trasformazione. Non c'è un mercato di mezzo. La sua incertezza è **macro** (quanto
  crescerà il PIL) e **normativa** (come scenderà il coefficiente), non finanziaria. Applicarle la
  volatilità dei mercati azionari sarebbe un errore concettuale: simulerebbe un rischio che quel
  pilastro non ha.

- La pensione **complementare** (fondo pensione) è investita in un comparto. Il suo montante dipende
  dai **rendimenti di mercato** lungo gli anni di accumulo. Qui la volatilità c'è davvero, ed è
  esattamente ciò che un Monte Carlo serve a catturare.

Per questo lo script tiene l'INPS come **àncora deterministica** (il valore lordo annuo che hai già
stimato nel foglio) e fa girare il Monte Carlo **solo** sul fondo pensione. Non è una
semplificazione per pigrizia: è il modo corretto di rappresentare due rischi diversi.

## La conseguenza onesta

Siccome solo un pilastro è stocastico, **tutta la dispersione del tasso di sostituzione viene dal
complementare**, e il pubblico la àncora. È un risultato che vale la pena vedere a occhio: tipicamente
il pilastro pubblico fissa il tasso di sostituzione a una base solida, e il fondo pensione ci aggiunge
una *banda* di mercato sopra. Quanto è larga quella banda dipende dal comparto scelto — ed è proprio
lì che la decisione (quanto azionario nel fondo pensione, per quanti anni) sposta gli esiti. Lo
script stampa la decomposizione esplicitamente: la parte fissa pubblica e la banda P10–P90 aggiunta
dal complementare.

Questo ridimensiona anche l'ansia da volatilità: se il complementare è una quota minoritaria del
reddito pensionistico totale, anche un comparto azionario movimenta il tasso di sostituzione finale
meno di quanto si tema, perché la base pubblica non si muove. Se invece il complementare pesa molto
(autonomi, o chi ha versato a lungo e tanto), la banda si allarga e la scelta del comparto diventa
decisiva — coerentemente con `it-pianificazione-autonomi`, dove la pubblica è più magra e la
complementare conta di più.

## Il motore è quello di obiettivi

Sotto il cofano è lo stesso **block bootstrap** di `it-pianificazione-obiettivi/montecarlo-obiettivi.py`,
sulla stessa serie storica Damodaran (S&P 500 + Treasury decennale, 1928–2025): ricampiona blocchi di
anni *consecutivi*, così le code grasse, le correlazioni e la mean reversion sono quelle reali e non
quelle lisce di una Normale. La media storica viene **ricentrata** sul rendimento atteso del comparto
che imposti tu: si calibra il *livello* sull'ipotesi (idealmente non USA-centrica), si mantiene la
*forma* reale. La mediana del montante simulato sta sotto il valore deterministico calcolato col
rendimento medio: è il **volatility drag**, ed è giusto che ci sia.

## Cosa resta fuori (e perché)

Il Monte Carlo isola il rischio di **mercato** sul fondo pensione. Restano deliberatamente fuori:

- la **discesa del coefficiente di trasformazione** (demografica/normativa): è già modellata nel
  foglio come coefficiente proiettato all'anno di pensionamento, e va esplorata come *scenario*, non
  come volatilità;
- la **rivalutazione PIL** dell'INPS: incertezza macro, anch'essa da scenario;
- la **crescita salariale** futura, che muove sia i contributi sia la RAL finale (denominatore del
  tasso di sostituzione).

Metterle dentro come "volatilità" darebbe una falsa precisione su grandezze che non sono rischio di
mercato. La via onesta è: Monte Carlo per ciò che è mercato (il comparto del fondo pensione), scenari
deterministici nel foglio per ciò che è macro o normativo. Tutti i valori vanno espressi in modo
coerente, preferibilmente in euro di oggi (potere d'acquisto), così il tasso di sostituzione è reale
e confrontabile.
