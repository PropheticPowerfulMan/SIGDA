"""Build the illustrated demonstration guide from actual captured screens."""
from hashlib import sha256
from io import BytesIO
import json
from math import ceil
from pathlib import Path
import sys
from xml.sax.saxutils import escape

from PIL import Image
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'apps/backend'))
from sigda.catalog import DOCUMENT_TYPES
from sigda.catalog import AGENTS, format_date
from sigda.pdf import EMBLEM, FOOTER, render_pdf
from sigda.social_icons import draw_icon
from datetime import date
import pypdfium2 as pdfium

DOCS=ROOT/'docs/manual';SHOTS=DOCS/'screenshots';OUTPUT=ROOT/'output/pdf';OUTPUT.mkdir(parents=True,exist_ok=True)
CHAPTERS=json.loads((DOCS/'manual_content.json').read_text(encoding='utf-8'))
CAPTURES=json.loads((DOCS/'captures.json').read_text(encoding='utf-8'))
REGISTRY={c['file']:c for c in CAPTURES['captures']}
for entry in CAPTURES['captures']:
    path=SHOTS/entry['file']
    if not path.is_file():raise ValueError('Capture absente : '+str(path))
    if entry.get('sha256') and sha256(path.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('Capture modifiée : '+str(path))

illustrations=DOCS/'illustrations';illustrations.mkdir(exist_ok=True)
footer_pdf=render_pdf('attestation-service',DOCUMENT_TYPES['attestation-service'],next(iter(AGENTS.values())), 'SPEC-ATS-GUIDE-2026',format_date(date(2026,11,12)))
with pdfium.PdfDocument(footer_pdf) as source:
    image=source[0].render(scale=3.4).to_pil().convert('RGB')
    image.crop((60,image.height-400,image.width-60,image.height)).save(illustrations/'pied-page.png')

source_digest=sha256((DOCS/'manual_content.json').read_bytes())
for file in sorted(REGISTRY):source_digest.update(file.encode());source_digest.update((SHOTS/file).read_bytes())
source_digest.update((illustrations/'pied-page.png').read_bytes());source_digest.update(EMBLEM.read_bytes());source_digest.update(Path(__file__).read_bytes())
SOURCE_HASH=source_digest.hexdigest();IDENTIFIER='SIGDA-GUIDE-20261112-'+SOURCE_HASH[:8].upper()
PRIMARY_SCREENS={chapter['screen'] for chapter in CHAPTERS if chapter.get('screen') and not chapter.get('kind')}
ATLAS=sorted(set(REGISTRY)-PRIMARY_SCREENS)
WIDTH,HEIGHT=A4;LEFT=44;RIGHT=WIDTH-44;USABLE=RIGHT-LEFT;PAGES=len(CHAPTERS)+2+ceil(len(ATLAS)/2)
NAVY=HexColor('#0a2039');GOLD=HexColor('#aa844c');INK=HexColor('#23394b');MUTED=HexColor('#596a76');PALE=HexColor('#eee8dc');PAPER=HexColor('#fbf9f5');BORDER=HexColor('#d9cfbf')
for name,file in [('GuideBody','times.ttf'),('GuideUI','segoeui.ttf'),('GuideStrong','seguisb.ttf')]:pdfmetrics.registerFont(TTFont(name,str(Path('C:/Windows/Fonts')/file)))
BODY=ParagraphStyle('body',fontName='GuideBody',fontSize=11.3,leading=14.6,textColor=INK,spaceAfter=7)
SMALL=ParagraphStyle('small',fontName='GuideUI',fontSize=8.2,leading=11,textColor=MUTED)
TITLE=ParagraphStyle('title',fontName='GuideStrong',fontSize=22,leading=26,textColor=NAVY)
LEAD=ParagraphStyle('lead',parent=BODY,fontSize=12,leading=16)
NOTE=ParagraphStyle('note',parent=BODY,fontSize=10,leading=13,textColor=HexColor('#5a482c'))


def plain(text):return escape(str(text).replace('\u2011','-').replace('\u2013','-').replace('\u2014','-'))


def para(text,x,y,width,style=BODY,html=False,draw=True):
    paragraph=Paragraph(text if html else plain(text),style);_,h=paragraph.wrap(width,1000)
    if draw:paragraph.drawOn(canvas,x,y-h)
    return h


def header(cover=False):
    canvas.drawImage(str(EMBLEM),LEFT,HEIGHT-52,width=30,height=30,mask='auto')
    canvas.setFillColor(HexColor('#e2e9ee') if cover else NAVY);canvas.setFont('GuideStrong',8.6)
    canvas.drawString(LEFT+40,HEIGHT-30,'RÉPUBLIQUE DÉMOCRATIQUE DU CONGO')
    canvas.setFillColor(HexColor('#bfcfdb') if cover else MUTED);canvas.setFont('GuideUI',7.3)
    canvas.drawString(LEFT+40,HEIGHT-44,'Cabinet du Président de la République | SIGDA - Guide de démonstration')
    if not cover:
        canvas.setFont('GuideUI',8);canvas.drawRightString(RIGHT,HEIGHT-33,'Sommaire')
        canvas.linkRect('', 'sommaire',(RIGHT-50,HEIGHT-41,RIGHT,HEIGHT-23),relative=0,thickness=0)
    canvas.setStrokeColor(GOLD if cover else BORDER);canvas.setLineWidth(.6);canvas.line(LEFT,HEIGHT-59,RIGHT,HEIGHT-59)


def frame(number):
    canvas.setFillColor(PAPER);canvas.rect(0,0,WIDTH,HEIGHT,fill=1,stroke=0)
    header()
    canvas.setStrokeColor(BORDER);canvas.line(LEFT,47,RIGHT,47)
    canvas.setFont('GuideUI',7.1);canvas.setFillColor(MUTED);canvas.drawString(LEFT,33,'12 novembre 2026 · Démonstration · Données fictives')
    canvas.setFont('GuideUI',6.6);canvas.drawString(LEFT,21,'ADN d’édition : '+SOURCE_HASH[:24].upper());canvas.setFont('GuideStrong',8);canvas.drawRightString(RIGHT,28,f'{number:02d} / {PAGES:02d}')


def steps(items,x,y,width):
    for index,text in enumerate(items,1):
        h=para(text,x+23,y,width-23,draw=False)
        canvas.setFillColor(NAVY);canvas.circle(x+7.5,y-7,7.5,fill=1,stroke=0);canvas.setFillColor(white);canvas.setFont('GuideStrong',8);canvas.drawCentredString(x+7.5,y-10,str(index))
        para(text,x+23,y,width-23);y-=h+10
    return y


def steps_height(items,width):return sum(para(text,0,0,width-23,draw=False)+10 for text in items)


def note(text,y):
    height=para(text,0,0,USABLE-30,NOTE,draw=False)+24
    if y-height<65:raise ValueError(f'Texte trop bas : page {canvas.getPageNumber()}, bas={y-height:.1f}')
    canvas.setFillColor(PALE);canvas.roundRect(LEFT,y-height,USABLE,height,6,fill=1,stroke=0);canvas.setFillColor(GOLD);canvas.roundRect(LEFT,y-height,3,height,1,fill=1,stroke=0);para(text,LEFT+15,y-12,USABLE-30,NOTE)
    return y-height


def photo(filename,x,y,width,maxheight):
    if filename not in REGISTRY:raise ValueError('Image non documentée : '+filename)
    image=Image.open(SHOTS/filename).convert('RGB')
    # Enlarge useful controls by removing empty margins in desktop content screens.
    if image.width==1180 and filename not in ['01-connexion.jpg','03-erreur-connexion.jpg','05-menu-rail.jpg','13-grand-format.jpg','29-installation.jpg']:
        image=image.crop((250,80,1170,850))
    image.thumbnail((1500,1500))
    ratio=min(width/image.width,maxheight/image.height);w=image.width*ratio;h=image.height*ratio
    data=BytesIO();image.save(data,format='JPEG',quality=84,optimize=True);data.seek(0)
    image_x=x+(width-w)/2
    canvas.setFillColor(PALE);canvas.setStrokeColor(BORDER);canvas.roundRect(image_x-1,y-h-1,w+2,h+2,5,fill=1,stroke=1)
    canvas.drawImage(ImageReader(data),image_x,y-h,width=w,height=h)
    caption=REGISTRY[filename]['surface']+' · '+REGISTRY[filename]['label']
    ch=para(caption,x,y-h-7,width,SMALL)
    return h+ch+16


def cards(items,y,height=90):
    gap=10;w=(USABLE-gap*(len(items)-1))/len(items)
    for i,(title,description) in enumerate(items):
        x=LEFT+i*(w+gap);canvas.setFillColor(NAVY);canvas.roundRect(x,y-height,w,height,7,fill=1,stroke=0)
        style=ParagraphStyle('cardtitle',fontName='GuideStrong',fontSize=12,leading=15,textColor=HexColor('#dfc38e'))
        para(title,x+12,y-13,w-24,style)
        style=ParagraphStyle('cardbody',fontName='GuideUI',fontSize=9,leading=13,textColor=HexColor('#e8eaf0'))
        para(description,x+12,y-37,w-24,style)
    return y-height-18


def table(rows,widths,y):
    style=ParagraphStyle('cell',fontName='GuideUI',fontSize=9.1,leading=12,textColor=INK)
    cells=[[Paragraph(plain(value),style) for value in row] for row in rows]
    t=Table(cells,colWidths=widths,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('FONTNAME',(0,0),(-1,0),'GuideStrong'),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,-1),.4,BORDER)]));_,h=t.wrap(USABLE,HEIGHT);t.drawOn(canvas,LEFT,y-h);return y-h-18


def cover():
    canvas.setFillColor(NAVY);canvas.rect(0,0,WIDTH,HEIGHT,fill=1,stroke=0)
    canvas.setFillColor(HexColor('#142f49'));canvas.circle(WIDTH+90,HEIGHT-80,300,fill=1,stroke=0)
    header(cover=True)
    canvas.drawImage(str(EMBLEM),WIDTH-153,HEIGHT-205,width=108,height=108,mask='auto')
    canvas.setFont('GuideStrong',52);canvas.setFillColor(white);canvas.drawString(LEFT,HEIGHT-246,'SIGDA')
    title=ParagraphStyle('cover',fontName='GuideStrong',fontSize=30,leading=37,textColor=white);para('Guide d’utilisation<br/>illustré',LEFT,HEIGHT-276,450,title,html=True)
    style=ParagraphStyle('promise',fontName='GuideBody',fontSize=17,leading=24,textColor=HexColor('#e1c18b'));para('Comprendre son espace.<br/>Produire avec précision.<br/>Valider en responsabilité.',LEFT,HEIGHT-380,440,style,html=True)
    y=HEIGHT-505;gap=8;w=(USABLE-3*gap)/4
    for i,(role,label) in enumerate([('OPS','Préparer'),('SECAD','Contrôler'),('AP','Donner le visa'),('DIRCAB','Décider')]):
        x=LEFT+i*(w+gap);canvas.setFillColor(HexColor('#1b3c58'));canvas.roundRect(x,y-64,w,64,6,fill=1,stroke=0);canvas.setFillColor(HexColor('#e1c18b'));canvas.setFont('GuideStrong',13);canvas.drawString(x+12,y-24,role);canvas.setFillColor(white);canvas.setFont('GuideUI',9);canvas.drawString(x+12,y-46,label)
    style=ParagraphStyle('scope',fontName='GuideUI',fontSize=10,leading=15,textColor=HexColor('#ced9e4'));para('Une procédure pour les quatre profils du workflow et la Maintenance, des captures réelles et un parcours jusqu’à l’impression. SIGDA et SSDC sont deux projets indépendants.',LEFT,190,390,style)
    canvas.setStrokeColor(GOLD);canvas.line(LEFT,111,RIGHT,111);canvas.setFont('GuideStrong',9);canvas.setFillColor(HexColor('#e1c18b'));canvas.drawString(LEFT,87,'ÉDITION DÉMONSTRATION · 12 NOVEMBRE 2026')
    canvas.setFont('GuideUI',7.5);canvas.setFillColor(HexColor('#ced9e4'));canvas.drawString(LEFT,66,IDENTIFIER);canvas.drawString(LEFT,50,'Données fictives · Aucun système officiel connecté à la démonstration')
    canvas.linkURL('https://propheticpowerfulman.github.io/SIGDA/',(LEFT,46,RIGHT,100),relative=0,thickness=0);canvas.showPage()


def contents():
    frame(2);canvas.bookmarkPage('sommaire');canvas.addOutlineEntry('Sommaire','sommaire',level=0)
    para('Votre parcours dans SIGDA',LEFT,HEIGHT-72,USABLE,TITLE)
    y=HEIGHT-116
    for i,chapter in enumerate(CHAPTERS,1):
        canvas.setFont('GuideStrong',9);canvas.setFillColor(GOLD);canvas.drawString(LEFT,y,f'{i:02d}')
        canvas.setFont('GuideUI',9.4);canvas.setFillColor(INK);canvas.drawString(LEFT+28,y,chapter['title']);canvas.setFont('GuideStrong',9.4);canvas.drawRightString(RIGHT,y,str(i+2));canvas.linkRect('',f'chapter-{i}',(LEFT,y-5,RIGHT,y+13),relative=0,thickness=0);y-=18.7
    if ATLAS:
        canvas.setFillColor(GOLD);canvas.setFont('GuideStrong',9);canvas.drawString(LEFT,y,'A');canvas.setFillColor(INK);canvas.setFont('GuideUI',9.4);canvas.drawString(LEFT+28,y,'Atlas des écrans complémentaires');canvas.drawRightString(RIGHT,y,str(len(CHAPTERS)+3));canvas.linkRect('','atlas',(LEFT,y-5,RIGHT,y+13),relative=0,thickness=0);y-=18.7
    para('Le sommaire et le lien Sommaire en haut des pages sont cliquables. Les captures de serveur privé sont signalées et utilisent uniquement des dossiers fictifs.',LEFT,y-5,USABLE,SMALL)
    canvas.showPage()


def chapter(index,content):
    frame(index+2);canvas.bookmarkPage(f'chapter-{index}');canvas.addOutlineEntry(content['title'],f'chapter-{index}',level=0)
    canvas.setFillColor(GOLD);canvas.setFont('GuideStrong',8.8);canvas.drawString(LEFT,HEIGHT-70,f'PARCOURS {index:02d}'+('   /   ESPACE '+content['profile'] if content.get('profile') else ''))
    y=HEIGHT-85;y-=para(content['title'],LEFT,y,USABLE,TITLE)+12;y-=para(content['lead'],LEFT,y,USABLE,LEAD)+16
    kind=content.get('kind');items=content['steps']
    note_h=para(content['note'],0,0,USABLE-30,NOTE,draw=False)+24
    if content.get('layout')=='portrait':
        sw=210;leftwidth=USABLE-sw-22;available=y-83-note_h-22
        image_h=photo(content['screen'],RIGHT-sw,y,sw,available)
        text_y=steps(items,LEFT,y,leftwidth);y=min(text_y,y-image_h)-8
    elif kind=='environment':
        y=cards([('GitHub Pages','Connexion et workflow simulés. Données locales à cet appareil.'),('Django fictif','Contrôles serveur, registre et archivage. Base isolée pour le guide.'),('Production réelle','Déploiement institutionnel à préparer et à autoriser.')],y,112);y=steps(items,LEFT,y,USABLE)
    elif kind=='roles':
        y=cards([('OPS','Saisir et corriger'),('SECAD','Contrôler'),('AP','Donner le visa'),('DIRCAB','Valider et piloter')],y,80);y=steps(items,LEFT,y,USABLE)
        y=table([['Espace','Périmètre des indicateurs'],['OPS','Mes brouillons, mes pièces en validation et validées.'],['SECAD / AP','Mes tâches, mes échéances et mes retours.'],['DIRCAB','Mes décisions et accès au pilotage global.'],['Maintenance','Base agents, demandes, périodes et suivi technique.']],[130,USABLE-130],y-4)
    elif kind=='catalogue':
        rows=[['Modèle','Finalité']]+[[model.title,model.description] for model in DOCUMENT_TYPES.values()]
        y=table(rows,[210,USABLE-210],y);y=steps(items,LEFT,y,USABLE)
    elif kind=='dna':
        y=cards([('UUID','Identité stable du dossier'),('Révision','Version du contenu')],y,80)
        y=cards([('ADN SHA-256','Contenu et métadonnées de la version'),('SHA-256 PDF','Octets du fichier final archivé')],y,92);y=steps(items,LEFT,y,USABLE)
    elif kind=='footer':
        image=Image.open(illustrations/'pied-page.png').convert('RGB');buffer=BytesIO();image.save(buffer,format='PNG');buffer.seek(0);h=USABLE*image.height/image.width
        canvas.drawImage(ImageReader(buffer),LEFT,y-h,width=USABLE,height=h);y-=h+12
        x=LEFT
        for item in FOOTER['social']:
            draw_icon(canvas,item['key'],x,y-12,12);canvas.linkURL(item['url'],(x-2,y-15,x+14,y+2),relative=0,thickness=0);x+=26
        para('Icônes cliquables dans ce guide et dans le PDF administratif final.',LEFT,y-25,USABLE,SMALL);y-=48;y=steps(items,LEFT,y,USABLE)
    elif kind=='checklist':
        y=cards([('Préparer','Données exactes et aperçu relu'),('Valider','Tâches attribuées et visas tracés'),('Vérifier','Version, ADN, QR et sortie')],y,100);y=steps(items,LEFT,y,USABLE)
        y=table([['Avant de terminer','Point à contrôler'],['Document','Identité de l’agent, dates, destinataire, signataire.'],['Circuit','Révision identique, décisions et responsables connus.'],['Sortie','A4, pied de page complet, liens et QR lisibles.'],['Traçabilité','UUID, ADN, empreinte PDF et historique disponibles.']],[140,USABLE-140],y-4)
    elif kind=='sources':
        y=steps(items,LEFT,y,USABLE)
        links=[('Démonstration SIGDA','https://propheticpowerfulman.github.io/SIGDA/'),('Présidence de la RDC : source des liens sociaux','https://presidence.cd/'),('Manuel SSDC : démarche de référence','https://github.com/PropheticPowerfulMan/ssdc/tree/main/docs/manual'),('Django : préparation d’un déploiement sécurisé','https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/')]
        for label,url in links:
            y-=para('<a href="'+escape(url,{'"':'&quot;'})+'" color="#173e61"><u>'+plain(label)+'</u></a>',LEFT,y,USABLE,BODY,html=True)+7
        y-=12;y-=para('Identifiant d’édition : '+IDENTIFIER,LEFT,y,USABLE,SMALL)+8
        y-=para('Empreinte des textes et captures : '+SOURCE_HASH,LEFT,y,USABLE,SMALL)+12
    else:
        available=y-82-note_h-steps_height(items,USABLE)-30
        maxheight=min(320,available)
        if maxheight<165:raise ValueError('Capture trop petite dans le chapitre '+str(index))
        used=photo(content['screen'],LEFT,y,USABLE,maxheight-24);y-=used+8;y=steps(items,LEFT,y,USABLE)
    note(content['note'],y-6);canvas.showPage()


destination=OUTPUT/'Guide_utilisateur_SIGDA_demo.pdf'
canvas=Canvas(str(destination),pagesize=A4,pageCompression=1)
canvas.setTitle('SIGDA - Guide d’utilisation illustré - Démonstration')
canvas.setAuthor('Équipe projet SIGDA');canvas.setSubject(IDENTIFIER+' · ADN d’édition '+SOURCE_HASH);canvas.setKeywords('SIGDA, guide, OPS, SECAD, AP, DIRCAB, démonstration')
cover();contents()
for index,content in enumerate(CHAPTERS,1):chapter(index,content)
for offset in range(0,len(ATLAS),2):
    frame(len(CHAPTERS)+3+offset//2)
    if offset==0:canvas.bookmarkPage('atlas');canvas.addOutlineEntry('Atlas des écrans complémentaires','atlas',level=0)
    para('Atlas des écrans',LEFT,HEIGHT-72,USABLE,TITLE)
    para('Captures réelles complémentaires : navigation, apparence, consultation et suivi des réponses. Les environnements sont indiqués sous chaque image.',LEFT,HEIGHT-108,USABLE,SMALL)
    for position,filename in enumerate(ATLAS[offset:offset+2]):photo(filename,LEFT,HEIGHT-138-position*330,USABLE,260)
    canvas.showPage()
canvas.save()
data=destination.read_bytes();published=DOCS/'Guide_utilisateur_SIGDA_demo.pdf';published.write_bytes(data)
manifest={'edition':'2026-11-12','id':IDENTIFIER,'pages':PAGES,'chapters':len(CHAPTERS),'captures':len(REGISTRY),'source_sha256':SOURCE_HASH,'pdf_sha256':sha256(data).hexdigest(),'bytes':len(data),'file':published.name}
(DOCS/'guide_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=True))
