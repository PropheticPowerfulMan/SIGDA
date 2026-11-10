from contextlib import closing
from io import BytesIO
from threading import Lock

import pypdfium2 as pdfium


_PDFIUM_LOCK = Lock()


def render_preview(pdf: bytes) -> bytes:
    """Rasteriser la première page du spécimen généré par SIGDA."""
    output = BytesIO()
    # PDFium exige de sérialiser les appels entre les threads du serveur.
    with _PDFIUM_LOCK, closing(pdfium.PdfDocument(pdf)) as document:
        with closing(document[0]) as page, closing(page.render(scale=1.75)) as bitmap:
            with bitmap.to_pil() as image:
                image.save(output, format="PNG")
    return output.getvalue()
