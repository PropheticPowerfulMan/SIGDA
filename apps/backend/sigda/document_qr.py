from hashlib import sha256
from urllib.parse import urlencode


SPECIMEN_SHEET_URL = "https://propheticpowerfulman.github.io/SIGDA/fiche.html"


def specimen_link(key, reference, date_label, style, text):
    """Describe the specimen without exposing its body or personal names in the QR."""
    fields = {
        "m": key,
        "r": reference,
        "d": date_label,
        "s": style,
        "h": sha256(text.encode("utf-8")).hexdigest(),
    }
    # The fragment is read locally by the sheet, rather than sent to the host.
    return SPECIMEN_SHEET_URL + "#" + urlencode(fields)
