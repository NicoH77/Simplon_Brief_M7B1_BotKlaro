# M6 - Concepts techniques : de la surveillance d'un modèle à la décision de déploiement

Synthèse des concepts rencontrés en surveillant un modèle de classification en production, en fiabilisant ses données de retour terrain, puis en décidant s'il faut le remplacer. À relire pour réviser. Trois fils : **savoir** (étape 1), **comprendre** (étape 2), **décider** (étape 3).

---

## Partie A - Surveiller un modèle en production

### Qu'est-ce que la dérive de données

Un modèle apprend une relation entre des variables d'entrée et une cible, sur une période donnée. Si les variables d'entrée changent ensuite de comportement, le modèle continue de raisonner sur un monde qui n'existe plus.

| Notion | Définition |
|---|---|
| **Référence** | Le jeu de données sur lequel le modèle a été entraîné. Fixe, sert de point de comparaison. |
| **Dérive de données (data drift)** | Écart entre la distribution des variables d'entrée en production et leur distribution en référence. |
| **Fenêtre courante** | L'échantillon de production qu'on compare à la référence (une semaine, un mois...). |

**Règle d'or.** On compare toujours à la référence d'entraînement, jamais à la période précédente. Une comparaison glissante mesure une variation locale, pas un écart au monde appris : un décalage qui s'installe durablement devient invisible dès la deuxième comparaison, car la nouvelle distribution devient sa propre référence.

### Mesurer un écart de distribution

| Méthode | Principe | Limite |
|---|---|---|
| **PSI (Population Stability Index)** | Découpe la référence en tranches de quantiles, compare la proportion d'observations par tranche entre référence et fenêtre courante. Taille d'effet, robuste au volume. | Seuils usuels : `< 0,1` stable, `0,1-0,25` à surveiller, `> 0,25` significatif. |
| **Test de Kolmogorov-Smirnov (KS)** | Test statistique, renvoie une p-value. | Détecte un écart minime dès que l'échantillon est grand. À garder indicatif, jamais décisionnel seul. |

**Repère :** en production, des bibliothèques comme Evidently fournissent les mêmes mesures de dérive avec plus d'outillage.

### Segmentation

Un écart massif localisé sur une minorité d'un ensemble peut être dilué par la majorité saine dès qu'on calcule un indicateur global. Un indicateur agrégé peut donc rester sous le seuil d'alerte alors qu'un sous-groupe est fortement touché.

**Règle d'or.** Toujours répéter le calcul à une granularité plus fine (sous-groupe, puis unité individuelle si besoin) avant de conclure à l'absence de dérive.

### Deux causes archétypales d'un écart

| Cause | Signature | Correctif |
|---|---|---|
| **Anomalie de mesure** (la chaîne de captation a changé, pas la réalité) | Écart localisé sur une seule famille de variables ; performance réelle inchangée sur le périmètre concerné | Corriger à la source. **Pas de réentraînement.** |
| **Population réellement différente** (des cas jamais vus en apprentissage) | Écart sur plusieurs variables liées entre elles ; performance réelle dégradée | Réentraînement légitime. Discuter le périmètre (modèle unique enrichi ou modèle dédié). |

**Règle d'or.** Traiter une anomalie de mesure par un réentraînement fait apprendre au modèle l'erreur de mesure elle-même, pas un phénomène réel.

---

## Partie B - Fiabiliser la vérité terrain

### Étiquettes et vérité terrain

Pour savoir si un modèle a raison, il faut confronter ses prédictions à ce qui s'est réellement passé (l'étiquette). Ces étiquettes proviennent souvent de plusieurs sources, chacune avec sa propre couverture et ses propres angles morts.

### Le biais de vérification

Quand on ne vérifie que ce qu'un système a lui-même signalé, toute métrique calculée sur ce seul sous-ensemble est biaisée par construction : le dénominateur exclut les cas que le système a manqués. Un rappel calculé de cette façon tend mécaniquement vers 1 et ne mesure plus rien.

| Piège | Parade |
|---|---|
| Mesurer la performance uniquement à partir des cas déjà signalés par le système | Croiser avec une source de vérité **indépendante** des signalements du système |
| Réentraîner uniquement sur ce corpus | Boucle auto-confirmante : le modèle n'apprend jamais sur ses propres angles morts |

### Rapprocher des sources hétérogènes

Quand deux systèmes désignent la même entité avec des identifiants dans des formats différents, il faut normaliser une clé commune avant de pouvoir les rapprocher. Un rapprochement mal fait (jointure silencieusement incomplète) masque le problème plutôt que de le révéler : mieux vaut compter explicitement les entrées non résolues que les ignorer.

---

## Partie C - Comparer, décider, déployer

### Rappel des métriques classiques

| Métrique | Ce qu'elle dit | Quand s'en méfier |
|---|---|---|
| **Précision** | Part des alertes qui sont de vrais positifs | À lire avec le rappel |
| **Rappel** | Part des positifs réels effectivement détectés | À lire avec la précision |
| **F1** | Moyenne harmonique des deux | Traite un faux positif et un faux négatif comme des erreurs de poids égal |
| **Accuracy** | Part de prédictions correctes, toutes classes confondues | Trompeuse sur des classes déséquilibrées |

### Coût attendu (évaluation sensible au coût)

Quand les erreurs n'ont pas le même impact (un faux négatif coûte beaucoup plus cher qu'un faux positif, ou l'inverse), aucune métrique classique seule ne capture cette asymétrie. On valorise chaque case de la matrice de confusion par son coût réel, puis on somme :

```
coût attendu = (TP × coût_TP) + (FP × coût_FP) + (FN × coût_FN) + (TN × coût_TN)
```

**Règle d'or.** Comparer deux modèles **au même seuil, sur le même jeu de test**. Un seuil différent ou un jeu de données différent invalide la comparaison, quel que soit l'écart de score observé.

### Réentraîner et déployer

| Notion | Idée |
|---|---|
| **Champion / challenger** | Le modèle en production et le modèle candidat, comparés côte à côte avant toute décision |
| **Registre de modèles** | Système qui versionne les modèles et matérialise lequel sert le trafic en production |
| **Décision de déploiement** | Acte explicite et motivé. Jamais automatique quand l'enjeu (coût, sécurité) est fort |

**Ordre à respecter.** Corriger d'abord toute anomalie de mesure identifiée en amont, puis réentraîner, puis comparer au modèle en production, puis décider. Un modèle candidat entraîné avant correction de la mesure est construit sur une donnée faussée, quel que soit le score obtenu ensuite.

---

## Trois principes transversaux du module

1. **On compare à une référence fixe, jamais à la période précédente.** Sinon on mesure une variation, pas un écart au monde appris.
2. **Toutes les causes d'un écart n'appellent pas le même correctif.** Distinguer une anomalie de mesure d'un changement réel avant d'agir, sous peine de corriger le mauvais problème.
3. **La métrique de décision doit refléter le coût réel des erreurs**, pas un score moyen abstrait qui traite toutes les erreurs comme équivalentes.
