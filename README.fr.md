# Pack Halloween — 5 armes FiveM

Pack d'armes **supplémentaires** pour un serveur GTA V **Legacy / FiveM** utilisant ESX et ox_inventory.
Les cinq modèles sont originaux et stylisés, inspirés de la planche de concept. Les images de concept sont des illustrations ; les images individuelles dans `previews/` montrent les modèles réellement livrés.

| Arme | Identifiant dans ox_inventory | Munitions | Chargeur |
|---|---|---|---|
| Braise, pistolet | `WEAPON_HW_EMBER` | `ammo-9` | 12 |
| Revenant, AR | `WEAPON_HW_REVENANT` | `ammo-rifle` | 30 |
| Citrouille, AK | `WEAPON_HW_PUMPKIN` | `ammo-rifle2` | 30 |
| Faucheuse, hache | `WEAPON_HW_REAPER_AXE` | Aucune | — |
| Âme perdue, faux | `WEAPON_HW_SOUL_SCYTHE` | Aucune | — |

## Installation

1. Copier **le dossier `hw_weapons`** dans les ressources du serveur, par exemple `resources/[weapons]/hw_weapons`.
2. Ajouter les définitions et les icônes à votre installation ox_inventory. Depuis le dossier décompressé du pack, exécuter :

   ```sh
   python3 integration/install_ox.py --ox '/chemin/vers/resources/[ox]/ox_inventory'
   ```

   Sous Windows, utiliser `python` à la place de `python3`. L'installateur vérifie les conflits, sauvegarde `data/weapons.lua` dans `ox_inventory/.hw-backups/`, conserve les autres armes et peut être relancé sans dupliquer les entrées. Pour vérifier sans écrire, ajouter `--dry-run`.

   Sans Python : copier les cinq entrées de `integration/ox_weapons_entries.lua` **à l'intérieur de la table `Weapons = { ... }`** de `ox_inventory/data/weapons.lua`, puis copier les cinq PNG de `integration/images/` dans `ox_inventory/web/images/`. Ne pas remplacer tout le fichier, ne pas les mettre dans `data/items.lua` et ne pas créer d'items SQL ESX pour ces armes.

3. Ajouter après votre ligne `ensure ox_inventory` dans `server.cfg` :

   ```cfg
   ensure hw_weapons
   add_ace group.admin command.hw_give allow
   ```

   Le groupe admin ESX ne donne pas automatiquement les permissions ACE. Si nécessaire, rattacher votre identifiant administrateur à votre groupe ACE existant ; un exemple est fourni dans `integration/server.cfg.example`.

4. Redémarrer complètement le serveur et reconnecter les joueurs, pour recharger à la fois les définitions ox_inventory et les métadonnées du client.

Le serveur doit déjà disposer d'une installation ESX + ox_inventory opérationnelle, avec ses dépendances et ses munitions standard. Il n'est pas nécessaire de modifier le code ESX ni le système de loadout : la distribution utilise directement ox_inventory.

## Donner les armes et tester

Depuis la console du serveur, remplacer `12` par l'ID réel du joueur :

```text
hw_give 12 all 60
hw_give 12 WEAPON_HW_REAPER_AXE 0
hw_give 12 WEAPON_HW_EMBER 40
```

Dans le jeu, un administrateur autorisé par ACE peut utiliser `/hw_give`. Les armes sont ajoutées à l'inventaire avec une durabilité de 100 et un chargeur vide ; utiliser les munitions fournies pour recharger. Le maximum de munitions par distribution est configurable et vaut 250 par défaut. Aucun item ne peut être choisi en dehors des cinq identifiants du pack.

Dans la console client F8, exécuter `hw_check`. Le diagnostic vérifie pour chaque arme la définition native, le modèle attendu, son chargement et la taille du chargeur. Il ne donne aucune arme. Les états `PASS` concernent ces vérifications techniques, pas les animations ou les dégâts.

Terminer le test en jeu pour chacune des cinq armes :

- L'icône et le libellé apparaissent dans ox_inventory ; l'équipement et le rangement fonctionnent.
- Les trois armes à feu tirent, éjectent les douilles, jouent les sons, rechargent leur chargeur et consomment les munitions correspondantes.
- La hache et la faux frappent avec les animations GTA de mêlée, sans demander de munitions.
- Vérifier la position dans les mains, la vue à la première personne et les accents lumineux de nuit.
- Avec un deuxième joueur, vérifier les modèles et les actions vus à distance.
- Quitter puis revenir pour vérifier la persistance de l'inventaire, du numéro de série et de la durabilité.

## Contenu

L'archive `install` contient la ressource, l'intégration, les aperçus et les guides. L'archive `complete` contient aussi toutes les sources et tous les outils ci-dessous.

- `hw_weapons/` : ressource avec manifeste, scripts, quatre fichiers `.meta`, huit `.ydr` binaires et une texture `.ytd` binaire. Les `.ydr` ne sont pas des fichiers XML renommés.
- `integration/` : entrées ox_inventory, installateur réversible, cinq icônes PNG transparentes de 256 × 256 et exemple de configuration serveur.
- `sources/blend/` : cinq fichiers Blender modifiables, avec armatures et texture embarquée.
- `sources/glb/` : cinq modèles GLB, incluant leurs chargeurs pour les aperçus et les échanges avec d'autres outils.
- `sources/cwxml/` : sources des modèles natifs et de la texture au format XML CodeWalker.
- `sources/textures/` : atlas original PNG et DDS BC3/DXT5 de 1024 × 512 avec onze niveaux de mipmap.
- `previews/` : rendus des véritables modèles et planche de concept.
- `tools/`, `tests/` : génération, export natif, validation et tests reproductibles.

Les chargeurs sont des composants par défaut séparés. La culasse et la détente utilisent les tags de squelette GTA. Les sons, animations et effets de tir utilisent les ressources intégrées au jeu : aucune banque audio supplémentaire n'est requise. La hache utilise les animations de mêlée à une main, et la faux les animations GTA à deux mains. Il n'y a pas d'animation spécialement capturée pour la faux ni de pouvoir magique scripté. Les accents orange/violet utilisent un shader émissif.

## Vérifications réalisées et limites

Les huit drawables et le dictionnaire de texture ont été compilés et décodés de nouveau avec CodeWalker. Les références entre modèles, chargeurs, textures, définitions, libellés et icônes ont été contrôlées. Les scripts ont été exécutés dans Lua 5.4 avec des mocks des natives FiveM/ox_inventory. Les tests de l'installateur couvrent notamment l'installation répétée, les conflits, la conservation du contenu, la sauvegarde et la désinstallation.

**Le client GTA V/FiveM et votre serveur ne sont pas disponibles dans l'environnement de création. Le fonctionnement en jeu, la synchronisation réseau, les animations et la prise en main ne sont donc pas encore validés.** Le pack est fourni pour installation et essai ; utiliser la liste de tests ci-dessus avant une mise en service. Le rapport détaillé se trouve dans `VALIDATION.fr.md`.

Les modèles de cette première version sont stylisés et plus simples que l'illustration de concept. Ils ne reproduisent pas tous les détails gravés de l'image générée. La prise en charge de GTA V Enhanced n'a pas été vérifiée.

## Modifier et reconstruire

Les fichiers natifs sont déjà inclus : il n'est pas nécessaire de compiler pour installer le pack.

Pour reconstruire les sources : Blender 4.3.2 ou compatible, Python avec Pillow 12.3.0, .NET SDK 8 et CodeWalker.Core sont nécessaires. Commandes depuis la racine du pack :

```sh
python3 tools/build_texture.py
blender -b --threads 4 --python tools/build_models.py
git clone https://github.com/dexyfex/CodeWalker.git /chemin/CodeWalker
git -C /chemin/CodeWalker checkout 485d56bec00262ed7fa472261cce7bbc6202b96e
dotnet build tools/NativeExporter/NativeExporter.csproj -c Release -p:CodeWalkerProject=/chemin/CodeWalker/CodeWalker.Core/CodeWalker.Core.csproj
dotnet tools/NativeExporter/bin/Release/net8.0/NativeExporter.dll sources/cwxml hw_weapons/stream
python3 tools/validate_pack.py --roundtrip sources/native_validation
```

L'export vise les ressources GTA Legacy : YDR version 165, YTD version 13. Le générateur utilise les objets déjà dans ce dépôt ; il n'a pas besoin d'assets tiers ni de Meshy. Le build CodeWalker a été vérifié avec le commit noté dans `VALIDATION.fr.md`. Conserver les fichiers `.meta` livrés pour les mêmes noms de modèles ; les dégâts et cadences se règlent dans `hw_weapons/data/weapons.meta`.

Pour exécuter les tests de scripts et d'installation :

```sh
python3 -m pip install lupa==2.8
python3 -m unittest discover -s tests -v
```

Pour retirer le pack de l'inventaire sans effacer les autres définitions :

```sh
python3 integration/install_ox.py --ox '/chemin/vers/ox_inventory' --uninstall
```

Retirer aussi `ensure hw_weapons`, puis redémarrer. Retirer au préalable les exemplaires de ces cinq armes des inventaires persistants pour ne pas conserver des items dont la définition a été supprimée.
