"""Render the authored Blender actions on an original simple mannequin (not gameplay)."""
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
import bpy
import json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'previews/animation_frames';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sources/animations/hw_melee_animations.blend'))
rig=bpy.data.objects['HW_GTA_melee_rig']
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.scene.frame_set(1)

mat=bpy.data.materials.new('Mannequin neutral');mat.use_nodes=True
p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.16,.21,.28,1);p.inputs['Roughness'].default_value=.45
def capsule(name,a,b,radius,bone):
    a,b=Vector(a),Vector(b);direction=b-a
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=1,location=(a+b)/2)
    o=bpy.context.object;o.name=name;o.scale=(radius,radius,max(radius,direction.length/2+radius*.4))
    o.rotation_euler=direction.to_track_quat('Z','Y').to_euler()
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat)
    for f in o.data.polygons:f.use_smooth=True
    o.parent=rig;g=o.vertex_groups.new(name=bone);g.add(list(range(len(o.data.vertices))),1,'REPLACE')
    modifier=o.modifiers.new('Mannequin rig','ARMATURE');modifier.object=rig
for side in ('L','R'):
    for part,child,radius in [('UpperArm','Forearm',.046),('Forearm','Hand',.038),('Thigh','Calf',.072),('Calf','Foot',.052)]:
        name='SKEL_'+side+'_'+part;end='SKEL_'+side+'_'+child
        capsule(name,rig.data.bones[name].head_local,rig.data.bones[end].head_local,radius,name)
    hand='SKEL_'+side+'_Hand';position=rig.data.bones[hand].head_local
    palm=rig.data.bones['PH_'+side+'_Hand'].head_local
    capsule('Hand',palm-Vector((0,.018,0)),palm+Vector((0,.018,0)),.033,hand)
capsule('Torso',rig.data.bones['SKEL_Spine1'].head_local,rig.data.bones['SKEL_Spine3'].head_local,.135,'SKEL_Spine2')
capsule('Hips',(-.095,0,-.02),(.095,0,-.02),.092,'SKEL_Pelvis')
head=rig.data.bones['SKEL_Head'].head_local
capsule('Head',head,head+Vector((0,0,.105)),.084,'SKEL_Head')
bpy.ops.object.camera_add(location=(2.8,3.5,1.6));camera=bpy.context.object
camera.rotation_euler=(Vector((0,.18,.18))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO';camera.data.ortho_scale=2.70
scene=bpy.context.scene;scene.camera=camera;scene.render.engine='CYCLES';scene.cycles.samples=16
scene.cycles.use_denoising=False;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.world.color=(.07,.07,.07)
for loc,energy in [((1.5,1.8,2.5),220),((-1.5,-1,1),350)]:
    bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.data.energy=energy;light.data.size=2
    light.rotation_euler=(Vector((0,0,.1))-light.location).to_track_quat('-Z','Y').to_euler()
samples=json.loads((ROOT/'sources/animations/preview_samples.json').read_text())
for clip,model in [('axe_chop','w_me_hw_reaper'),('scythe_sweep','w_me_hw_soul')]:
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ROOT/'sources/glb'/(model+'.glb')))
    imported=[o for o in bpy.data.objects if o not in before];meshes=[o for o in imported if o.type=='MESH']
    transforms={}
    for o in meshes:
        bpy.context.view_layer.objects.active=o
        for modifier in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
        world=o.matrix_world.copy();o.parent=None;o.matrix_world=world;transforms[o]=world
    rig.animation_data.action=bpy.data.actions[clip]
    frames=samples[clip];indices=sorted(set(round(i*(len(frames)-1)/13) for i in range(14)))
    for ordinal,index in enumerate(indices):
        scene.frame_set(index+1);bpy.context.view_layer.update()
        sample=frames[index];x,y,z,w=sample['rotation'];weapon=Matrix.Translation(Vector(sample['root']))@Quaternion((w,x,y,z)).to_matrix().to_4x4()
        for o,rest in transforms.items():o.matrix_world=weapon@rest
        scene.render.filepath=str(OUT/(clip+'_'+str(ordinal).zfill(2)+'.png'));bpy.ops.render.render(write_still=True)
    for o in imported:
        if o.name in bpy.data.objects:bpy.data.objects.remove(o,do_unlink=True)
print('FINISHED authored-animation preview frames (Blender, not FiveM)',flush=True)
