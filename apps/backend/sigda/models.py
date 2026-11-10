from uuid import uuid4

from django.conf import settings
from django.db import models


class DocumentRequest(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Brouillon"
        SUBMITTED = "submitted", "En attente de décision"
        APPROVED = "approved", "Approuvée"
        REJECTED = "rejected", "Refusée"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    agent_key = models.SlugField(max_length=64)
    document_key = models.SlugField(max_length=64)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "id"]
        permissions = [("review_documentrequest", "Peut décider d’une demande documentaire")]


class RequestEvent(models.Model):
    id = models.BigAutoField(primary_key=True)
    request = models.ForeignKey(DocumentRequest, related_name="events", on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    status = models.CharField(max_length=16, choices=DocumentRequest.Status.choices)
    note = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
