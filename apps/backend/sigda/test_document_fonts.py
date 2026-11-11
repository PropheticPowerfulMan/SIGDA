from unittest.mock import patch

from django.test import SimpleTestCase

from .catalog import AGENTS, DOCUMENT_TYPES
from .document_fonts import register_body_font
from .pdf import render_pdf


class DocumentFontTests(SimpleTestCase):
    def test_document_embeds_real_times_new_roman(self):
        pdf = render_pdf("attestation-service", DOCUMENT_TYPES["attestation-service"],
                         AGENTS["alpha"], "SPEC-ATS-DEMO-001-2026", "15 janvier 2026")
        self.assertIn(b"TimesNewRomanPSMT", pdf)
        self.assertIn(b"/FontFile2", pdf)

    def test_missing_configured_font_is_reported_without_substitution(self):
        with patch("sigda.document_fonts.environ", {"SIGDA_TIMES_NEW_ROMAN": "absent-times-new-roman.ttf"}):
            with self.assertRaisesRegex(RuntimeError, "Times New Roman est requise"):
                register_body_font()
