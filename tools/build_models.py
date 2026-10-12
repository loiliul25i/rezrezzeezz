"""Run with Blender 4.3+: blender -b --python tools/build_models.py.

Original meshes, real-scale GTA Legacy CWXML, editable Blend sources and GLBs.
No GTA / third-party mesh is copied. All positions are in metres, +X forward.
"""
from pathlib import Path
from math import pi, sin, cos
import bpy
from mathutils import Vector, Quaternion
import xml.etree.ElementTree as E
import json

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'sources'
XML = SRC / 'cwxml'
PREVIEW = ROOT / 'previews'
ICONS = ROOT / 'integration' / 'images'
for directory in (XML, PREVIEW, ICONS, SRC / 'blend', SRC / 'glb'):
    directory.mkdir(parents=True, exist_ok=True)
PALETTE = [(0.035, .045, .062, 1), (.48, .54, .63, 1), (1, .18, .005, 1),
           (.40, .012, .85, 1), (.22, .075, .025, 1), (.065, .027, .020, 1),
           (.64, .55, .38, 1), (.004, .006, .009, 1)]
METAL, SILVER, ORANGE, PURPLE, WOOD, LEATHER, IVORY, BLACK = range(8)
objects = []
mats = []

def material(index):
    m = bpy.data.materials.new(['Gunmetal', 'Steel', 'Ember', 'Soul', 'Charred wood', 'Leather', 'Bone', 'Recess'][index])
    m.diffuse_color = PALETTE[index]
    m.use_nodes = True
    nodes = m.node_tree.nodes
    p = nodes.get('Principled BSDF')
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(SRC / 'textures' / 'hw_finish.png'), check_existing=True)
    m.node_tree.links.new(tex.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Metallic'].default_value = .8 if index in (METAL, SILVER) else .12
    p.inputs['Roughness'].default_value = .32 if index in (METAL, SILVER) else .62
    if index in (ORANGE, PURPLE):
        m.node_tree.links.new(tex.outputs['Color'], p.inputs['Emission Color'])
        p.inputs['Emission Strength'].default_value = 1.4
    return m

def finish(obj, name, mat, bone=2, bevel=0):
    obj.name = name
    obj.data.materials.append(mats[mat])
    obj['finish'] = mat
    obj['bone_index'] = bone
    obj['magazine'] = False
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        modifier = obj.modifiers.new('Machined edges', 'BEVEL')
        modifier.width = bevel
        modifier.segments = 2
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    objects.append(obj)
    return obj

def box(name, loc, scale, mat=METAL, bevel=.002, rotation=0, bone=2):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.scale = scale
    obj.rotation_euler.y = rotation
    return finish(obj, name, mat, bone, bevel)

def cylinder(name, loc, radius, length, mat=METAL, axis='X', vertices=16, bone=2):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=length, location=loc)
    obj = bpy.context.object
    if axis == 'X': obj.rotation_euler.y = pi / 2
    elif axis == 'Y': obj.rotation_euler.x = pi / 2
    return finish(obj, name, mat, bone, .0008)

def ellipsoid(name, loc, scale, mat=METAL, bone=2):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1, location=loc)
    obj = bpy.context.object
    obj.scale = scale
    return finish(obj, name, mat, bone)

def polygon(name, points, depth, mat=METAL, y=0, bone=2, bevel=.001):
    n = len(points)
    verts = [(x, y - depth/2, z) for x,z in points] + [(x, y + depth/2, z) for x,z in points]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
    faces += [(i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return finish(obj, name, mat, bone, bevel)

def line(name, coords, radius, mat, bone=2):
    for i,(a,b) in enumerate(zip(coords, coords[1:])):
        a,b = Vector(a),Vector(b)
        obj = cylinder(f'{name}_{i}', (a+b)/2, radius, (b-a).length, mat, axis='Z', vertices=8, bone=bone)
        obj.rotation_euler = (b-a).to_track_quat('Z','Y').to_euler()

def bolt(x,z,y=.028, radius=.003, bone=2):
    for sign in (-1,1):
        cylinder('Hex rivet', (x, sign*y, z),radius,.002,SILVER,'Y',6,bone)

def pumpkin(x,z,y,r=.018, bone=2):
    for side in (-1,1):
        sy = side*y
        ellipsoid('Pumpkin medallion',(x,sy,z),(r,.0015,r*.84),ORANGE,bone)
        for eye in (-1,1):
            ex=x+eye*r*.35
            polygon('Carved eye',[(ex-r*.18,z+r*.08),(ex+r*.17,z+r*.08),(ex,z+r*.39)],.001,BLACK,sy+side*.002,bone,0)
        polygon('Carved grin',[(x-r*.58,z-r*.16),(x-r*.30,z-r*.40),(x-r*.05,z-r*.22),
                              (x+r*.10,z-r*.39),(x+r*.48,z-r*.17),(x+r*.33,z-r*.55),(x-r*.28,z-r*.56)],
                .001,BLACK,sy+side*.002,bone,0)
        box('Pumpkin stem',(x,sy,z+r*.90),(r*.20,.003,r*.28),WOOD,0,bone=bone)

def bat(x,z,y,r=.030):
    wing=[(-1,0),(-.70,.35),(-.43,.13),(-.12,.20),(0,.45),(.12,.20),(.43,.13),(.70,.35),(1,0),
          (.63,-.12),(.43,-.40),(.25,-.15),(0,-.36),(-.25,-.15),(-.43,-.40),(-.63,-.12)]
    for side in (-1,1):
        polygon('Bat emblem',[(x+a*r,z+b*r) for a,b in wing],.0015,PURPLE,side*y)

def skull(x,z,y=0,r=.025):
    ellipsoid('Skull',(x,y,z),(r,r*.72,r*1.1),IVORY)
    for side in (-1,1):
        sy=y+side*r*.70
        for eye in (-1,1):
            ellipsoid('Eye socket',(x+eye*r*.35,sy,z+r*.10),(r*.21,.002,r*.25),BLACK)
            ellipsoid('Soul eye',(x+eye*r*.35,sy+side*.001,z+r*.10),(r*.10,.002,r*.13),PURPLE)
        polygon('Nose',[(x-r*.12,z-r*.05),(x+r*.12,z-r*.05),(x,z-r*.28)],.001,BLACK,sy)
        for t in range(5):
            box('Tooth',(x+(t-2)*r*.22,sy,z-r*.74),(r*.17,.004,r*.23),IVORY,.0004)

def pistol():
    box('Lower frame',(-.010,0,.008),(.195,.035,.023),METAL)
    box('Slide',(-.005,0,.035),(.210,.038,.031),METAL,.003,bone=3)
    cylinder('Barrel',(0.076,0,.035),.009,.075,SILVER)
    cylinder('Muzzle recess',(.113,0,.035),.0065,.001,BLACK)
    polygon('Grip',[(-.066,.002),(-.032,-.011),(-.058,-.111),(-.102,-.111)],.033,IVORY,bevel=.003)
    for side in (-1,1):
        polygon('Grip dark inset',[(-.070,-.027),(-.043,-.030),(-.061,-.103),(-.094,-.103)],.0015,LEATHER,side*.018)
    box('Grip bottom',(-.077,0,-.112),(.052,.039,.009),METAL)
    line('Trigger guard',[(-.032,0,.002),(.020,0,-.007),(.027,0,-.033),(-.049,0,-.033)],.003,METAL)
    box('Trigger',(-.011,0,-.013),(.005,.007,.020),ORANGE,.001,rotation=.22,bone=4)
    for x in [-.090,-.081,-.072,-.063,.063,.072,.081]:
        box('Slide serration',(x,-.020,.035),(.003,.002,.022),SILVER,.0002,bone=3)
        box('Slide serration',(x,.020,.035),(.003,.002,.022),SILVER,.0002,bone=3)
    for x in [-.086,.088]:
        box('Sight',(x,0,.056),(.012,.013,.011),BLACK,.0005,bone=3)
        box('Sight ember',(x,0,.062),(.003,.005,.003),ORANGE,0,bone=3)
    line('Ember slide edge',[(-.103,-.021,.049),(.097,-.021,.049)],.0009,ORANGE,3)
    line('Ember slide edge',[(-.103,.021,.049),(.097,.021,.049)],.0009,ORANGE,3)
    pumpkin(.026,.035,.021,.011,3)
    pumpkin(-.069,-.063,.020,.013)
    for x in [-.082,-.063]: bolt(x,-.031,.019,.002)
    start=len(objects)
    box('Ember magazine',(-.071,0,-.074),(.028,.025,.087),METAL,.001)
    box('Ember magazine plate',(-.077,0,-.120),(.047,.033,.007),ORANGE,.001)
    for obj in objects[start:]: obj['magazine']=True
    return (.114,0,.035),(-.061,0,-.013)

def rifle(ak=False):
    accent=ORANGE if ak else PURPLE
    box('Receiver',(.016,0,.043),(.268,.052,.058),METAL,.003)
    box('Upper receiver',(.040,0,.076),(.290,.046,.016),METAL,.002)
    polygon('Pistol grip',[(-.080,.023),(-.030,.014),(-.055,-.102),(-.107,-.097)],.037,WOOD if ak else LEATHER,bevel=.003)
    line('Trigger guard',[(-.029,0,.014),(.038,0,.014),(.034,0,-.018),(-.038,0,-.020)],.003,METAL)
    box('Trigger',(.001,0,.000),(.006,.009,.024),SILVER,.001,rotation=.20,bone=4)
    cylinder('Barrel',(.355,0,.050),.009,.400,METAL)
    cylinder('Muzzle brake',(.568,0,.050),.014,.042,METAL)
    cylinder('Muzzle bore',(.590,0,.050),.007,.001,BLACK)
    for x in [.558,.570,.582]:
        box('Muzzle vent',(x,-.014,.050),(.005,.001,.011),BLACK,0)
        box('Muzzle vent',(x,.014,.050),(.005,.001,.011),BLACK,0)
    cylinder('Buffer tube',(-.168,0,.053),.016,.200,METAL)
    if ak:
        polygon('Wood stock',[(-.120,.069),(-.346,.050),(-.342,-.079),(-.302,-.066),(-.185,.020),(-.120,.020)],.046,WOOD,bevel=.003)
        box('Stock butt',(-.345,0,-.013),(.008,.052,.139),BLACK,.001)
        box('Wood foregrip',(.267,0,.035),(.184,.053,.052),WOOD,.003)
        box('Upper wood guard',(.262,0,.078),(.160,.048,.021),WOOD,.003)
        cylinder('Gas tube',(.369,0,.083),.007,.204,METAL)
        box('Gas block',(.423,0,.066),(.015,.028,.043),METAL)
        line('Front sight tower',[(.504,-.007,.047),(.504,-.007,.111),(.504,.007,.111),(.504,.007,.047)],.0035,METAL)
        box('Rear sight',(.108,0,.092),(.025,.021,.017),METAL,.001)
        pumpkin(-.284,-.006,.025,.028)
        pumpkin(.270,.035,.028,.018)
        for x in [.204,.225,.246,.267,.288,.309]:
            box('Guard slot',(x,-.028,.043),(.009,.001,.010),BLACK,0)
            box('Guard slot',(x,.028,.043),(.009,.001,.010),BLACK,0)
        start=len(objects)
        polygon('Curved AK magazine',[(.061,.018),(.122,.018),(.127,-.039),(.160,-.109),(.195,-.149),(.158,-.173),(.114,-.135),(.078,-.067)],.039,METAL,bevel=.002)
        for side in (-1,1):
            for dx in [-.011,.0,.011]:
                line('Magazine rib',[(.090+dx,side*.021,-.011),(.099+dx,side*.021,-.066),(.127+dx,side*.021,-.114),(.163+dx,side*.021,-.153)],.0015,accent)
    else:
        # A skeletal adjustable stock with a genuinely open centre.
        line('Stock frame',[(-.144,0,.068),(-.344,0,.061),(-.350,0,-.078),(-.305,0,-.058),(-.225,0,.014),(-.144,0,.019)],.011,METAL)
        box('Stock rubber pad',(-.350,0,-.008),(.012,.055,.157),BLACK,.002)
        box('Cheek support',(-.246,0,.075),(.150,.048,.018),METAL,.003)
        box('Handguard',(.285,0,.051),(.235,.052,.052),METAL,.003)
        for x in [.192,.221,.250,.279,.308,.337,.366]:
            for side in (-1,1):
                box('Handguard inset',(x,side*.027,.052),(.017,.002,.011),BLACK,.002)
                box('Soul vent edge',(x,side*.029,.045),(.014,.001,.0018),PURPLE,0)
        for x in [i*.013+.025 for i in range(28)]:
            box('Picatinny tooth',(x,0,.087),(.006,.030,.006),METAL,.0005)
        box('Optic mount',(.045,0,.104),(.060,.030,.026),METAL,.002)
        line('Reflex sight frame',[(.028,-.016,.116),(.028,-.016,.152),(.028,.016,.152),(.028,.016,.116)],.003,METAL)
        box('Reflex soul dot',(.032,0,.133),(.002,.004,.004),PURPLE,.0003)
        bat(-.248,.051,.026,.052)
        bat(.085,.043,.028,.025)
        start=len(objects)
        polygon('AR magazine',[(.063,.018),(.124,.018),(.142,-.148),(.079,-.156)],.040,METAL,bevel=.002)
        for side in (-1,1):
            for x in [.084,.100,.116]:
                line('Magazine soul groove',[(x,side*.022,.000),(x+.015,side*.022,-.135)],.0013,PURPLE)
        box('Magazine base',(.111,0,-.154),(.069,.046,.010),METAL,.002,rotation=-.08)
    for obj in objects[start:]:obj['magazine']=True
    for x,z in [(-.071,.050),(-.021,.033),(.102,.060),(.150,.047)]:bolt(x,z)
    box('Ejection port',(.086,-.027,.068),(.056,.002,.019),BLACK,.001)
    box('Bolt',(.080,-.029,.068),(.040,.002,.008),SILVER,.001,bone=3)
    box('Selector',(-.054,-.029,.041),(.023,.003,.004),SILVER,.001,rotation=.23)
    return (.590,0,.050),(.092,0,.019)

def axe():
    cylinder('Charred haft',(0,0,.180),.019,.780,WOOD,'Z')
    for z in [i*.018-.195 for i in range(18)]:
        cylinder('Leather wrap',(0,0,z),.0215,.012,LEATHER,'Z')
    for z in [-.210,.095,.170,.440,.520]:
        cylinder('Forged collar',(0,0,z),.024,.024,METAL,'Z')
        cylinder('Ember collar',(0,0,z+.003),.0246,.002,ORANGE,'Z')
    skull(0,-.230,0,.033)
    # Thick central head and separate sharpened cutting edge.
    blade=[(-.038,.470),(.035,.470),(.114,.537),(.191,.570),(.241,.583),(.199,.521),(.196,.420),(.236,.335),(.178,.355),(.091,.408),(.035,.422),(-.038,.422)]
    polygon('Crescent axe head',blade,.026,METAL,bevel=.002)
    polygon('Honed cutting edge',[(.191,.570),(.241,.583),(.199,.521),(.196,.420),(.236,.335),(.214,.352),(.176,.423),(.177,.522)],.030,SILVER,bevel=.001)
    polygon('Back spike',[(-.038,.476),(-.150,.515),(-.084,.434),(-.038,.422)],.023,METAL)
    skull(.018,.462,0,.030)
    for side in (-1,1):
        line('Ember fracture',[(.052,side*.015,.454),(.091,side*.015,.480),(.123,side*.015,.453),(.168,side*.015,.470),(.190,side*.015,.443)],.0018,ORANGE)
        line('Ember fracture',[(.110,side*.015,.464),(.105,side*.015,.421),(.152,side*.015,.404),(.183,side*.015,.378)],.0012,ORANGE)
    pumpkin(.097,.448,.016,.026)
    return None,None

def scythe():
    cylinder('Long charred shaft',(0,0,.330),.018,.1+1.40,WOOD,'Z')
    for z in [-.390,-.120,.120,.420,.770,1.035]:
        cylinder('Soul collar',(0,0,z),.024,.025,METAL,'Z')
        cylinder('Soul collar light',(0,0,z+.004),.025,.003,PURPLE,'Z')
    for lo,hi in [(-.32,-.17),(-.08,.08),(.31,.45)]:
        for i in range(9):
            z=lo+(hi-lo)*i/8
            cylinder('Leather grip',(0,0,z),.0215,.012,LEATHER,'Z')
    # Curved tapered blade, not a rectangular placeholder.
    blade=[(-.025,.981),(.042,1.044),(.146,1.077),(.270,1.073),(.395,1.026),(.511,.936),(.604,.812),(.649,.662),
           (.585,.738),(.496,.812),(.395,.868),(.277,.913),(.164,.941),(.050,.950)]
    polygon('Reaper curved blade',blade,.017,METAL,bevel=.0015)
    edge=[(.270,1.073),(.395,1.026),(.511,.936),(.604,.812),(.649,.662),(.585,.738),(.496,.812),(.395,.868),(.412,.894),(.521,.868),(.592,.798),(.565,.893),(.480,.979),(.366,1.036)]
    polygon('Silver scythe edge',edge,.018,SILVER,bevel=.0005)
    polygon('Back hook',[(-.025,1.018),(-.148,1.111),(-.130,1.018),(-.052,.949)],.021,METAL)
    skull(.044,1.005,0,.049)
    for side in (-1,1):
        line('Soul blade runes',[(.125,side*.010,.987),(.177,side*.010,1.013),(.205,side*.010,.980),(.290,side*.010,1.019),(.344,side*.010,.985),(.411,side*.010,.973)],.002,PURPLE)
        for z in [.17,.24,.58,.65,.86]:
            line('Shaft rune',[(-.008,side*.019,z-.020),(.008,side*.019,z),(-.008,side*.019,z+.020)],.0012,PURPLE)
    polygon('Tail spike',[(-.015,-.421),(.015,-.421),(.038,-.489),(-.009,-.461)],.021,METAL)
    return None,None

def element(parent, tag, text=None, **attributes):
    e=E.SubElement(parent,tag,{k:str(v) for k,v in attributes.items()})
    if text is not None:e.text=str(text)
    return e

def vec(parent,tag,values,w=None):
    a=dict(zip(('x','y','z'),(f'{v:.8g}' for v in values)))
    if w is not None:a['w']=str(w)
    return element(parent,tag,**a)

def bones_for(kind,muzzle,clip):
    # Standard GTA weapon bone tags; hand frame, not borrowed meshes.
    if kind=='pistol':
        grip=Vector((-.105,-.014,-.046)); q=Quaternion((.7545,.6552,-.0031,.0381)).normalized()
    elif kind in ('ar','ak'):
        grip=Vector((-.105,-.023,-.043));q=Quaternion((.7474,.6578,.0003,.0931)).normalized()
    else:
        grip=Vector((-.045,.002,.012));q=Quaternion((.778,.619,-.106,.018)).normalized()
    iq=q.inverted()
    bones=[('Gun_Root',0,-1,Vector((0,0,0)),Quaternion()),
           ('Gun_GripR',18308,0,grip,q),
           ('Gun_Main_Bone',3360,1,iq @ -grip,iq)]
    if muzzle:
        bones += [('Gun_Cock1',39439,2,Vector((0,0,.035 if kind=='pistol' else .068)),Quaternion((0,1,0,0))),
                  ('Gun_Trigger_Pr',56099,2,Vector((-.011 if kind=='pistol' else .001,0,-.013 if kind=='pistol' else 0)),Quaternion()),
                  ('Gun_Muzzle',17833,2,Vector(muzzle),Quaternion((0,1,0,0))),
                  ('Gun_VFX_Eject',28405,2,Vector((.014 if kind=='pistol' else .086,-.017 if kind=='pistol' else -.027,.038 if kind=='pistol' else .068)),Quaternion((.7071,0,0,-.7071)).normalized()),
                  ('WAPClip',1477,2,Vector(clip),Quaternion())]
        if kind!='pistol':bones.append(('Gun_GripL',18302,0,Vector((.255,0,.025)),Quaternion()))
    return bones

def put_skeleton(root,bones):
    s=element(root,'Skeleton')
    for tag,val in [('Unknown1C',16777216),('Unknown50',2139062143),('Unknown54',2139062143),('Unknown58',2139062143)]:
        element(s,tag,value=val)
    b=element(s,'Bones')
    for idx,(name,tag,parent,pos,q) in enumerate(bones):
        item=element(b,'Item');element(item,'Name',name)
        later=[j for j in range(idx+1,len(bones)) if bones[j][2]==parent]
        for key,val in [('Tag',tag),('Index',idx),('ParentIndex',parent),('SiblingIndex',later[0] if later else -1)]:
            element(item,key,value=val)
        element(item,'Flags','RotX, RotY, RotZ, TransX, TransY, TransZ' + (', Unk0' if idx<3 else ''))
        vec(item,'Translation',pos);vec(item,'Rotation',(q.x,q.y,q.z),q.w);vec(item,'Scale',(1,1,1));vec(item,'TransformUnk',(0,4,-3),0)

def export_xml(name,selected,bones=None,offset=Vector((0,0,0))):
    groups={}
    for obj in selected:
        mesh=obj.data;mesh.calc_loop_triangles()
        normal_matrix=obj.matrix_world.to_3x3().inverted().transposed()
        material_index=obj['finish'];bone=obj['bone_index'] if bones else 0
        vertices=groups.setdefault(material_index,[])
        for tri in mesh.loop_triangles:
            for vertex_index in tri.vertices:
                p=obj.matrix_world @ mesh.vertices[vertex_index].co-offset
                n=(normal_matrix @ tri.normal).normalized()
                # Coordinates stay inside the appropriate original atlas tile.
                a,b=(p.x,p.z) if abs(n.y)>.6 else ((p.x,p.y) if abs(n.z)>.6 else (p.y,p.z))
                uv=((material_index%4+.10+.80*((a*2.4+.5)%1))/4,
                    (material_index//4+.10+.80*((b*2.4+.5)%1))/2)
                vertices.append((p,n,uv,bone))
    allpoints=[row[0] for rows in groups.values() for row in rows]
    low=Vector(tuple(min(p[i] for p in allpoints) for i in range(3)))
    high=Vector(tuple(max(p[i] for p in allpoints) for i in range(3)))
    root=E.Element('Drawable');element(root,'Name',name)
    vec(root,'BoundingSphereCenter',(low+high)/2);element(root,'BoundingSphereRadius',value=f'{(high-low).length/2:.8g}')
    vec(root,'BoundingBoxMin',low);vec(root,'BoundingBoxMax',high)
    for lod in ['High','Med','Low','Vlow']:
        element(root,'LodDist'+lod,value=9998);element(root,'Flags'+lod,value=1 if lod=='High' else 0)
    sg=element(root,'ShaderGroup');shaders=element(sg,'Shaders')
    used=sorted(groups)
    for mat in used:
        shader=element(shaders,'Item');emissive=mat in (ORANGE,PURPLE)
        element(shader,'Name','emissive' if emissive else 'default')
        element(shader,'FileName','emissive.sps' if emissive else 'default.sps');element(shader,'RenderBucket',value=0)
        params=element(shader,'Parameters');d=element(params,'Item',name='DiffuseSampler',type='Texture');element(d,'Name','hw_finish')
        element(params,'Item',name='matMaterialColorScale',type='Vector',x=1,y=0,z=0,w=1)
        if emissive:element(params,'Item',name='emissiveMultiplier',type='Vector',x=1.4,y=0,z=0,w=0)
        else:
            for key,val in [('HardAlphaBlend',(1,0,0,0)),('useTessellation',(0,0,0,0)),('wetnessMultiplier',(0,0,0,0)),('globalAnimUV1',(0,1,0,0)),('globalAnimUV0',(1,0,0,0))]:
                element(params,'Item',name=key,type='Vector',**dict(zip(('x','y','z','w'),val)))
    if bones:put_skeleton(root,bones)
    model=element(element(root,'DrawableModelsHigh'),'Item')
    for key,val in [('RenderMask',255),('Flags',1 if bones else 0),('HasSkin',1 if bones else 0),('BoneIndex',0),('Unknown1',len(bones) if bones else 0)]:element(model,key,value=val)
    geometries=element(model,'Geometries')
    for shader_index,mat in enumerate(used):
        rows=groups[mat]
        assert len(rows)<65536, f'Too many vertices for 16-bit GTA indices: {name}'
        g=element(geometries,'Item');element(g,'ShaderIndex',value=shader_index)
        vec(g,'BoundingBoxMin',tuple(min(r[0][i] for r in rows) for i in range(3)),0)
        vec(g,'BoundingBoxMax',tuple(max(r[0][i] for r in rows) for i in range(3)),0)
        if bones:element(g,'BoneIDs',', '.join(str(i) for i in range(len(bones))))
        vb=element(g,'VertexBuffer');element(vb,'Flags',value=0);layout=element(vb,'Layout',type='GTAV1')
        for key in (['Position','BlendWeights','BlendIndices','Normal','Colour0','TexCoord0'] if bones else ['Position','Normal','Colour0','TexCoord0']):element(layout,key)
        lines=[]
        for p,n,uv,bone in rows:
            parts=[' '.join(f'{v:.8g}' for v in p)]
            if bones:parts += ['255 0 0 0',f'{bone} 0 0 0']
            parts += [' '.join(f'{v:.8g}' for v in n),'255 255 255 255',' '.join(f'{v:.8g}' for v in uv)]
            lines.append('   '.join(parts))
        element(vb,'Data','\n'+'\n'.join(lines)+'\n')
        ib=element(g,'IndexBuffer');element(ib,'Data','\n'+' '.join(str(i) for i in range(len(rows)))+'\n')
    put_collision(root,low,high)
    E.indent(root)
    E.ElementTree(root).write(XML/(name+'.ydr.xml'),encoding='UTF-8',xml_declaration=True)
    return {'model':name,'triangles':len(allpoints)//3,'materials':len(used),'bones':len(bones) if bones else 0,'min':list(low),'max':list(high)}

def put_collision(root,low,high):
    center=(low+high)/2;size=high-low;half=size/2
    bounds=element(root,'Bounds',type='Composite')
    def properties(node,a,b,c,margin,material,kind):
        vec(node,'BoxMin',a);vec(node,'BoxMax',b);vec(node,'BoxCenter',c);vec(node,'SphereCenter',c)
        element(node,'SphereRadius',value=f'{(b-a).length/2:.8g}')
        element(node,'Margin',value=margin);element(node,'Volume',value=f'{size.x*size.y*size.z:.8g}')
        vec(node,'Inertia',((size.y**2+size.z**2)/12,(size.x**2+size.z**2)/12,(size.x**2+size.y**2)/12))
        for tag,val in [('MaterialIndex',material),('MaterialColourIndex',0),('ProceduralID',0),('RoomID',0),('PedDensity',0),('UnkFlags',0),('PolyFlags',0),('UnkType',kind)]:element(node,tag,value=val)
    properties(bounds,low,high,center,0,0,2)
    box=element(element(bounds,'Children'),'Item',type='Box')
    properties(box,-half,half,Vector((0,0,0)),.002,55,2)
    element(box,'CompositeTransform',f'1 0 0 0\n0 1 0 0\n0 0 1 0\n{center.x} {center.y} {center.z} 1')
    element(box,'CompositeFlags1','MAP_WEAPON, MAP_DYNAMIC, MAP_ANIMAL, MAP_COVER, MAP_VEHICLE')
    element(box,'CompositeFlags2','VEHICLE_NOT_BVH, VEHICLE_BVH, PED, RAGDOLL, ANIMAL, ANIMAL_RAGDOLL, OBJECT, PLANT, PROJECTILE, EXPLOSION, TEST_WEAPON, TEST_CAMERA, TEST_AI, TEST_SCRIPT, GLASS')
    element(root,'Lights')

def make_armature(name,bones,selected):
    bpy.ops.object.armature_add(enter_editmode=True)
    rig=bpy.context.object;rig.name=name+'_rig'
    rig.data.edit_bones.remove(rig.data.edit_bones[0])
    worlds=[]
    for idx,(bname,tag,parent,pos,q) in enumerate(bones):
        from mathutils import Matrix
        local=Matrix.Translation(pos)@q.to_matrix().to_4x4()
        world=worlds[parent]@local if parent>=0 else local
        worlds.append(world)
        bone=rig.data.edit_bones.new(bname);bone.head=world.translation;bone.tail=world@Vector((0,.035,0))
        bone.align_roll(world.to_3x3()@Vector((0,0,1)))
        if parent>=0:bone.parent=rig.data.edit_bones[bones[parent][0]]
    bpy.ops.object.mode_set(mode='OBJECT')
    for i,bone in enumerate(rig.data.bones):bone['gta_tag']=bones[i][1]
    for obj in selected:
        obj.parent=rig
        group=obj.vertex_groups.new(name=bones[obj['bone_index']][0]);group.add(list(range(len(obj.data.vertices))),1,'REPLACE')
        modifier=obj.modifiers.new('Weapon skeleton','ARMATURE');modifier.object=rig
    return rig

def uv_map(obj):
    mesh=obj.data
    while mesh.uv_layers: mesh.uv_layers.remove(mesh.uv_layers[0])
    layer=mesh.uv_layers.new(name='UVMap');layer.active_render=True
    mat=obj['finish']
    for poly in mesh.polygons:
        worldnormal=obj.matrix_world.to_3x3()@poly.normal
        for index in poly.loop_indices:
            p=obj.matrix_world@mesh.vertices[mesh.loops[index].vertex_index].co
            a,b=(p.x,p.z) if abs(worldnormal.y)>.6 else ((p.x,p.y) if abs(worldnormal.z)>.6 else (p.y,p.z))
            layer.data[index].uv=((mat%4+.10+.80*((a*2.4+.5)%1))/4,1-(mat//4+.10+.80*((b*2.4+.5)%1))/2)

def render(name,selected):
    pts=[o.matrix_world@v.co for o in selected for v in o.data.vertices]
    low=Vector(tuple(min(p[i] for p in pts) for i in range(3)));high=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    center=(low+high)/2;width=high.x-low.x;height=high.z-low.z;span=max(width,height)
    bpy.ops.object.camera_add(location=center+Vector((span*.12,-span*2.5,span*.10)))
    camera=bpy.context.object;camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=max(width,height*1.5)*1.20
    scene=bpy.context.scene;scene.camera=camera
    scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=False
    scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True
    scene.world.color=(.18,.18,.18)
    scene.view_settings.view_transform='AgX'
    for loc,power,colour in [(Vector((-.6,-1.5,1.5)),500,(.72,.82,1)),(Vector((.8,1,1)),700,(.9,.6,.35)),(Vector((0,-1,-.5)),180,(.6,.65,.85))]:
        bpy.ops.object.light_add(type='AREA',location=center+loc*max(.4,span))
        light=bpy.context.object;light.data.energy=power*max(.18,span)**2;light.data.shape='DISK';light.data.size=max(.4,span)
        light.data.color=colour;light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(PREVIEW/(name+'.png'));bpy.ops.render.render(write_still=True)
    # A separate actual render for square inventory icons; no concept-image cutouts.
    scene.render.resolution_x=256;scene.render.resolution_y=256
    camera.data.ortho_scale=max(width,height)*1.20
    scene.render.filepath=str(ICONS/(name+'.png'));bpy.ops.render.render(write_still=True)

SPECS=[('WEAPON_HW_EMBER','w_pi_hw_ember','pistol',pistol),
       ('WEAPON_HW_REVENANT','w_ar_hw_revenant','ar',lambda:rifle(False)),
       ('WEAPON_HW_PUMPKIN','w_ar_hw_pumpkin','ak',lambda:rifle(True)),
       ('WEAPON_HW_REAPER_AXE','w_me_hw_reaper','axe',axe),
       ('WEAPON_HW_SOUL_SCYTHE','w_me_hw_soul','scythe',scythe)]
stats=[]
bpy.context.preferences.filepaths.save_version=0
for weapon,model,kind,builder in SPECS:
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    objects=[];mats=[material(i) for i in range(8)]
    muzzle,clip=builder();bpy.context.view_layer.update()
    for obj in objects:uv_map(obj)
    bones=bones_for(kind,muzzle,clip)
    main=[o for o in objects if not o['magazine']]
    stats.append(export_xml(model,main,bones))
    magazines=[o for o in objects if o['magazine']]
    if magazines:
        for obj in magazines:obj['bone_index']=0
        stats.append(export_xml(model+'_mag',magazines,[('AAPClip',0,-1,Vector((0,0,0)),Quaternion())],offset=Vector(clip)))
    rig=make_armature(model,bones,main)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects+[rig]:obj.select_set(True)
    bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.gltf(filepath=str(SRC/'glb'/(model+'.glb')),export_format='GLB',use_selection=True)
    for image in bpy.data.images:
        if image.source=='FILE':image.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(SRC/'blend'/(model+'.blend')))
    render(weapon,objects)
    print('BUILT',weapon,flush=True)
(SRC/'model_stats.json').write_text(json.dumps(stats,indent=2))
print('FINISHED: five original weapon sources and eight GTA drawables',flush=True)
