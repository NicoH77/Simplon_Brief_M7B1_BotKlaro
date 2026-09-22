"""Utilitaires partages par les 4 agents (fourni, ne pas modifier).

Mutualise ce dont chaque agent LLM a besoin : construire le modele Mistral
une seule fois (avec un debit limite, pour eviter les erreurs 429 du palier
gratuit), reessayer un appel qui se heurte quand meme a un 429, convertir
l'historique de messages LangChain en une trace exploitable, mener une
conversation simple en respectant le budget d'actions (agents 1 et 2), et
ecrire une trace JSON coherente pour tous les agents.
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from functools import lru_cache

from .. import config as C


@lru_cache(maxsize=1)
def construire_modele_llm():
    """Construit le modele Mistral utilise par les 4 agents (une seule fois,
    voir `lru_cache` ci-dessus).

    `InMemoryRateLimiter` espace les appels sortants : sans lui, une boucle
    d'appels rapprochee (l'agent 3 sur plusieurs messages, par exemple)
    declenche presque a coup sur une erreur 429 "Rate limit exceeded" sur le
    palier gratuit de l'API Mistral. C.MISTRAL_REQUETES_PAR_SECONDE (config.py)
    pilote ce debit : baissez-le encore si vous continuez a voir des 429.

    Le `lru_cache` est essentiel, pas juste une optimisation : sans lui,
    chaque appel reconstruirait un nouveau limiteur avec un compteur remis a
    zero, et la limite de debit ne s'appliquerait jamais vraiment entre deux
    appels successifs.

    Ce limiteur espace les appels a l'avance, mais ne garantit rien a lui
    seul : un palier gratuit peut rester plus restrictif (quota partage,
    fenetre glissante...). `executer_avec_reprises` (ci-dessous) est le
    filet de securite qui absorbe les 429 malgre tout.
    """
    from langchain.chat_models import init_chat_model
    from langchain_core.rate_limiters import InMemoryRateLimiter

    limiteur = InMemoryRateLimiter(
        requests_per_second=C.MISTRAL_REQUETES_PAR_SECONDE,
        check_every_n_seconds=0.1,
        max_bucket_size=1,
    )
    return init_chat_model(C.MODELE_MISTRAL, rate_limiter=limiteur)


def executer_avec_reprises(fonction, *args, **kwargs):
    """Execute `fonction(*args, **kwargs)` et reessaie, avec un delai
    croissant, si l'appel se heurte a une erreur 429 (limite de debit
    depassee cote API).

    Important a comprendre : le retry integre de `langchain-mistralai` (le
    parametre `max_retries` du modele) ne couvre QUE les erreurs reseau
    (connexion coupee, timeout), pas les reponses HTTP 429 elles-memes, qui
    sont levees immediatement. C'est cette fonction qui comble ce manque.

    Utilisee par toutes les fonctions fournies qui declenchent un appel API
    (`executer_conversation`, `agent4_autonomie.executer_agent4`,
    `agent3_pretriage.pretrier`) : vous n'avez normalement pas besoin de
    l'appeler vous-meme dans votre propre code.
    """
    import httpx

    attente = C.MISTRAL_ATTENTE_INITIALE_RETRY
    derniere_erreur = None
    for tentative in range(1, C.MISTRAL_TENTATIVES_MAX + 1):
        try:
            return fonction(*args, **kwargs)
        except httpx.HTTPStatusError as erreur:
            if erreur.response.status_code != 429:
                raise
            derniere_erreur = erreur
            if tentative < C.MISTRAL_TENTATIVES_MAX:
                print(f"    (429 rate limit, nouvelle tentative dans {attente:.0f}s "
                     f"[{tentative}/{C.MISTRAL_TENTATIVES_MAX}])")
                time.sleep(attente)
                attente *= 2
    raise derniere_erreur


def extraire_trace(messages: list) -> list[dict]:
    """Convertit l'historique de messages d'un agent LangChain en une liste de
    dictionnaires JSON-serialisables (role, contenu, appels d'outils).

    C'est cette fonction qui rend la traçabilité vérifiable : chaque appel
    d'outil que le modèle a effectué, avec ses arguments, apparaît ici, pas
    seulement la réponse finale.
    """
    trace = []
    for m in messages:
        entree = {"role": type(m).__name__, "content": getattr(m, "content", None)}
        tool_calls = getattr(m, "tool_calls", None)
        if tool_calls:
            entree["tool_calls"] = [{"name": tc["name"], "args": tc["args"]} for tc in tool_calls]
        nom_outil = getattr(m, "name", None)
        if nom_outil:
            entree["tool_name"] = nom_outil
        trace.append(entree)
    return trace


def executer_conversation(agent, message_utilisateur: str) -> dict:
    """Invoque un agent LangChain sur un seul message utilisateur.

    Retourne {"reponse": ..., "trace": ...}. Suffisant pour les agents 1 et 2,
    qui n'ont pas besoin de suspendre leur execution (pas d'outil d'ecriture).
    L'agent 4, qui peut etre interrompu par le middleware human-in-the-loop,
    a son propre point d'entree dans `agent4_autonomie.py`.
    """
    config = {"recursion_limit": C.AGENT_BUDGET_ACTIONS * 2 + 1}
    resultat = executer_avec_reprises(
        agent.invoke, {"messages": [{"role": "user", "content": message_utilisateur}]}, config)
    messages = resultat["messages"]
    return {"reponse": messages[-1].content, "trace": extraire_trace(messages)}


def tracer(nom_agent: str, resultat: dict) -> dict:
    """Ecrit resultat dans outputs/traces_agent/ et ajoute le chemin du fichier."""
    horodate = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    nom = f"{nom_agent}_{horodate}.json"
    (C.DIR_TRACES / nom).write_text(
        json.dumps(resultat, ensure_ascii=False, indent=2, default=str))
    resultat["fichier_trace"] = str(C.DIR_TRACES / nom)
    return resultat
