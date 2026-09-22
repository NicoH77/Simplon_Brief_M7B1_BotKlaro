"""Orchestration de bout en bout du corrige Module 7 bis - Klaro.

Rejoue l'echec de l'ancienne architecture, puis enchaine les 4 agents (tous
bases sur un vrai modele Mistral) et ecrit les livrables dans outputs/.
Aucune generation de donnees requise : tout est statique dans data/.

Necessite une cle MISTRAL_API_KEY valide (voir .env.example) : chaque
question posee a un agent est un appel API reel. Le nombre de messages
classes par l'agent 3 est borne par C.LIMITE_MESSAGES_PRETRIAGE
(config.py) pour ne pas consommer inutilement de credits pendant le
developpement.

    python scripts/run_all.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config as C          # noqa: E402
from src import data as D            # noqa: E402
from src.agent.ancien_bot import repondre_ancien_bot        # noqa: E402
from src.agent.tools import ContexteOutils                   # noqa: E402
from src.agent import agent1_renseignement as A1              # noqa: E402
from src.agent import agent2_remboursement as A2               # noqa: E402
from src.agent import agent3_pretriage as A3                    # noqa: E402
from src.agent import agent4_autonomie as A4                     # noqa: E402


def section(titre: str) -> None:
    print("\n" + "=" * 72)
    print(titre)
    print("=" * 72)


def afficher_trace(trace: list[dict]) -> None:
    for entree in trace:
        appels = entree.get("tool_calls")
        if appels:
            for a in appels:
                print(f"    -> appel outil : {a['name']}({a['args']})")
        elif entree.get("tool_name"):
            print(f"    <- resultat {entree['tool_name']} : {str(entree['content'])[:140]}")


def main() -> None:
    section("Chargement des donnees")
    faq = D.charger_faq()
    commandes = D.charger_commandes()
    tickets = D.charger_tickets()
    messages = D.charger_messages()
    print(f"faq={len(faq)}  commandes={len(commandes)}  "
          f"tickets={len(tickets)}  messages={len(messages)}")

    # ---------------------------------------------------------------
    section("Etape 1 : l'ancienne architecture, telle quelle (a evaluer)")
    for q in ["Ou en est ma commande CMD-1013 ?",
             "Je veux etre rembourse pour la commande CMD-1007"]:
        print(f"Q: {q}")
        print(f"R (ancien bot): {repondre_ancien_bot(q)}\n")
    print("-> Aucune donnee reelle consultee, remboursement annonce sans verification, "
         "aucune trace. C'est cette architecture que le binome remplace.")

    ctx = ContexteOutils(faq=faq, commandes=commandes, tickets=tickets)

    # ---------------------------------------------------------------
    section("Etape 2 : Agent 1 - Renseignement general (LLM Mistral)")
    for q in ["Ou en est ma commande CMD-1013 ?",
             "Quel est le delai de livraison standard ?"]:
        res = A1.repondre(ctx, q)
        d = res["diagnostic"]
        print(f"Q: {q}\nR: {d['reponse']}")
        afficher_trace(res["trace"])
        print()

    section("Etape 2 : Agent 2 - Remboursement (LLM Mistral)")
    for q in ["Je veux etre rembourse pour la commande CMD-1004",
             "Je veux etre rembourse pour la commande CMD-1007"]:
        res = A2.repondre(ctx, q)
        d = res["diagnostic"]
        print(f"Q: {q}\nR: {d['reponse']}")
        afficher_trace(res["trace"])
        print()

    print("Rappel frontiere : ni agent 1 ni agent 2 ne recoivent l'outil "
         "d'ecriture initier_remboursement (voir leur construire_agent).")

    # ---------------------------------------------------------------
    section("Etape 2 : Agent 3 - Pre-triage des messages entrants (LLM Mistral)")
    limite = C.LIMITE_MESSAGES_PRETRIAGE
    print(f"(LIMITE_MESSAGES_PRETRIAGE={limite} -> "
         f"{'tous les messages' if limite is None else f'{limite} premiers messages'})")
    pretri = A3.pretrier(messages)
    valide = A3.simuler_validation(pretri)
    t = A3.taux(valide)
    for k, v in t.items():
        print(f"  {k}: {v}")
    valide.to_csv(C.OUTPUTS / "messages_pretries.csv", index=False)

    # ---------------------------------------------------------------
    section("Etape 2 : Agent 4 - Autonomie sous contrainte (LLM Mistral + HITL)")
    print("Cas 1 : eligible, sous le plafond, APPROUVE par un humain")
    r1 = A4.executer_agent4(ctx, "CMD-1004", {"type": "approve"})
    print(" ", r1["diagnostic"]["reponse"])

    print("\nCas 2 : eligible, sous le plafond, REJETE par un humain")
    r2 = A4.executer_agent4(ctx, "CMD-1035", {"type": "reject", "message": "non valide par le conseiller"})
    print(" ", r2["diagnostic"]["reponse"])

    print("\nCas 3 : eligible mais montant au-dessus du plafond automatisable")
    r3 = A4.executer_agent4(ctx, "CMD-1009", {"type": "approve"})
    print(" ", r3["diagnostic"]["reponse"])

    # ---------------------------------------------------------------
    section("Termine")
    print("Livrables dans outputs/ (traces_agent/, messages_pretries.csv).")


if __name__ == "__main__":
    main()
