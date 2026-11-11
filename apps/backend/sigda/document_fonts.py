from os import environ, name as platform_name
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def register_body_font():
    configured = environ.get("SIGDA_TIMES_NEW_ROMAN")
    if configured:
        candidates = [Path(configured)]
    elif platform_name == "nt":
        candidates = [Path(environ.get("WINDIR", "C:/Windows")) / "Fonts" / "times.ttf"]
    else:
        candidates = [
            Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf"),
            Path("/Library/Fonts/Times New Roman.ttf"),
            Path("/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf"),
            Path("/usr/share/fonts/truetype/msttcorefonts/times.ttf"),
        ]
    path = next((path for path in candidates if path.is_file()), None)
    if path is None:
        raise RuntimeError("Times New Roman est requise. Définissez SIGDA_TIMES_NEW_ROMAN avec le chemin du fichier times.ttf installé sous licence.")
    font = TTFont("SIGDA-TimesNewRoman", str(path))
    if font.face.familyName != b"Times New Roman":
        raise RuntimeError("SIGDA_TIMES_NEW_ROMAN doit désigner la véritable police Times New Roman.")
    pdfmetrics.registerFont(font)
    return font.fontName, path


# Module initialization registers the font once, before request threads use it.
BODY_FONT, BODY_FONT_PATH = register_body_font()
