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


EMBLEM = Path(__file__).parent / "static" / "sigda" / "EmblemRDC.jpg"
WIDTH, HEIGHT = A4
MARGIN = 60
INK = HexColor("#152A43")
BODY = ParagraphStyle("body", fontName="Helvetica", fontSize=11, leading=17, alignment=TA_JUSTIFY)


def draw_paragraph(page: Canvas, text: str, top: float) -> float:
    paragraph = Paragraph(text, BODY)
    _, height = paragraph.wrap(WIDTH - 2 * MARGIN, HEIGHT)
    paragraph.drawOn(page, MARGIN, top - height)
    return top - height - 16


def draw_standard_body(page: Canvas, key: str, agent: Agent) -> float:
    identity = f"<b>{escape(agent.name)}</b>, matricule <b>{escape(agent.registration)}</b>"
    if key == "attestation-nuit":
        paragraphs = (
            f"Dans ce scénario de démonstration, il est attesté que {identity}, exerce au "
            f"{escape(agent.service)} en qualité de {escape(agent.job)} et assure le service de nuit.",
            "Cette attestation illustre la présentation d’un document de service.",
        )
    elif key == "attestation-service":
        paragraphs = (
            f"Il est attesté, pour les besoins de cette démonstration, que {identity}, exerce au "
            f"{escape(agent.service)} en qualité de {escape(agent.job)}.",
            f"<b>Grade renseigné</b> · {escape(agent.grade)}.",
        )
    elif key == "convocation":
        paragraphs = (
            f"<b>Destinataire</b> · {identity}.",
            "<b>Objet</b> · Entretien de mise à jour du dossier administratif.",
            "<b>Lieu indicatif</b> · Service des ressources humaines, Kinshasa.",
            "Dans ce scénario fictif, la date et l’heure sont communiquées séparément par le service.",
        )
    elif key == "bordereau-transmission":
        paragraphs = (
            f"<b>Dossier concerné</b> · {identity}.",
            f"<b>Service expéditeur</b> · {escape(agent.service)}.",
            "<b>Service destinataire</b> · Service des ressources humaines.",
            "<b>Pièce transmise</b> · Une fiche de situation administrative fictive, pour vérification.",
        )
    else:
        raise ValueError(f"Modèle de document sans contenu : {key}")

    top = 531
    for paragraph in paragraphs:
        top = draw_paragraph(page, paragraph, top)
    return top


def render_pdf(
    key: str, document: DocumentType, agent: Agent, reference: str, date_label: str
) -> bytes:
    output = BytesIO()
    page = Canvas(output, pagesize=A4)
    page.setTitle(f"{document.title} — Spécimen SIGDA")
    page.setAuthor("SIGDA — Démonstration")
    page.setFillColor(INK)
    page.setFont("Helvetica-Bold", 11)
    page.drawCentredString(WIDTH / 2, 804, "RÉPUBLIQUE DÉMOCRATIQUE DU CONGO")
    page.drawImage(str(EMBLEM), WIDTH / 2 - 36, 723, width=72, height=72)
    page.setFont("Helvetica", 10)
    page.drawCentredString(WIDTH / 2, 704, "SECRÉTARIAT GÉNÉRAL AUPRÈS DU PRÉSIDENT DE LA RÉPUBLIQUE")

    page.setFillColor(HexColor("#963238"))
    page.setFont("Helvetica-Bold", 11)
    page.drawCentredString(WIDTH / 2, 677, "SPÉCIMEN — NON VALABLE")
    page.setFillColor(INK)
    page.setFont("Helvetica", 10)
    page.drawString(MARGIN, 645, f"N/Réf. : {reference}")
    page.drawRightString(WIDTH - MARGIN, 645, f"Kinshasa, le {date_label}")

    if key == "notification":
        page.setFont("Helvetica", 9)
        page.drawString(324, 614, "Copie pour information")
        page.drawString(324, 601, "Service des ressources humaines")
        page.setFont("Helvetica-Bold", 11)
        page.drawString(324, 575, f"À {agent.name}")
        page.setFont("Helvetica", 10)
        page.drawString(324, 557, agent.service)
        page.drawString(324, 540, "Kinshasa – Gombe")
        page.setFont("Helvetica-Bold", 12)
        page.drawString(MARGIN, 498, "Concerne : Régularisation de votre situation administrative")
        top = draw_paragraph(page, "Madame, Monsieur,", 468)
        top = draw_paragraph(
            page,
            "Dans le cadre de cet exemple, nous vous informons de la mise à jour "
            "de votre situation administrative.",
            top,
        )
        top = draw_paragraph(
            page,
            f"Le grade renseigné dans ce dossier fictif est <b>{escape(agent.grade)}</b>, "
            f"sous le matricule de démonstration <b>{escape(agent.registration)}</b>.",
            top,
        )
        top = draw_paragraph(page, "Veuillez agréer nos salutations distinguées.", top)
    else:
        page.setFont("Helvetica-Bold", 15)
        title = document.title.upper()
        page.drawCentredString(WIDTH / 2, 575, title)
        title_width = page.stringWidth(title, "Helvetica-Bold", 15)
        page.line((WIDTH - title_width) / 2, 571, (WIDTH + title_width) / 2, 571)
        top = draw_standard_body(page, key, agent)

    page.setFont("Helvetica", 10)
    page.drawRightString(WIDTH - MARGIN, top - 35, f"Fait à Kinshasa, le {date_label}")
    page.setStrokeColor(INK)
    page.roundRect(300, top - 132, WIDTH - MARGIN - 300, 72, 4)
    page.setFont("Helvetica", 9)
    page.drawString(312, top - 78, "Signature et cachet")
    page.line(MARGIN, 58, WIDTH - MARGIN, 58)
    page.drawCentredString(WIDTH / 2, 41, "SIGDA  •  Modèle de démonstration  •  Données fictives")
    page.showPage()
    page.save()
    return output.getvalue()
