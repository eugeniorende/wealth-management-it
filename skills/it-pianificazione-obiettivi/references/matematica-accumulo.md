# Matematica del piano di accumulo

Questa reference contiene le formule per calcolare quanto risparmiare per raggiungere un obiettivo, il trattamento dell'inflazione, esempi worked e la logica di riconciliazione quando gli obiettivi sono più di uno e le risorse non bastano.

## Le tre domande del piano di accumulo

1. **Quanto devo versare al mese** per raggiungere un obiettivo, dato un rendimento atteso?
2. **Quale rendimento mi serve** per raggiungere un obiettivo, data una capacità di versamento fissa?
3. **Quanto raggiungo** con un dato versamento e rendimento, su un dato orizzonte?

La più usata è la prima. Tutte ruotano attorno alla formula del valore futuro.

## Le formule

### Aggiustamento del target per l'inflazione

Se l'obiettivo è espresso in € di oggi, va proiettato a valore nominale alla scadenza:

```
target_nominale = target_oggi × (1 + inflazione)^anni
```

Esempio: €40.000 di oggi, tra 6 anni, inflazione 2% → 40.000 × 1,02^6 = **€45.047**. Servono €45.047 nominali tra 6 anni per avere il potere d'acquisto di €40.000 oggi.

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

### Rendimento richiesto (la domanda 2)

Non ha forma chiusa: si risolve numericamente (in Excel è la funzione `RATE`/`TASSO`, oppure per tentativi). Serve quando l'utente ha una capacità di versamento fissa e vuole sapere se è raggiungibile con un profilo a rischio accettabile, o se l'obiettivo richiede un rendimento (e quindi un rischio) troppo alto.

⚠️ Se il rendimento richiesto è molto alto (es. > 7-8% netto), è un campanello: l'obiettivo non è raggiungibile con un rischio ragionevole su quell'orizzonte. Le opzioni diventano: allungare l'orizzonte, ridurre il target, o aumentare il versamento — NON prendere più rischio del dovuto inseguendo un rendimento improbabile.

## Esempi worked

### Esempio 1 — Anticipo casa (medio termine)

- Target: €40.000 (di oggi) · Orizzonte: 6 anni · Già accantonato: €5.000
- Profilo: moderato → rendimento atteso 3,5% netto · Inflazione: 2%

```
target_nominale = 40.000 × 1,02^6 = 45.047
crescita del capitale iniziale = 5.000 × 1,035^6 = 6.146
da accumulare con i versamenti = 45.047 − 6.146 = 38.901

r_m = 1,035^(1/12) − 1 = 0,002871
N = 72
fattore rendita = (1,002871^72 − 1) / 0,002871 = 79,87

PMT = 38.901 / 79,87 = €487/mese
```

→ Servono circa **€487/mese** per 6 anni.

### Esempio 2 — Fondo di emergenza (liquidità, no rendimento)

- Target: 6 mesi × €2.000 di spese = €12.000 · Costruirlo in 2 anni · Rendimento ~0% (liquidità)

```
PMT ≈ 12.000 / 24 = €500/mese
```

→ Circa **€500/mese** per 2 anni. (Gli interessi del conto deposito sono trascurabili ai fini del piano; il fondo serve per la sicurezza, non per il rendimento.)

### Esempio 3 — Obiettivo a lungo termine (la forza del tempo)

- Target: €100.000 (di oggi) · Orizzonte: 20 anni · Già accantonato: €0
- Profilo: crescita → rendimento atteso 5% netto · Inflazione: 2%

```
target_nominale = 100.000 × 1,02^20 = 148.595
r_m = 1,05^(1/12) − 1 = 0,004074
N = 240
fattore rendita = (1,05^20 − 1) / 0,004074 = 405,8

PMT = 148.595 / 405,8 = €366/mese
```

→ Bastano circa **€366/mese** per 20 anni per avere il potere d'acquisto di €100.000 di oggi. È la dimostrazione di quanto contino tempo e capitalizzazione composta: lo stesso €100k su 6 anni richiederebbe oltre €1.200/mese.

## Riconciliazione multi-obiettivo

Quando gli obiettivi sono più di uno, si sommano i versamenti necessari e si confrontano con la capacità di risparmio.

### Esempio di riconciliazione

Capacità di risparmio: **€1.200/mese**. Obiettivi:

| Obiettivo | Versamento/mese | Durata |
|---|---|---|
| Fondo emergenza | €500 | 2 anni (poi si libera) |
| Anticipo casa | €487 | 6 anni |
| Lungo termine | €366 | 20 anni |
| **Totale** | **€1.353** | |

Totale €1.353 > capacità €1.200 → **gap di €153/mese**. Come si chiude:

**La chiave: gli obiettivi a breve si completano e liberano capacità.** Il fondo di emergenza assorbe €500/mese ma solo per 2 anni; poi quei €500 si liberano. Quindi la sequenza ottimale non è "tutto in parallelo da subito", ma:

```
Anni 1-2:  Fondo emergenza (€500) + Lungo termine (€366) + parte casa (€334)
           = €1.200 (capacità piena). La casa parte sottofinanziata.
Anno 3+:   Liberati i €500 dell'emergenza → redirigere su casa e lungo termine
           Ora casa (€487+) e lungo termine (€366) stanno comodamente in €1.200
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
2. **Usare il rendimento atteso del profilo**, non un rendimento ottimistico: meglio un piano prudente che si rivela facile che uno aggressivo che fallisce.
3. **Sfruttare la sequenza temporale**: gli obiettivi a breve liberano capacità quando si completano; pianificare in sequenza, non solo in parallelo.
4. **Segnalare i rendimenti richiesti irrealistici**: se un obiettivo richiede > 7-8% netto, dirlo chiaramente e proporre di allungare/ridurre invece di inseguire rischio eccessivo.
5. **Debiti cari prima degli investimenti discrezionali**: quantificare il "rendimento garantito" dell'estinzione.
6. **Comunicare i rendimenti come range, non come certezze**: le proiezioni deterministiche danno un numero, ma la realtà è una distribuzione. Dirlo sempre.
7. **Il piano è sostenibile o non è un piano**: se i versamenti necessari eccedono cronicamente la capacità, rivedere obiettivi e orizzonti invece di assumere una disciplina di risparmio irrealistica.
