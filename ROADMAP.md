# Roadmap

Stato al 20/10/2026, sulla v0.9.6. La base è l'[audit di ottobre 2026](docs/audit-2026-10.md): 65 problemi confermati (11 di gravità alta, 40 media, 14 bassa), raccolti in 14 temi. Ogni voce cita gli ID dei finding. Il dettaglio (file e righe, evidenza, correzioni dei verificatori, fonti) è nel report.

## Decisioni

Prese il 20/10/2026.

1. **0.10.0 correttiva entro il 31/12/2026**, con il fix della CI, i quick win, tutti i temi P0 (T1–T8) e T11.
2. **Repository privato ora, pubblico più avanti.** Licenza, privacy, Windows e packaging si chiudono nella milestone «Pre-pubblicazione», prima di cambiare la visibilità.
3. **Regime dichiarativo: solo principi.** Il motore resta sull'amministrato e la reference del dichiarativo diventa corretta e completa (T3). Non si costruisce un importatore per IBKR o Degiro.
4. **Uscite operative con gate stretti e disclaimer.** La OPZIONE sulla leva di rischio, il «versa fino a €5.300» e il CSV degli ordini restano, ma solo quando le condizioni sono rispettate. Il disclaimer va anche nei commands e nel CSV.
5. **Proposte dell'audit adottate:**
   - regola di rientro mista nel ribilanciamento: a target se costa zero, al bordo banda più un margine se tassato; modulazione per volatilità spenta di default;
   - copie dei dati normativi in ogni skill, con un test di coerenza tra skill;
   - convenzione dei rendimenti «netti» definita in modo esplicito, con conversione solo nell'asset location;
   - parte educativa sulle successioni ammessa;
   - Python minimo 3.11.
6. **F012 è una correzione, non una scelta di design.** In amministrato la base di costo è il costo medio ponderato (art. 6 c. 4 D.Lgs. 461/97). Il LIFO (art. 67 c. 1-bis TUIR) serve a individuare i titoli ceduti in dichiarativo.

## Regole per ogni intervento

- **Propagare.** Ogni correzione si applica a tutte le copie dello stesso dato o della stessa regola in `skills/`, `commands/` e README. Il critico dell'audit ha trovato copie che i finding non coprono, per esempio `coordinamento-zainetto.md:91` e `previdenza-gestione-separata.md:70-71`.
- **Fonti primarie.** Prima di aggiornare il marcatore `Verificato: AAAA-MM` si controllano Normattiva, la Gazzetta Ufficiale, le circolari di INPS e Agenzia delle Entrate e COVIP. Le fonti secondarie servono a trovare un problema, non a chiuderlo.
- **Test che vincolano i numeri.** Si lavora in TDD, con valori chiusi o invarianti. Uno smoke test che controlla solo `rc == 0` non chiude un finding.
- **Citazioni dal 2027.** Doppio riferimento, vecchio e nuovo testo unico, con la mappa di F035 (T11).
- **Gitflow.** `feature/*` verso `develop`; `release/0.10.0` verso `main`, con il tag.

## 0.10.0 — correttiva, entro il 31/12/2026

### Ondata 0 — fine ottobre (chiusa il 20/10/2026, PR #5 e #7-#13)

- [x] Fix pipefail del workflow di freshness, che non apriva mai la issue mensile (PR #5).
- [x] Ricalcolo headless degli Excel con LibreOffice in CI, anticipato da T12. Serve ai test a valori di T4, T5 e T6. Il ricalcolo in locale italiano ha trovato due bug fuori dall'audit, già corretti: le ipotesi di `Scenari` salvate come testo e `TEXT(x;"0.0%")` dipendente dal locale.
- [x] Disclaimer in `commands/pensione.md`, in `commands/pensione-autonomi.md` e nel CSV degli ordini del ribilanciamento (decisione 4). Esteso a tutti i commands, con un test di igiene, e allo stdout del ribilanciamento (PR #9).
- Quick win, sotto le 2 ore ciascuno:
  - [x] **F006.** Quadro RW sempre dovuto per titoli, ETF e cripto presso intermediari esteri. La soglia di €15.000 vale solo per conti e depositi.
  - [x] **F007 (testo) e F051.** Il contributo del datore conta nel plafond di €5.300, il TFR no. Vanno tolti l'appunto di bozza e i dati personali dell'autore dalle reference.
  - [x] **F008.** Detrazione pensionati in `Pubblica!B64` con la formula dell'art. 13 c. 3 TUIR già usata da `netto-pensione.py`.
  - [x] **F002.** Massimale 2026 a €122.295 e prima fascia a €56.224, coerenti tra le skill.
  - [x] **F003, F052 e F042 (testo):**
    - ETF non armonizzati tra gli strumenti non compensabili;
    - scarto di emissione come reddito di capitale;
    - polizze vita esenti IRPEF solo per la componente demografica.
  - [x] **F009 e F010 (testo):**
    - requisiti 2026: via Quota 103, Opzione donna e «Quota 104»;
    - soglia di vecchiaia a 1× l'assegno sociale;
    - portabilità e adesione automatica secondo la L. 199/2025.
  - [x] **F016 (testo) e F038.** Artigiani e commercianti dichiarati fuori perimetro; righe CIPAG ed ENPAM corrette.
  - [x] **F020.** Comunicazione al fondo dei contributi non dedotti in tutte le superfici «Scadenza».
  - [x] **F036 (a)-(d).** Reference cripto: pena, ravvedimento, amministrato dal 2023, Trade Republic.
  - [x] **F017.** Gate della OPZIONE legato a `FINESTRA_DERISK` e alla priorità «discrezionale», con test.
  - [x] **F005 e F056 (parte).** `rendimenti-storici.csv` ancorato a `__file__`; `RENDIMENTO_FP_REALE=0` gestito in ponte-pensione.
  - [x] **F029.** Off-by-one del bootstrap in decumulo-obiettivi.
  - [x] **F060 (b) e F049 (b).** Quota azionaria su tutte le classi in genera-ips, con il mese in italiano; celle TWR vuote invece di −100%.
  - [x] **F025 e riga comune:**
    - «Cosa il plugin NON fa» riscritto;
    - `/revisione` tra i comandi;
    - un solo conteggio dei test;
    - via «default ±5%» da `commands/ribilancia.md`.
  - [x] **F024 (test).** Elenco esplicito dei file obbligati al marcatore in `t_freshness` (`OBBLIGATI_FRESHNESS`, 19 file). I quattro file che ne erano privi sono stati verificati alle fonti e corretti prima di marcarli: in `criptovalute-casi-speciali.md` c'erano errori di sostanza (importi del regime neo-residenti, IVA del mining, localizzazione delle cripto, decorrenza della riforma delle successioni).

**Emerso nell'ondata 0, oltre l'audit:**
- Le fonti primarie hanno smentito l'audit su due punti. Il capitale del fondo pensione resta al 50%: l'aumento al 60% della L. 199/2025 è stato soppresso dal DL 62/2026 prima di entrare in vigore. La CIPAG applica il 5% anche verso la PA. «Quota 104» non risulta da nessuna fonte.
- Il ricalcolo in locale italiano ha trovato due bug negli Excel, corretti nella PR #7.
- I marcatori nuovi sono circoscritti alle parti verificate: dove un file è stato riverificato solo in parte, la data del file intero resta quella di prima.
- Restano da verificare su fonte primaria, e sono esclusi dai marcatori: le righe Inarcassa, Forense, CNPADC ed ENPAP; la leva ETN/ETC su cripto; le minus pregresse di Scalable; gli articoli dei testi unici 2027 che sostituiscono l'art. 13 TUIR e i commi 76-84 della L. 190/2014. Finiscono in T3, T6 e T11.

### Ondata 1 — fiscale, novembre

- [ ] **T1 Asimmetria fiscale e zainetto** (P0, L): F003, F011, F012, F042, F052.
  - ETF non armonizzati classificati correttamente.
  - Certificazione delle minus alla chiusura del rapporto (art. 6 c. 5 D.Lgs. 461/97).
  - Costo medio in amministrato.
  - Scarto di emissione e polizze.
  - Test di igiene sulle formulazioni vietate.
- [ ] **T2 Importatore estratti broker** (P0, M): F001, F034. Viene dopo T1.
  - «Da classificare» al posto del default «diverso».
  - Scadenza a 4 anni.
  - Conversione 12,5/26 nei due versi.
  - `--json` su file e migliaia in formato italiano.
  - Test numerico sull'esempio: plus compensabili 0, zainetto 800.
- [ ] **T3 Broker esteri, dichiarativo e cripto** (P0, M): F006, F036, F053.
  - Quadro RW.
  - Stato per broker, con data di verifica: Trade Republic, Scalable, IBKR, Degiro.
  - Cambio del giorno.
  - Solo principi (decisione 3).

### Ondata 2 — previdenza, novembre-dicembre

- [ ] **T4 Fondo pensione** (P0, L): F007, F010, F014, F020, F037.
  - Quota deducibile nell'Excel.
  - Uscita del forfettario senza tassare contributi non dedotti e rendimenti.
  - Novità della L. 199/2025.
  - Confronto TFR in azienda o nel fondo.
- [ ] **T5 Pensione pubblica dipendenti** (P0, L): F002, F008, F009, F013, F062.
  - Foglio Scenari tutto in euro di oggi.
  - Requisiti 2026.
  - Tassi di capitalizzazione.
  - Test contro `netto-pensione.py` e `proiezione-inps.py`.

### Ondata 3 — strumenti, dicembre

- [ ] **T7 Ribilanciamento tax-aware** (P0, L): F004, F019, F030, F044, F045, F046, F047. Viene dopo T1.
  - Versamenti in entrata.
  - Vendita parziale a costo zero.
  - Aliquota per posizione.
  - Regola di rientro unica e bande coerenti tra script, Excel e skill.
  - Prelievo in decumulo.
- [ ] **T6 Autonomi e forfettari** (P0, L): F015, F016, F038, F039. Riusa la logica di T4.
  - Massimale e minimale.
  - Foglio completo: altri redditi, netto, scenari.
  - Primo test della skill.
- [ ] **T8 Pianificazione obiettivi** (P0, L): F017, F018, F022, F029, F040, F041, F043.
  - Glide path nel calcolo del versamento.
  - Convenzione dei rendimenti netti.
  - Test che catturano i mutanti.
  - Dal critico: la serie storica è nominale in USD ma è descritta come reale.

### Trasversale, entro il 31/12

- [ ] **T11 Governance normativa** (P1, M): F024, F035.
  - [x] Elenco dei file obbligati al marcatore (PR #13).
  - [ ] `references/mappa-nuovo-tuir.md`, per il D.Lgs. 117/2026 in vigore dal 1/1/2027.
  - [x] Tabella dello stato dei dati nel README, generata da `run_tests.py --tabella-freshness` (PR #14).
  - [x] Calendario dei parametri annuali: coefficienti di trasformazione 2027-28, legge di bilancio 2027, massimale e requisiti 2027 (PR #14).

### Linea di taglio e rilascio

- A inizio dicembre si valuta l'avanzamento. Se si è in ritardo, T8 e il foglio completo di T6 (F039) passano a una 0.10.1. T11 non slitta, perché il nuovo TUIR entra in vigore il 1/1/2027.
- `release/0.10.0` parte da develop verso metà dicembre. La suite completa, freshness compresa, deve essere verde prima del tag.

## 0.11 — script e test

- [ ] **T12 Test e CI che vincolano i numeri** (P1, L): F032, F065.
  - Test strutturali su ogni xlsx.
  - `--json` con valori chiusi.
  - Fixture realistiche.
  - [x] Matrice Python 3.11 e 3.14, con versioni minime delle dipendenze (PR #17).
  - [x] Versione fissata di claude-code nel job validate (PR #15).
- [ ] **T9 Interfaccia degli script e flusso dati** (P1, XL): F005, F026, F027, F028, F031, F033, F056, F059.
  - Helper `cli()` comune: `--help`, `--set`, `--json`, `--from`.
  - Lettore unico del pianificatore.
  - `--dati` per genera-ips e per il ribilanciamento.
  - Catena `--json` → `--from` tra gli script.
- [x] **T10 Revisione annuale** (P1, M): F049, F050, F060, F064 (PR #12, #18). Anticipato: non dipendeva davvero da T4 e T7.
  - [x] TWR con 120 righe e ultima riga dinamica, Leggimi con i limiti.
  - [x] Costi dell'anno (trasparenza, non da sottrarre di nuovo).
  - [x] Semaforo per priorità (85/75/60%).
  - [x] In più, da F030: soglia 5/25 per classe nel cruscotto e nella riga aggregata del tracker.
  - [ ] Contratto di input della revisione (F031): resta a T9.

## Pre-pubblicazione — prima di rendere pubblico il repository

- [x] **Licenza** (PR #16):
  - LICENSE e NOTICE (Apache-2.0) nel repository e nello zip, cioè in `INCLUDI` di `scripts/pacchetto.py`;
  - SHA dell'upstream fissato: l'ultimo commit prima della rimozione è `ef165e4160`; il confronto non trova righe di testo in comune con l'upstream;
  - sezione Licenza riscritta e link all'upstream fissato al commit. Il campo `upstream` di `plugin.json` resta a T14.
- [ ] **Privacy dei dati utente:**
  - inventario dei campi che ogni script stampa;
  - flag `--anonimo`, perché importa-previdenza stampa nome e data di nascita;
  - sezione «Dove vanno i tuoi dati» nel README.
- [ ] **Windows ed encoding.** UTF-8 forzato su stdout e in tutte le `open()`, più `windows-latest` nella CI: oggi 6 script su 7 vanno in crash con cp1252.
- [ ] **Formati italiani:**
  - punto per le migliaia in tutti gli script;
  - CSV degli ordini apribile in Excel italiano, con `;` come separatore e la virgola decimale.
- [ ] **T14 Authoring, documentazione e packaging** (P2, M): F023, F025, F051, F057, F058, F061, F066.
  - description entro i 1.024 caratteri;
  - CHANGELOG.md;
  - commands come alias delle skill;
  - plugin.json senza warning.
- [ ] Prova di installazione da zero, da un account senza accesso al repository, e in Cowork con lo zip della release.
- [x] Supply chain della CI: action fissate per SHA con test di igiene, claude-code a versione fissa (PR #15). Dependabot su pip non serve: le dipendenze hanno solo versioni minime.
- [ ] Rilettura degli output operativi rispetto alla postura «educativa» (decisione 4).
- [ ] README coerente con un repository pubblico: marketplace e Releases.

## Dopo — da decidere

- [ ] **T13 Estensioni** (P1, L): F021, F054, F055, F063.
  - Reference sui dividendi esteri e su successione e donazione.
  - Sezione sul riscatto della laurea.
  - Casi frequenti del freelance.

  La proposta dell'audit, non ancora decisa, è: sì alle due reference; riscatto solo come sezione e con `--set`. Il confronto TFR contro fondo (F037) e il prelievo in decumulo (F046) sono già in T4 e T7.

## Fuori dal codice

- [ ] Branch protection su `main` e `develop` con i check `test` e `validate`, da impostare su GitHub.
