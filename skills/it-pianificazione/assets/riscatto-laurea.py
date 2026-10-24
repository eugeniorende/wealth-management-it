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

Gli anni riscattati valgono per il diritto alla pensione (c. 5-ter); l'onere entra nel montante e si
rivaluta dalla data della domanda (c. 5), quindi la pensione in più è proporzionale a quanto si paga.
L'ordinario compra più pensione a un prezzo più alto; l'agevolato compra gli stessi ANNI DI ANZIANITÀ
al prezzo minimo. Si paga in un'unica soluzione o fino a 120 rate mensili senza interessi (c. 4-bis)
e si deduce dal reddito complessivo senza tetto (art. 10 c. 1 lett. e TUIR; dal 2027 art. 10 c. 1
lett. f D.Lgs. 117/2026). Gli anni di corso prima del 1996 seguono altre regole (vedi
ANNI_PRIMA_DEL_1996): lo script ne stima solo l'anzianità, non l'onere.

Uso:
    python riscatto-laurea.py [--from FILE ...] [--set NOME=VALORE ...] [--json FILE]
    (--help elenca le costanti; --from legge il JSON di importa-previdenza.py e di proiezione-inps.py;
     il JSON scritto con --json porta il montante con il riscatto e l'età di uscita, che
     proiezione-inps.py --from rilegge: gli altri --set di scenario vanno ripetuti)

ONESTÀ METODOLOGICA
- Tutto in euro di oggi: il montante si rivaluta al PIL reale e il coefficiente di trasformazione è
  quello di proiezione-inps.py all'età di uscita (la tabella e la riduzione annua si leggono da lì),
  oppure quello del suo JSON passato con --from.
- La pensione in più si calcola alla STESSA età di uscita. Se il riscatto serve ad anticipare
  (anticipata ordinaria), uscire prima abbassa la pensione: va rifatta la proiezione all'età
  dell'anticipata (proiezione-inps.py --set ETA_PENSIONAMENTO=...).
- Il risparmio IRPEF usa una sola aliquota marginale: vale finché la deduzione dell'anno resta nello
  stesso scaglione. Con l'unica soluzione su un reddito medio una parte scende allo scaglione sotto
  e il risparmio è minore; lo script lo segnala, e le rate spalmano la deduzione su più anni.
- Anche l'aliquota sulla pensione in più è una marginale: il default vale per la pensione che
  proiezione-inps.py stima sui suoi default; per un'altra pensione si ricava da netto-pensione.py.
- Gli anni per rientrare confrontano il costo netto di oggi con la pensione netta in più: non
  tengono conto di cosa avrebbe reso la stessa somma investita altrove.
- I requisiti dell'anticipata ordinaria si adeguano alla speranza di vita: il default è quello noto
  dal 2028, e per chi esce tra decenni sarà più alto.
Questo strumento è educativo e non costituisce consulenza finanziaria o previdenziale.
"""

import importlib.util
import os

from motore_bootstrap import cli, errore, numero, pct, scrivi_json

# ============================== PARAMETRI ==============================

ANNI_RISCATTO = 5.0           # anni di corso legale ancora riscattabili (non quelli fuori corso né quelli
                              # già coperti da contributi); frazionari per i mesi: 4.5
ANNI_PRIMA_DEL_1996 = 0.0     # quanti di quegli anni di corso cadono prima del 1996 (vedi l'avviso)
MODALITA = "agevolato"        # quella che va nel JSON per la catena: "agevolato" o "ordinario"

# Onere (Verificato: 2026-10 su Circ. INPS 14/2026 e sulla scheda INPS del riscatto di laurea)
MINIMALE_ARTIGIANI_COMMERCIANTI = 18_808.0  # minimale di reddito 2026 (art. 1 c. 3 L. 233/1990)
ALIQUOTA_COMPUTO_FPLD = 0.33  # aliquota di computo del Fondo lavoratori dipendenti (agevolato)
ALIQUOTA_ORDINARIO = 0.33     # aliquota contributiva FPLD sulla retribuzione (ordinario, dipendenti)
RAL_ATTUALE = 36_000.0        # retribuzione imponibile degli ultimi 12 mesi (per l'ordinario)
RATE_MENSILI = 120            # 1 = unica soluzione; fino a 120 rate senza interessi

ALIQUOTA_MARGINALE_IRPEF = 0.33    # aliquota a cui si deduce l'onere (scaglione del reddito di oggi)
ALIQUOTA_IRPEF_IN_PENSIONE = 0.38  # marginale sulla pensione in più: 33% + calo della detrazione pensionati
                                   # + addizionali sulla pensione dei default (≈ €29.800; netto-pensione.py dà
                                   # 38,4%); tra €8.500 e €28.000 di pensione ≈ 32%

# Proiezione (come proiezione-inps.py, che con --json li passa qui)
MONTANTE_ATTUALE = 85_000.0   # montante contributivo a oggi (da importa-previdenza.py)
ETA_ATTUALE = 37.0
ETA_PENSIONAMENTO = 69.0
ANNI_AL_PENSIONAMENTO = None  # dal JSON di proiezione-inps.py; None = ETA_PENSIONAMENTO − ETA_ATTUALE
PIL_REALE = 0.005             # rivalutazione reale del montante
COEFF_TRASFORMAZIONE = None   # None = come proiezione-inps.py all'età di uscita; dal suo JSON con --from

# Anzianità e pensione anticipata ordinaria (Circ. INPS 28/2026, All. 2; Verificato: 2026-10)
ANZIANITA_ATTUALE = 12.0      # anni di contributi a oggi (estratto conto; da importa-previdenza.py)
SESSO = "M"                   # "M" o "F": decide il requisito dell'anticipata ordinaria
REQUISITO_ANTICIPATA = None   # None = dal 2028 43 anni e 1 mese gli uomini, 42 e 1 mese le donne
                              # (nel 2026 42 e 10 mesi, 41 e 10 mesi); in decimali: 42.0833
FINESTRA_ANTICIPATA = 0.25    # la pensione decorre tre mesi dopo i requisiti
CONTRIBUTI_SOLO_DAL_1996 = False  # True dal JSON di importa-previdenza.py se ci sono retribuzioni prima del 1996

REDDITO_SU_RAL = 1 - 0.0919   # reddito imponibile ≈ RAL meno i contributi a carico del lavoratore (9,19%)
SOGLIA_SCAGLIONE = {0.23: 0.0, 0.33: 28_000.0, 0.43: 50_000.0}  # IRPEF 2026: da dove parte ogni aliquota

# =======================================================================


def _proiezione_inps():
    """Il modulo di proiezione-inps.py: tabella dei coefficienti e riduzione annua stanno solo lì."""
    percorso = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proiezione-inps.py")
    spec = importlib.util.spec_from_file_location("proiezione_inps", percorso)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def requisito_anticipata():
    if REQUISITO_ANTICIPATA is not None:
        return REQUISITO_ANTICIPATA
    return 43 + 1 / 12 if SESSO == "M" else 42 + 1 / 12


def onere_annuo(modalita):
    """Onere di un anno di riscatto nella modalità data (€ alla data della domanda)."""
    if modalita == "agevolato":
        return MINIMALE_ARTIGIANI_COMMERCIANTI * ALIQUOTA_COMPUTO_FPLD
    return RAL_ATTUALE * ALIQUOTA_ORDINARIO


def eta_anticipata(anzianita):
    """Età di decorrenza dell'anticipata ordinaria lavorando da oggi senza interruzioni."""
    return ETA_ATTUALE + max(0.0, requisito_anticipata() - anzianita) + FINESTRA_ANTICIPATA


def scenario(modalita, anni_contributivi, anni, coeff):
    """Costo, rata, pensione in più e anni per rientrare di una modalità, sugli anni nel contributivo."""
    onere = onere_annuo(modalita) * anni_contributivi
    netto = onere * (1 - ALIQUOTA_MARGINALE_IRPEF)
    delta_montante = onere * (1 + PIL_REALE) ** anni
    delta_pensione = delta_montante * coeff
    netta = delta_pensione * (1 - ALIQUOTA_IRPEF_IN_PENSIONE)
    return {"onere": onere, "rata": onere / RATE_MENSILI, "netto": netto,
            "deduzione_annua": min(onere, onere / RATE_MENSILI * 12),
            "delta_montante": delta_montante, "delta_pensione": delta_pensione,
            "anni_rientro": netto / netta if netta > 0 else float("inf")}


def valida():
    if not 0 < ANNI_RISCATTO <= 10:
        errore(f"ANNI_RISCATTO = {ANNI_RISCATTO}: gli anni di corso legale riscattabili vanno da 0 a 10.")
    if not 0 <= ANNI_PRIMA_DEL_1996 <= ANNI_RISCATTO:
        errore(f"ANNI_PRIMA_DEL_1996 = {ANNI_PRIMA_DEL_1996}: va da 0 ad ANNI_RISCATTO ({ANNI_RISCATTO}).")
    if MODALITA not in ("agevolato", "ordinario"):
        errore(f"MODALITA = {MODALITA!r}: usa 'agevolato' oppure 'ordinario'.")
    if SESSO not in ("M", "F"):
        errore(f"SESSO = {SESSO!r}: usa 'M' oppure 'F' (decide il requisito dell'anticipata ordinaria).")
    if RATE_MENSILI != int(RATE_MENSILI) or not 1 <= RATE_MENSILI <= 120:
        errore(f"RATE_MENSILI = {RATE_MENSILI}: da 1 (unica soluzione) a 120 rate mensili.")
    for nome in ("ALIQUOTA_MARGINALE_IRPEF", "ALIQUOTA_IRPEF_IN_PENSIONE", "ALIQUOTA_COMPUTO_FPLD", "ALIQUOTA_ORDINARIO"):
        if not 0 <= globals()[nome] < 1:
            errore(f"{nome} = {globals()[nome]}: è una frazione tra 0 e 1 (0.33, non 33).")
    if ETA_PENSIONAMENTO <= ETA_ATTUALE:
        errore("ETA_PENSIONAMENTO deve superare ETA_ATTUALE.")
    # gli anni all'uscita e il coefficiente del JSON di proiezione-inps.py valgono per le sue età: un --set
    # successivo di ETA_ATTUALE o ETA_PENSIONAMENTO non li ricalcola (come in ponte-pensione.py)
    if ANNI_AL_PENSIONAMENTO is not None and abs((ETA_PENSIONAMENTO - ETA_ATTUALE) - ANNI_AL_PENSIONAMENTO) > 0.5:
        errore(f"gli anni all'uscita letti da --from ({ANNI_AL_PENSIONAMENTO}) e il coefficiente di trasformazione "
               f"valgono per un'altra età: con ETA_ATTUALE={numero(ETA_ATTUALE, 1)} ed ETA_PENSIONAMENTO="
               f"{numero(ETA_PENSIONAMENTO, 1)} rifai la proiezione (proiezione-inps.py --from dati.json --set "
               f"ETA_PENSIONAMENTO={ETA_PENSIONAMENTO} --json inps.json) e passa qui quel file insieme al JSON di "
               "importa-previdenza.py.")


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
    if COEFF_TRASFORMAZIONE is not None:
        coeff, origine = COEFF_TRASFORMAZIONE, "dal JSON di proiezione-inps.py o da --set"
    else:
        pi = _proiezione_inps()
        coeff = pi.coeff_vigente(ETA_PENSIONAMENTO) * (1 - pi.RIDUZIONE_COEFF_ANNUA) ** anni
        origine = (f"come proiezione-inps.py: tabella 2025-26 a {ETA_PENSIONAMENTO:.0f} anni ridotta del "
                   f"{pct(pi.RIDUZIONE_COEFF_ANNUA)}/anno per {anni} anni")
    anni_contributivi = ANNI_RISCATTO - ANNI_PRIMA_DEL_1996
    agev, ordi = scenario("agevolato", anni_contributivi, anni, coeff), scenario("ordinario", anni_contributivi, anni, coeff)

    print("=" * 72)
    print(f"RISCATTO DELLA LAUREA — {numero(ANNI_RISCATTO, 1 if ANNI_RISCATTO % 1 else 0)} anni, "
          "valori reali (€ di oggi)")
    print("=" * 72)
    if CONTRIBUTI_SOLO_DAL_1996:
        print("⚠ posizione mista: ci sono contributi prima del 1996. Le due colonne valgono solo per gli anni di")
        print("  corso dal 1996, che cadono nel contributivo. Per quelli precedenti l'ordinario segue la riserva")
        print("  matematica (art. 2 c. 4 D.Lgs. 184/1997, art. 13 L. 1338/1962) e lo calcola solo INPS; l'agevolato")
        print("  richiede l'opzione al contributivo (art. 1 c. 23 L. 335/1995; Circ. INPS 6/2020 e 54/2021),")
        print("  irrevocabile e su tutta la pensione: valutala con INPS o un patronato prima di pagare.")
        print()
    if ANNI_PRIMA_DEL_1996 > 0:
        print(f"⚠ {numero(ANNI_PRIMA_DEL_1996, 1)} anni di corso cadono prima del 1996: per quelli l'ordinario segue la")
        print("  riserva matematica (lo calcola solo INPS) e l'agevolato vale solo se la pensione si calcola tutta")
        print("  con il contributivo, per esempio con l'opzione dell'art. 1 c. 23 L. 335/1995. Con contributi solo")
        print("  dal 1996, riscattare anni precedenti tocca il sistema di calcolo e i canali di uscita della pensione:")
        print("  valutalo con INPS o un patronato. Onere e pensione qui sotto contano solo gli anni dal 1996;")
        print("  l'anzianità li conta tutti.")
        print()
    if anni_contributivi > 0:
        righe = [(f"Onere lordo ({numero(anni_contributivi, 1 if anni_contributivi % 1 else 0)} anni nel contributivo)",
                  "onere", 0),
                 ("Rata mensile" + (f" ({RATE_MENSILI} rate)" if RATE_MENSILI > 1 else " (unica soluzione)"), "rata", 2),
                 (f"Costo netto (deduzione al {pct(ALIQUOTA_MARGINALE_IRPEF, 0)})", "netto", 0),
                 (f"Montante in più a {ETA_PENSIONAMENTO:.0f} anni", "delta_montante", 0),
                 ("Pensione lorda annua in più", "delta_pensione", 0)]
        print(f"  {'':<44}{'agevolato':>12}{'ordinario':>14}")
        for etichetta, chiave, dec in righe:
            print(f"  {etichetta:<44}{'€ ' + numero(agev[chiave], dec):>12}{'€ ' + numero(ordi[chiave], dec):>14}")
        print(f"  {'Anni di pensione per rientrare':<44}{numero(agev['anni_rientro'], 1):>12}"
              f"{numero(ordi['anni_rientro'], 1):>14}")
        print(f"\nOnere per anno: agevolato € {numero(onere_annuo('agevolato'), 2)} "
              f"(€ {numero(MINIMALE_ARTIGIANI_COMMERCIANTI)} × {pct(ALIQUOTA_COMPUTO_FPLD, 0)}), "
              f"ordinario € {numero(onere_annuo('ordinario'), 2)} "
              f"(€ {numero(RAL_ATTUALE)} × {pct(ALIQUOTA_ORDINARIO, 0)}).")
        if onere_annuo("ordinario") < onere_annuo("agevolato"):
            print("  Con una retribuzione sotto il minimale l'ordinario costa meno dell'agevolato.")
        print("Negli anni nel contributivo i due modi rendono allo stesso modo (l'onere va tutto nel montante):")
        print("l'ordinario compra più pensione, l'agevolato gli stessi anni di anzianità al prezzo minimo.")
        print(f"Coefficiente di trasformazione: {pct(coeff, 3)} ({origine}); pensione netta in più con "
              f"l'aliquota del {pct(ALIQUOTA_IRPEF_IN_PENSIONE, 0)}.")
        modo = f"con {RATE_MENSILI} rate" if RATE_MENSILI > 1 else "con l'unica soluzione"
        print(f"Deduzione dell'anno {modo}: € {numero(agev['deduzione_annua'])} (agevolato).", end=" ")
        reddito = RAL_ATTUALE * REDDITO_SU_RAL
        soglia = SOGLIA_SCAGLIONE.get(ALIQUOTA_MARGINALE_IRPEF)
        if soglia is not None and reddito - agev["deduzione_annua"] < soglia:
            print(f"Supera la parte del reddito (≈ € {numero(reddito)}) tassata al {pct(ALIQUOTA_MARGINALE_IRPEF, 0)}:")
            print("  una parte scende allo scaglione sotto, o oltre l'imposta, e il costo netto vero è più alto di")
            print("  quello indicato; le rate spalmano la deduzione su più anni.")
        else:
            print(f"Il risparmio al {pct(ALIQUOTA_MARGINALE_IRPEF, 0)} vale finché resta nello scaglione.")
    else:
        print("Tutti gli anni di corso cadono prima del 1996: l'onere lo calcola solo INPS (riserva matematica).")

    # ------------------------- anzianità e uscita -------------------------
    con = ANZIANITA_ATTUALE + ANNI_RISCATTO
    senza_eta, con_eta = eta_anticipata(ANZIANITA_ATTUALE), eta_anticipata(con)
    chi = {"M": "uomini", "F": "donne"}[SESSO] if REQUISITO_ANTICIPATA is None else "da --set"
    print("\n" + "-" * 72)
    print(f"ANZIANITÀ: {numero(ANZIANITA_ATTUALE, 1)} anni oggi → {numero(con, 1)} con il riscatto")
    print(f"Pensione anticipata ordinaria ({numero(requisito_anticipata(), 2)} anni di contributi, requisito {chi} "
          "dal 2028, + finestra di 3 mesi),")
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
            "anni_prima_del_1996": ANNI_PRIMA_DEL_1996,
            "onere_riscatto": round(scelto["onere"], 2),
            "onere_agevolato": round(agev["onere"], 2),
            "onere_ordinario": round(ordi["onere"], 2),
            "rata_mensile": round(scelto["rata"], 2),
            "costo_netto": round(scelto["netto"], 2),
            "coefficiente_trasformazione": round(coeff, 5),
            "delta_montante_al_pensionamento": round(scelto["delta_montante"], 2),
            "delta_pensione_lorda_annua": round(scelto["delta_pensione"], 2),
            "anni_per_rientrare": round(scelto["anni_rientro"], 1),
            "anzianita_con_riscatto": round(con, 2),
            "eta_anticipata_senza_riscatto": round(senza_eta, 2),
            "eta_anticipata_con_riscatto": round(con_eta, 2),
            # per la catena: proiezione-inps.py --from riscatto.json proietta il montante con il riscatto,
            # alla stessa età di uscita (gli altri --set di scenario vanno ripetuti)
            "montante_attuale": round(MONTANTE_ATTUALE + scelto["onere"], 2),
            "ral_attuale": RAL_ATTUALE,
            "eta_attuale": ETA_ATTUALE,
            "eta_pensionamento": ETA_PENSIONAMENTO,
            "contributi_solo_dal_1996": CONTRIBUTI_SOLO_DAL_1996,
        })


if __name__ == "__main__":
    main()
