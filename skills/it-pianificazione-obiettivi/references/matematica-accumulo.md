# Matematica del piano di accumulo

Questa reference contiene le formule per calcolare quanto risparmiare per raggiungere un obiettivo, il trattamento dell'inflazione, il glide path nel versamento, esempi worked e la logica di riconciliazione quando gli obiettivi sono più di uno e le risorse non bastano. Gli esempi usano i parametri del pianificatore Excel (`assets/pianificatore-obiettivi.xlsx`), quindi i numeri coincidono con quelli del foglio.

## Le tre domande del piano di accumulo

1. **Quanto devo versare al mese** per raggiungere un obiettivo, dato un rendimento atteso?
2. **Quale rendimento mi serve** per raggiungere un obiettivo, data una capacità di versamento fissa?
3. **Quanto raggiungo** con un dato versamento e rendimento, su un dato orizzonte?

La più usata è la prima. Tutte ruotano attorno alla formula del valore futuro.

## Le convenzioni sui rendimenti

I rendimenti dei profili (foglio Parametri) sono:

- **nominali**: il target si proietta con l'inflazione, il rendimento la include;
- **netti di costi e imposte**: TER, bollo e imposte sui rendimenti sono già tolti, come se si pagassero ogni anno. Dal rendimento lordo atteso di un portafoglio si passa al netto da inserire con **netto ≈ (lordo − costi) × (1 − 26%)**: per esempio un lordo del 7,8% con costi dello 0,4% dà circa il 5,5% netto. È un'approssimazione prudente, perché negli ETF ad accumulazione l'imposta si paga solo alla vendita (e sulla quota in titoli di Stato è il 12,5%). Con questa convenzione il versamento non si sottostima: l'imposta alla scadenza è già scontata nel rendimento. L'unico strumento che riparte dal lordo è l'ottimizzatore di asset location, che toglie costi e imposte contenitore per contenitore (`asset-location-optimizer.py`, conversione inversa esplicita);
- **medie aritmetiche annue attese**: il Monte Carlo le usa come media dei rendimenti di ciascun anno, quindi la crescita composta mediana è circa rendimento − σ²/2 (vedi `monte-carlo.md`). Chi parte da rendimenti annualizzati (geometrici, come quelli del Global Investment Returns Yearbook) aggiunge σ²/2: col profilo Crescita (volatilità 13%) un 4,65% annualizzato corrisponde al 5,5% del foglio.

## Le formule

### Aggiustamento del target per l'inflazione

Se l'obiettivo è espresso in € di oggi, va proiettato a valore nominale alla scadenza:

```
target_nominale = target_oggi × (1 + inflazione)^anni
```

Esempio: €40.000 di oggi, tra 6 anni, inflazione 2% → 40.000 × 1,02^6 = **€45.046**. Servono €45.046 nominali tra 6 anni per avere il potere d'acquisto di €40.000 oggi.

### Valore futuro: capitale iniziale + versamenti

```
FV = PV × (1+r)^n  +  PMT × [ ((1+r_m)^N − 1) / r_m ]

dove:
  PV   = capitale già accantonato per l'obiettivo
  r    = rendimento annuo atteso (del profilo di allocazione)
  n    = anni all'obiettivo
  r_m  = rendimento mensile = (1+r)^(1/12) − 1
  N    = n × 12  (numero di versamenti mensili)
  PMT  = versamento mensile
```

### Versamento mensile necessario (la domanda 1)

Risolvendo per PMT:

```
PMT = ( target_nominale − PV × (1+r)^n ) / [ ((1+r_m)^N − 1) / r_m ]
```

È il versamento a **quota fissa**: vale per gli obiettivi che non de-riskano (i permanenti, come il fondo di emergenza, e i profili senza azionario).

### Il glide path nel versamento (obiettivi terminanti)

Un obiettivo che si spende a una data (casa, università) **de-riska** negli ultimi anni: la quota azionaria scende fino a 0% alla scadenza (`glide-path.md`), e con lei il rendimento atteso. Calcolare il versamento al rendimento pieno del profilo lo sottostima, di circa il 10% sugli orizzonti lunghi. Il foglio usa due fasi:

```
anni di de-risking  m = min(finestra, n) − 1     (Obiettivi!O; finestra in Parametri!B7)
anni a quota piena  k = n − m
rendimento in de-risking  r2 = (r + r_atterraggio) / 2     (Obiettivi!P; r_atterraggio = Preservazione)

FV = [PV × (1+r)^k + PMT × F(r, k)] × (1+r2)^m  +  PMT × F(r2, m)
F(r, a) = ((1+r)^a − 1) / ((1+r)^(1/12) − 1)      (12 × a se r = 0)
```

La quota dell'anno è quella del calendario a inizio anno (it-rebalance riallinea una volta l'anno): con la finestra di 7 anni la quota piena vale fino a 7 anni dalla scadenza, poi scende per 6 anni. Durante la rampa il rendimento atteso è lineare nella quota, quindi la sua media sulla rampa è a metà tra profilo e atterraggio. Rispetto al calcolo anno per anno questa formula sbaglia per difetto di meno dell'1,5%; Monte Carlo, glide path e allocatore usano la stessa (`motore_bootstrap.pmt_glide`), così il versamento è lo stesso numero ovunque.

### Rendimento richiesto (la domanda 2)

Non ha forma chiusa: si risolve numericamente (in Excel è la funzione `RATE`/`TASSO`, oppure per tentativi). Serve quando l'utente ha una capacità di versamento fissa e vuole sapere se è raggiungibile con un profilo a rischio accettabile, o se l'obiettivo richiede un rendimento (e quindi un rischio) troppo alto.

⚠️ Se il rendimento richiesto è molto alto (es. > 7-8% netto), è un campanello: l'obiettivo non è raggiungibile con un rischio ragionevole su quell'orizzonte. Le opzioni diventano: allungare l'orizzonte, ridurre il target, o aumentare il versamento — NON prendere più rischio del dovuto inseguendo un rendimento improbabile.

## Esempi worked

Sono i tre obiettivi d'esempio del pianificatore Excel (inflazione 2%, finestra di de-risking 7 anni).

### Esempio 1 — Anticipo casa (medio termine)

- Target: €40.000 (di oggi) · Orizzonte: 6 anni · Già accantonato: €5.000
- Profilo: Moderato → rendimento atteso 4,0% netto (40% azionario) · terminante

A quota fissa:

```
target_nominale = 40.000 × 1,02^6 = 45.046
crescita del capitale iniziale = 5.000 × 1,04^6 = 6.327
da accumulare con i versamenti = 45.046 − 6.327 = 38.719

r_m = 1,04^(1/12) − 1 = 0,003274
fattore rendita = (1,04^6 − 1) / 0,003274 = 81,04

PMT = 38.719 / 81,04 = €478/mese
```

Col glide path (6 anni: finestra effettiva 6, quindi 1 anno a quota piena e 5 di de-risking al 2,75%, la media tra 4,0% e l'1,5% della Preservazione):

```
crescita del capitale iniziale = 5.000 × 1,04 × 1,0275^5 = 5.955
fattore = F(4,0%, 1) × 1,0275^5 + F(2,75%, 5) = 12,22 × 1,1453 + 64,19 = 78,18

PMT = (45.046 − 5.955) / 78,18 = €500/mese
```

→ Servono circa **€500/mese** per 6 anni: il de-risking che protegge l'anticipo costa €22 al mese rispetto ai €478 a quota fissa.

### Esempio 2 — Fondo di emergenza (liquidità)

- Target: 6 mesi × €2.000 di spese = €12.000 · Costruirlo in 2 anni · Profilo Preservazione 1,5% · permanente (non de-riska)

```
target_nominale = 12.000 × 1,02^2 = 12.485
fattore rendita = (1,015^2 − 1) / (1,015^(1/12) − 1) = 24,35

PMT = 12.485 / 24,35 = €513/mese
```

→ Circa **€513/mese** per 2 anni (a rendimento zero e senza inflazione sarebbero €500: interessi e inflazione quasi si compensano). Il fondo serve per la sicurezza, non per il rendimento.

### Esempio 3 — Obiettivo a lungo termine (la forza del tempo)

- Target: €100.000 (di oggi) · Orizzonte: 20 anni · Già accantonato: €0
- Profilo: Crescita → rendimento atteso 5,5% netto (65% azionario) · terminante

A quota fissa:

```
target_nominale = 100.000 × 1,02^20 = 148.595
r_m = 1,055^(1/12) − 1 = 0,004472
fattore rendita = (1,055^20 − 1) / 0,004472 = 428,9

PMT = 148.595 / 428,9 = €346/mese
```

Col glide path (14 anni a quota piena, 6 di de-risking al 3,5%):

```
fattore = F(5,5%, 14) × 1,035^6 + F(3,5%, 6) = 249,6 × 1,2293 + 79,9 = 386,7

PMT = 148.595 / 386,7 = €384/mese
```

→ Bastano circa **€384/mese** per 20 anni per avere il potere d'acquisto di €100.000 di oggi. Il de-risking finale pesa per l'11% sul versamento (€384 contro €346): ignorarlo lascerebbe l'obiettivo sotto-finanziato di circa il 10%. Resta la dimostrazione di quanto contino tempo e capitalizzazione composta: lo stesso €100k su 6 anni richiederebbe oltre €1.300/mese.

## Riconciliazione multi-obiettivo

Quando gli obiettivi sono più di uno, si sommano i versamenti necessari e si confrontano con la capacità di risparmio.

### Esempio di riconciliazione

Capacità di risparmio: **€1.200/mese**. Obiettivi (i versamenti del foglio, glide path compreso):

| Obiettivo | Versamento/mese | Durata |
|---|---|---|
| Fondo emergenza | €513 | 2 anni (poi si libera) |
| Anticipo casa | €500 | 6 anni |
| Lungo termine | €384 | 20 anni |
| **Totale** | **€1.397** | |

Totale €1.397 > capacità €1.200 → **gap di €197/mese**. Come si chiude:

**La chiave: gli obiettivi a breve si completano e liberano capacità.** Il fondo di emergenza assorbe €513/mese ma solo per 2 anni; poi quei €513 si liberano. Quindi la sequenza ottimale non è "tutto in parallelo da subito", ma:

```
Anni 1-2:  Fondo emergenza (€513) + Lungo termine (€384) + parte casa (€303)
           = €1.200 (capacità piena). La casa parte sottofinanziata.
Anno 3+:   Liberati i €513 dell'emergenza → redirigere su casa e lungo termine
           Ora casa (€500+) e lungo termine (€384) stanno comodamente in €1.200
```

In alternativa, o in aggiunta, le leve viste nello SKILL.md:
- **Allungare** l'orizzonte casa da 6 a 8 anni → il versamento mensile scende (più tempo, più capitalizzazione)
- **Ridurre** il target di un obiettivo desiderabile
- **Posticipare** l'obiettivo a priorità più bassa

### L'ordine di priorità (ribadito)

```
1. Fondo di emergenza         (sempre prima — è la fondazione)
2. Debiti ad alto interesse   (estinguere rende un "rendimento garantito"
                               pari al tasso del debito, spesso > di qualsiasi
                               investimento)
3. Contributo datore fondo pensione, se previsto dal CCNL  ("soldi gratis",
                               vedi it-pianificazione)
4. Obiettivi essenziali       (per orizzonte e profilo appropriati)
5. Obiettivi importanti
6. Obiettivi desiderabili
```

⚠️ **Il debito caro batte l'investimento**: estinguere un debito al 10% equivale a un investimento con rendimento garantito del 10% netto — difficile da battere sul mercato con certezza. Prima di investire per obiettivi discrezionali, estinguere i debiti cari (carte revolving, prestiti al consumo costosi). Fa eccezione il mutuo casa a tasso basso, che di solito non conviene estinguere anticipatamente rispetto a investire.

## Heuristic per la skill

1. **Sempre proiettare il target a nominale** con l'inflazione: ignorarla sottostima il versamento necessario.
2. **Usare il rendimento atteso del profilo, netto**, non un rendimento ottimistico: meglio un piano prudente che si rivela facile che uno aggressivo che fallisce.
3. **Includere il glide path** negli obiettivi terminanti: il de-risking finale abbassa il rendimento proprio quando il capitale è più grande.
4. **Sfruttare la sequenza temporale**: gli obiettivi a breve liberano capacità quando si completano; pianificare in sequenza, non solo in parallelo.
5. **Segnalare i rendimenti richiesti irrealistici**: se un obiettivo richiede > 7-8% netto, dirlo chiaramente e proporre di allungare/ridurre invece di inseguire rischio eccessivo.
6. **Debiti cari prima degli investimenti discrezionali**: quantificare il "rendimento garantito" dell'estinzione.
7. **Comunicare i rendimenti come range, non come certezze**: le proiezioni deterministiche danno un numero, ma la realtà è una distribuzione. Dirlo sempre.
8. **Il piano è sostenibile o non è un piano**: se i versamenti necessari eccedono cronicamente la capacità, rivedere obiettivi e orizzonti invece di assumere una disciplina di risparmio irrealistica.
