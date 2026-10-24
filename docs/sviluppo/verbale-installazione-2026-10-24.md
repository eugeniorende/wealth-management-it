# Verbale: prove di installazione

Data: 24/10/2026. Claude Code 2.1.310 su Linux, nella sessione cloud di sviluppo. Voce di `ROADMAP.md` «Prova di installazione da zero, da un account senza accesso al repository, e in Cowork con lo zip della release» e § 2.6 di `docs/sviluppo/HANDOFF.md`.

## Prova locale del 21/10/2026

Fatta su un profilo Claude Code vuoto, con il marketplace locale e `/plugin install`, poi gli script lanciati dalla copia installata. Non ne era rimasto un verbale: l'esito è la procedura del README («Installazione», vie A, B e C). Le prove di oggi la ripetono e la estendono.

## Prove del 24/10/2026

Ogni prova usa un profilo vuoto, ottenuto puntando `CLAUDE_CONFIG_DIR` su una cartella nuova: niente plugin, marketplace o impostazioni preesistenti.

### Via B: marketplace locale, branch `feature/prepubblicazione-verifiche`

```bash
claude plugin marketplace add /percorso/del/checkout     # √ Successfully added marketplace: wm-it
claude plugin install wealth-management-it@wm-it         # √ Successfully installed (scope: user)
claude plugin list                                       # Version 0.10.0, Read from: /percorso/del/checkout, enabled
claude plugin details wealth-management-it@wm-it
```

- Il plugin si legge **dalla cartella**, senza copia in cache (`Read from:`). Il README diceva che anche questa via copiava il plugin nella cache: corretto.
- Dopo l'installazione Claude Code avvisa: «1 userConfig option not yet set». L'opzione `cartella_lavoro` si imposta con `/plugin configure` in sessione, oppure da shell con `claude plugin configure <plugin> --values-stdin` e un oggetto JSON; finisce in `pluginConfigs` di `settings.json`. `claude plugin install … --config cartella_lavoro=…` la imposta già all'installazione: provato in un terzo profilo vuoto, dopo l'installazione `claude plugin configure` la dà come «set». Il README ora lo dice.
- Componenti: 6 skill e 6 comandi. Stima del costo di contesto sempre caricato, da `claude plugin details`:

| Versione | Sempre caricato | Skill all'invocazione |
|---|---|---|
| 0.10.0 (da GitHub, sotto) | circa 4.350 token | 7.100-21.800 token |
| questo branch | circa 3.050 token | 7.900-19.600 token |

  Il calo viene dalle description più corte, dai comandi alias e dalle «Note per l'iterazione» spostate in `CHANGELOG.md` (T14). La stima resta di Claude Code, non una misura.

### Via A: marketplace da GitHub

```bash
claude plugin marketplace add eugeniorende/wealth-management-it   # clone, √ Successfully added marketplace: wm-it
claude plugin install wealth-management-it@wm-it --config cartella_lavoro=/percorso/piano
```

- Installa il branch di default, `main`, cioè la 0.10.0: senza `userConfig`, quindi Claude Code dice «--config not applied: … declares no userConfig options». Con la 0.11.0 su `main` l'opzione esisterà.
- La copia va in `<config>/plugins/cache/wm-it/wealth-management-it/0.10.0/` e contiene tutto il repository (anche `docs/`, `tests/`, `scripts/`), perché il marketplace punta alla radice (`"source": "./"`).
- Da una cartella di lavoro esterna, `proiezione-inps.py` e `ribilanciamento-multibroker.py` lanciati dalla copia in cache girano con rc 0 e scrivono gli output (cartella `ordini/`) nella cartella di lavoro, non nel plugin.
- Il clone è riuscito con le credenziali git della sessione, che ha accesso al repository privato: **non** è la prova «da un account senza accesso», che resta al proprietario (sotto).

### Zip per Cowork

```bash
python scripts/pacchetto.py --out <cartella>       # wealth-management-it-v0.10.0.zip: 79 file, 551 KB
```

- In cima allo zip: `.claude-plugin`, `CHANGELOG.md`, `LICENSE`, `NOTICE`, `README.md`, `commands`, `skills`. Fuori: test, workflow, `scripts/`, `docs/`.
- Estratto in una cartella, `claude plugin validate <cartella>/wealth-management-it --strict` passa.

## Cosa resta al proprietario

Le due prove richiedono un'identità o un'interfaccia che la sessione di sviluppo non ha.

**1. Installazione da un account senza accesso al repository** (dopo che il repository è pubblico, decisione 2):

1. su una macchina o un profilo senza credenziali GitHub del proprietario, con Claude Code aggiornato: `claude plugin marketplace add eugeniorende/wealth-management-it`;
2. `claude plugin install wealth-management-it@wm-it --config cartella_lavoro=~/piano-finanziario`;
3. `claude plugin list`: versione uguale all'ultima release, stato enabled;
4. in una sessione, `/minusvalenze` e una domanda sulla pensione: il comando carica la skill, la domanda attiva `it-pianificazione`;
5. dalla cartella di lavoro, uno script con il percorso della copia in cache: rc 0 e output nella cartella di lavoro.

**2. Upload in Cowork** con lo zip allegato alla release `v0.11.0`:

1. Settings → Plugins → Add plugin → Upload a zip;
2. controllare che compaiano le sei skill e i sei comandi;
3. in una conversazione, una domanda per skill: si attiva quella giusta;
4. verificare cosa diventano `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PLUGIN_ROOT}` e `${user_config.cartella_lavoro}` nelle istruzioni (Cowork non ha `/plugin configure`: le skill devono chiedere la cartella quando il segnaposto non è sostituito);
5. lanciare uno script: Cowork deve avere Python con `numpy`, `openpyxl` e `python-docx`; il ricalcolo degli Excel (`scripts/ricalcola-excel.py`) non è nello zip.

Annotare gli esiti in questo file, sotto una nuova data.
