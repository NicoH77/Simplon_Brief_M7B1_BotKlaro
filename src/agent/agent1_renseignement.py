"""Agent 1 - Renseignement general : FAQ et suivi de commande.

Repond aux questions generales (livraison, compte, produit, paiement) et au
suivi de commande, via un vrai agent LLM (Mistral). N'a acces qu'a 2 outils :
`chercher_faq` et `consulter_commande`. Ne touche jamais au remboursement
(c'est l'agent 2) ni a une action d'ecriture (c'est l'agent 4) : il ne les a
tout simplement pas dans sa liste d'outils, c'est ca qui rend la frontiere
verifiable dans le code plutot que dans le seul prompt.
"""
from __future__ import annotations

from .commun import construire_modele_llm, executer_conversation, tracer
from .tools import ContexteOutils, outils_langchain

PROMPT_SYSTEME = """Tu es l'agent de renseignement general du support Klaro.
Tu reponds aux questions sur la livraison, le compte client, les produits et
le paiement, et tu donnes le statut d'une commande si son numero est fourni.

Regles imperatives :
- N'affirme AUCUN statut ni information qui ne provienne d'un appel d'outil.
- Tu ne traites PAS les demandes de remboursement : si la question en
  contient une, dis que l'agent remboursement de Klaro va la reprendre.
- Tu n'as accès a aucun outil d'ecriture.
"""


def construire_agent(ctx: ContexteOutils):
    """A COMPLETER.

    Doit retourner un agent `create_agent` (import : `from langchain.agents
    import create_agent`) construit avec :
    - `model=construire_modele_llm()` (importee de `commun.py`, deja
      rate-limitee : ne construisez pas votre propre modele a la main) ;
    - `tools` : uniquement `chercher_faq` et `consulter_commande`, piochés
      dans `outils_langchain(ctx)` (qui retourne un dict, voir tools.py) ;
    - `system_prompt=PROMPT_SYSTEME`.

    C'est le choix des 2 outils, et l'absence de tout autre, qui garantit que
    cet agent ne peut structurellement pas déclencher ou promettre un
    remboursement, même si le prompt était mal rédigé ou contourné.
    """
    ## raise NotImplementedError("A completer : construire_agent (agent 1)")

    from langchain.agents import create_agent

    outils = outils_langchain(ctx)

    return create_agent(
        model=construire_modele_llm(),
        tools=[
            outils["chercher_faq"],
            outils["consulter_commande"],
        ],
        system_prompt=PROMPT_SYSTEME,
    )


def repondre(ctx: ContexteOutils, question: str, tracer_trace: bool = True) -> dict:
    """Point d'entree. Retourne une reponse + la trace des appels d'outils."""
    agent = construire_agent(ctx)
    sortie = executer_conversation(agent, question)
    res = {"diagnostic": {"question": question, "reponse": sortie["reponse"]},
           "trace": sortie["trace"]}
    return tracer("agent1_renseignement", res) if tracer_trace else res
