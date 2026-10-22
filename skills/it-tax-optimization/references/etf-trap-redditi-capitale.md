# La trappola degli ETF UCITS armonizzati

## Il problema in una frase

In Italia, **la perdita** sulla vendita di un ETF UCITS armonizzato è "reddito diverso" (compensabile con plus future); **il guadagno** sulla vendita dello stesso tipo di ETF è "reddito di capitale" (NON compensabile con minus pregresse).

Questa asimmetria rende il classico "tax-loss harvesting" americano largamente inefficace su portafogli basati su ETF UCITS, che sono però il veicolo standard per il retail europeo.

## Riferimento normativo

- Art. 67 comma 1 lettera c-ter TUIR (dal 2027 art. 76 c. 1 lett. f TU D.Lgs. 117/2026): include tra i redditi diversi le plusvalenze "realizzate mediante cessione a titolo oneroso ovvero rimborso di titoli non rappresentativi di merci, di certificati di massa, di valute estere, oggetto di cessione a termine o rivenienti da depositi o conti correnti, di metalli preziosi, sempreché siano allo stato grezzo o monetato, e di quote di partecipazione ad organismi di investimento collettivo".
- Per gli OICR (Organismi di Investimento Collettivo del Risparmio), sia **armonizzati** (conformi alla direttiva UCITS) sia **non armonizzati**, il legislatore ha però disposto che il provento sia classificato come reddito di capitale ex art. 44 TUIR comma 1 lettera g (dal 2027 art. 46 c. 1 lett. h TU D.Lgs. 117/2026). Per i non armonizzati cambia anche il regime: vedi la tabella "nemici".
- La conseguenza pratica: i due flussi (in entrata da plus, in uscita per coprire minus) viaggiano su binari fiscali separati che non comunicano.

## Esempio numerico 1: la situazione ingenua

**Ipotesi**: hai €10.000 di minus 2022 nello zainetto, scadenza 31/12/2026. Vorresti "usarle".

**Tentativo**: vendi un ETF UCITS (es. iShares Core MSCI World UCITS, IE00B4L5Y983) con plusvalenza latente di €10.000, sperando che la plus venga azzerata dalla minus.

**Realtà**: il broker preleva il 26% di tassazione sulla plus di €10.000 = **€2.600**. La minus pregressa **non viene toccata** perché la categoria fiscale è diversa.

Risultato: hai pagato comunque €2.600 di tasse, e lo zainetto continua a scadere il 31/12/2026.

## Esempio numerico 2: la strategia corretta (Pattern A)

**Ipotesi**: stesse €10.000 di minus 2022 in scadenza.

**Strategia**: identifichi nel portafoglio un'azione singola (es. €10.000 di azioni Generali) con plusvalenza latente di €10.000.

**Esecuzione**: vendi le azioni Generali per €10.000 di plus realizzata, eventualmente riacquistandole immediatamente (no wash sale in Italia).

**Risultato fiscale**: la plus da azioni è reddito diverso, quindi compensa la minus pregressa. Tasse dovute sulla plus = €0. Lo zainetto residuo si riduce a €0.

Risparmio: €2.600 (effettivo).

Costi: solo commissioni di trading + eventuale Tobin tax 0,20% se Generali (sì, è > €500M cap, su mercato regolamentato; aliquota raddoppiata dal 2026) → ~€10 + €40 = €50.

Impatto netto: ~€2.550 di risparmio.

## Esempio numerico 3: creazione di zainetto da ETF UCITS (Pattern B con caveat)

**Ipotesi**: hai €10.000 in un ETF UCITS World con minusvalenza latente di €3.000 (l'ETF è in perdita).

**Domanda**: conviene vendere per creare zainetto?

**Analisi**:
- Vendita → realizzi una minus di €3.000 → entra nello zainetto come reddito diverso
- Riacquisto immediato dello stesso ETF (o di un sostituto UCITS) → nuovo PMC più basso → futura plus su questo ETF sarà reddito di capitale, **NON compensabile** con i €3.000 appena creati

**Quando ha senso**:
- Se prevedi di avere plus su azioni/certificates/ETC nei prossimi 4 anni → SÌ, lo zainetto verrà consumato da quelle
- Se il tuo portafoglio è puramente ETF UCITS → NO, lo zainetto creato evaporerà a vuoto

**Quando NON ha senso**:
- Portafoglio composto solo da ETF UCITS armonizzati, senza azioni singole, senza intenzione di entrarci → la minus creata non potrà mai essere consumata, e in 4 anni evaporerà

**Decisione**: l'esempio numerico in isolamento non basta. Serve guardare la composizione complessiva del portafoglio e la traiettoria pluriennale.

## Esempio numerico 4: switch tra ETF UCITS equivalenti (la "pseudo-TLH" che NON funziona)

**Tentazione**: vendere un ETF UCITS World in perdita (es. iShares IWDA) e ricomprare un equivalente diverso ISIN (es. Vanguard VWCE FTSE All-World, simile esposizione). L'idea è "ho realizzato la minus, mantengo l'esposizione".

**Risultato fiscale**: identico all'esempio 3. Minus realizzata = reddito diverso. Plus futura sul nuovo ETF = reddito di capitale. Non si parlano.

**Verdetto**: questa operazione **crea zainetto** ma **non riassorbe zainetto pregresso**. Se l'obiettivo era "scaricare" minus pregresse, fallisce. Se l'obiettivo è solo creare nuovo zainetto, funziona — ma vale il caveat dell'esempio 3 sulla "fungibilità" futura.

## Strumenti "amici" delle minus (reddito diverso)

| Strumento | Plus = reddito diverso? | Compensa minus pregresse? |
|---|---|---|
| Azione singola (italiana o estera) | Sì | Sì |
| Certificate (investment, leva, ecc.) | Sì | Sì |
| Obbligazione (solo la differenza di prezzo, al netto di cedole, ratei e scarto di emissione) | Sì | Sì |
| Warrant, covered warrant, opzioni quotate | Sì | Sì |
| ETC fisico (oro, argento, materie prime) | Sì (con eccezioni) | Generalmente sì |

## Strumenti "nemici" delle minus (reddito di capitale)

| Strumento | Plus = reddito di capitale | Compensa minus pregresse? |
|---|---|---|
| ETF UCITS armonizzato | Sì | NO |
| Fondo comune armonizzato | Sì | NO |
| ETF o fondo non armonizzato (non UCITS, es. domiciliato USA) | Sì: 26% solo se UE/SEE con gestore vigilato AIFMD, altrimenti IRPEF progressiva con acconto 26% e quadro RL | NO |
| Scarto di emissione (BOT, CTZ, zero coupon tenuti a scadenza) | Sì (12,5% sui titoli di Stato) | NO |
| Dividendo azionario | Sì | NO |
| Cedola obbligazionaria | Sì | NO |
| Distribuzione ETF (anche se UCITS) | Sì | NO |
| Interesse conto deposito | Sì | NO |

## Heuristic per la skill

Quando proponi un trade di "consumo zainetto", verifica che la posizione candidata sia nella tabella "amici". Se è "nemica", NON proporre come consumatrice di zainetto pregresso. Eventualmente proponi come *creatrice* di nuovo zainetto, ma con avviso esplicito sul rischio di evaporazione.

## Caso ibrido: l'ETF a distribuzione UCITS

Un ETF UCITS armonizzato a distribuzione genera DUE flussi fiscali distinti:
1. Distribuzioni periodiche → reddito di capitale (tassate al 26%, NON compensabili)
2. Plus/minus alla vendita → la plus è reddito di capitale (NON compensabile); la minus è reddito diverso (compensabile e generatrice di zainetto)

Questo è il caso più sottile e spesso trascurato: anche se cambi la formula da accumulazione a distribuzione, la trappola asimmetrica resta.

---
*Dati normativi (qualificazione fiscale di ETF/fondi come redditi di capitale) — Verificato: 2026-06.*
*OICR non armonizzati (art. 10-ter L. 77/1983, vigente fino al 31/12/2026, → art. 59 del testo unico versamenti e riscossione, D.Lgs. 33/2025; Circ. 21/E/2014) e scarto di emissione (artt. 44-45 e 68 c. 7 TUIR, dal 2027 artt. 46-47 e 77 c. 8 D.Lgs. 117/2026) — Verificato: 2026-10.*
*Corrispondenze nel TU 2027 (artt. 46, 47, 76 e 77 D.Lgs. 117/2026) — Verificato: 2026-10.*
