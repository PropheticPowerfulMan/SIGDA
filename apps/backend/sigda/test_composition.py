from base64 import b64decode
from contextlib import closing

import pypdfium2 as pdfium
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import signing
from .composition import render_composed
from django.test import Client, TestCase
from django.urls import reverse

from .models import AgentRecord, DocumentRequest
from .composition_schema import MODELS


def pdf_text(content):
    with closing(pdfium.PdfDocument(content)) as doc:
        assert len(doc) == 1
        with closing(doc[0]) as page, closing(page.get_textpage()) as text:
            return text.get_text_range()


class CompositionTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user("composer-owner")
        self.other = get_user_model().objects.create_user("composer-other")
        for user in (self.owner, self.other):
            user.groups.add(Group.objects.get_or_create(name="SIGDA_OPS")[0])
        self.agent = AgentRecord.objects.create(owner=self.owner, name="Aline Démonstration", registration="TEST-083",
                    service="Service des archives", job="Archiviste", grade="Agent de deuxième classe")
        self.client.force_login(self.owner)
        self.base = {"kind": "attestation-service", "wording": "classique", "agent_id": str(self.agent.pk),
            "issuer_service": "Direction administrative", "place": "Kinshasa", "issue_date": "2026-11-11",
            "signatory": "Responsable Exemple", "signatory_role": "Directeur du service",
            "since": "2024-01-10", "purpose": "compléter le dossier administratif"}

    def test_entry_always_opens_login_and_composer_requires_authentication(self):
        self.assertRedirects(self.client.get("/"), reverse("login"), fetch_redirect_response=False)
        self.assertEqual(Client().get(reverse("compose")).status_code, 302)
        csrf = Client(enforce_csrf_checks=True); csrf.force_login(self.owner)
        self.assertEqual(csrf.post(reverse("compose_preview"), self.base).status_code, 403)

    def test_authoritative_agent_data_is_read_from_owner_database(self):
        response = self.client.post(reverse("compose_preview"), {**self.base, "name": "Faux nom injecté", "grade": "Faux grade"})
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn(self.agent.name, result["text"])
        self.assertIn(self.agent.grade, result["text"])
        self.assertNotIn("Faux nom", result["text"])
        self.assertIn(self.agent.name, pdf_text(render_composed(signing.loads(result["ticket"], salt="sigda-composition"))))
        self.assertIn("no-store", response["Cache-Control"])
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(reverse("compose_preview"), self.base).status_code, 400)
        self.assertEqual(self.client.post(reverse("agent_save"), {"id": self.agent.pk, "name": "Modification"}).status_code, 404)

    def test_brouillon_is_idempotent_and_preserves_snapshot_after_profile_change(self):
        result = self.client.post(reverse("compose_preview"), self.base).json()
        for _ in range(2):
            self.assertEqual(self.client.post(reverse("compose_save"), {"ticket": result["ticket"]}).status_code, 200)
        self.assertEqual(DocumentRequest.objects.count(), 1)
        record = DocumentRequest.objects.get()
        self.assertEqual(record.events.count(), 1)
        self.assertEqual(record.payload["reference"], result["reference"])
        self.agent.name = "Nouveau nom du dossier"; self.agent.save()
        response = self.client.get(reverse("saved_document", args=[record.pk, "pdf"]))
        self.assertEqual(response.status_code, 403)
        self.assertIn("Aline Démonstration", pdf_text(render_composed(record.payload)))
        self.assertNotIn("Nouveau nom", pdf_text(render_composed(record.payload)))
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("saved_document", args=[record.pk, "pdf"])).status_code, 404)
        self.assertEqual(self.client.post(reverse("compose_save"), {"ticket": result["ticket"]}).status_code, 400)

    def test_agent_save_normalizes_and_rejects_duplicate_registration(self):
        data = {key: getattr(self.agent, key) for key in ("name", "registration", "service", "job", "grade")}
        self.assertEqual(self.client.post(reverse("agent_save"), data).status_code, 400)
        response = self.client.post(reverse("agent_save"), {**data, "registration": "test-099"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["agent"]["registration"], "TEST-099")
        self.assertEqual(self.client.post(reverse("agent_save"), {**data, "id": "invalid"}).status_code, 400)

    def test_each_model_generates_a_filled_a4_and_invalid_ranges_are_rejected(self):
        sample = {"since": "2024-01-10", "purpose": "vérification", "schedule": "de 20 h à 6 h", "presence_date": "2026-11-10", "presence_place": "Bureau des archives", "effective_date": "2026-01-01", "decision_ref": "DEMO/084", "decision_date": "2026-11-01", "reason": "mise à jour du dossier", "meeting_date": "2026-11-20", "meeting_time": "10:30", "meeting_place": "Bureau administratif", "recipient": "Direction des ressources humaines", "item": "Dossier de vérification", "quantity": "3", "subject": "Mise à jour des dossiers", "instructions": "Transmettre les fiches actualisées au secrétariat.", "exit_date": "2026-11-20", "from_time": "10:00", "to_time": "12:00", "destination": "Kinshasa / Gombe", "mission_start": "2026-11-20", "mission_end": "2026-11-22", "objective": "Vérifier et inventorier les dossiers d’archives."}
        for key, model in MODELS.items():
            with self.subTest(model=key):
                response = self.client.post(reverse("compose_preview"), {**self.base, **sample, "kind": key})
                self.assertEqual(response.status_code, 200)
                text = pdf_text(render_composed(signing.loads(response.json()["ticket"], salt="sigda-composition")))
                self.assertIn(self.agent.name if model["subject"] == "agent" else sample.get("item") if model["subject"] == "piece" else sample["subject"], text)
        self.assertEqual(self.client.post(reverse("compose_preview"), {**self.base, **sample, "kind": "ordre-mission", "mission_end": "2026-11-19"}).status_code, 400)

    def test_correction_creates_new_revision_and_submitted_document_is_locked(self):
        first = self.client.post(reverse('compose_preview'), self.base).json()
        self.client.post(reverse('compose_save'), {'ticket': first['ticket']})
        record = DocumentRequest.objects.get()
        second = self.client.post(reverse('compose_preview'), {**self.base, 'draft_id': record.pk, 'purpose': 'archiver la correction'}).json()
        self.assertEqual(self.client.post(reverse('compose_save'), {'ticket': second['ticket']}).status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.revision, 2)
        self.assertIn('archiver la correction', record.payload['text'])
        self.assertEqual(record.tasks.get(state='pending').revision, 2)
        self.assertEqual(self.client.post(reverse('compose_save'), {'ticket': first['ticket']}).status_code, 409)
        self.assertEqual(self.client.post(reverse('compose_save'), {'ticket': second['ticket']}).status_code, 200)
        record.status = 'submitted'; record.save(update_fields=['status'])
        self.assertEqual(self.client.post(reverse('compose_preview'), {**self.base, 'draft_id': record.pk}).status_code, 409)
        self.assertEqual(self.client.get(reverse('compose') + '?draft=invalid').status_code, 404)
