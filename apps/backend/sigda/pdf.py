from io import BytesIO
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


def institutional_footer(page, key, reference, date_label, style, text):
    """Two contact rows, a tricolour rule and a printable QR with a quiet zone."""
    page.saveState()
    width = WIDTH - 2 * MARGIN
    start = MARGIN
    for ratio, colour in ((0.40, "#174e85"), (0.30, "#c6993e"), (0.30, "#ac2535")):
        page.setFillColor(HexColor(colour))
        page.rect(start, 96, width * ratio, 3, stroke=0, fill=1)
        start += width * ratio

    page.setFillColor(HexColor("#40464d"))
    page.setFont("Helvetica", 7)
    for x, first, second in (
        (MARGIN, "+243 81 940 21 22", "Palais de la Nation"),
        (178, "sgpr@presidence.cd", "Avenue Roi Baudouin, Gombe"),
        (333, "www.presidence.cd", "Kinshasa · B.P. 201 Kin 38"),
    ):
        page.drawString(x, 80, first)
        page.drawString(x, 66, second)

    page.setFont("Helvetica", 6.5)
    page.drawString(MARGIN, 44, reference + " · Empreinte du texte dans le QR")
    page.setFillColor(HexColor("#963238"))
    page.setFont("Helvetica-Bold", 6.5)
    page.drawString(MARGIN, 29, "SPÉCIMEN — NON VALABLE · Données fictives")

    size = 68
    qr_x = WIDTH - MARGIN - size
    # Explicit black/white and four-module quiet zone remain readable in both themes.
    code = QrCodeWidget(specimen_link(key, reference, date_label, style, text),
                        barLevel="M", barBorder=4, barFillColor=colors.black)
    x0, y0, x1, y1 = code.getBounds()
    drawing = Drawing(size, size, transform=[size / (x1 - x0), 0, 0, size / (y1 - y0), 0, 0])
    drawing.add(code)
    page.setFillColor(colors.white)
    page.rect(qr_x, 24, size, size, fill=1, stroke=0)
    renderPDF.draw(drawing, page, qr_x, 24)
    page.linkURL(specimen_link(key, reference, date_label, style, text),
                 (qr_x, 24, qr_x + size, 24 + size), relative=0, thickness=0)
    page.setFont("Helvetica", 6)
    page.setFillColor(HexColor("#40464d"))
    page.drawCentredString(qr_x + size / 2, 18, "Fiche du spécimen")
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
               *, wording="classique", body_text=None, context=None, preview_only=False) -> bytes:
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
    institutional_footer(page, key, reference, date_label,
                         wording if body_text is None else "personnalise", text)
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
