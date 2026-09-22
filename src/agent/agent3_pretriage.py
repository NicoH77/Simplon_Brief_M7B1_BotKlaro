"""Agent 3 - Pre-triage des messages clients entrants.

Pour chaque message en texte libre, l'agent propose une categorie, un niveau
de confiance et une justification citant le message, en interrogeant un vrai
modele de langage (Mistral). Le conseiller valide, corrige ou rejette ;
SEULE la version validee entre dans la file de traitement.

On mesure ensuite deux taux :
  - taux d'accord agent / decision retenue ;
  - part de propositions validees SANS modification (indicateur de biais
    d'automatisation : un taux tres eleve suggere que le validateur ne
    valide plus).

Chaque message classe coute un appel API : voir `C.LIMITE_MESSAGES_PRETRIAGE`
dans config.py pour limiter le nombre de messages traites pendant le
developpement.
"""
from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd

from .. import config as C
from .commun import construire_modele_llm, executer_avec_reprises


def classifier_message(texte: str) -> dict:
    """A COMPLETER.

    Doit interroger `construire_modele_llm()` (importee de `commun.py`, deja
    rate-limitee : ne construisez pas votre propre modele a la main, et
    n'appelez cette fonction qu'une fois par appel, pas en boucle) pour
    classer `texte` parmi `C.TAXONOMIE`, et retourner un dict avec au moins
    "categorie", "confiance" (0-1) et "justification".

    Demandez au modele une reponse en JSON strict (par exemple :
    `{"categorie": "...", "confiance": 0.0, "justification": "..."}`), passez
    le texte brut de sa reponse (`modele.invoke(prompt).content`) a la
    fonction `_parser_reponse_json` fournie plus bas, qui gere le parsing et
    les cas de reponse mal formee.
    """
    # raise NotImplementedError("A completer : classifier_message (agent 3)")

    modele = construire_modele_llm()

    prompt = f"""
        Tu es un agent de pré-triage du support client Klaro.
        Tu dois classer le message dans UNE SEULE catégorie parmi :
        - livraison
        - retour_remboursement
        - compte
        - produit
        - paiement
        - autre
        Réponds UNIQUEMENT avec un JSON valide.
        
        Exemple :
        {{
            "categorie": "livraison",
            "confiance": 0.87,
            "justification": "Le client demande des informations sur la livraison."
        }}
        Message client :
        {texte}
        """

    reponse = modele.invoke(prompt).content

    return _parser_reponse_json(reponse)


def _parser_reponse_json(brut: str) -> dict:
    """Extrait un objet JSON de la reponse du modele, meme entoure de texte ou
    de balises markdown. Se replie sur 'autre' si le parsing echoue : un LLM
    peut mal formater sa reponse, ca ne doit jamais faire planter tout le
    pre-triage pour un seul message."""
    match = re.search(r"\{.*\}", str(brut), re.DOTALL)
    if not match:
        return {"categorie": "autre", "confiance": 0.0, "justification": "reponse non interpretable"}
    try:
        donnees = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"categorie": "autre", "confiance": 0.0, "justification": "reponse non interpretable"}

    categorie = donnees.get("categorie") if donnees.get("categorie") in C.TAXONOMIE else "autre"
    try:
        confiance = float(donnees.get("confiance", 0.0))
    except (TypeError, ValueError):
        confiance = 0.0
    return {"categorie": categorie, "confiance": round(max(0.0, min(1.0, confiance)), 2),
            "justification": str(donnees.get("justification", ""))}


def pretrier(messages: pd.DataFrame) -> pd.DataFrame:
    """Propose une categorie par message (colonne _categorie_vraie = verite).

    Respecte C.LIMITE_MESSAGES_PRETRIAGE : ne traite que les N premiers
    messages si elle est definie, pour economiser des appels API pendant le
    developpement. Chaque appel passe par `executer_avec_reprises` : un 429
    isole ralentit le pre-triage, il ne le fait pas planter.
    """
    sous_ensemble = messages if C.LIMITE_MESSAGES_PRETRIAGE is None \
        else messages.head(C.LIMITE_MESSAGES_PRETRIAGE)
    propositions = [executer_avec_reprises(classifier_message, t) for t in sous_ensemble["texte"]]
    out = sous_ensemble.copy()
    out["cat_proposee"] = [p["categorie"] for p in propositions]
    out["confiance"] = [p["confiance"] for p in propositions]
    out["justification"] = [p["justification"] for p in propositions]
    return out


def simuler_validation(pretri: pd.DataFrame,
                       seuil_confiance: float = 0.5,
                       rng_seed: int = C.SEED) -> pd.DataFrame:
    """Simule la validation humaine.

    Modele de validateur : quand la confiance de l'agent est haute, le
    conseiller a tendance a valider sans regarder (biais d'automatisation).
    Quand elle est basse, il corrige plus souvent vers la vraie categorie.
    """
    rng = np.random.default_rng(rng_seed)
    decisions, sans_modif = [], []
    for _, r in pretri.iterrows():
        vrai = r["_categorie_vraie"]
        prop = r["cat_proposee"]
        conf = r["confiance"]
        p_valider_tel_quel = 0.55 + 0.4 * conf
        if rng.random() < p_valider_tel_quel:
            decision = prop
            modif = False
        else:
            decision = vrai  # le conseiller corrige vers la verite
            modif = (decision != prop)
        decisions.append(decision)
        sans_modif.append(not modif)
    out = pretri.copy()
    out["decision_retenue"] = decisions
    out["valide_sans_modif"] = sans_modif
    return out


def taux(valide: pd.DataFrame) -> dict:
    """Taux d'accord et part validee sans modification."""
    accord = float((valide["cat_proposee"] == valide["decision_retenue"]).mean())
    sans_modif = float(valide["valide_sans_modif"].mean())
    amb = valide[valide["_ambigu"] == 1]
    accord_ambigu = float((amb["cat_proposee"] == amb["decision_retenue"]).mean()) \
        if len(amb) else float("nan")
    return {
        "taux_accord_global": round(accord, 3),
        "taux_accord_ambigus": round(accord_ambigu, 3),
        "part_validee_sans_modification": round(sans_modif, 3),
        "alerte_biais_automatisation": bool(sans_modif > 0.8),
    }
