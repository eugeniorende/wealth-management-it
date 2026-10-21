# Importare i dati fiscali dai broker

Questa skill lavora meglio sui dati reali del tuo portafoglio. Il modo per portarceli **non** è
un collegamento "live" via API ai broker — quella strada è stata valutata e scartata, per ragioni
che vale la pena ricordare perché spiegano il design di ciò che c'è qui.

## Perché non un MCP "live" sui broker

Tre broker italiani diffusi — Directa, Fineco, Trade Republic — sono stati verificati uno per uno:

- **Directa** ha un'API ufficiale (la dAPI di Darwin, socket su `localhost`, con wrapper Python e
  repo GitHub ufficiali). Ma espone posizioni, ordini e un P/L *aggregato*, non lo zainetto fiscale;
  e richiede che la piattaforma Darwin (app Java desktop) sia aperta e loggata in locale, perché
  l'API è un ponte socket, non un endpoint cloud.
- **Fineco** non ha API ufficiali retail. C'è solo Xcell DDE per i prezzi in Excel e l'Open Banking
  PSD2, che però copre il conto corrente, non il dossier titoli.
- **Trade Republic** non ha API ufficiali: è una piattaforma mobile chiusa. L'unico accesso
  programmatico sarebbe il reverse-engineering dell'API privata dell'app, che viola le condizioni
  d'uso ed è fragile.

Il punto che decide la questione: anche dove l'API c'è (Directa), **non dà il dato che alla skill
serve davvero**. L'ottimizzazione fiscale non ha bisogno delle posizioni live — quelle le conosci.
Ha bisogno dello **zainetto** (le minus compensabili per anno di scadenza e aliquota) e delle
plus/minus realizzate. Quello è un calcolo fiscale che ogni broker, come sostituto d'imposta, fa e
mette solo nella sua **sezione "Fiscalità" o nella certificazione** — documenti esportabili, non API.

Aggiungi il rovescio della medaglia di un collegamento live: dare a un tool le **credenziali del
conto e il 2FA**, che è esattamente ciò che non si deve mai fare. La conclusione è che il dato giusto
si prende da un **report che scarichi tu**, senza credenziali in giro.

## Cosa fa l'importatore

`assets/importa-estratto-broker.py` ingerisce un **estratto del portafoglio in CSV** che esporti dal
broker, e:

1. calcola le **plus/minus latenti** per ogni posizione (valore di mercato − costo di carico, cioè il
   PMC del broker, che in amministrato è la base fiscale);
2. assegna a ogni posizione la **categoria fiscale**: dalla colonna «tipo fiscale» se c'è, altrimenti
   dalla descrizione (vedi sotto). Le plus di ETF e fondi mobiliari sono reddito di capitale e non
   entrano tra le compensabili; quelle degli OICR fuori UE/SEE sono segnalate come IRPEF (quadro RL);
3. deduce l'**aliquota**, salvo una colonna «aliquota» nel file. Il 12,5% spetta ai titoli di Stato
   italiani e agli equiparati (enti territoriali, organismi internazionali come BEI e BIRS) e alle
   obbligazioni degli Stati della white list e dei loro enti territoriali (art. 6 c. 1 D.Lgs. 461/97
   → art. 306 c. 1 TU 2027; vedi `aliquote-12-5-26.md`). Lo script lo riconosce dalla descrizione per
   BTP, BOT, CCT, CTZ ed enti territoriali italiani (con ISIN IT o senza ISIN), per Bund, OAT, Bonos,
   Treasury, Gilt e JGB e per BEI, BERS, BIRS e le altre banche multilaterali. Le altre obbligazioni
   con ISIN estero restano al 26% **con un avviso**: se sono di uno Stato white list, di un suo ente
   territoriale (per esempio un Land tedesco) o di un organismo internazionale, l'aliquota va
   indicata nella colonna;
4. se gli passi anche un CSV con lo **zainetto** (un secondo file, perché vive nella certificazione),
   calcola la **scadenza** di ogni minus (31/12 del quarto anno successivo), esclude quelle scadute
   rispetto a `--anno`, converte il 12,5% in «26%-equivalente» nei due versi e ti dice **quanta plus
   compensabile puoi realizzare a imposta zero**, broker per broker se i file hanno la colonna
   `broker` (lo zainetto non si compensa tra intermediari);
5. stampa un report leggibile e, con `--json`, scrive il **JSON completo** (posizioni, zainetto con
   scadenze, analisi per broker, avvisi) che il workflow di `/minusvalenze` può rileggere.

Uso:

```
python importa-estratto-broker.py estratto.csv [zainetto.csv] [--anno 2026] [--broker Fineco] [--json risultato.json]
```

`--json -` stampa solo il JSON su stdout. Gli errori sui file (mancanti, vuoti, colonne non
riconosciute, aliquote ignote) escono con un messaggio leggibile e codice 2. Solo libreria standard.

### Come classifica senza la colonna «tipo fiscale»

La categoria si deduce dalla **descrizione**, non dal prefisso dell'ISIN: DE, FR, IE e LU coprono anche
azioni singole come SAP o LVMH, ed ETC ed ETN con ISIN IE o JE non sono fondi. Le regole, nell'ordine:
- ETC, ETN, ETP e certificate → reddito diverso.
- «ETF», «UCITS», «fondo», «fund(s)» o «SICAV» → OICR: reddito di capitale se l'ISIN è di un Paese
  UE/SEE, `reddito_capitale_irpef` se è di un altro Paese (per esempio un ETF domiciliato negli USA),
  da classificare se la descrizione dice «non armonizzato» (dipende dal gestore) o se è un fondo
  immobiliare (plus e minus seguono regole proprie, art. 7 DL 351/2001).
- «Physical» o «fisico» senza la parola ETF (per esempio «WisdomTree Physical Gold», «iShares Physical
  Gold») → ETC fisico, reddito diverso.
- Il solo nome di un emittente (iShares, Vanguard, Xtrackers, Amundi, Lyxor, SPDR, Invesco, VanEck,
  WisdomTree) non basta, perché gli stessi emittenti fanno anche ETC, e alcuni hanno azioni quotate:
  con un indice nella descrizione (MSCI, FTSE, S&P, STOXX…) e ISIN UE/SEE è un ETF, reddito di capitale;
  altrimenti resta **da classificare**. Dal solo nome non si deduce mai la tassazione IRPEF.
- Azioni riconoscibili dalla forma societaria (SpA, SE, AG, SA, NV, PLC, Inc) → reddito diverso, ma non
  se la descrizione contiene un indice: «… High Dividend Yield Inc» è la classe a distribuzione di un
  ETF, e resta da classificare.
- Obbligazioni e titoli di Stato → reddito diverso, al netto di ratei e scarto di emissione maturati.
  BOT, CTZ, BTF, T-Bill e zero coupon restano **da classificare**: la loro plus latente è in gran parte
  scarto di emissione, cioè reddito di capitale.
- Nessun indizio → **da classificare**: la plus non viene contata tra le compensabili e il report
  chiede di indicarne la categoria. Non si assume mai «reddito diverso».

Valori accettati nella colonna «tipo fiscale»: `reddito_diverso`, `reddito_capitale`,
`reddito_capitale_irpef`, `da_classificare` (o le forme brevi «diverso», «capitale»; «Redditi diversi
(capital gain)» è reddito diverso). Un valore non riconosciuto è segnalato negli avvisi e vale la
categoria dedotta dalla descrizione. La colonna si chiama «tipo fiscale», «categoria fiscale» o
«natura fiscale»: una «Natura strumento» (azione, ETF) non è letta come categoria fiscale.

## Il parser è tollerante ai formati (deve esserlo)

La difficoltà vera non è leggere *un* formato, è che i tre broker hanno **layout diversi e non
standard**. Per questo il parser non assume colonne fisse: riconosce i nomi-colonna tipici dei
dossier italiani con un dizionario di sinonimi e un matching tollerante (ignora maiuscole, accenti,
spazi, e gestisce sia i numeri all'italiana `1.234,56` sia all'inglese `1,234.56`). Il formato si
decide **per file**: se in una colonna numerica compare una virgola decimale (`12,40`), il file è
all'italiana e `1.000` o `1.234.567` sono migliaia. Se il file non dà indizi (nessun decimale) o dà
indizi in conflitto, decide il delimitatore: con `;` il file è all'italiana, con `,` all'inglese
(`"1,000"` vale mille); in ogni caso il report elenca le celle il cui valore dipende dal formato.
Le righe senza costo o valore leggibili sono scartate con un avviso, mai in silenzio. Riconosce per esempio `ISIN`/`Codice ISIN`, `Descrizione`/`Strumento`/`Titolo`, `Quantità`/`Pezzi`,
`Prezzo medio di carico`/`PMC`/`Prezzo di carico`, `Controvalore`/`Valore di mercato`. Se il tuo
export usa nomi che non riconosce, li aggiungi ai dizionari `SINONIMI` in testa allo script — è una
riga. I file `assets/esempio-estratto.csv` ed `esempio-zainetto.csv` mostrano il formato atteso: sugli
esempi le uniche plus sono di un ETF, quindi l'importatore risponde «€ 0 a imposta zero».
Lo zainetto accetta le colonne anno di **realizzo** (non di scadenza), importo residuo, aliquota e,
se serve, broker. Le varianti della certificazione sono gestite con un avviso:
- solo l'anno di scadenza («Anno di scadenza», «Utilizzabile fino al»): l'anno di realizzo è la
  scadenza meno 4;
- la minus lorda accanto al residuo («Minusvalenza» e «Residuo»): vale il residuo;
- la minus lorda e l'utilizzato, senza residuo: residuo = lorda − utilizzato.

Le righe senza anno sono escluse (scadenza ignota); un'aliquota vuota, «-» o «n.d.» vale 26% con un
avviso, mentre un numero diverso da 26 e 12,5 ferma l'import con il nome del file e la riga.

## Come esportare da ciascun broker

I percorsi esatti cambiano con gli aggiornamenti delle interfacce, ma in linea di massima:

- **Directa**: dall'area personale o da Darwin puoi esportare la tabella del portafoglio (posizioni
  con carico e controvalore). Lo zainetto e le minus compensabili stanno nella sezione fiscale /
  nella certificazione annuale.
- **Fineco**: la situazione fiscale e lo zainetto sono in *Portafoglio > Fiscalità*; il portafoglio
  e i movimenti sono esportabili dall'area titoli (con il filtro Trading sui movimenti).
- **Trade Republic**: dal 30/1/2025, con la succursale italiana, fa da sostituto d'imposta (regime
  amministrato) per i nuovi clienti; chi ha aperto il conto prima verifichi nell'app il regime attivo.
  In amministrato lo zainetto lo gestisce il broker, che fornisce un **report fiscale PDF annuale**.
  L'estratto delle posizioni si ricava dall'app; il report fiscale è il documento di riferimento per
  i dati per anno. Le cripto detenute su Trade Republic restano da dichiarare.
- **Scalable Capital**: dal 1/9/2026, con la succursale di Milano, il regime amministrato si attiva su
  richiesta; vale dall'attivazione e i periodi precedenti restano da dichiarare.
- **Interactive Brokers e Degiro**: nessun sostituto d'imposta italiano, quindi regime dichiarativo.
  L'importatore non li copre per scelta di perimetro (il motore resta sull'amministrato): i loro report
  servono per i quadri RT, RM e RW del dichiarativo, con il LIFO e i cambi del giorno, non per lo zainetto. Vedi
  `regime-dichiarativo.md`, con lo stato dei broker a ottobre 2026.

Quando l'export è in PDF (es. la certificazione, o il report di Trade Republic), per ora va
convertito in CSV a mano — il parsing diretto dei PDF è il passo successivo, non incluso in questo
pilota.

## Limiti dichiarati (onestà del pilota)

- **Legge CSV, non PDF.** Il formato CSV è il più robusto; il PDF della certificazione richiede un
  parser dedicato per ciascun broker ed è rimandato.
- **Lo zainetto è un input separato.** Sta in un documento diverso (la certificazione) rispetto
  all'estratto delle posizioni, quindi è un secondo CSV opzionale, non ricavabile dalle posizioni.
- **La classificazione dalla descrizione è un'euristica.** La plus da vendita di ETF e fondi mobiliari
  è reddito di **capitale** e non compensa lo zainetto (art. 44 c. 1 lett. g TUIR; circ. AdE 21/E/2014); solo
  la minus è reddito diverso (vedi `etf-trap-redditi-capitale.md`). Lo script lo applica, ma
  riconosce gli strumenti dalla descrizione: quando sbaglia o non sa, la colonna «tipo fiscale»
  nel CSV ha la precedenza, e le posizioni senza indizi restano da classificare.
- **Scarto di emissione e ratei non sono scorporati.** La plus latente di un'obbligazione include lo
  scarto maturato: per i BTP emessi vicino alla pari conta poco, per BOT, CTZ e zero coupon è quasi
  tutto (per questo restano da classificare). Vedi l'Esempio D di `aliquote-12-5-26.md`.
- **Obbligazioni a nominale.** Se l'export dà il nominale e il prezzo in percentuale senza il valore
  di carico, il costo calcolato come quantità × prezzo è sbagliato di un fattore 100: serve la
  colonna del valore di carico.
- **Solo amministrato.** Per i conti in dichiarativo (broker esteri) i numeri non valgono: lì si
  applicano il LIFO e il cambio del giorno, che lo script non calcola (vedi `regime-dichiarativo.md`).
- **Niente credenziali a tool.** Il flusso è volutamente "scarichi tu, dai in pasto il file": nessuna
  password, nessun 2FA, nessun reverse-engineering. È la scelta che tiene insieme robustezza,
  conformità alle condizioni d'uso e sicurezza.

Per la logica fiscale a valle (compensazione, gerarchia delle leve, regime dichiarativo) vedi il
resto della skill; questo modulo si limita a trasformare un estratto grezzo nei numeri che servono.

---
*Categorie fiscali applicate dall'importatore (artt. 44 c. 1 lett. g e 67 TUIR, art. 10-ter L. 77/1983, Circ. AdE 21/E/2014), scadenza e certificazione delle minus (art. 6 c. 5 D.Lgs. 461/97), coefficiente 48,08% (art. 6 c. 1 D.Lgs. 461/97) — Verificato: 2026-10.*
*Stato dei broker a ottobre 2026: comunicato stampa di Trade Republic del 30/1/2025 e help center di Scalable Capital; per Interactive Brokers e Degiro fonti di settore, da riverificare sul sito del broker.*
