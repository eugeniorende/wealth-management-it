# Proiezione tenore di vita post-pensionamento

## L'approccio gap analysis

La pianificazione pensionistica si riduce concettualmente a una domanda: **il reddito atteso dalla pensione coprirà il tenore di vita desiderato?**

```
gap = spesa_target_post_pensione - reddito_pensione_netto_atteso

se gap > 0 → manca copertura, servono strategie
se gap ≈ 0 → pianificazione adeguata
se gap < 0 → over-saving, possibile alleggerire
```

## Spesa target post-pensione

### Approccio top-down: fattore di trasformazione

Regola empirica: spesa post-pensione ≈ **75-85% della spesa pre-pensione**, perché:

**Voci che SCENDONO:**
- Trasporto casa-lavoro
- Pasti fuori per lavoro
- Abbigliamento da lavoro
- Mutuo casa (se estinto prima del pensionamento)
- Eventuali figli a carico (per chi ha figli grandi a pensionamento)
- Contributi previdenziali sulla retribuzione (non più dovuti)
- Risparmio (per chi accumulava: non più necessario in pensione)

**Voci che SALGONO:**
- Sanità privata (visite, esami, farmaci, integratori, assicurazioni sanitarie)
- Tempo libero (viaggi, hobby, sport)
- Aiuti a figli/nipoti (se rilevanti)
- Assistenza/badante (in età avanzata)
- Casa (se servono adeguamenti come ascensori, monta-scale)

**Voci che restano costanti:**
- Bollette utenze
- Spesa alimentare
- Manutenzione casa
- Tasse sulla casa (IMU su seconde case)

La media netta in Italia è una riduzione del 15-25% rispetto alle spese pre-pensione, da cui il fattore 75-85%.

### Approccio bottom-up: budget dettagliato

Più accurato ma richiede più input:

| Categoria | Spesa attuale | Stima post-pensione | Note |
|---|---|---|---|
| Casa (mutuo/affitto) | €X | €Y | Estinto mutuo a 67? Manutenzione straordinaria? |
| Utenze | €X | €X | Stabile (forse +)
| Alimentazione | €X | €X×0,95 | Leggera diminuzione (no mensa lavoro) |
| Trasporti | €X | €X×0,50 | Forte calo (no casa-lavoro) |
| Salute | €X | €X×1,5-2 | Forte aumento |
| Tempo libero/viaggi | €X | €X×1,2-1,5 | Aumento moderato/forte |
| Abbigliamento | €X | €X×0,7 | Calo (no formale lavoro) |
| Famiglia/figli | €X | €X×0,5-1 | Dipende età figli |
| Altro | €X | €X | |

Per il PoC della skill, accettare entrambi gli approcci. Se l'utente non ha breakdown dettagliato, applicare fattore 0,78 di default (raccomandato dal Comparto Welfare di Bankitalia in studi su questo).

### Inflazione e potere d'acquisto

Critico: la pianificazione è in valori **nominali** (€ del giorno del pensionamento) ma il tenore di vita va calibrato in potere d'acquisto. Per orizzonti lunghi serve normalizzare:

```
spesa_target_nominal(t_pensione) = spesa_target_oggi × (1 + inflazione)^anni_residui
```

Tasso inflazione di default: **2%** (target BCE). Scenari: 1,5% conservativo (deflazione), 3% prudenziale (ondate inflattive). L'Italia 2021-2024 ha vissuto un episodio inflattivo significativo che ha eroso 8-12% di potere d'acquisto cumulativo: lezione di stress da considerare.

**Importante**: le pensioni INPS sono rivalutate annualmente all'inflazione (perequazione), ma con meccanismi non perfetti — per pensioni alte la rivalutazione è parziale (es. 90% per pensioni 4-5x minimo INPS, 75% per pensioni 5-6x minimo, ecc.). Quindi su orizzonte lungo la pensione INPS reale tende a erodersi se l'inflazione è alta e prolungata.

## Reddito pensionistico totale

### Pensione INPS netta

Calcolata in `references/previdenza-obbligatoria.md`. Output: importo netto annuo / mensile.

### Prestazione previdenza complementare

Due regimi possibili:

**Se rendita vitalizia**: contribuisce direttamente al reddito mensile.
```
rendita_lorda_mensile = (montante_netto_post_tax × tasso_conversione_annuo) / 12
rendita_netta_mensile = rendita_lorda × (1 - aliquota_IRPEF_marginale_pensione)
```

Tassi di conversione tipici (immediata vitalizia, persona singola, senza opzioni):
- A 67 anni: ~5,0-5,5% del capitale annuo
- A 70 anni: ~5,5-6,0% annuo
- A 75 anni: ~6,5-7,5% annuo (per dilazione)

Con reversibilità coniuge 60%: -10% tasso. Con certezza 10 anni: -5% tasso. Con controassicurazione completa: -15% tasso.

**Se capitale**: NON è reddito ricorrente, è patrimonio. Va trattato come:

```
flusso_annuo_da_capitale = capitale_netto × tasso_prelievo_sostenibile
```

Tasso prelievo sostenibile tipico (per durata indefinita con erosione minima): **3-4% annuo** del capitale iniziale, indicizzato all'inflazione. Questa è la celebre "4% rule" americana, applicabile con cautela in Europa (rendimenti attesi più bassi → forse 3-3,5% più prudente).

### Altri redditi

- Locazioni: stimare reddito netto (al netto cedolare secca 21% o IRPEF + spese)
- Patrimonio finanziario: applicare anche qui tasso di prelievo sostenibile
- Eredità attesa: solo se l'utente la cita, e con riserva

## Scenari di proiezione

La skill produce 3 scenari side-by-side con parametri variabili:

| Parametro | Conservativo | Base | Ottimistico |
|---|---|---|---|
| Crescita RAL annua reale | 0,5% | 1,5% | 2,5% |
| Rivalutazione PIL (montante INPS) | 1,0% | 1,8% | 2,5% |
| Inflazione | 2,5% | 2,0% | 1,5% |
| Rendimento netto comparto fondo | comparto-1% | comparto base | comparto+1% |
| Tasso prelievo capitale finanziario | 3,0% | 3,5% | 4,0% |

Tutti i tre scenari con stesse ipotesi di vita (es. orizzonte 30 anni post-pensione = vivere fino ai 97).

## Pattern di copertura del gap

Quando gap > 0 (manca copertura), proporre pattern ordinati per impatto stimato:

### P1: Massimizzare contributo deducibile complementare

Se l'utente versa meno di €5.300/anno volontari:

```
delta_montante_finale = (5300 - contributo_attuale) × CAGR_compounding(rendimento_netto, anni_residui)
risparmio_fiscale_annuo = (5300 - contributo_attuale) × aliquota_marginale_IRPEF
risparmio_fiscale_cumulato = risparmio_fiscale_annuo × anni_residui  # in nominale, non scontato
beneficio_totale_v.t. = delta_montante_finale + risparmio_fiscale_cumulato
```

Per RAL nel secondo scaglione (28-50k) il rapporto costo/beneficio è particolarmente favorevole: ogni €1.000 versato torna €330 di IRPEF risparmiato + €1.000 capitalizzato 30 anni a 4% netto = €3.243 finali. **Praticamente impossibile fare di meglio** sul medesimo €1.000 in altri strumenti.

### P2: Cambiare comparto del fondo (se troppo conservativo per l'orizzonte)

Tipico: utente con 25+ anni alla pensione in comparto garantito o obbligazionario.

```
montante_attuale_comparto_X = projection(rendimento_X, anni_residui)
montante_alternativo = projection(rendimento_Y, anni_residui)  # Y più aggressivo
delta = montante_alternativo - montante_attuale_comparto_X
```

Su 25 anni, passare da garantito (1,5% netto) a bilanciato (3,5% netto) raddoppia tipicamente il montante. Vincolo: l'utente deve essere comodo con la volatilità — non cambiare comparto in panico durante crisi.

### P3: Ritardare pensionamento

Confronto multi-età (es. 64 / 67 / 70):

```
per età_alt in [64, 67, 70]:
    montante_finale(età_alt) = aumento contributi + minore capitalizzazione vs età corrente
    coefficiente(età_alt) = tabella
    pensione_lorda(età_alt) = montante × coefficiente
    pensione_netta(età_alt) = applica fiscalità pensionati
    anni_pensione(età_alt) = aspettativa_vita - età_alt
    flusso_totale_atteso = pensione_netta × anni_pensione
```

Tipicamente passare da 64 a 67 aumenta la pensione del 15-20% e riduce gli anni di pensione percepita del 8-12% → impatto netto positivo significativo. Da 67 a 70 ulteriore +15-20%.

Trade-off: 3 anni di vita lavorativa in più vs 3 anni di "libertà" in meno. Non monetizzabile.

### P4: Conferire TFR (se ancora in azienda)

Per chi ha ancora TFR in azienda, calcolare il delta cumulato:

```
TFR_azienda_finale_netto = TFR_lordo_finale × (1 - aliquota_separata ~0,27)
TFR_fondo_finale_netto = montante_TFR_in_fondo × (1 - aliquota_fondo ~0,11)
# considerando 35+ anni partecipazione → 9% e arrotondando alle altre tasse periodiche
delta = TFR_fondo_finale_netto - TFR_azienda_finale_netto
```

Tipicamente positivo per €5.000-30.000 nominali su carriere di 25-35 anni. Vincolo: decisione irrevocabile una volta presa.

### P5: Risparmio non previdenziale (PAC, immobili, finanziario)

Pattern "riempi il resto": se P1-P4 non chiudono il gap, residuo va coperto con risparmio non vincolato.

```
gap_residuo_post_P1_P4 = gap_originale - beneficio_P1 - beneficio_P2 - beneficio_P3 - beneficio_P4
capitale_necessario_inizio_pensione = gap_residuo_residuo / tasso_prelievo_sostenibile
contributo_PAC_annuo_necessario = soluzione_capitalizzazione(capitale_necessario, anni_residui, rendimento_atteso)
```

A questo punto la skill rinvia a strumenti separati (PAC ETF, immobiliare a reddito, ecc.) e collega — se applicabile — alla skill `it-tax-optimization` per la gestione fiscalmente efficiente dei rendimenti.

## Heuristic per la skill

1. **Spesa target sempre in valori reali (potere d'acquisto)**, poi proiettata nominale all'orizzonte. Mai chiedere all'utente "quanto spenderai a 67 anni" — chiedere "quanto spendi oggi" e applicare fattori.

2. **3 scenari obbligatori** nel report: conservativo, base, ottimistico. Mai un singolo numero proiettato — orizzonte 30 anni rende la precisione apparente fuorviante.

3. **Quantificare ogni raccomandazione**: ogni pattern deve avere stima di impatto (€ delta, % gap chiuso, anni di anticipo della "indipendenza"), altrimenti è chiacchiera.

4. **Soglia minima per agire**: se un pattern produce delta < 5% del gap o < €5.000 nominali, non vale la complessità. Skill deve dire "non vale la pena" quando appropriato.

5. **Avversione al rischio della longevità**: in scenari conservativi, assumere aspettativa di vita lunga (es. 95 anni). È più costoso pianificare sotto-stimando la longevità che sovra-stimando.

6. **Inflation drift**: per scenari multi-decennali, sempre mostrare valori sia nominali sia reali (al potere d'acquisto di oggi). I numeri nominali a 30+ anni di distanza sono enormi e fuorvianti se non normalizzati.

7. **Patrimonio non finanziario**: la casa di proprietà è un asset rilevante per il tenore di vita (no affitto in pensione) ma NON va contata come reddito. Va tenuta separata nel report.

8. **Eredità futura**: se l'utente la cita, contarla con cautela (sconto al 50%+, incertezza di tempistica e ammontare). Mai considerarla un pilastro centrale della pianificazione personale.
