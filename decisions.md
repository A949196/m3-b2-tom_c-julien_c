# Decisions — Binôme `Tom` × `Julien` (M3-B2 Acerox)

## 1. Source choisie pour l'ingestion

**Choix** : `erp_export.json` (JSON ~2k ordres)

**Argument** :
- `produit_ref` dans l'ERP correspond exactement aux références de `produits.csv` (ex : `ALU-T1-22`) : c'est la seule des deux sources qui permet une vraie FK vers le schéma existant.
- L'ERP contient une donnée à caractère personnel (`ouvrier_id`), ce qui nous confronte à un vrai enjeu RGPD.

## 1.1 Format de stockage choisi

**Choix** : SQLite

**Argument** : 
- Une vraie relation entre `produits` (FK sur `produit_ref`)
- Un volume modeste (2000 identifiants)

## 2. Stratégie de gestion des doublons 

**Choix** : dédup pandas avant insertion, sur la clé naturelle `ordre_id` (unique par construction dans l'ERP), puis vérification en base des `ordre_id` déjà présents avant `INSERT` (même logique idempotente que `ingest_produits()` dans `pipeline_existante.py`).
 
**Argument** : `ordre_id` est un identifiant métier unique (contrairement à `sensor_id` + `timestamp` côté IoT, qui n'a pas de clé naturelle aussi nette). Filtrer côté pandas avant d'aller en base évite des allers-retours SQL inutiles sur un volume de ~2k lignes ; on garde la vérification "refs déjà en base" pour garantir l'idempotence même si le script est relancé plusieurs fois (critère de performance 3).

## 3. Stratégie RGPD (si vous prenez ERP)
- ☐ Hash salé (avec quel sel ?)

**Argument** : `ouvrier_id` est haché (SHA-256) avec un sel fixe stocké en variable d'environnement (`ACEROX_HASH_SALT`), plutôt que supprimé purement. On choisit le hash salé plutôt que la suppression pure car `ouvrier_id` peut avoir une valeur analytique pour le modèle de prédiction de défauts en aval, le supprimer ferait perdre un signal potentiellement utile, alors que le hasher le rend non ré-identifiable directement tout en restant un identifiant stable et joignable. Le sel évite les attaques par dictionnaire.

## 4. Stratégie de tests

1. **Migration appliquée → la table existe** : applique les migrations (`alembic upgrade head`) sur une BDD SQLite éphémère, puis vérifie que `erp_export` est présente, avec les colonnes attendues (notamment `ouvrier_id_hash`).

2. **Ingestion d'un fichier valide → N lignes insérées sans doublon** : appelle `ingest_erp()` sur un `erp_export.json` de test contenant des `ordre_id` uniques, vérifie que le nombre de lignes retourné correspond au nombre de lignes du fichier, puis relance `ingest_erp()` une seconde fois et vérifie que 0 ligne est insérée.

3. **Ingestion fichier malformé → exception claire, BDD inchangée** : appelle `ingest_erp()` sur un fichier avec une colonne obligatoire manquante ou un type invalide (ex. `quantite_kg` non numérique), vérifie qu'une `IngestionError` explicite est levée.


## 5. Convention binôme

- Driver / Navigator switch toutes les **30 min** : oui
- Tous les commits significatifs ont `Co-authored-by:` : oui
- Branche perso ou main partagée : main partagée

## 6. Conformité au contrat de données

| Clause du contrat | Honorée ? | Comment / où dans le code |
|---|---|---|
| Unicité respectée (ingestion idempotente) | ☒ | Index unique sur `ordre_id` (migration `0002`) ; filtre `existing_refs` avant insertion dans `ingest_erp()` et `ingest_erp_export()`. Vérifié : relancer le script 2 fois insère 0 ligne au second passage. |
| Manquants traités explicitement | Partielle | `ouvrier_id` absent → `ouvrier_id_hash = NULL` (colonne `nullable=True`, migration `ecd3aa95da63`), implémenté dans `src/ingest_erp.py::_hash_ouvrier_id()`. |
| Capteur défaillant Roubaix L3 : repéré + décision tracée (écarter / marquer / aval) *(option A)* | s.o. | Non applicable — source IoT non retenue pour cette itération (cf. section 1). |
| `ouvrier_id` hashé ou retiré, jamais en clair *(option B)* | ☒ | Hash SHA-256 salé, sel lu depuis `OUVRIER_SALT` (fichier `.env`). Colonne renommée `ouvrier_id_hash` (migration corrective `ecd3aa95da63`) pour que le nom documente lui-même son contenu. |
| Types conformes (DateTime, numériques typés) | ☒ | `models.py` — `date_lancement`/`date_fin_prevue` en `DateTime`, `quantite_kg` en `Float`, `ordre_id`/`line_id` en `Integer`, `produit_ref` en `String(20)` (FK), `ouvrier_id_hash` en `String(64)`. Contraintes reflétées dans les migrations `0002` et `ecd3aa95da63`. |
---

*Décisions tracées par le binôme `Tom` × `Julien` — `01/07/2026`.*
