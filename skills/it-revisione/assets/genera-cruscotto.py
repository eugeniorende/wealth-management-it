#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
genera-cruscotto.py — il cruscotto grafico del piano, in un file HTML autosufficiente.

Legge i JSON che gli script del plugin scrivono con --json (allocatore, look-through del portafoglio,
glide path, Monte Carlo degli obiettivi, catena della pensione con ponte e riscatto della laurea, capitale
umano, importatore dei broker, ribilanciamento),
ne riconosce il tipo dalle chiavi, ne estrae solo i campi che la pagina mostra (il «bundle») e li
incorpora nel template cruscotto.html accanto a questo script. La pagina disegna i grafici nel
browser, senza librerie né risorse esterne: si apre dal disco, offline, e si può pubblicare come
Artifact su claude.ai, ma solo se l'utente lo chiede (vedi SKILL.md, «Cruscotto grafico»).

Uso (dalla cartella di lavoro):
    python "${CLAUDE_SKILL_DIR}/assets/genera-cruscotto.py" --from alloc.json --from mc.json ... \
        [-o cruscotto.html] [--json bundle.json] [--data AAAA-MM-GG] \
        [--archivia [CARTELLA]] [--solo-dati] [--precedente FILE|CARTELLA]

Archivio: --archivia scrive anche il bundle in CARTELLA/cruscotto-AAAA-MM-GG.json (default revisioni/, creata
se manca; la data è quella di generato_il, e un secondo lancio nello stesso giorno sovrascrive la foto del
giorno). --solo-dati compone, archivia e legge la revisione precedente senza scrivere la pagina (vuole --json o
--archivia, non accetta -o). --precedente indica la revisione con cui confrontare: un bundle, una pagina
generata dal plugin o una cartella di foto (si prende la più recente con data precedente a quella corrente).

ONESTÀ METODOLOGICA
- Il cruscotto disegna i numeri degli script, non ne calcola di nuovi: ogni valore della pagina
  è un campo di un JSON di origine, e la testata elenca i file da cui viene.
- Un JSON non riconosciuto, incompleto o doppio ferma lo script: meglio nessun grafico che un
  grafico sbagliato.
- Le singole posizioni dell'estratto (ISIN, descrizioni, quantità) non entrano nella pagina:
  dalla fiscalità passano gli aggregati per broker e le righe dello zainetto.
Questo strumento è educativo e non costituisce consulenza finanziaria o fiscale.
"""

import argparse
import datetime
import json
import os
import re
import sys

CARTELLA = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(CARTELLA, "cruscotto.html")
PLUGIN_JSON = os.path.join(CARTELLA, "..", "..", "..", ".claude-plugin", "plugin.json")
SEGNAPOSTO = "__DATI_CRUSCOTTO__"


class ErroreDati(Exception):
    """Un JSON o un parametro che il cruscotto non può usare: messaggio per «ERRORE:» e uscita con codice 1."""


def numero(x, decimali=0):
    """Numero in formato italiano: punto per le migliaia, virgola per i decimali (come genera-ips.py:
    questa skill non ha il motore)."""
    testo = f"{x:,.{decimali}f}"
    return testo.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def _ha(d, *chiavi):
    return isinstance(d, dict) and all(k in d for k in chiavi)


def _primo(d, chiave):
    """Il primo elemento della lista d[chiave], o {} se non c'è (per le firme sugli obiettivi)."""
    v = d.get(chiave)
    return v[0] if isinstance(v, list) and v and isinstance(v[0], dict) else {}


# ═══════════════════════════ FIRME DEI JSON ═══════════════════════════
# Il tipo di un file si riconosce dalle chiavi di primo livello: i JSON degli script non hanno un
# campo «tipo». Firme verificate sugli output degli esempi del plugin (il test T17 le rilancia):
# se uno script cambia le sue chiavi, quel test fallisce e la riga qui va aggiornata.
FIRME = [
    ("allocatore",      lambda d: _ha(d, "aggregato", "capitale") and "allocato" in _primo(d, "obiettivi")),
    ("look_through",    lambda d: _ha(d, "copertura", "settori", "paesi", "titoli", "controvalore_totale")),
    ("glide_path",      lambda d: _ha(d, "anni", "portafoglio", "finestra") and "quota_azionaria" in _primo(d, "obiettivi")),
    ("mc_obiettivi",    lambda d: _ha(d, "n_sim") and "probabilita_successo" in _primo(d, "obiettivi")),
    ("inps",            lambda d: _ha(d, "pensione_inps_lorda_annua", "coefficiente_trasformazione")),
    ("mc_pensione",     lambda d: _ha(d, "tasso_sostituzione_lordo", "montante_fp") and isinstance(d["tasso_sostituzione_lordo"], dict)),
    ("netto_pensione",  lambda d: _ha(d, "scenari", "netto_pensione_inps")),
    ("ponte",           lambda d: _ha(d, "anni_ponte", "capitale_ponte")),
    ("riscatto",        lambda d: _ha(d, "onere_riscatto", "anni_riscatto")),
    ("capitale_umano",  lambda d: _ha(d, "bilancio", "proiezione", "esposizione_totale")),
    ("broker",          lambda d: _ha(d, "posizioni", "zainetto", "analisi") and _ha(d["analisi"], "per_broker")),
    ("ribilanciamento", lambda d: _ha(d, "drift", "risultante", "ordini")),
]
# JSON di altri script del plugin che il cruscotto riconosce e salta (la catena si passa intera)
IGNORATI = [
    ("importa-previdenza", lambda d: _ha(d, "montante_attuale", "ral_attuale", "fp_versamento_annuo")),
]
ORDINE = [t for t, _ in FIRME]


def riconosci(dati):
    """Il tipo del JSON (una chiave di FIRME), «ignorato:<script>» per gli IGNORATI, None se nessuna firma."""
    for tipo, firma in FIRME:
        if firma(dati):
            return tipo
    for nome, firma in IGNORATI:
        if firma(dati):
            return f"ignorato:{nome}"
    return None


# ═══════════════════════════ LETTURA DEI CAMPI ═══════════════════════════

def campo(dati, percorso, file, dove=""):
    """Il valore di una chiave puntata («a.b.c»); ErroreDati con file e chiave se manca. `dove` è il percorso
    dell'oggetto dentro il file (es. «obiettivi[1].»), per il messaggio."""
    v = dati
    for parte in percorso.split("."):
        if not isinstance(v, dict) or parte not in v:
            raise ErroreDati(f"«{file}»: manca {dove}{percorso}")
        v = v[parte]
    return v


def numero_di(dati, percorso, file, nullo=False, dove=""):
    """Come campo(), ma il valore deve essere un numero (o None, se nullo=True)."""
    v = campo(dati, percorso, file, dove)
    if v is None and nullo:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ErroreDati(f"«{file}»: {dove}{percorso} non è un numero ({v!r})")
    return v


def lista_di(dati, percorso, file):
    v = campo(dati, percorso, file)
    if not isinstance(v, list):
        raise ErroreDati(f"«{file}»: {percorso} non è una lista")
    return v


def estrai(elemento, chiavi, file, dove):
    """Le chiavi indicate di un elemento di lista, con il percorso dell'elemento nel messaggio d'errore."""
    if not isinstance(elemento, dict):
        raise ErroreDati(f"«{file}»: {dove} non è un oggetto")
    for k in chiavi:
        if k not in elemento:
            raise ErroreDati(f"«{file}»: manca {dove}.{k}")
    return {k: elemento[k] for k in chiavi}


def percentili(dati, percorso, file, dove=""):
    """P10, mediana e P90 di un oggetto di percentili, tutti numeri."""
    return {k: numero_di(dati, f"{percorso}.{k}", file, dove=dove) for k in ("p10", "mediana", "p90")}


# ═══════════════════════════ IL BUNDLE ═══════════════════════════

def _allocazione(alloc, rib):
    if not alloc and not rib:
        return None
    sezione = {"target_aggregato": None, "obiettivi": [], "classi": None}
    if alloc:
        f, d = alloc
        sezione["target_aggregato"] = {k: numero_di(d, f"aggregato.{k}", f) for k in ("azioni", "obbligazioni", "liquidita", "totale")}
        sezione["capitale"] = numero_di(d, "capitale", f)
        sezione["obiettivi"] = [estrai(o, ("nome", "profilo", "tipo", "richiesto", "allocato", "peso_az"), f, f"obiettivi[{i}]")
                                for i, o in enumerate(lista_di(d, "obiettivi", f))]
    if rib:
        f, d = rib
        risultante = campo(d, "risultante", f)
        sezione["classi"] = []
        for classe, dr in campo(d, "drift", f).items():
            riga = estrai(dr, ("peso", "target", "tight", "wide", "fuori_banda"), f, f"drift.{classe}")
            riga["classe"] = classe
            riga["risultante"] = risultante.get(classe) if isinstance(risultante, dict) else None
            sezione["classi"].append(riga)
    return sezione


def _look_through(lt):
    """Solo gli aggregati del look-through: le posizioni dell'utente (nomi, ISIN) restano fuori dalla pagina,
    ne passa il numero e la quota di quelle senza composizione. Paesi oltre i primi dieci sommati in «altri», valute oltre le
    prime otto in «altre N valute» («altra 1 valuta» se una sola). Regioni, valute e quota in euro sono facoltative (un
    JSON della 0.12.0 non le ha): se mancano valgono None e la pagina salta i due grafici. Gli ISIN dei titoli non passano."""
    if not lt:
        return None
    f, d = lt
    def voci(chiave):
        return [{"nome": str(campo(x, "nome", f, f"{chiave}[{i}].")), "peso": numero_di(x, "peso", f, dove=f"{chiave}[{i}].")}
                for i, x in enumerate(lista_di(d, chiave, f))]
    paesi, altri = voci("paesi")[:10], voci("paesi")[10:]
    if altri:
        paesi.append({"nome": f"altri {len(altri)} paesi", "peso": sum(p["peso"] for p in altri)})
    valute = voci("valute") if "valute" in d else None
    if valute is not None and len(valute) > 8:
        resto = valute[8:]
        valute = valute[:8] + [{"nome": "altra 1 valuta" if len(resto) == 1 else f"altre {len(resto)} valute", "peso": sum(v["peso"] for v in resto)}]
    copertura = {k: numero_di(d, f"copertura.{k}", f) for k in ("settori", "paesi", "titoli")}
    for k in ("regioni", "valute"):
        if k in d:
            copertura[k] = numero_di(d, f"copertura.{k}", f)
    senza = lista_di(d, "senza_composizione", f)
    # i titoli «diretti» sono posizioni dell'utente descritte a mano: restano fuori dalla pagina, se ne dice il numero
    n_report = numero_di(d, "n_titoli_report", f)
    titoli = [t for t, x in zip(voci("titoli"), lista_di(d, "titoli", f)) if not x.get("diretto")]
    return {
        "copertura": copertura,
        "settori": voci("settori"), "regioni": voci("regioni") if "regioni" in d else None, "paesi": paesi,
        "valute": valute, "quota_euro": numero_di(d, "quota_euro", f, nullo=True) if "quota_euro" in d else None,
        "titoli": titoli[:n_report],
        "n_titoli_diretti": len(voci("titoli")) - len(titoli),
        "quota_primi_titoli": numero_di(d, "quota_primi_titoli", f),
        "n_posizioni": len(lista_di(d, "posizioni", f)) + len(senza),
        "n_senza_composizione": len(senza),
        "quota_senza_composizione": sum(numero_di(x, "quota", f, dove=f"senza_composizione[{i}].") for i, x in enumerate(senza)),
    }


def _obiettivi(mco):
    if not mco:
        return None
    f, d = mco
    chiavi = ("nome", "profilo", "priorita", "anni", "target_oggi", "target_nominale", "gia", "probabilita_successo",
              "versamento_deterministico", "versamento_confidenza", "confidenza")
    obiettivi = []
    for i, o in enumerate(lista_di(d, "obiettivi", f)):
        riga = estrai(o, chiavi, f, f"obiettivi[{i}]")
        riga["capitale_finale"] = percentili(o, "capitale_finale", f, dove=f"obiettivi[{i}].")
        obiettivi.append(riga)
    return {"modello": campo(d, "modello", f), "n_sim": numero_di(d, "n_sim", f), "obiettivi": obiettivi,
            "totale_versamento_deterministico": numero_di(d, "totale_versamento_deterministico", f),
            "totale_versamento_confidenza": numero_di(d, "totale_versamento_confidenza", f)}


def _glide_path(gp):
    if not gp:
        return None
    f, d = gp
    return {"anni": lista_di(d, "anni", f), "portafoglio": lista_di(d, "portafoglio", f),
            "obiettivi": [estrai(o, ("nome", "quota_azionaria", "capitale_proiettato"), f, f"obiettivi[{i}]")
                          for i, o in enumerate(lista_di(d, "obiettivi", f))]}


def _pensione(inps, mc, netto, ponte=None, riscatto=None):
    if not (inps or mc or netto or ponte or riscatto):
        return None
    sezione = {"inps": None, "tasso_lordo": None, "target": None, "prob_target": None, "montante_fp": None, "netto": None,
               "ponte": None, "riscatto": None}
    if inps:
        f, d = inps
        sezione["inps"] = {k: numero_di(d, k, f) for k in ("pensione_inps_lorda_annua", "eta_pensionamento",
                                                           "anni_al_pensionamento", "montante_finale", "ral_finale")}
    if mc:
        f, d = mc
        sezione["tasso_lordo"] = percentili(d, "tasso_sostituzione_lordo", f)
        sezione["montante_fp"] = percentili(d, "montante_fp", f)
        sezione["target"] = numero_di(d, "target", f)
        sezione["prob_target"] = numero_di(d, "prob_target", f)
    if netto:
        f, d = netto
        sezione["netto"] = {
            "netto_ultimo_stipendio": numero_di(d, "netto_ultimo_stipendio", f),
            "netto_pensione_inps": numero_di(d, "netto_pensione_inps", f),
            "scenari": [estrai(s, ("nome", "pensione_netta_totale", "tasso_sostituzione_netto", "tasso_sostituzione_lordo"),
                               f, f"scenari[{i}]") for i, s in enumerate(lista_di(d, "scenari", f))]}
    if ponte:
        f, d = ponte
        sezione["ponte"] = {k: numero_di(d, k, f) for k in ("eta_uscita", "eta_pensione_vecchiaia", "anni_ponte", "capitale_ponte",
                                                            "probabilita_successo", "costo_permanente_lordo_annuo")}
        sezione["ponte"]["capitale_necessario"] = {k: numero_di(d, f"capitale_necessario.{k}", f) for k in ("85%", "95%")}
        sezione["ponte"]["rita"] = {"attiva": campo(d, "rita.attiva", f),
                                    "eta_inizio": numero_di(d, "rita.eta_inizio", f, nullo=True),
                                    "rata_netta": numero_di(d, "rita.rata_netta", f, nullo=True)}
    if riscatto:
        f, d = riscatto
        sezione["riscatto"] = {"modalita": campo(d, "modalita", f)}
        sezione["riscatto"].update({k: numero_di(d, k, f) for k in ("anni_riscatto", "onere_agevolato", "onere_ordinario",
                                                                    "costo_netto", "rata_mensile", "rate_mensili",
                                                                    "delta_pensione_lorda_annua", "eta_pensionamento")})
        sezione["riscatto"].update({k: numero_di(d, k, f, nullo=True) for k in ("anni_per_rientrare", "eta_anticipata_senza_riscatto",
                                                                                "eta_anticipata_con_riscatto")})
    return sezione


def _capitale_umano(cu):
    if not cu:
        return None
    f, d = cu
    settore = d.get("settore")
    if settore is not None:
        settore = estrai(settore, ("settore", "quota_settore_fin", "peso_mondo", "sovrappeso"), f, "settore")
    return {
        "voci": [estrai(v, ("nome", "valore"), f, f"bilancio.voci[{i}]") for i, v in enumerate(lista_di(d, "bilancio.voci", f))],
        "esposizione_finanziaria": numero_di(d, "esposizione_finanziaria", f, nullo=True),
        "esposizione_totale": numero_di(d, "esposizione_totale", f),
        "proiezione": [estrai(r, ("eta", "F", "HC", "esposizione", "p10", "p90"), f, f"proiezione[{i}]")
                       for i, r in enumerate(lista_di(d, "proiezione", f))],
        "eta_sorpasso": numero_di(d, "eta_sorpasso", f, nullo=True),
        "stato_sorpasso": campo(d, "stato_sorpasso", f),
        "settore": settore,
    }


def _fiscalita(br):
    if not br:
        return None
    f, d = br
    totali = {k: numero_di(d, f"analisi.{k}", f) for k in (
        "totale_valore", "zainetto_26_equivalente", "zainetto_in_scadenza", "zainetto_scaduto",
        "plus_latenti_compensabili", "plus_realizzabili_a_costo_zero", "imposta_risparmiabile")}
    per_broker = {}
    for nome, b in campo(d, "analisi.per_broker", f).items():
        per_broker[nome] = estrai(b, ("plus_latenti_compensabili", "zainetto_26_equivalente", "zainetto_in_scadenza",
                                      "plus_realizzabili_a_costo_zero", "imposta_risparmiabile"), f, f"analisi.per_broker.{nome}")
    zainetto = [estrai(z, ("broker", "anno", "scade_il", "stato", "importo_26_equivalente"), f, f"zainetto[{i}]")
                for i, z in enumerate(lista_di(d, "zainetto", f))]
    avvisi, omessi = _avvisi_senza_posizioni(d, per_broker)
    return {"totali": totali, "per_broker": per_broker, "zainetto": zainetto, "avvisi": avvisi, "avvisi_omessi": omessi}


def _avvisi_senza_posizioni(d, per_broker):
    """Gli avvisi dell'importatore che possono entrare nella pagina: quelli dello zainetto e dei broker, mai
    quelli che nominano una posizione (descrizione o ISIN) o una riga dell'estratto. Ritorna (avvisi, omessi)."""
    nomi = [str(p.get(k)) for p in d.get("posizioni") or [] if isinstance(p, dict)
            for k in ("isin", "descrizione") if p.get(k)]
    tenuti, omessi = [], 0
    for a in d.get("avvisi") or []:
        a = str(a)
        di_broker = any(a.startswith(f"{b}: ") for b in per_broker)
        if (a.startswith("zainetto") or di_broker) and not any(n in a for n in nomi):
            tenuti.append(a)
        else:
            omessi += 1
    return tenuti, omessi


def _ribilanciamento(rib):
    if not rib:
        return None
    f, d = rib
    drift = {cl: estrai(dr, ("peso", "target", "drift", "tight", "wide", "fuori_banda", "esito", "motivo"), f, f"drift.{cl}")
             for cl, dr in campo(d, "drift", f).items()}
    ordini = [estrai(o, ("broker", "operazione", "classe", "categoria_fiscale", "importo_eur", "imposta_eur", "nota"),
                     f, f"ordini[{i}]") for i, o in enumerate(lista_di(d, "ordini", f))]
    # un JSON di prima della revisione finale non ha dati_esempio: vale come dati dell'utente
    return {k: numero_di(d, k, f) for k in ("totale", "totale_post", "imposta", "prelievo")} | {
        "drift": drift, "risultante": campo(d, "risultante", f), "zainetto": campo(d, "zainetto", f), "ordini": ordini,
        "dati_esempio": d.get("dati_esempio") is True}


def _indicatori(b):
    """La riga in testata: un indicatore c'è solo se c'è la sua fonte, sempre con l'etichetta della fonte."""
    ind = []
    if b["allocazione"] and b["allocazione"].get("capitale") is not None:
        ind.append({"id": "capitale_allocato", "etichetta": "Capitale allocato", "valore": b["allocazione"]["capitale"],
                    "formato": "euro", "fonte": "allocatore", "nota": ""})
    if b["fiscalita"]:
        ind.append({"id": "valore_portafoglio", "etichetta": "Valore in portafoglio",
                    "valore": b["fiscalita"]["totali"]["totale_valore"], "formato": "euro", "fonte": "estratto del broker", "nota": ""})
    if b["obiettivi"]:
        essenziali = [o for o in b["obiettivi"]["obiettivi"] if o["priorita"] == "essenziale"]
        if essenziali:
            peggiore = min(essenziali, key=lambda o: o["probabilita_successo"])
            ind.append({"id": "probabilita_essenziali", "etichetta": "Probabilità minima degli obiettivi essenziali",
                        "valore": peggiore["probabilita_successo"], "formato": "percento",
                        "fonte": "Monte Carlo degli obiettivi", "nota": peggiore["nome"]})
    netto = b["pensione"] and b["pensione"]["netto"]
    if netto:
        mediana = next((s for s in netto["scenari"] if s["nome"] == "mediana"), None)
        if mediana:
            ind.append({"id": "sostituzione_netta", "etichetta": "Tasso di sostituzione netto (mediana)",
                        "valore": mediana["tasso_sostituzione_netto"], "formato": "percento",
                        "fonte": "netto della pensione", "nota": ""})
    if b["fiscalita"]:
        ind.append({"id": "zainetto_in_scadenza", "etichetta": "Zainetto in scadenza al 31/12",
                    "valore": b["fiscalita"]["totali"]["zainetto_in_scadenza"], "formato": "euro",
                    "fonte": "estratto del broker", "nota": ""})
    return ind


def componi_bundle(sorgenti, data, versione_plugin):
    """Il bundle della pagina da {tipo: (nome del file, JSON)}. Chiavi delle sezioni (le legge cruscotto.html):
    - allocazione: target_aggregato {azioni, obbligazioni, liquidita, totale} | None, capitale, obiettivi
      [{nome, profilo, tipo, richiesto, allocato, peso_az}], classi [{classe, peso, target, tight, wide,
      fuori_banda, risultante}] | None (dal ribilanciamento);
    - look_through: copertura {settori, paesi, titoli, e regioni, valute se il JSON le ha}, settori e titoli [{nome, peso}]
      (i titoli delle posizioni dirette esclusi, contati in n_titoli_diretti), paesi [{nome, peso}] con «altri N paesi»
      oltre i primi dieci, regioni [{nome, peso}] | None, valute [{nome, peso}] | None (le prime otto, poi «altre N valute»),
      quota_euro (quota in euro della parte coperta dalle valute) | None; senza le chiavi nuove, None;
      quota_primi_titoli, n_posizioni, n_senza_composizione, quota_senza_composizione;
    - obiettivi: modello, n_sim, obiettivi [{nome, profilo, priorita, anni, target_oggi, target_nominale, gia,
      probabilita_successo, capitale_finale {p10, mediana, p90}, versamento_deterministico,
      versamento_confidenza, confidenza}], totale_versamento_deterministico, totale_versamento_confidenza;
    - glide_path: anni, portafoglio, obiettivi [{nome, quota_azionaria, capitale_proiettato}];
    - pensione: inps {pensione_inps_lorda_annua, eta_pensionamento, anni_al_pensionamento, montante_finale,
      ral_finale} | None, tasso_lordo e montante_fp {p10, mediana, p90} | None, target, prob_target,
      netto {netto_ultimo_stipendio, netto_pensione_inps, scenari [{nome, pensione_netta_totale,
      tasso_sostituzione_netto, tasso_sostituzione_lordo}]} | None, ponte {eta_uscita, eta_pensione_vecchiaia,
      anni_ponte, capitale_ponte, probabilita_successo, capitale_necessario {85%, 95%}, rita {attiva, eta_inizio,
      rata_netta}, costo_permanente_lordo_annuo} | None, riscatto {modalita, anni_riscatto, onere_agevolato,
      onere_ordinario, costo_netto, rata_mensile, rate_mensili, delta_pensione_lorda_annua, eta_pensionamento, anni_per_rientrare,
      eta_anticipata_senza_riscatto, eta_anticipata_con_riscatto} | None;
    - capitale_umano: voci [{nome, valore}], esposizione_finanziaria, esposizione_totale, proiezione
      [{eta, F (patrimonio finanziario), HC (capitale umano), esposizione, p10, p90}], eta_sorpasso, stato_sorpasso, settore {settore, quota_settore_fin,
      peso_mondo, sovrappeso} | None;
    - fiscalita: totali, per_broker, zainetto [{broker, anno, scade_il, stato, importo_26_equivalente}], avvisi
      (solo quelli di zainetto e broker), avvisi_omessi (quanti nominavano una posizione);
    - ribilanciamento: totale, totale_post, imposta, prelievo, drift {classe: {peso, target, drift, tight, wide,
      fuori_banda, esito, motivo}}, risultante, zainetto, ordini [{broker, operazione, classe,
      categoria_fiscale, importo_eur, imposta_eur, nota}], dati_esempio (il piano gira sull'esempio dello script).
    - confronto e anonimo: None (li compilano il confronto con la revisione precedente e la versione anonimizzata).
    Una sezione senza fonte è None. ErroreDati per un campo mancante, con il file e la chiave."""
    s = sorgenti.get
    bundle = {
        "versione": 2,
        "generato_il": data,
        "plugin": versione_plugin,
        "fonti": [{"file": sorgenti[t][0], "tipo": t} for t in ORDINE if t in sorgenti],
        "allocazione": _allocazione(s("allocatore"), s("ribilanciamento")),
        "look_through": _look_through(s("look_through")),
        "obiettivi": _obiettivi(s("mc_obiettivi")),
        "glide_path": _glide_path(s("glide_path")),
        "pensione": _pensione(s("inps"), s("mc_pensione"), s("netto_pensione"), s("ponte"), s("riscatto")),
        "capitale_umano": _capitale_umano(s("capitale_umano")),
        "fiscalita": _fiscalita(s("broker")),
        "ribilanciamento": _ribilanciamento(s("ribilanciamento")),
        "confronto": None,
        "anonimo": None,
    }
    bundle["indicatori"] = _indicatori(bundle)
    return bundle


def incorpora(template, bundle):
    """Il template con il bundle al posto del segnaposto. Ogni «<» del JSON diventa \\u003c: nessuna stringa
    dei dati può chiudere il tag <script> che lo contiene."""
    if template.count(SEGNAPOSTO) != 1:
        raise ErroreDati(f"il template deve contenere {SEGNAPOSTO} esattamente una volta "
                         f"(trovato {template.count(SEGNAPOSTO)} volte): reinstallare il plugin")
    dati = json.dumps(bundle, ensure_ascii=False).replace("<", "\\u003c")
    return template.replace(SEGNAPOSTO, dati)


_RE_DATI = re.compile(r'<script id="dati" type="application/json">(.*?)</script>', re.S)


def estrai_bundle_da_pagina(html):
    """Il bundle incorporato in una pagina del plugin (blocco <script id="dati" type="application/json">),
    o None se il blocco manca, contiene ancora il segnaposto del template o non è un JSON."""
    m = _RE_DATI.search(html)
    if not m or SEGNAPOSTO in m.group(1):
        return None
    try:
        return json.loads(m.group(1))
    except ValueError:
        return None


def _bundle_da_file(percorso):
    """(nome del file, bundle) letto da un bundle JSON o da una pagina del plugin; ErroreDati se non lo è."""
    nome = os.path.basename(percorso)
    try:
        with open(percorso, encoding="utf-8") as f:
            testo = f.read()
    except UnicodeDecodeError:
        raise ErroreDati(f"«{nome}» non è una revisione del cruscotto: non è un testo")
    except OSError as e:
        raise ErroreDati(f"impossibile leggere «{percorso}»: {e}")
    try:
        bundle = json.loads(testo)
    except ValueError:
        bundle = estrai_bundle_da_pagina(testo)
        if bundle is None:
            if SEGNAPOSTO in testo:
                raise ErroreDati(f"«{nome}» è il template del cruscotto, senza dati: serve una pagina già generata "
                                 "o un bundle")
            raise ErroreDati(f"«{nome}» non è una revisione del cruscotto (né un bundle né una pagina del plugin)")
    if not _ha(bundle, "versione", "generato_il", "fonti"):
        raise ErroreDati(f"«{nome}» non è una revisione del cruscotto (né un bundle né una pagina del plugin)")
    if bundle["versione"] not in (1, 2) or isinstance(bundle["versione"], bool):
        raise ErroreDati(f"«{nome}»: versione {bundle['versione']!r} del bundle sconosciuta "
                         "(si leggono la 1 e la 2): aggiornare il plugin")
    if bundle.get("anonimo") is not None:
        raise ErroreDati(f"«{nome}» è una versione anonimizzata: i suoi numeri sono riscalati, "
                         "non si confronta con una revisione anonimizzata")
    try:
        datetime.date.fromisoformat(str(bundle["generato_il"]))
    except ValueError:
        raise ErroreDati(f"«{nome}»: generato_il {bundle['generato_il']!r} non è una data AAAA-MM-GG")
    return nome, bundle


def leggi_precedente(percorso, data_corrente):
    """(nome del file, bundle) della revisione precedente a data_corrente. `percorso` è un bundle JSON, una
    pagina del plugin o una cartella: tra i suoi cruscotto-*.json si prende la foto con il generato_il più
    recente tra quelli precedenti a data_corrente (la data è il generato_il, non il nome del file). Gli altri
    file della cartella si ignorano; una foto illeggibile ferma la lettura e si nomina, senza saltare a una più
    vecchia. ErroreDati se manca il percorso o la foto, o se la revisione non è utilizzabile."""
    if os.path.isdir(percorso):
        foto = sorted(f for f in os.listdir(percorso)
                      if f.startswith("cruscotto-") and f.endswith(".json") and os.path.isfile(os.path.join(percorso, f)))
        precedenti = []
        for f in foto:
            nome, bundle = _bundle_da_file(os.path.join(percorso, f))
            if str(bundle["generato_il"]) < data_corrente:
                precedenti.append((str(bundle["generato_il"]), nome, bundle))
        if not precedenti:
            raise ErroreDati(f"nessuna revisione precedente al {data_corrente} nella cartella «{percorso}» "
                             "(cercati i cruscotto-*.json)")
        precedenti.sort(key=lambda t: (t[0], t[1]))
        _, nome, bundle = precedenti[-1]
        return nome, bundle
    if not os.path.exists(percorso):
        raise ErroreDati(f"--precedente: «{percorso}» non trovato")
    nome, bundle = _bundle_da_file(percorso)
    if str(bundle["generato_il"]) >= data_corrente:
        raise ErroreDati(f"«{nome}» è del {bundle['generato_il']}: la data non è precedente a quella corrente "
                         f"({data_corrente}), non è una revisione precedente")
    return nome, bundle


def archivia(bundle, cartella):
    """Scrive il bundle in cartella/cruscotto-<generato_il>.json, creando la cartella. Ritorna (percorso,
    se ha sovrascritto la foto dello stesso giorno). ErroreDati se non si può scrivere."""
    percorso = os.path.join(cartella, f"cruscotto-{bundle['generato_il']}.json")
    sovrascritta = os.path.isfile(percorso)
    try:
        os.makedirs(cartella, exist_ok=True)
        with open(percorso, "w", encoding="utf-8") as f:
            f.write(json.dumps(bundle, ensure_ascii=False, indent=2))
    except OSError as e:
        raise ErroreDati(f"impossibile scrivere {percorso}: {e}")
    return percorso, sovrascritta


def _controlla_scrivibile(percorso):
    """Prima della prima scrittura: ErroreDati se `percorso` (un file) non si potrà scrivere, perché la sua
    cartella è un file o un file esiste già al posto di una cartella, o il percorso è una cartella."""
    p = os.path.abspath(percorso)
    if os.path.isdir(p):
        raise ErroreDati(f"impossibile scrivere {percorso}: è una cartella")
    cartella = os.path.dirname(p)
    while not os.path.exists(cartella):
        cartella = os.path.dirname(cartella)
    if not os.path.isdir(cartella):
        raise ErroreDati(f"impossibile scrivere {percorso}: «{cartella}» non è una cartella")
    if not os.access(cartella, os.W_OK | os.X_OK):
        raise ErroreDati(f"impossibile scrivere {percorso}: «{cartella}» non è scrivibile")
    if os.path.exists(p) and not os.access(p, os.W_OK):
        raise ErroreDati(f"impossibile scrivere {percorso}: file non scrivibile")


# ═══════════════════════════ RIGA DI COMANDO ═══════════════════════════

def leggi_sorgenti(percorsi):
    """{tipo: (nome del file, JSON)} dai --from, più l'elenco degli ignorati [(file, script)]."""
    sorgenti, ignorati = {}, []
    for percorso in percorsi:
        nome = os.path.basename(percorso)
        try:
            with open(percorso, encoding="utf-8-sig") as f:
                dati = json.load(f)
        except FileNotFoundError:
            raise ErroreDati(f"«{percorso}» non trovato")
        except json.JSONDecodeError as e:
            raise ErroreDati(f"«{nome}» non è un JSON valido: {e}")
        except OSError as e:
            raise ErroreDati(f"impossibile leggere «{percorso}»: {e}")
        if not isinstance(dati, dict):
            raise ErroreDati(f"«{nome}» non è un oggetto JSON: il cruscotto legge i --json degli script del plugin")
        tipo = riconosci(dati)
        if tipo is None:
            raise ErroreDati(f"«{nome}» non è un output riconosciuto. Tipi accettati: {', '.join(ORDINE)} "
                             "(i --json di allocatore, look-through del portafoglio, glide path, Monte Carlo degli "
                             "obiettivi, proiezione INPS, Monte Carlo e netto della pensione, ponte pensione, riscatto della "
                             "laurea, capitale umano, importatore dei broker, ribilanciamento)")
        if tipo.startswith("ignorato:"):
            ignorati.append((nome, tipo.split(":", 1)[1]))
            continue
        if tipo in sorgenti:
            raise ErroreDati(f"«{sorgenti[tipo][0]}» e «{nome}» sono dello stesso tipo ({tipo}): passane uno solo, "
                             "il cruscotto non sceglie al posto tuo")
        sorgenti[tipo] = (nome, dati)
    return sorgenti, ignorati


def versione_plugin():
    try:
        with open(PLUGIN_JSON, encoding="utf-8") as f:
            return str(json.load(f).get("version", "?"))
    except (OSError, ValueError):
        return "?"


def _valore(ind):
    if ind["formato"] == "euro":
        return f"€{numero(ind['valore'])}"
    return f"{numero(ind['valore'] * 100, 1)}%"


def main(argv=None):
    for flusso in (sys.stdout, sys.stderr):   # UTF-8 anche su Windows (cp1252)
        try:
            flusso.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(
        allow_abbrev=False,
        description="Cruscotto grafico del piano: legge i JSON scritti con --json dagli script del plugin e genera "
                    "una pagina HTML autosufficiente con i grafici (nessuna risorsa esterna). "
                    "Codici d'uscita: 0 riuscito, 1 errore nei dati o nella scrittura, 2 riga di comando errata.")
    ap.add_argument("--from", dest="sorgenti", metavar="FILE", action="append",
                    help="JSON di uno script del plugin (ripetibile, l'ordine non conta)")
    ap.add_argument("-o", "--output", metavar="FILE",
                    help="la pagina da scrivere (default: cruscotto.html nella cartella corrente)")
    ap.add_argument("--json", metavar="FILE", help="scrive anche il bundle, cioè i dati che finiscono nella pagina")
    ap.add_argument("--data", metavar="AAAA-MM-GG", help="data in testata (default: oggi)")
    ap.add_argument("--archivia", nargs="?", const="revisioni", metavar="CARTELLA",
                    help="scrive anche il bundle in CARTELLA/cruscotto-AAAA-MM-GG.json (default: revisioni/; "
                         "un secondo lancio nello stesso giorno sovrascrive la foto del giorno)")
    ap.add_argument("--solo-dati", action="store_true",
                    help="compone, archivia e confronta senza scrivere la pagina (vuole --json o --archivia, non -o)")
    ap.add_argument("--precedente", metavar="FILE|CARTELLA",
                    help="la revisione con cui confrontare: un bundle, una pagina del plugin o una cartella di foto")
    args = ap.parse_args(argv)
    if not args.sorgenti:
        ap.error("serve almeno un --from FILE")
    if args.solo_dati and args.output:
        ap.error("--solo-dati non scrive la pagina: non si usa con -o")
    if args.solo_dati and not (args.json or args.archivia):
        ap.error("--solo-dati vuole --json o --archivia: altrimenti non scrive nulla")
    if not args.solo_dati and not args.output:
        args.output = "cruscotto.html"
    try:
        data = datetime.date.today().isoformat()
        if args.data:
            try:
                data = datetime.date.fromisoformat(args.data).isoformat()
            except ValueError:
                raise ErroreDati(f"--data {args.data}: data non valida, il formato è AAAA-MM-GG")
        sorgenti, ignorati = leggi_sorgenti(args.sorgenti)
        if not sorgenti:
            raise ErroreDati("nessun JSON che il cruscotto sappia disegnare tra quelli passati")
        if args.precedente:
            leggi_precedente(args.precedente, data)    # il confronto vero e proprio è un passo successivo
        bundle = componi_bundle(sorgenti, data, versione_plugin())
        html = None
        if not args.solo_dati:
            with open(TEMPLATE, encoding="utf-8") as f:
                html = incorpora(f.read(), bundle)
        # tutti i controlli prima della prima scrittura: un errore non lascia file a metà
        testo_bundle = json.dumps(bundle, ensure_ascii=False, indent=2)
        if args.archivia:
            _controlla_scrivibile(os.path.join(args.archivia, f"cruscotto-{bundle['generato_il']}.json"))
        for percorso in (args.output, args.json):
            if percorso:
                _controlla_scrivibile(percorso)
        archiviato = archivia(bundle, args.archivia) if args.archivia else None
        for percorso, testo in ((args.output, html), (args.json, testo_bundle)):
            if percorso:
                try:
                    with open(percorso, "w", encoding="utf-8") as f:
                        f.write(testo)
                except OSError as e:
                    raise ErroreDati(f"impossibile scrivere {percorso}: {e}")
    except ErroreDati as e:
        print(f"ERRORE: {e}", file=sys.stderr)
        raise SystemExit(1)

    if args.solo_dati:
        print("Dati del cruscotto: nessuna pagina scritta")
    else:
        print(f"Cruscotto: {args.output}")
    if archiviato:
        print(f"Archiviato: {archiviato[0]}" + (" (sovrascritta la foto dello stesso giorno)" if archiviato[1] else ""))
    for fonte in bundle["fonti"]:
        print(f"  {fonte['file']} → {fonte['tipo']}")
    for nome, script in ignorati:
        print(f"  ℹ {nome} ({script}) ignorato: il cruscotto non lo usa")
    sezioni = [k for k in ("allocazione", "look_through", "obiettivi", "glide_path", "pensione", "capitale_umano",
                           "fiscalita", "ribilanciamento") if bundle[k]]
    print(f"Sezioni: {', '.join(sezioni)}")
    for ind in bundle["indicatori"]:
        nota = f" ({ind['nota']})" if ind["nota"] else ""
        print(f"  {ind['etichetta']}: {_valore(ind)}{nota}")
    if args.json:
        print(f"Bundle: {args.json}")
    if not args.solo_dati:
        print("Il file resta nella cartella di lavoro. Pubblicarlo come Artifact lo mette su claude.ai: "
              "farlo solo su richiesta esplicita.")
    print("Strumento educativo: non costituisce consulenza finanziaria o fiscale.")


if __name__ == "__main__":
    main()
