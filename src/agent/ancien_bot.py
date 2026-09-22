"""Ancien bot de support Klaro : l'architecture EXISTANTE, avant evolution.

Ce fichier n'est pas a completer. C'est le point de depart de l'etape 1 :
le binome l'execute, observe ses limites, et s'en sert comme preuve dans sa
note d'evaluation d'architecture. Ne vous en inspirez pas pour les 4
nouveaux agents : il illustre ce qu'il ne faut pas faire.

Trois defauts a repérer (la liste n'est pas exhaustive) :
  1. Aucun acces aux donnees reelles (FAQ, commandes, politique) : les
     reponses sont des textes fixes, jamais verifies.
  2. Sur toute mention de retour ou remboursement, il annonce un
     remboursement, sans verifier l'eligibilite ni demander de validation
     humaine. C'est precisement ce que l'article 22 du RGPD interdit pour
     une decision entierement automatisee a effet financier.
  3. Aucune tracabilite : impossible de savoir d'ou vient une reponse.
"""
from __future__ import annotations

_REPONSES = {
    "livraison": "Votre colis arrive sous 3 a 5 jours ouvres.",
    "retard": "Votre colis arrive sous 3 a 5 jours ouvres.",
    "rembours": "Pas de souci, vous serez rembourse sous peu !",
    "retour": "Pas de souci, vous serez rembourse sous peu !",
    "compte": "Essayez de reinitialiser votre mot de passe depuis la page de connexion.",
    "mot de passe": "Essayez de reinitialiser votre mot de passe depuis la page de connexion.",
    "paiement": "Nous acceptons la carte bancaire et PayPal.",
}


def repondre_ancien_bot(question: str) -> str:
    """Reponse canned, sans acces aux donnees, sans tracabilite, sans controle humain."""
    q = question.lower()
    for mot_cle, reponse in _REPONSES.items():
        if mot_cle in q:
            return reponse
    return "Je n'ai pas compris votre demande, un conseiller vous recontactera."
