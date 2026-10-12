fx_version 'cerulean'
game 'gta5'

author 'Halloween Weapons Pack'
description 'Five original Halloween addon weapons for ESX and ox_inventory'
version '2.0.0'

dependency 'ox_inventory'
dependency '/onesync'

files {
    'data/weaponarchetypes.meta',
    'data/weaponcomponents.meta',
    'data/weapons.meta',
    'data/weaponanimations.meta'
}

data_file 'WEAPON_METADATA_FILE' 'data/weaponarchetypes.meta'
data_file 'WEAPONCOMPONENTSINFO_FILE' 'data/weaponcomponents.meta'
data_file 'WEAPONINFO_FILE' 'data/weapons.meta'
data_file 'WEAPON_ANIMATIONS_FILE' 'data/weaponanimations.meta'

shared_script 'config.lua'
client_script 'client.lua'
client_script 'melee_client.lua'
server_script 'server.lua'
server_script 'melee_server.lua'
