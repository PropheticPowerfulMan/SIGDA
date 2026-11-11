from base64 import b64decode
from hashlib import sha256
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .catalog import AGENTS, format_date
from .document_qr import specimen_link
from .wording import document_text


class DocumentQrTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create_user("qr-test"))
        self.date = format_date(timezone.localdate())
        self.reference = f"SPEC-ATS-DEMO-001-{timezone.localdate().year}"

    def test_qr_describes_text_without_including_its_body_or_personal_name(self):
        text = document_text("attestation-service", AGENTS["alpha"], self.date)
        url = urlsplit(specimen_link("attestation-service", self.reference, self.date, "classique", text))
        self.assertEqual(url.scheme, "https")
        self.assertEqual(url.netloc, "propheticpowerfulman.github.io")
        self.assertEqual(url.path, "/SIGDA/fiche.html")
        self.assertEqual(url.query, "")
        fields = parse_qs(url.fragment)
        self.assertEqual(fields["h"], [sha256(text.encode()).hexdigest()])
        self.assertEqual(fields["r"], [self.reference])
        self.assertNotIn(AGENTS["alpha"].name, str(fields))
        self.assertNotIn(text, str(fields))

    def test_selected_wording_is_the_text_referenced_by_the_pdf_link(self):
        for style in ("classique", "formel", "direct"):
            text = document_text("attestation-service", AGENTS["alpha"], self.date, style)
            expected = specimen_link("attestation-service", self.reference, self.date, style, text)
            response = self.client.get(reverse("specimen", args=["attestation-service", "alpha"]), {"wording": style})
            self.assertEqual(response.status_code, 200)
            self.assertIn(expected.encode("ascii"), response.content)

    def test_custom_preview_qr_follows_the_applied_text(self):
        text = document_text("attestation-service", AGENTS["alpha"], self.date)
        text += "\n\nCette rédaction personnalisée accompagne le dossier."
        response = self.client.post(reverse("document_draft"), {
            "kind": "attestation-service", "agent": "alpha", "wording": "classique",
            "action": "preview", "mode": "local", "text": text,
        })
        self.assertEqual(response.status_code, 200)
        pdf = b64decode(response.json()["pdf"].split(",", 1)[1])
        expected = specimen_link("attestation-service", self.reference, self.date, "personnalise", text)
        self.assertIn(expected.encode("ascii"), pdf)
        windows = self.client.post(reverse("document_draft"), {
            "kind": "attestation-service", "agent": "alpha", "wording": "classique",
            "action": "preview", "mode": "local", "text": text.replace("\n", "\r\n"),
        })
        self.assertEqual(windows.status_code, 200)
        self.assertIn(expected.encode("ascii"), b64decode(windows.json()["pdf"].split(",", 1)[1]))
