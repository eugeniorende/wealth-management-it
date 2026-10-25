---
name: cruscotto
description: "Cruscotto grafico del piano: una pagina HTML con allocazione, obiettivi, glide path, pensione, capitale umano, fiscalità e ribilanciamento, dai JSON degli script; pubblicabile come Artifact solo su conferma."
argument-hint: "[file JSON degli script, oppure niente per quelli della cartella di lavoro]"
disable-model-invocation: true
---

Esegui la skill `it-revisione` (nel plugin: `wealth-management-it:it-revisione`) dal passo 6, «Cruscotto grafico», su: $ARGUMENTS

Senza argomenti, usa i JSON della cartella di lavoro scritti dagli script con `--json`; se non ce ne sono, indica quali script lanciare. Non inventare numeri e non pubblicare l'Artifact senza un sì esplicito.

Disclaimer obbligatorio in fondo alla risposta: non è consulenza finanziaria, fiscale o di investimento; per le decisioni rinviare a un professionista abilitato.
