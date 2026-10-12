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
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))

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

MATERIALS=json.loads((SRC/'materials.json').read_text())

def material(index):
    info=MATERIALS[index];name=info['name']
    m=bpy.data.materials.new(name);m.use_nodes=True
    nodes=m.node_tree.nodes;p=nodes.get('Principled BSDF')
    for suffix,socket in [('d','Base Color'),('n',None),('s',None)]:
        tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(SRC/'textures'/('hw_'+name+'_'+suffix+'.png')),check_existing=True)
        if suffix!='d':tex.image.colorspace_settings.name='Non-Color'
        if suffix=='d':
            m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color'])
            if info['emissive']:
                m.node_tree.links.new(tex.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=.7
        if suffix=='n':
            normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.35
            m.node_tree.links.new(tex.outputs['Color'],normal.inputs['Color']);m.node_tree.links.new(normal.outputs['Normal'],p.inputs['Normal'])
    p.inputs['Metallic'].default_value=info['metallic'];p.inputs['Roughness'].default_value=info['roughness']
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
        modifier.segments = 4
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
    if kind=='scythe':bones.append(('Gun_GripL',18302,0,Vector((0,0,.26)),Quaternion()))
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
        mesh=obj.data;mesh.calc_loop_triangles();mesh.calc_tangents(uvmap=mesh.uv_layers.active.name)
        normal_matrix=obj.matrix_world.to_3x3().inverted().transposed()
        material_index=obj['finish'];bone=obj['bone_index'] if bones else 0
        vertices=groups.setdefault(material_index,[])
        for tri in mesh.loop_triangles:
            a,b,c=(mesh.vertices[i].co for i in tri.vertices)
            face_normal=(b-a).cross(c-a)
            if face_normal.length_squared<1e-20:continue
            for loop_index in tri.loops:
                loop=mesh.loops[loop_index]
                p=obj.matrix_world @ mesh.vertices[loop.vertex_index].co-offset
                local_normal=mesh.corner_normals[loop_index].vector
                if local_normal.length_squared<.5:local_normal=face_normal.normalized()
                n=(normal_matrix @ local_normal).normalized()
                uv=mesh.uv_layers.active.data[loop_index].uv
                tangent=(normal_matrix @ loop.tangent).normalized()
                vertices.append((p,n,(uv.x,1-uv.y),bone,(*tangent,loop.bitangent_sign)))
    allpoints=[row[0] for rows in groups.values() for row in rows]
    low=Vector(tuple(min(p[i] for p in allpoints) for i in range(3)))
    high=Vector(tuple(max(p[i] for p in allpoints) for i in range(3)))
    root=E.Element('Drawable');element(root,'Name',name)
    vec(root,'BoundingSphereCenter',(low+high)/2);element(root,'BoundingSphereRadius',value=f'{(high-low).length/2:.8g}')
    vec(root,'BoundingBoxMin',low);vec(root,'BoundingBoxMax',high)
    for lod in ['High','Med','Low','Vlow']:
        element(root,'LodDist'+lod,value=9998);element(root,'Flags'+lod,value=1 if lod=='High' else 0)
    shaders=element(element(root,'ShaderGroup'),'Shaders');used=sorted(groups)
    for mat in used:
        info=MATERIALS[mat];material_name=info['name'];emissive=info['emissive']
        shader=element(shaders,'Item');preset='emissive' if emissive else 'normal_spec'
        element(shader,'Name',preset);element(shader,'FileName',preset+'.sps');element(shader,'RenderBucket',value=0)
        params=element(shader,'Parameters')
        for sampler,suffix in ([('DiffuseSampler','d')] if emissive else [('DiffuseSampler','d'),('BumpSampler','n'),('SpecSampler','s')]):
            item=element(params,'Item',name=sampler,type='Texture');element(item,'Name','hw_'+material_name+'_'+suffix)
        scalars={'emissiveMultiplier':.7} if emissive else {'HardAlphaBlend':1,'useTessellation':0,'wetnessMultiplier':.15,'bumpiness':.35,'specularIntensityMult':.85,'specularFalloffMult':110 if info['metallic']>.5 else 35,'specularFresnel':.65}
        for key,value in scalars.items():element(params,'Item',name=key,type='Vector',x=value,y=0,z=0,w=0)
        if not emissive:element(params,'Item',name='specMapIntMask',type='Vector',x=1,y=0,z=0,w=0)
        else:element(params,'Item',name='matMaterialColorScale',type='Vector',x=1,y=0,z=0,w=1)
    if bones:put_skeleton(root,bones)
    model=element(element(root,'DrawableModelsHigh'),'Item')
    for key,val in [('RenderMask',255),('Flags',1 if bones else 0),('HasSkin',1 if bones else 0),('BoneIndex',0),('Unknown1',len(bones) if bones else 0)]:element(model,key,value=val)
    geometries=element(model,'Geometries');geocount=0;vertices_count=0
    for shader_index,mat in enumerate(used):
        allrows=groups[mat]
        # Split before 16-bit index overflow. Dedupe loop tuples within each chunk.
        for start in range(0,len(allrows),54000):
            lookup={};rows=[];indices=[]
            for p,n,uv,bone,tangent in allrows[start:start+54000]:
                key=tuple(round(v,7) for v in (*p,*n,*uv,bone,*tangent))
                if key not in lookup:lookup[key]=len(rows);rows.append((p,n,uv,bone,tangent))
                indices.append(lookup[key])
            assert len(rows)<65536
            geocount+=1;vertices_count+=len(rows)
            g=element(geometries,'Item');element(g,'ShaderIndex',value=shader_index)
            vec(g,'BoundingBoxMin',tuple(min(r[0][i] for r in rows) for i in range(3)),0)
            vec(g,'BoundingBoxMax',tuple(max(r[0][i] for r in rows) for i in range(3)),0)
            if bones:element(g,'BoneIDs',', '.join(str(i) for i in range(len(bones))))
            vb=element(g,'VertexBuffer');element(vb,'Flags',value=0);layout=element(vb,'Layout',type='GTAV1')
            keys=['Position']+(['BlendWeights','BlendIndices'] if bones else [])+['Normal','Colour0','TexCoord0','Tangent']
            for key in keys:element(layout,key)
            lines=[]
            for p,n,uv,bone,tangent in rows:
                parts=[' '.join(f'{v:.8g}' for v in p)]
                if bones:parts+=['255 0 0 0',f'{bone} 0 0 0']
                parts+=[' '.join(f'{v:.8g}' for v in n),'255 255 255 255',' '.join(f'{v:.8g}' for v in uv),' '.join(f'{v:.8g}' for v in tangent)]
                lines.append('   '.join(parts))
            element(vb,'Data','\n'+'\n'.join(lines)+'\n');element(element(g,'IndexBuffer'),'Data','\n'+' '.join(str(i) for i in indices)+'\n')
    put_collision(root,low,high);E.indent(root)
    E.ElementTree(root).write(XML/(name+'.ydr.xml'),encoding='UTF-8',xml_declaration=True)
    return {'model':name,'triangles':len(allpoints)//3,'vertices':vertices_count,'geometries':geocount,'materials':len(used),'bones':len(bones) if bones else 0,'smooth_normals':True,'tangent_space':True,'min':list(low),'max':list(high)}

def add_lods(model,selected,bones,offset=Vector((0,0,0))):
    high_file=XML/(model+'.ydr.xml');root=E.parse(high_file).getroot()
    high_names=[n.findtext("Parameters/Item[@name='DiffuseSampler']/Name") for n in root.findall('ShaderGroup/Shaders/Item')]
    counts={}
    for level,ratio in [('Medium',.40),('Low',.14)]:
        copies=[]
        try:
            for original in selected:
                duplicate=original.copy();duplicate.data=original.data.copy();bpy.context.collection.objects.link(duplicate)
                copies.append(duplicate);bpy.context.view_layer.objects.active=duplicate
                if len(duplicate.data.polygons)>120 and duplicate['finish'] not in (2,3):
                    modifier=duplicate.modifiers.new('Shipping LOD','DECIMATE');modifier.ratio=ratio
                    bpy.ops.object.modifier_apply(modifier=modifier.name)
                tri=duplicate.modifiers.new('LOD ngons','TRIANGULATE');tri.min_vertices=5
                if hasattr(tri,'keep_custom_normals'):tri.keep_custom_normals=True
                bpy.ops.object.modifier_apply(modifier=tri.name)
            name=model+'__'+level.lower();info=export_xml(name,copies,bones,offset);counts[level]=info['triangles']
            lod_file=XML/(name+'.ydr.xml');lod_root=E.parse(lod_file).getroot()
            names=[n.findtext("Parameters/Item[@name='DiffuseSampler']/Name") for n in lod_root.findall('ShaderGroup/Shaders/Item')]
            node=lod_root.find('DrawableModelsHigh');node.tag='DrawableModels'+level
            for index in node.findall('.//ShaderIndex'):index.set('value',str(high_names.index(names[int(index.get('value'))])))
            root.append(node);lod_file.unlink()
        finally:
            for duplicate in copies:bpy.data.objects.remove(duplicate,do_unlink=True)
    for key,value in [('LodDistHigh',35),('LodDistMed',90),('LodDistLow',250),('FlagsMed',1),('FlagsLow',1)]:root.find(key).set('value',str(value))
    E.indent(root);E.ElementTree(root).write(high_file,encoding='UTF-8',xml_declaration=True)
    return counts

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
    for poly in mesh.polygons:poly.use_smooth=True
    mesh.set_sharp_from_angle(angle=.65)
    bpy.context.view_layer.objects.active=obj
    modifier=obj.modifiers.new('Area-weighted smooth shading','WEIGHTED_NORMAL');modifier.keep_sharp=True;modifier.weight=50
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    triangulate=obj.modifiers.new('Triangulate ngons for tangent export','TRIANGULATE');triangulate.min_vertices=5
    if hasattr(triangulate,'keep_custom_normals'):triangulate.keep_custom_normals=True
    bpy.ops.object.modifier_apply(modifier=triangulate.name)
    repaired=[]
    for index,normal in enumerate(mesh.corner_normals):
        value=normal.vector.copy()
        if value.length_squared<.5:
            value=mesh.vertices[mesh.loops[index].vertex_index].normal.copy()
            if value.length_squared<.5:value=Vector((0,0,1))
        repaired.append(value.normalized())
    mesh.normals_split_custom_set(repaired)
    # A UV island per projection face; no coordinate modulo and no colour atlas.
    while mesh.uv_layers:mesh.uv_layers.remove(mesh.uv_layers[0])
    layer=mesh.uv_layers.new(name='UVMap');layer.active_render=True
    coords=[v.co for v in mesh.vertices]
    low=[min(p[i] for p in coords) for i in range(3)];high=[max(p[i] for p in coords) for i in range(3)]
    span=[max(.000001,high[i]-low[i]) for i in range(3)]
    for poly in mesh.polygons:
        axis=max(range(3),key=lambda i:abs(poly.normal[i]))
        axes=[i for i in range(3) if i!=axis]
        for index in poly.loop_indices:
            point=mesh.vertices[mesh.loops[index].vertex_index].co
            u=(point[axes[0]]-low[axes[0]])/span[axes[0]];v=(point[axes[1]]-low[axes[1]])/span[axes[1]]
            layer.data[index].uv=(.02+.96*u,.02+.96*v)

def render(name,selected):
    pts=[o.matrix_world@v.co for o in selected for v in o.data.vertices]
    low=Vector(tuple(min(p[i] for p in pts) for i in range(3)));high=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    center=(low+high)/2;width=high.x-low.x;height=high.z-low.z;span=max(width,height)
    bpy.ops.object.camera_add(location=center+Vector((span*.12,-span*2.5,span*.10)))
    camera=bpy.context.object;camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO';camera.data.ortho_scale=max(width,height*1.5)*1.20
    scene=bpy.context.scene;scene.camera=camera
    scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=False
    scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True
    scene.world.color=(.025,.025,.025)
    scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
    for loc,power,colour in [(Vector((-.6,-1.5,1.5)),80,(.72,.82,1)),(Vector((.8,1,1)),110,(.9,.6,.35)),(Vector((0,-1,-.5)),35,(.6,.65,.85))]:
        bpy.ops.object.light_add(type='AREA',location=center+loc*max(.4,span))
        light=bpy.context.object;light.data.energy=power*max(.18,span)**2;light.data.shape='DISK';light.data.size=max(.4,span)
        light.data.color=colour;light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(PREVIEW/(name+'.png'));bpy.ops.render.render(write_still=True)
    # A separate actual render for square inventory icons; no concept-image cutouts.
    scene.render.resolution_x=256;scene.render.resolution_y=256
    camera.data.ortho_scale=max(width,height)*1.20
    scene.render.filepath=str(ICONS/(name+'.png'));bpy.ops.render.render(write_still=True)

import model_design_v2
BUILDERS=model_design_v2.builders(globals())
SPECS=list(zip(['WEAPON_HW_EMBER','WEAPON_HW_REVENANT','WEAPON_HW_PUMPKIN','WEAPON_HW_REAPER_AXE','WEAPON_HW_SOUL_SCYTHE'],
               ['w_pi_hw_ember','w_ar_hw_revenant','w_ar_hw_pumpkin','w_me_hw_reaper','w_me_hw_soul'],
               ['pistol','ar','ak','axe','scythe'],BUILDERS))
stats=[]
bpy.context.preferences.filepaths.save_version=0
for weapon,model,kind,builder in SPECS:
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    objects=[];mats=[material(i) for i in range(len(MATERIALS))]
    muzzle,clip=builder();bpy.context.view_layer.update()
    for obj in objects:uv_map(obj)
    bones=bones_for(kind,muzzle,clip)
    main=[o for o in objects if not o['magazine']]
    stats.append(export_xml(model,main,bones))
    stats[-1]['lod_triangles']=add_lods(model,main,bones)
    magazines=[o for o in objects if o['magazine']]
    if magazines:
        for obj in magazines:obj['bone_index']=0
        mag_bones=[('AAPClip',0,-1,Vector((0,0,0)),Quaternion())]
        stats.append(export_xml(model+'_mag',magazines,mag_bones,offset=Vector(clip)))
        stats[-1]['lod_triangles']=add_lods(model+'_mag',magazines,mag_bones,Vector(clip))
    rig=make_armature(model,bones,main)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects+[rig]:obj.select_set(True)
    bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.gltf(filepath=str(SRC/'glb'/(model+'.glb')),export_format='GLB',use_selection=True)
    for image in bpy.data.images:
        if image.source=='FILE':image.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(SRC/'blend'/(model+'.blend')))
    if '--no-render' not in sys.argv:render(weapon,objects)
    print('BUILT',weapon,flush=True)
(SRC/'model_stats.json').write_text(json.dumps(stats,indent=2))
print('FINISHED: five original weapon sources and eight GTA drawables',flush=True)
