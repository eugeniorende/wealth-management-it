---
name: it-pianificazione
description: Pianificazione pensionistica integrata per lavoratori dipendenti italiani. Coordina previdenza obbligatoria (INPS contributivo), previdenza complementare (fondi pensione, PIP, TFR) e proiezione del tenore di vita post-pensionamento. Usa questa skill ogni volta che l'utente parla di: pensione futura, quando andrò in pensione, quanto prenderò di pensione, conferimento TFR, scelta fondo pensione (negoziale/aperto/PIP), deduzione fiscale €5.300, anzianità contributiva, coefficiente di trasformazione, tasso di sostituzione, gap pensionistico, tenore di vita post-67 anni, simulazione "ce la farò a mantenere lo stile di vita?", anticipata vs vecchiaia, riscatto laurea, ricongiunzione, totalizzazione. Trigger anche su domande di scelta tra fondo aperto/negoziale/PIP, anticipazioni fondo pensione, opzione capitale vs rendita, decisioni a 30-40 anni dal pensionamento. Questa skill è per i lavoratori DIPENDENTI; per autonomi/partite IVA/forfettari usa `it-pianificazione-autonomi`. NON sostituisce un consulente previdenziale abilitato e NON copre dipendenti pubblici.
---

# it-pianificazione

Skill per la pianificazione pensionistica integrata di un lavoratore dipendente privato italiano. Coordina tre sottosistemi (obbligatoria, complementare, tenore di vita) per produrre proiezioni multi-anno e raccomandazioni d'azione.

## Scope esplicito

**Cosa fa:**
1. **Proiezione previdenza obbligatoria**: stima del montante contributivo e dell'assegno pensionistico INPS atteso
2. **Proiezione previdenza complementare**: capitalizzazione contributi (TFR + volontari + datore) con tassazione finale
3. **Confronto TFR azienda vs fondo**: blocco «Confronto TFR» nel foglio Complementare dell'Excel (rivalutazione tassata al 17% e tassazione separata contro 15→9% sulle sole quote), con il vantaggio netto in euro di oggi
4. **Gap analysis tenore di vita**: confronto tra pensione totale attesa e spesa proiettata
5. **Raccomandazioni d'azione**: pattern di copertura del gap, quantificati

**Cosa NON fa (v0.1):**
- ❌ Non copre lavoratori autonomi, P.IVA forfettari, casse professionali → usa la skill gemella `it-pianificazione-autonomi` (regime previdenziale e fiscale diverso: Gestione Separata 26,07%, no TFR, e per i forfettari il fondo pensione NON è deducibile)
- ❌ Non copre dipendenti pubblici (TFS vs TFR, regimi specifici)
- ❌ Non gestisce ricongiunzione, totalizzazione, riscatto laurea (questi richiederebbero accesso a dati INPS reali)
- ⚠️ Il foglio Excel è deterministico (scenari multipli a parametri editabili); il Monte Carlo c'è ma in uno script a parte (`montecarlo-pensione.py`), e simula il fondo pensione, non il pilastro pubblico (che è rivalutato al PIL, non al mercato)
- ❌ Non sostituisce il consulente previdenziale abilitato o il commercialista

## I tre sottosistemi (overview)

### Sistema 1: Previdenza obbligatoria (INPS)

Per i lavoratori senza contribuzione al 31/12/1995 (cioè tutti coloro nati dopo ~1976-1980), il sistema è interamente **contributivo**:

```
montante_contributivo = Σ (retribuzione_anno × 33%) × rivalutazione (media PIL nominale 5 anni)
pensione_lorda_annua = montante_contributivo × coefficiente_trasformazione_PROIETTATO(età_pensionamento)
                       # il coefficiente va proiettato in calo all'anno di pensionamento (vedi Step 2)
```

I coefficienti di trasformazione sono fissati per legge e aggiornati ogni 2 anni (in calo strutturale per via dell'aumento speranza di vita). Per il biennio 2025-2026 (Decreto direttoriale 20/11/2024, GU n. 35 del 12/02/2025): a 67 anni = **5,608%** (era 5,723%); range 57-71 anni.

Vedi `references/previdenza-obbligatoria.md` per: tabella coefficienti completa, requisiti accesso (vecchiaia, anticipata ordinaria e contributiva, APE sociale; Quota 103 e Opzione donna solo per chi aveva già maturato i requisiti), tasso di sostituzione tipico, tassazione assegno pensione.

### Sistema 2: Previdenza complementare

Tre forme: fondo negoziale (di categoria), fondo aperto, PIP (Piano Individuale Pensionistico). Si alimenta con:

1. **TFR** (se conferito): ~6,91% della RAL annua + rivalutazione
2. **Contributo volontario lavoratore**: deducibile fino a **€5.300/anno** (era €5.164,57, alzato dalla Legge di Bilancio 2026)
3. **Contributo datore di lavoro**: se previsto da CCNL/contratto, **conta nel plafond** di €5.300 insieme ai contributi del lavoratore (art. 8 c. 4 D.Lgs. 252/2005); il TFR conferito no

Tassazione:
- Sui rendimenti annui (fase accumulo): **20%** (12,5% sulla quota in titoli di Stato whitelist)
- Sulle prestazioni finali: **15%** di base, scende di 0,30 punti % per ogni anno di partecipazione oltre il 15esimo, fino a un minimo del **9%** (al 35° anno), sui soli TFR conferito e contributi dedotti (rendimenti già tassati e non dedotti comunicati esclusi)

Vedi `references/previdenza-complementare.md` per: scelta tra forma (negoziale vs aperto vs PIP), conferimento TFR, scelta comparto (garantito/obbligazionario/bilanciato/azionario), anticipazioni, riscatti, opzione capitale vs rendita.

### Sistema 3: Proiezione tenore di vita

Gap analysis tra:
- **Pensione netta totale** = pensione obbligatoria netta + (eventuale) rendita complementare netta o equivalente di un capitale erogato
- **Spesa target post-pensione** = spesa attuale × fattore di trasformazione (cambia il mix: meno lavoro, più sanità, più tempo libero, ma di solito netto inferiore)

Strategie di copertura del gap (vedi `references/proiezione-tenore-vita.md`):
- Aumentare contribuzione complementare (entro €5.300 deducibili)
- Cambiare comparto (più rischio → più rendimento atteso, se orizzonte lungo)
- Ritardare pensionamento (più anni contribuzione + coefficiente più alto)
- Risparmio non previdenziale extra (PAC ETF, immobiliare, ecc.)
- Conferire TFR se ancora in azienda (decisione fiscalmente quasi sempre conveniente)

## Regole fiscali e contributive fondamentali (2026)

### IRPEF (Legge di Bilancio 2026, L. 199/2025)

| Scaglione | Aliquota |
|---|---|
| Fino a €28.000 | 23% |
| €28.001 - €50.000 | **33%** (ridotta da 35%) |
| Oltre €50.000 | 43% |

No tax area: €8.500 (dipendenti/pensionati). Detrazione lavoro dipendente max: €1.955. Detrazione pensione: art. 13 c. 3 TUIR (dal 2027 art. 13 c. 3 D.Lgs. 117/2026), formula nella sezione «Tassazione assegno pensionistico».

Sterilizzazione benefit per redditi > €200.000: le detrazioni per oneri al 19% (escluse le spese sanitarie), per erogazioni ai partiti politici e per premi di polizze contro eventi calamitosi sono ridotte di €440 (art. 16-ter c. 5-bis TUIR, introdotto dalla L. 199/2025; dal 2027 art. 18 c. 6 D.Lgs. 117/2026): neutralizza il risparmio massimo della riduzione di aliquota (2% × €22.000).

*Scaglioni IRPEF 2026 (art. 11 TUIR, mod. L. 199/2025 c. 3; dal 2027 art. 11 D.Lgs. 117/2026), detrazione lavoro dipendente max €1.955 e no tax area €8.500 (art. 13 TUIR; dal 2027 art. 13), riduzione di €440 per redditi > €200.000 (art. 16-ter c. 5-bis TUIR; dal 2027 art. 18 c. 6) — Verificato: 2026-10.*

### Contributi INPS lavoro dipendente privato

- **Aliquota di computo**: 33%
- **A carico lavoratore**: 9,19% (10% per la parte di reddito oltre la prima fascia di retribuzione pensionabile, €56.224 nel 2026)
- **A carico azienda**: 23,81%
- **Tetto contributivo annuo**: €122.295 nel 2026, Circ. INPS 6/2026 (oltre, no contribuzione obbligatoria — soglia post-1995)

### TFR (lavoratore dipendente privato)

- **Accantonamento annuo**: RAL_lordo × (1 / 13,5) ≈ 6,91% (formula esatta: RAL ÷ 13,5 deducendo lo 0,5% destinato a INPS Fondo di Garanzia)
- **Rivalutazione TFR in azienda**: 1,5% + 75% inflazione ISTAT (art. 2120 c.c.), con imposta sostitutiva del **17%** sulla rivalutazione di ogni anno
- **Tassazione TFR liquidato in azienda**: separata (artt. 17 e 19 TUIR; dal 2027 artt. 19 e 21 D.Lgs. 117/2026), sulle quote senza le rivalutazioni già tassate, all'aliquota media del «reddito di riferimento» (TFR × 12 / anni di servizio); gli uffici poi riliquidano sull'aliquota media dei 5 anni precedenti (tipicamente 23-30%)
- **Tassazione TFR conferito a fondo**: 15% scendente al 9% (vedi sopra) sulle sole quote di TFR; i rendimenti, già tassati ogni anno nel fondo, sono esclusi

### Tassazione assegno pensionistico

L'assegno pensione INPS è soggetto a IRPEF ordinaria con scaglioni standard. Si applicano:
- Detrazione pensionati (art. 13 c. 3 TUIR, dal 2027 art. 13 c. 3 D.Lgs. 117/2026; R = reddito complessivo): €1.955 fino a €8.500 (no tax area); 700 + 1.255 × (28.000 − R) / 19.500 fino a €28.000; 700 × (50.000 − R) / 22.000 fino a €50.000; zero oltre; +€50 tra €25.000 e €29.000 (c. 3-bis; dal 2027 art. 13 c. 4 D.Lgs. 117/2026). È la formula di `assets/netto-pensione.py`
- Addizionali regionali e comunali (variabili: 0,7-3,33% regionale, 0-0,9% comunale)

## Workflow operativo

### Step 1: Ingestion

**Percorso automatico (preferito)**: se l'utente ha i file reali, usare `assets/importa-previdenza.py`:

```bash
python importa-previdenza.py estratto_inps.xml [storico_fondo.csv] [--anonimo]
```

Con `--anonimo` lo script non stampa intestatario e data di nascita (l'età resta, arrotondata all'anno): proporlo quando l'output finisce in chat o in un documento da condividere.

Legge l'**estratto conto contributivo INPS** (XML dal portale) e lo **storico movimenti del fondo pensione** (CSV), e produce: anzianità e retribuzioni per anno, la ricostruzione del montante contributivo (contributi × aliquota, capitalizzati coi tassi ufficiali ISTAT — tabella verificata nello script, ±qualche % rispetto al dato esatto de "La mia pensione futura"), montante del fondo per comparto con stima euristica del mix azionario, versamenti per anno/fonte, e il blocco di parametri pronti per `proiezione-inps.py` e `montecarlo-pensione.py`. I dati reali battono sempre quelli dichiarati a memoria.

**Percorso manuale**: raccogliere obbligatoriamente:

**Dati anagrafici e lavorativi:**
- `data_nascita` (o età corrente)
- `sesso` (rilevante per requisiti pensione anticipata)
- `eta_pensionamento_target` (default: 67 = vecchiaia; opzioni: 64 anticipata contributiva, 67 vecchiaia, 70 ritardata)
- `RAL_lordo_attuale` (€)
- `anni_anzianita_INPS_correnti` (a oggi)
- `montante_INPS_corrente` (€, dal **estratto conto INPS** — il dato esatto; se assente viene stimato dalla RAL e dall'anzianità)
- `eta_inizio_lavoro` (per calcolare anzianità totale stimata)
- `crescita_retributiva_attesa` (default: 1,5%/anno + inflazione)

**Stato TFR:**
- `tfr_in_azienda_residuo` (€, se ancora in azienda)
- `tfr_conferito_a_fondo` (sì/no, da quando)

**Fondo pensione esistente (se applicabile):**
- `tipo_fondo` (negoziale/aperto/PIP)
- `nome_fondo` (per riferimento)
- `montante_accumulato_corrente` (€)
- `contributo_volontario_annuo` (€)
- `contributo_datore_annuo` (€, se previsto)
- `comparto_scelto` (garantito/obbligazionario/bilanciato/azionario)
- `anni_partecipazione_correnti`

**Spese e obiettivi:**
- `spese_mensili_attuali` (€, breakdown opzionale: casa, alimentazione, trasporti, salute, tempo libero, altro)
- `aspettativa_spese_pensione` (% delle correnti, default: 75-80%)
- `priorita_lascito` (se l'utente ha figli/eredi e considera importante il lascito → influenza scelta capitale vs rendita)

**Altri redditi (opzionali ma utili):**
- `redditi_locazione_annui`
- `patrimonio_finanziario_attuale`

Se manca un dato critico (RAL, anzianità, età) → CHIEDERE, non inventare.

### Step 2: Calcolo previdenza obbligatoria

Lo script `assets/proiezione-inps.py` implementa questo calcolo in forma parametrica ed eseguibile: montante attuale + contributi futuri (RAL con crescita reale) capitalizzati al PIL reale, coefficiente di trasformazione dalla tabella vigente 2025-26 (DM 436/2024) con riduzione parametrica per l'allungamento della speranza di vita, e **tabella di sensibilità 3×3** sui due parametri fuori dal controllo dell'utente (PIL reale × riduzione coefficienti). Preferirlo al calcolo a mano: rispetta la meccanica L.335/1995 (l'ultimo anno di contributi non si rivaluta) e rende confrontabili gli scenari. Lo pseudocodice sotto resta la specifica di riferimento.

```pseudocodice
# 1) Montante GIÀ MATURATO a oggi — usare il valore REALE dall'estratto conto INPS
#    (sito INPS → "La mia pensione futura" o estratto conto contributivo). È il dato ESATTO,
#    e va preferito a qualsiasi stima. Nell'Excel: cella "Montante INPS da estratto conto".
montante_oggi = montante_da_estratto_conto              # se disponibile

#    FALLBACK se non disponibile (stima): tiene conto sia della RAL passata più bassa
#    (cresciuta a g) sia della rivalutazione dei contributi già versati (a riv), anno per anno.
#    k = anni fa (k=1 è l'anno scorso); il massimale è costante in euro di oggi e il contributo
#    dell'anno scorso non si è ancora rivalutato (L. 335/1995):
montante_oggi ≈ Σ(k=1..anzianità) min(RAL_attuale / (1+g)^k, massimale) × 0,33 × (1+riv)^(k-1)
#    Senza massimale si avvicina alla vecchia stima grezza (anzianità × RAL × 0,33) quando
#    riv ≈ g, perché i due effetti si compensano; diverge (correttamente) quando differiscono.

# 2) Proiezione FUTURA anno per anno (foglio "Pubblica"), in euro di oggi: ogni anno il
#    montante è rivalutato al PIL reale e vi si aggiunge il contributo dell'anno
#    (min(RAL_crescente, massimale) × 33%), che si rivaluta solo dall'anno dopo.
#    La rivalutazione si applica ANNO PER ANNO: ogni contributo futuro è rivalutato solo
#    per gli anni che gli restano (una rivalutazione "in blocco" sull'intera somma sovrastima).
anni_residui = eta_pensionamento_target - eta_corrente
montante_finale = proiezione_anno_per_anno(montante_oggi, RAL_crescente, rivalutazione, anni_residui)

# 3) Pensione lorda — il coefficiente va PROIETTATO in calo all'anno di pensionamento.
# I coefficienti calano ~1,8% per biennio (speranza di vita in aumento). Usare quello
# ATTUALE per una pensione lontana sovrastima l'assegno (errore comune e grave).
coefficiente_attuale = coefficiente_trasformazione(eta_pensionamento_target)  # da tabella DM 20/11/2024
bienni_mancanti = anni_residui / 2
coefficiente_proiettato = coefficiente_attuale × (1 - decadimento_biennale)^bienni_mancanti
                          # decadimento_biennale ≈ 0,018 (1,8%); usare 0 solo per scenario "congelato"
pensione_lorda_annua = montante_finale × coefficiente_proiettato

# Pensione netta
detrazione_pensionati = calcola_detrazione(pensione_lorda_annua)  # art. 13 c. 3 TUIR (dal 2027 stesso articolo e comma), come netto-pensione.py
IRPEF = applica_scaglioni(pensione_lorda_annua) - detrazione_pensionati
addizionali = pensione_lorda × ~2%  # stima medio
pensione_netta_annua = pensione_lorda_annua - IRPEF - addizionali
```

> **Il montante di partenza è il dato che più conta, e il più incerto da stimare.** La stima dipende dall'intera carriera passata, che la formula non conosce: per questo va sempre chiesto all'utente il **montante reale dall'estratto conto INPS** (gratis sul sito INPS). La stima è solo un ripiego ed è dichiarata tale.

**Esempio del perché conta** (caso d'esempio: 37 anni, pensione a 67 = 30 anni di orizzonte):
- Coefficiente attuale a 67 anni: 5,608%
- Coefficiente proiettato al 2056 (15 bienni × −1,8%): **4,271%**
- Su un montante di €786k: pensione lorda €33.576 col proiettato, contro €44.100 col coefficiente attuale (sovrastima del 31%!). Il tasso di sostituzione passa da un irrealistico 79% a un realistico 61%.

Output Step 2:
- Pensione lorda mensile/annua attesa
- Pensione netta mensile/annua attesa
- Tasso di sostituzione lordo (= pensione_lorda / RAL_finale_stimata)
- Tasso di sostituzione netto (= pensione_netta / RAL_netta_finale)

⚠️ Disclaimer numerico obbligatorio: indicare *sempre* che il calcolo è una stima basata su assunzioni di crescita retributiva, rivalutazione PIL e proiezione del coefficiente di trasformazione — tutte soggette a variazione su orizzonti multidecennali. In particolare il coefficiente è proiettato in calo (default 1,8%/biennio): l'entità reale del calo è incerta, quindi la pensione stimata è un ordine di grandezza, non un valore preciso.

### Step 3: Calcolo previdenza complementare

```pseudocodice
# Contributi annui al fondo
contributo_tfr_annuo = RAL × 0,0691  # se conferito
contributo_volontario = input_utente
contributo_dovuto = input_utente  # minimo del lavoratore da CCNL, se previsto
contributo_datore = input_utente  # da CCNL
contributi_totali_annui = contributo_tfr_annuo + contributo_volontario + contributo_dovuto + contributo_datore

# Beneficio fiscale annuo dalla deduzione: lavoratore e datore condividono il plafond
# di €5.300 (il TFR no); il volontario deduce solo lo spazio lasciato da datore e dovuto
aliquota_marginale = max_aliquota_irpef_applicata(RAL)  # 23%, 33%, o 43%
gia_dedotti = contributo_datore + contributo_dovuto
volontario_deducibile = min(5300, gia_dedotti + contributo_volontario) - min(5300, gia_dedotti)
risparmio_fiscale_annuo = volontario_deducibile × aliquota_marginale
# i contributi oltre il plafond vanno comunicati al fondo entro il 31/12 dell'anno successivo

# Proiezione montante
rendimento_lordo_comparto = parametro(comparto)
# Tipici: garantito 1-2%, obbligazionario 2-3%, bilanciato 3-4,5%, azionario 5-7%
rendimento_netto_annuo = rendimento_lordo × (1 - 0,20)  # ~tassa 20%, ~12,5% per quota titoli stato
# i tipici sopra sono nominali: l'Excel e lo Step 4 sono in euro di oggi e vogliono il REALE
rendimento_reale ≈ rendimento_netto_annuo − costi − inflazione  # bilanciato ~2,5% (come montecarlo-pensione.py)
montante_finale = capitalizza(montante_attuale, contributi_totali_annui, rendimento_netto_annuo, anni_residui)

# Tassazione finale
anni_partecipazione_totali = anni_partecipazione_correnti + anni_residui
aliquota_finale = max(9%, 15% - 0,30% × max(0, anni_partecipazione_totali - 15))
prestazione_lorda = montante_finale
# base imponibile: TFR conferito + contributi dedotti; esclusi i rendimenti già tassati
# e i contributi non dedotti comunicati al fondo (art. 11 c. 6 D.Lgs. 252/2005; dal 2027 art. 258 c. 4 D.Lgs. 117/2026)
prestazione_netta = montante_finale - (tfr_conferito + contributi_dedotti) × aliquota_finale
```

Confronto chiave: **TFR azienda vs TFR conferito al fondo**, sulle medesime ipotesi di RAL e durata:
- TFR azienda: capitale netto = TFR_rivalutato − quote × aliquota_media_separata (~23-27%); la rivalutazione (1,5% + 75% dell'inflazione) paga già il 17% ogni anno
- TFR fondo: capitale netto = montante_TFR − quote × aliquota_fondo (9-15%); i rendimenti, già tassati al 20%, non pagano altro

Il foglio Complementare dell'Excel fa il conto (blocco «Confronto TFR»): con RAL €40.000 per 30 anni, inflazione 2% e comparto al 2,5% reale il fondo vale ~€40.100 netti in più in euro di oggi, di cui ~€7.700 di tasse risparmiate (a scaglioni di oggi) e il resto dal rendimento atteso, che è incerto. Il vantaggio fiscale è certo, quello di rendimento no. Si conferisce il TFR futuro: quello già maturato di regola resta in azienda, e con il TFR ancora in azienda il blocco confronta le sole quote future.

### Step 4: Proiezione tenore vita

```pseudocodice
# Spesa target post-pensione
spesa_attuale = input_utente
fattore_riduzione = input_utente OR default 0.78  # 78% delle correnti
spesa_target_annua = spesa_attuale × 12 × fattore_riduzione

# Pensione totale netta
# Se previdenza complementare → rendita: assumere conversione ~5-6% del montante
# Se previdenza complementare → capitale (max 50%; il resto in rendita vitalizia o, dal 2026,
#   a durata definita, con prelievi o frazionata): il capitale non è rendita, va gestito come patrimonio
rendita_complementare_netta_annua = capitale_complementare_netto × tasso_conversione_rendita

reddito_pensione_totale = pensione_pubblica_netta_annua + rendita_complementare_netta_annua

gap_annuo = spesa_target_annua - reddito_pensione_totale
gap_percentuale = gap_annuo / spesa_target_annua
```

### Step 5: Raccomandazioni

Per ciascun pattern di copertura, quantificare l'impatto:

- **Pattern P1 — Massimizzare contributo deducibile**: se contributi del lavoratore e del datore insieme non saturano i €5.300/anno, calcolare il delta montante finale + il risparmio IRPEF cumulato
- **Pattern P2 — Cambiare comparto**: se l'utente è in garantito con 25+ anni alla pensione, mostrare il delta atteso passando a bilanciato/azionario
- **Pattern P3 — Ritardare pensionamento**: confronto 64/67/70 anni — più anni contributi + coefficiente migliore + meno anni di pensione (ma tenore di vita)
- **Pattern P4 — Conferire TFR**: se ancora in azienda, simulare il delta cumulato sulle quote future di TFR (il maturato resta in azienda), come scenario: la scelta è irrevocabile
- **Pattern P5 — Risparmio non previdenziale**: copertura del residuo gap via PAC ETF (rinviare a competenze separate)

Per ogni pattern: pro, contro, vincoli (es. €5.300 cap, rischio comparto), orizzonte temporale.

## Formato output

Report markdown in 5 sezioni + (su richiesta) Excel di proiezione.

### 1. Stato attuale

| Voce | Valore |
|---|---|
| Età corrente / Età target pensionamento | XX / 67 |
| RAL attuale | €XX.XXX |
| Anzianità INPS | XX anni |
| TFR (azienda residuo / conferito) | €XX.XXX / €XX.XXX |
| Fondo pensione esistente | Tipo, montante, comparto |
| Spesa mensile attuale | €X.XXX |

### 2. Proiezione previdenza obbligatoria

- Pensione lorda annua attesa a età target
- Pensione netta annua/mensile
- Tasso di sostituzione lordo e netto
- Coefficiente applicato e disclaimer aggiornamento biennale

### 3. Proiezione previdenza complementare

- Montante atteso a pensionamento (per comparto attuale)
- Tassazione finale stimata (aliquota e valore)
- Beneficio fiscale cumulato dalle deduzioni
- Confronto TFR azienda vs fondo (delta in €)

### 4. Gap analysis tenore di vita

- Reddito pensionistico totale netto atteso
- Spesa target post-pensione
- Gap (assoluto e %)
- Sensitivity: scenari conservativo / base / ottimistico (basati su variazioni di crescita retributiva, rivalutazione PIL, rendimento comparto)

### 5. Raccomandazioni d'azione

Lista dei pattern applicabili, ordinati per impatto stimato:
- Cosa fare
- Perché
- Quanto cambia il gap
- Vincoli e rischi

### Excel allegato (su richiesta)

Il template `assets/proiezione-pensione.xlsx` (incluso nella skill) è il deliverable Excel pronto all'uso. Contiene 5 fogli:

- **Input**: tutti i parametri editabili dall'utente (testo blu), in euro di oggi. Età, RAL, anzianità INPS, crescita retributiva reale, **PIL reale** (default 0,5%, come `proiezione-inps.py`), inflazione, **decadimento del coefficiente per biennio** (default 1,8%), stato TFR, parametri fondo pensione, spese, massimale contributivo 2026. Le formule (testo nero) calcolano i valori derivati: anni residui, aliquota IRPEF marginale, aliquota fondo finale, spesa annua target, e il **coefficiente proiettato all'anno di pensionamento**.

- **Coefficienti**: tabella ufficiale completa DM 20/11/2024 (15 valori 57-71 anni) con note operative.

- **Pubblica**: proiezione INPS anno per anno (50 righe), con risultati finali aggregati: contributi fino al massimale, rivalutazione dall'anno successivo al versamento (L. 335/1995). Mostra **sia il coefficiente attuale 2025-2026** (come riferimento) **sia quello proiettato** all'anno di pensionamento (quello effettivamente usato per la pensione), così la differenza è visibile. Poi pensione lorda, IRPEF, detrazione pensionati, addizionali, pensione netta, tasso di sostituzione.

- **Complementare**: proiezione fondo pensione anno per anno (TFR se conferito, contributi del lavoratore e del datore, rendimenti), con quota deducibile e non dedotto da comunicare (plafond condiviso), spazio deducibile residuo, prestazione finale netta (tassa sui soli TFR e contributi dedotti), rendita stimata, risparmio IRPEF sulla quota deducibile e il **confronto TFR in azienda vs fondo**.

- **Scenari**: confronto Conservativo / Base / Ottimistico, tutto in euro di oggi. Base coincide con i fogli di calcolo; gli altri due ricalcolano pensione INPS e fondo con crescita RAL, PIL reale, decadimento del coefficiente e rendimento della propria colonna. GAP (spesa target − reddito pensione) in euro di oggi e, in una riga a parte, in € del pensionamento. Con il TFR in azienda il suo netto è capitale fuori dal gap (riga 16), tradotto in rendita equivalente al 5,5% nella riga 34 per confrontare le due scelte. Le soglie fiscali (scaglioni, plafond) restano quelle di oggi in euro di oggi.

Il template usa convenzioni industry-standard (blu = input, nero = formule, verde = cross-sheet) e si auto-aggiorna quando l'utente modifica le celle blu. Il ricalcolo in locale italiano con LibreOffice (CI) verifica che nessuna cella vada in errore. **Il coefficiente di trasformazione è proiettato in calo** all'anno di pensionamento (non usa quello attuale), così la pensione stimata è realistica anche su orizzonti lunghi.

✅ **Montante INPS iniziale (migliorato in v0.3)**: il template ora accetta il **montante reale dall'estratto conto INPS** (cella dedicata nel foglio Input) e lo usa quando valorizzato — è il dato esatto. Se assente, la stima di ripiego non è più la grezza `anzianità × RAL × 33%` ma la somma anno per anno di `min(RAL/(1+g)^k, massimale) × 33% × (1+rivalutazione)^(k−1)`, che tiene conto della retribuzione passata più bassa, del massimale (costante in euro di oggi) e della rivalutazione dei contributi già versati (e si avvicina alla grezza quando i due effetti si compensano). Resta comunque preferibile inserire il valore reale (gratis sul portale INPS, www.inps.it, area riservata con SPID, CIE o CNS: servizio "Estratto conto contributivo").

### Disclaimer (obbligatorio in fondo)

> **Disclaimer**: questo report ha finalità informative di pianificazione personale. Non costituisce consulenza previdenziale, fiscale, finanziaria o di investimento professionale. Le proiezioni si basano su assunzioni (crescita retributiva, rivalutazione PIL, rendimento fondi, inflazione) che possono divergere significativamente nell'arco di 20-40 anni. I coefficienti di trasformazione INPS sono aggiornati ogni 2 anni e tendono al ribasso. La normativa fiscale (deducibilità, scaglioni IRPEF, tassazione fondi) è soggetta a modifiche con le Leggi di Bilancio annuali. Per situazioni specifiche (riscatto laurea, totalizzazione, lavoratori usuranti, opzioni anticipate, lavoratore dipendente pubblico con TFS, doppia gestione INPS+cassa) consultare un patronato o consulente previdenziale abilitato.

## Anti-pattern (NON FARE MAI)

- ❌ Confrontare TFR azienda vs fondo solo sui rendimenti — la tassazione (separata ~23-27% contro 9-15% sulle sole quote) è il vantaggio certo; quello di rendimento dipende dal comparto
- ❌ Assumere coefficienti di trasformazione fissi nel tempo — calano ~1,8% ogni biennio. Per pensioni lontane si DEVE proiettare il coefficiente in avanti (vedi Step 2), non usare quello attuale: su 30 anni la sovrastima della pensione arriva al 30%. L'Excel della skill lo fa automaticamente tramite il parametro "Decadimento coefficiente / biennio".
- ❌ Promettere pensioni in valore nominale a 30+ anni come fossero certezze — l'inflazione e i cambi normativi rendono ogni stima un range, non un punto
- ❌ Calcolare il "tasso di sostituzione" senza specificare se lordo o netto — sono valori diversi (il netto è quasi sempre più alto del lordo per via delle detrazioni pensionati)
- ❌ Dimenticare il beneficio fiscale immediato del contributo volontario al fondo (per RAL nel secondo scaglione, con €800 di contributo datore: (€5.300 − €800) × 33% = €1.485 di risparmio IRPEF annuo)
- ❌ Confondere "comparto garantito" con "investimento sicuro": il garantito ha rendimento atteso 1-2% lordo, sotto inflazione media → erosione del potere d'acquisto
- ❌ Raccomandare di non aderire a fondo pensione "perché non si fida" senza quantificare il costo opportunità
- ❌ Trattare l'opzione capitale al pensionamento (max 50% del montante, art. 11 c. 3; il 100% solo se la rendita sul 70% del montante è sotto il 50% dell'assegno sociale) come reddito pensionistico — è patrimonio, va gestito separatamente
- ❌ Dimenticare il contributo datore di lavoro: è "soldi gratis" se previsto dal CCNL e si attiva solo aderendo
- ❌ Ignorare che per dipendenti pubblici (Cassa CPDEL, CPI, ecc.) le regole sono **diverse** — questa skill NON li copre

## Riferimenti

- `references/previdenza-obbligatoria.md` — sistema contributivo INPS, tabella coefficienti, requisiti accesso pensione, tassazione assegno
- `references/previdenza-complementare.md` — forme (negoziale/aperto/PIP), conferimento TFR, deduzione €5.300, comparti, tassazione fondi
- `references/proiezione-tenore-vita.md` — metodologia gap analysis, parametri scenari, strategie di copertura
- `references/montecarlo-pensione.md` — la dimensione **stocastica** della proiezione: perché i due pilastri hanno rischi opposti (il pubblico INPS è rivalutato al PIL, non al mercato → àncora deterministica; il fondo pensione è esposto al mercato → Monte Carlo), e la lettura onesta che ne segue (tutta la dispersione del tasso di sostituzione viene dal complementare)
- `references/integrazione-fiscale-joint.md` — pattern fiscali joint con `it-tax-optimization`: allocazione risparmio extra, realizzo plus + deduzione fondo, sterilizzazione redditi alti
- `assets/proiezione-pensione.xlsx` — template Excel editabile con 5 fogli (Input, Coefficienti, Pubblica, Complementare, Scenari), in euro di oggi, deterministico, con coefficiente proiettato all'anno di pensionamento e cella dedicata per il **montante INPS reale da estratto conto** (con stima di ripiego migliorata se assente)
- `assets/montecarlo-pensione.py` — il **Monte Carlo** del tasso di sostituzione: àncora l'INPS al valore deterministico del foglio e simula solo il fondo pensione via block bootstrap sulla serie storica USA nominale in dollari (Damodaran), di cui di default usa solo la forma: la media è ricentrata sul rendimento reale del comparto; con `RICENTRA_MEDIA = False` la serie si deflaziona anno per anno (stesso motore di obiettivi). Restituisce i percentili del tasso di sostituzione, la probabilità di una soglia obiettivo, e la decomposizione àncora-pubblica / banda-di-mercato-complementare. Richiede numpy; usa `rendimenti-storici.csv`
- `assets/rendimenti-storici.csv` — serie annuale azionario/obbligazionario (Damodaran/NYU Stern, 1928–2025) per il bootstrap; sostituibile con una propria serie

## Note per iterazione (v0.4)

Questa è la versione 0.11 della skill (introdotta in v0.4 del plugin, estesa in v0.8.11).

In quest'iterazione (v0.11):
- **Pipeline `--json <file>`** su tutta la catena previdenziale (`proiezione-inps`, `montecarlo-pensione`, `netto-pensione`, `ponte-pensione`): i risultati chiave si scrivono anche in JSON, così passano da uno script all'altro senza travasi a mano. Componibile con `--set`.
- **Freshness fiscale**: i dati normativi negli script e nelle reference portano il marcatore `Verificato: AAAA-MM`; la test suite fallisce se un marcatore supera i 12 mesi — i dati fiscali scadono per design, e la suite obbliga a riverificarli.

In quest'iterazione (v0.10):
- **`ponte-pensione.py`** — risponde a "posso smettere a X anni?": Monte Carlo del capitale-ponte dall'uscita anticipata all'età di copertura, sulla serie storica USA deflazionata anno per anno con l'inflazione USA perché la spesa è in euro di oggi (probabilità di successo + capitale necessario per confidenza via bisezione sugli stessi percorsi), **RITA integrata** (D.Lgs. 252/2005 art. 11 co. 4, requisiti verificati su COVIP/AdE: 5 anni dalla vecchiaia con ≥20 anni di contributi e ≥5 di complementare; 10 anni se inoccupati >24 mesi; tassazione 15%→9%), e — la parte che i calcoli ingenui omettono — i **costi permanenti** dell'uscita: contributi INPS mancati, versamenti al fondo fermi e montante consumato in RITA, tradotti in euro/anno di pensione persa per sempre. La quota di montante da destinare alla RITA è parametrica: calibrarla sulla spesa (invece di usare tutto) preserva rendita a 69. Supporta `--set`.

In quest'iterazione (v0.9):
- **`netto-pensione.py`** — dal tasso di sostituzione LORDO a quello NETTO/NETTO: IRPEF 2026 a tre scaglioni (23/33/43, secondo scaglione ridotto dalla L.199/2025 — verificato), detrazioni pensione e lavoro dipendente (art. 13 TUIR, dal 2027 art. 13 D.Lgs. 117/2026), contributi IVS 9,19%, addizionali parametriche, e imposta sostitutiva sulla rendita complementare 15%→9% con l'anzianità di partecipazione (art. 11 c. 6 D.Lgs. 252/2005; dal 2027 art. 258 c. 4 D.Lgs. 117/2026). Accetta più scenari di rendita (P10/P50/P90 dal Monte Carlo) e confronta pensione netta / ultimo stipendio netto. Il lordo sottostima sistematicamente la copertura: sul caso reale validato, la mediana passa dal 74,6% lordo al 97,5% netto. Supporta `--set`.

In quest'iterazione (v0.8):
- **Override `--set NOME=VALORE`** (via `motore_bootstrap.applica_override`): le costanti in testa a `montecarlo-pensione.py` e `proiezione-inps.py` si sovrascrivono da riga di comando senza modificare i file — es. `python proiezione-inps.py --set PIL_REALE=0.0 --set COEFF_ESPLICITO=0.048`. I nomi inesistenti vengono respinti (protezione dai refusi), gli override applicati sono stampati (run documentato e ripetibile).

In quest'iterazione (v0.7):
- **Motore bootstrap condiviso** (`motore_bootstrap.py`): `carica_storico`, campionamento a blocchi circolari (`indici_bootstrap`/`blocchi_bootstrap`) e percentili vivono in un modulo unico, copia sincronizzata con `it-pianificazione-obiettivi` (l'identità è verificata dalla test suite). `montecarlo-pensione.py` lo importa; refactor validato bit-per-bit: con lo stesso seed produce output identico alla versione precedente.

In quest'iterazione (v0.6):
- **`importa-previdenza.py`**: ingestione dei dati previdenziali reali — parser dell'estratto conto INPS (XML) e dello storico movimenti del fondo pensione (CSV, tollerante su separatori e formato numerico italiano), ricostruzione del montante contributivo coi tassi di capitalizzazione ufficiali (tabella verificata: floor a 1,0 nel 2021 post-COVID, recupero 2022, fino a 1,040445 per decorrenze 2026), montante fondo per comparto e stima euristica del mix azionario (keyword specifiche prima delle generiche: "obbligazionar" prima di "azionar"). Validato su estratto e storico reali.
- **`proiezione-inps.py`**: proiezione parametrica della pensione INPS in termini reali, con tabella coefficienti di trasformazione 2025-26 (DM 436/2024), riduzione parametrica per speranza di vita e sensibilità 3×3 (PIL reale × coefficienti). Chiude la catena: importatore → proiezione INPS → Monte Carlo del fondo, senza calcoli a mano.

In quest'iterazione (v0.5):
- **Crescita reale dei versamenti** nel Monte Carlo pensione (`CRESCITA_VERSAMENTO_REALE`): TFR e contributi crescono con lo stipendio, invece di restare costanti. Serve a proiettare in modo realistico chi prevede una progressione di carriera — e fa emergere l'effetto chiave: una RAL crescente *abbassa* il tasso di sostituzione (la pensione contributiva, basata sulla media dei versamenti di una vita, sostituisce una quota minore di uno stipendio finale più alto). Validato su caso reale.

In quest'iterazione (v0.4):
- **Monte Carlo del tasso di sostituzione** (`assets/montecarlo-pensione.py` + `references/montecarlo-pensione.md`): la proiezione non è più solo deterministica. Il punto metodologico è trattare i due pilastri secondo il loro rischio reale — l'INPS pubblico è rivalutato al PIL (àncora deterministica), il fondo pensione è esposto al mercato (Monte Carlo via block bootstrap, stesso motore di obiettivi). La lettura onesta che ne emerge: tutta la dispersione del tasso di sostituzione viene dal complementare, ed è lì che la scelta del comparto conta. Validato contro replica indipendente (mediana sotto il deterministico per il volatility drag, percentili coerenti).

In quest'iterazione (v0.3):
- **Accuratezza del montante INPS iniziale**: input del montante reale da estratto conto + stima di ripiego migliorata (serie geometrica che tiene conto di crescita salariale e rivalutazione passate). Era l'unica approssimazione nota dichiarata della skill. Validato su tre rami (montante reale fornito, caso limite riv=g che ritorna alla stima grezza, riv>g che la corregge al rialzo).

Versioni precedenti:
- v0.2: coefficiente di trasformazione proiettato in calo all'anno di pensionamento; integrazione fiscale joint con `it-tax-optimization`
- v0.1: dipendenti privati INPS, proiezione deterministica con scenari, Excel a 5 fogli

Limiti dell'iterazione corrente:
- Solo dipendenti privati italiani (non pubblici)
- Il foglio Excel resta deterministico; la dimensione stocastica è nello script Monte Carlo (`montecarlo-pensione.py`), limitata al pilastro complementare — il pubblico INPS è àncora deterministica per scelta metodologica (rivalutato al PIL, non al mercato)
- Solo regime pubblico INPS (non casse professionali → `it-pianificazione-autonomi`)

Roadmap:
- ✅ Lavoratori autonomi/forfettari → coperti dalla skill dedicata `it-pianificazione-autonomi`
- ✅ Accuratezza del montante INPS iniziale → fatto in v0.3 (estratto conto reale + stima migliorata)
- Dipendenti pubblici (TFS, regimi specifici)
- ✅ Monte Carlo per scenari di rendimento → fatto in v0.4 (`montecarlo-pensione.py`, due pilastri: complementare stocastico, pubblico àncora)
- Integrazione completa con it-tax-optimization (ottimizzazione joint IRPEF + finanziaria)
- Ricongiunzione, totalizzazione, riscatto laurea (richiedono dati INPS reali)
