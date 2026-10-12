#!/usr/bin/env python3
"""Add the pack to an existing ox_inventory; preserve existing definitions and icons.

python integration/install_ox.py --ox /path/to/ox_inventory [--dry-run|--uninstall]
Only Python's standard library is required. Restart the server after installation.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile

HERE = Path(__file__).resolve().parent
START = '-- BEGIN HW_WEAPONS (managed by install_ox.py)'
END = '-- END HW_WEAPONS'
NAMES = ['WEAPON_HW_EMBER', 'WEAPON_HW_REVENANT', 'WEAPON_HW_PUMPKIN',
         'WEAPON_HW_REAPER_AXE', 'WEAPON_HW_SOUL_SCYTHE']

def install(ox, dry_run=False, uninstall=False):
    ox = Path(ox).resolve()
    target = ox / 'data' / 'weapons.lua'
    images = ox / 'web' / 'images'
    if not target.is_file() or not images.is_dir():
        raise ValueError('Chemin ox_inventory invalide: data/weapons.lua et web/images sont requis.')
    raw = target.read_bytes()
    text = raw.decode('utf-8-sig')
    newline = '\r\n' if b'\r\n' in raw else '\n'
    prefix = b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b''
    entries = HERE.joinpath('ox_weapons_entries.lua').read_text(encoding='utf-8')
    entries = '\n'.join(line for line in entries.splitlines() if not line.lstrip().startswith('--')).strip()
    block = '\n    ' + START + '\n' + '\n'.join('    ' + line for line in entries.splitlines()) + '\n    ' + END + '\n'
    block = block.replace('\n', newline)
    if text.count(START) != text.count(END) or text.count(START) > 1:
        raise ValueError('Marqueurs HW_WEAPONS incoherents; aucune modification effectuee.')
    if START in text:
        a = text.index(START)
        a = text.rfind(newline, 0, a)
        b = text.index(END) + len(END)
        b += len(newline) if text[b:].startswith(newline) else 0
        if text[a:b] != block:
            raise ValueError('Le bloc du pack a ete modifie manuellement; conservez vos changements avant de reinstaller.')
        updated = text[:a] + text[b:] if uninstall else text
    elif uninstall:
        updated = text
    else:
        if any(re.search(r"\[['\"]" + re.escape(name) + r"['\"]\]\s*=", text) for name in NAMES):
            raise ValueError('Une arme HW existe deja hors du bloc gere; aucune definition ne sera ecrasee.')
        anchors = list(re.finditer(r'^\s*Weapons\s*=\s*\{', text, re.MULTILINE))
        if len(anchors) != 1:
            raise ValueError('Impossible de localiser une unique table Weapons. Utilisez ox_weapons_entries.lua manuellement.')
        at = anchors[0].end()
        updated = text[:at] + block + text[at:]
    known_path=HERE/'known_icon_versions.json'
    known=json.loads(known_path.read_text()) if known_path.exists() else {}
    files = []
    for name in NAMES:
        source = HERE / 'images' / (name + '.png')
        dest = images / source.name
        if not source.is_file() or source.stat().st_size < 100:
            raise ValueError('Icone du pack absente ou vide: ' + source.name)
        if dest.exists() and dest.read_bytes() != source.read_bytes():
            digest=hashlib.sha256(dest.read_bytes()).hexdigest()
            if digest not in known.get(dest.name,[]):
                raise ValueError('Une icone differente porte deja ce nom; aucune icone ne sera ecrasee: ' + dest.name)
        files.append((source, dest))
    new_raw = prefix + updated.encode('utf-8')
    if dry_run:
        print('Validation OK; mode simulation, aucun fichier modifie.')
        return
    if new_raw != raw:
        backups = ox / '.hw-backups'
        backups.mkdir(exist_ok=True)
        backup = backups / ('weapons.lua.' + hashlib.sha256(raw).hexdigest()[:16] + '.bak')
        if not backup.exists():
            with backup.open('xb') as stream:
                stream.write(raw)
        fd, temp = tempfile.mkstemp(prefix='.hw-weapons-', dir=target.parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(new_raw)
            shutil.copymode(target, temp)
            os.replace(temp, target)
        finally:
            if Path(temp).exists():
                Path(temp).unlink()
        print('Definitions mises a jour. Sauvegarde: ' + str(backup))
    for source, dest in files:
        if uninstall:
            if dest.exists(): dest.unlink()
        elif not dest.exists() or dest.read_bytes()!=source.read_bytes():
            if dest.exists():
                backups=ox/'.hw-backups';backups.mkdir(exist_ok=True)
                digest=hashlib.sha256(dest.read_bytes()).hexdigest()[:16]
                backup=backups/(dest.name+'.'+digest+'.bak')
                if not backup.exists():shutil.copyfile(dest,backup)
            shutil.copyfile(source, dest)
    print('Pack retire.' if uninstall else 'Cinq definitions et cinq icones installees. Redemarrez le serveur.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ox', required=True, type=Path)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--dry-run', action='store_true')
    group.add_argument('--uninstall', action='store_true')
    args = parser.parse_args()
    try:
        install(args.ox, args.dry_run, args.uninstall)
    except (OSError, ValueError) as exc:
        sys.exit('Installation interrompue: ' + str(exc))
