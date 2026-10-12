"""Real Lua execution with mocked FiveM/ox natives; does not claim game validation."""
from pathlib import Path
import unittest
from lupa.lua54 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]

class LuaTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute((ROOT / 'hw_weapons/config.lua').read_text())
        self.lua.execute('''
            messages = {}; commands = {}; calls = {}; events = {}; online = true
            missing = nil; canCarry = true; addSuccess = true; failAmmo = false
            function print(message) table.insert(messages, message) end
            function RegisterCommand(name, cb, restricted) commands[name] = { cb = cb, restricted = restricted } end
            function AddEventHandler(name, cb) events[name] = cb end
            function GetCurrentResourceName() return 'hw_weapons' end
            function GetPlayerName(id) if online and id == 12 then return 'Test player' end end
            function TriggerClientEvent(...) end
            exports = { ox_inventory = {
                Items = function(self, name) if name ~= missing then return {name = name} end end,
                CanCarryItem = function(self, target, name, count) return canCarry end,
                AddItem = function(self, target, name, count, metadata)
                    table.insert(calls, {target = target, name = name, count = count, metadata = metadata})
                    if not addSuccess or (failAmmo and name:sub(1,5) == 'ammo-') then return false, 'inventory_full' end
                    return true, {slot=1}
                end
            } }
        ''')
        self.lua.execute((ROOT / 'hw_weapons/server.lua').read_text())

    def give(self, *args):
        self.lua.globals().commands['hw_give']['cb'](0, self.lua.table_from(args))

    def test_command_requires_ace(self):
        self.assertTrue(self.lua.globals().commands['hw_give']['restricted'])

    def test_give_pistol_with_ammo_uses_inventory(self):
        self.give('12', 'weapon_hw_ember', '40')
        calls = self.lua.globals().calls
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1]['name'], 'WEAPON_HW_EMBER')
        self.assertEqual(calls[1]['metadata']['durability'], 100)
        self.assertEqual(calls[1]['metadata']['ammo'], 0)
        self.assertEqual(calls[2]['name'], 'ammo-9')
        self.assertEqual(calls[2]['count'], 40)

    def test_all_gives_five_weapons_and_three_ammo_types(self):
        self.give('12', 'all', '60')
        calls = self.lua.globals().calls
        self.assertEqual(len(calls), 8)
        weapons = [calls[i]['name'] for i in range(1, len(calls)+1) if calls[i]['name'].startswith('WEAPON_')]
        self.assertEqual(len(set(weapons)), 5)

    def test_melee_requires_no_ammo(self):
        self.give('12', 'WEAPON_HW_SOUL_SCYTHE')
        self.assertEqual(len(self.lua.globals().calls), 1)

    def test_invalid_inputs_do_not_add_any_item(self):
        for args in [('12', 'WEAPON_RPG'), ('13', 'all'), ('12.5', 'all'),
                     ('12', 'all', '-1'), ('12', 'all', '251'), ('12', 'all', '2.5'),
                     ('12', 'all', 'abc'), ('abc', 'all')]:
            self.give(*args)
        self.assertEqual(len(self.lua.globals().calls), 0)

    def test_missing_weapon_definition_is_reported(self):
        self.lua.globals().missing = 'WEAPON_HW_EMBER'
        self.give('12', 'WEAPON_HW_EMBER')
        self.assertEqual(len(self.lua.globals().calls), 0)
        self.assertIn('manque', self.lua.globals().messages[1])

    def test_missing_ammo_does_not_partially_grant_weapon(self):
        self.lua.globals().missing = 'ammo-9'
        self.give('12', 'WEAPON_HW_EMBER')
        self.assertEqual(len(self.lua.globals().calls), 0)

    def test_full_inventory_blocks_weapon(self):
        self.lua.globals().canCarry = False
        self.give('12', 'WEAPON_HW_EMBER')
        self.assertEqual(len(self.lua.globals().calls), 0)

    def test_failed_weapon_add_does_not_add_ammo(self):
        self.lua.globals().addSuccess = False
        self.give('12', 'WEAPON_HW_EMBER')
        self.assertEqual(len(self.lua.globals().calls), 1)
        self.assertIn('Ajout refuse', self.lua.globals().messages[1])

    def test_ammo_failure_reports_partial_result(self):
        self.lua.globals().failAmmo = True
        self.give('12', 'WEAPON_HW_EMBER')
        self.assertEqual(len(self.lua.globals().calls), 2)
        self.assertIn('munitions non ajoutees', self.lua.globals().messages[2])

    def test_zero_ammo_grants_weapon_only(self):
        self.give('12', 'WEAPON_HW_EMBER', '0')
        self.assertEqual(len(self.lua.globals().calls), 1)

    def test_client_labels_and_diagnostics_execute(self):
        self.lua.execute('''
            labels = {}; hashes = {}; nextHash = 1
            function joaat(name)
                if not hashes[name] then hashes[name] = nextHash; nextHash = nextHash + 1 end
                return hashes[name]
            end
            function AddTextEntry(key, label) labels[key] = label end
            function CreateThread(cb) cb() end
            function Wait(ms) end
            function GetGameTimer() return 0 end
            function IsWeaponValid(hash) return true end
            function GetWeapontypeModel(hash)
                for _,weapon in ipairs(Config.Weapons) do
                    if joaat(weapon.name)==hash then return joaat(weapon.model) end
                end
            end
            function GetWeaponClipSize(hash)
                for _,weapon in ipairs(Config.Weapons) do
                    if joaat(weapon.name)==hash then return weapon.clip end
                end
            end
            function IsModelValid(hash) return true end
            function IsModelInCdimage(hash) return true end
            function RequestModel(hash) end
            function HasModelLoaded(hash) return true end
            function SetModelAsNoLongerNeeded(hash) end
        ''')
        self.lua.execute((ROOT / 'hw_weapons/client.lua').read_text())
        self.assertEqual(len(list(self.lua.globals().labels)), 5)
        self.lua.globals().commands['hw_check']['cb']()
        passes = [v for v in self.lua.globals().messages.values() if 'PASS WEAPON_HW_' in v]
        self.assertEqual(len(passes), 5)

    def test_manifest_is_valid_lua_and_registers_four_meta_files(self):
        self.lua.execute('''
            dataFiles = {}
            function fx_version(v) end; function game(v) end; function author(v) end
            function description(v) end; function version(v) end; function dependency(v) end
            function files(v) end; function shared_script(v) end
            function client_script(v) end; function server_script(v) end
            function data_file(kind) return function(file) table.insert(dataFiles,{kind=kind,file=file}) end end
        ''')
        self.lua.execute((ROOT / 'hw_weapons/fxmanifest.lua').read_text())
        self.assertEqual(len(self.lua.globals().dataFiles), 4)

if __name__ == '__main__': unittest.main()
