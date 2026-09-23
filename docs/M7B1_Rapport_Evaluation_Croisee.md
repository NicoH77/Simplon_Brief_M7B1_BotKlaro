# Rapport d'évaluation croisée (étape 3)

**Évaluateur :** apprenant en charge des agents 2 et 4
**Agents évalués :** agent 1 (renseignement général) et agent 3 (pré-triage), développés par le binôme
**Base de l'évaluation :** exécution réelle via `scripts/run_all.py` et `notebooks/M7B_pilotage.ipynb`, lecture du code et des traces JSON de `outputs/traces_agent/`

---

## 1. Agent 1 — Renseignement général

### 1.1 Traçabilité : respectée

Chaque information factuelle de la réponse est rattachable à un appel d'outil visible dans la trace.

Cas testé : « Où en est ma commande CMD-1013 ? »

```
-> appel outil : consulter_commande({'commande_id': 'CMD-1013'})
<- resultat : {'trouvee': True, 'produit': 'Enceinte bluetooth Sona',
               'montant_eur': 79.0, 'statut': 'retard', ...}
```

Le produit, le montant, le statut et la date annoncés au client proviennent tous
de ce résultat. Aucune donnée inventée sur ce cas.

Comparaison avec l'ancien bot sur la même question : « Je n'ai pas compris votre
demande ». L'écart est net et démontre l'apport de l'architecture outillée.

### 1.2 Frontière de décision : vérifiable dans le code

`construire_agent` ne transmet que deux outils :

```python
tools=[outils["chercher_faq"], outils["consulter_commande"]]
```

`initier_remboursement` et `verifier_eligibilite_remboursement` sont absents de
la liste. L'agent ne peut donc structurellement ni promettre, ni vérifier, ni
exécuter un remboursement, indépendamment de ce que dit son prompt système ou
de toute tentative d'injection. La frontière est vérifiable par lecture de trois
lignes de code, ce qui est exactement le critère demandé.

### 1.3 Point d'amélioration : des engagements non adossés à un outil

Sur CMD-1013, l'agent a conclu par : « Je vais vérifier les raisons de ce retard
et vous tenir informé ». Aucun outil ne lui permet de faire l'un ou l'autre.
C'est une promesse sans support technique — moins grave que celle de l'ancien
bot (elle n'a pas d'effet financier), mais de même nature : elle crée une
attente que le système ne peut pas honorer.

Correction suggérée : ajouter au prompt système l'interdiction d'annoncer une
action future, et renvoyer explicitement vers un conseiller.

### 1.4 Point d'architecture : le transfert vers l'agent 2 est déclaratif

Le prompt demande à l'agent 1 d'indiquer que « l'agent remboursement va
reprendre la demande ». Cette phrase n'est qu'un texte : il n'existe aucun lien
technique entre les deux agents. Aucun orchestrateur, aucun routage.

Ce cloisonnement est cohérent avec le brief (périmètres clairs et limités) et ne
doit pas être corrigé à la légère : un agent capable d'en appeler un autre
hériterait indirectement de ses capacités et rendrait la frontière de décision
beaucoup plus difficile à prouver. En revanche, la limite doit être documentée :
en l'état, un client dont la demande est mal orientée n'est repris par personne.

---

## 2. Agent 3 — Pré-triage des messages entrants

### 2.1 Choix technique : appel direct au modèle, sans outil

L'agent 3 n'utilise pas `create_agent` mais `modele.invoke(prompt).content`.
Le choix est justifié : la tâche est une classification à partir du seul texte
du message, sans donnée métier à consulter. Savoir ne pas outiller un agent
quand ce n'est pas nécessaire est un choix d'architecture pertinent.

### 2.2 Garde-fou : le parsing, pas la liste d'outils

Le contrôle porte ici sur la **sortie** du modèle. `_parser_reponse_json`
extrait le JSON même mal formaté, **rejette toute catégorie absente de
`C.TAXONOMIE`** (repli sur `"autre"`), borne la confiance entre 0 et 1, et ne
lève jamais d'exception. Un message mal classé ne peut pas faire tomber
l'ensemble du pré-triage. Correctement fait.

### 2.3 Défaut relevé : la taxonomie est dupliquée dans le prompt

Le prompt liste les six catégories en dur :

```
- livraison
- retour_remboursement
- compte
- produit
- paiement
- autre
```

alors que `C.TAXONOMIE` existe dans `config.py` et pourrait être injectée par
`", ".join(C.TAXONOMIE)`. Aujourd'hui les deux listes coïncident, donc rien ne
casse. Mais si la taxonomie évolue dans `config.py`, le prompt ne suivra pas :
le modèle continuera de proposer les anciennes catégories, que le parseur
rejettera systématiquement en `"autre"`. La panne serait silencieuse et
difficile à diagnostiquer.

Correction : une ligne à changer dans le prompt. À faire avant tout déploiement.

### 2.4 Biais d'automatisation : mesuré, et l'alerte se déclenche

Résultats obtenus sur 8 messages (`LIMITE_MESSAGES_PRETRIAGE = 8`) :

| Indicateur | Valeur |
|---|---|
| `taux_accord_global` | 0,875 |
| `taux_accord_ambigus` | nan |
| `part_validee_sans_modification` | 0,875 |
| `alerte_biais_automatisation` | **True** |

Lecture : 87,5 % des propositions de l'agent ont été validées **sans aucune
modification**, ce qui déclenche l'alerte (seuil 0,8).

Le piège à ne pas commettre est de lire ce chiffre comme une réussite. Le
simulateur de validation applique `p_valider_tel_quel = 0.55 + 0.4 * conf` :
**plus l'agent est confiant, plus le conseiller valide sans regarder**. Un taux
élevé ne signifie donc pas que l'agent est bon, mais que le contrôle humain
s'érode. C'est précisément la crainte formulée par Karim Diallo : « je veux être
sûr qu'ils valident vraiment, pas qu'ils cliquent sans regarder ».

Réserve méthodologique : `taux_accord_ambigus` vaut `nan`, car l'échantillon de
8 messages ne contient aucun message marqué ambigu. Or ce sont justement les cas
ambigus qui testent la qualité du tri. Le run final doit passer
`LIMITE_MESSAGES_PRETRIAGE` à `None` (50 messages) pour que cet indicateur ait
une valeur.

### 2.5 Risque de détournement en outil de surveillance

Les métriques produites (qui corrige, à quelle fréquence, avec quel écart)
peuvent basculer d'aide opérationnelle en mesure individuelle de performance.
Le code ne produit aujourd'hui que des taux agrégés, ce qui est le bon choix,
mais rien n'empêche techniquement de les recalculer par conseiller.

Mesure à inscrire dans la gouvernance, pas dans le code : interdiction explicite
d'exploiter ces données à des fins d'évaluation individuelle, indicateurs
agrégés uniquement, transparence auprès des conseillers sur ce qui est enregistré.

---

## 3. Synthèse de l'évaluation

| Critère | Agent 1 | Agent 3 |
|---|---|---|
| Traçabilité des informations factuelles | Respectée | Sans objet (pas d'outil), justification fournie par le modèle |
| Frontière de décision vérifiable dans le code | Oui, par la liste `tools` | Oui, aucun outil d'écriture |
| Robustesse aux sorties mal formées | Sans objet | Bonne (`_parser_reponse_json`) |
| Défaut relevé | Promesses d'action sans outil support | Taxonomie dupliquée hors de `config.py` |
| Risque principal | Demande mal orientée non reprise | Biais d'automatisation (alerte active) |

Les deux agents remplissent les contraintes non négociables du brief. Les défauts
relevés sont des points de robustesse et de maintenance, non des failles de
sécurité : aucun des deux ne peut déclencher d'effet financier.
