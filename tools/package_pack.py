"""Produce an install archive plus a complete archive containing editable sources."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist'
OUT.mkdir(exist_ok=True)
docs = ['README.md', 'README.fr.md', 'VALIDATION.fr.md', 'LICENSE']
for name, full in [('halloween_fivem_esx_ox_install.zip', False), ('halloween_fivem_esx_ox_complete.zip', True)]:
    selected = [ROOT / doc for doc in docs] + [ROOT / 'sources/asset_validation.json']
    folders = ['hw_weapons', 'integration', 'previews'] + (['sources', 'tools', 'tests'] if full else [])
    for folder in folders:
        selected += [p for p in (ROOT / folder).rglob('*') if p.is_file()
                     and not set(p.relative_to(ROOT).parts).intersection({'__pycache__', 'bin', 'obj', 'native_validation'})
                     and p.suffix not in {'.pyc', '.blend1'}]
    archive = OUT / name
    with ZipFile(archive, 'w', compression=ZIP_DEFLATED, compresslevel=6) as stream:
        for path in sorted(set(selected)):
            stream.write(path, 'halloween_weapon_pack/' + path.relative_to(ROOT).as_posix())
    with ZipFile(archive) as stream:
        assert stream.testzip() is None
        names = stream.namelist()
        assert sum(n.endswith('.ydr') for n in names) == 8
        assert sum(n.endswith('.ytd') for n in names) == 1
        assert 'halloween_weapon_pack/hw_weapons/fxmanifest.lua' in names
        assert all('halloween_weapon_pack/integration/images/' + n + '.png' in names
                   for n in ['WEAPON_HW_EMBER','WEAPON_HW_REVENANT','WEAPON_HW_PUMPKIN','WEAPON_HW_REAPER_AXE','WEAPON_HW_SOUL_SCYTHE'])
        if full:
            assert sum(n.endswith('.blend') for n in names) == 5
            assert sum(n.endswith('.glb') for n in names) == 5
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (OUT / (name + '.sha256')).write_text(digest + '  ' + name + '\n')
    print(f'{name}: {archive.stat().st_size:,} bytes; archive integrity and required content verified')
