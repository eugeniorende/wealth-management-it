---
name: cruscotto
description: "Cruscotto grafico del piano: una pagina HTML con allocazione, obiettivi, glide path, pensione, capitale umano, fiscalità e ribilanciamento, dai JSON degli script; pubblicabile come Artifact solo su conferma."
argument-hint: "[file JSON degli script, oppure niente per quelli della cartella di lavoro]"
disable-model-invocation: true
---

Esegui la skill `it-revisione` (nel plugin: `wealth-management-it:it-revisione`) dal passo 6, «Cruscotto grafico», su: $ARGUMENTS

Senza argomenti, usa i JSON della cartella di lavoro scritti dagli script con `--json`, non i file di input dei `--dati`; se non ce ne sono, indica quali script lanciare. Se la cartella `revisioni/` ha già la foto di una revisione precedente, aggiungi `--precedente revisioni/` e la pagina avrà il confronto; fuori da una revisione non archiviare (`--archivia`), se l'utente non lo chiede. Se l'utente vuole mostrare la pagina ad altri, genera la versione anonimizzata con `--anonimo` e pubblica quella, dicendo nella richiesta di conferma che cosa resta visibile e il limite. Non inventare numeri e non pubblicare l'Artifact senza un sì esplicito.

Disclaimer obbligatorio in fondo alla risposta: non è consulenza finanziaria, fiscale o di investimento; per le decisioni rinviare a un professionista abilitato.
