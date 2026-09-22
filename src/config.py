"""Configuration centralisee du kit Module 7 bis - Klaro.

Toutes les valeurs pilotant les donnees, la politique de remboursement et
les 4 agents sont ici. Ne pas coder de valeur en dur ailleurs dans le projet.

Les 4 agents s'appuient tous sur un vrai modele de langage (Mistral) : il n'y
a pas de mode hors ligne. `load_dotenv()` charge `MISTRAL_API_KEY` depuis un
fichier `.env` local (voir `.env.example`) avant que quoi que ce soit
n'essaie de construire un modele.
"""
from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------------------------------
# Reproductibilite (utilisee uniquement par la simulation de validation
# humaine de l'etape 3 ; les donnees elles-memes sont statiques, pas generees)
# --------------------------------------------------------------------------
SEED = 42

# --------------------------------------------------------------------------
# Chemins
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FICHIER_FAQ = DATA / "faq.json"
FICHIER_COMMANDES = DATA / "commandes.csv"
FICHIER_POLITIQUE = DATA / "politique_remboursement.md"
FICHIER_TICKETS = DATA / "tickets_historique.csv"
FICHIER_MESSAGES = DATA / "messages_entrants.csv"

OUTPUTS = ROOT / "outputs"
DIR_TRACES = OUTPUTS / "traces_agent"

for _d in (OUTPUTS, DIR_TRACES):
    _d.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Point de reference temporel du scenario (donnees statiques, pas d'horloge
# systeme : tout est calcule par rapport a cette date fictive).
# --------------------------------------------------------------------------
DATE_REFERENCE = "2026-03-15"

# --------------------------------------------------------------------------
# Politique de remboursement (voir data/politique_remboursement.md)
# --------------------------------------------------------------------------
DELAI_RETOUR_JOURS = 14
STATUTS_NON_LIVRES = ["en_preparation", "expediee", "retard"]
STATUT_ANNULE = "annulee"

# --------------------------------------------------------------------------
# Pre-triage des messages entrants (agent 3)
# --------------------------------------------------------------------------
TAXONOMIE = ["livraison", "retour_remboursement", "compte", "produit", "paiement", "autre"]

# Nombre de messages a classer par l'agent 3 : chaque message coute un appel
# API. Mettez un petit nombre pendant le developpement (8 par exemple) pour
# economiser des appels, puis repassez a None (tous les messages, 50) pour le
# run final du livrable.
LIMITE_MESSAGES_PRETRIAGE: int | None = 8

# --------------------------------------------------------------------------
# Agents
# --------------------------------------------------------------------------
MODELE_MISTRAL = "mistralai:ministral-14b-2512"
MISTRAL_REQUETES_PAR_SECONDE = 0.3   # debit maximal vers l'API (palier gratuit : baissez encore si 429)
MISTRAL_TENTATIVES_MAX = 5           # nouvelles tentatives sur une erreur 429, avant d'abandonner
MISTRAL_ATTENTE_INITIALE_RETRY = 5.0 # secondes avant la 1ere reprise (double a chaque nouvel echec)
AGENT_BUDGET_ACTIONS = 5        # agent 4 : limite d'aller-retours modele/outils par conversation
MONTANT_MAX_AUTO = 60.0         # agent 4 : plafond de remboursement automatisable, verrouille dans tools.py
