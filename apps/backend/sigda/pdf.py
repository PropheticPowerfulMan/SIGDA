from io import BytesIO
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph

from .catalog import Agent, DocumentType
from .document_qr import specimen_link
from .document_fonts import BODY_FONT
from .document_identity import identity as make_identity
from .social_icons import draw_icon

FOOTER = json.loads((Path(__file__).resolve().parents[3] / "config/institutional_links.json").read_text(encoding="utf-8"))
from .wording import document_text


EMBLEM = Path(__file__).parent / "static" / "sigda" / "EmblemRDC.jpg"
WIDTH, HEIGHT = A4
MARGIN = 60
INK = HexColor("#151515")


def right_date(page, text, top):
    for size in (10, 9, 8):
        block = Paragraph(escape(text), ParagraphStyle("date", fontName="Helvetica", fontSize=size, leading=size + 1, alignment=TA_RIGHT))
        _, height = block.wrap(220, 40)
        if height <= 22:
            block.drawOn(page, WIDTH - MARGIN - 220, top - height)
            return
    raise ValueError("Le lieu d’établissement est trop long. Indiquez seulement la ville.")


def institutional_footer(page, key, reference, date_label, style, text, dna, verification_url=None):
    """Full-width two-row contact strip, social URI annotations and document DNA."""
    page.saveState()
    page.translate(0,10)
    left=24; right=WIDTH-24; qr_size=72; qr_x=right-qr_size; text_right=qr_x-12
    start=left
    for ratio,colour in ((.4,'#174e85'),(.3,'#c6993e'),(.3,'#ac2535')):
        page.setFillColor(HexColor(colour));page.rect(start,89,(right-left)*ratio,3,stroke=0,fill=1);start+=(right-left)*ratio
    page.setFillColor(HexColor('#40464d'));page.setFont('Helvetica',7)
    for x,label,url in ((left,FOOTER['phone'],'tel:+243819402122'),(140,FOOTER['email'],'mailto:'+FOOTER['email']),(265,FOOTER['website_label'],FOOTER['website'])):
        page.drawString(x,73,label);page.linkURL(url,(x,71,x+page.stringWidth(label,'Helvetica',7),81),relative=1,thickness=0)
    icon_size=10;gap=4;start=text_right-(len(FOOTER['social'])*icon_size+(len(FOOTER['social'])-1)*gap)
    for item in FOOTER['social']:
        draw_icon(page,item['key'],start,71,icon_size);page.linkURL(item['url'],(start-1,69,start+icon_size+1,83),relative=1,thickness=0);start+=icon_size+gap
    page.setFont('Helvetica',6.8);page.drawString(left,58,'Palais de la Nation,');page.drawString(140,58,FOOTER['address']);page.drawRightString(text_right,58,FOOTER['postal'])
    page.setFont('Helvetica',6.2)
    reference_label=reference+' · Révision '+str(dna['revision'])
    if page.stringWidth(reference_label,'Helvetica',6.2)>text_right-left:raise ValueError('La référence dépasse la largeur du pied de page.')
    page.drawString(left,42,reference_label);page.setFont('Helvetica-Bold',6.2);page.drawString(left,28,'ADN numérique · '+dna['label'])
    page.setFillColor(HexColor('#963238'));page.setFont('Helvetica-Bold',6);page.drawString(left,14,'SPÉCIMEN - NON VALABLE · Données fictives')
    url=verification_url or specimen_link(key,reference,date_label,style,text,identity=dna)
    code=QrCodeWidget(url,barLevel='M',barBorder=4,barFillColor=colors.black);x0,y0,x1,y1=code.getBounds()
    drawing=Drawing(qr_size,qr_size,transform=[qr_size/(x1-x0),0,0,qr_size/(y1-y0),0,0]);drawing.add(code)
    page.setFillColor(colors.white);page.rect(qr_x,14,qr_size,qr_size,fill=1,stroke=0);renderPDF.draw(drawing,page,qr_x,14)
    page.linkURL(url,(qr_x,14,qr_x+qr_size,14+qr_size),relative=1,thickness=0);page.setFont('Helvetica',5.8);page.setFillColor(HexColor('#40464d'));page.drawCentredString(qr_x+qr_size/2,7,'Vérifier le document')
    page.restoreState()


def centered_title(page, text, top):
    size = 14
    while page.stringWidth(text, "Helvetica-Bold", size) > WIDTH - 2 * MARGIN:
        size -= 0.5
    page.setFont("Helvetica-Bold", size)
    page.drawCentredString(WIDTH / 2, top, text)
    title_width = page.stringWidth(text, "Helvetica-Bold", size)
    page.line((WIDTH - title_width) / 2, top - 4, (WIDTH + title_width) / 2, top - 4)


def body_watermark(page, top, bottom):
    """A faint emblem behind the writing area; restore full opacity for text."""
    size = min(250, top - bottom)
    page.saveState()
    page.setFillAlpha(0.045)
    page.drawImage(str(EMBLEM), (WIDTH - size) / 2, (top + bottom - size) / 2,
                   width=size, height=size, preserveAspectRatio=True, mask='auto')
    page.restoreState()


def render_body(page, text, top, bottom=220):
    lines = [line.strip() for line in text.split("\n\n") if line.strip()]
    for size, leading in ((12, 18), (11.5, 17), (11, 16)):
        style = ParagraphStyle("body", fontName=BODY_FONT, fontSize=size,
                               leading=leading, alignment=TA_JUSTIFY,
                               firstLineIndent=(WIDTH - 2 * MARGIN) / 2)
        paragraphs = [Paragraph(escape(line).replace("\n", "<br/>"), style) for line in lines]
        heights = [paragraph.wrap(WIDTH - 2 * MARGIN, HEIGHT)[1] for paragraph in paragraphs]
        if sum(heights) + max(0, len(lines) - 1) * 14 <= top - bottom:
            break
    else:
        raise ValueError("Le texte est trop long pour cette mise en page A4. Réduisez-le.")
    for paragraph, height in zip(paragraphs, heights):
        paragraph.drawOn(page, MARGIN, top - height)
        top -= height + 14
    return top


def certificate_header(page, document, reference, date_label, context=None):
    page.setFont("Times-Italic", 16)
    page.drawCentredString(WIDTH / 2, 808, "République Démocratique du Congo")
    page.drawImage(str(EMBLEM), WIDTH / 2 - 37, 722, width=74, height=74)
    page.setFont("Times-Roman", 11)
    page.drawCentredString(WIDTH / 2, 700, "CABINET DU PRÉSIDENT DE LA RÉPUBLIQUE")
    page.setFont("Times-Italic", 10)
    place = context["place"] if context else "Kinshasa"
    if context:
        block = Paragraph(escape(context["issuer_service"]), ParagraphStyle("issuer", fontName="Times-Italic", fontSize=10, leading=11))
        _, height = block.wrap(220, 40)
        block.drawOn(page, MARGIN, 680 - height)
    else:
        page.drawString(MARGIN, 670, "Service des ressources humaines")
    if context:
        right_date(page, f"{place}, le {date_label}", 680)
    else:
        page.drawRightString(WIDTH - MARGIN, 670, f"{place}, le {date_label}")
    page.drawString(MARGIN, 640 if context else 652, f"N/Réf. : {reference}")
    centered_title(page, document.title.upper(), 575)
    return 532


def letter_header(page, key, document, agent, reference, date_label, context=None):
    page.setFont("Helvetica", 12)
    page.drawCentredString(WIDTH / 2, 805, "RÉPUBLIQUE DÉMOCRATIQUE DU CONGO")
    page.drawCentredString(WIDTH / 2, 786, "PRÉSIDENCE DE LA RÉPUBLIQUE")
    page.line(195, 778, 400, 778)
    page.setFont("Helvetica", 8)
    page.drawString(MARGIN, 750, "CABINET DU PRÉSIDENT")
    page.drawString(MARGIN, 739, "DU PRÉSIDENT DE LA RÉPUBLIQUE")
    place = context["place"] if context else "Kinshasa"
    if context:
        right_date(page, f"{place}, le {date_label}", 760)
    else:
        page.drawRightString(WIDTH - MARGIN, 750, f"{place}, le {date_label}")
    page.drawImage(str(EMBLEM), 94, 675, width=55, height=55)
    page.setFont("Times-Italic", 10)
    if context:
        block = Paragraph(escape(context["issuer_service"]), ParagraphStyle("issuer", fontName="Times-Italic", fontSize=10, leading=11))
        _, height = block.wrap(220, 40)
        block.drawOn(page, MARGIN, 670 - height)
    else:
        page.drawString(MARGIN, 659, "Service des ressources humaines")
    page.setFont("Helvetica", 10)
    page.drawString(MARGIN, 623 if context else 638, f"N/Réf. : {reference}")
    page.setFont("Helvetica", 8)
    page.drawString(308, 613, "Copie pour information")
    page.drawString(308, 601, "Service concerné")
    page.setFont("Helvetica-Bold", 10)
    destination = "Au service des ressources humaines" if key in {"bordereau-transmission", "lettre-transmission", "note-service"} else f"À {agent.name}"
    if context:
        destination = context.get("recipient") or f"À {agent.name}"
        block = Paragraph(escape(destination), ParagraphStyle("recipient", fontName="Helvetica-Bold", fontSize=10, leading=12))
        _, height = block.wrap(WIDTH - MARGIN - 308, 60)
        block.drawOn(page, 308, 590 - height)
    else:
        page.drawString(308, 577, destination)
    page.setFont("Helvetica", 9)
    page.drawString(308, 548 if context else 560, "à " + place.upper() if context else "à KINSHASA – GOMBE")
    if key in {"notification", "convocation", "lettre-transmission"}:
        page.setFont("Helvetica-Bold", 11)
        page.drawString(MARGIN, 516, "Concerne : " + document.title)
    else:
        centered_title(page, document.title.upper(), 516)
    return 478


def render_pdf(key: str, document: DocumentType, agent: Agent, reference: str, date_label: str,
               *, wording="classique", body_text=None, context=None, preview_only=False, identity=None, verification_url=None) -> bytes:
    output = BytesIO()
    page = Canvas(output, pagesize=A4)
    page.setTitle(f"{document.title} — Spécimen SIGDA")
    page.setAuthor("SIGDA — Démonstration")
    page.setFillColor(INK)
    page.setStrokeColor(INK)
    if document.category == "Attestations":
        top = certificate_header(page, document, reference, date_label, context)
        specimen_y = 624
    else:
        top = letter_header(page, key, document, agent, reference, date_label, context)
        specimen_y = 825
    page.setFillColor(HexColor("#963238"))
    page.setFont("Helvetica-Bold", 9)
    page.drawCentredString(WIDTH / 2, specimen_y, "SPÉCIMEN — NON VALABLE")
    page.setFillColor(INK)
    text = document_text(key, agent, date_label, wording) if body_text is None else body_text
    body_bottom = 310 if key == "bordereau-transmission" else 220
    body_watermark(page, top, body_bottom)
    top = render_body(page, text, top, bottom=body_bottom)
    if key == "bordereau-transmission":
        # A transmission slip also identifies the enclosed item independently of prose.
        top -= 5
        page.rect(MARGIN, top - 54, WIDTH - 2 * MARGIN, 54)
        page.line(MARGIN, top - 22, WIDTH - MARGIN, top - 22)
        page.line(390, top, 390, top - 54)
        page.setFont("Helvetica-Bold", 9)
        page.drawString(MARGIN + 8, top - 15, "Désignation de la pièce")
        page.drawString(398, top - 15, "Nombre")
        page.setFont("Helvetica", 9)
        item = context["item"] if context else "Fiche de situation administrative"
        block = Paragraph(escape(item), ParagraphStyle("item", fontName=BODY_FONT, fontSize=9, leading=10))
        _, height = block.wrap(310, 28)
        if height > 27:
            raise ValueError("Raccourcissez la désignation des pièces pour préserver le tableau du bordereau.")
        block.drawOn(page, MARGIN + 8, top - 27 - height)
        page.drawString(398, top - 41, context["quantity"] if context else "1")
        top -= 68
    signature_y = min(top - 35, 270)
    page.setFont("Helvetica", 10)
    place = context["place"] if context else "Kinshasa"
    if context:
        right_date(page, f"Fait à {place}, le {date_label}", signature_y + 10)
    else:
        page.drawRightString(WIDTH - MARGIN, signature_y, f"Fait à {place}, le {date_label}")
    page.setFont("Helvetica-Bold", 10)
    label = (context.get("signatory") or context["signatory_role"]) if context else "Autorité habilitée"
    block = Paragraph(escape(label), ParagraphStyle("signatory", fontName="Helvetica-Bold", fontSize=10, leading=11))
    _, height = block.wrap(WIDTH - MARGIN - 325, 35)
    if height > 22:
        raise ValueError("Raccourcissez le nom ou la qualité du signataire pour préserver sa zone de signature.")
    block.drawOn(page, 325, signature_y - 22 - height)
    page.setFont("Helvetica", 9)
    page.drawString(325, signature_y - 54, "Signature et cachet")
    dna = identity or make_identity(key, reference, date_label, wording if body_text is None else 'personnalise', text, context)
    page.setSubject('Identité '+dna['id']+' · Révision '+str(dna['revision']))
    page.setKeywords('SIGDA, '+dna['schema']+', '+dna['hash'])
    institutional_footer(page, key, reference, date_label,
                         wording if body_text is None else "personnalise", text, dna, verification_url)
    if preview_only:
        page.saveState()
        page.setFillColor(HexColor("#ac5a5a"))
        page.setFillAlpha(0.25)
        page.translate(WIDTH / 2, HEIGHT / 2)
        page.rotate(32)
        page.setFont("Helvetica-Bold", 32)
        page.drawCentredString(0, 0, "APERÇU — NON VALIDÉ")
        page.restoreState()
    page.showPage()
    page.save()
    return output.getvalue()
