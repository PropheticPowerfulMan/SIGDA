"""Build SIGDA PWA icons from the supplied RDC emblem and a distinct SIGDA label."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'apps/backend/sigda/static/sigda/icons'


def icon(size, name):
    image = Image.new('RGB', (size, size), '#071b35')
    draw = ImageDraw.Draw(image)
    s = size / 512
    def box(values):
        return tuple(round(v * s) for v in values)
    emblem=Image.open(ROOT/'apps/backend/sigda/static/sigda/EmblemRDC.jpg').convert('RGB')
    emblem=emblem.resize((round(328*s),round(328*s)),Image.Resampling.LANCZOS)
    draw.ellipse(box((85,51,427,393)), fill='#eee9df',outline='#c5a265',width=max(1,round(4*s)))
    mask=Image.new('L',emblem.size,0);ImageDraw.Draw(mask).ellipse((0,0,emblem.width-1,emblem.height-1),fill=255)
    image.paste(emblem,(round(92*s),round(58*s)),mask)
    font=ImageFont.truetype(str(ROOT/'apps/demo/manrope.ttf'),round(52*s))
    try:
        font.set_variation_by_name('Bold')
    except (ValueError, OSError):
        pass
    draw.text((size/2,round(436*s)), 'SIGDA', font=font, fill='#e8ddc5', anchor='mm')
    if name.startswith('maskable'):
        inner=image.resize((round(size*.9),round(size*.9)),Image.Resampling.LANCZOS)
        image=Image.new('RGB',(size,size),'#071b35');image.paste(inner,((size-inner.width)//2,(size-inner.height)//2))
    image.save(OUTPUT/name)
    updated={"icon-192.png":"icon-192-rdc.png","icon-512.png":"icon-512-rdc.png","maskable-512.png":"maskable-rdc-512.png","apple-touch-icon.png":"apple-touch-icon-rdc.png"}
    image.save(OUTPUT/updated[name])


if __name__ == '__main__':
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for size, name in [(192,'icon-192.png'),(512,'icon-512.png'),(512,'maskable-512.png'),(180,'apple-touch-icon.png')]:
        icon(size,name)
    print('SIGDA RDC-emblem PWA icons generated with a distinct label.')
