"""Tests de la pipeline existante — DOIVENT rester verts après vos ajouts.

C'est un test de **non-régression** : si vous cassez la pipeline initiale
en ajoutant votre nouvelle source, ces tests sautent et vous le saurez tout
de suite.
"""
from __future__ import annotations

from sqlalchemy import select, func

from src.models import Produit, ErpExport

from datetime import datetime

import pytest

from src.pipeline_existante import ingest_erp_export


def test_produits_table_exists(tmp_engine):
    """La table produits existe après création du schéma."""
    with tmp_engine.connect() as connection:
        inspector_tables = list(tmp_engine.dialect.get_table_names(connection))
    assert "produits" in inspector_tables


def test_produits_schema_attendu(tmp_session):
    """Les colonnes attendues de produits sont présentes."""
    # Insertion test
    p = Produit(produit_ref="TEST-01", nom="Test", categorie="aluminium", unite="kg")
    tmp_session.add(p)
    tmp_session.commit()

    # Lecture
    result = tmp_session.execute(select(Produit).where(Produit.produit_ref == "TEST-01")).scalar_one()
    assert result.nom == "Test"
    assert result.categorie == "aluminium"
    assert result.unite == "kg"


def test_erp_export_table_exists(tmp_engine):
    """La table erp_export existe après création du schéma."""
    with tmp_engine.connect() as connection:
        inspector_tables = list(tmp_engine.dialect.get_table_names(connection))
    assert "erp_export" in inspector_tables

def test_erp_export_schema_attendu(tmp_session):
    """Les colonnes attendues de erp_export sont présentes."""
    # Insertion test
    e = ErpExport(
        ordre_id=100000,
        produit_ref="TEST-01",
        site="Arthon-en-Retz",
        line_id=1,
        date_lancement=datetime(2026, 7, 1, 8, 0, 0),
        date_fin_prevue=datetime(2026, 7, 1, 12, 0, 0),
        statut="en_cours",
        ouvrier_id="12345678912345789",
        quantite_kg=1000,
    )
    tmp_session.add(e)
    tmp_session.commit()

    # Lecture
    result = tmp_session.execute(select(ErpExport).where(ErpExport.produit_ref == "TEST-01")).scalar_one()
    assert result.ordre_id == 100000
    assert result.produit_ref == "TEST-01"
    assert result.site == "Arthon-en-Retz"
    assert result.line_id == 1
    assert result.date_lancement == datetime(2026, 7, 1, 8, 0, 0)
    assert result.date_fin_prevue == datetime(2026, 7, 1, 12, 0, 0)
    assert result.statut == "en_cours"
    assert result.ouvrier_id == "12345678912345789"
    assert result.quantite_kg == 1000

def test_ingestion_erp_export_invalide(tmp_session, monkeypatch, tmp_path):
    before = tmp_session.scalar(select(func.count()).select_from(ErpExport))
    
    monkeypatch.setattr("src.pipeline_existante.ERP_EXPORT_JSON", tmp_path / "absent.json")
    monkeypatch.setattr("src.pipeline_existante.get_session", lambda: tmp_session)
    with pytest.raises(FileNotFoundError):
        ingest_erp_export()
        
    after = tmp_session.scalar(select(func.count()).select_from(ErpExport))
    assert after == before