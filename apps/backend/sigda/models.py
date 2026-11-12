from uuid import uuid4

from django.conf import settings
from django.db import models


class DocumentRequest(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Brouillon"
        SUBMITTED = "submitted", "Contrôle SECAD"
        AP = "ap", "Visa AP"
        DIRCAB = "dircab", "Validation DIRCAB"
        APPROVED = "approved", "Approuvée"
        REJECTED = "rejected", "Refusée"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    agent_key = models.SlugField(max_length=64)
    document_key = models.SlugField(max_length=64)
    payload = models.JSONField(default=dict, blank=True)
    revision = models.PositiveIntegerField(default=1)
    cycle = models.PositiveIntegerField(default=0)
    payload_hash = models.CharField(max_length=64, blank=True)
    issued_pdf = models.BinaryField(default=bytes, blank=True)
    issued_hash = models.CharField(max_length=64, blank=True)
    issued_at = models.DateTimeField(null=True, blank=True)
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
    actor_role = models.CharField(max_length=12, blank=True)
    event_type = models.CharField(max_length=24, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]


class AgentRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    registration = models.CharField(max_length=40)
    service = models.CharField(max_length=100)
    job = models.CharField(max_length=100)
    grade = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["owner", "registration"], name="agent_registration_per_owner")]


class ValidationTask(models.Model):
    class State(models.TextChoices):
        PENDING = "pending", "À traiter"
        APPROVED = "approved", "Validée"
        RETURNED = "returned", "Retournée en correction"
        COMPLETED = "completed", "Terminée"
        REJECTED = "rejected", "Refusée"

    request = models.ForeignKey(DocumentRequest, related_name="tasks", on_delete=models.PROTECT)
    stage = models.CharField(max_length=12)
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="validation_tasks", on_delete=models.PROTECT)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="assigned_validation_tasks", on_delete=models.PROTECT)
    cycle = models.PositiveIntegerField(default=0)
    revision = models.PositiveIntegerField(default=1)
    snapshot_hash = models.CharField(max_length=64)
    state = models.CharField(max_length=12, choices=State.choices, default=State.PENDING)
    note = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    due_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at", "pk"]
        constraints = [models.UniqueConstraint(fields=["request"], condition=models.Q(state="pending"), name="one_pending_validation_task")]


class DocumentAccess(models.Model):
    request = models.ForeignKey(DocumentRequest, related_name="accesses", on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=24)
    file_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)


class UsageEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    actor_role = models.CharField(max_length=12, blank=True)
    action = models.CharField(max_length=32)
    document = models.ForeignKey(DocumentRequest, null=True, blank=True, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class LoginAttemptBucket(models.Model):
    key = models.CharField(primary_key=True, max_length=64)
    attempts = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField()


class ServiceValidity(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    starts_on = models.DateField()
    expires_on = models.DateField()
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    updated_at = models.DateTimeField(auto_now=True)


class SupportTicket(models.Model):
    CATEGORIES = [('agent_add', 'Ajout d’un agent'), ('agent_update', 'Correction d’un dossier agent'),
                  ('app_update', 'Mise à jour de l’application'), ('renewal', 'Renouvellement annuel'), ('assistance', 'Assistance'), ('complaint', 'Réclamation')]
    STATES = [('open', 'À traiter'), ('processing', 'En cours'), ('resolved', 'Traitée')]
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    category = models.CharField(max_length=24, choices=CATEGORIES)
    details = models.CharField(max_length=2000)
    state = models.CharField(max_length=16, choices=STATES, default='open')
    response = models.CharField(max_length=1000, blank=True)
    handled_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='handled_support_tickets', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class MaintenanceEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=32)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
