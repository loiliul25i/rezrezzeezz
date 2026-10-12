"""Create an original eight-finish atlas and mipmapped BC3 DDS, without external assets."""
from pathlib import Path
from PIL import Image, ImageDraw
import random
import struct

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'sources' / 'textures'
OUT.mkdir(parents=True, exist_ok=True)
random.seed(31102026)
palette = [(35, 40, 47), (151, 160, 172), (245, 90, 10), (151, 40, 232),
           (82, 39, 20), (40, 27, 24), (198, 184, 152), (9, 11, 15)]
im = Image.new('RGBA', (1024, 512))
for index, base in enumerate(palette):
    tile = Image.new('RGBA', (256, 256))
    pixels = tile.load()
    for y in range(256):
        for x in range(256):
            noise = random.gauss(0, 2.5 if index in (2, 3) else 5)
            if index == 4:
                noise += 10 * __import__('math').sin(y * .17 + 2 * __import__('math').sin(x * .022))
            pixels[x, y] = tuple(max(0, min(255, round(c + noise))) for c in base) + (255,)
    draw = ImageDraw.Draw(tile)
    if index not in (2, 3):
        for _ in range(90):
            x, y = random.randrange(256), random.randrange(256)
            colour = tuple(min(255, c + 14) for c in base) + (255,)
            draw.line((x, y, x + random.randrange(4, 22), y + random.randrange(-1, 2)), fill=colour)
    if index == 5:
        for y in range(0, 256, 16):
            draw.line((0, y, 256, y + 4), fill=(24, 16, 14, 255), width=2)
    im.paste(tile, ((index % 4) * 256, (index // 4) * 256))
im.save(OUT / 'hw_finish.png')
# Assemble actual mip levels rather than only declaring them in the metadata.
payloads = []
size = im.size
while True:
    level = im.resize(size, Image.Resampling.LANCZOS)
    import io
    buf = io.BytesIO()
    level.save(buf, format='DDS', pixel_format='DXT5')
    raw = buf.getvalue()
    payloads.append(raw[128:])
    if size == (1, 1):
        break
    size = (max(1, size[0] // 2), max(1, size[1] // 2))
header = bytearray(raw[:128])
struct.pack_into('<I', header, 8, 0x000A1007)  # DDSD_MIPMAPCOUNT | LINEARSIZE | required flags
struct.pack_into('<III', header, 12, im.height, im.width, len(payloads[0]))
struct.pack_into('<I', header, 28, len(payloads))
struct.pack_into('<I', header, 108, 0x00401008)  # TEXTURE | COMPLEX | MIPMAP
(OUT / 'hw_finish.dds').write_bytes(header + b''.join(payloads))
print(f'Original texture atlas: {im.width}x{im.height}, {len(payloads)} BC3 mip levels')
