import json
from io import BytesIO
from unittest.mock import patch
from urllib.error import URLError

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse


class AssistantTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("assistant-test")
        self.client.force_login(self.user)
        cache.clear()

    @override_settings(OPENAI_API_KEY="")
    def test_local_guidance_has_no_external_call_and_suggests_real_model(self):
        with patch("sigda.assistant.urlopen") as api:
            response = self.client.post(reverse("assistant_ask"), {
                "question": "Quel document pour certifier un emploi ?", "mode": "local",
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mode"], "Guidage local")
        self.assertEqual(response.json()["links"][0]["model"], "attestation-service")
        self.assertIn("no-store", response["Cache-Control"])
        api.assert_not_called()
        self.assertEqual(self.client.post(reverse("assistant_ask"), {
            "question": "Bonjour", "mode": "gpt",
        }).status_code, 503)

    def test_authentication_csrf_and_validation(self):
        self.assertEqual(Client().get(reverse("assistant")).status_code, 302)
        self.assertEqual(Client().post(reverse("assistant_ask")).status_code, 302)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(reverse("assistant_ask"), {
            "question": "Bonjour", "mode": "local",
        }).status_code, 403)
        self.assertEqual(self.client.post(reverse("assistant_ask"), {
            "question": "x" * 2001, "mode": "local",
        }).status_code, 400)

    @override_settings(OPENAI_API_KEY="test-key-secret", SIGDA_OPENAI_MODEL="configured-model")
    def test_provider_payload_rate_limit_and_sanitized_failure(self):
        output = {"output": [{"type": "message", "content": [{"type": "output_text", "text": "Réponse de test."}]}]}
        url = reverse("assistant_ask")
        with patch("sigda.assistant.urlopen", return_value=BytesIO(json.dumps(output).encode())) as api:
            response = self.client.post(url, {"question": "Aidez-moi à rédiger.", "mode": "gpt"})
            request = api.call_args.args[0]
            payload = json.loads(request.data)
        self.assertEqual(response.json()["text"], "Réponse de test.")
        self.assertEqual(payload["model"], "configured-model")
        self.assertIs(payload["store"], False)
        self.assertEqual(payload["max_output_tokens"], 1200)
        self.assertNotIn("test-key-secret", response.content.decode())
        self.assertNotContains(self.client.get(reverse("assistant")), "test-key-secret")
        with patch("sigda.assistant.urlopen", side_effect=URLError("test-key-secret")):
            response = self.client.post(url, {"question": "Bonjour", "mode": "gpt"})
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("test-key-secret", response.content.decode())
        cache.set(f"sigda-gpt:{self.user.pk}:2", 10, 70)
        with patch("sigda.assistant.time.time", return_value=120), patch("sigda.assistant.urlopen") as api:
            self.assertEqual(self.client.post(url, {"question": "Bonjour", "mode": "gpt"}).status_code, 429)
            api.assert_not_called()
