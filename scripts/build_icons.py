"""Draw the SIGDA document monogram from code; no institutional seal is reused."""
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
    # All identifying marks lie inside the central 80% for OS icon masks.
    draw.rounded_rectangle(box((130, 102, 363, 346)), radius=round(22*s), fill='#102e4a', outline='#7f785f', width=max(1,round(3*s)))
    draw.rounded_rectangle(box((150, 82, 383, 326)), radius=round(22*s), fill='#e8ddc5', outline='#c5a265', width=max(1,round(5*s)))
    for y, end in [(140,330),(177,330),(214,300)]:
        draw.rounded_rectangle(box((192,y,end,y+9)), radius=max(1,round(4*s)), fill='#21486b')
    draw.line(box((292,273,313,293,348,248)), fill='#9b742c', width=max(2,round(8*s)))
    font=ImageFont.truetype(str(ROOT/'apps/demo/manrope.ttf'),round(67*s))
    try:
        font.set_variation_by_name('Bold')
    except (ValueError, OSError):
        pass
    draw.text((size/2,round(381*s)), 'SIGDA', font=font, fill='#e8ddc5', anchor='mm')
    draw.rounded_rectangle(box((183,429,329,435)), radius=max(1,round(3*s)), fill='#c5a265')
    image.save(OUTPUT/name)


if __name__ == '__main__':
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for size, name in [(192,'icon-192.png'),(512,'icon-512.png'),(512,'maskable-512.png'),(180,'apple-touch-icon.png')]:
        icon(size,name)
    print('SIGDA icons generated: document monogram, gold and navy, safe mask area.')
