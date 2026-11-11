from datetime import date, time
from uuid import UUID, uuid4

from django import forms
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from .catalog import DOCUMENT_TYPES, format_date
from .composition_schema import COMMON_FIELDS, IDENTITY_FIELDS, MODELS, OPENINGS, CLOSINGS, compose_agent, compose_text
from .models import AgentRecord, DocumentRequest, RequestEvent, ValidationTask, DocumentAccess
from .roles import require_ops
from .usage import log_usage
from .pdf import render_pdf
from .preview import render_preview
from .service_policy import creation_allowed
from .wording import STYLES


def agent_data(record):
    return {"id": str(record.pk), **{key: getattr(record, key) for key in ("name", "registration", "service", "job", "grade")}}


class AgentForm(forms.ModelForm):
    class Meta:
        model = AgentRecord
        fields = ("name", "registration", "service", "job", "grade")
        labels = {item["key"]: item["label"] for item in IDENTITY_FIELDS}

    def clean_registration(self):
        return self.cleaned_data["registration"].strip().upper()

    def clean(self):
        data = super().clean()
        for key, value in data.items():
            if isinstance(value, str) and any(ord(char) < 32 for char in value):
                self.add_error(key, "Saisissez cette donnée sur une seule ligne.")
        return data


class CompositionForm(forms.Form):
    kind = forms.ChoiceField(choices=[(key, model.title) for key, model in DOCUMENT_TYPES.items()])
    wording = forms.ChoiceField(choices=list(STYLES.items()))
    agent_id = forms.UUIDField(required=False)

    def __init__(self, data, *, user):
        super().__init__(data)
        self.user = user
        schema = MODELS.get(data.get("kind"), MODELS["attestation-service"])
        for spec in COMMON_FIELDS + schema["fields"]:
            options = {"required": spec["key"] != "signatory", "label": spec["label"]}
            cls = {"date": forms.DateField, "time": forms.TimeField, "number": forms.IntegerField}.get(spec["type"], forms.CharField)
            if cls is forms.CharField:
                options["max_length"] = spec["max"]
            if cls is forms.IntegerField:
                options.update(min_value=1, max_value=999)
            self.fields[spec["key"]] = cls(**options)

    def clean(self):
        data = super().clean()
        for key, value in list(data.items()):
            if isinstance(value, str):
                data[key] = value.replace("\r\n", "\n").replace("\r", "\n")
                if key not in {"instructions", "objective"} and any(ord(char) < 32 for char in data[key]):
                    self.add_error(key, "Saisissez cette donnée sur une seule ligne.")
        schema = MODELS.get(data.get("kind"))
        if not schema:
            return data
        if schema["subject"] == "agent":
            record = AgentRecord.objects.filter(pk=data.get("agent_id"), owner=self.user).first()
            if record is None:
                self.add_error("agent_id", "Choisissez un dossier enregistré. Pour un ajout ou une correction, contactez la maintenance.")
            else:
                data.update({spec["key"]: getattr(record, spec["key"]) for spec in IDENTITY_FIELDS})
        for start, end in (("mission_start", "mission_end"), ("from_time", "to_time")):
            if data.get(start) and data.get(end) and data[end] < data[start]:
                self.add_error(end, "La fin doit être postérieure ou égale au début.")
        return data


@never_cache
@login_required
@require_safe
@require_ops
def page(request):
    editing = None
    if request.GET.get("draft"):
        try:
            identifier = UUID(request.GET['draft'])
        except (ValueError, TypeError):
            raise Http404
        editing = get_object_or_404(DocumentRequest, pk=identifier, owner=request.user, status=DocumentRequest.Status.DRAFT)
    return render(request, "compose.html", {"current_view": "compose", "current_label": "Créer un document",
        "composition_schema": {"models": MODELS, "identity": IDENTITY_FIELDS, "common": COMMON_FIELDS,
                               "openings": OPENINGS, "closings": CLOSINGS},
        "composition_models": {key: {"title": model.title, "category": model.category} for key, model in DOCUMENT_TYPES.items()},
        "composition_styles": STYLES,
        "composition_agents": [agent_data(record) for record in AgentRecord.objects.filter(owner=request.user)],
        "today": timezone.localdate().isoformat(), "initial_model": request.GET.get("type", "attestation-service"),
        "initial_agent": request.GET.get("agent", ""), "editing_request": editing,
        "initial_data": editing.payload.get("data", {}) if editing else {}})


@never_cache
@login_required
@require_POST
def save_agent(request):
    return JsonResponse({'error': 'La base agents est administrée par l’équipe de maintenance. Ouvrez Maintenance et assistance pour demander un ajout ou une correction.'}, status=403)


def render_composed(snapshot, preview_only=False):
    data = snapshot["data"]
    return render_pdf(data["kind"], DOCUMENT_TYPES[data["kind"]], compose_agent(data), snapshot["reference"],
        format_date(date.fromisoformat(data["issue_date"])), body_text=snapshot["text"], context=data, preview_only=preview_only)


@never_cache
@login_required
@require_POST
@require_ops
@creation_allowed
def preview(request):
    from base64 import b64encode
    form = CompositionForm(request.POST, user=request.user)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)
    data = {key: value.isoformat() if isinstance(value, (date, time)) else str(value) if value is not None else ""
            for key, value in form.cleaned_data.items()}
    existing = None
    if request.POST.get("draft_id"):
        try:
            existing = get_object_or_404(DocumentRequest, pk=UUID(request.POST["draft_id"]), owner=request.user)
        except (ValueError, TypeError):
            return JsonResponse({"error": "Identifiant de brouillon invalide."}, status=400)
        if existing.status != DocumentRequest.Status.DRAFT:
            return JsonResponse({"error": "Le document est déjà dans le circuit de validation. Actualisez son suivi."}, status=409)
    identifier = existing.pk if existing else uuid4()
    snapshot = {"version": 1, "id": str(identifier), "owner": request.user.pk, "data": data,
                "reference": f"SPEC-{DOCUMENT_TYPES[data['kind']].prefix}-{identifier.hex[:12].upper()}-{data['issue_date'][:4]}",
                "text": compose_text(data)}
    snapshot["base_revision"] = existing.revision if existing else 0
    if existing:
        snapshot["reference"] = existing.payload["reference"]
    try:
        pdf = render_composed(snapshot, preview_only=True)
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    log_usage(request.user, "preview")
    return JsonResponse({"preview": "data:image/png;base64," + b64encode(render_preview(pdf)).decode(),
        "text": snapshot["text"], "reference": snapshot["reference"],
        "data": data,
        "ticket": signing.dumps(snapshot, salt="sigda-composition", compress=True)})


@never_cache
@login_required
@require_POST
@require_ops
@creation_allowed
def save(request):
    try:
        snapshot = signing.loads(request.POST.get("ticket", ""), salt="sigda-composition", max_age=3600)
        if snapshot["owner"] != request.user.pk:
            raise signing.BadSignature
    except (signing.BadSignature, KeyError, TypeError, ValueError):
        return JsonResponse({"error": "L’aperçu a expiré. Générez-le de nouveau avant d’enregistrer."}, status=400)
    data = snapshot["data"]
    from .workflow import payload_digest, new_task
    with transaction.atomic():
        record, created = DocumentRequest.objects.get_or_create(pk=snapshot["id"], owner=request.user,
            defaults={"document_key": data["kind"], "agent_key": "saisie", "payload": snapshot, "payload_hash": payload_digest(snapshot)})
        if created:
            RequestEvent.objects.create(request=record, actor=request.user, status=DocumentRequest.Status.DRAFT,
                                        actor_role="OPS", event_type="created", note="Document composé depuis les données du dossier et les champs du modèle.")
            new_task(record, "OPS", request.user, request.user)
            log_usage(request.user, "draft_create", record)
        elif record.payload != snapshot:
            if record.status != DocumentRequest.Status.DRAFT or record.revision != snapshot.get("base_revision"):
                return JsonResponse({"error": "Ce brouillon a changé. Actualisez-le avant de l’enregistrer."}, status=409)
            digest = payload_digest(snapshot)
            if not DocumentRequest.objects.filter(pk=record.pk, status=DocumentRequest.Status.DRAFT, revision=record.revision).update(
                payload=snapshot, payload_hash=digest, document_key=data["kind"], revision=record.revision + 1, updated_at=timezone.now()):
                return JsonResponse({"error": "Une autre modification est intervenue. Actualisez le dossier."}, status=409)
            ValidationTask.objects.filter(request=record, stage="OPS", state=ValidationTask.State.PENDING).update(snapshot_hash=digest, revision=record.revision + 1)
            RequestEvent.objects.create(request=record, actor=request.user, actor_role="OPS", event_type="updated", status=DocumentRequest.Status.DRAFT, note="Nouvelle révision enregistrée par OPS.")
            log_usage(request.user, "draft_update", record)
    request.session["sigda-feedback"] = "Le brouillon est enregistré. Vous pouvez poursuivre le circuit de validation."
    return JsonResponse({"url": reverse("request_detail", args=[record.pk])})


@never_cache
@login_required
@require_safe
def saved_document(request, pk, extension):
    if extension not in {"pdf", "png"}:
        raise Http404
    from .workflow import visible_requests
    record = get_object_or_404(visible_requests(request.user).exclude(payload={}), pk=pk)
    if extension == "pdf" and (record.status != DocumentRequest.Status.APPROVED or not record.issued_pdf):
        return HttpResponseForbidden("Le PDF imprimable est disponible uniquement après validation finale DIRCAB.")
    pdf = bytes(record.issued_pdf) if record.status == DocumentRequest.Status.APPROVED and record.issued_pdf else render_composed(record.payload, preview_only=True)
    if extension == "png":
        return HttpResponse(render_preview(pdf), content_type="image/png")
    from hashlib import sha256
    if sha256(pdf).hexdigest() != record.issued_hash:
        return HttpResponse("L’empreinte du fichier archivé ne correspond pas. La sortie est bloquée.", status=409)
    DocumentAccess.objects.create(request=record, actor=request.user, action="final_pdf_open", file_hash=record.issued_hash)
    log_usage(request.user, "final_pdf_open", record)
    return HttpResponse(pdf, content_type="application/pdf", headers={
        "Content-Disposition": f'inline; filename="{record.payload["reference"]}.pdf"'})
