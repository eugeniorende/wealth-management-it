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

1. calcola le **plus/minus latenti** per ogni posizione (valore di mercato − costo di carico);
2. separa le **minus latenti** (candidate all'harvesting: venderle realizza una minus che ricarica
   lo zainetto) dalle **plus latenti** (venderle genera imposta, salvo compensazione);
3. se gli passi anche un CSV con lo **zainetto** (un secondo file, perché vive nella certificazione,
   non nell'estratto delle posizioni), incrocia le due cose e ti dice **quanta plus puoi realizzare
   a imposta zero** compensandola con le minus disponibili;
4. produce un report leggibile e un **JSON strutturato** che alimenta il workflow di `/minusvalenze`.

Uso:

```
python importa-estratto-broker.py estratto.csv [zainetto.csv]
```

Solo libreria standard, nessuna dipendenza.

## Il parser è tollerante ai formati (deve esserlo)

La difficoltà vera non è leggere *un* formato, è che i tre broker hanno **layout diversi e non
standard**. Per questo il parser non assume colonne fisse: riconosce i nomi-colonna tipici dei
dossier italiani con un dizionario di sinonimi e un matching tollerante (ignora maiuscole, accenti,
spazi, e gestisce sia i numeri all'italiana `1.234,56` sia all'inglese `1,234.56`). Riconosce per
esempio `ISIN`/`Codice ISIN`, `Descrizione`/`Strumento`/`Titolo`, `Quantità`/`Pezzi`,
`Prezzo medio di carico`/`PMC`/`Prezzo di carico`, `Controvalore`/`Valore di mercato`. Se il tuo
export usa nomi che non riconosce, li aggiungi ai dizionari `SINONIMI` in testa allo script — è una
riga. I file `assets/esempio-estratto.csv` ed `esempio-zainetto.csv` mostrano il formato atteso.

## Come esportare da ciascun broker

I percorsi esatti cambiano con gli aggiornamenti delle interfacce, ma in linea di massima:

- **Directa**: dall'area personale o da Darwin puoi esportare la tabella del portafoglio (posizioni
  con carico e controvalore). Lo zainetto e le minus compensabili stanno nella sezione fiscale /
  nella certificazione annuale.
- **Fineco**: la situazione fiscale e lo zainetto sono in *Portafoglio > Fiscalità*; il portafoglio
  e i movimenti sono esportabili dall'area titoli (con il filtro Trading sui movimenti).
- **Trade Republic**: dal 30/1/2025 è sostituto d'imposta in Italia (regime amministrato), quindi lo
  zainetto lo gestisce internamente e fornisce un **report fiscale PDF annuale**. L'estratto delle
  posizioni si ricava dall'app; il report fiscale è il documento di riferimento per i dati per anno.

Quando l'export è in PDF (es. la certificazione, o il report di Trade Republic), per ora va
convertito in CSV a mano — il parsing diretto dei PDF è il passo successivo, non incluso in questo
pilota.

## Limiti dichiarati (onestà del pilota)

- **Legge CSV, non PDF.** Il formato CSV è il più robusto; il PDF della certificazione richiede un
  parser dedicato per ciascun broker ed è rimandato.
- **Lo zainetto è un input separato.** Sta in un documento diverso (la certificazione) rispetto
  all'estratto delle posizioni, quindi è un secondo CSV opzionale, non ricavabile dalle posizioni.
- **La classificazione fiscale è semplificata.** La plus/minus su vendita è reddito diverso
  (compensabile) e il parser la tratta così. La trappola dei proventi degli ETF armonizzati (reddito
  di **capitale**, non compensabile con le minus) è un'altra cosa: vedi `etf-trap-redditi-capitale.md`.
- **Niente credenziali a tool.** Il flusso è volutamente "scarichi tu, dai in pasto il file": nessuna
  password, nessun 2FA, nessun reverse-engineering. È la scelta che tiene insieme robustezza,
  conformità alle condizioni d'uso e sicurezza.

Per la logica fiscale a valle (compensazione, gerarchia delle leve, regime dichiarativo) vedi il
resto della skill; questo modulo si limita a trasformare un estratto grezzo nei numeri che servono.
