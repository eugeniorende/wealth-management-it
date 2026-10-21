# Passaggio della sessione di sviluppo — 21/10/2026

Documento per riprendere lo sviluppo della 0.10.0 in un'altra sessione (Claude Code in cloud o su un'altra macchina). Tutto ciò che serve è nel repository: questo file, `ROADMAP.md`, `docs/audit-2026-10.md` e i dati in `docs/sviluppo/`.

## 1. Dove siamo

`develop` (0f8ba21) contiene l'ondata 0 completa e, in anticipo, T10, la prima parte di T11, licenza, supply chain e matrice Python della CI (PR #5, #7-#19). I temi della 0.10.0 sono implementati su branch pubblicati, non ancora mergiati:

| Tema | Branch | Base | Stato |
|---|---|---|---|
| T1 asimmetria e zainetto | `feature/t1-asimmetria-zainetto` | develop | **pronto**: correzioni della revisione applicate (1cf2a7a), suite 49/49. **PR #20** aperta: far ripassare la CI e mergiare |
| T2 importatore broker | `feature/t2-importatore-broker` | T1 (merge fe6b03b) | correzioni **da applicare**: `revisioni/review-t2.json` |
| T3 broker esteri e dichiarativo | `feature/t3-broker-esteri` | T2 (75e0795) | correzioni da applicare: `revisioni/review-t3.json`; prima incorporare T2 aggiornato |
| T13 dividendi esteri, successioni | `feature/t13-reference` | develop | correzioni + integrazione da fare: `revisioni/review-t13.json` e § 3 |
| T8 obiettivi | `feature/t8-obiettivi` | develop (merge 05fbf60) | **pronto**: correzioni applicate (9064ada), suite 55/55; note in `revisioni/esito-t8.json` |
| T5 pensione pubblica | `feature/t5-pensione-pubblica` | develop 0f8ba21 | correzioni da applicare: `revisioni/review-t5.json` |
| T4 fondo pensione | `feature/t4-fondo-pensione` | T5 | correzioni da applicare: `revisioni/review-t4.json` |
| T6 autonomi | `feature/t6-autonomi` | T4 | correzioni da applicare: `revisioni/review-t6.json` |

Restano da fare: **T7** (ribilanciamento), la **seconda parte di T11** (mappa dei testi unici 2027 e doppie citazioni, materiale pronto in `t11/`), i lavori trasversali di 0.11 e pre-pubblicazione, la release.

**I file `revisioni/review-*.json`** sono gli esiti delle revisioni avversariali (4 lenti, 2 verificatori per rilievo). Gruppi: `confermati` (due voti: applicare salvo prova contraria), `contesi` (un voto: valutare), `non_verificati` (verifica caduta per limiti tecnici: valutare con scetticismo, applicare solo se dimostrabili). Il campo `correzione` è una proposta, da verificare sul testo del branch.

## 2. Ordine di lavoro consigliato

1. **PR #20 (T1)**: push già fatto con le correzioni; CI verde → merge (merge commit) → elimina il branch.
2. **T2**: `git merge develop`, applica `review-t2.json` (tra i confermati: aliquota 12,5% solo ai titoli di Stato italiani mentre spetta anche a white list ed enti sovranazionali; ETC WisdomTree con ISIN JE classificati come OICR a IRPEF) → PR → CI → merge.
3. **T3**: `git merge feature/t2-importatore-broker` (o develop dopo il merge di T2), applica `review-t3.json` → PR → merge.
4. **T13**: `git merge develop`, applica `review-t13.json` e l'integrazione del § 3 → PR → merge.
5. **T8**: `git merge develop` → PR → merge.
6. **T5 → T4 → T6**: applica le tre revisioni in ordine (ogni branch incorpora il precedente) → tre PR in ordine → merge.
7. **Dopo T8 e T5-T6**: le note fuori perimetro del § 4 (deflazione della serie in `ponte-pensione.py`, diciture «serie storica reale», `--anonimo` in importa-previdenza, ecc.).
8. **T7 ribilanciamento** (dopo T1): F004, F019, F030 (restano `bande-dinamiche.md` e lo script: cruscotto e tracker sono già a 5/25), F044, F045 (regola di rientro mista), F046 (prelievo in decumulo), F047. Vedi `docs/audit-2026-10.md`, § T7.
9. **T11 seconda parte**: `t11/mappa-nuovo-tuir.md` → `skills/it-tax-optimization/references/mappa-nuovo-tuir.md` (con rimando dalla SKILL e voce in `OBBLIGATI_FRESHNESS`), poi `t11/doppie-citazioni.md`.
10. **Rilascio 0.10.0**: changelog v0.10.0 (voci per T1-T8, T13 e correzioni), ROADMAP spuntata, README («Errori noti», conteggio dei test, tabella `--tabella-freshness` rigenerata), poi `release/0.10.0` da develop → PR su main (merge commit) → tag `v0.10.0` → verifica di `release.yml` (suite completa con freshness, zip con LICENSE e NOTICE) → merge back su develop.
11. **0.11 e pre-pubblicazione** (ROADMAP): T9 helper CLI comune (`--help`, `--set`, `--json`, `--from`), Windows ed encoding (UTF-8 su stdout e `open()`, `windows-latest` in CI), formati italiani (migliaia col punto, CSV ordini con `;`), T12 test strutturali sugli xlsx e `--json` a valori chiusi, T14 (description ≤ 1.024 caratteri, CHANGELOG.md, campo `upstream` di plugin.json, commands come alias, recalc della sandbox in autonomi SKILL).

## 3. Integrazione di T13 (da fare sul branch T13)

- `skills/it-tax-optimization/SKILL.md`, elenco delle reference:
  - `references/dividendi-esteri.md` — dividendi esteri e doppia imposizione: ritenute alla fonte di sette Paesi con il prelievo totale, il 26% sul netto frontiera in amministrato, W-8BEN e rimborsi esteri, il credito per le imposte estere (negato dall'Agenzia, aperture della Cassazione), ETF ad accumulazione o a distribuzione e azioni dirette;
  - `references/successione-donazione.md` — costo per gli eredi pari al valore di successione e per i donatari pari al costo del donante, fondi ed ETF come caso a parte, zainetto che si estingue col decesso, aliquote e franchigie dopo il D.Lgs. 139/2024, il confronto «vendo in decumulo o lascio in eredità».
  - Riga dei «Casi limite (successioni…)»: aggiungere «principi in `references/successione-donazione.md`».
- `skills/it-rebalance/references/sequenza-liquidazione.md`, fine del punto 2: «Per i dividendi esteri il netto incassato sconta anche la ritenuta dello Stato estero, e il 26% italiano si applica sul netto frontiera. L'eventuale eccedenza rispetto alla convenzione si recupera solo con le pratiche estere (W-8BEN, rimborsi): vedi `it-tax-optimization/references/dividendi-esteri.md`.» Nuovo paragrafo «Finalità successoria»: «Per azioni e obbligazioni detenute direttamente gli eredi ricevono come costo il valore di successione: la plusvalenza latente si azzera. Se una parte del dossier è destinata agli eredi, le posizioni dirette con la plusvalenza latente più alta sono le ultime da vendere. Per fondi ed ETF il testo vigente tratta l'intestazione agli eredi come una cessione: da verificare.»
- Bucket «Eredità» di it-pianificazione-obiettivi (dopo il merge di T8): «La fiscalità dietro il profilo: per azioni e obbligazioni detenute direttamente gli eredi prendono come costo il valore di successione, e l'imposta di successione è nulla entro €1.000.000 per coniuge e figli. Per fondi ed ETF l'azzeramento della plusvalenza non è garantito. Vedi `it-tax-optimization/references/successione-donazione.md`.»
- `tests/run_tests.py`: le due reference in `OBBLIGATI_FRESHNESS` (più `multi-intermediario.md` e `import-dati-broker.md`, se marcati) e un test che vincoli i numeri (prelievo = r + 26%×(1−r); esempi 629/518/590; successione 78.000 e 249.600) e l'indice nella SKILL, validato per mutazione.
- Attenzione al contenuto: per fondi ed ETF l'intestazione agli eredi è trattata come cessione nel testo vigente (artt. 26-quinquies c. 6 DPR 600/73 e 10-ter c. 3 L. 77/83): l'azzeramento della plusvalenza vale con certezza solo per i titoli detenuti direttamente. La ritenuta francese per le persone fisiche è 12,8% (non 25% come nell'audit).

## 4. Note fuori perimetro raccolte dagli agenti

- **ponte-pensione.py** (dopo T8): deflazionare la serie storica come il decumulo (`carica_inflazione` e `deflaziona` del motore, parametri `INFLAZIONE=None` e `INFLAZIONE_RIPIEGO=0.02`); sui default la probabilità di coprire il ponte scende da circa 44% a circa 21%. Dirlo nel changelog (output con seed cambiati). Test a valore chiuso.
- **montecarlo-pensione.py:20-22, it-pianificazione/SKILL.md (serie storica), references/montecarlo-pensione.md**: «serie storica reale» → «serie storica USA nominale in dollari (Damodaran), ne usa solo la forma: media ricentrata».
- **Due copie di `motore_bootstrap.py`**: quella di T8 è la versione di riferimento; se un altro tema tocca la copia in it-pianificazione, riallinearla.
- **sequenza-liquidazione.md (it-rebalance)**: allineare alle nuove forme di erogazione del fondo (rendita a durata definita, prelievi, frazionata) e alla ritenuta 15→9% sulla sola parte imponibile.
- **it-pianificazione-obiettivi/SKILL.md e asset-location-optimizer.py**: «€5.300 al 33%» presuppone l'assenza del contributo del datore: nota sul plafond condiviso.
- **it-revisione (T10)**: aggiungere lo spazio deducibile residuo (plafond − datore − dovuto) e la perdita del 9-15% se i non dedotti non sono comunicati.
- **importa-previdenza.py**: flag `--anonimo` (oggi stampa intestatario e data di nascita).
- **commands/ribilancia.md**: «PMC (o lotti)» → i lotti servono solo a ricostruire il PMC (come it-rebalance/SKILL.md).
- **criptovalute-casi-speciali.md**: «art. 6 c. 6 D.Lgs. 461/1997» senza successore (dal 2027 art. 306 c. 7 D.Lgs. 117/2026).
- **README**: conteggio dei test superato; «Errori noti» elenca come aperti F001, F007, F011, F012 (chiusi dai temi); tabella freshness da rigenerare; voci di changelog per i temi.
- **Circ. AdE 30/E/2023**: il PDF sul sito AdE dà 404; copia integrale su dirittobancario.it.

## 5. Regole di lavoro (invariate)

- **Gitflow**: `feature/*` → PR su `develop`, merge commit (`gh pr merge N --merge`), poi eliminazione del branch; `release/X.Y.Z` → `main` con tag e merge back. Messaggi di commit in italiano, ultima riga `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; descrizione delle PR che chiude con `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
- **Decisioni del proprietario**: § «Decisioni» di `ROADMAP.md` (0.10.0 con P0 e T11; repository privato fino alla pre-pubblicazione; dichiarativo solo come principi; uscite operative con gate stretti e disclaimer; F012 come correzione).
- **TDD**: prima il test che fallisce per la ragione giusta, poi il fix; test che vincolano i numeri; validazione per mutazione dove possibile.
- **Fonti primarie** (Normattiva, Gazzetta Ufficiale, AdE, INPS, COVIP, MEF) per ogni dato normativo; marcatori `Verificato: AAAA-MM` circoscritti a ciò che è confermato; doppia citazione per le norme che cambiano dal 2027.
- **Propagazione**: ogni correzione in tutte le copie (`git grep` su skills/, commands/, README, plugin.json).
- **Excel**: mai salvare con openpyxl i file con convalide o strutture delicate; modificare l'XML nello zip e poi `python scripts/ricalcola-excel.py FILE --in-place` (ricalcolo in locale it-IT). Confrontare la struttura prima e dopo.
- **Revisione avversariale prima di ogni merge di tema**: `docs/sviluppo/workflows/review-tema-roadmap.js` (Workflow tool, args `{repo, scratch, python, branch, base, tema, finding}`); il modello di workflow per applicare le correzioni è `correzioni-temi-roadmap.js`.

## 6. Ambiente

```bash
pip install -r tests/requirements.txt          # numpy, openpyxl, python-docx
sudo apt-get install -y libreoffice-calc        # per i test che ricalcolano gli Excel (altrimenti risultano saltati)
python tests/run_tests.py                       # tutta la suite
python tests/run_tests.py --only freshness      # solo freshness
python tests/run_tests.py --tabella-freshness   # tabella per il README
```

In CI: `RICHIEDI_LIBREOFFICE=1` rende obbligatori i test Excel; matrice Python 3.11 e 3.14.
