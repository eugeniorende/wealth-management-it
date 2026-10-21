# Integrazione fiscale joint: previdenza + ottimizzazione finanziaria

Questa reference è il punto di contatto tra `it-pianificazione` (IRPEF progressiva, regime previdenziale) e `it-tax-optimization` (imposta sostitutiva 26%/12,5%, regime amministrato sui finanziari). Le due fiscalità operano su **regimi distinti** e non si compensano direttamente, ma esistono **decisioni joint** dove coordinarle produce un beneficio fiscale combinato superiore alla somma delle singole.

## Mappa concettuale: due regimi separati, leve coordinabili

```
IRPEF (progressiva)              Imposta sostitutiva (flat 26%/12,5%)
─────────────────────            ──────────────────────────────────
Stipendio                        Plus/minus azioni
Pensione                         Plus/minus certificates, ETC
Affitti (ordinaria)              Plus/minus obbligazioni
Lavoro autonomo                  Cedole, dividendi
Plus ETF non armonizzati         ETF UCITS armonizzati (no compensaz.)
  fuori UE/SEE o senza gestore
  vigilato (no compensaz.)
Deducibili:
  Fondo pensione (€5.300)         (nessuna compensazione cross-regime)
  Contributi obbligatori
  ...
```

**Non c'è cross-compensation**: un realizzo di plus su ETF (26%) non riduce IRPEF, una deduzione del fondo pensione non riduce l'imposta sostitutiva. Ma le due leve **incidono entrambe sul reddito netto disponibile dell'utente** e sono coordinabili nello stesso anno fiscale.

## I quattro pattern joint con valore concreto

### Pattern J1: Allocazione risparmio annuo extra

**Setup**: l'utente ha €X di risparmio annuo extra, deve scegliere dove allocarlo per massimo vantaggio fiscale netto su orizzonte lungo (≥10 anni).

**Opzioni**:
- **A — Fondo pensione complementare** (entro €5.300 deducibili):
  - Deduzione IRPEF immediata = €X × aliquota_marginale
  - Capitalizzazione interna tassata 20% (12,5% titoli Stato)
  - Tassazione finale 9-15% (in base ad anni partecipazione)
- **B — Investimento finanziario su dossier titoli normale** (ETF/azioni):
  - No deduzione IRPEF
  - Tassazione 26% sui gains realizzati (12,5% se titoli Stato whitelist)
  - Liquidità immediata

**Decisione**:

| Aliquota marginale IRPEF utente | Orizzonte | Raccomandazione |
|---|---|---|
| 43% (RAL > €50k) | ≥10 anni | A: fondo, sempre |
| 33% (RAL €28k-€50k) | ≥10 anni | A: fondo, salvo necessità liquidità |
| 33% | <10 anni | B: dossier, perché aliquota finale fondo non scende sotto ~12% |
| 23% (RAL < €28k) | qualsiasi | B: dossier, vantaggio fondo si assottiglia |

**Numeri concreti per quantificazione (RAL €40k, aliquota 33%, orizzonte 22 anni a pensionamento)**:

```
Scenario A — €3.000/anno al fondo pensione (bilanciato, rendimento netto 3,5%)
  Risparmio IRPEF annuo: €3.000 × 33% = €990
  Risparmio IRPEF cumulato: €990 × 22 = €21.780
  Montante a pensione (capitalizzato 22 anni): €98.500
  Aliquota finale fondo: ~12% (27 anni partecipazione)
  Netto finale: €86.700
  TOTALE valore: €86.700 + €21.780 = €108.480 (in nominale)

Scenario B — €3.000/anno su ETF MSCI World UCITS (rendimento lordo 6%)
  Nessuna deduzione IRPEF
  Montante a pensione (capitalizzato): €144.700 lordo
  Tassazione plus 26%: parte realizzata; se mantenuto in accumulazione, tassazione differita
  Quota effettivamente investita (€3.000 al netto IRPEF ~33% sui medesimi soldi extra)
  →In realtà confronto va fatto a parità di "costo opportunità netto"
```

Il calcolo corretto del confronto deve normalizzare per **euro netto disponibile oggi**: il fondo lo riceve "lordo IRPEF", il dossier lo riceve "netto IRPEF". Una cella nel template Excel `proiezione-pensione.xlsx` quantifica già il risparmio IRPEF cumulato dalle deduzioni.

### Pattern J2: Realizzo plus + deduzione fondo per uscire da scaglione

**Setup**: l'utente è in prossimità o appena sopra una soglia di scaglione IRPEF (€28k o €50k), con plusvalenze latenti su finanziari.

**Scenario tipico**: RAL €52.000 (appena sopra €50k → scaglione 43% sull'eccedenza). L'utente sta valutando se:
- Realizzare una plus di €5.000 prima di fine anno
- Versare €2.000 al fondo pensione

**Analisi**:

```
Senza azioni:
  IRPEF su €52k = 28.000×23% + 22.000×33% + 2.000×43% = 14.560
  
Versando €2.000 al fondo:
  Reddito imponibile: €50.000 (esattamente al limite)
  IRPEF: 28.000×23% + 22.000×33% = 13.700
  Risparmio IRPEF: €860 (su €2.000 versati = effettivo 43% marginale)
  Plus su finanziari: realizzata pure → tassa 26% × €5.000 = €1.300 (no impatto IRPEF)

Realizzando solo la plus:
  IRPEF su €52k = €14.560 (invariato, plus non in IRPEF)
  Tassa plus = €1.300
  
Doing entrambe le cose nello stesso anno:
  Risparmio IRPEF: €860
  Tassa plus: €1.300
  Netto guadagnato dall'operazione fiscale: €860 - €0 (la plus la pagavi comunque) = €860 risparmio puro
```

**Insight**: le due decisioni sono **fiscalmente indipendenti** (no double-counting), ma cumulative. Vale la pena fare entrambe nello stesso anno, e il versamento al fondo per uscire dallo scaglione 43% è il pattern a maggior ritorno marginale per redditi tra €50k e €60k.

### Pattern J3: Anno di realizzo plus alti — protezione IRPEF

**Setup**: l'utente realizza plus significative nel corso dell'anno (es. vendita di un portafoglio storico) e ha redditi da lavoro vicini al limite di scaglione.

**Falso allarme**: l'utente potrebbe pensare "le plus aumentano il mio reddito IRPEF, mi spingono nello scaglione superiore". **Non è vero**: le plus su finanziari in regime amministrato sono **escluse dal reddito IRPEF complessivo** (sostitutiva, separata). **Eccezione**: le plus di ETF e fondi non armonizzati fuori UE/SEE o senza gestore vigilato (per esempio ETF domiciliati negli USA) sono reddito di capitale che concorre al reddito complessivo, con ritenuta del 26% a titolo d'acconto e quadro RL anche in amministrato (art. 10-ter cc. 6-7 L. 77/1983, vigente fino al 31/12/2026, dal 2027 art. 59 cc. 9-10 dell'All. 1 al D.Lgs. 33/2025; aliquota del 26% dall'art. 3 c. 1 DL 66/2014): quelle sì possono spingere nello scaglione superiore.

**Eccezione importante**: per chi è in **regime dichiarativo** (no sostituto d'imposta), le plus finanziarie che sono redditi diversi vanno nel quadro RT del Modello Redditi PF con la sostitutiva del 26% e non concorrono all'IRPEF ordinaria. Vi concorrono invece, nel quadro RL, i proventi di ETF e fondi non armonizzati fuori UE/SEE o senza gestore vigilato, sia distribuiti sia da cessione o rimborso (vedi sopra): con un broker estero è il caso tipico degli ETF domiciliati negli USA.

**Conclusione operativa**: l'ottimizzazione finanziaria (it-tax-optimization) e l'ottimizzazione IRPEF (it-pianificazione) sono **disaccoppiate** per le casistiche standard del lavoratore dipendente. Coordinarle non offre vantaggi cross-regime, ma evita errori (es. l'utente che evita di vendere "perché entrerebbe in scaglione superiore" sbaglia).

### Pattern J4: Sterilizzazione redditi alti (>€200k)

**Setup**: Legge di Bilancio 2026 introduce la sterilizzazione del beneficio IRPEF (riduzione aliquota 35→33% sul secondo scaglione) per redditi complessivi > €200.000. Meccanismo: riduzione di €440 sulle detrazioni 19% (escluse spese sanitarie, partiti politici, calamità naturali).

**Definizione di "reddito complessivo"**: include IRPEF imponibile (lavoro, pensione, locazioni ordinarie). **Non include** redditi a sostitutiva (plus finanziari, cedolare secca).

**Implicazione**:
- Un libero professionista o dirigente con RAL €220.000 subisce la sterilizzazione
- Lo stesso soggetto, con €100.000 di plus finanziarie nell'anno, **non viene ulteriormente penalizzato** (sostitutiva resta 26% indipendentemente)
- Anche le pensioni alte (>€200k lordi annui) ricadono nella sterilizzazione

**Decisione joint**: per redditi vicini alla soglia €200k, **massimizzare le deducibilità IRPEF** (fondo pensione fino a €5.300, contributi obbligatori, ecc.) può portare sotto soglia e recuperare il beneficio €440. Il calcolo si fa nell'anno: se reddito stimato = €203k, versare €3.500 al fondo riduce il reddito a €199.500 (under threshold) e si recupera €440 + risparmio IRPEF marginale 43% × €3.500 = €1.505. Beneficio totale operazione = **€1.945**.

## Protocollo di handoff tra le due skill

Quando una conversazione tocca **entrambi** i domini:

1. **Utente parte dalla pianificazione pensionistica** (`it-pianificazione` invocata):
   - Se nella raccolta dati emergono asset finanziari rilevanti → segnala: "Vedo che hai un dossier titoli significativo. Se vuoi, dopo posso applicare anche l'ottimizzazione minus/plus tramite `it-tax-optimization`."
   - Output del report pensionistico include una riga "Risparmio IRPEF cumulato dalle deduzioni" che è il *primo input* per il calcolo dell'aliquota marginale rilevante.

2. **Utente parte dall'ottimizzazione finanziaria** (`it-tax-optimization` invocata):
   - Se RAL alta o redditi totali > €100k → segnala: "Per redditi nel tuo scaglione, la deducibilità del fondo pensione è la singola leva fiscale a maggior impatto. Se vuoi, dopo posso passare a `it-pianificazione`."
   - L'aliquota marginale IRPEF stimata (`Input!aliquota_irpef_marginale` nel template Excel) è il parametro chiave per quantificare il pattern J1.

3. **Anno fiscale di fine periodo (novembre-dicembre)**:
   - Coordinare le due decisioni nello stesso ciclo: prima massimizzare deducibili (fondo, contributi volontari) e comunicare al fondo quelli eccedenti il plafond, poi gestire le minus in scadenza (entro 31/12 del 4° anno).
   - Le due operazioni sono fiscalmente indipendenti ma operativamente da fare prima di Capodanno.

## Anti-pattern (NON FARE)

- ❌ Trattare la deduzione fondo pensione come "compensazione" delle plus finanziarie. Sono regimi separati.
- ❌ Evitare di realizzare plus per "non salire di scaglione IRPEF". In regime amministrato la plus è separata.
- ❌ Considerare i redditi finanziari nel calcolo della soglia €200k di sterilizzazione. Non concorrono.
- ❌ Versare al fondo pensione una somma > aliquota_marginale × beneficio_atteso per "saturare il deducibile" — il vantaggio è proporzionale all'aliquota marginale, oltre soglia non c'è più beneficio fiscale.
- ❌ Coordinare le due skill su un cliente con cassa professionale (Inarcassa, Cassa Forense): le regole IRPEF interagiscono diversamente con i contributi obbligatori della cassa. v0.3 non lo copre.

## Heuristic operative per la skill

1. **Sempre stimare l'aliquota marginale IRPEF prima di raccomandare**: una raccomandazione "versa al fondo pensione" senza l'aliquota marginale è incompleta.
2. **Mai cumulare i risparmi cross-regime nel "beneficio totale"** se non chiaramente etichettati (`risparmio IRPEF su fondo` vs `imposta su plus realizzate` sono linee separate).
3. **Per redditi vicini a soglia di scaglione**, calcolare il "ritorno marginale" del versamento al fondo: il primo €1 deduce all'aliquota più alta, ma man mano che la deduzione fa scendere lo scaglione, il ritorno scende. Esempio: chi guadagna €30k versare €2.000 deduce primi €2.000 al 33%; chi guadagna €52k versare €2.000 deduce primi €2.000 al 43% — quindi più conviene.
4. **Documentare l'anno fiscale di riferimento**: queste regole sono per il 2026 (Legge di Bilancio L. 199/2025). Saranno potenzialmente diverse dal 2027 in poi.
