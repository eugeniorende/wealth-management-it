# Previdenza obbligatoria INPS (lavoratore dipendente privato)

## Il sistema contributivo

Per i lavoratori senza contribuzione al 31/12/1995 (Legge Dini 335/1995), il sistema è interamente **contributivo**: la pensione si calcola in base ai contributi effettivamente versati, rivalutati, e trasformati in rendita all'età di pensionamento.

Per chi ha contributi prima del 31/12/1995:
- **>18 anni di contribuzione al 31/12/1995**: sistema misto, con quota retributiva (più favorevole) fino al 2011 e contributiva dal 2012 in poi (riforma Fornero)
- **<18 anni di contribuzione al 31/12/1995**: contributivo pro-rata dal 1° gennaio 1996

Per Eugenio (developer, presumibilmente con primo lavoro post-1996) il sistema è interamente **contributivo**.

## Formula di calcolo (contributivo puro)

```
Step 1: Contributo annuo accreditato
  contributo_anno = retribuzione_annua × aliquota_di_computo
  aliquota_di_computo (lavoratore dipendente) = 33%

Step 2: Rivalutazione montante
  Ogni anno il montante accumulato viene rivalutato in base alla 
  media quinquennale del PIL nominale (con minimo 1)
  
  montante(t+1) = (montante(t) + contributo_anno(t+1)) × (1 + tasso_PIL)
  
  Storicamente tasso medio: 1,5-2,5% annuo (più alto in fasi inflattive)

Step 3: Pensione lorda annua
  pensione_lorda = montante_finale × coefficiente_trasformazione(età)
```

## Aliquote contributive lavoro dipendente privato 2026

- **Aliquota di computo (totale)**: 33% (FPLD - Fondo Pensioni Lavoratori Dipendenti)
- **A carico lavoratore**: 9,19% sulla retribuzione lorda fino al primo scaglione INPS; 10% sulla parte eccedente
- **A carico azienda**: 23,81%
- **Tetto contributivo annuo 2026**: ~€120.607 (oltre questa soglia, per chi è interamente contributivo post-1995, **non si versa più contributo obbligatorio** sulla parte eccedente — e quindi non matura ulteriore montante)

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
5. **Verifica sempre con INPS**: per chi è prossimo al pensionamento, rinviare a verifica diretta sul sito INPS (mypensione → estratto contributivo + simulazione) o patronato. La proiezione serve per chi è lontano dal pensionamento; chi è vicino usa il coefficiente reale del proprio biennio.

## Requisiti di accesso pensione 2026

### Pensione di vecchiaia

- **Età anagrafica**: 67 anni (adeguamento speranza di vita: previsti aumenti di 1 mese nel 2027, 2 mesi nel 2028)
- **Anzianità contributiva**: 20 anni
- **Importo soglia** (solo contributivi puri): pensione spettante ≥ 1,5 volte assegno sociale (per il 2026 circa €795 mensili)

Se l'importo soglia non è raggiunto a 67 anni, si può comunque andare in pensione a 71 anni con almeno 5 anni di contributi effettivi.

### Pensione anticipata ordinaria

Requisiti contributivi puri (a prescindere dall'età):
- **Uomini**: 42 anni e 10 mesi di contributi (con finestra mobile 3 mesi)
- **Donne**: 41 anni e 10 mesi di contributi (finestra 3 mesi)

Adeguamento alla speranza di vita previsto dal 2027.

### Misure sperimentali / Quota X

In vigore o di prossima introduzione:

- **Quota 103** (prorogata): 62 anni + 41 contributi, ma con calcolo interamente contributivo (penalizzazione rispetto al misto)
- **Quota 104**: ulteriore opzione, dettagli da Legge di Bilancio annuale
- **Opzione donna**: 59-61 anni (variabile per categoria) + 35 contributi, con calcolo contributivo (penalizzazione)
- **APE Sociale**: 63 anni e 5 mesi + 30 contributi (lavoratori in difficoltà specifiche), prorogata al 31/12/2026 dalla Legge di Bilancio 2026
- **Lavoratori precoci / Quota 41**: 41 anni di contributi (di cui almeno 1 prima dei 19 anni di età) per categorie tutelate

Tutti questi richiedono ricostruzione della posizione contributiva con patronato/INPS.

## Tassazione assegno pensionistico

L'assegno è soggetto a:

### IRPEF (2026)

Scaglioni standard: 23% / 33% / 43%. La pensione concorre a formare il reddito complessivo.

### Detrazioni pensionati 2026

- No tax area: €8.500 (parificata ai lavoratori dipendenti dal 2024)
- Detrazione max: €1.955 per redditi fino a €8.500
- Detrazione decrescente tra €8.500 e €28.000
- Detrazione minima oltre €28.000: ~€1.880

Le detrazioni pensionati sono leggermente diverse da quelle dei lavoratori dipendenti, ma simili in struttura.

### Addizionali

- **Regionale**: 0,70% - 3,33% (varia per regione; Calabria attualmente ~2,03%)
- **Comunale**: 0% - 0,90% (varia per comune)

### Esempio numerico (pensione lorda annua €16.824 a 67 anni, residenza tipica)

```
Pensione lorda annua: €16.824
IRPEF lorda (tutto nel primo scaglione 23%): €3.870
Meno detrazione pensionati (su €16.824, decrescente): ~€1.920
IRPEF netta: €1.950
Addizionali (~2%): €336
Pensione netta annua: €16.824 - €1.950 - €336 = €14.538
Pensione netta mensile (su 13 mensilità): €1.118
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

1. **Età corrente vs età target**: chiedere sempre, non assumere 67. Molti developer e profili tech mirano a 64 con anticipata o quota; molti vogliono valutare l'opzione di lavorare fino a 70.

2. **Anzianità INPS corrente**: l'utente la trova nell'estratto conto INPS (PIN/CIE/SPID → mypensione → estratto contributivo). Se non disponibile, stimare da `eta_inizio_lavoro` ma flaggare l'approssimazione.

2-bis. **Montante contributivo già maturato**: è il dato che più pesa sul risultato, e il più incerto se stimato (dipende dall'intera carriera passata, che non conosciamo). Va **chiesto all'utente il valore reale**: lo trova sul sito INPS in "La mia pensione futura" o nell'estratto conto contributivo (il montante rivalutato a oggi). Se non disponibile, lo si **stima** dalla RAL attuale e dall'anzianità, ma la stima va dichiarata tale. La stima migliore non è la grezza `anzianità × RAL × 33%` (che assume RAL costante e nessuna rivalutazione dei contributi passati): è `RAL × 33% × Σ q^k` con `q = (1+rivalutazione)/(1+crescita_RAL)`, che tiene conto sia della retribuzione passata più bassa sia della rivalutazione dei versamenti già fatti. Quando rivalutazione ≈ crescita salariale le due distorsioni si compensano e si torna alla grezza; quando differiscono, la stima migliorata corregge nella direzione giusta. Il template Excel lo fa: se la cella "Montante INPS da estratto conto" è valorizzata usa quella, altrimenti applica la stima migliorata.

3. **Coefficienti aggiornati**: usare i valori 2025-2026 nei calcoli ma raccomandare **sempre** all'utente di verificare sul sito INPS per la propria età esatta al momento del pensionamento. Per chi si pensiona oltre il 2026, i coefficienti saranno diversi (più bassi) — quindi le proiezioni sono ottimistiche.

4. **Rivalutazione PIL**: usare 1,8% di default (media storica) come scenario base. Permettere all'utente di variare in scenari (1,5% conservativo, 2,5% ottimistico).

5. **Disclaimer obbligatori**: orizzonte temporale lungo + variabilità normativa + variabilità macroeconomica = range, non puntuale. Non promettere mai.

6. **Riferimento patronato**: per dati esatti su anzianità contributiva, riscatto, totalizzazione, ricongiunzione, sempre rinviare a patronato (CGIL/CISL/UIL/INAS/etc.) o INPS. Sono servizi gratuiti.
