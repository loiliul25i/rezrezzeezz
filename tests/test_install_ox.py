import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
import hashlib
import json
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('installer', ROOT / 'integration/install_ox.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ox = Path(self.tmp.name) / 'ox_inventory'
        (self.ox / 'data').mkdir(parents=True)
        (self.ox / 'web/images').mkdir(parents=True)
        self.target = self.ox / 'data/weapons.lua'
        self.original = b"return {\n Weapons = {\n  ['WEAPON_PISTOL'] = {label = 'Original', weight = 1000},\n },\n Ammo = { ['ammo-9'] = {label = '9 mm'} },\n}\n"
        self.target.write_bytes(self.original)
        (self.ox / 'web/images/WEAPON_PISTOL.png').write_bytes(b'preserve-existing-image')

    def tearDown(self):
        self.tmp.cleanup()

    def test_install_preserves_existing_data_and_icons(self):
        installer.install(self.ox)
        result = self.target.read_text()
        for name in installer.NAMES:
            self.assertEqual(result.count("['" + name + "']"), 1)
            self.assertTrue((self.ox / 'web/images' / (name + '.png')).is_file())
        self.assertIn("['WEAPON_PISTOL'] = {label = 'Original', weight = 1000}", result)
        self.assertIn("Ammo = { ['ammo-9'] = {label = '9 mm'} }", result)
        self.assertEqual((self.ox / 'web/images/WEAPON_PISTOL.png').read_bytes(), b'preserve-existing-image')
        self.assertEqual(next((self.ox / '.hw-backups').glob('*.bak')).read_bytes(), self.original)

    def test_reinstall_is_idempotent(self):
        installer.install(self.ox)
        first = self.target.read_bytes()
        installer.install(self.ox)
        self.assertEqual(self.target.read_bytes(), first)
        self.assertEqual(len(list((self.ox / '.hw-backups').glob('*.bak'))), 1)

    def test_uninstall_restores_original_and_preserves_unrelated_edits(self):
        installer.install(self.ox)
        current = self.target.read_text().replace("label = 'Original'", "label = 'Modified by user'")
        self.target.write_text(current)
        installer.install(self.ox, uninstall=True)
        self.assertEqual(self.target.read_bytes(), self.original.replace(b"label = 'Original'", b"label = 'Modified by user'"))
        self.assertTrue((self.ox / 'web/images/WEAPON_PISTOL.png').exists())
        self.assertFalse((self.ox / 'web/images/WEAPON_HW_EMBER.png').exists())

    def test_dry_run_makes_no_changes(self):
        installer.install(self.ox, dry_run=True)
        self.assertEqual(self.target.read_bytes(), self.original)
        self.assertFalse((self.ox / '.hw-backups').exists())

    def test_conflicting_weapon_is_not_overwritten(self):
        content = self.original.replace(b"['WEAPON_PISTOL']", b"['WEAPON_HW_EMBER']")
        self.target.write_bytes(content)
        with self.assertRaises(ValueError): installer.install(self.ox)
        self.assertEqual(self.target.read_bytes(), content)

    def test_conflicting_icon_prevents_any_definition_change(self):
        (self.ox / 'web/images/WEAPON_HW_EMBER.png').write_bytes(b'custom-icon')
        with self.assertRaises(ValueError): installer.install(self.ox)
        self.assertEqual(self.target.read_bytes(), self.original)

    def test_crlf_and_bom_survive_install_and_uninstall(self):
        content = b'\xef\xbb\xbf' + self.original.replace(b'\n', b'\r\n')
        self.target.write_bytes(content)
        installer.install(self.ox)
        self.assertTrue(self.target.read_bytes().startswith(b'\xef\xbb\xbf'))
        installer.install(self.ox, uninstall=True)
        self.assertEqual(self.target.read_bytes(), content)

    def test_manually_changed_managed_block_is_not_overwritten(self):
        installer.install(self.ox)
        content = self.target.read_bytes().replace(b'weight = 1000', b'weight = 9999')
        self.target.write_bytes(content)
        with self.assertRaises(ValueError): installer.install(self.ox)
        self.assertEqual(self.target.read_bytes(), content)

    def test_invalid_layout_is_rejected(self):
        self.target.write_text('return {}')
        with self.assertRaises(ValueError): installer.install(self.ox)
        self.assertEqual(self.target.read_text(), 'return {}')

    def test_known_older_pack_icon_is_backed_up_and_upgraded(self):
        old = b'known-old-pack-icon'
        dest = self.ox / 'web/images/WEAPON_HW_EMBER.png'
        dest.write_bytes(old)
        known = {'WEAPON_HW_EMBER.png': [hashlib.sha256(old).hexdigest()]}
        with patch.object(installer.json, 'loads', return_value=known):
            installer.install(self.ox)
        self.assertEqual(dest.read_bytes(), (ROOT / 'integration/images/WEAPON_HW_EMBER.png').read_bytes())
        self.assertTrue(any(p.read_bytes() == old for p in (self.ox / '.hw-backups').glob('WEAPON_HW_EMBER.png.*.bak')))

if __name__ == '__main__': unittest.main()
