"""Chargement des donnees statiques du kit (fourni, ne pas modifier).

Toutes les donnees sont des fichiers fixes versionnes dans data/ : il n'y a
pas de generateur a lancer, contrairement aux Modules 6 et 7.
"""
from __future__ import annotations

import json

import pandas as pd

from . import config as C


def charger_faq() -> pd.DataFrame:
    with open(C.FICHIER_FAQ, encoding="utf-8") as f:
        return pd.DataFrame(json.load(f))


def charger_commandes() -> pd.DataFrame:
    df = pd.read_csv(C.FICHIER_COMMANDES)
    for col in ("date_commande", "date_livraison_prevue", "date_livraison_reelle"):
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def charger_tickets() -> pd.DataFrame:
    df = pd.read_csv(C.FICHIER_TICKETS)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def charger_messages() -> pd.DataFrame:
    df = pd.read_csv(C.FICHIER_MESSAGES)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def charger_politique() -> str:
    return C.FICHIER_POLITIQUE.read_text(encoding="utf-8")
