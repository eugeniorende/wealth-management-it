#!/usr/bin/env python3
"""
decumulo-obiettivi.py — la fase di PRELIEVO, che è un problema diverso dall'accumulo.

Tre output:

1. TASSO DI PRELIEVO SOSTENIBILE (Monte Carlo). Dato un capitale, un prelievo annuo
   reale e un orizzonte, simula migliaia di percorsi (bootstrap a blocchi dalla serie
   storica, che preserva la SEQUENZA dei rendimenti) e calcola la probabilità che
   il capitale duri tutto l'orizzonte. Più una tabella di sensibilità su più tassi.

2. RISCHIO DI SEQUENZA DEI RENDIMENTI. In prelievo conta l'ORDINE dei rendimenti, non
   solo la media: gli stessi rendimenti in ordine "peggiori-prima" possono esaurire il
   capitale, mentre "migliori-prima" lo fanno crescere. Lo script lo dimostra prendendo
   un identico insieme di rendimenti e simulandolo nei due ordini opposti (stessa media,
   esiti opposti). È la ragione per cui il decumulo NON è l'accumulo al contrario.

3. BUFFER DI LIQUIDITÀ (strategia bucket). Tenere N anni di prelievi in liquidità e
   attingervi negli anni negativi (invece di vendere in perdita) attenua il rischio di
   sequenza. Lo script confronta la probabilità di successo e il capitale finale mediano
   con e senza buffer, rendendo visibile il trade-off (il buffer protegge ma rende ~0).

⚠️ La serie storica è S&P 500 + US T-Bond (Damodaran): rendimenti NOMINALI in dollari, che
lo script porta in termini reali anno per anno con l'inflazione USA storica (CPI dicembre su
dicembre, colonna del CSV): la stagflazione degli anni '70 resta nella serie, dove il rischio
di sequenza pesa di più. Nessuna componente di cambio: è l'esperienza di un investitore USA.
Il mercato USA è storicamente ECCEZIONALE, quindi i tassi di successo qui sono OTTIMISTICI
per un investitore europeo.
La celebre "regola del 4%" nasce su questi dati e su orizzonte 30 anni; va presa come
punto di partenza, non come garanzia. Vedi decumulo.md per i caveat. NON è consulenza.

Dipendenze: numpy   (pip install numpy)
Uso:        python decumulo-obiettivi.py
"""

import numpy as np

from motore_bootstrap import applica_override, carica_inflazione, carica_storico, deflaziona

# ─────────────────────────── INPUT (editabili) ───────────────────────────
CAPITALE_INIZIALE     = 500000     # capitale a inizio decumulo (€)
PRELIEVO_ANNUO_REALE  = 20000      # prelievo annuo in € di OGGI, costante in termini reali (qui 4%)
ORIZZONTE_ANNI        = 30         # durata del decumulo
PESO_AZIONARIO        = 0.60       # quota azionaria (il resto obbligazionario)
INFLAZIONE            = None       # None = inflazione USA storica anno per anno (colonna del CSV);
                                   # un numero (es. 0.02) = inflazione costante, che però appiattisce
                                   # gli anni '70 (inflazione a due cifre) proprio dove la sequenza conta
INFLAZIONE_RIPIEGO    = 0.02       # usata se la serie (propria) non ha la colonna inflazione
BUFFER_ANNI           = 2          # anni di prelievo tenuti in liquidità (0 = nessun buffer)
DERATING_AZIONARIO    = 0.015      # scarto verso il basso sull'azionario reale, per trasformare
                                   # "storia USA" in "scenario globale" (USA-vs-mondo ≈ -1,5%, fonte DMS).
                                   # 0 = lente USA grezza (ottimistica). Vedi mercati-e-correlazione.md

N_SIM                 = 20000
BLOCCO_BOOTSTRAP      = 5          # blocco (anni consecutivi) nel bootstrap: preserva la sequenza
SEED                  = 42
FILE_STORICO          = "rendimenti-storici.csv"
TASSI_SENSIBILITA     = [0.03, 0.035, 0.04, 0.045, 0.05, 0.06]  # prelievi % del capitale da testare
# ──────────────────────────────────────────────────────────────────────────


def inflazione_usata():
    """Inflazione per deflazionare la serie: l'array storico, o una costante (INFLAZIONE o il
    ripiego se la serie non ha la colonna). Ritorna (inflazione, descrizione)."""
    if INFLAZIONE is not None:
        return INFLAZIONE, f"inflazione costante {INFLAZIONE*100:.1f}%"
    storica = carica_inflazione(FILE_STORICO)
    if storica is None:
        return INFLAZIONE_RIPIEGO, (f"inflazione costante {INFLAZIONE_RIPIEGO*100:.1f}% "
                                    "(la serie non ha la colonna inflazione)")
    return storica, "inflazione USA storica anno per anno (CPI dicembre su dicembre)"


def carica_rendimenti_reali(derating=0.0):
    """Serie annuale di rendimenti REALI del portafoglio (azionario/obbligazionario pesati).
    La serie del CSV è nominale in dollari: ogni anno si deflaziona con l'inflazione di
    quell'anno. `derating` è uno scarto sottratto al solo azionario reale (USA → scenario globale)."""
    az, ob = carica_storico(FILE_STORICO)
    inflazione, _ = inflazione_usata()
    az_real = deflaziona(az, inflazione) - derating   # azionario reale, de-ratato
    ob_real = deflaziona(ob, inflazione)              # obbligazionario reale
    return PESO_AZIONARIO * az_real + (1 - PESO_AZIONARIO) * ob_real


def percorso_bootstrap(returns, rng):
    """Costruisce un percorso di ORIZZONTE anni con bootstrap a blocchi (preserva sequenza)."""
    n = len(returns)
    path = []
    while len(path) < ORIZZONTE_ANNI:
        start = rng.integers(0, max(1, n - BLOCCO_BOOTSTRAP + 1))  # estremo escluso: l'ultimo blocco compreso
        path.extend(returns[start:start + BLOCCO_BOOTSTRAP].tolist())
    return path[:ORIZZONTE_ANNI]


def simula_decumulo(path, prelievo, buffer_anni):
    """Un singolo percorso. Ritorna (sopravvissuto: bool, anno_esaurimento|None, capitale_finale)."""
    buffer_target = buffer_anni * prelievo
    buffer = buffer_target
    invest = CAPITALE_INIZIALE - buffer
    for t, r in enumerate(path):
        # prelievo a inizio anno: negli anni negativi attingi dal buffer (non vendere in perdita)
        if buffer_anni > 0 and r < 0 and buffer >= prelievo:
            buffer -= prelievo
        elif invest >= prelievo:
            invest -= prelievo
        elif buffer >= prelievo:
            buffer -= prelievo
        else:
            return False, t + 1, 0.0
        # rendimento sull'investito
        invest *= (1 + r)
        # rifornisci il buffer negli anni positivi (vende un po' di investito quando i prezzi sono su)
        if buffer_anni > 0 and r >= 0 and buffer < buffer_target and invest > 0:
            refill = min(buffer_target - buffer, invest)
            invest -= refill
            buffer += refill
    return True, None, invest + buffer


def monte_carlo(prelievo, buffer_anni, derating=0.0):
    returns = carica_rendimenti_reali(derating)
    rng = np.random.default_rng(SEED)
    successi, finali, anni_es = 0, [], []
    for _ in range(N_SIM):
        path = percorso_bootstrap(returns, rng)
        ok, anno, fin = simula_decumulo(path, prelievo, buffer_anni)
        if ok:
            successi += 1
            finali.append(fin)
        else:
            anni_es.append(anno)
    p = successi / N_SIM
    fin_med = float(np.median(finali)) if finali else 0.0
    anno_med = float(np.median(anni_es)) if anni_es else None
    return p, fin_med, anno_med


def demo_sequenza():
    """Stesso insieme di rendimenti, due ordini opposti: dimostra il rischio di sequenza."""
    rng = np.random.default_rng(SEED)
    returns = carica_rendimenti_reali()
    sample = rng.choice(returns, size=ORIZZONTE_ANNI, replace=False)
    peggiori_prima = np.sort(sample)            # ascendente
    migliori_prima = np.sort(sample)[::-1]      # discendente
    # prelievo aggressivo per rendere visibile l'esito (6% del capitale)
    prelievo = round(CAPITALE_INIZIALE * 0.06)
    r_pp = simula_decumulo(peggiori_prima.tolist(), prelievo, 0)
    r_mp = simula_decumulo(migliori_prima.tolist(), prelievo, 0)
    return prelievo, float(np.mean(sample)), r_pp, r_mp


def stampa():
    print(f"\n{'='*72}")
    print(f"DECUMULO — capitale €{CAPITALE_INIZIALE:,.0f}, orizzonte {ORIZZONTE_ANNI} anni, "
          f"{PESO_AZIONARIO*100:.0f}/{(1-PESO_AZIONARIO)*100:.0f}")
    print(f"{'='*72}")
    print("Dati: S&P 500 + US T-Bond (Damodaran), nominali in dollari, bootstrap a blocchi. "
          "USA = caso storicamente favorevole → successi ottimistici.")
    print(f"Termini reali: {inflazione_usata()[1]}.")

    # 1) tasso sostenibile (base)
    p, fin_med, _ = monte_carlo(PRELIEVO_ANNUO_REALE, BUFFER_ANNI)
    tasso = PRELIEVO_ANNUO_REALE / CAPITALE_INIZIALE
    print(f"\n1) PRELIEVO BASE: €{PRELIEVO_ANNUO_REALE:,.0f}/anno reali ({tasso*100:.1f}% del capitale), "
          f"buffer {BUFFER_ANNI} anni")
    print(f"   probabilità che il capitale duri {ORIZZONTE_ANNI} anni: {p*100:.1f}%")
    print(f"   capitale finale mediano (nei successi): €{fin_med:,.0f}")

    # 1b) sensibilità sul tasso
    print(f"\n   Sensibilità (buffer {BUFFER_ANNI} anni):")
    print(f"   {'prelievo':>10}{'% capitale':>12}{'prob. successo':>16}")
    for t in TASSI_SENSIBILITA:
        prel = round(CAPITALE_INIZIALE * t)
        pp, _, _ = monte_carlo(prel, BUFFER_ANNI)
        print(f"   €{prel:>8,.0f}{t*100:>10.1f}%{pp*100:>14.1f}%")

    # 2) rischio di sequenza
    prelievo, media, r_pp, r_mp = demo_sequenza()
    print(f"\n2) RISCHIO DI SEQUENZA — stesso insieme di rendimenti, due ordini opposti")
    print(f"   (prelievo {prelievo/CAPITALE_INIZIALE*100:.0f}% = €{prelievo:,.0f}/anno; "
          f"rendimento medio reale identico nei due casi: {media*100:+.1f}%)")
    def descrivi(r):
        ok, anno, fin = r
        return (f"capitale finale €{fin:,.0f}" if ok
                else f"ESAURITO all'anno {anno}")
    print(f"   • peggiori rendimenti PRIMA:  {descrivi(r_pp)}")
    print(f"   • migliori rendimenti PRIMA:  {descrivi(r_mp)}")
    print(f"   → stessa media, esiti opposti: è il rischio di sequenza. In prelievo l'ordine conta.")

    # 3) effetto del buffer di liquidità
    print(f"\n3) BUFFER DI LIQUIDITÀ — confronto a parità di prelievo (€{PRELIEVO_ANNUO_REALE:,.0f}/anno)")
    p0, fin0, _ = monte_carlo(PRELIEVO_ANNUO_REALE, 0)
    pB, finB, _ = monte_carlo(PRELIEVO_ANNUO_REALE, BUFFER_ANNI)
    print(f"   senza buffer:           successo {p0*100:.1f}%  | finale mediano €{fin0:,.0f}")
    print(f"   buffer {BUFFER_ANNI} anni:           successo {pB*100:.1f}%  | finale mediano €{finB:,.0f}")
    verso = "alza" if pB > p0 else "abbassa"
    print(f"   → su questi dati il buffer {verso} il successo di {abs(pB-p0)*100:.1f} punti: la liquidità")
    print(f"     rende ~0 e il mercato USA recupera in fretta, quindi il costo-rendimento supera la")
    print(f"     protezione. È il consenso accademico (Estrada, Kitces): il buffer NON è un free lunch.")
    print(f"     Il suo valore vero è (1) non essere COSTRETTI a vendere in un crollo — beneficio")
    print(f"     comportamentale — e (2) coprire bear market PROLUNGATI, che la media USA sottostima.")

    # 4) lente USA vs globale (de-rating dell'azionario)
    print(f"\n4) LENTE USA vs GLOBALE — de-rating dell'azionario (€{PRELIEVO_ANNUO_REALE:,.0f}/anno, buffer {BUFFER_ANNI})")
    p_usa, _, _ = monte_carlo(PRELIEVO_ANNUO_REALE, BUFFER_ANNI, derating=0.0)
    p_glob, _, _ = monte_carlo(PRELIEVO_ANNUO_REALE, BUFFER_ANNI, derating=DERATING_AZIONARIO)
    print(f"   lente USA (derating 0):                 successo {p_usa*100:.1f}%   ← ottimistica")
    print(f"   scenario globale (derating −{DERATING_AZIONARIO*100:.1f}%):       successo {p_glob*100:.1f}%   ← prudente")
    print(f"   → la sola fortuna storica USA vale ~{(p_usa-p_glob)*100:.1f} punti di probabilità di successo.")
    print(f"     L'azionario mondiale ha reso ~5,2% reale dal 1900 (DMS), gli USA di più: pianificare")
    print(f"     sullo scenario globale, non sulla serie americana. Vedi mercati-e-correlazione.md.")
    print()


if __name__ == "__main__":
    applica_override(globals())
    stampa()

# ─────────────────────────── ATTESO (validazione) ───────────────────────────
# • La probabilità di successo DECRESCE in modo monotòno all'aumentare del tasso di
#   prelievo (3% → ~quasi certo; 6% → sensibilmente più basso).
# • Nel punto 2 i due ordini hanno la STESSA media reale (proprietà dello stesso insieme)
#   ma esiti diversi: "peggiori-prima" finisce sempre ≤ "migliori-prima" (di norma uno
#   esaurisce e l'altro sopravvive con ampio margine). È la dimostrazione del rischio di
#   sequenza ed è strutturalmente garantita dall'ordinamento.
# • Sui dati USA al 4% su 30 anni il successo è alto (~90%, con l'inflazione storica anno per
#   anno), coerente con la regola del 4% — ma è il caso favorevole: per l'Europa va scontato.
