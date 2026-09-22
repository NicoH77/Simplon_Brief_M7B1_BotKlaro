# Politique de remboursement Klaro (usage interne et agent)

Cette politique est la référence que l'outil `verifier_eligibilite_remboursement` applique, et que le conseiller consulte pour valider une décision de l'agent.

## Règles d'éligibilité

1. **Délai standard.** Un article peut être retourné et remboursé dans un délai de **14 jours** après la date de livraison réelle. Au-delà, aucun remboursement standard n'est accordé.
2. **Commande non livrée.** Une commande dont le statut est `en_preparation`, `expediee` ou `retard` n'est pas éligible à un remboursement pour retour : elle peut faire l'objet d'une réclamation transporteur (voir FAQ F03), pas d'un remboursement pour insatisfaction.
3. **Commande annulée.** Une commande `annulee` est hors périmètre de cet outil : elle suit le circuit d'annulation, pas celui du retour.
4. **Défaut de fabrication.** Un produit défectueux à réception peut être remboursé **hors délai des 14 jours**, sous garantie légale. Ce cas ne peut pas être vérifié automatiquement par l'outil : il doit toujours être escaladé à un conseiller humain, quelle que soit l'ancienneté de la commande.
5. **Montant.** Le montant remboursable est le montant de la commande (`montant_eur`). Il n'y a pas de remboursement partiel automatisé dans ce dispositif.

## Ce que l'outil ne décide jamais seul

Même quand une commande est éligible selon les règles ci-dessus, **aucun remboursement n'est déclenché automatiquement** par l'agent de base (étape 2 du brief) : l'outil de vérification renvoie un verdict et son motif, la décision d'exécuter le remboursement reste humaine. L'étape optionnelle du brief (étape 4) explore, sous garde-fous stricts, ce que signifierait laisser l'agent déclencher lui-même le remboursement dans les cas les plus clairs.
