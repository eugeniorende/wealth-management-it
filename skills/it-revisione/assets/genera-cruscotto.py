#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
genera-cruscotto.py — il cruscotto grafico del piano, in un file HTML autosufficiente.

Legge i JSON che gli script del plugin scrivono con --json (allocatore, glide path, Monte Carlo
degli obiettivi, catena della pensione, capitale umano, importatore dei broker, ribilanciamento),
ne riconosce il tipo dalle chiavi, ne estrae solo i campi che la pagina mostra (il «bundle») e li
incorpora nel template cruscotto.html accanto a questo script. La pagina disegna i grafici nel
browser, senza librerie né risorse esterne: si apre dal disco, offline, e si può pubblicare come
Artifact su claude.ai, ma solo se l'utente lo chiede (vedi SKILL.md, «Cruscotto grafico»).

Uso (dalla cartella di lavoro):
    python "${CLAUDE_SKILL_DIR}/assets/genera-cruscotto.py" --from alloc.json --from mc.json ... \
        [-o cruscotto.html] [--json bundle.json] [--data AAAA-MM-GG]

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
    ("glide_path",      lambda d: _ha(d, "anni", "portafoglio", "finestra") and "quota_azionaria" in _primo(d, "obiettivi")),
    ("mc_obiettivi",    lambda d: _ha(d, "n_sim") and "probabilita_successo" in _primo(d, "obiettivi")),
    ("inps",            lambda d: _ha(d, "pensione_inps_lorda_annua", "coefficiente_trasformazione")),
    ("mc_pensione",     lambda d: _ha(d, "tasso_sostituzione_lordo", "montante_fp") and isinstance(d["tasso_sostituzione_lordo"], dict)),
    ("netto_pensione",  lambda d: _ha(d, "scenari", "netto_pensione_inps")),
    ("capitale_umano",  lambda d: _ha(d, "bilancio", "proiezione", "esposizione_totale")),
    ("broker",          lambda d: _ha(d, "posizioni", "zainetto", "analisi") and _ha(d["analisi"], "per_broker")),
    ("ribilanciamento", lambda d: _ha(d, "drift", "risultante", "ordini")),
]
# JSON di altri script del plugin che il cruscotto riconosce e salta (la catena si passa intera)
IGNORATI = [
    ("importa-previdenza", lambda d: _ha(d, "montante_attuale", "ral_attuale", "fp_versamento_annuo")),
    ("ponte-pensione",     lambda d: _ha(d, "anni_ponte", "capitale_ponte")),
    ("riscatto-laurea",    lambda d: _ha(d, "onere_riscatto", "anni_riscatto")),
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


def _pensione(inps, mc, netto):
    if not (inps or mc or netto):
        return None
    sezione = {"inps": None, "tasso_lordo": None, "target": None, "prob_target": None, "montante_fp": None, "netto": None}
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
    - obiettivi: modello, n_sim, obiettivi [{nome, profilo, priorita, anni, target_oggi, target_nominale, gia,
      probabilita_successo, capitale_finale {p10, mediana, p90}, versamento_deterministico,
      versamento_confidenza, confidenza}], totale_versamento_deterministico, totale_versamento_confidenza;
    - glide_path: anni, portafoglio, obiettivi [{nome, quota_azionaria, capitale_proiettato}];
    - pensione: inps {pensione_inps_lorda_annua, eta_pensionamento, anni_al_pensionamento, montante_finale,
      ral_finale} | None, tasso_lordo e montante_fp {p10, mediana, p90} | None, target, prob_target,
      netto {netto_ultimo_stipendio, netto_pensione_inps, scenari [{nome, pensione_netta_totale,
      tasso_sostituzione_netto, tasso_sostituzione_lordo}]} | None;
    - capitale_umano: voci [{nome, valore}], esposizione_finanziaria, esposizione_totale, proiezione
      [{eta, F (patrimonio finanziario), HC (capitale umano), esposizione, p10, p90}], eta_sorpasso, stato_sorpasso, settore {settore, quota_settore_fin,
      peso_mondo, sovrappeso} | None;
    - fiscalita: totali, per_broker, zainetto [{broker, anno, scade_il, stato, importo_26_equivalente}], avvisi
      (solo quelli di zainetto e broker), avvisi_omessi (quanti nominavano una posizione);
    - ribilanciamento: totale, totale_post, imposta, prelievo, drift {classe: {peso, target, drift, tight, wide,
      fuori_banda, esito, motivo}}, risultante, zainetto, ordini [{broker, operazione, classe,
      categoria_fiscale, importo_eur, imposta_eur, nota}], dati_esempio (il piano gira sull'esempio dello script).
    Una sezione senza fonte è None. ErroreDati per un campo mancante, con il file e la chiave."""
    s = sorgenti.get
    bundle = {
        "versione": 1,
        "generato_il": data,
        "plugin": versione_plugin,
        "fonti": [{"file": sorgenti[t][0], "tipo": t} for t in ORDINE if t in sorgenti],
        "allocazione": _allocazione(s("allocatore"), s("ribilanciamento")),
        "obiettivi": _obiettivi(s("mc_obiettivi")),
        "glide_path": _glide_path(s("glide_path")),
        "pensione": _pensione(s("inps"), s("mc_pensione"), s("netto_pensione")),
        "capitale_umano": _capitale_umano(s("capitale_umano")),
        "fiscalita": _fiscalita(s("broker")),
        "ribilanciamento": _ribilanciamento(s("ribilanciamento")),
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
                             "(i --json di allocatore, glide path, Monte Carlo degli obiettivi, proiezione INPS, "
                             "Monte Carlo e netto della pensione, capitale umano, importatore dei broker, ribilanciamento)")
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
    ap.add_argument("-o", "--output", default="cruscotto.html", metavar="FILE",
                    help="la pagina da scrivere (default: cruscotto.html nella cartella corrente)")
    ap.add_argument("--json", metavar="FILE", help="scrive anche il bundle, cioè i dati che finiscono nella pagina")
    ap.add_argument("--data", metavar="AAAA-MM-GG", help="data in testata (default: oggi)")
    args = ap.parse_args(argv)
    if not args.sorgenti:
        ap.error("serve almeno un --from FILE")
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
        bundle = componi_bundle(sorgenti, data, versione_plugin())
        with open(TEMPLATE, encoding="utf-8") as f:
            html = incorpora(f.read(), bundle)
        for percorso, testo in ((args.output, html),
                                (args.json, json.dumps(bundle, ensure_ascii=False, indent=2) if args.json else None)):
            if percorso:
                try:
                    with open(percorso, "w", encoding="utf-8") as f:
                        f.write(testo)
                except OSError as e:
                    raise ErroreDati(f"impossibile scrivere {percorso}: {e}")
    except ErroreDati as e:
        print(f"ERRORE: {e}", file=sys.stderr)
        raise SystemExit(1)

    print(f"Cruscotto: {args.output}")
    for fonte in bundle["fonti"]:
        print(f"  {fonte['file']} → {fonte['tipo']}")
    for nome, script in ignorati:
        print(f"  ℹ {nome} ({script}) ignorato: il cruscotto non lo usa")
    sezioni = [k for k in ("allocazione", "obiettivi", "glide_path", "pensione", "capitale_umano", "fiscalita",
                           "ribilanciamento") if bundle[k]]
    print(f"Sezioni: {', '.join(sezioni)}")
    for ind in bundle["indicatori"]:
        nota = f" ({ind['nota']})" if ind["nota"] else ""
        print(f"  {ind['etichetta']}: {_valore(ind)}{nota}")
    if args.json:
        print(f"Bundle: {args.json}")
    print("Il file resta nella cartella di lavoro. Pubblicarlo come Artifact lo mette su claude.ai: "
          "farlo solo su richiesta esplicita.")
    print("Strumento educativo: non costituisce consulenza finanziaria o fiscale.")


if __name__ == "__main__":
    main()
