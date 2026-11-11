from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph

from .catalog import Agent, DocumentType
from .wording import document_text


EMBLEM = Path(__file__).parent / "static" / "sigda" / "EmblemRDC.jpg"
WIDTH, HEIGHT = A4
MARGIN = 60
INK = HexColor("#151515")


def centered_title(page, text, top):
    size = 14
    while page.stringWidth(text, "Helvetica-Bold", size) > WIDTH - 2 * MARGIN:
        size -= 0.5
    page.setFont("Helvetica-Bold", size)
    page.drawCentredString(WIDTH / 2, top, text)
    title_width = page.stringWidth(text, "Helvetica-Bold", size)
    page.line((WIDTH - title_width) / 2, top - 4, (WIDTH + title_width) / 2, top - 4)


def render_body(page, text, top, bottom=220):
    lines = [line.strip() for line in text.split("\n\n") if line.strip()]
    for size, leading in ((11, 17), (10.5, 15.5), (10, 14)):
        style = ParagraphStyle("body", fontName="Helvetica", fontSize=size,
                               leading=leading, alignment=TA_JUSTIFY)
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


def certificate_header(page, document, reference, date_label):
    page.setFont("Times-Italic", 16)
    page.drawCentredString(WIDTH / 2, 808, "République Démocratique du Congo")
    page.drawImage(str(EMBLEM), WIDTH / 2 - 37, 722, width=74, height=74)
    page.setFont("Times-Roman", 11)
    page.drawCentredString(WIDTH / 2, 700, "SECRÉTARIAT GÉNÉRAL AUPRÈS DU PRÉSIDENT DE LA RÉPUBLIQUE")
    page.setFont("Times-Italic", 10)
    page.drawString(MARGIN, 670, "Service des ressources humaines")
    page.drawRightString(WIDTH - MARGIN, 670, f"Kinshasa, le {date_label}")
    page.drawString(MARGIN, 652, f"N/Réf. : {reference}")
    centered_title(page, document.title.upper(), 575)
    return 532


def letter_header(page, key, document, agent, reference, date_label):
    page.setFont("Helvetica", 12)
    page.drawCentredString(WIDTH / 2, 805, "RÉPUBLIQUE DÉMOCRATIQUE DU CONGO")
    page.drawCentredString(WIDTH / 2, 786, "PRÉSIDENCE DE LA RÉPUBLIQUE")
    page.line(195, 778, 400, 778)
    page.setFont("Helvetica", 8)
    page.drawString(MARGIN, 750, "SECRÉTARIAT GÉNÉRAL AUPRÈS")
    page.drawString(MARGIN, 739, "DU PRÉSIDENT DE LA RÉPUBLIQUE")
    page.drawRightString(WIDTH - MARGIN, 750, f"Kinshasa, le {date_label}")
    page.drawImage(str(EMBLEM), 94, 675, width=55, height=55)
    page.setFont("Times-Italic", 10)
    page.drawString(MARGIN, 659, "Service des ressources humaines")
    page.setFont("Helvetica", 10)
    page.drawString(MARGIN, 638, f"N/Réf. : {reference}")
    page.setFont("Helvetica", 8)
    page.drawString(308, 613, "Copie pour information")
    page.drawString(308, 601, "Service concerné")
    page.setFont("Helvetica-Bold", 10)
    destination = "Au service des ressources humaines" if key in {"bordereau-transmission", "lettre-transmission", "note-service"} else f"À {agent.name}"
    page.drawString(308, 577, destination)
    page.setFont("Helvetica", 9)
    page.drawString(308, 560, "à KINSHASA – GOMBE")
    if key in {"notification", "convocation", "lettre-transmission"}:
        page.setFont("Helvetica-Bold", 11)
        page.drawString(MARGIN, 516, "Concerne : " + document.title)
    else:
        centered_title(page, document.title.upper(), 516)
    return 478


def render_pdf(key: str, document: DocumentType, agent: Agent, reference: str, date_label: str,
               *, wording="classique", body_text=None) -> bytes:
    output = BytesIO()
    page = Canvas(output, pagesize=A4)
    page.setTitle(f"{document.title} — Spécimen SIGDA")
    page.setAuthor("SIGDA — Démonstration")
    page.setFillColor(INK)
    page.setStrokeColor(INK)
    if document.category == "Attestations":
        top = certificate_header(page, document, reference, date_label)
        specimen_y = 624
    else:
        top = letter_header(page, key, document, agent, reference, date_label)
        specimen_y = 825
    page.setFillColor(HexColor("#963238"))
    page.setFont("Helvetica-Bold", 9)
    page.drawCentredString(WIDTH / 2, specimen_y, "SPÉCIMEN — NON VALABLE")
    page.setFillColor(INK)
    text = document_text(key, agent, date_label, wording) if body_text is None else body_text
    top = render_body(page, text, top, bottom=310 if key == "bordereau-transmission" else 220)
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
        page.drawString(MARGIN + 8, top - 41, "Fiche de situation administrative")
        page.drawString(398, top - 41, "1")
        top -= 68
    signature_y = min(top - 35, 270)
    page.setFont("Helvetica", 10)
    page.drawRightString(WIDTH - MARGIN, signature_y, f"Fait à Kinshasa, le {date_label}")
    page.setFont("Helvetica-Bold", 10)
    page.drawString(325, signature_y - 31, "Autorité habilitée")
    page.setFont("Helvetica", 9)
    page.drawString(325, signature_y - 54, "Signature et cachet")
    page.line(MARGIN, 58, WIDTH - MARGIN, 58)
    page.setFont("Times-Roman", 9)
    page.drawCentredString(WIDTH / 2, 41, "SIGDA · Kinshasa / Gombe · Données fictives · Spécimen")
    page.showPage()
    page.save()
    return output.getvalue()
