"""Pipeline Acerox existante — référentiel produits.

Le binôme **ne doit pas modifier** ce fichier. Il sert de référence :
la pipeline doit continuer de fonctionner après vos ajouts.

Usage::

    python -m src.pipeline_existante
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


from src.db import engine, get_session
from src.models import Base, Produit, ErpExport

import hashlib
import os

PRODUITS_CSV: Path = Path(__file__).parent.parent / "data" / "produits.csv"
ERP_EXPORT_JSON: Path = Path(__file__).parent.parent / "data" / "erp_export.json"

SALT = os.environ.get("OUVRIER_SALT")

def init_db() -> None:
    """Crée toutes les tables déclarées dans `models.Base.metadata`.

    En prod, c'est Alembic qui gère ça. Ici, init brutal pour bootstrap.
    """
    Base.metadata.create_all(engine)


def ingest_produits() -> int:
    """Charge le référentiel produits depuis le CSV vers la table `produits`.

    Idempotent : si un `produit_ref` existe déjà, il n'est pas réinséré.
    Retourne le nombre de produits effectivement insérés.
    """
    df = pd.read_csv(PRODUITS_CSV)
    session = get_session()
    inserted = 0
    try:
        existing_refs = {p.produit_ref for p in session.query(Produit.produit_ref).all()}
        for _, row in df.iterrows():
            if row["produit_ref"] in existing_refs:
                continue
            session.add(
                Produit(
                    produit_ref=row["produit_ref"],
                    nom=row["nom"],
                    categorie=row["categorie"],
                    unite=row["unite"],
                )
            )
            inserted += 1
        session.commit()
    finally:
        session.close()
    return inserted


def ingest_erp_export() -> int:
    """Charge le référentiel produits depuis le CSV vers la table `erp_export`.

    Idempotent : si un `ordre_id` existe déjà, il n'est pas réinséré.
    Retourne le nombre d'exports ERP effectivement insérés.
    """
    df = pd.read_json(ERP_EXPORT_JSON)

    # Normalisation des dates 
    df["date_lancement"] = pd.to_datetime(df["date_lancement"])
    df["date_fin_prevue"] = pd.to_datetime(df["date_fin_prevue"])

    session = get_session()
    inserted = 0
    try:
        existing_refs = {p.ordre_id for p in session.query(ErpExport.ordre_id).all()}
        for _, row in df.iterrows():
            if row["ordre_id"] in existing_refs:
                continue
            session.add(
                ErpExport(
                    ordre_id=row["ordre_id"],
                    produit_ref=row["produit_ref"],
                    site=row["site"],
                    line_id=row["line_id"],
                    date_lancement=row["date_lancement"],
                    date_fin_prevue=row["date_fin_prevue"],
                    statut=row["statut"],
                    ouvrier_id=hash_ouvrier_id(row["ouvrier_id"]),
                    quantite_kg=row["quantite_kg"],
                )
            )
            inserted += 1
        session.commit()
    finally:
        session.close()
    return inserted

# Hashage salé de l'identifiant ouvrier pour anonymisation
def hash_ouvrier_id(ouvrier_id: str) -> str:
    if pd.isna(ouvrier_id):
        ouvrier_id = "unknown"
    salted = (SALT + str(ouvrier_id)).encode()
    return hashlib.sha256(salted).hexdigest()

def main() -> None:
    """Init BDD + chargement référentiel produits."""
    init_db()
    n = ingest_produits()
    print(f"Pipeline existante : {n} produit(s) inséré(s) (idempotent — relancer ne duplique pas).")
    e = ingest_erp_export()
    print(f"Pipeline existante : {e} erp_export(s) inséré(s) (idempotent — relancer ne duplique pas).")


if __name__ == "__main__":
    main()
