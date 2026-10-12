"""Hand-authored curved weapon geometry, inspired by the supplied Halloween reference.

Lofted grips and magazines, hollow machined parts, smooth blade profiles,
sculpted skulls, real filigree relief and helical fabric/leather wraps.
"""
import bpy
from math import sin, cos, pi, sqrt
from mathutils import Vector

G = None
METAL, STEEL, EMBER, SOUL, WOOD, LEATHER, BONE, RECESS, ENGRAVING, CLOTH, GLASS = range(11)

def obj(name, vertices, faces, material=METAL, bone=2, bevel=0):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
    return G['finish'](ob,name,material,bone,bevel)

def box(name,loc,size,material=METAL,bevel=.0015,rotation=0,bone=2):
    return G['box'](name,loc,size,material,bevel,rotation,bone)

def profile(name,points,depth,material=METAL,y=0,bone=2,bevel=.0015):
    return G['polygon'](name,points,depth,material,y,bone,bevel)

def cyl(name,loc,radius,length,material=METAL,axis='X',vertices=48,bone=2):
    return G['cylinder'](name,loc,radius,length,material,axis,vertices,bone)

def sphere(name,loc,size,material=METAL,bone=2):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,radius=1,location=loc)
    ob=bpy.context.object;ob.scale=size
    return G['finish'](ob,name,material,bone)

def path(name,points,radius,material=METAL,bone=2,closed=False):
    curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.resolution_u=3 if radius>.0015 else 2
    curve.bevel_depth=radius;curve.bevel_resolution=2 if radius>.0015 else 1
    spline=curve.splines.new('BEZIER');spline.bezier_points.add(len(points)-1)
    for point,coordinate in zip(spline.bezier_points,points):
        point.co=coordinate;point.handle_left_type='AUTO';point.handle_right_type='AUTO'
    spline.use_cyclic_u=closed;curve.use_fill_caps=True
    ob=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(ob)
    bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    bpy.ops.object.convert(target='MESH');ob=bpy.context.object
    return G['finish'](ob,name,material,bone)

def boolean(target,cutter):
    bpy.context.view_layer.objects.active=target
    modifier=target.modifiers.new('True open recess','BOOLEAN');modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutter
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter,do_unlink=True)

def cutbox(target,loc,size,rounding=.003):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);cutter=bpy.context.object;cutter.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if rounding:
        b=cutter.modifiers.new('Round opening','BEVEL');b.width=rounding;b.segments=4
        bpy.ops.object.modifier_apply(modifier=b.name)
    boolean(target,cutter)

def roundrect(width,height,radius,steps=5):
    points=[]
    for cx,cy,start in [(width/2-radius,height/2-radius,0),(-width/2+radius,height/2-radius,pi/2),
                        (-width/2+radius,-height/2+radius,pi),(width/2-radius,-height/2+radius,3*pi/2)]:
        for k in range(steps+1):
            angle=start+k/steps*pi/2
            points.append((cx+radius*cos(angle),cy+radius*sin(angle)))
    return points

def loft(name,rings,material=METAL,bone=2):
    """rings: (center xyz, width in X, depth in Y); axis follows Z."""
    vertices=[];faces=[];n=24
    for center,width,depth in rings:
        for x,y in roundrect(width,depth,min(width,depth)*.24):vertices.append((center[0]+x,center[1]+y,center[2]))
    for k in range(len(rings)-1):
        for j in range(n):faces.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
    faces += [tuple(reversed(range(n))),tuple(range((len(rings)-1)*n,len(rings)*n))]
    return obj(name,vertices,faces,material,bone)

def wrap(name,center,radius,length,turns,material=LEATHER,axis='Z',width=.012):
    vertices=[];faces=[];segments=max(36,int(turns*28));cx,cy,cz=center
    for i in range(segments+1):
        t=i/segments;angle=t*turns*2*pi
        for radial,along in [(0,-width/2),(.0018,-width/2),(.0018,width/2),(0,width/2)]:
            p=Vector(((radius+radial)*cos(angle),(radius+radial)*sin(angle),length*(t-.5)+along))
            if axis=='X':p=Vector((p.z,p.x,p.y))
            vertices.append(tuple(p+Vector(center)))
    for i in range(segments):
        for j in range(4):faces.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
    return obj(name,vertices,faces,material)

def torus(name,loc,major,minor,material=METAL,axis='Z',bone=2):
    bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=40,minor_segments=8,location=loc)
    ob=bpy.context.object
    if axis=='X':ob.rotation_euler.y=pi/2
    if axis=='Y':ob.rotation_euler.x=pi/2
    return G['finish'](ob,name,material,bone)

def screw(x,z,y,r=.0025,bone=2):
    for side in (-1,1):
        cyl('Recessed screw',(x,side*y,z),r,.0015,STEEL,'Y',12,bone)
        box('Screw slot',(x,side*(y+.0008),z),(r*1.2,.0005,r*.20),RECESS,.0001,bone=bone)

def ornament(x,z,y,scale=.016,bone=2,material=ENGRAVING):
    # Each relief follows a smooth spiral and leaf profile, not straight sticks.
    for side in (-1,1):
        for sign in (-1,1):
            pts=[]
            for i in range(22):
                t=i/21;angle=t*2*pi*1.12;r=scale*(1-t*.86)
                pts.append((x+sign*r*cos(angle),side*y,z+r*sin(angle)))
            path('Engraved scroll',pts,scale*.035,material,bone)
            path('Filigree branch',[(x,side*y,z-scale*.5),(x+sign*scale*.9,side*y,z-scale),
                                  (x+sign*scale*1.4,side*y,z-scale*.5)],scale*.025,material,bone)

def pumpkin(x,z,y,r=.015,bone=2):
    for side in (-1,1):
        sy=side*y
        sphere('Pumpkin carved medallion',(x,sy,z),(r,.0019,r*.82),ENGRAVING,bone)
        for eye in (-1,1):
            ex=x+eye*r*.32
            profile('Pumpkin ember eye',[(ex-r*.18,z+r*.04),(ex+r*.18,z+r*.04),(ex,z+r*.35)],.001,EMBER,sy+side*.0025,bone,.0002)
        profile('Pumpkin ember grin',[(x-r*.54,z-r*.15),(x-r*.26,z-r*.44),(x-r*.05,z-r*.22),(x+r*.07,z-r*.42),
                    (x+r*.48,z-r*.18),(x+r*.30,z-r*.54),(x-r*.31,z-r*.54)],.001,EMBER,sy+side*.0025,bone,.0002)
        path('Pumpkin ribs',[(x-r*.6,sy+side*.002,z-r*.5),(x-r*.77,sy+side*.002,z),(x-r*.5,sy+side*.002,z+r*.60)],r*.025,STEEL,bone)
        path('Pumpkin ribs',[(x+r*.6,sy+side*.002,z-r*.5),(x+r*.77,sy+side*.002,z),(x+r*.5,sy+side*.002,z+r*.60)],r*.025,STEEL,bone)

def bat(x,z,y,r=.028,bone=2):
    points=[(-1,0),(-.76,.4),(-.58,.18),(-.28,.15),(-.18,.46),(0,.15),(.18,.46),(.28,.15),(.58,.18),(.76,.4),(1,0),
            (.68,-.1),(.55,-.30),(.32,-.14),(0,-.35),(-.32,-.14),(-.55,-.30),(-.68,-.1)]
    for side in (-1,1):
        profile('Forged bat relief',[(x+a*r,z+b*r) for a,b in points],.0016,STEEL,side*y,bone,.0006)
        path('Bat soul spine',[(x-r*.15,side*(y+.001),z),(x,side*(y+.001),z+r*.14),(x+r*.15,side*(y+.001),z)],.0006,SOUL,bone)

def skull(center,r=.035,glow=SOUL,material=METAL):
    x,y,z=center
    head=sphere('Rounded skull cranium',(x,y,z),(r,r*.71,r*1.08),material)
    # Real concave sockets in the metal shell, with a dark backing and small light.
    for side in (-1,1):
        for eye in (-1,1):
            ex=x+eye*r*.36;ey=y+side*r*.65;ez=z+r*.08
            bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=1,location=(ex,ey,ez))
            cutter=bpy.context.object;cutter.scale=(r*.29,r*.32,r*.32)
            bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);boolean(head,cutter)
            sphere('Deep socket',(ex,ey-side*r*.13,ez),(r*.20,r*.045,r*.22),RECESS)
            sphere('Eye ember',(ex,ey-side*r*.10,ez),(r*.09,r*.025,r*.10),glow)
        sphere('Cheekbone',(x-r*.69,y+side*r*.45,z-r*.3),(r*.31,r*.2,r*.38),material)
        sphere('Cheekbone',(x+r*.69,y+side*r*.45,z-r*.3),(r*.31,r*.2,r*.38),material)
        profile('Nose cavity',[(x-r*.13,z-r*.07),(x+r*.13,z-r*.07),(x,z-r*.37)],.002,RECESS,y+side*r*.71,bevel=.0004)
        for tooth in range(6):
            box('Individual tooth',(x+(tooth-2.5)*r*.18,y+side*r*.43,z-r*.76),(r*.14,r*.30,r*(.26+.025*(tooth%2))),STEEL,.0012)
    sphere('Lower jaw',(x,y,z-r*.78),(r*.66,r*.50,r*.29),material)
    for sign in (-1,1):
        path('Skull brow',[(x+sign*r*.10,y-r*.64,z+r*.32),(x+sign*r*.35,y-r*.65,z+r*.45),(x+sign*r*.68,y-r*.4,z+r*.21)],r*.085,STEEL)
    return head

def muzzle(x,z,r=.013,length=.028,accent=STEEL):
    body=cyl('Machined hollow muzzle',(x-length/2,0,z),r,length,METAL)
    bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=r*.48,depth=length+.010,location=(x-length/2,0,z),rotation=(0,pi/2,0))
    boolean(body,bpy.context.object)
    torus('Muzzle crown',(x,0,z),r*.74,r*.10,STEEL,'X')
    for k in range(3):
        px=x-length*.82+k*length*.27
        cutbox(body,(px,0,z),(.003,r*2.6,.006),.001)
    return body

def pistol():
    profile('Contoured lower receiver',[(-.102,.004),(-.083,.022),(.099,.022),(.106,.005),(.045,-.001),(.021,-.017),(-.022,-.006),(-.064,-.001)],.034,METAL,bevel=.004)
    slide=profile('Rounded machined slide',[(-.110,.027),(-.107,.057),(-.092,.064),(.090,.064),(.111,.050),(.111,.029),(.052,.025)],.039,METAL,bone=3,bevel=.004)
    cutbox(slide,(.025,-.017,.053),(.047,.015,.010),.0018)
    cyl('Steel barrel',(.077,0,.038),.009,.080,STEEL)
    muzzle(.121,.038,.0095,.020,EMBER)
    loft('Rounded ivory grip',[(Vector((-.076,0,-.115)),.052,.034),(Vector((-.076,0,-.10)),.050,.035),
              (Vector((-.065,0,-.051)),.042,.036),(Vector((-.052,0,-.012)),.037,.036),(Vector((-.055,0,.002)),.041,.034)],BONE)
    for side in (-1,1):
        profile('Grip inset',[(-.082,-.102),(-.050,-.101),(-.043,-.025),(-.057,-.016),(-.072,-.054)],.002,BONE,side*.018,bevel=.003)
        for x in [-.097,-.089,-.081,-.073,.061,.070,.079,.088]:
            box('Milled slide flute',(x,side*.020,.045),(.003,.002,.024),RECESS,.001,bone=3)
        path('Ember edge',[(-.103,side*.021,.061),(.044,side*.021,.061),(.106,side*.021,.050)],.00065,EMBER,3)
    # Curved, closed trigger guard and a curved trigger, not a rectangular frame.
    path('Rounded trigger guard',[(-.039,-.001,-.004),(.023,-.001,-.003),(.034,-.001,-.027),(.008,-.001,-.039),(-.032,-.001,-.035),(-.039,-.001,-.004)],.0027,METAL,closed=True)
    path('Curved trigger',[(-.009,0,-.007),(-.003,0,-.019),(-.009,0,-.029)],.0022,ENGRAVING,4)
    for x in [-.091,.091]:
        box('Rear and front sight',(x,0,.069),(.012,.013,.010),METAL,.002,bone=3)
        sphere('Night sight',(x,-.007,.072),(.002,.001,.002),EMBER,3)
    for x,z in [(-.068,-.030),(-.084,-.098),(-.057,.020)]:screw(x,z,.020,.002,3 if z>0 else 2)
    pumpkin(-.022,.045,.021,.011,3);pumpkin(-.065,-.065,.020,.014)
    for x,z,r in [(.021,.044,.009),(-.063,.045,.010),(-.072,-.088,.011),(-.054,-.039,.011)]:ornament(x,z,.021,r,3 if z>0 else 2)
    profile('Beavertail',[(-.103,.007),(-.128,.014),(-.132,.006),(-.109,-.003)],.026,METAL,bevel=.002)
    cyl('Hammer pivot',(-.108,0,.028),.004,.027,STEEL,'Y')
    profile('Hammer',[(-.111,.028),(-.127,.047),(-.140,.043),(-.124,.022)],.009,METAL,bevel=.001)
    start=len(G['objects'])
    loft('Ember detachable magazine',[(Vector((-.077,0,-.115)),.039,.026),(Vector((-.069,0,-.080)),.026,.025),(Vector((-.060,0,-.016)),.027,.025)],METAL)
    box('Magazine plate',(-.079,0,-.119),(.050,.036,.007),METAL,.002)
    for o in G['objects'][start:]:o['magazine']=True
    return (.121,0,.038),(-.061,0,-.013)

def rifle(ak=False):
    accent=EMBER if ak else SOUL
    receiver=profile('Forged contoured receiver',[(-.111,.073),(-.086,.088),(.107,.084),(.165,.060),(.153,.015),
                    (.056,.012),(.024,-.007),(-.028,.004),(-.089,.008),(-.115,.035)],.052,METAL,bevel=.004)
    cyl('Rounded upper action',(.026,0,.075),.024,.251,METAL)
    box('Lower action spine',(.031,0,.020),(.171,.053,.016),METAL,.004)
    loft('Ergonomic curved grip',[(Vector((-.087,0,-.108)),.052,.036),(Vector((-.078,0,-.087)),.047,.039),
                 (Vector((-.060,0,-.046)),.044,.035),(Vector((-.050,0,-.006)),.036,.030),(Vector((-.052,0,.015)),.040,.031)],WOOD if ak else CLOTH)
    path('Rounded rifle trigger guard',[(-.033,0,.008),(.038,0,.008),(.043,0,-.016),(.012,0,-.027),(-.030,0,-.021),(-.033,0,.008)],.003,METAL,closed=True)
    path('Rifle trigger',[(.002,0,.010),(.009,0,-.005),(.002,0,-.019)],.0022,STEEL,4)
    cyl('Main barrel',(.366,0,.055),.009,.426,METAL)
    muzzle(.592,.055,.014,.035)
    cyl('Barrel barrel-lock ring',(.438,0,.055),.013,.025,METAL)
    if ak:
        loft('Sculpted orange wooden butt',[(Vector((-.303,0,-.031)),.068,.046),(Vector((-.307,0,.015)),.070,.045),
                (Vector((-.258,0,.059)),.125,.047),(Vector((-.160,0,.063)),.070,.039)],WOOD)
        # Solid wood silhouette with a softly carved shoulder.
        stock=profile('AK curved wooden stock',[(-.120,.079),(-.346,.060),(-.354,-.070),(-.315,-.077),
                       (-.262,-.028),(-.213,.013),(-.136,.025),(-.120,.037)],.047,WOOD,bevel=.006)
        box('Rubber butt pad',(-.354,0,-.004),(.009,.050,.135),RECESS,.003)
        fore=profile('Curved wood forearm',[(.174,.067),(.359,.066),(.370,.056),(.364,.020),(.304,.008),(.192,.018)],.057,WOOD,bevel=.007)
        cyl('Wood upper gas guard',(.268,0,.087),.017,.175,WOOD)
        cyl('Gas tube',(.381,0,.089),.007,.226,METAL)
        box('Gas block',(.451,0,.074),(.017,.024,.045),METAL,.002)
        for x in [.192,.214,.236,.258,.280,.302,.324]:cutbox(fore,(x,0,.051),(.009,.073,.009),.003)
        torus('AK front sight hoop',(.518,0,.121),.012,.0025,METAL,'X')
        path('AK sight tower',[(.518,-.010,.055),(.518,-.009,.118),(.518,.009,.118),(.518,.010,.055)],.003,METAL)
        box('AK rear sight',(.119,0,.098),(.027,.021,.014),METAL,.002)
        pumpkin(-.283,.014,.025,.026);pumpkin(.271,.036,.030,.017)
        for x,z,r in [(-.206,.045,.020),(-.300,-.027,.023),(.199,.040,.014),(.324,.036,.014)]:ornament(x,z,.026 if x<0 else .030,r)
        wrap('Weathered guard band',(.364,0,.071),.027,.067,3,LEATHER,'X',.017)
    else:
        cyl('Stock buffer tube',(-.166,0,.064),.015,.178,METAL)
        stock=profile('Rounded skeletal stock',[(-.137,.085),(-.336,.077),(-.350,.045),(-.355,-.092),(-.317,-.081),(-.213,.013),(-.145,.029)],.048,METAL,bevel=.005)
        cutbox(stock,(-.265,0,.005),(.120,.072,.088),.022)
        box('Textured shoulder pad',(-.356,0,-.009),(.011,.054,.155),RECESS,.004)
        for z in [-.065,-.043,-.021,.001,.023,.045]:box('Stock pad rib',(-.363,0,z),(.003,.056,.004),LEATHER,.001)
        box('Cheekpiece',(-.239,0,.090),(.174,.046,.014),METAL,.005)
        # Hollow handguard and actual capsule-shaped ventilation openings.
        guard=cyl('Octagonal hollow handguard',(.285,0,.062),.035,.241,METAL,vertices=8)
        guard.rotation_euler.x=pi/8;bpy.context.view_layer.update()
        bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.026,depth=.261,location=(.285,0,.062),rotation=(0,pi/2,0))
        boolean(guard,bpy.context.object)
        for x in [.196,.227,.258,.289,.320,.351,.382]:
            cutbox(guard,(x,0,.059),(.022,.095,.011),.004)
            for side in (-1,1):
                path('Soul slot inset',[(x-.007,side*.031,.052),(x+.006,side*.031,.052)],.00055,SOUL)
        for x in [i*.013+.026 for i in range(27)]:
            box('Picatinny rail tooth',(x,0,.103),(.006,.030,.006),METAL,.001)
        box('Rail base',(.173,0,.098),(.323,.025,.005),METAL,.001)
        box('Reflex mounting foot',(.031,0,.112),(.063,.029,.021),METAL,.002)
        optic=box('Rounded reflex hood',(.029,0,.141),(.030,.036,.044),METAL,.006)
        cutbox(optic,(.029,0,.142),(.054,.024,.029),.007)
        sphere('Optical soul lens',(.030,0,.143),(.001,.012,.015),GLASS)
        sphere('Reflex reticle',(.032,-.001,.143),(.001,.001,.001),SOUL)
        bat(-.257,.059,.026,.045);bat(.078,.045,.028,.028)
        for x,z,r in [(-.191,.058,.015),(-.038,.044,.016),(.125,.045,.015)]:ornament(x,z,.028,r)
    # Both firearms share a rounded ejection-port detail and machined controls.
    cutbox(receiver,(.080,-.024,.065),(.054,.015,.016),.004)
    box('Bolt face',(.080,-.026,.065),(.042,.0018,.009),STEEL,.001,bone=3)
    cyl('Selector boss',(-.041,-.030,.049),.007,.003,METAL,'Y')
    path('Selector lever',[(-.041,-.033,.049),(-.056,-.033,.055)],.0021,STEEL)
    for x,z in [(-.078,.039),(-.015,.028),(.119,.043),(.150,.047)]:screw(x,z,.029)
    grip_wrap=wrap('Grip fabric wrap',(-.071,0,-.057),.022,.093,5,LEATHER if ak else CLOTH,width=.016)
    grip_wrap.rotation_euler.y=-.19
    start=len(G['objects'])
    if ak:
        loft('True curved AK magazine',[(Vector((.093,0,.019)),.061,.039),(Vector((.098,0,-.028)),.060,.040),
             (Vector((.114,0,-.078)),.060,.040),(Vector((.142,0,-.126)),.059,.040),(Vector((.177,0,-.161)),.058,.039)],METAL)
        for side in (-1,1):
            for dx in [-.016,0,.016]:
                path('Magazine pressed flute',[(.092+dx,side*.021,.007),(.099+dx,side*.021,-.044),(.121+dx,side*.021,-.092),(.163+dx,side*.021,-.147)],.0012,ENGRAVING)
                path('Magazine ember seam',[(.092+dx,side*.022,-.020),(.103+dx,side*.022,-.055),(.127+dx,side*.022,-.103),(.163+dx,side*.022,-.143)],.00040,EMBER)
    else:
        loft('Rounded AR magazine',[(Vector((.092,0,.019)),.062,.039),(Vector((.095,0,-.026)),.062,.040),
            (Vector((.099,0,-.076)),.060,.040),(Vector((.111,0,-.137)),.063,.039),(Vector((.116,0,-.151)),.065,.041)],METAL)
        for side in (-1,1):
            for dx in [-.018,-.006,.006,.018]:
                path('Magazine rounded flute',[(.091+dx,side*.021,-.009),(.098+dx,side*.021,-.079),(.111+dx,side*.021,-.130)],.0010,RECESS)
            bat(.108,-.106,.022,.022)
            path('Magazine soul inlay',[(.076,side*.022,-.025),(.079,side*.022,-.090),(.091,side*.022,-.137)],.0005,SOUL)
            path('Magazine soul inlay',[(.122,side*.022,-.025),(.126,side*.022,-.090),(.137,side*.022,-.137)],.0005,SOUL)
    for o in G['objects'][start:]:o['magazine']=True
    return (.592,0,.055),(.092,0,.019)

def bezier(a,b,c,d,steps=20):
    return [tuple((1-t)**3*a[k]+3*(1-t)**2*t*b[k]+3*(1-t)*t*t*c[k]+t**3*d[k] for k in range(2)) for t in [i/steps for i in range(steps)]]

def curved_blade(name,segments,depth=.034):
    outline=[]
    for a,b,c,d in segments:outline+=bezier(a,b,c,d)
    n=len(outline);centroid=Vector((sum(p[0] for p in outline)/n,sum(p[1] for p in outline)/n))
    vertices=[];faces=[]
    # Lens-shaped cross section: sharp perimeter, bevel band, raised centre.
    for scale,y in [(1,0),(.95,-depth*.32),(.84,-depth*.5),(.84,depth*.5),(.95,depth*.32)]:
        for x,z in outline:
            p=centroid+(Vector((x,z))-centroid)*scale;vertices.append((p.x,y,p.y))
    for k in range(5):
        for i in range(n):faces.append((k*n+i,k*n+(i+1)%n,((k+1)%5)*n+(i+1)%n,((k+1)%5)*n+i))
    faces += [tuple(reversed(range(2*n,3*n))),tuple(range(3*n,4*n))]
    return obj(name,vertices,faces,METAL),outline

def axe():
    cyl('Rounded dark wooden haft',(0,0,.185),.019,.795,WOOD,'Z',64)
    wrap('Real diagonal leather binding',(0,0,-.061),.020,.290,15,LEATHER,width=.020)
    for z in [-.225,.093,.169,.410,.515]:
        cyl('Forged grip collar',(0,0,z),.024,.018,METAL,'Z')
        torus('Collar engraved bead',(0,0,z+.009),.0225,.0012,ENGRAVING)
    skull((0,0,-.248),.039,EMBER,METAL)
    seg=[((.027,.450),(.082,.437),(.123,.396),(.145,.341)),
         ((.145,.341),(.318,.390),(.371,.624),(.220,.813)),
         ((.220,.813),(.162,.783),(.151,.744),(.181,.692)),
         ((.181,.692),(.151,.596),(.093,.572),(.024,.553)),
         ((.024,.553),(-.019,.542),(-.019,.474),(.027,.450))]
    blade,outline=curved_blade('Smooth crescent axe blade',seg,.042)
    # True continuous steel cutting ribbon along the entire outer crescent.
    edge=bezier((.145,.341),(.318,.390),(.371,.624),(.220,.813),48)+[(.220,.813)]
    for side in (-1,1):
        path('Polished axe cutting edge',[(x,side*.001,z) for x,z in edge],.0032,STEEL)
        path('Ember cutting seam',[(x-.006,side*.010,z) for x,z in edge[3:-3]],.00075,EMBER)
    profile('Axe rear spike',[(-.023,.471),(-.127,.448),(-.178,.481),(-.118,.524),(-.023,.533)],.032,METAL,bevel=.004)
    skull((.030,0,.505),.035,EMBER)
    for x,z,r in [(.111,.498,.031),(.200,.558,.036),(.239,.645,.032),(.177,.441,.025)]:ornament(x,z,.023,r)
    for side in (-1,1):
        path('Irregular ember fracture',[(.083,side*.023,.503),(.114,side*.023,.536),(.139,side*.023,.525),(.154,side*.023,.567),(.194,side*.023,.597),(.208,side*.023,.663),(.229,side*.020,.684)],.0011,EMBER)
        path('Fracture branch',[(.145,side*.023,.546),(.166,side*.023,.489),(.205,side*.020,.469)],.0007,EMBER)
        for z in [.206,.288,.367]:ornament(0,z,.020,.014)
    # Hanging chain and carved pumpkin pendant, modelled geometry.
    for k in range(6):torus('Pendant chain',(.094,-.032,.437-k*.010),.006,.0012,ENGRAVING,'Y' if k%2 else 'X')
    pumpkin(.094,.359,.039,.019)
    return None,None

def scythe():
    cyl('Rounded sculpted wooden shaft',(0,0,.351),.020,1.590,WOOD,'Z',64)
    for z in [-.441,-.262,.03,.277,.588,.912,1.117]:
        cyl('Carved forged collar',(0,0,z),.026,.022,METAL,'Z')
        torus('Soul collar edge',(0,0,z+.010),.025,.0011,ENGRAVING)
    for center,length,turns in [(-.153,.190,8),(.184,.184,8),(.686,.150,6)]:
        wrap('Real purple textile wrapping',(0,0,center),.022,length,turns,CLOTH,width=.024)
    # Twisted raised carvings along the shaft, matching the gothic visual language.
    for k in range(6):
        start=-.39+k*.245
        for sign in (-1,1):
            pts=[]
            for i in range(16):
                t=i/15;angle=sign*pi*.7+1.35*pi*t
                pts.append((.021*cos(angle),.021*sin(angle),start+t*.19))
            path('Raised shaft vine',pts,.0021,METAL)
        for side in (-1,1):
            path('Violet shaft rune',[(-.007,side*.023,start+.046),(.008,side*.023,start+.080),(-.004,side*.023,start+.106)],.00065,SOUL)
    seg=[((.007,1.102),(.221,1.171),(.516,1.092),(.664,.856)),
         ((.664,.856),(.749,.720),(.786,.573),(.792,.408)),
         ((.792,.408),(.688,.652),(.431,.879),(.044,.955)),
         ((.044,.955),(-.031,.982),(-.054,1.052),(.007,1.102))]
    blade,outline=curved_blade('True swept curved scythe blade',seg,.027)
    inner=bezier((.792,.408),(.688,.652),(.431,.879),(.044,.955),52)+[(.044,.955)]
    for side in (-1,1):
        path('Continuous sharpened scythe edge',[(x,side*.001,z) for x,z in inner],.0038,STEEL)
        path('Soul spine fracture',[(.098,side*.016,1.070),(.150,side*.016,1.085),(.183,side*.016,1.047),(.252,side*.016,1.081),
              (.304,side*.016,1.047),(.365,side*.016,1.052),(.405,side*.016,1.012),(.471,side*.016,1.003),(.500,side*.014,.962)],.0013,SOUL)
    skull((.042,0,1.061),.051,SOUL,METAL)
    for sign in (-1,1):
        for i in range(3):
            path('Curving bone crown',[(.031+sign*.025,0,1.076),(.02+sign*(.04+i*.014),0,1.140+i*.01),
                (.00+sign*(.073+i*.014),0,1.151+i*.017),(-.013+sign*(.060+i*.010),0,1.120+i*.025)],.004-i*.0007,STEEL)
    for x,z,r in [(.154,1.034,.027),(.252,1.015,.027),(.369,.977,.030),(.519,.893,.029)]:ornament(x,z,.016,r)
    # Three hooked talons at the lower end, instead of a triangular block.
    for sign in [-1,0,1]:
        path('Claw pommel',[(sign*.012,0,-.419),(sign*.034,-.007,-.458),(sign*.037,-.010,-.485),(sign*.013,-.01,-.479)],.004,METAL)
    for k in range(8):torus('Soul charm chain',(-.023,-.027,.702-k*.010),.0055,.0010,ENGRAVING,'Y' if k%2 else 'X')
    profile('Soul diamond charm',[(-.023,.608),(-.045,.578),(-.023,.545),(-.001,.578)],.006,METAL,-.029,bevel=.002)
    path('Soul charm rune',[(-.032,-.034,.579),(-.022,-.034,.592),(-.015,-.034,.577),(-.023,-.034,.560)],.0008,SOUL)
    return None,None

def builders(namespace):
    global G
    G=namespace
    return pistol,lambda:rifle(False),lambda:rifle(True),axe,scythe
