from itertools import product

from django.test import SimpleTestCase
from django.urls import reverse

from .catalog import AGENTS, DOCUMENT_TYPES


class WorkspaceTests(SimpleTestCase):
    def test_selection_updates_the_preview_and_download(self):
        url = reverse("specimen", args=["notification", "beta"])
        response = self.client.get("/", {"agent": "beta", "type": "notification"})
        self.assertContains(response, "Dominique Témoin")
        self.assertContains(response, "SIGDA et SSDC sont deux projets indépendants.")
        self.assertContains(response, f'src="{url}"')
        self.assertContains(response, f'href="{url}?download=1"')

    def test_unknown_agent_and_model_return_404(self):
        self.assertEqual(self.client.get("/", {"agent": "unknown"}).status_code, 404)
        self.assertEqual(self.client.get("/", {"type": "unknown"}).status_code, 404)
        self.assertEqual(self.client.get("/specimens/notification/unknown.pdf").status_code, 404)
        self.assertEqual(self.client.get("/specimens/unknown/alpha.pdf").status_code, 404)

    def test_all_agent_and_model_pairs_render_a_pdf(self):
        for key, agent in product(DOCUMENT_TYPES, AGENTS):
            with self.subTest(document=key, agent=agent):
                url = reverse("specimen", args=[key, agent])
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["Content-Type"], "application/pdf")
                self.assertEqual(response["X-Frame-Options"], "SAMEORIGIN")
                self.assertIn("no-store", response["Cache-Control"])
                self.assertTrue(response.content.startswith(b"%PDF-"))
                self.assertTrue(response["Content-Disposition"].startswith("inline;"))

    def test_download_uses_attachment_disposition_and_specimen_reference(self):
        url = reverse("specimen", args=["attestation-nuit", "alpha"])
        response = self.client.get(url, {"download": "1"})
        self.assertRegex(response["Content-Disposition"], r'^attachment; filename="SPEC-ATN-DEMO-001-\d{4}\.pdf"$')

    def test_demo_endpoints_reject_post(self):
        self.assertEqual(self.client.post("/").status_code, 405)
        self.assertEqual(self.client.post("/specimens/notification/beta.pdf").status_code, 405)
