# Rapport de validation

État : **fichiers créés et vérifications locales réussies ; test en jeu non réalisé**.

## Résultats

| Contrôle | Résultat |
|---|---|
| Modèles originaux | 5 sources Blender et 5 GLB générés |
| Conversion au format GTA natif | 8 `.ydr` RSC7 version 165, 1 `.ytd` RSC7 version 13 |
| Décodage après export | Les 8 modèles ont été relus avec CodeWalker ; géométries, nombre de triangles, shaders, poids et indices de squelette vérifiés |
| Texture | Atlas original BC3/DXT5 de 1024 × 512, 11 mipmaps réels ; dictionnaire natif décodé |
| Références entre fichiers | 5 identifiants d'armes, 3 chargeurs, 8 archetypes, texture partagée, libellés et icônes cohérents |
| Rendus | Les cinq rendus des véritables modèles ont été inspectés ; UV et cadrage corrigés |
| Icônes | 5 PNG RGBA de 256 × 256 |
| Tests Lua 5.4 et installateur Python | **22 réussis**, 0 échec, 0 ignoré |
| Table réelle ox_inventory | Installation sur une copie de la table actuelle : 108 armes existantes conservées, 5 ajoutées ; munitions présentes ; réinstallation et désinstallation vérifiées |
| GTA V / client FiveM | **Non exécuté** |
| Votre serveur ESX / réseau / persistance réelle | **Non exécuté** |

Le test de la table ox_inventory lit les données dans Lua 5.4 en interprétant les littéraux de hash FiveM dans le banc d'essai. Il ne lance pas ox_inventory dans FXServer. Les tests de distribution utilisent des mocks des exports et des natives ; ils vérifient les branches de validation et les erreurs, mais ne prouvent pas les permissions ou la persistance sur votre serveur.

Les tests couvrent la restriction ACE du manifeste de commande, la distribution des cinq armes, l'absence d'ammo pour la mêlée, les entrées manquantes, l'inventaire plein, les échecs d'ajout, les quantités invalides et le diagnostic client. L'installateur a été testé pour les sauvegardes, les conflits, les installations répétées, la conservation des changements sans rapport, la désinstallation et les encodages UTF-8 BOM/CRLF.

## Outils effectivement utilisés

- Blender **4.3.2**, génération locale des géométries et rendus Cycles.
- Python **3.12**, Pillow **12.3.0**, Lua **5.4** via lupa **2.8**.
- .NET SDK **8.0.425**.
- CodeWalker.Core, commit `485d56bec00262ed7fa472261cce7bbc6202b96e` du dépôt `dexyfex/CodeWalker`.
- Table ox_inventory inspectée au commit `488aa6d754dfbf7d169f355ccbd647dc60c5ec3a` du dépôt `overextended/ox_inventory`.

Le stream contient environ **1,87 Mo** de fichiers binaires non archivés. Les tailles et sommes SHA-256 exactes sont dans `sources/asset_validation.json`.

## Tests restant sur FiveM

Suivre la procédure du guide : installer la ressource et les entrées ox_inventory, redémarrer le serveur, lancer `hw_check`, puis tester équipement, visée FPS, tir, rechargement, frappe, synchronisation à deux joueurs et reconnexion.

La calibration dans les mains et les animations natives nécessitent un contrôle visuel en jeu. Les modèles utilisent des tags de squelette GTA et des clipsets stock ; cela ne remplace pas un test client. La version livrée est stylisée et n'a pas tous les détails de l'illustration de concept. GTA V Enhanced n'a pas été testé.
