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

> Quels 3 tests minimum allez-vous écrire ?

1. Migration appliquée → la table existe : ...
2. Ingestion d'un fichier valide → N lignes insérées sans doublon : ...
3. Ingestion fichier malformé → exception claire, BDD inchangée : ...

## 5. Convention binôme

- Driver / Navigator switch toutes les **30 min** : oui
- Tous les commits significatifs ont `Co-authored-by:` : 
- Branche perso ou main partagée : main partagée

## 6. Conformité au contrat de données

> Confrontez votre livraison à `ressources/contrat_donnees_modele.md`. Pour
> chaque clause de qualité **honorée** : laquelle, comment, et **où** dans le
> code. (Documenté ici — c'est ce que vous montrez au RDV vendredi.)

| Clause du contrat | Honorée ? | Comment / où dans le code |
|---|---|---|
| Unicité respectée (ingestion idempotente) | ☐ | ... |
| Manquants traités explicitement | ☐ | ... |
| Capteur défaillant Roubaix L3 : repéré + décision tracée (écarter / marquer / aval) *(option A)* | ☐ / s.o. | ... |
| `ouvrier_id` hashé ou retiré, jamais en clair *(option B)* | ☐ / s.o. | ... |
| Types conformes (DateTime, numériques typés) | ☐ | ... |

---

*Décisions tracées par le binôme `Tom` × `Julien` — `01/07/2026`.*
