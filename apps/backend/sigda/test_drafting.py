from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .catalog import AGENTS, DOCUMENT_TYPES, format_date
from .drafting import validate_facts
from .wording import STYLES, document_text


class DraftingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("draft-test")
        self.client.force_login(self.user)
        cache.clear()
        self.url = reverse("document_draft")
        self.original = document_text("ordre-mission", AGENTS["alpha"], format_date(timezone.localdate()))
        self.payload = {"agent": "alpha", "kind": "ordre-mission", "wording": "classique",
                        "action": "rewrite", "mode": "local", "text": self.original}

    def test_variants_preserve_facts_for_every_model_and_agent(self):
        for key in DOCUMENT_TYPES:
            for agent in AGENTS.values():
                original = document_text(key, agent, "15 janvier 2026")
                variants = {document_text(key, agent, "15 janvier 2026", style) for style in STYLES}
                self.assertEqual(len(variants), 3)
                for text in variants:
                    validate_facts(text, original, agent)
        with patch("sigda.assistant.urlopen") as api:
            response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["wording"], "formel")
        self.assertNotEqual(response.json()["text"], self.original)
        api.assert_not_called()

    def test_auth_csrf_and_preview_cannot_change_identity_or_numbers(self):
        self.assertEqual(Client().post(self.url, self.payload).status_code, 302)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(self.url, self.payload).status_code, 403)
        for text in (self.original.replace("Camille Exemple", "Autre personne"),
                     self.original.replace("1 jour", "3 jours")):
            response = self.client.post(self.url, {**self.payload, "action": "preview", "text": text})
            self.assertEqual(response.status_code, 400)
        response = self.client.post(self.url, {**self.payload, "action": "preview"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("pdf", response.json())
        self.assertTrue(response.json()["preview"].startswith("data:image/png;base64,iVBOR"))
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(self.client.post(self.url, {**self.payload, "text": "x" * 1801}).status_code, 400)
        crowded = self.original + "\n\n" + ("Paragraphe.\n\n" * 80)
        response = self.client.post(self.url, {**self.payload, "action": "preview", "text": crowded})
        self.assertEqual(response.status_code, 400)

    @override_settings(OPENAI_API_KEY="configured-test-key")
    def test_gpt_reformulation_is_checked_before_returning(self):
        with patch("sigda.drafting.gpt_answer", return_value=self.original.replace("Le présent document", "Ce document")) as api:
            response = self.client.post(self.url, {**self.payload, "mode": "gpt"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Préserve exactement", api.call_args.kwargs["instructions"])
        with patch("sigda.drafting.gpt_answer", return_value=self.original.replace("1 jour", "3 jours")):
            response = self.client.post(self.url, {**self.payload, "mode": "gpt"})
        self.assertEqual(response.status_code, 400)

    def test_style_query_reaches_pdf_and_preview_links(self):
        response = self.client.get(reverse("workspace"), {"type": "ordre-mission", "wording": "formel"})
        self.assertContains(response, ".png?wording=formel")
        self.assertNotContains(response, "?download=1")
        self.assertEqual(self.client.get(reverse("specimen", args=["ordre-mission", "alpha"]), {"wording": "unknown"}).status_code, 404)
