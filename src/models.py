"""Modèles SQLAlchemy — schéma BDD Acerox.

Schéma initial : 1 table `produits` (référentiel produits, déjà
peuplé depuis `data/produits.csv` par `pipeline_existante.py`).

TODO binôme : ajouter ICI le modèle de votre nouvelle table
(`MesuresIoT` ou `OrdresErp` selon votre choix).
"""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Produit(Base):
    """Référentiel produits Acerox (table existante, ne pas modifier)."""

    __tablename__ = "produits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    produit_ref = Column(String(20), unique=True, nullable=False, index=True)
    nom = Column(String(100), nullable=False)
    categorie = Column(String(20), nullable=False)  # "aluminium" / "inox"
    unite = Column(String(10), nullable=False, default="kg")

    def __repr__(self) -> str:
        return f"Produit(ref={self.produit_ref!r}, nom={self.nom!r})"


# ----------------------------------------------------------------------------
# TODO BINÔME — Ajoutez votre nouvelle table ici
# ----------------------------------------------------------------------------
#
# ⚠️ Votre table utilisera des types non encore importés en haut de ce
#    fichier (DateTime, Float, ForeignKey, UniqueConstraint…). Ajoutez aux
#    imports sqlalchemy ce dont vous avez besoin, sinon → NameError.
#
#  Ajoutez ici le modèle correspondant au contrat de données.
#
#  Consultez :
#
#  ressources/contrat_donnees_modele.md
#
#  Vérifiez notamment :
#
#  - types
#  - contraintes
#  - index
#  - clés étrangères
#  - contraintes d'unicité
#
class ErpExport(Base):
    """Export des données ERP Acerox"""

    __tablename__ = "erp_export"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ordre_id = Column(Integer, unique=True, nullable=False, index=True)
    produit_ref = Column(String(20), ForeignKey("produits.produit_ref"), nullable=False)
    site = Column(String(50), nullable=False)
    line_id = Column(Integer, nullable=False)
    date_lancement = Column(DateTime, nullable=False)
    date_fin_prevue = Column(DateTime, nullable=False)
    statut = Column(String(20), nullable=False)  # "suspendu", "termine", "en_cours"
    ouvrier_id = Column(String(20), nullable=False)
    quantite_kg = Column(Float, nullable=False)

    def __repr__(self) -> str:
        return f"ErpExport(ordre_id={self.ordre_id!r}, produit_ref={self.produit_ref!r}, statut={self.statut!r})"