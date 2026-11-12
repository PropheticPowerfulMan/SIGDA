"""Small monochrome symbols constructed from vector primitives, without a font."""
import re

ICONS={
 'facebook':[{'tag':'path','d':'M14 23 L14 13 L18 13 L19 9 L14 9 L14 6 C14 4 15 4 19 4 L19 0 L15 0 C10 0 9 3 9 6 L9 9 L5 9 L5 13 L9 13 L9 23 Z'}],
 'x':[{'tag':'path','d':'M3 2 L8 2 L21 22 L16 22 Z M19 2 L22 2 L5 22 L2 22 Z'}],
 'instagram':[{'tag':'rect','x':2,'y':2,'width':20,'height':20,'rx':5,'outline':True},{'tag':'circle','cx':12,'cy':12,'r':4.5,'outline':True},{'tag':'circle','cx':18,'cy':6,'r':1.3}],
 'youtube':[{'tag':'rect','x':1,'y':4,'width':22,'height':16,'rx':5},{'tag':'path','d':'M10 8 L17 12 L10 16 Z','white':True}],
 'linkedin':[{'tag':'circle','cx':4,'cy':4,'r':2},{'tag':'rect','x':2,'y':8,'width':4,'height':14},{'tag':'path','d':'M9 8 L13 8 L13 10 C15 6 22 7 22 13 L22 22 L18 22 L18 14 C18 10 13 10 13 14 L13 22 L9 22 Z'}],
 'tiktok':[{'tag':'path','d':'M14 1 L18 1 C18 5 20 7 24 7 L24 11 C21 11 19 10 18 9 L18 17 C18 26 4 26 4 17 C4 12 8 10 12 11 L12 15 C7 13 6 21 11 21 C13 21 14 19 14 17 Z'}],
 'flickr':[{'tag':'circle','cx':6,'cy':12,'r':4.5},{'tag':'circle','cx':18,'cy':12,'r':4.5}],
}


def draw_icon(page,key,x,y,size):
    page.saveState();page.translate(x,y+size);page.scale(size/24,-size/24);page.setLineWidth(1.9)
    for shape in ICONS[key]:
        page.setFillColorRGB(1,1,1) if shape.get('white') else page.setFillColorRGB(.18,.22,.27)
        page.setStrokeColorRGB(.18,.22,.27)
        stroke=int(bool(shape.get('outline')));fill=1-stroke
        if shape['tag']=='rect':page.roundRect(shape['x'],shape['y'],shape['width'],shape['height'],shape.get('rx',0),stroke=stroke,fill=fill)
        elif shape['tag']=='circle':page.circle(shape['cx'],shape['cy'],shape['r'],stroke=stroke,fill=fill)
        else:
            tokens=re.findall(r'[MLCZ]|-?\d+(?:\.\d+)?',shape['d']);p=page.beginPath();i=0
            while i<len(tokens):
                command=tokens[i];i+=1
                if command=='Z':p.close();continue
                count=6 if command=='C' else 2;values=[float(v) for v in tokens[i:i+count]];i+=count
                if command=='M':p.moveTo(*values)
                elif command=='L':p.lineTo(*values)
                else:p.curveTo(*values)
            page.drawPath(p,stroke=stroke,fill=fill)
    page.restoreState()
