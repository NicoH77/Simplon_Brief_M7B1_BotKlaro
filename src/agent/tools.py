"""Outils partages par les 4 agents de Klaro (fourni, ne pas modifier).

Cinq outils : quatre en LECTURE SEULE (utilises par les agents 1, 2 et 3),
un en ECRITURE (`initier_remboursement`, reserve a l'agent 4). Chacun
renvoie une structure typee (dict), jamais du texte libre : c'est ce qui
rend verifiable la contrainte "aucune information sans appel d'outil".

Ce fichier est commun au binome : il ne depend d'aucun agent en particulier,
c'est le socle sur lequel les 4 agents s'appuient. Le travail individuel de
chacun porte sur la construction de l'agent LLM (quel sous-ensemble d'outils,
quel prompt, quel garde-fou), pas sur ces outils eux-memes.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from .. import config as C


@dataclass
class ContexteOutils:
    """Etat injecte dans les outils (donnees chargees une fois)."""
    faq: pd.DataFrame
    commandes: pd.DataFrame
    tickets: pd.DataFrame

    # ------------------ Outil 1 : chercher dans la FAQ ------------------
    def chercher_faq(self, mots_cles: str, k: int = 3) -> dict:
        """Recherche les k entrees de FAQ les plus pertinentes pour une requete."""
        requete = str(mots_cles).lower()
        mots = [m for m in requete.split() if len(m) > 2]

        def _score(row) -> int:
            texte = f"{row['question']} {row['reponse']}".lower()
            return sum(texte.count(m) for m in mots)

        scores = self.faq.apply(_score, axis=1)
        top = self.faq.assign(_score=scores)
        top = top[top["_score"] > 0].sort_values("_score", ascending=False).head(k)
        resultats = top[["id", "categorie", "question", "reponse"]].to_dict("records")
        return {"requete": mots_cles, "resultats": resultats, "n_resultats": len(resultats)}

    # ------------------ Outil 2 : consulter une commande ------------------
    def consulter_commande(self, commande_id: str) -> dict:
        """Retourne le statut et les details d'une commande."""
        ligne = self.commandes[self.commandes["commande_id"] == commande_id]
        if ligne.empty:
            return {"trouvee": False, "commande_id": commande_id}
        r = ligne.iloc[0]
        return {
            "trouvee": True,
            "commande_id": commande_id,
            "produit": r["produit"],
            "montant_eur": float(r["montant_eur"]),
            "statut": r["statut"],
            "date_commande": r["date_commande"].date().isoformat(),
            "date_livraison_prevue": r["date_livraison_prevue"].date().isoformat(),
            "date_livraison_reelle": (r["date_livraison_reelle"].date().isoformat()
                                      if pd.notna(r["date_livraison_reelle"]) else None),
        }

    # ------------------ Outil 3 : verifier l'eligibilite au remboursement --
    def verifier_eligibilite_remboursement(self, commande_id: str) -> dict:
        """Applique la politique de remboursement (voir data/politique_remboursement.md)."""
        infos = self.consulter_commande(commande_id)
        if not infos["trouvee"]:
            return {"commande_id": commande_id, "eligible": False,
                    "motif": "commande introuvable"}

        if infos["statut"] == C.STATUT_ANNULE:
            return {"commande_id": commande_id, "eligible": False,
                    "motif": "commande annulee : hors perimetre du retour"}

        if infos["statut"] in C.STATUTS_NON_LIVRES:
            return {"commande_id": commande_id, "eligible": False,
                    "motif": f"commande pas encore livree (statut: {infos['statut']})"}

        date_livraison = pd.Timestamp(infos["date_livraison_reelle"])
        aujourdhui = pd.Timestamp(C.DATE_REFERENCE)
        jours_ecoules = int((aujourdhui - date_livraison).days)

        if jours_ecoules <= C.DELAI_RETOUR_JOURS:
            return {"commande_id": commande_id, "eligible": True,
                    "jours_ecoules": jours_ecoules,
                    "motif": (f"livree il y a {jours_ecoules} jours, dans le delai "
                             f"de {C.DELAI_RETOUR_JOURS} jours"),
                    "montant_max_eur": infos["montant_eur"]}
        return {"commande_id": commande_id, "eligible": False,
                "jours_ecoules": jours_ecoules,
                "motif": (f"livree il y a {jours_ecoules} jours, delai standard de "
                         f"{C.DELAI_RETOUR_JOURS} jours depasse. Un defaut de fabrication "
                         "reste possible hors delai mais doit etre confirme par un conseiller.")}

    # ------------------ Outil 4 : rechercher l'historique ------------------
    def rechercher_historique(self, requete: str, k: int = 3) -> dict:
        """Recherche plein-texte simple dans les tickets deja resolus."""
        req = str(requete).lower()
        mots = [m for m in req.split() if len(m) > 2]

        def _score(row) -> int:
            texte = f"{row['sujet']} {row['resolution']}".lower()
            return sum(texte.count(m) for m in mots)

        scores = self.tickets.apply(_score, axis=1)
        top = self.tickets.assign(_score=scores)
        top = top[top["_score"] > 0].sort_values("_score", ascending=False).head(k)
        resultats = top[["ticket_id", "date", "sujet", "resolution"]].copy()
        resultats["date"] = resultats["date"].dt.date.astype(str)
        return {"requete": requete, "resultats": resultats.to_dict("records"),
                "n_resultats": len(resultats)}

    # ------------------ Outil 5 (ECRITURE) : initier un remboursement ------
    def initier_remboursement(self, commande_id: str, montant_eur: float) -> dict:
        """Declenche (simule) un remboursement. Reserve a l'agent 4.

        Deux garde-fous structurels, independants du modele de langage qui
        appelle cet outil :
        1. Le plafond `C.MONTANT_MAX_AUTO` est verifie ICI, dans le code, pas
           seulement rappele dans un prompt. Un modele peut se tromper ou
           etre mal guide ; ce controle s'applique quoi qu'il arrive.
        2. Cet outil n'est jamais expose sans le middleware human-in-the-loop
           construit dans `agent4_autonomie.construire_agent` : voir ce
           fichier pour le second garde-fou (validation humaine explicite).
        """
        if montant_eur > C.MONTANT_MAX_AUTO:
            return {"commande_id": commande_id, "montant_eur": float(montant_eur),
                    "statut": "refuse",
                    "motif": (f"montant ({montant_eur:.2f} EUR) au-dessus du plafond "
                             f"automatisable ({C.MONTANT_MAX_AUTO:.2f} EUR) : a traiter "
                             "manuellement par un conseiller (agent 2)")}
        return {"commande_id": commande_id, "montant_eur": float(montant_eur),
                "statut": "rembourse", "horodatage": datetime.now().isoformat()}


def outils_langchain(ctx: ContexteOutils) -> dict:
    """Enveloppe les methodes de ContexteOutils en outils LangChain (@tool).

    Retourne un dictionnaire {nom: outil} : chaque agent pioche le sous-ensemble
    dont il a besoin (voir les fichiers agent1_*.py a agent4_*.py). C'est ce
    choix, fait fichier par fichier dans chaque `construire_agent`, qui
    materialise la frontiere de decision dans le code.
    """
    from langchain_core.tools import tool

    @tool
    def chercher_faq(mots_cles: str) -> str:
        """Recherche dans la FAQ produit/livraison/retour/compte/paiement."""
        return str(ctx.chercher_faq(mots_cles))

    @tool
    def consulter_commande(commande_id: str) -> str:
        """Retourne le statut et les details d'une commande a partir de son identifiant."""
        return str(ctx.consulter_commande(commande_id))

    @tool
    def verifier_eligibilite_remboursement(commande_id: str) -> str:
        """Verifie si une commande est eligible a un remboursement standard."""
        return str(ctx.verifier_eligibilite_remboursement(commande_id))

    @tool
    def rechercher_historique(requete: str) -> str:
        """Recherche dans l'historique des tickets de support deja resolus."""
        return str(ctx.rechercher_historique(requete))

    @tool
    def initier_remboursement(commande_id: str, montant_eur: float) -> str:
        """Declenche un remboursement (refuse si le montant depasse le plafond
        automatisable). NE JAMAIS exposer cet outil sans middleware
        human-in-the-loop : voir agent4_autonomie.py."""
        return str(ctx.initier_remboursement(commande_id, montant_eur))

    return {
        "chercher_faq": chercher_faq,
        "consulter_commande": consulter_commande,
        "verifier_eligibilite_remboursement": verifier_eligibilite_remboursement,
        "rechercher_historique": rechercher_historique,
        "initier_remboursement": initier_remboursement,
    }
