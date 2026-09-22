"""Agent 4 - Autonomie sous contrainte : propose puis, seulement si un humain
valide, declenche un remboursement automatise dans les cas les plus clairs.

C'est l'agent le plus proche de l'ancien bot dans ce qu'il PEUT faire (il a
acces a `initier_remboursement`) mais tout l'enjeu est de ne JAMAIS l'executer
sans verrou verifiable dans le code. Deux garde-fous independants du modele :

1. Un middleware `HumanInTheLoopMiddleware` (LangChain) intercepte tout appel
   a `initier_remboursement` : l'execution du graphe d'agent est SUSPENDUE
   (via `interrupt`) tant qu'une decision humaine explicite n'a pas ete
   transmise. Le modele ne peut pas contourner ca, ce n'est pas une consigne
   de prompt, c'est structurel.
2. Le plafond `C.MONTANT_MAX_AUTO` est verifie une seconde fois, en dur, dans
   l'outil lui-meme (`tools.ContexteOutils.initier_remboursement`) : meme un
   humain qui approuverait par erreur un montant trop eleve ne peut pas faire
   passer le remboursement.

`construire_agent` (A COMPLETER) met en place le premier garde-fou.
`executer_agent4` (fourni) gere la mecanique d'interruption/reprise.
"""
from __future__ import annotations

from .. import config as C
from .commun import construire_modele_llm, executer_avec_reprises, extraire_trace, tracer
from .tools import ContexteOutils, outils_langchain

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver

PROMPT_SYSTEME = f"""Tu es l'agent d'autonomie du support Klaro. Pour une
commande donnee :

1. Verifie TOUJOURS l'eligibilite via verifier_eligibilite_remboursement
   avant toute autre action.
2. Si la commande est eligible ET que le montant est inferieur ou egal a
   {C.MONTANT_MAX_AUTO} EUR, propose le remboursement en appelant
   initier_remboursement.
3. Si la commande n'est pas eligible, ou si le montant depasse
   {C.MONTANT_MAX_AUTO} EUR, n'appelle JAMAIS initier_remboursement :
   explique la raison et indique que le dossier doit etre traite par un
   conseiller (agent 2).

Le declenchement du remboursement reste soumis a une validation humaine
explicite, quoi qu'il arrive : ce n'est jamais toi qui decides seul.
"""


def construire_agent(ctx: ContexteOutils):
    """A COMPLETER.

    Doit retourner un agent `create_agent` construit avec :
    - `model=construire_modele_llm()` (importee de `commun.py`, deja
      rate-limitee : ne construisez pas votre propre modele a la main) ;
    - `tools` : `verifier_eligibilite_remboursement` et
      `initier_remboursement`, pioches dans `outils_langchain(ctx)` ;
    - `system_prompt=PROMPT_SYSTEME` ;
    - `middleware=[HumanInTheLoopMiddleware(interrupt_on={...})]` (import :
      `from langchain.agents.middleware import HumanInTheLoopMiddleware`) :
      la cle `interrupt_on` doit cibler UNIQUEMENT `"initier_remboursement"`
      (jamais `verifier_eligibilite_remboursement`, qui est un outil de
      lecture sans consequence et n'a pas besoin d'etre valide). Exemple de
      valeur : `{"initier_remboursement": {"allowed_decisions": ["approve", "reject"]}}` ;
    - `checkpointer=InMemorySaver()` (import : `from langgraph.checkpoint.memory
      import InMemorySaver`) : sans lui, l'agent ne peut pas suspendre puis
      reprendre son execution entre deux appels a `.invoke(...)`.

    C'est cette fonction, et elle seule, qui rend le remboursement automatise
    impossible sans validation humaine explicite.
    """
    # raise NotImplementedError("A completer : construire_agent (agent 4)")

    outils = outils_langchain(ctx)

    mes_outils = [
        outils["verifier_eligibilite_remboursement"],
        outils["initier_remboursement"],
    ]

    middleware = [
        HumanInTheLoopMiddleware(
            interrupt_on={
                "initier_remboursement": {
                    "allowed_decisions": [
                        "approve",
                        "reject",
                    ]
                }
            }
        )
    ]

    return create_agent(
        model=construire_modele_llm(),
        tools=mes_outils,
        system_prompt=PROMPT_SYSTEME,
        middleware=middleware,
        checkpointer=InMemorySaver(),
    )


def executer_agent4(ctx: ContexteOutils, commande_id: str, decision: dict,
                    tracer_trace: bool = True) -> dict:
    """Point d'entree fourni : lance la conversation, s'arrete si le
    middleware interrompt l'execution, puis la reprend avec la decision
    humaine transmise.

    `decision` a la forme attendue par `HumanInTheLoopMiddleware`, par
    exemple `{"type": "approve"}` ou `{"type": "reject", "message": "..."}`.
    Si le modele ne propose jamais `initier_remboursement` (commande non
    eligible, ou montant au-dessus du plafond bien identifie par le prompt),
    aucune interruption n'a lieu et `decision` n'est pas utilisee.
    """
    from langgraph.types import Command

    agent = construire_agent(ctx)
    thread = {"configurable": {"thread_id": f"agent4-{commande_id}"},
             "recursion_limit": C.AGENT_BUDGET_ACTIONS * 2 + 1}
    question = (f"Le client de la commande {commande_id} demande un remboursement. "
               "Verifie son eligibilite et propose l'action adaptee.")

    resultat = executer_avec_reprises(
        agent.invoke, {"messages": [{"role": "user", "content": question}]}, thread)
    interrompu = "__interrupt__" in resultat

    if interrompu:
        resultat = executer_avec_reprises(agent.invoke, Command(resume={"decisions": [decision]}), thread)

    messages = resultat["messages"]
    diagnostic = {"commande_id": commande_id, "interrompu": interrompu,
                 "decision_transmise": decision if interrompu else None,
                 "reponse": messages[-1].content}
    res = {"diagnostic": diagnostic, "trace": extraire_trace(messages)}
    return tracer("agent4_autonomie", res) if tracer_trace else res
