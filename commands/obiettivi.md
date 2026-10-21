---
name: obiettivi
description: Pianificazione finanziaria goals-based multi-obiettivo. Definisce gli obiettivi (fondo emergenza, casa, figli, pensione, obiettivi liberi) con orizzonte e priorità, propone per ciascuno un profilo di allocazione appropriato all'orizzonte (esempi illustrativi, non raccomandazioni) e calcola il piano di accumulo necessario.
---

Esegui la pianificazione finanziaria per obiettivi seguendo la skill `it-pianificazione-obiettivi`.

Postura: EDUCATIVA e METODOLOGICA. Mostra profili di allocazione come esempi illustrativi, NON raccomanda titoli specifici, NON sceglie l'allocazione "giusta" al posto dell'utente. Non è consulenza di investimento.

Workflow:

1. **Situazione attuale**: capacità di risparmio mensile (entrate − spese), liquidità, investimenti esistenti, debiti (con tasso), ed esistenza di un fondo di emergenza adeguato (3-6 mesi di spese liquide). Se manca, è l'obiettivo 0 con priorità assoluta.

2. **Elicitazione obiettivi**: per ciascuno → nome, importo target (€ di oggi), orizzonte (anni), priorità (essenziale/importante/desiderabile), importo già accantonato. Se l'obiettivo "pensione" compare, instradarlo a `it-pianificazione` o `it-pianificazione-autonomi` (veicolo dedicato, non secchiello generico).

3. **Profilo di allocazione per obiettivo**: in base all'orizzonte, proporre il profilo-tipo (preservazione <2a / conservativo 2-4a / moderato 4-7a / crescita 7-12a / crescita massima >12a) come punto di partenza illustrativo. Spiegare la logica orizzonte→rischio. Far calibrare all'utente.

4. **Piano di accumulo**: per ogni obiettivo, target proiettato a nominale (inflazione), rendimento atteso del profilo (nominale, netto di costi e imposte), versamento mensile necessario. Per gli obiettivi terminanti il versamento sconta il de-risking degli ultimi anni (glide path), come il pianificatore Excel.

5. **Riconciliazione multi-obiettivo**: somma versamenti vs capacità. Se non basta, mostrare il gap e le leve (fondo emergenza prima, debiti cari prima degli investimenti discrezionali, allungare orizzonte, ridurre target, posticipare per priorità, sfruttare la sequenza temporale). La scelta è dell'utente.

6. **Collegamento alle altre skill**: le allocazioni-target → input per `it-rebalance`; strumenti → fiscalità in `it-tax-optimization`; pensione → skill previdenziale.

Se mancano dati essenziali (capacità di risparmio, obiettivi), chiedere prima di procedere. Disclaimer obbligatorio: non è consulenza di investimento; per scelte concrete rinviare a consulente abilitato.
