# Module 7 bis - Support de remplissage du code

Ce document explique, pour chaque fonction à compléter dans le squelette, ce qu'elle doit faire, quelle logique mettre dedans, qui l'appelle, et quelle ressource lire en cas de blocage. Il ne donne pas de code : le but est de comprendre le comportement attendu avant d'écrire quoi que ce soit.

## 0. Avant de commencer : la clé API Mistral

Les 4 agents s'appuient tous sur un vrai modèle (**Mistral**) : il n'y a pas de mode hors ligne dans ce kit.

1. Créez une clé sur https://console.mistral.ai/ (une par binôme suffit).
2. Copiez `.env.example` en `.env` à la racine du projet, et collez votre clé :
   ```
   MISTRAL_API_KEY=votre_cle_ici
   ```
3. Ne mettez **jamais** cette clé directement dans un fichier `.py`, ni dans un commit. `.env` est déjà listé dans `.gitignore` : vérifiez que `git status` ne le montre jamais comme fichier à commiter.
4. `src/config.py` appelle `load_dotenv()` au chargement : c'est ce qui lit `.env` et rend la variable disponible. Vous n'avez rien d'autre à faire, `init_chat_model` (déjà fourni dans chaque agent) la retrouve tout seul.

## 1. Arborescence

```
M7B_Klaro_Squelette/
├── .env.example            modele pour votre cle Mistral - a copier en .env
├── data/                    fixtures fournies, ne pas modifier
│   ├── faq.json
│   ├── commandes.csv
│   ├── politique_remboursement.md
│   ├── tickets_historique.csv
│   └── messages_entrants.csv
├── src/
│   ├── config.py                    parametres + chargement de .env - fourni
│   ├── data.py                      chargement des fixtures - fourni
│   └── agent/
│       ├── ancien_bot.py            l'architecture existante, a evaluer - fourni
│       ├── tools.py                 5 outils partages (4 lecture + 1 ecriture) - fourni
│       ├── commun.py                modele partage, trace, conversation - fourni
│       ├── agent1_renseignement.py  Agent 1 - A COMPLETER
│       ├── agent2_remboursement.py  Agent 2 - A COMPLETER
│       ├── agent3_pretriage.py      Agent 3 - A COMPLETER
│       └── agent4_autonomie.py      Agent 4 - A COMPLETER
├── scripts/run_all.py      enchaine tout, de bout en bout - fourni
└── notebooks/M7B_pilotage.ipynb   meme enchainement, cellule par cellule - fourni
```

`run_all.py` est le fil conducteur : il fait tourner l'ancien bot sur quelques questions, puis les 4 agents chacun leur tour. Tant qu'une fonction n'est pas codée, il s'arrête sur `NotImplementedError` à cet endroit précis, dans l'ordre agent1 → agent2 → agent3 → agent4. **Chaque question posée à un agent est un appel API reel**, facturé ou décompté d'un quota gratuit.

Aucune donnée à générer : tout est dans `data/`, des fichiers fixes. Le point de référence temporel du scénario est `C.DATE_REFERENCE` (pas la date du jour de votre machine).

**À ne pas réimplémenter** : `ancien_bot.py`, `tools.py` et `commun.py` sont entièrement fournis. Ce sont les fonctions communes au binôme ; les modifier crée du conflit dans le dépôt partagé pour rien. Si vous pensez qu'il faut les changer, discutez-en avec votre binôme avant.

## 2. `src/agent/ancien_bot.py` (fourni, à observer avant tout)

Ne contient rien à compléter, mais c'est le point de départ de l'étape 1 : exécutez `repondre_ancien_bot(...)` sur plusieurs questions avant d'écrire la moindre ligne d'agent. Le docstring du fichier liste 3 défauts à retrouver par l'exécution, pas seulement par la lecture : aucun accès aux données réelles, un remboursement annoncé sans aucune vérification, aucune trace de ce qui a motivé la réponse. Ce fichier ne fait aucun appel API (pas de LLM), il tourne toujours hors ligne.

## 3. `src/agent/tools.py` et `src/agent/commun.py` (fournis)

**Ressource générale pour ces deux fichiers** : https://docs.langchain.com/oss/python/langgraph/overview (agents outillés, API `create_agent`, décorateur `@tool`).

`ContexteOutils` expose 5 méthodes, utilisées par les 4 agents selon leur périmètre :

| Méthode | Type | Utilisée par |
|---|---|---|
| `chercher_faq(mots_cles, k=3)` | lecture | Agent 1 |
| `consulter_commande(commande_id)` | lecture | Agent 1 |
| `verifier_eligibilite_remboursement(commande_id)` | lecture | Agent 2, Agent 4 |
| `rechercher_historique(requete, k=3)` | lecture | Agent 2 |
| `initier_remboursement(commande_id, montant_eur)` | **écriture** | Agent 4 seulement |

`initier_remboursement` refuse elle-même (statut `"refuse"`) tout montant au-dessus de `C.MONTANT_MAX_AUTO` : c'est un garde-fou **dans le code**, indépendant de ce que l'agent 4 propose ou de ce qu'un humain approuve par erreur. Gardez ce comportement en tête : même bien construit, l'agent 4 ne peut pas le contourner.

`outils_langchain(ctx)` retourne un dictionnaire (et non une liste) qui enveloppe ces 5 méthodes en outils LangChain, clé par nom (`"chercher_faq"`, `"consulter_commande"`, etc.). Chaque agent n'importe que le sous-ensemble qui le concerne, par exemple dans `agent1_renseignement.py` :

```python
outils = outils_langchain(ctx)
mes_outils = [outils["chercher_faq"], outils["consulter_commande"]]
```

C'est ce sous-ensemble, choisi fichier par fichier, qui matérialise dans le code la frontière de décision demandée par le brief : `initier_remboursement` n'apparaît que dans `agent4_autonomie.py`.

`commun.py` fournit cinq fonctions que vous appellerez sans les modifier :
- `construire_modele_llm()` : construit **le** modèle Mistral partagé par les 4 agents, avec un débit limité (`InMemoryRateLimiter`) pour éviter les erreurs `429 Rate limit exceeded` du palier gratuit. Elle est mise en cache (`@lru_cache`) : **appelez-la à chaque fois que vous avez besoin d'un modèle, ne stockez pas le résultat dans une variable globale vous-même**, c'est déjà géré.
- `executer_avec_reprises(fonction, *args, **kwargs)` : exécute `fonction(*args, **kwargs)` et réessaie, avec un délai croissant, si l'appel se heurte quand même à un `429` malgré le débit limité (palier gratuit particulièrement restrictif, quota partagé...). Déjà branchée sur tous les appels API fournis (`executer_conversation`, `executer_agent4`, `pretrier`) : vous n'avez normalement pas à l'appeler vous-même.
- `extraire_trace(messages)` : convertit l'historique de messages d'un agent LangChain en une trace JSON-exploitable (rôle, contenu, appels d'outils).
- `executer_conversation(agent, question)` : invoque un agent sur une seule question et retourne `{"reponse": ..., "trace": ...}` ; utilisée par `repondre` dans les agents 1 et 2.
- `tracer(nom_agent, resultat)` : écrit le résultat dans `outputs/traces_agent/`.

**Si vous voyez une erreur `429` malgré tout, après plusieurs tentatives infructueuses** : baissez `C.MISTRAL_REQUETES_PAR_SECONDE` dans `config.py` (0.3 par défaut) et/ou augmentez `C.MISTRAL_TENTATIVES_MAX` / `C.MISTRAL_ATTENTE_INITIALE_RETRY`, puis relancez. Un `429` isolé pendant l'agent 3 ne doit plus jamais faire planter tout le pré-triage : vous verrez à la place un message `(429 rate limit, nouvelle tentative dans ...s)` dans la console, le temps que ça reparte.

## 4. `src/agent/agent1_renseignement.py`

Agent 1 : renseignement général (FAQ, statut de commande). Ne répond jamais aux questions de remboursement, il redirige vers l'agent 2.

### `construire_agent(ctx)`

Doit retourner un agent construit avec `create_agent` (import : `from langchain.agents import create_agent`).

Logique attendue :
- récupérez le dictionnaire d'outils avec `outils_langchain(ctx)` ;
- ne gardez que `chercher_faq` et `consulter_commande` dans la liste `tools` ;
- appelez `create_agent(model=construire_modele_llm(), tools=mes_outils, system_prompt=PROMPT_SYSTEME)` (`construire_modele_llm` vient de `commun.py`, `PROMPT_SYSTEME` est déjà fourni dans le fichier).

C'est ce choix de 2 outils, et l'absence de tout autre, qui garantit que cet agent ne peut **structurellement** pas déclencher ou promettre un remboursement, même si le prompt était mal rédigé ou contourné par le modèle. `repondre` (déjà fournie) appelle cette fonction, exécute la conversation via `executer_conversation` (voir `commun.py`), et trace le résultat.

**Ressource** : https://docs.langchain.com/oss/python/langgraph/overview (section `create_agent`).

## 5. `src/agent/agent2_remboursement.py`

Agent 2 : vérifie l'éligibilité au remboursement, **n'exécute jamais rien**.

### `construire_agent(ctx)`

Même logique que pour l'agent 1, mais avec `verifier_eligibilite_remboursement` et `rechercher_historique`. Aucun outil d'écriture ici : c'est ce qui garantit structurellement que cet agent ne peut jamais exécuter de remboursement, quel que soit le prompt.

`PROMPT_SYSTEME` et `repondre` sont déjà fournis.

## 6. `src/agent/agent3_pretriage.py`

**Ressource** : https://docs.langchain.com/oss/python/langchain/models (invoquer un modèle directement, sans passer par `create_agent` : pas besoin d'outils ici, juste d'un appel au modèle avec un prompt de classification).

### `classifier_message(texte)`

Doit interroger le modèle pour classer `texte` parmi les catégories de `C.TAXONOMIE`, et retourner un dict `{"categorie": ..., "confiance": ..., "justification": ...}`.

Logique attendue :
- récupérez le modèle avec `construire_modele_llm()` (importée de `commun.py` en haut du fichier) ;
- construisez un prompt qui liste les catégories possibles (`", ".join(C.TAXONOMIE)`) et qui demande **une réponse JSON stricte**, par exemple au format `{"categorie": "...", "confiance": 0.0, "justification": "..."}` ;
- appelez `modele.invoke(prompt).content` pour obtenir le texte brut de la réponse ;
- passez ce texte à `_parser_reponse_json` (déjà fournie juste en dessous) : elle extrait le JSON même s'il est entouré de texte ou de balises markdown, et se replie proprement sur `"autre"` si le modèle a mal répondu.

Un LLM peut renvoyer une réponse mal formée de temps en temps : c'est justement pour ça que `_parser_reponse_json` existe déjà, ne dupliquez pas cette logique, appelez-la.

**Piège classique.** N'appelez `construire_modele_llm()` qu'une fois par message (au début de `classifier_message`), pas plusieurs fois dans la même fonction : elle est déjà mise en cache, donc ça ne casse rien, mais ce n'est pas la peine.

Appelée par : `pretrier` (déjà fournie), une fois par message, dans la limite de `C.LIMITE_MESSAGES_PRETRIAGE`. Avec 8 messages et un débit de 0,5 requête/seconde (voir section 3), comptez environ 15-20 secondes pour que la cellule termine : c'est normal, ce n'est pas bloqué. `simuler_validation` et `taux` (déjà fournies, inchangées) n'ont pas besoin d'être modifiées : elles fonctionnent sur les colonnes que `pretrier` remplit, peu importe d'où vient la catégorie proposée.

## 7. `src/agent/agent4_autonomie.py`

Agent 4 : explore l'automatisation du remboursement dans les cas les plus simples, **sous contrôle strict**. C'est le seul fichier qui appelle `initier_remboursement`, et seulement derrière une validation humaine explicite.

### `construire_agent(ctx)`

Le TODO le plus consistant du brief. Doit retourner un agent construit avec :
- `model=construire_modele_llm()` (importée de `commun.py`) ;
- `tools` : `verifier_eligibilite_remboursement` et `initier_remboursement`, pioches dans `outils_langchain(ctx)` ;
- `system_prompt=PROMPT_SYSTEME` (déjà fourni) ;
- `middleware=[HumanInTheLoopMiddleware(interrupt_on={...})]`. Import :
  ```python
  from langchain.agents.middleware import HumanInTheLoopMiddleware
  ```
  La clé `interrupt_on` doit cibler **uniquement** `"initier_remboursement"` :
  ```python
  HumanInTheLoopMiddleware(
      interrupt_on={"initier_remboursement": {"allowed_decisions": ["approve", "reject"]}}
  )
  ```
  Ne mettez pas `verifier_eligibilite_remboursement` dans `interrupt_on` : c'est un outil de lecture, sans conséquence, il n'a pas besoin d'être validé.
- `checkpointer=InMemorySaver()`. Import :
  ```python
  from langgraph.checkpoint.memory import InMemorySaver
  ```
  Sans checkpointer, l'agent ne peut pas suspendre puis reprendre son exécution entre deux appels à `.invoke(...)` : c'est ce qui rend l'interruption possible.

C'est cette fonction, et elle seule, qui rend le remboursement automatisé impossible sans validation humaine explicite. Le second garde-fou (le plafond) est déjà dans l'outil lui-même (`tools.py`), vous n'avez rien à coder pour celui-là.

`executer_agent4` (déjà fournie) gère la mécanique d'interruption/reprise : elle appelle l'agent, détecte si l'exécution a été suspendue (`"__interrupt__" in resultat`), et si oui la reprend avec `Command(resume={"decisions": [decision]})`. Lisez cette fonction pour comprendre le flux avant de tester : c'est elle que `run_all.py` appelle avec 3 cas (approuvé, rejeté, montant au-dessus du plafond).

**Ressource** : https://docs.langchain.com/oss/python/langchain/human-in-the-loop (mécanisme complet, y compris la reprise après interruption) et https://reference.langchain.com/python/langchain/agents/middleware (détail de `HumanInTheLoopMiddleware`).

## 8. Ordre de travail conseillé

En binôme, une fois la répartition actée (étape 1) :

1. Configurez `.env` (section 0 ci-dessus) avant toute chose : rien ne fonctionne sans clé Mistral valide.
2. Chacun commence par lire (sans modifier) `tools.py` et `commun.py`, pour comprendre les outils disponibles.
3. Apprenant en charge de l'agent 1 : `construire_agent` dans `agent1_renseignement.py`.
4. Apprenant en charge de l'agent 2 : `construire_agent` dans `agent2_remboursement.py`.
5. Apprenant en charge de l'agent 3 : `classifier_message` dans `agent3_pretriage.py`. Gardez `C.LIMITE_MESSAGES_PRETRIAGE` à une petite valeur (8 par défaut) pendant que vous testez, remontez-la à `None` seulement pour le run final.
6. Apprenant en charge de l'agent 4 : `construire_agent` dans `agent4_autonomie.py`. À faire après l'agent 2 si possible : la logique d'éligibilité y est déjà familière.

À chaque fonction terminée, relancez `python scripts/run_all.py` : il avance un peu plus loin avant de buter sur le prochain `NotImplementedError`. Comme le dépôt est partagé, committez dès qu'une fonction passe, pour limiter les conflits de fusion avec votre binôme (et ne committez jamais `.env`).
