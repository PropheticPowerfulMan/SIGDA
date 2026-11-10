from itertools import product

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .catalog import AGENTS, DOCUMENT_TYPES


class WorkspaceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="agent-test")

    def setUp(self):
        self.client.force_login(self.user)

    def test_selection_updates_the_preview_and_download(self):
        url = reverse("specimen", args=["notification", "beta"])
        preview = reverse("specimen_preview", args=["notification", "beta"])
        response = self.client.get("/", {"agent": "beta", "type": "notification"})
        self.assertContains(response, "Dominique Témoin")
        self.assertContains(response, "SIGDA et SSDC sont deux projets indépendants.")
        self.assertContains(response, f'src="{preview}"')
        self.assertContains(response, f'href="{url}?download=1"')

    def test_navigation_opens_distinct_pages(self):
        for route, view in (
            ("overview", "overview"), ("agent_directory", "directory"),
            ("workspace", "workspace"), ("request_queue", "requests"), ("activity", "activity"),
        ):
            with self.subTest(route=route):
                url = reverse(route)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["current_view"], view)
        directory = self.client.get(reverse("agent_directory"), {"q": "temoin"})
        self.assertContains(directory, "Dominique Témoin")
        self.assertNotContains(directory, "Camille Exemple")
        self.assertNotContains(directory, "data-print-specimen")
        self.assertContains(self.client.get(reverse("workspace")), "data-print-specimen")

    def test_unknown_agent_and_model_return_404(self):
        self.assertEqual(self.client.get("/", {"agent": "unknown"}).status_code, 404)
        self.assertEqual(self.client.get("/", {"type": "unknown"}).status_code, 404)
        self.assertEqual(self.client.get("/specimens/notification/unknown.pdf").status_code, 404)
        self.assertEqual(self.client.get("/specimens/unknown/alpha.pdf").status_code, 404)
        self.assertEqual(self.client.get("/specimens/notification/unknown.png").status_code, 404)

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

    def test_specimen_preview_is_png_and_not_cached(self):
        url = reverse("specimen_preview", args=["notification", "beta"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertTrue(response.content.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertIn("no-store", response["Cache-Control"])

    def test_demo_endpoints_reject_post(self):
        self.assertEqual(self.client.post("/").status_code, 405)
        self.assertEqual(self.client.post("/specimens/notification/beta.pdf").status_code, 405)


class AuthenticationTests(TestCase):
    credentials = {"username": "agent-test", "password": "Mots-de-passe-test-2026"}

    @classmethod
    def setUpTestData(cls):
        get_user_model().objects.create_user(**cls.credentials)

    def test_workspace_and_direct_document_access_require_login(self):
        urls = (
            reverse("workspace"),
            reverse("specimen", args=["notification", "beta"]),
            reverse("specimen_preview", args=["notification", "beta"]),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, f"{reverse('login')}?next={url}", fetch_redirect_response=False)
                self.assertIn("no-store", response["Cache-Control"])

    def test_login_returns_to_requested_document_and_logout_revokes_access(self):
        url = reverse("specimen", args=["notification", "beta"])
        login_url = reverse("login")
        logout_url = reverse("logout")
        client = Client(enforce_csrf_checks=True)

        response = client.get(login_url, {"next": url})
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertIn("no-store", response["Cache-Control"])
        csrf = client.cookies["csrftoken"].value
        response = client.post(login_url, {**self.credentials, "next": url, "csrfmiddlewaretoken": csrf})
        self.assertRedirects(response, url, fetch_redirect_response=False)
        self.assertEqual(client.get(url).status_code, 200)

        self.assertEqual(client.get(logout_url).status_code, 405)
        self.assertEqual(client.post(logout_url).status_code, 403)
        self.assertEqual(client.get(url).status_code, 200)

        csrf = client.cookies["csrftoken"].value
        self.assertRedirects(client.post(logout_url, {"csrfmiddlewaretoken": csrf}), login_url)
        self.assertRedirects(client.get(url), f"{login_url}?next={url}", fetch_redirect_response=False)

    def test_invalid_password_does_not_create_session(self):
        response = self.client.post(reverse("login"), {
            "username": self.credentials["username"],
            "password": "Identifiant-de-test-incorrect",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertEqual(self.client.get(reverse("workspace")).status_code, 302)
