# Validation — Halloween Weapons V2

État : **export natif et contrôles locaux réussis ; tests GTA V/FiveM non exécutés**.

| Contrôle | Résultat |
|---|---|
| Sources 3D | Cinq modèles Blender et cinq GLB refaits ; poignées/chargeurs galbés, évidements, biseaux, lames courbes |
| Normales / textures | Normales lissées pondérées et tangentes ; 33 cartes indépendantes diffuse/normal/specular, 512 × 512 avec 10 mipmaps réels |
| Export GTA Legacy | 8 YDR version 165, 1 YTD version 13, 1 YCD version 46, tous binaires RSC7 |
| Décodage natif | Tous les fichiers ont été relus dans CodeWalker après export |
| LOD | High, Medium et Low pour les huit modèles ; références de shaders et comptes de triangles vérifiés après décodage |
| Animations originales | Deux clips à 60 images/s, 42 pistes chacun ; 67 images pour la hache, 85 pour la faux |
| Données des animations | Les quaternions de chaque image ont été décodés et vérifiés normalisés ; le rig/actions est modifiable dans Blender |
| Prévisualisations | Cinq rendus inspectés ; mouvements prévisualisés sur un mannequin dans Blender, avec deux GIF livrés |
| Scripts / installateur | **40 tests réussis**, aucun échec ni test ignoré ; Lua 5.4 réel avec mocks FiveM/ox_inventory |
| Client GTA / FXServer | **Non exécuté** |

Le stream fait environ **14.22 Mo**. Les fichiers, tailles et SHA-256 exacts figurent dans `sources/asset_validation.json`. L'export inclut les niveaux de détail et les matériaux utilisés dans le jeu ; il ne se limite pas aux GLB de présentation.

Les 40 tests couvrent l'installation et le passage d'icônes connues V1 vers V2 avec sauvegarde, la conservation des définitions et icônes personnalisées, la réinstallation/désinstallation, les erreurs d'inventaire et la commande admin. Les tests de mêlée vérifient la nécessité d'une arme réellement équipée/possédée, le délai d'impact, le cooldown, la durabilité, les échanges de slot/arme, les cibles distantes ou derrière le joueur, les routing buckets, la déconnexion, les événements locaux forgés et les contrôles de visibilité/propriété du côté client. Le serveur fixe les dégâts et le timing ; il ne reçoit pas un montant de dégâts du joueur.

**Ces tests emploient des mocks des natives et exports et ne remplacent pas l'exécution dans FiveM.** La lecture réelle des clips, l'alignement des mains sur différents peds, la vue FPS, les dégâts sur les entités réseau, l'attribution des morts et la synchronisation à deux joueurs restent à contrôler sur votre serveur. Les GIF sont rendus dans Blender, pas dans GTA.

## Outils

- Blender 4.3.2 ; Python 3.12 ; Pillow 12.3.0 ; NumPy ; Lua 5.4 via lupa 2.8.
- .NET SDK 8.0.425 ; CodeWalker.Core `485d56bec00262ed7fa472261cce7bbc6202b96e`.
- Schéma ox_inventory inspecté à `488aa6d754dfbf7d169f355ccbd647dc60c5ec3a`.
- Données de bind GTA de Sollumz : voir `third_party/README.md` et la licence incluse.

## Limites restantes

La V2 suit la palette et les silhouettes de la référence et ajoute des détails sculptés, mais ne reproduit pas à l'identique tous les ornements de l'illustration. Les cinq rendus livrés permettent de voir les modèles réellement créés. GTA V Enhanced n'est pas vérifié. La gestion de mêlée demande OneSync et utilise des impacts scriptés, avec les conséquences d'intégration décrites dans le guide. Aucun résultat de test en jeu n'est revendiqué.
