#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
riscatto-laurea.py — quanto costa riscattare gli anni di laurea, quanta pensione compra e quanto
anticipa l'uscita.

Il riscatto (art. 2 D.Lgs. 184/1997) trasforma gli anni del corso legale di laurea non coperti da
contributi in anni di contribuzione. Per gli anni che cadono nel sistema contributivo l'onere si
calcola in due modi:

  - AGEVOLATO (c. 5-quater, aggiunto dall'art. 20 c. 6 DL 4/2019): per ogni anno, il minimale di
    reddito di artigiani e commercianti per l'aliquota di computo del Fondo lavoratori dipendenti
    (33%), vigenti alla data della domanda: €18.808 × 33% = €6.206,64 l'anno per le domande del 2026;
  - ORDINARIO (c. 5): l'aliquota contributiva della gestione (33% per i dipendenti privati) sulla
    retribuzione dei dodici mesi prima della domanda, per ogni anno.

In entrambi i modi l'onere entra nel montante e si rivaluta dalla data della domanda (c. 5): la
pensione in più è proporzionale a quanto si paga. L'ordinario compra più pensione a un prezzo più
alto; l'agevolato compra gli stessi ANNI DI ANZIANITÀ (utili al diritto, c. 5-ter) al prezzo minimo.
Si paga in un'unica soluzione o fino a 120 rate mensili senza interessi (c. 4-bis) e si deduce dal
reddito complessivo senza tetto (art. 10 c. 1 lett. e TUIR; dal 2027 art. 10 c. 1 lett. f
D.Lgs. 117/2026).

Uso:
    python riscatto-laurea.py [--from FILE ...] [--set NOME=VALORE ...] [--json FILE]
    (--help elenca le costanti; --from legge il JSON di importa-previdenza.py e di proiezione-inps.py;
     il JSON scritto con --json porta il montante con il riscatto, che proiezione-inps.py --from rilegge)

ONESTÀ METODOLOGICA
- Tutto in euro di oggi: il montante si rivaluta al PIL reale, come in proiezione-inps.py, e il
  coefficiente di trasformazione è quello che quello script stima all'età di uscita.
- La pensione in più si calcola alla STESSA età di uscita. Se il riscatto serve ad anticipare
  (anticipata ordinaria), uscire prima abbassa la pensione: va rifatta la proiezione all'età
  dell'anticipata (proiezione-inps.py --set ETA_PENSIONAMENTO=...).
- Il risparmio IRPEF usa una sola aliquota marginale: vale finché la deduzione dell'anno resta nello
  stesso scaglione. Con l'unica soluzione su un reddito medio una parte scende allo scaglione sotto
  e il risparmio è minore; le rate spalmano la deduzione su più anni.
- Gli anni per rientrare confrontano il costo netto di oggi con la pensione netta in più: non
  tengono conto di cosa avrebbe reso la stessa somma investita altrove.
- I requisiti dell'anticipata ordinaria si adeguano alla speranza di vita: il default è quello noto
  dal 2028 per gli uomini, e per chi esce tra decenni sarà più alto.
Questo strumento è educativo e non costituisce consulenza finanziaria o previdenziale.
"""

from motore_bootstrap import cli, errore, numero, pct, scrivi_json

# ============================== PARAMETRI ==============================

ANNI_RISCATTO = 5.0           # anni di corso legale da riscattare (frazionari per i mesi: 4.5)
MODALITA = "agevolato"        # quella che va nel JSON per la catena: "agevolato" o "ordinario"

# Onere (Verificato: 2026-10 su Circ. INPS 14/2026 e sulla scheda INPS del riscatto di laurea)
MINIMALE_ARTIGIANI_COMMERCIANTI = 18_808.0  # minimale di reddito 2026 (art. 1 c. 3 L. 233/1990)
ALIQUOTA_COMPUTO_FPLD = 0.33  # aliquota di computo del Fondo lavoratori dipendenti (agevolato)
ALIQUOTA_ORDINARIO = 0.33     # aliquota contributiva FPLD sulla retribuzione (ordinario, dipendenti)
RAL_ATTUALE = 36_000.0        # retribuzione imponibile degli ultimi 12 mesi (per l'ordinario)
RATE_MENSILI = 120            # 1 = unica soluzione; fino a 120 rate senza interessi

ALIQUOTA_MARGINALE_IRPEF = 0.33    # aliquota a cui si deduce l'onere (scaglione del reddito di oggi)
ALIQUOTA_IRPEF_IN_PENSIONE = 0.25  # marginale sulla pensione in più (23% + addizionali)

# Proiezione (come proiezione-inps.py, che con --json li passa qui)
MONTANTE_ATTUALE = 85_000.0   # montante contributivo a oggi (da importa-previdenza.py)
ETA_ATTUALE = 37.0
ETA_PENSIONAMENTO = 69.0
ANNI_AL_PENSIONAMENTO = None  # dal JSON di proiezione-inps.py; None = ETA_PENSIONAMENTO − ETA_ATTUALE
PIL_REALE = 0.005             # rivalutazione reale del montante
COEFF_TRASFORMAZIONE = 0.04811  # coefficiente a 69 anni di proiezione-inps.py sui suoi default

# Anzianità e pensione anticipata ordinaria (Circ. INPS 28/2026, All. 2; Verificato: 2026-10)
ANZIANITA_ATTUALE = 12.0      # anni di contributi a oggi (estratto conto; da importa-previdenza.py)
REQUISITO_ANTICIPATA = 43 + 1 / 12  # uomini dal 2028 (donne 42 anni e 1 mese; nel 2026 42 e 10 mesi)
FINESTRA_ANTICIPATA = 0.25    # la pensione decorre tre mesi dopo i requisiti
CONTRIBUTI_SOLO_DAL_1996 = False  # True dal JSON di importa-previdenza.py se ci sono retribuzioni prima del 1996

# =======================================================================


def onere_annuo(modalita):
    """Onere di un anno di riscatto nella modalità data (€ alla data della domanda)."""
    if modalita == "agevolato":
        return MINIMALE_ARTIGIANI_COMMERCIANTI * ALIQUOTA_COMPUTO_FPLD
    return RAL_ATTUALE * ALIQUOTA_ORDINARIO


def eta_anticipata(anzianita):
    """Età di decorrenza dell'anticipata ordinaria lavorando da oggi senza interruzioni."""
    return ETA_ATTUALE + max(0.0, REQUISITO_ANTICIPATA - anzianita) + FINESTRA_ANTICIPATA


def scenario(modalita, anni):
    """Costo, rata, pensione in più e anni per rientrare di una modalità."""
    onere = onere_annuo(modalita) * ANNI_RISCATTO
    netto = onere * (1 - ALIQUOTA_MARGINALE_IRPEF)
    delta_montante = onere * (1 + PIL_REALE) ** anni
    delta_pensione = delta_montante * COEFF_TRASFORMAZIONE
    netta = delta_pensione * (1 - ALIQUOTA_IRPEF_IN_PENSIONE)
    return {"onere": onere, "rata": onere / RATE_MENSILI, "netto": netto,
            "deduzione_annua": min(onere, onere / RATE_MENSILI * 12),
            "delta_montante": delta_montante, "delta_pensione": delta_pensione,
            "anni_rientro": netto / netta if netta > 0 else float("inf")}


def valida():
    if not 0 < ANNI_RISCATTO <= 10:
        errore(f"ANNI_RISCATTO = {ANNI_RISCATTO}: gli anni di corso legale riscattabili vanno da 0 a 10.")
    if MODALITA not in ("agevolato", "ordinario"):
        errore(f"MODALITA = {MODALITA!r}: usa 'agevolato' oppure 'ordinario'.")
    if RATE_MENSILI != int(RATE_MENSILI) or not 1 <= RATE_MENSILI <= 120:
        errore(f"RATE_MENSILI = {RATE_MENSILI}: da 1 (unica soluzione) a 120 rate mensili.")
    for nome in ("ALIQUOTA_MARGINALE_IRPEF", "ALIQUOTA_IRPEF_IN_PENSIONE", "ALIQUOTA_COMPUTO_FPLD", "ALIQUOTA_ORDINARIO"):
        if not 0 <= globals()[nome] < 1:
            errore(f"{nome} = {globals()[nome]}: è una frazione tra 0 e 1 (0.33, non 33).")
    if ETA_PENSIONAMENTO <= ETA_ATTUALE:
        errore("ETA_PENSIONAMENTO deve superare ETA_ATTUALE.")


def main():
    args = cli("Riscatto della laurea, agevolato e ordinario a confronto: costo lordo e netto, rata, pensione "
               "in più, anni per rientrare e anticipo sulla pensione anticipata ordinaria.", globals(), json=True,
               da_json={"montante_attuale": "MONTANTE_ATTUALE", "ral_attuale": "RAL_ATTUALE",
                        "eta_attuale": "ETA_ATTUALE", "anzianita_contributiva": "ANZIANITA_ATTUALE",
                        "contributi_solo_dal_1996": "CONTRIBUTI_SOLO_DAL_1996",   # importa-previdenza.py
                        "coefficiente_trasformazione": "COEFF_TRASFORMAZIONE",
                        "anni_al_pensionamento": "ANNI_AL_PENSIONAMENTO",
                        "eta_pensionamento": "ETA_PENSIONAMENTO"})                # proiezione-inps.py
    valida()
    anni = ANNI_AL_PENSIONAMENTO if ANNI_AL_PENSIONAMENTO is not None else round(ETA_PENSIONAMENTO - ETA_ATTUALE)
    agev, ordi = scenario("agevolato", anni), scenario("ordinario", anni)

    print("=" * 72)
    print(f"RISCATTO DELLA LAUREA — {numero(ANNI_RISCATTO, 1 if ANNI_RISCATTO % 1 else 0)} anni, "
          "valori reali (€ di oggi)")
    print("=" * 72)
    if CONTRIBUTI_SOLO_DAL_1996:
        print("⚠ posizione mista: ci sono contributi prima del 1996. L'agevolato vale solo per gli anni di corso")
        print("  dal 1996, che cadono nel contributivo; per quelli precedenti serve l'opzione al contributivo")
        print("  (art. 1 c. 23 L. 335/1995; Circ. INPS 6/2020 e 54/2021), irrevocabile e su tutta la pensione:")
        print("  valutala con INPS o un patronato prima di pagare.")
        print()
    righe = [("Onere lordo", "onere", 0), ("Rata mensile" + (f" ({RATE_MENSILI} rate)" if RATE_MENSILI > 1 else
                                                            " (unica soluzione)"), "rata", 2),
             (f"Costo netto (deduzione al {pct(ALIQUOTA_MARGINALE_IRPEF, 0)})", "netto", 0),
             (f"Montante in più a {ETA_PENSIONAMENTO:.0f} anni", "delta_montante", 0),
             ("Pensione lorda annua in più", "delta_pensione", 0)]
    print(f"  {'':<40}{'agevolato':>14}{'ordinario':>16}")
    for etichetta, chiave, dec in righe:
        print(f"  {etichetta:<40}{'€ ' + numero(agev[chiave], dec):>14}{'€ ' + numero(ordi[chiave], dec):>16}")
    rientro = agev["anni_rientro"]
    print(f"  {'Anni di pensione per rientrare':<40}{numero(rientro, 1):>14}{numero(ordi['anni_rientro'], 1):>16}")
    print(f"\nOnere per anno: agevolato € {numero(onere_annuo('agevolato'), 2)} "
          f"(€ {numero(MINIMALE_ARTIGIANI_COMMERCIANTI)} × {pct(ALIQUOTA_COMPUTO_FPLD, 0)}), "
          f"ordinario € {numero(onere_annuo('ordinario'), 2)} "
          f"(€ {numero(RAL_ATTUALE)} × {pct(ALIQUOTA_ORDINARIO, 0)}).")
    if onere_annuo("ordinario") < onere_annuo("agevolato"):
        print("  Con una retribuzione sotto il minimale l'ordinario costa meno dell'agevolato.")
    print("I due modi rendono allo stesso modo (l'onere va tutto nel montante): l'ordinario compra più")
    print("pensione, l'agevolato gli stessi anni di anzianità al prezzo minimo.")
    print(f"Deduzione dell'anno con le rate: € {numero(agev['deduzione_annua'])} (agevolato); il risparmio al "
          f"{pct(ALIQUOTA_MARGINALE_IRPEF, 0)} vale finché resta nello scaglione.")

    # ------------------------- anzianità e uscita -------------------------
    con = ANZIANITA_ATTUALE + ANNI_RISCATTO
    senza_eta, con_eta = eta_anticipata(ANZIANITA_ATTUALE), eta_anticipata(con)
    print("\n" + "-" * 72)
    print(f"ANZIANITÀ: {numero(ANZIANITA_ATTUALE, 1)} anni oggi → {numero(con, 1)} con il riscatto")
    print(f"Pensione anticipata ordinaria ({numero(REQUISITO_ANTICIPATA, 2)} anni di contributi + finestra di 3 mesi),")
    print("lavorando da oggi senza interruzioni:")
    print(f"  senza riscatto: a {numero(senza_eta, 1)} anni")
    print(f"  con il riscatto: a {numero(con_eta, 1)} anni")
    if con_eta >= ETA_PENSIONAMENTO:
        print(f"  Arriva comunque dopo l'uscita ipotizzata ({ETA_PENSIONAMENTO:.0f} anni): qui il riscatto non anticipa.")
    else:
        print(f"  Uscire a {numero(con_eta, 1)} anni invece che a {ETA_PENSIONAMENTO:.0f} abbassa la pensione: rifai la "
              f"proiezione con proiezione-inps.py --set ETA_PENSIONAMENTO={round(con_eta, 2)}.")
    anz_uscita = ANZIANITA_ATTUALE + (ETA_PENSIONAMENTO - ETA_ATTUALE)
    if anz_uscita < 20 <= anz_uscita + ANNI_RISCATTO:
        print(f"  Senza riscatto a {ETA_PENSIONAMENTO:.0f} anni avresti {numero(anz_uscita, 1)} anni di contributi, "
              "sotto i 20 della vecchiaia: il riscatto li completa.")

    print("\nAvvertenze:")
    print("  - la pensione in più è lorda e alla stessa età di uscita; i requisiti dell'anticipata salgono")
    print("    con la speranza di vita, quindi per chi esce tra decenni l'anticipo è indicativo")
    print("  - l'onere vale per le domande dell'anno: il minimale si aggiorna ogni anno")
    print("  - pagamenti parziali accreditano solo il periodo corrispondente; con la domanda di pensione le rate")
    print("    residue si pagano in un'unica soluzione; il riscatto pagato non si revoca")
    print("  - il dato esatto lo dà INPS (simulazione del riscatto di laurea) o un patronato")
    print("\nQuesto strumento è educativo e non costituisce consulenza finanziaria o previdenziale.")

    if args.json:
        scelto = agev if MODALITA == "agevolato" else ordi
        scrivi_json(args.json, {
            "modalita": MODALITA,
            "anni_riscatto": ANNI_RISCATTO,
            "onere_riscatto": round(scelto["onere"], 2),
            "onere_agevolato": round(agev["onere"], 2),
            "onere_ordinario": round(ordi["onere"], 2),
            "rata_mensile": round(scelto["rata"], 2),
            "costo_netto": round(scelto["netto"], 2),
            "delta_montante_al_pensionamento": round(scelto["delta_montante"], 2),
            "delta_pensione_lorda_annua": round(scelto["delta_pensione"], 2),
            "anni_per_rientrare": round(scelto["anni_rientro"], 1),
            "anzianita_con_riscatto": round(con, 2),
            "eta_anticipata_senza_riscatto": round(senza_eta, 2),
            "eta_anticipata_con_riscatto": round(con_eta, 2),
            # per la catena: proiezione-inps.py --from riscatto.json proietta il montante con il riscatto
            "montante_attuale": round(MONTANTE_ATTUALE + scelto["onere"], 2),
            "ral_attuale": RAL_ATTUALE,
            "eta_attuale": ETA_ATTUALE,
            "contributi_solo_dal_1996": CONTRIBUTI_SOLO_DAL_1996,
        })


if __name__ == "__main__":
    main()
