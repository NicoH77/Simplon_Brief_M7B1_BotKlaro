# Synthèse d'intégration et décision de déploiement (étape 4)

**Livrable commun** — établi à partir des deux rapports d'évaluation croisée et
de l'exécution complète de `scripts/run_all.py`.

---

## 1. Ce qui fonctionne

L'exécution de bout en bout est reproductible : `python scripts/run_all.py`
déroule l'ancien bot, les 4 agents, et régénère les traces des 4 agents dans
`outputs/traces_agent/` sans intervention manuelle.

**La frontière de décision est vérifiable dans le code**, agent par agent :

| Agent | Outils reçus | Peut écrire ? |
|---|---|---|
| Agent 1 | `chercher_faq`, `consulter_commande` | Non |
| Agent 2 | `verifier_eligibilite_remboursement`, `rechercher_historique` | Non |
| Agent 3 | aucun (appel direct au modèle) | Non |
| Agent 4 | `verifier_eligibilite_remboursement`, `initier_remboursement` | Oui, sous conditions |

L'unique outil d'écriture n'est transmis qu'à l'agent 4. Cette vérification se
fait par lecture de quatre fonctions `construire_agent`, sans avoir à faire
confiance aux prompts.

**Le verrou human-in-the-loop fonctionne.** Sur les trois cas de l'agent 4,
`HumanInTheLoopMiddleware` a suspendu l'exécution avant tout appel à
`initier_remboursement` (`interrompu: True`). Le cas 2, avec une décision
`reject`, n'a produit aucune écriture. L'interruption est dans le graphe
d'exécution, pas dans le prompt : le modèle ne peut pas la contourner.

C'est la réponse directe à l'exigence d'Élise Vasseur et à l'article 22 du RGPD :
il n'existe plus de décision automatisée à effet financier sans intervention
humaine explicite.

---

## 2. Incohérences relevées entre agents

### 2.1 Politique de remboursement : un agent la réinterprète

`data/politique_remboursement.md` est explicite : « Il n'y a pas de remboursement
partiel automatisé dans ce dispositif ». Or l'agent 2, sur CMD-1004, a répondu
que la commande est « **éligible à un remboursement partiel** », en
réinterprétant le champ `montant_max_eur` renvoyé par l'outil comme un plafond
négociable.

Un client qui interroge l'agent 2 puis l'agent 4 sur la même commande peut donc
recevoir deux cadrages différents de la même règle. La politique elle-même est
bien centralisée dans `tools.py` — le verdict d'éligibilité est identique — mais
sa **restitution en langage naturel** diverge.

### 2.2 Informations inventées dans une réponse

Toujours sur CMD-1004, l'agent 2 a cité le ticket **T-512** alors que
`rechercher_historique` lui avait renvoyé **T-516**, et a fabriqué une URL
`support.klaro.com` qui n'existe dans aucune source. Son prompt lui interdit
pourtant d'affirmer ce qui ne provient pas d'un outil.

Constat : une règle inscrite dans un prompt n'est pas un contrôle. Seul ce qui
est contraint par le code tient.

### 2.3 Taxonomie dupliquée

L'agent 3 liste les six catégories en dur dans son prompt au lieu d'utiliser
`C.TAXONOMIE`. Les deux listes coïncident aujourd'hui ; une évolution de la
taxonomie provoquerait une panne silencieuse (toutes les propositions rejetées
en `"autre"` par le parseur).

### 2.4 Aucun routage entre agents

Les 4 agents sont indépendants : aucun ne peut en appeler un autre. Le
« transfert » de l'agent 1 vers l'agent 2 est une phrase, pas un mécanisme.
Ce cloisonnement est volontaire et protège la frontière de décision, mais il
signifie qu'aucune demande n'est réellement orientée : la sortie de l'agent 3
est mesurée, jamais routée.

---

## 3. Faille bloquante : le plafond contrôle une donnée non fiable

Le cas 3 (CMD-1009) devait démontrer le refus par plafond. Il a produit
l'inverse : `statut: "rembourse"`.

- Montant réel de la commande : **499,00 €**
- Montant annoncé par le modèle et transmis à l'outil : **49,90 €**
- Plafond automatisable : **60,00 €**

`initier_remboursement(commande_id, montant_eur)` compare au plafond la valeur
**fournie par le LLM**, sans jamais relire `commandes.csv`. Le contrôle est
correctement écrit mais s'applique à une donnée non vérifiée. Un remboursement
de 499 € a donc été déclenché sous un plafond de 60 €, après approbation humaine.

Le modèle imposé (`ministral-14b-2512`) rend ce type d'erreur de lecture plus
fréquent qu'un grand modèle, mais le défaut est de conception : il existerait à
l'identique avec un modèle plus performant, simplement moins souvent déclenché,
donc plus difficile à détecter.

**Correction requise :** l'outil doit ignorer l'argument `montant_eur` et relire
le montant réel via `self.consulter_commande(commande_id)["montant_eur"]` avant
comparaison. Le modèle ne fournirait alors que l'identifiant de commande, qu'il
ne peut pas inventer sans être détecté (`trouvee: False`).

**Principe retenu :** un garde-fou ne vaut que par la fiabilité de la donnée
qu'il contrôle. Une valeur produite par un LLM ne doit jamais servir d'entrée à
un contrôle de sécurité.

---

## 4. Décision de déploiement

### Agents 1, 2 et 3 : déploiement en assistance, sous conditions

Ces trois agents n'ont aucun outil d'écriture : leur pire défaillance est une
réponse inexacte, jamais un effet financier. Ils apportent un gain net par
rapport à l'ancien bot, qui ne consultait aucune donnée.

Conditions préalables :

1. Renforcer les prompts des agents 1 et 2 contre l'ajout d'informations non
   issues d'un outil (références de tickets, URL, promesses d'action).
2. Remplacer la liste de catégories en dur de l'agent 3 par `C.TAXONOMIE`.
3. Repasser `LIMITE_MESSAGES_PRETRIAGE` à `None` et mesurer
   `taux_accord_ambigus` sur les 50 messages avant toute mise en service.
4. Afficher systématiquement au conseiller la trace des appels d'outils, et non
   la seule réponse finale.

### Agent 4 : déploiement refusé en l'état

Motif : la faille du paragraphe 3. Le second garde-fou, présenté comme
indépendant du modèle, dépend en réalité d'une valeur produite par le modèle.
Un seul verrou effectif subsiste (le middleware), ce qui est insuffisant pour
une décision à effet financier.

Réexamen possible après correction de `initier_remboursement` et exécution d'une
campagne de tests incluant des commandes au-dessus et au-dessous du plafond.

### Surveillance du biais d'automatisation

`part_validee_sans_modification` atteint 0,875 et déclenche l'alerte. Un taux
élevé n'est pas un succès : il indique que le contrôle humain s'érode. À suivre
comme indicateur de dérive, avec revue périodique, et à n'exploiter qu'en
agrégé — jamais comme mesure individuelle de performance des conseillers.

---

## 5. Conclusion

L'architecture à 4 agents corrige les trois défauts de l'ancien bot : accès aux
données réelles, vérification avant toute décision de remboursement,
traçabilité complète des appels d'outils.

Elle démontre surtout que les garanties tiennent au **code** et non aux prompts :
partout où un contrôle a été placé dans une liste d'outils ou dans un middleware,
il a tenu ; partout où il reposait sur une consigne de prompt ou sur une donnée
produite par le modèle, il a cédé. C'est cette distinction qui fonde la décision
ci-dessus.
