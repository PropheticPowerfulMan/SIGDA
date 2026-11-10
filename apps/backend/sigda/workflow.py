from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from .catalog import AGENTS, DOCUMENT_TYPES
from .models import DocumentRequest, RequestEvent


REVIEW_PERMISSION = "sigda.review_documentrequest"
Status = DocumentRequest.Status


class DraftForm(forms.Form):
    agent = forms.ChoiceField(label="Agent fictif")
    document = forms.ChoiceField(label="Modèle documentaire")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["agent"].choices = [(key, agent.name) for key, agent in AGENTS.items()]
        self.fields["document"].choices = [(key, kind.title) for key, kind in DOCUMENT_TYPES.items()]


class DecisionForm(forms.Form):
    note = forms.CharField(label="Motif ou commentaire", required=False, max_length=500,
                           widget=forms.Textarea(attrs={"rows": 3}))


def visible_requests(user):
    records = DocumentRequest.objects.select_related("owner")
    own = records.filter(owner=user)
    if user.has_perm(REVIEW_PERMISSION):
        return own | records.exclude(status=Status.DRAFT)
    return own


def catalog_labels(record):
    agent = AGENTS.get(record.agent_key)
    document = DOCUMENT_TYPES.get(record.document_key)
    return (
        agent.name if agent else record.agent_key,
        document.title if document else record.document_key,
    )


@never_cache
@login_required
@require_http_methods(["GET", "HEAD", "POST"])
def queue(request):
    if request.method == "POST":
        form = DraftForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                record = DocumentRequest.objects.create(
                    owner=request.user,
                    agent_key=form.cleaned_data["agent"],
                    document_key=form.cleaned_data["document"],
                )
                RequestEvent.objects.create(request=record, actor=request.user, status=Status.DRAFT)
            return redirect("request_detail", pk=record.pk)
    else:
        form = DraftForm(initial={
            "agent": request.GET.get("agent"),
            "document": request.GET.get("type"),
        })

    page = Paginator(visible_requests(request.user), 20).get_page(request.GET.get("page"))
    return render(request, "workflow/queue.html", {
        "current_view": "requests",
        "current_label": "Demandes",
        "current_view": "requests",
        "current_label": "Demandes",
        "draft_form": form,
        "page": page,
        "rows": [(record, *catalog_labels(record)) for record in page],
        "reviewer": request.user.has_perm(REVIEW_PERMISSION),
    })


def render_detail(request, record, *, form=None, conflict=False, status=200):
    owner = record.owner_id == request.user.pk
    agent_label, document_label = catalog_labels(record)
    return render(request, "workflow/detail.html", {
        "workflow_page": True,
        "workflow_page": True,
        "record": record,
        "agent_label": agent_label,
        "document_label": document_label,
        "events": record.events.select_related("actor"),
        "can_submit": owner and record.status == Status.DRAFT,
        "can_review": (
            not owner and record.status == Status.SUBMITTED
            and request.user.has_perm(REVIEW_PERMISSION)
        ),
        "decision_form": DecisionForm() if form is None else form,
        "conflict": conflict,
        "catalog_available": record.agent_key in AGENTS and record.document_key in DOCUMENT_TYPES,
    }, status=status)


@never_cache
@login_required
@require_safe
def detail(request, pk):
    record = get_object_or_404(visible_requests(request.user), pk=pk)
    return render_detail(request, record)


@never_cache
@login_required
@require_POST
def transition(request, pk):
    record = get_object_or_404(visible_requests(request.user), pk=pk)
    action = request.POST.get("action")
    note = ""
    if action == "submit":
        if record.owner_id != request.user.pk:
            raise PermissionDenied
        before, after = Status.DRAFT, Status.SUBMITTED
    elif action in {"approve", "reject"}:
        if record.owner_id == request.user.pk or not request.user.has_perm(REVIEW_PERMISSION):
            raise PermissionDenied
        before = Status.SUBMITTED
        after = Status.APPROVED if action == "approve" else Status.REJECTED
        form = DecisionForm(request.POST)
        if form.is_valid():
            note = form.cleaned_data["note"]
            if action == "reject" and not note:
                form.add_error("note", "Indiquez le motif du refus.")
        if form.errors:
            return render_detail(request, record, form=form, status=400)
    else:
        raise Http404

    with transaction.atomic():
        updated = DocumentRequest.objects.filter(pk=pk, status=before).update(
            status=after, updated_at=timezone.now(),
        )
        if updated:
            RequestEvent.objects.create(request=record, actor=request.user, status=after, note=note)
    if not updated:
        record.refresh_from_db()
        return render_detail(request, record, conflict=True, status=409)
    return redirect("request_detail", pk=pk)


urlpatterns = [
    path("", queue, name="request_queue"),
    path("<uuid:pk>/", detail, name="request_detail"),
    path("<uuid:pk>/decision/", transition, name="request_transition"),
]
