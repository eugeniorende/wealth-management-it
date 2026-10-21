# Fiscalità del forfettario e previdenza complementare

Questa reference affronta il tema fiscalmente più delicato e frainteso della pianificazione previdenziale per autonomi: **come il regime forfettario cambia (e spesso annulla) la convenienza fiscale del fondo pensione**.

## Come funziona il forfettario (L. 190/2014)

```
Step 1: reddito lordo forfettario
  reddito_lordo = ricavi_incassati × coefficiente_redditività

Step 2: deduzione contributi obbligatori (UNICA deduzione ammessa)
  reddito_imponibile = reddito_lordo − contributi_INPS_versati_nell'anno

Step 3: imposta sostitutiva
  imposta = reddito_imponibile × aliquota
  aliquota = 15% (ordinaria) oppure 5% (primi 5 anni se requisiti)
```

L'imposta sostitutiva **sostituisce**: IRPEF, addizionali regionali e comunali, IRAP. Il reddito forfettario **NON concorre** al reddito complessivo IRPEF.

### Coefficienti di redditività per codice ATECO

| Attività | Coefficiente |
|---|---|
| Professioni / attività scientifiche, tecniche, sanitarie (include **sviluppo software, consulenza IT**, ATECO 62.x, 70-74) | **78%** |
| Costruzioni e attività immobiliari | 86% |
| Intermediari del commercio | 62% |
| Commercio ambulante di prodotti non alimentari | 54% |
| Commercio (ingrosso e dettaglio) | 40% |
| Industrie alimentari e bevande | 40% |
| Servizi di alloggio e ristorazione | 40% |
| Altre attività economiche | 67% |

Per developer/consulenti IT il coefficiente è **78%**: il 78% dei ricavi è reddito tassabile, il 22% è abbattimento forfettario che rappresenta le "spese" riconosciute a forfait.

⚠️ I coefficienti del 40%, 54%, 62% e 86% (commercio e ambulanti, alimentari, ristorazione, intermediari, costruzioni e attività immobiliari) riguardano attività di solito iscritte alle gestioni INPS di artigiani e commercianti, che hanno contributi fissi sul minimale e sono fuori dal perimetro della skill. Decide la gestione di iscrizione, non il coefficiente: chiederla sempre e, se è artigiani o commercianti, rinviare a INPS o al commercialista.

### Requisiti 2026

- Ricavi anno precedente ≤ **€85.000** (uscita immediata al superamento di €100.000 in corso d'anno)
- Reddito da lavoro dipendente/pensione anno precedente ≤ **€35.000** (causa ostativa)
- Aliquota **5%** primi 5 anni se: nessuna attività d'impresa/professione nei 3 anni precedenti, e l'attività non è mera prosecuzione di lavoro dipendente/autonomo precedente

## Il nodo: la deducibilità dei contributi previdenziali

### Contributi INPS obbligatori → DEDUCIBILI

I contributi previdenziali **obbligatori** (Gestione Separata, o cassa) versati nell'anno si deducono dal reddito forfettario prima di applicare l'imposta sostitutiva. È l'**unica** deduzione ammessa nel forfettario (non si deducono affitto, attrezzature, bollette, ecc.).

```
Esempio: consulente IT, ricavi €40.000, coefficiente 78%
  reddito_lordo = 40.000 × 0,78 = 31.200
  contributi_INPS = 31.200 × 0,2607 = 8.134
  reddito_imponibile = 31.200 − 8.134 = 23.066
  imposta_sostitutiva (15%) = 23.066 × 0,15 = 3.460

  Senza dedurre i contributi: 31.200 × 0,15 = 4.680
  Risparmio dalla deduzione contributi: €1.220
```

⚠️ Dimenticare di dedurre i contributi obbligatori costa il 15% (o 5%) del loro ammontare in imposta non risparmiata. È un errore da non fare mai.

### Contributo VOLONTARIO al fondo pensione → NON DEDUCIBILE (per il forfettario puro)

Questo è il punto centrale. **Il contributo che versi volontariamente a un fondo pensione NON è deducibile** se sei un forfettario senza altri redditi IRPEF.

**Perché**:
- La deduzione del fondo pensione (art. 10, comma 1, lett. e-bis TUIR) opera sul **reddito complessivo IRPEF**
- Il reddito forfettario è tassato con imposta sostitutiva e **non concorre** al reddito complessivo IRPEF
- Quindi non c'è un reddito IRPEF da cui dedurre → la deduzione vale **zero**

Fonte: Modello Redditi PF 2026, quadro LM. La prassi dell'Agenzia delle Entrate conferma che per i forfettari i contributi volontari a fondo pensione non sono deducibili (mentre i contributi obbligatori sì, perché espressamente previsti dalla legge istitutiva del forfettario).

**Il contributo non dedotto non deve essere tassato due volte**: il forfettario puro deve **comunicare al fondo** i contributi non dedotti entro il 31/12 dell'anno successivo al versamento, o prima se matura il diritto alla prestazione (art. 8 c. 4 D.Lgs. 252/2005). Così in uscita quella parte è esente (art. 11 c. 6 D.Lgs. 252/2005; dal 2027 art. 258 c. 4 D.Lgs. 117/2026); senza comunicazione il fondo la tassa come se fosse stata dedotta. *(Verificato: 2026-10, Risposta AdE 154/2024.)*

**Conseguenza pratica enorme**: per un dipendente nel secondo scaglione IRPEF, versare €5.000 al fondo pensione fa risparmiare €1.650 di IRPEF (33%). Per un forfettario puro, gli stessi €5.000 fanno risparmiare **€0**. Il motore principale della convenienza del fondo pensione per i dipendenti **non gira** per i forfettari.

### L'eccezione: forfettario CON altri redditi IRPEF

Se il forfettario ha **anche** redditi soggetti a IRPEF — affitti tassati IRPEF (non cedolare secca), un lavoro dipendente part-time, redditi occasionali, ecc. — allora il contributo al fondo pensione **deduce da quei redditi IRPEF**, fino a capienza. Il risparmio pieno vale per redditi senza detrazioni proprie (affitti a IRPEF ordinaria): con un lavoro dipendente o redditi occasionali le detrazioni dell'art. 13 TUIR riducono già l'IRPEF, e quindi il risparmio, fino ad azzerarlo per redditi piccoli.

```
Esempio: forfettario IT con €30.000 di reddito forfettario
  + €12.000 di affitti tassati IRPEF (regime ordinario, non cedolare)

  Il contributo al fondo pensione (fino a €5.300) deduce dai €12.000 di affitti IRPEF
  Beneficio = contributo × aliquota IRPEF sui €12.000
  (i €12.000 di affitti, sommati ad altri eventuali redditi IRPEF, determinano lo scaglione)
```

⚠️ Se gli affitti sono a **cedolare secca** (21% o 10%), NON sono redditi IRPEF → niente capienza per la deduzione del fondo. Solo i redditi a tassazione IRPEF ordinaria creano capienza.

## Confronto fondo pensione vs ETF per un forfettario puro

Poiché per il forfettario puro il fondo pensione perde il vantaggio della deduzione, va confrontato **onestamente** con l'alternativa: un PAC di ETF su dossier titoli ordinario.

| Aspetto | Fondo pensione | PAC ETF (dossier ordinario) |
|---|---|---|
| Deduzione in ingresso | **€0** (forfettario puro) | €0 (mai prevista) |
| Tassazione rendimenti annui | 20% (12,5% titoli Stato) | 26% (12,5% titoli Stato), solo al realizzo |
| Tassazione in uscita | zero sui versamenti non dedotti comunicati al fondo; 15→9% solo su quelli dedotti; rendimenti esclusi (art. 11 c. 6 D.Lgs. 252/2005; dal 2027 art. 258 c. 4 D.Lgs. 117/2026) | 26% sulle plusvalenze (12,5% quota titoli Stato) |
| Liquidità prima della pensione | Vincolata (anticipazioni limitate) | Totale, in qualsiasi momento |
| Flessibilità | Bassa | Alta |
| Protezione patrimoniale | Alta (impignorabilità relativa) | Standard |
| Costi | ISC fondo (0,2-1,5% secondo forma) | TER ETF (0,1-0,3%) + bollo 0,2% |

**I due vantaggi residui del fondo pensione per il forfettario puro**:
1. **Uscita quasi esente**: i versamenti non dedotti, se comunicati al fondo, in uscita non sono tassati, e i rendimenti hanno già pagato il 20% (12,5% sui titoli di Stato) anno per anno senza un secondo prelievo. Sull'ETF il 26% colpisce tutta la plusvalenza al realizzo.
2. **Tassazione rendimenti più bassa nella fase di accumulo**: 20% nel fondo vs 26% sul dossier (ma sul dossier la tassazione è differita al realizzo, il che è un vantaggio compensativo per l'ETF ad accumulazione).

**Il vantaggio principale dell'ETF**: liquidità totale. Il forfettario, che ha redditi spesso più variabili del dipendente, può avere più bisogno di un cuscinetto liquido.

### Esempio numerico semplificato (orizzonte 25 anni, €3.000/anno)

```
Ipotesi: €3.000/anno per 25 anni, rendimento lordo 5%

Versamenti a fine anno, valori nominali.

FONDO PENSIONE (forfettario puro, no deduzione):
  Deduzione: €0
  Montante a 25 anni (rendimento netto ~4% dopo la tassa annua del 20%): ~€125.000
  Tassa in uscita, se i €75.000 non dedotti sono comunicati al fondo: €0
    (i rendimenti sono già tassati, i contributi non dedotti sono esclusi)
  Netto: ~€125.000
  Senza comunicazione: 12% (25 anni di partecipazione) su €75.000 = ~€9.000 → ~€116.000

ETF ACCUMULAZIONE (dossier ordinario):
  Nessuna deduzione (mai prevista)
  Montante lordo a 25 anni (rendimento 5% lordo, tassazione differita): ~€143.000
  Plusvalenza ~€68.000, tassata 26% al realizzo: ~€17.700
  Meno bollo 0,2%/anno cumulato: ~€3.000
  Netto: ~€122.000
```

In questo esempio stilizzato, per il **forfettario puro** che comunica i non dedotti il fondo (~€125.000) supera di poco l'ETF ad accumulazione (~€122.000); se non li comunica scende a ~€116.000 e resta indietro. Il margine è piccolo:
- il fondo non offre la deduzione (che per il dipendente allargherebbe molto il divario)
- la tassazione differita dell'ETF ad accumulazione compensa buona parte della sua aliquota più alta
- costi del fondo (ISC) e dell'ETF (TER e bollo) possono spostare il risultato da una parte o dall'altra

⚠️ Questo confronto è **stilizzato e sensibile alle ipotesi** (rendimenti, costi, aliquota finale, orizzonte). Non è una raccomandazione: serve a mostrare che, per il forfettario puro, il fondo pensione **non è automaticamente la scelta migliore** come lo è per il dipendente. La decisione dipende da liquidità desiderata, costi effettivi del fondo scelto, orizzonte, e priorità personali. Va valutata caso per caso.

### Quando il fondo pensione conviene comunque al forfettario puro

- Se sceglie un fondo **negoziale a costi bassissimi** (ISC 0,2-0,5%) e comunica ogni anno i non dedotti, l'uscita esente e la tassazione annua più bassa possono prevalere
- Se vuole **vincolarsi** per disciplina (il vincolo di illiquidità è un "vantaggio comportamentale" per chi farebbe fatica a non toccare i risparmi)
- Se valorizza la **protezione patrimoniale** (impignorabilità relativa)
- Se prevede di passare in futuro a un **regime IRPEF** (ordinario, o lavoro dipendente), recuperando la deducibilità

## Confronto regime forfettario vs ordinario (cenni)

Il passaggio da forfettario a ordinario è una valutazione fiscale complessa. Ai fini di questa skill, i punti previdenziali rilevanti:

- **Forfettario**: imposta sostitutiva 15%/5%, deduzione solo contributi obbligatori, fondo pensione non deducibile (se reddito puro forfettario)
- **Ordinario**: IRPEF progressiva, deduzione di tutti i costi reali E del fondo pensione (fino a €5.300), ma aliquote IRPEF più alte (23-43%) e addizionali

Per chi ha **costi reali elevati** o vuole **dedurre il fondo pensione**, l'ordinario può convenire. Per chi ha pochi costi e reddito medio, il forfettario è quasi sempre più leggero. È una valutazione da **commercialista**, non automatizzabile: dipende da costi, redditi collaterali, prospettive di crescita, e dall'orizzonte temporale.

## Heuristic per la skill

1. **MAI dire a un forfettario che il fondo pensione "fa risparmiare tasse"**: per il forfettario puro è falso. Spiegare il perché (imposta sostitutiva ≠ IRPEF).
2. **Verificare se il forfettario ha altri redditi IRPEF**: se sì, il fondo pensione deduce fino a capienza di quelli. Chiederlo esplicitamente.
3. **Distinguere cedolare secca da IRPEF**: gli affitti a cedolare secca NON creano capienza per la deduzione; quelli a IRPEF ordinaria sì.
4. **Ricordare la deducibilità dei contributi obbligatori**: quelli SÌ si deducono dal forfettario (unica deduzione). Non dedurli è un errore costoso.
5. **Presentare il confronto fondo vs ETF onestamente**: per il forfettario puro non c'è una risposta univoca; dipende da liquidità, costi, orizzonte.
6. **Coefficiente 78% per IT/professioni**: usarlo come default per developer/consulenti, ma confermare il codice ATECO.
7. **Rinviare al commercialista** per la scelta del regime: è una valutazione complessa, non un calcolo meccanico.
