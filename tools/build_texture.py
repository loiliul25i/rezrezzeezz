"""V2: separate, mipmapped material maps. No shared colour atlas or UV modulo."""
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
import struct
import io
import json
import shutil
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'sources/textures';OUT.mkdir(parents=True,exist_ok=True)
SIZE=512
FINISHES=[('metal',(27,30,35),.86,.29,175),('steel',(122,126,133),.92,.24,210),
 ('ember',(236,65,4),.15,.40,85),('soul',(109,14,188),.15,.40,90),
 ('wood',(99,40,13),.02,.52,42),('leather',(28,18,18),.02,.72,25),
 ('bone',(176,157,116),.03,.40,65),('recess',(6,7,9),.10,.65,18),
 ('engraving',(62,51,32),.78,.32,175),('cloth',(39,17,48),.01,.90,12),
 ('glass',(28,38,42),.45,.16,210)]
def save_dds(image,path):
 levels=[];size=image.size;header=None
 while True:
  buffer=io.BytesIO();image.resize(size,Image.Resampling.LANCZOS).save(buffer,format='DDS',pixel_format='DXT5')
  data=buffer.getvalue()
  if header is None:header=bytearray(data[:128])
  levels.append(data[128:])
  if size==(1,1):break
  size=(max(1,size[0]//2),max(1,size[1]//2))
 struct.pack_into('<I',header,8,0x000A1007)
 struct.pack_into('<III',header,12,image.height,image.width,len(levels[0]))
 struct.pack_into('<I',header,28,len(levels))
 struct.pack_into('<I',header,108,0x00401008)
 path.write_bytes(header+b''.join(levels));return len(levels)
rng=np.random.default_rng(31102026);y,x=np.mgrid[:SIZE,:SIZE];manifest=[]
for name,colour,metallic,roughness,specular in FINISHES:
 noise=rng.normal(0,1.1,(SIZE,SIZE));relief=np.zeros((SIZE,SIZE))
 if name=='wood':
  grain=np.sin(y*.26+np.sin(x*.022)*3+np.sin(x*.05)*.5)
  noise+=grain*9+np.sin(y*.83+x*.013)*2;relief=grain*.8
 elif name in ('leather','cloth'):
  weave=np.cos(x*np.pi)*np.cos(y*np.pi)
  noise+=weave*2.5+np.sin(y*.17)*1.5;relief=weave*.65
 elif name in ('metal','steel','engraving'):
  relief=rng.normal(0,.20,(SIZE,SIZE));noise+=np.sin(y*1.1)*.4
 rgb=np.clip(np.array(colour)[None,None,:]+noise[:,:,None],0,255).astype('uint8')
 diffuse=Image.fromarray(rgb).convert('RGBA')
 if name in ('metal','steel','engraving'):
  draw=ImageDraw.Draw(diffuse)
  for _ in range(240):
   xx,yy=rng.integers(12,SIZE-40,2);length=int(rng.integers(3,28))
   draw.line((int(xx),int(yy),int(xx)+length,int(yy)+int(rng.integers(-2,3))),fill=tuple(min(255,c+9) for c in colour)+(255,))
 dy,dx=np.gradient(relief);normals=np.dstack((-dx*.08,dy*.08,np.ones_like(dx)))
 normals/=np.linalg.norm(normals,axis=2,keepdims=True)
 normal=Image.fromarray(np.clip((normals*.5+.5)*255,0,255).astype('uint8')).convert('RGBA')
 spec=Image.fromarray(np.stack([np.full((SIZE,SIZE),specular),np.full((SIZE,SIZE),int(roughness*255)),np.full((SIZE,SIZE),int(metallic*255))],axis=2).astype('uint8')).convert('RGBA')
 for suffix,image in [('d',diffuse),('n',normal),('s',spec)]:
  texture='hw_'+name+'_'+suffix;image.save(OUT/(texture+'.png'))
  levels=save_dds(image,OUT/(texture+'.dds'))
  manifest.append(dict(name=texture,width=SIZE,height=SIZE,mips=levels,format='D3DFMT_DXT5'))
(ROOT/'sources/materials.json').write_text(json.dumps([dict(index=i,name=n,metallic=m,roughness=r,specular=s,emissive=n in ('ember','soul')) for i,(n,c,m,r,s) in enumerate(FINISHES)],indent=2))
(ROOT/'sources/texture_manifest.json').write_text(json.dumps(manifest,indent=2))
print(f'Created {len(manifest)} separate material maps with real mip chains.')

# Keep the native texture dictionary sources synchronized with rebuilt maps.
folder=ROOT/'sources/cwxml/hw_finishes';folder.mkdir(parents=True,exist_ok=True)
dictionary=E.Element('TextureDictionary')
for texture in manifest:
 item=E.SubElement(dictionary,'Item')
 for tag,value in [('Name',texture['name']),('Usage','DIFFUSE' if texture['name'].endswith('_d') else 'NORMAL' if texture['name'].endswith('_n') else 'SPECULAR'),('UsageFlags','0'),('Format',texture['format']),('FileName',texture['name']+'.dds')]:E.SubElement(item,tag).text=value
 for tag,value in [('Unk32',0),('ExtraFlags',0),('Width',texture['width']),('Height',texture['height']),('MipLevels',texture['mips'])]:E.SubElement(item,tag,value=str(value))
 shutil.copyfile(OUT/(texture['name']+'.dds'),folder/(texture['name']+'.dds'))
E.indent(dictionary);E.ElementTree(dictionary).write(ROOT/'sources/cwxml/hw_finishes.ytd.xml',encoding='UTF-8',xml_declaration=True)
