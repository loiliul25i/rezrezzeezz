# Halloween Weapons — V2

Cinq armes supplémentaires pour **FiveM GTA V Legacy, ESX + ox_inventory et OneSync**. La V2 refait les modèles, les matériaux et la gestion des frappes de mêlée. Les identifiants restent compatibles avec les armes déjà possédées dans ox_inventory.

| Arme | Identifiant | Munitions | Chargeur |
|---|---|---|---|
| Braise, pistolet | `WEAPON_HW_EMBER` | `ammo-9` | 12 |
| Revenant, AR | `WEAPON_HW_REVENANT` | `ammo-rifle` | 30 |
| Citrouille, AK | `WEAPON_HW_PUMPKIN` | `ammo-rifle2` | 30 |
| Faucheuse, hache | `WEAPON_HW_REAPER_AXE` | Aucune | — |
| Âme perdue, faux | `WEAPON_HW_SOUL_SCYTHE` | Aucune | — |

## Ce qui change en V2

- Poignées et chargeurs galbés, surfaces lissées, normales pondérées, tangentes exportées ; tubes et bouches de canon ouverts, évidements de garde-main, biseaux et lames à profils courbes.
- Crânes avec cavités, filigranes en relief, chaînes, pendentifs et bandes de cuir/tissu en hélice.
- Métal sombre, orange pour pistolet/AK/hache, violet pour AR/faux, poignée ivoire et bois orange, suivant la référence.
- **Suppression de l'ancien atlas de couleurs** : 33 cartes séparées de diffuse, relief et reflet, toutes avec dix mipmaps. Shaders GTA `normal_spec.sps` et `emissive.sps`.
- Trois niveaux de détail High/Medium/Low pour chaque arme et chaque chargeur.
- **Deux animations originales dans `hw_melee_v2.ycd`** : `axe_chop` (frappe de hache, 1,10 s), `scythe_sweep` (balayage de faux à deux mains, 1,40 s). Chacune anime 42 pistes de squelette à 60 images/s.
- Gestion dédiée de la mêlée : la frappe native est bloquée pendant l'équipement de ces deux armes ; la ressource joue son propre clip, plutôt qu'une attaque de couteau. Les dégâts et la durabilité sont gérés avec ox_inventory et OneSync.

Les nouveaux PNG de `previews/` montrent les vrais modèles. Les GIF `axe_chop.gif` et `scythe_sweep.gif` montrent les animations sur un mannequin dans Blender. **Ce ne sont pas des captures de FiveM.** L'illustration initiale reste une référence artistique : les gravures et certains détails ne sont pas reproduits à l'identique.

## Installation et mise à jour depuis V1

1. Arrêter le serveur. Conserver vos éventuels réglages personnalisés de l'ancienne ressource, puis remplacer **le dossier `hw_weapons`** par celui du ZIP V2, par exemple dans `resources/[weapons]/hw_weapons`. Ne pas lancer V1 et V2 ensemble.
2. Depuis le dossier décompressé, installer les entrées et icônes :

   ```sh
   python3 integration/install_ox.py --ox '/chemin/vers/resources/[ox]/ox_inventory'
   ```

   Sous Windows, utiliser `python`. Pour une simulation, ajouter `--dry-run`.

   Les autres définitions sont conservées, le fichier `weapons.lua` est sauvegardé dans `ox_inventory/.hw-backups/`, et la réinstallation ne duplique pas les entrées. Les icônes connues de V1 sont sauvegardées puis mises à jour. Une icône personnalisée différente est conservée et signalée comme conflit à résoudre manuellement.

   Sans Python : mettre les cinq entrées de `integration/ox_weapons_entries.lua` **dans la table `Weapons = { ... }`** de `ox_inventory/data/weapons.lua`, puis copier les cinq PNG de `integration/images/` dans `ox_inventory/web/images/`. Si les entrées existent déjà, ne pas les dupliquer. Ne pas remplacer tout `weapons.lua`, ne pas mettre les armes dans `data/items.lua` et ne pas créer d'items SQL ESX pour elles.
3. Dans `server.cfg`, conserver votre configuration ESX/ox existante et placer après `ensure ox_inventory` :

   ```cfg
   ensure hw_weapons
   add_ace group.admin command.hw_give allow
   ```

   **OneSync doit être activé.** Si votre configuration ne l'active pas déjà, utiliser le réglage OneSync de votre hébergement/txAdmin. La ressource déclare la contrainte `/onesync` dans son manifeste.

   Le groupe admin ESX ne donne pas automatiquement l'ACE `command.hw_give`. Utiliser votre groupe ACE existant ; un exemple est fourni dans `integration/server.cfg.example`.
4. Redémarrer complètement le serveur, puis reconnecter les joueurs. Les définitions et les nouveaux fichiers stream doivent être rechargés ensemble.

Les IDs restent inchangés ; il n'est pas nécessaire de retirer les armes persistantes pour passer à V2. L'installation ESX + ox_inventory doit être opérationnelle avec ses dépendances et ses munitions standard.

## Donner les armes et vérifier en jeu

Depuis la console serveur, remplacer `12` par l'ID du joueur :

```text
hw_give 12 all 60
hw_give 12 WEAPON_HW_REAPER_AXE 0
hw_give 12 WEAPON_HW_SOUL_SCYTHE 0
```

En jeu, un administrateur autorisé par ACE peut utiliser `/hw_give`. Les armes à feu arrivent avec le chargeur vide ; recharger avec les munitions fournies. ox_inventory gère la persistance et les numéros de série.

Dans F8, lancer `hw_check`. Le diagnostic vérifie les cinq modèles, les tailles de chargeur, puis le chargement et la durée des deux clips d'animation. **Un PASS technique ne vérifie pas l'aspect visuel ni les dégâts.**

Pour hache et faux : équiper l'arme, sortir du véhicule et cliquer pour frapper. Une requête est validée côté serveur avant de lancer le clip. Une frappe est limitée par le délai du profil et consomme 0,5 de durabilité, même lorsqu'elle touche le vide. La cible doit être un ped réseau vivant, proche et devant l'attaquant, dans la même instance. Le serveur fixe le délai d'impact et les dégâts ; le client propriétaire de la cible applique les dégâts après un contrôle de visibilité.

Le serveur vérifie l'arme réellement équipée dans ox_inventory, le hash sélectionné, la durabilité, le délai, le slot, la distance, la hauteur et le routing bucket. Changer/ranger/lâcher l'arme annule l'impact en attente. Les animations sont des tâches de ped normales diffusées par FiveM ; leur synchronisation réelle doit être contrôlée à deux joueurs.

Les contrôles de mêlée native, dont les takedowns, sont bloqués pour éviter une seconde frappe ou un retour au couteau. Cette gestion dédiée ne fournit pas de nouveaux takedowns ni de parade animée. Les scripts tiers de combat/emotes qui remplacent les tâches du ped peuvent interférer.

Pour les systèmes de mort/attribution, les dégâts scriptés peuvent nécessiter une adaptation de votre ressource de combat : l'événement serveur `hw_weapons:meleeHit` expose `(attaquant, netIdCible, arme, dégâts)`, et l'export `GetLastMeleeAttacker(netId)` fournit l'attaquant récent et l'arme pendant dix secondes. Cet événement indique un impact validé/dispatché, pas une mort confirmée. Ne pas supposer que ces dégâts produisent un événement balistique GTA.

## Liste de tests sur votre serveur

- Inspecter les cinq armes de près et de nuit : couleurs, relief, faces arrière, absence de clignotement et chargement des textures.
- Vérifier icônes, équipement/rangement et persistance après reconnexion.
- Tirer et recharger les trois armes à feu ; vérifier chargeurs, douilles, sons et munitions.
- Hache : vérifier un mouvement de frappe, sans piqûre de couteau. Faux : vérifier le balayage et les deux mains sur le manche.
- Tester la vue FPS, des personnages masculins/féminins, l'arrêt après changement d'arme, la mort et le ragdoll.
- À deux joueurs, vérifier l'animation vue à distance, l'impact, les dégâts, la durabilité et les scripts de mort de votre serveur.
- Tester un coup dans le vide, une cible derrière soi, une cible trop loin, un obstacle et des instances différentes.

**Le client GTA V/FiveM n'est pas accessible dans l'environnement de création. Les fichiers natifs et les scripts ont été vérifiés localement, mais cette liste de tests en jeu reste à exécuter.** Il n'est pas possible de garantir ici la calibration exacte des mains, le rendu final ou la synchronisation de votre serveur.

## Contenu des archives

L'archive `v2_install` contient la ressource, l'intégration, les aperçus, les licences et les guides. L'archive `v2_complete` ajoute les sources et les outils.

- `hw_weapons/stream/` : huit `.ydr`, un `.ytd` à 33 cartes et un `.ycd` à deux clips, réellement binaires.
- `integration/` : installateur, cinq entrées d'armes, cinq icônes RGBA 256 × 256 et exemple de configuration.
- `sources/blend/` et `sources/glb/` : cinq modèles modifiables dans chaque format.
- `sources/animations/` : rig/actions Blender modifiables, spécification des timings et données de prévisualisation.
- `sources/cwxml/` : sources XML CodeWalker des modèles avec leurs LOD, des textures et des animations.
- `sources/textures/` : diffuse, normal et specular en PNG/DDS BC3, 512 × 512, dix mipmaps.
- `previews/` : vrais rendus, deux GIF de mouvement, galerie locale et illustration de référence.
- `tools/`, `tests/` : génération et validation reproductibles.

Voir `VALIDATION.fr.md` pour les contrôles exécutés et leurs limites, et `third_party/README.md` pour la provenance des données de squelette de compatibilité.

## Reconstruire et modifier

Les fichiers natifs sont déjà inclus ; aucune compilation n'est nécessaire pour installer le pack.

Pour refaire les sources : Blender 4.3.2, Python 3.12 avec Pillow 12.3.0 et NumPy, .NET 8, et CodeWalker.Core. Depuis la racine du pack :

```sh
python3 tools/build_texture.py
blender -b --threads 8 --python tools/build_models.py
blender -b --python tools/build_melee_animations.py
```

Le générateur de textures synchronise les 33 cartes DDS et leur dictionnaire XML. Après ces générations :

```sh
git clone https://github.com/dexyfex/CodeWalker.git /chemin/CodeWalker
git -C /chemin/CodeWalker checkout 485d56bec00262ed7fa472261cce7bbc6202b96e
dotnet build tools/NativeExporter/NativeExporter.csproj -c Release -p:CodeWalkerProject=/chemin/CodeWalker/CodeWalker.Core/CodeWalker.Core.csproj
dotnet tools/NativeExporter/bin/Release/net8.0/NativeExporter.dll sources/cwxml hw_weapons/stream
python3 tools/validate_pack.py --roundtrip sources/native_validation
```

Les formats sont GTA Legacy : YDR 165, YTD 13, YCD 46. GTA V Enhanced n'est pas vérifié.

Pour recréer les aperçus de mouvement : `blender -b --python tools/render_melee_previews.py`. Ces rendus sont dans Blender, pas dans le jeu. Les paramètres de portée/dégâts/durabilité et les timings de lecture sont dans `hw_weapons/config.lua`. Si vous changez une animation, mettre à jour le timing d'impact et la durée correspondants.

Tests :

```sh
python3 -m pip install lupa==2.8
python3 -m unittest discover -s tests -v
```

Désinstallation de l'inventaire : `python3 integration/install_ox.py --ox '/chemin/ox_inventory' --uninstall`. Retirer ensuite `ensure hw_weapons` et les exemplaires persistants de ces cinq armes avant de supprimer leurs définitions. Cela n'est pas nécessaire pour une mise à jour V1 → V2.
