# Module 7 bis - Klaro - Squelette du binôme

Point de départ du Module 7 bis. Les données, le chargement, les outils
communs et le harnais de test sont fournis. **À vous d'implémenter** les
fonctions marquées `TODO` / `NotImplementedError` dans `src/agent/`, en
suivant le brief.

Travail **en binôme**, dans un dépôt partagé : chaque apprenant complète les
2 agents qui lui sont attribués.

## Mise en route

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python scripts/run_all.py   # echoue tant que les TODO ne sont pas faits
```

`run_all.py` est votre harnais de test : chaque fonction complétée fait
avancer l'exécution un peu plus loin. Le notebook
`notebooks/M7B_pilotage.ipynb` guide étape par étape.

Les 4 agents s'appuient tous sur un vrai modèle **Mistral** : il n'y a pas de
mode hors ligne. Avant toute chose, copiez `.env.example` en `.env` et
renseignez `MISTRAL_API_KEY` (clé sur https://console.mistral.ai/, une par
binôme suffit, jamais commitée).

## Qui fait quoi (proposition, à négocier en étape 1)

| Apprenant | Agents | Fichiers à compléter |
|---|---|---|
| **A** | Agent 1 (renseignement) + Agent 3 (pré-triage) | `agent1_renseignement.py`, `agent3_pretriage.py` |
| **B** | Agent 2 (remboursement) + Agent 4 (autonomie) | `agent2_remboursement.py`, `agent4_autonomie.py` |

## Où travailler

| Fichier | Fonction à compléter |
|---|---|
| `src/agent/agent1_renseignement.py` | `construire_agent` |
| `src/agent/agent2_remboursement.py` | `construire_agent` |
| `src/agent/agent3_pretriage.py` | `classifier_message` |
| `src/agent/agent4_autonomie.py` | `construire_agent` (avec `HumanInTheLoopMiddleware`) |

Pour chaque fonction, ce qu'elle doit faire et comment elle est appelée :
voir `docs/M7B_07_Support_Remplissage_Code.md`.

L'étape 1 (note d'architecture et de risques), l'étape 3 (rapport
d'évaluation croisée) et l'étape 4 (synthèse et décision) sont des
**livrables écrits**, pas du code avec des TODO : voir le brief.

## Fourni (ne pas réimplémenter, sauf envie)

`config.py`, `data.py`, les fixtures de `data/`, `agent/ancien_bot.py`,
`agent/tools.py` (y compris le plafond de remboursement, vérifié dans
`initier_remboursement`), `agent/commun.py` (`construire_modele_llm` avec son
débit limité, `executer_avec_reprises` pour absorber un 429 isolé,
`extraire_trace`, `executer_conversation`, `tracer`), `scripts/run_all.py`,
`PROMPT_SYSTEME` dans chaque agent, `_parser_reponse_json` /
`simuler_validation` / `taux` dans `agent3_pretriage.py`, l'orchestration
`repondre` dans `agent1_*` / `agent2_*`, l'orchestration `executer_agent4`
dans `agent4_autonomie.py`.

## Ce qui est évalué

Voir le brief. En résumé : une note d'architecture et de risques cohérente
avant tout code, des agents dont chaque information est traçable à un appel
d'outil, une frontière de décision vérifiable dans le code (un seul outil
d'écriture, réservé à l'agent 4, verrouillé par un middleware human-in-the-
loop et par un plafond vérifié dans l'outil), une évaluation croisée
sincère des agents de son binôme, et une décision de déploiement commune
argumentée.
