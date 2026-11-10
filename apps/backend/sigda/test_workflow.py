from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import DocumentRequest, RequestEvent


class WorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.author = users.objects.create_user(username="demandeur-test")
        cls.reviewer = users.objects.create_user(username="valideur-test")
        cls.other = users.objects.create_user(username="autre-test")
        cls.reviewer.user_permissions.add(Permission.objects.get(
            content_type__app_label="sigda", codename="review_documentrequest",
        ))

    def create_draft(self, author):
        self.client.force_login(author)
        response = self.client.post(reverse("request_queue"), {
            "agent": "beta", "document": "notification",
        })
        record = DocumentRequest.objects.get()
        self.assertRedirects(response, reverse("request_detail", args=[record.pk]))
        return record

    def test_approval_records_actors_and_rejects_a_stale_decision(self):
        record = self.create_draft(self.author)
        status = DocumentRequest.Status
        decision = reverse("request_transition", args=[record.pk])
        detail = reverse("request_detail", args=[record.pk])

        self.assertRedirects(self.client.post(decision, {"action": "submit"}), detail)
        self.client.force_login(self.reviewer)
        self.assertRedirects(self.client.post(decision, {
            "action": "approve", "note": "Dossier vérifié.",
        }), detail)
        self.assertEqual(self.client.post(decision, {
            "action": "reject", "note": "Décision obsolète.",
        }).status_code, 409)
        record.refresh_from_db()
        self.assertEqual(record.status, status.APPROVED)
        self.assertEqual(list(record.events.values_list("status", "actor_id", "note")), [
            (status.DRAFT, self.author.pk, ""),
            (status.SUBMITTED, self.author.pk, ""),
            (status.APPROVED, self.reviewer.pk, "Dossier vérifié."),
        ])

    def test_visibility_and_separation_of_roles(self):
        record = self.create_draft(self.reviewer)
        decision = reverse("request_transition", args=[record.pk])
        detail = reverse("request_detail", args=[record.pk])

        self.client.force_login(self.other)
        self.assertEqual(self.client.get(detail).status_code, 404)
        self.assertEqual(self.client.post(decision, {"action": "approve"}).status_code, 404)
        self.client.force_login(self.reviewer)
        self.assertRedirects(self.client.post(decision, {"action": "submit"}), detail)
        self.assertEqual(self.client.post(decision, {"action": "approve"}).status_code, 403)

    def test_rejection_requires_a_reason_and_mutation_requires_csrf(self):
        record = self.create_draft(self.author)
        decision = reverse("request_transition", args=[record.pk])
        detail = reverse("request_detail", args=[record.pk])
        self.client.post(decision, {"action": "submit"})
        self.client.force_login(self.reviewer)
        self.assertEqual(self.client.get(decision).status_code, 405)
        self.assertContains(self.client.post(decision, {"action": "reject", "note": " "}),
                            "Indiquez le motif du refus.", status_code=400)

        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.reviewer)
        self.assertEqual(csrf_client.post(decision, {"action": "approve"}).status_code, 403)
        self.assertRedirects(self.client.post(decision, {
            "action": "reject", "note": "Pièce justificative manquante.",
        }), detail)
        record.refresh_from_db()
        self.assertEqual(record.status, DocumentRequest.Status.REJECTED)
        self.assertEqual(record.events.last().note, "Pièce justificative manquante.")


    def test_activity_statistics_respect_scope_and_use_submission_before_period(self):
        status = DocumentRequest.Status
        finished = timezone.now() - timedelta(days=1)
        for owner, minutes, decision in (
            (self.author, 30, status.APPROVED),
            (self.other, 60, status.REJECTED),
            (self.other, 120, status.APPROVED),
        ):
            record = DocumentRequest.objects.create(
                owner=owner, agent_key="alpha", document_key="notification", status=decision,
            )
            submitted = RequestEvent.objects.create(request=record, actor=owner, status=status.SUBMITTED)
            decided = RequestEvent.objects.create(request=record, actor=self.reviewer, status=decision)
            RequestEvent.objects.filter(pk=submitted.pk).update(created_at=finished - timedelta(minutes=minutes))
            RequestEvent.objects.filter(pk=decided.pk).update(created_at=finished)

        older = DocumentRequest.objects.create(
            owner=self.other, agent_key="beta", document_key="notification", status=status.APPROVED,
        )
        submitted = RequestEvent.objects.create(request=older, actor=self.other, status=status.SUBMITTED)
        decided = RequestEvent.objects.create(request=older, actor=self.reviewer, status=status.APPROVED)
        RequestEvent.objects.filter(pk=submitted.pk).update(created_at=finished - timedelta(days=10))
        RequestEvent.objects.filter(pk=decided.pk).update(created_at=finished)

        url = reverse("activity")
        self.client.force_login(self.author)
        response = self.client.get(url, {"period": 7})
        self.assertEqual(response.context["decided"], 1)
        self.assertEqual(response.context["median_delay"], "30 min")
        self.assertNotContains(response, self.other.username)

        self.client.force_login(self.reviewer)
        response = self.client.get(url, {"period": 7})
        self.assertEqual(response.context["submitted"], 3)
        self.assertEqual(response.context["decided"], 4)
        self.assertEqual(response.context["approval_rate"], 75)
        self.assertEqual(response.context["sample"], 4)
        self.assertEqual(response.context["median_delay"], "1 h 30 min")
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(sum(row["decided"] for row in response.context["buckets"]), 4)
