---
name: ribilancia
description: "Ribilanciamento tax-aware del portafoglio (regime amministrato): drift sulle bande 5/25 e piano che usa prima le leve a costo fiscale zero, con il CSV degli ordini per broker."
argument-hint: "[posizioni, allocazione target]"
disable-model-invocation: true
---

Esegui la skill `it-rebalance` (nel plugin: `wealth-management-it:it-rebalance`) e seguine il workflow su: $ARGUMENTS

Senza argomenti, parti dalla raccolta dei dati descritta nella skill. Se mancano dati essenziali, chiedili prima di procedere e non inventare numeri.

Disclaimer obbligatorio in fondo alla risposta: non è consulenza di investimento; i CSV degli ordini sono una checklist da verificare sul portale del broker prima di eseguire.
