# Gerarchia delle leve di ribilanciamento tax-aware

Questa reference approfondisce le 4 leve con esempi numerici completi. Il principio guida: **esaurire le leve a costo fiscale zero prima di passare a quelle che realizzano plusvalenze tassabili**.

## Quadro riassuntivo

| Leva | Meccanismo | Costo fiscale | Quando usarla |
|---|---|---|---|
| 1 | Nuovi versamenti verso sottopesate | ZERO | Fase accumulo, sempre prima scelta |
| 2 | Dividendi/cedole verso sottopesate | ZERO | Quando ci sono flussi in entrata |
| 3 | Vendita posizioni in MINUS | ZERO o NEGATIVO | Se ci sono sovrappesate in perdita |
| 4 | Vendita posizioni in PLUS | POSITIVO (da minimizzare) | Ultima risorsa |

## Portafoglio di esempio (usato in tutti i casi)

Investitore in fase di accumulo, dossier presso un unico broker. Target: **60% azionario / 30% obbligazionario / 10% monetario**.

| Posizione | Asset class | Tipo fiscale | Controvalore | PMC vs attuale | Plus/minus latente |
|---|---|---|---|---|---|
| ETF MSCI World UCITS | Azionario globale | reddito_capitale | €68.000 | +40% | +€19.428 |
| ETF Euro Gov Bond UCITS | Obbligazionario | reddito_capitale | €24.000 | -3% | -€742 |
| ETF Money Market UCITS | Monetario | reddito_capitale | €8.000 | +1% | +€79 |
| **Totale** | | | **€100.000** | | |

**Drift attuale**:
- Azionario: 68% vs 60% target → **+8% sovrappeso** (€8.000 in eccesso)
- Obbligazionario: 24% vs 30% target → **-6% sottopeso** (€6.000 mancanti)
- Monetario: 8% vs 10% target → **-2% sottopeso** (€2.000 mancanti, ma dentro banda ±5%)

Le classi fuori banda (soglia ±5% assoluto): azionario (+8%) e obbligazionario (-6%). Il monetario (-2%) è dentro banda.

Per riportare a target servono: **−€8.000 azionario, +€6.000 obbligazionario, +€2.000 monetario**.

---

## CASO A: Fase di accumulo con versamento disponibile (Leva 1 sola)

**Setup**: l'investitore ha **€8.000 di liquidità** da versare (es. bonus annuale, risparmio accumulato).

**Soluzione tax-aware**: dirigere **tutto** il nuovo versamento verso le classi sottopesate, senza vendere nulla.

```
Nuovo versamento: €8.000
  → €6.000 all'obbligazionario (copre il sottopeso)
  → €2.000 al monetario (copre il sottopeso)

Allocazione risultante (totale ora €108.000):
  Azionario:      €68.000 / €108.000 = 63,0%  (target 60%, drift +3% → IN BANDA)
  Obbligazionario: €30.000 / €108.000 = 27,8%  (target 30%, drift -2,2% → IN BANDA)
  Monetario:      €10.000 / €108.000 =  9,3%  (target 10%, drift -0,7% → IN BANDA)
```

**Costo fiscale: €0.** Nessuna vendita, nessun realizzo. Tutte le classi rientrano in banda.

**Nota**: l'azionario resta leggermente sovrappeso in percentuale (63% vs 60%) perché il versamento non lo ha toccato, ma è ora **dentro la banda di tolleranza**. Non serve venderlo. Questo è il punto: il ribilanciamento via versamenti non azzera il drift, lo riporta in banda a costo zero. Perfetto.

**Confronto con l'approccio naïve (vendere per ribilanciare a target esatto)**:
```
Approccio naïve: vendere €8.000 di azionario + ricomprare obbligazionario/monetario
  Plus realizzata su €8.000 di ETF World (+40% di gain medio):
    quota di gain = €8.000 × (19.428/68.000) = €2.286 di plus
  Tassa 26% = €594
  + commissioni vendita + acquisto
  COSTO TOTALE: ~€620
```

La Leva 1 fa risparmiare ~€620 rispetto al ribilanciamento naïve con vendita. **Stesso risultato (in banda), costo zero contro €620.**

---

## CASO B: Accumulo senza versamento sufficiente (Leve 1+3)

**Setup**: l'investitore ha solo **€3.000** di liquidità, non bastano per coprire il gap di €8.000. Ha però l'ETF obbligazionario in **minus latente** (-€742).

Attenzione: l'obbligazionario è *sottopesato*, quindi non lo vendiamo (è tra le classi da aumentare). La Leva 3 si applica alle posizioni **sovrappesate in minus**. Qui l'unica sovrappesata è l'azionario, che è in **plus**, non in minus. Quindi la Leva 3 pura non è disponibile in questo esempio.

```
LEVA 1: versare €3.000
  → €3.000 all'obbligazionario (copre metà del sottopeso da -€6.000)

Gap residuo dopo Leva 1:
  Azionario:      €68.000 / €103.000 = 66,0%  (target 60%, +6% → ANCORA FUORI BANDA)
  Obbligazionario: €27.000 / €103.000 = 26,2%  (target 30%, -3,8% → in banda)
  Monetario:       €8.000 / €103.000 =  7,8%  (target 10%, -2,2% → in banda)
```

Dopo la Leva 1, solo l'azionario è ancora fuori banda (+6%). Per correggerlo serve vendere azionario (Leva 4, perché è in plus).

```
LEVA 4: vendere azionario per riportare in banda
  Per tornare esattamente a target 60%: vendere ~€6.180
  Ma basta riportare IN BANDA (entro +5%): vendere il minimo per scendere a 65% → ~€1.030
  
  Strategia "riporta in banda" (minimizza la vendita e quindi la tassa):
    Vendere €1.030 di ETF World
    Plus realizzata = €1.030 × (19.428/68.000) = €294
    Tassa 26% = €76
    
  Strategia "torna a target esatto":
    Vendere €6.180 di ETF World
    Plus realizzata = €6.180 × (19.428/68.000) = €1.766
    Tassa 26% = €459
```

**Decisione**: se l'obiettivo è solo rispettare la tolleranza, "riporta in banda" costa €76 contro €459. La skill dovrebbe presentare **entrambe le opzioni** e raccomandare quella in banda salvo che l'utente voglia esplicitamente tornare a target esatto.

**Limite dell'esempio**: qui non c'era una posizione sovrappesata in minus, quindi la Leva 3 non si è attivata. In un portafoglio dove l'asset sovrappesato è in perdita (es. dopo un rally seguito da correzione su quella classe), la Leva 3 permette di ribilanciare a costo fiscale zero o negativo.

---

## CASO C: La Leva 3 in azione (vendita in minus che ribilancia)

**Setup diverso**: immagina che dopo una fase di mercato l'azionario sia sovrappeso MA in leggera minus, e l'obbligazionario sottopeso in plus.

| Posizione | Asset class | Controvalore | Plus/minus latente |
|---|---|---|---|
| ETF Emerging Markets UCITS | Azionario | €35.000 (sovrappeso) | **-€2.500** (in perdita) |
| ETF World UCITS | Azionario | €33.000 | +€8.000 |
| ETF Gov Bond | Obbligazionario | €22.000 (sottopeso) | +€600 |
| Monetario | Monetario | €10.000 | +€50 |

Supponiamo che l'azionario totale (€68.000) sia sovrappeso e vada ridotto di €8.000, l'obbligazionario aumentato.

```
LEVA 3: vendere l'ETF Emerging Markets (sovrappeso E in minus)
  Vendere €8.000 di ETF EM
  Minus realizzata = €8.000 × (2.500/35.000) = €571 di minusvalenza
  
  → Questa minus NON costa tasse: al contrario, entra nello zainetto fiscale
    (utilizzabile per compensare plus future entro 4 anni)
  → Coordinare con it-tax-optimization: se l'utente ha plus da realizzare
    altrove, questa minus le compensa
  
  Il ricavato (€8.000) si reinveste nell'obbligazionario sottopeso
  
Costo fiscale: ZERO (anzi, genera €571 di zainetto = beneficio fiscale latente)
```

Questo è il caso ideale: ribilanciare vendendo proprio ciò che è in perdita realizza una minus utile **e** corregge il drift. La Leva 3 trasforma il ribilanciamento in un'opportunità fiscale.

⚠️ **Caveat ETF UCITS**: se l'ETF EM è UCITS armonizzato, la minus realizzata è comunque reddito diverso (le minus su ETF armonizzati SONO compensabili — è la *plus* che non lo è). Quindi la minus va nello zainetto e può compensare plus su redditi diversi. Vedi `it-tax-optimization/references/etf-trap-redditi-capitale.md` per l'asimmetria completa.

---

## CASO D: Fase di decumulo (prelievi che ribilanciano)

**Setup**: investitore in pensione che preleva €2.000/mese dal portafoglio. Il prelievo è la leva di ribilanciamento "al contrario": invece di aggiungere alle sottopesate, si **preleva dalle sovrappesate**.

```
Prelievo mensile: €2.000
  → prelevare dalle classi SOVRAPPESATE (le riduce, ribilanciando)
  → preferire, tra le sovrappesate, quelle con plus latente minore (meno tassa)
    o quelle compensabili con zainetto

Esempio: azionario sovrappeso, preleva €2.000 da lì
  Se ETF World (reddito capitale, plus +40%):
    plus realizzata = €2.000 × (19.428/68.000) = €571
    tassa 26% = €148 → il prelievo netto effettivo è €1.852 dopo tassa
    (per avere €2.000 netti in tasca servirebbe vendere ~€2.160)
```

In decumulo, la **sequenza di liquidazione tax-efficient** diventa centrale: prelevare prima dalle posizioni con minor plus latente (o in minus, o compensabili con zainetto) minimizza le tasse lungo il decumulo. Questo è materia avanzata, prevista per v0.5 della skill.

---

## Regola pratica finale

1. **In accumulo**: Leva 1 (versamenti) copre la maggior parte dei ribilanciamenti a costo zero. La vendita serve solo se il drift eccede quello che i versamenti possono correggere.
2. **Sempre**: prima di vendere in plus (Leva 4), controllare se c'è una posizione sovrappesata in minus da vendere (Leva 3) — ribilancia gratis e crea zainetto.
3. **"In banda" batte "a target esatto"**: riportare entro la tolleranza costa meno che azzerare il drift. Proporre entrambe, raccomandare la prima salvo richiesta esplicita.
4. **In decumulo**: i prelievi sono la leva naturale; sequenziarli per minimizzare le plus realizzate.
5. **Coordinare di fine anno**: se ci sono minus in scadenza (31/12 del 4° anno), il ribilanciamento è il momento per realizzare plus compensabili gratuitamente.
