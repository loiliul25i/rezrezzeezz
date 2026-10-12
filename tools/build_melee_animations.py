"""Author two original upper-body GTA clips, sampled with two-bone arm IK.

blender -b --python tools/build_melee_animations.py
Outputs a real YCD XML source, editable rig/action and pose preview scenes.
The bind transforms are a separately licensed GTA compatibility reference.
"""
from pathlib import Path
from math import radians, acos, sqrt, sin, cos
from mathutils import Matrix, Vector, Quaternion
import bpy
import json
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'sources/animations';OUT.mkdir(parents=True,exist_ok=True)
DATA=json.loads((ROOT/'sources/animation_bind.json').read_text())['bones']
BONES={b['name']:b for b in DATA}
REST={};LOCAL={}
for b in DATA:
    pos=Vector(b['translation']);x,y,z,w=b['rotation'];q=Quaternion((w,x,y,z)).normalized()
    local=Matrix.Translation(pos)@q.to_matrix().to_4x4();LOCAL[b['name']]=local
    REST[b['name']]=(REST[DATA[b['parent']]['name']]@local) if b['parent']>=0 else local

def interpolate(keys,t):
    for i in range(len(keys)-1):
        a,b=keys[i],keys[i+1]
        if t<=b[0]:
            s=max(0,min(1,(t-a[0])/(b[0]-a[0])));s=s*s*(3-2*s)
            pos=Vector(a[1]).lerp(Vector(b[1]),s)
            return pos,a[2]+s*(b[2]-a[2]),a[3]+s*(b[3]-a[3]),a[4]+s*(b[4]-a[4])
    return Vector(keys[-1][1]),*keys[-1][2:]

def aim_bone(name,origin,direction):
    restq=REST[name].to_quaternion()
    xaxis=restq@Vector((1,0,0))
    q=xaxis.rotation_difference(direction.normalized())@restq
    return Matrix.Translation(origin)@q.to_matrix().to_4x4()

def arm(side,target,hand_rotation,world):
    upper='SKEL_'+side+'_UpperArm';fore='SKEL_'+side+'_Forearm';hand='SKEL_'+side+'_Hand'
    parent=DATA[BONES[upper]['parent']]['name'];origin=world[parent]@Vector(BONES[upper]['translation'])
    a=Vector(BONES[fore]['translation']).length;b=Vector(BONES[hand]['translation']).length
    delta=target-origin;distance=max(.03,min(delta.length,a+b-.003));axis=delta.normalized()
    target=origin+axis*distance
    along=(a*a-b*b+distance*distance)/(2*distance)
    bend=Vector((.65 if origin.x>0 else -.65,-.50,-.65));bend=(bend-axis*bend.dot(axis)).normalized()
    elbow=origin+axis*along+bend*sqrt(max(0,a*a-along*along))
    world[upper]=aim_bone(upper,origin,elbow-origin)
    world[fore]=aim_bone(fore,elbow,target-elbow)
    world[hand]=Matrix.Translation(target)@hand_rotation.to_matrix().to_4x4()
    return (target-(origin+delta)).length

def pose(kind,t,keys):
    root,yaw,pitch,torso=interpolate(keys,t)
    root.x=-root.x;yaw=-yaw;torso=-torso
    world={};tracked={}
    # Local +X of the torso is its longitudinal axis in the GTA bind frame.
    for bone in DATA:
        name=bone['name'];parent=DATA[bone['parent']]['name'] if bone['parent']>=0 else None
        local=LOCAL[name].copy()
        if name in ('SKEL_Spine0','SKEL_Spine1','SKEL_Spine2'):
            local=local@Quaternion((1,0,0),radians(torso/3)).to_matrix().to_4x4()
        world[name]=(world[parent]@local) if parent else local
    # Weapon blade points forward; shaft is +Z in the authored model.
    frame=Matrix(((0,-1,0),(1,0,0),(0,0,1))).to_quaternion()
    weaponq=Quaternion((0,0,1),radians(yaw))@Quaternion((1,0,0),radians(pitch))@frame
    gripq=Quaternion((.778,.619,-.106,.018)).normalized()
    rightq=weaponq@gripq
    right_target=root+weaponq@Vector((-.045,.002,.012))-rightq@Vector(BONES['PH_R_Hand']['translation'])
    right_error=arm('R',right_target,rightq,world)
    left_target=root+weaponq@Vector((0,0,.26)) if kind=='scythe' else Vector((.24,.18,.14))
    leftq=(weaponq@gripq) if kind=='scythe' else REST['SKEL_L_Hand'].to_quaternion()
    if kind=='scythe':left_target-=leftq@Vector(BONES['PH_L_Hand']['translation'])
    left_error=arm('L',left_target,leftq,world)
    # Restore all dependent joints after solving the arms, and curl the fingers.
    for bone in DATA:
        name=bone['name'];parent=DATA[bone['parent']]['name'] if bone['parent']>=0 else None
        if name.startswith(('SKEL_R_Finger','SKEL_L_Finger')):
            local=LOCAL[name]@Quaternion((0,0,1),-.62 if '_R_' in name else .62).to_matrix().to_4x4()
            world[name]=world[parent]@local
        elif parent and name not in ('SKEL_R_UpperArm','SKEL_R_Forearm','SKEL_R_Hand','SKEL_L_UpperArm','SKEL_L_Forearm','SKEL_L_Hand') and ('ForeArm' in name or name.startswith(('IK_','PH_','RB_','MH_'))):
            world[name]=world[parent]@LOCAL[name]
    names=['SKEL_Spine0','SKEL_Spine1','SKEL_Spine2','SKEL_Spine3','SKEL_L_Clavicle','SKEL_R_Clavicle',
           'SKEL_R_UpperArm','SKEL_R_Forearm','SKEL_R_Hand','SKEL_L_UpperArm','SKEL_L_Forearm','SKEL_L_Hand']
    names += [b['name'] for b in DATA if b['name'].startswith(('SKEL_R_Finger','SKEL_L_Finger'))]
    for name in names:
        parent=DATA[BONES[name]['parent']]['name']
        tracked[name]=(world[parent].inverted()@world[name]).to_quaternion().normalized()
    return tracked,world,root,weaponq,max(right_error,left_error)

def element(parent,tag,text=None,**attrs):
    item=E.SubElement(parent,tag,{k:str(v) for k,v in attrs.items()})
    if text is not None:item.text=str(text)
    return item

SPECS=[
 {'name':'axe_chop','kind':'axe','duration':1.10,'contact':.56,
  'keys':[(0,(.19,.27,.20),-8,-8,-5),(.28,(.29,.02,.48),-25,56,-18),
          (.56,(.17,.42,.17),14,-62,16),(.76,(.08,.35,.12),28,-72,20),(1.10,(.19,.27,.20),-8,-8,-5)]},
 {'name':'scythe_sweep','kind':'scythe','duration':1.40,'contact':.68,
  'keys':[(0,(.16,.24,.22),-8,-8,-5),(.36,(.22,.02,.43),-45,25,-35),
          (.68,(-.06,.29,.24),20,-55,24),(.90,(-.14,.22,.18),45,-62,38),(1.40,(.16,.24,.22),-8,-8,-5)]}
]
root=E.Element('ClipDictionary');clips=element(root,'Clips');animations=element(root,'Animations');summary=[]
samples={}
for spec in SPECS:
    name=spec['name'];duration=spec['duration'];frame_count=round(duration*60)+1
    frames=[pose(spec['kind'],i/60,spec['keys']) for i in range(frame_count)]
    samples[name]=frames
    ci=element(clips,'Item');element(ci,'Hash',name);element(ci,'Name','pack:/hw_melee_v2/'+name+'.clip')
    element(ci,'Type',value='Animation');element(ci,'Unknown30',value=0);element(ci,'Tags');element(ci,'Properties')
    element(ci,'AnimationHash',name+'_anim');element(ci,'StartTime',value=0);element(ci,'EndTime',value=duration);element(ci,'Rate',value=1)
    anim=element(animations,'Item');element(anim,'Hash',name+'_anim');element(anim,'Unknown10',value=0)
    element(anim,'FrameCount',value=frame_count);element(anim,'SequenceFrameLimit',value=127);element(anim,'Duration',value=duration)
    element(anim,'Unknown1C','hash_00000000');boneids=element(anim,'BoneIds')
    sequence=element(element(anim,'Sequences'),'Item');element(sequence,'Hash',name+'_sequence');element(sequence,'FrameCount',value=frame_count)
    data=element(sequence,'SequenceData')
    for namebone in frames[0][0]:
        bone=element(boneids,'Item');element(bone,'BoneId',value=BONES[namebone]['tag']);element(bone,'Track',value=1);element(bone,'Unk0',value=0)
        qs=[frame[0][namebone].copy() for frame in frames]
        for i in range(1,len(qs)):
            if qs[i-1].dot(qs[i])<0:qs[i].negate()
        channels=element(element(data,'Item'),'Channels')
        for component in ('x','y','z','w'):
            item=element(channels,'Item');element(item,'Type',value='RawFloat')
            element(item,'Values','\n'+' '.join(f'{getattr(q,component):.8g}' for q in qs)+'\n')
    summary.append(dict(clip=name,kind=spec['kind'],frames=frame_count,tracks=len(frames[0][0]),duration=duration,contact=spec['contact'],max_hand_reach_error=round(max(f[4] for f in frames),5)))
    print('AUTHORED',name,summary[-1],flush=True)
E.indent(root);E.ElementTree(root).write(ROOT/'sources/cwxml/hw_melee_v2.ycd.xml',encoding='UTF-8',xml_declaration=True)
(OUT/'animation_specs.json').write_text(json.dumps(summary,indent=2))
(OUT/'preview_samples.json').write_text(json.dumps({name:[{'root':list(frame[2]),'rotation':[frame[3].x,frame[3].y,frame[3].z,frame[3].w]} for frame in frames] for name,frames in samples.items()}))

# Editable Blender rig/actions with the native transforms mapped into Blender frames.
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.armature_add(enter_editmode=True);rig=bpy.context.object;rig.name='HW_GTA_melee_rig'
rig.data.edit_bones.remove(rig.data.edit_bones[0])
for bone in DATA:
    name=bone['name'];w=REST[name];eb=rig.data.edit_bones.new(name);eb.head=w.translation
    eb.tail=w@Vector((.065,0,0));eb.align_roll(w.to_3x3()@Vector((0,0,1)))
    if bone['parent']>=0:eb.parent=rig.data.edit_bones[DATA[bone['parent']]['name']]
bpy.ops.object.mode_set(mode='OBJECT')
correction={name:REST[name].inverted()@rig.data.bones[name].matrix_local for name in REST}
for spec in SPECS:
    action=bpy.data.actions.new(spec['name']);rig.animation_data_create();rig.animation_data.action=action;action.use_fake_user=True
    for index,frame in enumerate(samples[spec['name']]):
        bpy.context.scene.frame_set(index+1)
        for bone in DATA:
            name=bone['name'];pb=rig.pose.bones[name];pb.rotation_mode='QUATERNION'
            target=frame[1][name]@correction[name]
            if bone['parent']>=0:
                parent=DATA[bone['parent']]['name']
                desired_local=(frame[1][parent]@correction[parent]).inverted()@target
                rest_local=rig.data.bones[parent].matrix_local.inverted()@rig.data.bones[name].matrix_local
            else:
                desired_local=target;rest_local=rig.data.bones[name].matrix_local
            pb.matrix_basis=rest_local.inverted()@desired_local
            if name in frame[0]:
                pb.keyframe_insert(data_path='rotation_quaternion',frame=index+1)
                pb.keyframe_insert(data_path='location',frame=index+1)
    rig['clip_'+spec['name']]=spec['duration']
bpy.context.scene.render.fps=60;bpy.context.scene.frame_end=85
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hw_melee_animations.blend'))
print('FINISHED two original animated strikes and editable actions',flush=True)
