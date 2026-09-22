# Note de risques
## Projet M7B1 Klaro - Analyse des risques liés aux agents IA

**Livrable :** note de risques  
**Projet :** M7B1 Klaro  
**Version :** 1.0

---

# 1. Objet du document

Cette note identifie les principaux risques associés à l'architecture multi-agents proposée pour Klaro.

Elle se concentre en particulier sur :

- les risques liés à l'automatisation des décisions de remboursement au regard du RGPD ;
- le risque de biais d'automatisation ;
- le risque que l'agent de pré-triage soit détourné de sa finalité initiale pour devenir un outil de surveillance des conseillers ;
- les risques techniques et organisationnels associés à l'utilisation d'agents IA.


---

# 2. Méthodologie d'analyse

Chaque risque est analysé selon les éléments suivants :

- description ;
- impact potentiel ;
- probabilité ;
- niveau de risque ;
- mesures de réduction proposées.

---

# 3. Risque principal : automatisation des remboursements et RGPD (article 22)

## 3.1 Contexte

Le remboursement d'une commande constitue une décision ayant un effet financier direct pour le client.

Le scénario décrit dans le contexte du projet présente un incident où un remboursement a été promis automatiquement sans vérification préalable.

---

## 3.2 Rappel de l'article 22 du RGPD

L'article 22 du RGPD encadre les décisions fondées exclusivement sur un traitement automatisé lorsqu'elles produisent des effets juridiques ou affectent significativement une personne.

Le risque pour Klaro apparaît lorsqu'un système informatique :

- analyse une demande ;
- décide seul de l'accorder ou de la refuser ;
- exécute automatiquement cette décision.

Dans un tel scénario, le client ne bénéficie plus d'une intervention humaine réelle dans le processus décisionnel.

---

## 3.3 Risque identifié

### Décision de remboursement entièrement automatisée

Un agent IA pourrait :

1. analyser une commande ;
2. appliquer la politique de remboursement ;
3. décider de l'éligibilité ;
4. déclencher le remboursement sans validation humaine.

Le client subirait alors une décision prise uniquement par une machine.

---

## 3.4 Impacts possibles

### Pour le client

- refus injustifié ;
- remboursement accordé par erreur ;
- impossibilité de comprendre la décision ;
- difficulté à contester le résultat.

### Pour Klaro

- non-conformité réglementaire ;
- risque juridique ;
- incidents financiers ;
- perte de confiance des clients ;
- difficultés d'audit.

---

## 3.5 Niveau de risque

| Critère | Évaluation |
|----------|-----------|
| Probabilité | Élevée si aucune protection n'est prévue |
| Impact | Élevé |
| Niveau global | Critique |

---

## 3.6 Mesures de réduction

### Séparation entre analyse et décision

L'agent 2 ne réalise qu'une analyse d'éligibilité.

Il peut produire :

- une justification ;
- un avis ;
- une recommandation.

Il ne peut jamais exécuter un remboursement.

### Validation humaine obligatoire

L'agent 4 peut préparer une action mais ne peut pas l'exécuter seul.

La décision finale appartient toujours à un humain.

### Human in the Loop réel

La validation doit être implémentée dans le flux d'exécution :

- interruption du traitement ;
- approbation explicite ;
- reprise contrôlée.

Une simple instruction dans un prompt n'est pas suffisante.

### Conservation des traces

Les éléments suivants doivent être enregistrés :

- commande analysée ;
- critères appliqués ;
- résultat de l'analyse ;
- identité du validateur ;
- décision finale.

---

# 4. Risque de validation humaine fictive

## 4.1 Description

Un risque fréquent dans les systèmes IA consiste à maintenir officiellement un humain dans la boucle alors qu'en pratique cet humain ne fait qu'approuver mécaniquement la proposition.

On parle parfois de validation de façade.

---

## 4.2 Exemple

L'agent recommande :

> Remboursement recommandé.

Le conseiller valide systématiquement sans relire les critères.

Au fil du temps, la décision réelle est donc prise par l'IA et non par l'humain.

---

## 4.3 Impacts

- perte de contrôle humain réel ;
- augmentation des erreurs ;
- détournement de la finalité de la validation ;
- risque de non-conformité.

---

## 4.4 Mesures de réduction

### Présentation des éléments justificatifs

Le conseiller doit voir :

- les données de commande ;
- les critères vérifiés ;
- les critères non vérifiés ;
- les informations manquantes.

### Validation active

Le validateur doit réaliser une action explicite :

- approuver ;
- refuser.

L'absence de réponse ne vaut jamais approbation.

### Audit régulier

Un contrôle périodique doit vérifier si :

- les dossiers sont réellement relus ;
- les refus existent ;
- les décisions humaines divergent parfois des recommandations IA.

---

# 5. Risque de biais d'automatisation

## 5.1 Description

Le biais d'automatisation correspond à la tendance des utilisateurs à considérer qu'un système automatisé a nécessairement raison.

Plus un système semble performant, plus l'utilisateur risque de lui faire confiance sans vérification.

---

## 5.2 Impact sur Klaro

Les conseillers pourraient :

- suivre aveuglément les recommandations ;
- ignorer leur propre jugement ;
- détecter moins souvent les erreurs.

---

## 5.3 Conséquences

- erreurs non détectées ;
- perte d'expertise humaine ;
- propagation de mauvaises décisions ;
- dépendance excessive à l'outil.

---

## 5.4 Mesures de réduction

### Aide à la décision uniquement

Les agents doivent être présentés comme :

> assistants à la décision

et non comme :

> décideurs automatiques.

### Affichage du niveau de confiance

Les recommandations doivent être accompagnées :

- d'une justification ;
- d'une confiance estimée ;
- des sources consultées.

### Formation des utilisateurs

Les conseillers doivent être sensibilisés au fait que :

- l'IA peut se tromper ;
- les recommandations doivent être vérifiées ;
- la responsabilité finale reste humaine.

---

# 6. Risque spécifique du pré-triage des messages

## 6.1 Finalité attendue

L'agent 3 a pour objectif :

- d'aider les conseillers ;
- de proposer une catégorie ;
- de réduire le temps de lecture initial.

Son rôle est organisationnel et non décisionnel.

---

# 7. Risque majeur : détournement en outil de surveillance

## 7.1 Description

Le risque apparaît lorsque les données produites par l'agent de pré-triage cessent d'être utilisées pour aider les conseillers et deviennent un moyen de mesurer ou d'évaluer leur activité.

Exemples :

- nombre de dossiers traités ;
- temps de validation ;
- taux de correction des propositions de l'agent ;
- comparaison entre conseillers.

---

## 7.2 Pourquoi ce risque existe

Le système génère naturellement des traces :

- catégories proposées ;
- validations ;
- corrections ;
- temps de traitement.

Ces informations peuvent être réutilisées à d'autres fins que l'assistance opérationnelle.

---

## 7.3 Scénario de dérive

Étape 1 :

Le système aide à classer les messages.

Étape 2 :

On mesure combien de fois un conseiller corrige la classification.

Étape 3 :

Ces indicateurs deviennent des critères de performance.

Étape 4 :

Le système ne sert plus principalement à aider les conseillers mais à les surveiller.

---

## 7.4 Conséquences pour les collaborateurs

### Conséquences individuelles

- sentiment de surveillance permanente ;
- perte d'autonomie ;
- autocensure ;
- stress accru.

### Conséquences collectives

- dégradation de la confiance ;
- résistance à l'outil ;
- baisse de la qualité des retours ;
- détournement de l'objectif du projet.

---

## 7.5 Niveau de risque

| Critère | Évaluation |
|----------|-----------|
| Probabilité | Moyenne |
| Impact | Élevé |
| Niveau global | Important |

---

## 7.6 Mesures de réduction

### Principe de finalité

Les données collectées doivent servir uniquement :

- à améliorer le tri ;
- à améliorer le système ;
- à améliorer la qualité de service.

Elles ne doivent pas être utilisées pour évaluer individuellement les conseillers.

### Limitation des métriques

Les tableaux de bord doivent privilégier :

- des indicateurs globaux ;
- des statistiques agrégées ;
- des mesures anonymisées lorsque cela est possible.

### Gouvernance claire

Une règle explicite doit préciser :

> Les données produites par l'agent de pré-triage ne constituent pas un système d'évaluation individuelle des salariés.

### Transparence

Les utilisateurs doivent savoir :

- quelles informations sont enregistrées ;
- pourquoi elles le sont ;
- qui peut y accéder ;
- combien de temps elles sont conservées.

---

# 8. Risque de mauvaise classification

## Description

L'agent 3 peut attribuer une mauvaise catégorie à un message.

Exemples :

- réclamation classée en simple demande d'information ;
- remboursement classé en question générale ;
- message ambigu mal interprété.

---

## Impacts

- retard de traitement ;
- mauvaise orientation ;
- dégradation de l'expérience client.

---

## Réduction du risque

- validation humaine systématique ;
- possibilité de correction ;
- amélioration progressive à partir des retours utilisateurs ;
- suivi des erreurs de classification.

---

# 9. Risque de manque de traçabilité

## Description

Sans historique fiable, il devient impossible de comprendre :

- quels outils ont été appelés ;
- quelles données ont été utilisées ;
- pourquoi une décision a été proposée.

---

## Conséquences

- audit impossible ;
- difficultés de débogage ;
- impossibilité de justifier certaines décisions.

---

## Mesures

Conserver pour chaque traitement :

- l'agent concerné ;
- les outils utilisés ;
- les sources consultées ;
- la réponse produite ;
- la validation humaine éventuelle.

---

# 10. Risque de fuite d'informations

## Description

Le système manipule :

- des données clients ;
- des commandes ;
- des historiques de tickets.

Une mauvaise gestion des traces ou des prompts peut entraîner une exposition inutile de données personnelles.

---

## Mesures

- minimisation des données ;
- contrôle des accès ;
- non-enregistrement des secrets ;
- limitation des informations présentes dans les logs ;
- revue régulière des traces produites.

---

# 11. Synthèse des risques

| Risque | Niveau |
|----------|----------|
| Remboursement automatisé sans validation humaine | Critique |
| Validation humaine de façade | Élevé |
| Biais d'automatisation | Élevé |
| Détournement du pré-triage en outil de surveillance | Important |
| Mauvaise classification des messages | Moyen |
| Manque de traçabilité | Élevé |
| Fuite d'informations | Élevé |

---

# 12. Conclusion

Le principal risque du projet concerne l'automatisation d'une décision financière. Pour rester conforme aux principes du RGPD et aux exigences du projet, l'IA doit rester un outil d'assistance et non un décideur autonome.

La séparation entre l'agent d'analyse (Agent 2) et l'agent d'exécution contrôlée (Agent 4), associée à une validation humaine réelle, constitue le principal mécanisme de maîtrise du risque.

Concernant l'agent de pré-triage, le danger majeur n'est pas technique mais organisationnel : un outil conçu pour aider les conseillers pourrait progressivement être utilisé pour les évaluer ou les surveiller. Une gouvernance claire, la limitation des indicateurs individuels et le respect du principe de finalité sont donc indispensables pour préserver la confiance des utilisateurs et l'acceptabilité du système.