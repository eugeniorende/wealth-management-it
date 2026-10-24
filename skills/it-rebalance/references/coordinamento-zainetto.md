# Coordinamento ribilanciamento + zainetto fiscale

Questa reference definisce il **protocollo operativo** per usare insieme `it-rebalance` e `it-tax-optimization`, in particolare per il ribilanciamento di fine anno, dove le due skill si rinforzano a vicenda.

## Indice

- Perché coordinarle
- Il problema dello zainetto in scadenza
- Protocollo operativo (sequenza)
- Esempio numerico coordinato
- Caveat e regole
- Quando NON coordinare

## Perché coordinarle

Le due skill ottimizzano cose diverse ma sullo **stesso atto** (la vendita):
- `it-tax-optimization` ragiona su: *quali minus sto per perdere? quali plus posso compensare?*
- `it-rebalance` ragiona su: *quali posizioni sono sovrappeste e vanno ridotte?*

Quando una vendita serve a **entrambi** gli scopi (ribilanciare E gestire lo zainetto), il valore è massimo: si corregge il drift e si ottimizza la fiscalità in un colpo solo. Il momento naturale è **novembre-dicembre**, prima della chiusura dell'anno fiscale.

## Il problema dello zainetto in scadenza

Le minusvalenze in regime amministrato durano **4 anni** (fino al 31/12 dell'anno N+4). Una minus formata nel 2022 evapora il 1° gennaio 2027 se non compensata.

Se l'utente ha:
- **Zainetto in scadenza** (minus 2022 che muore a fine 2026)
- **Posizioni in plus** che andrebbero comunque ridotte per ribilanciare

…allora vendere quelle posizioni in plus a fine 2026 **compensa la minus prima che scada** e contemporaneamente ribilancia. La plusvalenza che normalmente sarebbe tassata al 26% viene azzerata dalla compensazione. È un doppio beneficio.

## Protocollo operativo (sequenza)

### Fase 1 — Inventario fiscale (it-tax-optimization)

Prima di tutto, mappare con `it-tax-optimization`:

```
1. Zainetto disponibile per broker, con anno di formazione e scadenza
2. Quali minus scadono a fine anno corrente (le più urgenti)
3. Plus latenti per categoria fiscale (reddito_diverso compensabile vs
   reddito_capitale non compensabile)
```

Output: "Hai €X di zainetto, di cui €Y in scadenza il 31/12. Le tue posizioni in plus su redditi diversi ammontano a €Z compensabili."

### Fase 2 — Misura del drift (it-rebalance)

Parallelamente, con `it-rebalance`:

```
1. Drift attuale vs target
2. Posizioni sovrappesate (candidate alla vendita)
3. Di queste, quali sono in plus e di che categoria fiscale
```

Output: "Devi ridurre l'azionario di €W. Le posizioni azionarie sovrappesate sono [...]."

### Fase 3 — Intersezione (il piano coordinato)

Trovare le posizioni che sono **sia sovrappesate (da vendere per ribilanciare) sia in plus compensabile (utili per usare lo zainetto in scadenza)**:

```
candidati_ottimali = posizioni che sono:
    - sovrappesate (drift positivo oltre banda)  [da it-rebalance]
    - in plus latente                            [da entrambe]
    - categoria reddito_diverso (compensabile)   [da it-tax-optimization]

per candidato in candidati_ottimali:
    vendita = min(
        importo_da_vendere_per_ribilanciare,
        zainetto_in_scadenza_disponibile / (plus_per_euro_venduto × coeff)
    )
    # plus_per_euro_venduto = plus latente / controvalore (sul prezzo medio di carico)
    # coeff = 1 al 26%; 0,4808 per titoli di Stato e white list al 12,5%, la cui plus
    # consuma lo zainetto al 48,08% (art. 6 c. 1 D.Lgs. 461/97 → art. 306 c. 1 TU 2027,
    # nel testo dell'art. 3 c. 5 DL 66/2014)
    → questa vendita ribilancia E consuma zainetto in scadenza
    → tassa netta = 0 (compensata) fino a esaurimento zainetto
```

### Fase 4 — Sequenza di esecuzione

Ordine consigliato delle vendite di fine anno:

```
1. PRIMA: vendi le posizioni sovrappesate in plus su reddito_diverso,
   fino a consumare lo zainetto in scadenza
   → ribilancia + compensa minus morente, tassa zero: è una correzione a costo
     zero, quindi va fino al target già oltre la banda stretta

2. POI: se serve ancora ribilanciare e lo zainetto in scadenza è esaurito,
   valuta:
   a. posizioni sovrappesate in minus (Leva 3) → crea nuovo zainetto
   b. posizioni sovrappesate in plus che pagano imposta (Leva 4): solo se il drift
      della classe supera la banda larga (×2 la 5/25), e solo fino a metà banda;
      altrimenti si rinvia e il residuo si dichiara con il suo costo (bande-dinamiche.md)

3. INFINE: reinvesti i ricavati nelle classi sottopesate
```

## Esempio numerico coordinato

**Setup (novembre 2026)**:
- Zainetto: €3.000 di minus formate nel 2022 → **scadono il 31/12/2026**
- Portafoglio €120.000, azionario sovrappeso del +7% (€8.400 in eccesso, fuori banda)
- Posizione azionaria sovrappesata: **azioni italiane del FTSE MIB detenute direttamente (reddito diverso)** con €15.000 di controvalore e +€4.000 di plus latente

**Senza coordinamento** (ribilanciare a gennaio 2027):
```
Lo zainetto 2022 (€3.000) evapora il 1/1/2027 → perso
A gennaio la correzione pagherebbe imposta: vendere €8.400 di azioni FTSE MIB
  realizza €8.400 × (4.000/15.000) = €2.240 di plus → tassa 26% = €582
  (fino a metà banda: €5.400 venduti, plus €1.440, tassa €374)
Il drift +7% è sotto la banda larga (10%): la vendita tassata si rinvia,
  il residuo di €8.400 si dichiara con il suo costo e il drift resta aperto
  finché versamenti o flussi non lo correggono
COSTO: drift non corretto + €3.000 di zainetto buttato
```

**Con coordinamento** (ribilanciare a dicembre 2026):
```
A dicembre vendo €8.400 di azioni FTSE MIB per ribilanciare
  plus realizzata = €2.240 (reddito diverso, compensabile)
  compensazione con zainetto 2022: €2.240 compensati (su €3.000 disponibili)
  tassa = €0 (interamente compensata)
  
  Lo zainetto residuo (€760) può compensare altre plus entro il 31/12/2026
  
Reinvesto €8.400 nell'obbligazionario sottopeso
COSTO: €0 di tasse, zainetto sfruttato invece che perso
```

**Vantaggio del coordinamento: il drift si corregge subito, fino al target, a costo zero, e si usano €2.240 dei €3.000 di zainetto prima che evaporino.** La plus realizzata a dicembre non paga i €582 che costerebbe realizzarla più avanti senza zainetto; il residuo di €760 resta disponibile per altre plus entro il 31/12. Stesso ribilanciamento, tempistica diversa, e l'uso congiunto delle due skill.

## Caveat e regole

- ⚠️ **La compensazione è per-broker**: lo zainetto e le plus devono stare sullo stesso intermediario. Se la posizione sovrappesata da vendere è su un broker diverso da quello dove c'è lo zainetto in scadenza, non c'è compensazione automatica (vedi `it-tax-optimization/references/multi-intermediario.md`).
- ⚠️ **Solo reddito diverso compensa**: se la posizione sovrappesata in plus è un ETF UCITS armonizzato, la sua plus è reddito di capitale e **non** compensa lo zainetto. In quel caso il coordinamento non aiuta: meglio cercare un'altra posizione sovrappesata su reddito diverso, o accettare che la vendita di quella posizione paghi la tassa piena, con le regole della Leva 4: solo oltre la banda larga e fino a metà banda.
- ⚠️ **Non forzare il ribilanciamento solo per usare lo zainetto**: se il portafoglio è dentro banda, non vendere solo per compensare. Per il puro uso dello zainetto in scadenza senza ribilanciamento, è `it-tax-optimization` a gestirlo (può suggerire vendita + riacquisto immediato dello stesso strumento, legittimo in Italia, per realizzare plus compensabile senza cambiare l'allocazione).
- ⚠️ **Cut-off operativo**: le vendite vanno eseguite con valuta entro il 31/12. Considerare i tempi di regolamento (T+2 sui mercati azionari) — una vendita il 30/12 potrebbe regolare nel nuovo anno. Verificare il cut-off del broker, tipicamente metà dicembre per sicurezza.

## Quando NON coordinare

- Se non c'è zainetto in scadenza → il ribilanciamento segue la sua gerarchia di leve normale, senza urgenza fiscale di fine anno.
- Se il portafoglio è dentro banda → non ribilanciare; per lo zainetto in scadenza usa `it-tax-optimization` in modo indipendente (vendita+riacquisto per realizzare plus compensabile senza alterare l'allocazione).
- Se le posizioni sovrappesate sono tutte ETF UCITS armonizzati in plus → non c'è compensazione possibile; il coordinamento non offre vantaggi.
