# Previdenza obbligatoria INPS (lavoratore dipendente privato)

## Il sistema contributivo

Per i lavoratori senza contribuzione al 31/12/1995 (Legge Dini 335/1995), il sistema è interamente **contributivo**: la pensione si calcola in base ai contributi effettivamente versati, rivalutati, e trasformati in rendita all'età di pensionamento.

Per chi ha contributi prima del 31/12/1995:
- **>18 anni di contribuzione al 31/12/1995**: sistema misto, con quota retributiva (più favorevole) fino al 2011 e contributiva dal 2012 in poi (riforma Fornero)
- **<18 anni di contribuzione al 31/12/1995**: contributivo pro-rata dal 1° gennaio 1996

Per chi ha iniziato a lavorare dopo il 1995 il sistema è interamente **contributivo**.

## Formula di calcolo (contributivo puro)

```
Step 1: Contributo annuo accreditato
  contributo_anno = retribuzione_annua × aliquota_di_computo
  aliquota_di_computo (lavoratore dipendente) = 33%

Step 2: Rivalutazione montante
  Al 31 dicembre di ogni anno il montante accumulato fino all'anno prima
  si rivaluta con la media quinquennale del PIL nominale (mai sotto 1);
  il contributo dell'anno entra senza rivalutazione (L. 335/1995 art. 1 c. 8-9)

  montante(t) = montante(t-1) × (1 + tasso_PIL(t)) + contributo_anno(t)

  Tasso nominale: media ~2,8% annuo nel 1996-2025 e ~1,8% annuo nel 2006-2025
  (da 0% a 6,2% nei singoli anni). Nel 2014 e nel 2021 il coefficiente è stato 1,
  cioè rivalutazione nulla: l'ISTAT dava −0,19% e −0,02%, portati a 1 dal
  DL 65/2015. In euro di oggi conta il PIL REALE, cioè il nominale meno
  l'inflazione: ~0,5% annuo

Step 3: Pensione lorda annua
  pensione_lorda = montante_finale × coefficiente_trasformazione(età)
```

## Aliquote contributive lavoro dipendente privato 2026

- **Aliquota di computo (totale)**: 33% (FPLD - Fondo Pensioni Lavoratori Dipendenti)
- **A carico lavoratore**: 9,19% sulla retribuzione lorda; sulla parte oltre la prima fascia di retribuzione pensionabile (€56.224 nel 2026) si aggiunge l'1%, quindi 10,19%
- **A carico azienda**: 23,81%
- **Tetto contributivo annuo 2026**: €122.295 (Circ. INPS 6/2026; era €120.607 nel 2025). Oltre questa soglia, per chi è interamente contributivo post-1995, **non si versa più contributo obbligatorio** sulla parte eccedente — e quindi non matura ulteriore montante. Il foglio Pubblica dell'Excel e `proiezione-inps.py` lo applicano

Implicazione importante per RAL alti: per chi guadagna oltre il tetto, la pensione INPS smette di crescere col reddito. Diventa critico massimizzare la complementare per la parte sopra il tetto.

## Coefficienti di trasformazione 2025-2026 — Tabella ufficiale DM 20/11/2024

Tabella completa dal Decreto direttoriale del Ministero del Lavoro del 20 novembre 2024, pubblicato in GU n. 35 del 12 febbraio 2025. Aggiorna la Tabella A dell'Allegato 2 della Legge 247/2007 e la Tabella A della Legge 335/1995. Valido per pensioni con decorrenza dal **1° gennaio 2025 al 31 dicembre 2026**.

| Età | Divisore | Coefficiente |
|---|---|---|
| 57 | 23,789 | **4,204%** |
| 58 | 23,213 | **4,308%** |
| 59 | 22,631 | **4,419%** |
| 60 | 22,044 | **4,536%** |
| 61 | 21,453 | **4,661%** |
| 62 | 20,857 | **4,795%** |
| 63 | 20,258 | **4,936%** |
| 64 | 19,656 | **5,088%** |
| 65 | 19,049 | **5,250%** |
| 66 | 18,441 | **5,423%** |
| 67 | 17,831 | **5,608%** |
| 68 | 17,218 | **5,808%** |
| 69 | 16,600 | **6,024%** |
| 70 | 15,980 | **6,258%** |
| 71 | 15,360 | **6,510%** |

**Tasso di sconto utilizzato dal decreto**: 1,5%

Per i trattamenti liquidati a soggetti di età < 57 anni (assegno invalidità, pensione superstiti) si applica comunque il coefficiente dei 57 anni.

### Confronto biennio 2023-2024 vs 2025-2026

| Età | 2023-2024 | 2025-2026 | Variazione |
|---|---|---|---|
| 57 | 4,270% | 4,204% | -1,55% |
| 64 | 5,184% | 5,088% | -1,85% |
| 67 | 5,723% | 5,608% | -2,01% |
| 70 | 6,395% | 6,258% | -2,14% |
| 71 | n/d | 6,510% | esteso |

Trend: tutti negativi (mediamente -1,55% a -2,18%), per via dell'aumento speranza di vita ISTAT. Il prossimo aggiornamento sarà per il biennio 2027-2028 (decreto atteso entro novembre 2026).

### Calcolo per età non intera (interpolazione mensile)

La normativa prevede che il coefficiente sia incrementato di tanti 1/12 della differenza tra coefficiente dell'età immediatamente superiore e quello dell'età inferiore, per ogni mese intero trascorso dalla data di compimento dell'età alla decorrenza pensione.

**Formula**:

```
coefficiente(anni_y, mesi_m) = coefficiente(y) + (m/12) × (coefficiente(y+1) - coefficiente(y))
```

**Esempio worked**: pensionamento a 67 anni e 7 mesi.

```
coefficiente(67) = 5,608%
coefficiente(68) = 5,808%
delta = 5,808% - 5,608% = 0,200%
coefficiente(67y 7m) = 5,608% + (7/12) × 0,200%
                     = 5,608% + 0,1167%
                     = 5,7247%
```

Per un montante di €300.000:
- A 67 anni esatti: €300.000 × 5,608% = €16.824 lordi annui
- A 67 anni e 7 mesi: €300.000 × 5,7247% = €17.174 lordi annui (+€350/anno)
- A 68 anni esatti: €300.000 × 5,808% = €17.424 lordi annui (+€600/anno)

Quindi anche posticipare di pochi mesi ha un impatto numerico tangibile sull'assegno.

### Heuristic per la skill

1. **Usare la tabella ufficiale per età intere** sopra. Mai inventare o stimare.
2. **Per età non intere applicare l'interpolazione mensile** con la formula sopra.
3. **Disclaimer**: i coefficienti tabulati si applicano solo a pensioni con decorrenza nel biennio 2025-2026. Per chi va in pensione successivamente, applicare i valori del biennio appropriato (aggiornamento atteso novembre 2026 per il biennio 2027-2028, novembre 2028 per 2029-2030, ecc.).
4. **Proiezione del coefficiente per pensionamenti futuri (NON opzionale)**: i coefficienti calano strutturalmente. Per chi va in pensione tra molti anni, usare quello attuale **sovrastima** gravemente la pensione. Applicare la proiezione:

   ```
   bienni_mancanti = anni_residui / 2
   coefficiente_proiettato = coefficiente_attuale(età_target) × (1 − decadimento_biennale)^bienni_mancanti
   ```

   Tasso di decadimento storico: **~1,8% per biennio** (range osservato 1,5-2,2%). Esempio: pensione a 67 anni tra 30 anni (15 bienni):
   ```
   coefficiente_proiettato = 5,608% × (1 − 0,018)^15 = 5,608% × 0,7615 = 4,271%
   ```
   Su un montante di €786k, questo significa €33.576 di pensione lorda invece di €44.100 (sovrastima del 31% se si usasse il coefficiente attuale). Il template Excel della skill calcola automaticamente il coefficiente proiettato; il tasso di decadimento è un parametro editabile (mettere 0 solo per lo scenario "coefficiente congelato", da etichettare come irrealistico).
5. **Verifica sempre con INPS**: per chi è prossimo al pensionamento, rinviare a verifica diretta sul portale INPS (www.inps.it, area riservata con SPID, CIE o CNS: "Estratto conto contributivo" e simulatore "La mia pensione futura") o patronato. La proiezione serve per chi è lontano dal pensionamento; chi è vicino usa il coefficiente reale del proprio biennio.

## Requisiti di accesso pensione 2026

### Pensione di vecchiaia

- **Età anagrafica**: 67 anni nel 2026; 67 anni e 1 mese nel 2027, 67 anni e 3 mesi dal 2028 (adeguamento alla speranza di vita, Circ. INPS 28/2026)
- **Anzianità contributiva**: 20 anni
- **Importo soglia** (solo contributivi puri): pensione spettante ≥ 1 volta l'assegno sociale dal 2024 (L. 213/2023 c. 125; Circ. INPS 46/2024), cioè €546,24 al mese nel 2026

Se l'importo soglia non è raggiunto a 67 anni, si può comunque andare in pensione a 71 anni (71 anni e 1 mese nel 2027, 71 anni e 3 mesi dal 2028) con almeno 5 anni di contributi effettivi.

### Pensione anticipata ordinaria

Requisiti contributivi puri (a prescindere dall'età):
- **Uomini**: 42 anni e 10 mesi di contributi (con finestra mobile 3 mesi)
- **Donne**: 41 anni e 10 mesi di contributi (finestra 3 mesi)

Nel 2027: 42 anni e 11 mesi per gli uomini, 41 anni e 11 mesi per le donne; dal 2028: 43 anni e 1 mese e 42 anni e 1 mese (Circ. INPS 28/2026, All. 2).

### Pensione anticipata contributiva (solo contributivi puri)

- **Età**: 64 anni nel 2026 (63 per legge più gli adeguamenti alla speranza di vita); 64 anni e 1 mese nel 2027, 64 anni e 3 mesi dal 2028
- **Contributi**: almeno 20 anni di contribuzione effettiva (20 anni e 1 mese nel 2027, 20 anni e 3 mesi dal 2028)
- **Importo soglia**: pensione ≥ 3 volte l'assegno sociale (€1.638,72 al mese nel 2026); 2,8 volte per le donne con un figlio, 2,6 volte con due o più. Dal 2030 il 3 diventa 3,2
- **Tetto**: fino ai 67 anni l'assegno non supera 5 volte il trattamento minimo (€611,85 nel 2026, valore provvisorio); finestra di 3 mesi
- Fonte: art. 24 c. 11 DL 201/2011. La computabilità della rendita del fondo pensione per raggiungere la soglia, introdotta dalla L. 207/2024, è stata abrogata dalla L. 199/2025 (Circ. INPS 19/2026)

### Misure sperimentali / Quota X

Stato nel 2026:

- **Quota 103**: non prorogata per il 2026; resta solo per chi ha maturato i requisiti (62 anni + 41 di contributi) entro il 31/12/2025, con calcolo interamente contributivo (Circ. INPS 19/2026)
- **Opzione donna**: non prorogata; resta solo per chi ha maturato i requisiti entro il 31/12/2024, con calcolo contributivo (Circ. INPS 19/2026)
- **APE Sociale**: 63 anni e 5 mesi + 30 contributi (lavoratori in difficoltà specifiche), prorogata al 31/12/2026 dalla Legge di Bilancio 2026
- **Lavoratori precoci / Quota 41**: 41 anni di contributi (di cui almeno 1 prima dei 19 anni di età) per categorie tutelate; 41 anni e 1 mese nel 2027 e 41 anni e 3 mesi dal 2028, tranne chi svolge attività gravose, che resta a 41 anni (Circ. INPS 28/2026)

Tutti questi richiedono ricostruzione della posizione contributiva con patronato/INPS.

## Tassazione assegno pensionistico

L'assegno è soggetto a:

### IRPEF (2026)

Scaglioni standard: 23% / 33% / 43%. La pensione concorre a formare il reddito complessivo.

### Detrazioni pensionati 2026

- No tax area: €8.500 (parificata ai lavoratori dipendenti dal 2024)
- Detrazione (art. 13 c. 3 TUIR, dal 2027 art. 13 c. 3 D.Lgs. 117/2026; R = reddito complessivo):
  - €1.955 fino a €8.500;
  - 700 + 1.255 × (28.000 − R) / 19.500 tra €8.500 e €28.000;
  - 700 × (50.000 − R) / 22.000 tra €28.000 e €50.000;
  - zero oltre €50.000;
  - +€50 se R è tra €25.000 e €29.000 (c. 3-bis).

Rispetto ai lavoratori dipendenti la detrazione dei pensionati scende più in fretta e si azzera a €50.000. È la formula di `assets/netto-pensione.py` e del foglio Pubblica dell'Excel.

### Addizionali

- **Regionale**: 0,70% - 3,33% (varia per regione e per scaglione)
- **Comunale**: 0% - 0,90% (varia per comune)

### Esempio numerico (pensione lorda annua €16.824 a 67 anni, residenza tipica)

```
Pensione lorda annua: €16.824
IRPEF lorda (tutto nel primo scaglione 23%): €3.870
Meno detrazione pensionati: 700 + 1.255 × (28.000 − 16.824) / 19.500 = €1.419
IRPEF netta: €2.450
Addizionali (~2%): €336
Pensione netta annua: €16.824 - €2.450 - €336 = €14.038
Pensione netta mensile (su 13 mensilità): €1.080
```

Nota: la pensione INPS si percepisce in **13 mensilità** (tredicesima a dicembre). Il calcolo mensile diviso per 13 dà la mensilità.

## Tasso di sostituzione tipico (sistema contributivo puro)

Per un dipendente privato medio, carriera regolare a tempo indeterminato, pensione a 67 anni:

- **Tasso di sostituzione lordo** (pensione lorda / ultima RAL lorda): tipicamente **55-65%**
- **Tasso di sostituzione netto** (pensione netta / ultima RAL netta): tipicamente **70-80%** (per via delle detrazioni pensionati e dell'assenza di contributi previdenziali a carico)

⚠️ Questi sono medie. Casi con carriere discontinue, partiti tardi, periodi all'estero, scendono significativamente sotto (40-50% lordo non è raro). Casi con RAL alte oltre il tetto INPS hanno tassi di sostituzione molto bassi sulla parte eccedente.

Per generazioni che andranno in pensione tra 25-35 anni, ci si attendono tassi di sostituzione lordi attorno al **50-60%** per via:
- Calo dei coefficienti di trasformazione (speranza di vita in aumento)
- Eventuale modifica struttura sistema (riforme periodiche)
- Bassa crescita del PIL nominale (che governa la rivalutazione del montante)

Per questa ragione la **complementare diventa strutturalmente necessaria**, non opzionale, per mantenere il tenore di vita post-pensionamento.

## Heuristic per la skill

1. **Età corrente vs età target**: chiedere sempre, non assumere 67. Molti mirano a 64 con l'anticipata contributiva (20 anni di contributi e pensione ≥ 3 volte l'assegno sociale); molti vogliono valutare l'opzione di lavorare fino a 70.

2. **Anzianità INPS corrente**: l'utente la trova nell'estratto conto INPS (www.inps.it, area riservata con SPID, CIE o CNS → "Estratto conto contributivo"). Se non disponibile, stimare da `eta_inizio_lavoro` ma flaggare l'approssimazione.

2-bis. **Montante contributivo già maturato**: è il dato che più pesa sul risultato, e il più incerto se stimato (dipende dall'intera carriera passata, che non conosciamo). Va **chiesto all'utente il valore reale**: lo trova sul sito INPS in "La mia pensione futura" o nell'estratto conto contributivo (il montante rivalutato a oggi). Se non disponibile, lo si **stima** dalla RAL attuale e dall'anzianità, ma la stima va dichiarata tale. La stima migliore non è la grezza `anzianità × RAL × 33%` (che assume RAL costante e nessuna rivalutazione dei contributi passati): è la somma anno per anno `Σ(k=1..anzianità) min(RAL/(1+g)^k, massimale) × 33% × (1+rivalutazione)^(k−1)`, con k = anni fa. Tiene conto della retribuzione passata più bassa, del massimale (costante in euro di oggi, perché si rivaluta sui prezzi: L. 335/1995 art. 2 c. 18) e della rivalutazione dei versamenti già fatti; il contributo dell'anno scorso non è ancora rivalutato. Quando rivalutazione ≈ crescita salariale le due distorsioni si compensano e ci si avvicina alla grezza; quando differiscono, la stima migliorata corregge nella direzione giusta. Il template Excel lo fa: se la cella "Montante INPS da estratto conto" è valorizzata usa quella, altrimenti applica la stima migliorata.

3. **Coefficienti aggiornati**: usare i valori 2025-2026 nei calcoli ma raccomandare **sempre** all'utente di verificare sul sito INPS per la propria età esatta al momento del pensionamento. Per chi si pensiona oltre il 2026, i coefficienti saranno diversi (più bassi) — quindi le proiezioni sono ottimistiche.

4. **Rivalutazione PIL**: la proiezione è in euro di oggi (RAL reale, spesa reale), quindi il montante si rivaluta al PIL **reale**: 0,5% di default, come `proiezione-inps.py` e l'Excel; scenari 0% (stagnazione) e 1%. Il PIL nominale (~1,8-2%) applicato a una RAL reale gonfia la pensione di oltre il 20%: si usa solo se anche RAL e spesa sono espresse in valori nominali.

5. **Disclaimer obbligatori**: orizzonte temporale lungo + variabilità normativa + variabilità macroeconomica = range, non puntuale. Non promettere mai.

6. **Riferimento patronato**: per dati esatti su anzianità contributiva, riscatto, totalizzazione, ricongiunzione, sempre rinviare a patronato (CGIL/CISL/UIL/INAS/etc.) o INPS. Sono servizi gratuiti.

---
*Massimale e prima fascia 2026 (Circ. INPS 6/2026), requisiti di vecchiaia, anticipata e precoci 2026-2028 (Circ. INPS 19/2026 e 28/2026, All. 2), detrazione pensionati (art. 13 c. 3 TUIR; dal 2027 art. 13 c. 3 D.Lgs. 117/2026) — Verificato: 2026-10.*
*Meccanica di rivalutazione del montante (L. 335/1995 art. 1 c. 8-9, minimo 1 dal DL 65/2015 art. 5), massimale rivalutato sui prezzi (L. 335/1995 art. 2 c. 18) e tassi 1996-2025 (nota ISTAT del 16/10/2025) — Verificato: 2026-10.*
