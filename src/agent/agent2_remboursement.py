"""Agent 2 - Remboursement : verifie l'eligibilite, ne decide jamais seul.

Repond aux demandes de remboursement en verifiant l'eligibilite d'une
commande selon la politique (`data/politique_remboursement.md`) et en
citant des precedents similaires dans l'historique des tickets. N'a acces
qu'a 2 outils : `verifier_eligibilite_remboursement` et
`rechercher_historique`.

Contrainte non negociable, identique a celle de l'ancien bot qu'il remplace,
mais tenue cette fois : JAMAIS de remboursement annonce ou execute par cet
agent. Il n'a structurellement pas acces a `initier_remboursement` (l'agent 4,
etudie separement, explore ce que signifierait automatiser une partie de
cette decision sous garde-fous).
"""
from __future__ import annotations

from .commun import construire_modele_llm, executer_conversation, tracer
from .tools import ContexteOutils, outils_langchain
from langchain.agents import create_agent

PROMPT_SYSTEME = """Tu es l'agent remboursement du support Klaro. Tu verifies
si une commande est eligible a un remboursement, a partir de l'outil dedie,
et tu peux citer un precedent similaire dans l'historique des tickets.

Regles imperatives :
- N'affirme AUCUN verdict d'eligibilite qui ne provienne de
  verifier_eligibilite_remboursement.
- Tu informes sur l'eligibilite ; tu ne declenches JAMAIS toi-meme de
  remboursement. La decision et l'execution restent humaines.
- Si la question ne contient pas de numero de commande, demande-le avant
  de conclure quoi que ce soit.
"""


def construire_agent(ctx: ContexteOutils):
    """A COMPLETER.

    Doit retourner un agent `create_agent` construit avec :
    - `model=construire_modele_llm()` (importee de `commun.py`, deja
      rate-limitee : ne construisez pas votre propre modele a la main) ;
    - `tools` : uniquement `verifier_eligibilite_remboursement` et
      `rechercher_historique`, piochés dans `outils_langchain(ctx)` ;
    - `system_prompt=PROMPT_SYSTEME`.

    Aucun outil d'ecriture ici : c'est ce qui garantit structurellement que
    cet agent ne peut jamais executer de remboursement, quel que soit le
    prompt.
    """
    # raise NotImplementedError("A completer : construire_agent (agent 2)")

    outils = outils_langchain(ctx)

    mes_outils = [
        outils["verifier_eligibilite_remboursement"],
        outils["rechercher_historique"],
    ]

    return create_agent(
        model=construire_modele_llm(),
        tools=mes_outils,
        system_prompt=PROMPT_SYSTEME,
    )    


def repondre(ctx: ContexteOutils, question: str, tracer_trace: bool = True) -> dict:
    """Point d'entree. Retourne une reponse + la trace des appels d'outils."""
    agent = construire_agent(ctx)
    sortie = executer_conversation(agent, question)
    res = {"diagnostic": {"question": question, "reponse": sortie["reponse"]},
           "trace": sortie["trace"]}
    return tracer("agent2_remboursement", res) if tracer_trace else res
