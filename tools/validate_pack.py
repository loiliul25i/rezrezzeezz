"""Validate cross-file registration, stream headers, source meshes and inventory assets.

Python standard library only. --roundtrip accepts XML emitted by NativeExporter.
This is asset validation, not a substitute for running the FiveM client.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import struct
import xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parents[1]

def validate(roundtrip=None):
    resource = ROOT / 'hw_weapons'
    specs = json.loads((ROOT / 'sources/weapon_specs.json').read_text())
    stats = json.loads((ROOT / 'sources/model_stats.json').read_text())
    assert len(specs) == 5 and len({s['name'] for s in specs}) == 5
    assert len(stats) == 8
    weapons = E.parse(resource / 'data/weapons.meta').getroot()
    definitions = {i.findtext('Name'): i for i in weapons.findall('.//Item[@type="CWeaponInfo"]')}
    assert set(definitions) == {s['name'] for s in specs}
    archetypes = {i.findtext('modelName'): i for i in E.parse(resource / 'data/weaponarchetypes.meta').findall('InitDatas/Item')}
    assert len(archetypes) == 8
    components = {i.findtext('Name'): i for i in E.parse(resource / 'data/weaponcomponents.meta').findall('Infos/Item')}
    assert len(components) == 3
    animations = E.parse(resource / 'data/weaponanimations.meta').getroot()
    default = {i.get('key') for i in animations.findall("WeaponAnimationsSets/Item[@key='Default']/WeaponAnimations/Item")}
    assert default == set(definitions)
    inventory = (ROOT / 'integration/ox_weapons_entries.lua').read_text()
    config = (resource / 'config.lua').read_text()
    client = (resource / 'client.lua').read_text()
    assert 'AddTextEntry(weapon.text, weapon.label)' in client
    models = {s['model'] for s in stats}
    assert set(archetypes) == models
    for spec in specs:
        definition = definitions[spec['name']]
        assert definition.findtext('Model') == spec['model']
        assert definition.findtext('HumanNameHash') == spec['text']
        assert int(definition.find('ClipSize').get('value')) == spec['clip']
        assert spec['name'] in inventory and spec['name'] in config and spec['text'] in config
        if spec['clip']:
            component = definition.findtext('AttachPoints/Item/Components/Item/Name')
            assert component in components
            assert components[component].findtext('Model') == spec['model'] + '_mag'
            assert int(components[component].find('ClipSize').get('value')) == spec['clip']
        else:
            assert definition.findtext('DamageType') == 'MELEE'
            assert not list(definition.find('AttachPoints'))
        icon = (ROOT / 'integration/images' / (spec['name'] + '.png')).read_bytes()
        assert icon[:8] == b'\x89PNG\r\n\x1a\n'
        assert struct.unpack('>II', icon[16:24]) == (256, 256)
        glb = (ROOT / 'sources/glb' / (spec['model'] + '.glb')).read_bytes()
        assert glb[:4] == b'glTF' and struct.unpack_from('<I', glb, 8)[0] == len(glb)
        assert (ROOT / 'sources/blend' / (spec['model'] + '.blend')).stat().st_size > 1000
    for archetype in archetypes.values(): assert archetype.findtext('txdName') == 'hw_finishes'
    binary_report = []
    for path in sorted((resource / 'stream').iterdir()):
        assert path.suffix in ('.ydr', '.ytd'), 'Unexpected file in stream: ' + path.name
        data = path.read_bytes()
        assert data[:4] == b'RSC7', 'Not a native GTA file: ' + path.name
        version = struct.unpack_from('<I', data, 4)[0]
        assert version == (165 if path.suffix == '.ydr' else 13)
        binary_report.append({'file': path.name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'resource_version': version})
    assert len(binary_report) == 9
    for stat in stats:
        model = stat['model']
        assert model in models
        original = E.parse(ROOT / 'sources/cwxml' / (model + '.ydr.xml')).getroot()
        check_model(original, stat)
        if roundtrip:
            decoded = E.parse(Path(roundtrip) / (model + '.roundtrip.xml')).getroot()
            check_model(decoded, stat)
    dds = (ROOT / 'sources/textures/hw_finish.dds').read_bytes()
    assert dds[:4] == b'DDS ' and dds[84:88] == b'DXT5'
    height, width = struct.unpack_from('<II', dds, 12)
    levels = struct.unpack_from('<I', dds, 28)[0]
    assert (width, height, levels) == (1024, 512, 11)
    expected = 128
    for level in range(levels):
        w, h = max(1, width >> level), max(1, height >> level)
        expected += ((w+3)//4) * ((h+3)//4) * 16
    assert len(dds) == expected
    report = {'weapon_count': 5, 'drawables': 8, 'texture_dictionaries': 1,
              'texture_mips': levels, 'native_roundtrip_checked': bool(roundtrip),
              'game_client_tested': False, 'total_stream_bytes': sum(b['bytes'] for b in binary_report),
              'files': binary_report}
    print(json.dumps(report, indent=2))
    return report

def check_model(root, stat):
    bones = root.findall('Skeleton/Bones/Item')
    assert len(bones) == stat['bones']
    for index, bone in enumerate(bones):
        assert int(bone.find('Index').get('value')) == index
        assert int(bone.find('ParentIndex').get('value')) < index
    assert root.find('Bounds') is not None
    assert len(root.findall('Bounds/Children/Item')) == 1
    shaders = root.findall('ShaderGroup/Shaders/Item')
    assert len(shaders) == stat['materials']
    for shader in shaders:
        assert shader.findtext("Parameters/Item[@name='DiffuseSampler']/Name") == 'hw_finish'
    triangle_count = 0
    for geometry in root.findall('DrawableModelsHigh/Item/Geometries/Item'):
        assert int(geometry.find('ShaderIndex').get('value')) < len(shaders)
        vb = geometry.find('VertexBuffer')
        layout = [n.tag for n in vb.find('Layout')]
        rows = [line.split() for line in vb.findtext('Data').splitlines() if line.strip()]
        sizes = {'Position': 3, 'BlendWeights': 4, 'BlendIndices': 4, 'Normal': 3, 'Colour0': 4, 'TexCoord0': 2}
        assert all(len(row) == sum(sizes[key] for key in layout) for row in rows)
        indices = [int(i) for i in geometry.findtext('IndexBuffer/Data').split()]
        assert len(indices) % 3 == 0 and all(0 <= index < len(rows) for index in indices)
        triangle_count += len(indices) // 3
        for row in rows:
            numbers = [float(x) for x in row]
            assert all(math.isfinite(x) for x in numbers)
            assert all(0 <= x <= 1 for x in numbers[-2:])
            if 'BlendWeights' in layout:
                assert sum(numbers[3:7]) == 255
                assert all(0 <= x < len(bones) for x in numbers[7:11])
    assert triangle_count == stat['triangles'], (stat['model'], triangle_count, stat['triangles'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--roundtrip', type=Path)
    args = parser.parse_args()
    validate(args.roundtrip)
