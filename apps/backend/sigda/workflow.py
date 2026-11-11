from hashlib import sha256
import json

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_safe

from .catalog import AGENTS, DOCUMENT_TYPES
from .models import DocumentRequest, RequestEvent, ValidationTask
from .roles import ROLES, role_for
from .service_policy import policy

REVIEW_PERMISSION = 'sigda.review_documentrequest'
Status = DocumentRequest.Status
STAGES = {Status.DRAFT: 'OPS', Status.SUBMITTED: 'SECAD', Status.AP: 'AP', Status.DIRCAB: 'DIRCAB'}
NEXT = {Status.DRAFT: ('SECAD', Status.SUBMITTED), Status.SUBMITTED: ('AP', Status.AP), Status.AP: ('DIRCAB', Status.DIRCAB)}


def payload_digest(payload):
    return sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def visible_requests(user):
    records = DocumentRequest.objects.select_related('owner')
    if user.is_superuser or role_for(user) == 'DIRCAB':
        return records
    return records.filter(Q(owner=user) | Q(tasks__assignee=user) | Q(tasks__assigned_by=user)).distinct()


def catalog_labels(record):
    agent = AGENTS.get(record.agent_key)
    document = DOCUMENT_TYPES.get(record.document_key)
    data = record.payload.get('data', {})
    return (data.get('name') or data.get('item') or data.get('subject') or (agent.name if agent else record.agent_key), document.title if document else record.document_key)


def eligible_users(role, record, actor):
    previous = record.tasks.filter(cycle=record.cycle, state=ValidationTask.State.APPROVED).values_list('assignee_id', flat=True)
    users = get_user_model().objects.filter(is_active=True, groups__name='SIGDA_' + role).exclude(pk=record.owner_id).exclude(pk=actor.pk).exclude(pk__in=previous).distinct()
    return [user for user in users if role_for(user) == role]


class DecisionForm(forms.Form):
    revision = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    cycle = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    assignee = forms.ModelChoiceField(label='Utilisateur chargé de la prochaine étape', queryset=get_user_model().objects.none(), required=False)
    due_at = forms.DateTimeField(label='Échéance de la prochaine tâche (facultative)', required=False, widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    note = forms.CharField(label='Commentaire ou motif du retour', max_length=350, required=False, widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, record, actor, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial.update(revision=record.revision, cycle=record.cycle)
        target = NEXT.get(record.status, (None, None))[0]
        self.target_role = target
        if target:
            ids = [user.pk for user in eligible_users(target, record, actor)]
            self.fields['assignee'].queryset = get_user_model().objects.filter(pk__in=ids)
            self.fields['assignee'].label = f'Confier la tâche à un utilisateur {target}'
            if len(ids) == 1:
                self.initial['assignee'] = ids[0]
        else:
            self.fields.pop('assignee')
            self.fields.pop('due_at')


def task_for(record):
    return record.tasks.filter(state=ValidationTask.State.PENDING).select_related('assignee', 'assigned_by').first()


def new_task(record, stage, assignee, actor, due_at=None):
    return ValidationTask.objects.create(request=record, stage=stage, assignee=assignee, assigned_by=actor, cycle=record.cycle, revision=record.revision, snapshot_hash=record.payload_hash, due_at=due_at)


@never_cache
@login_required
@require_safe
def queue(request):
    records = visible_requests(request.user)
    page = Paginator(records, 20).get_page(request.GET.get('page'))
    return render(request, 'workflow/queue.html', {'current_view': 'requests', 'current_label': 'Mes tâches et documents', 'page': page,
        'rows': [(record, *catalog_labels(record), task_for(record)) for record in page],
        'assigned_tasks': ValidationTask.objects.filter(assignee=request.user, state=ValidationTask.State.PENDING).select_related('request'),
        'now': timezone.now()})


def render_detail(request, record, form=None, conflict=False, status=200):
    task = task_for(record)
    role = role_for(request.user)
    assigned = task and task.assignee_id == request.user.pk and task.stage == role
    return render(request, 'workflow/detail.html', {'current_view': 'requests', 'current_label': 'Mes tâches et documents', 'record': record,
        'agent_label': catalog_labels(record)[0], 'document_label': catalog_labels(record)[1], 'events': record.events.select_related('actor'),
        'tasks': record.tasks.select_related('assignee', 'assigned_by'), 'active_task': task,
        'can_submit': bool(assigned and role == 'OPS' and record.owner_id == request.user.pk and record.status == Status.DRAFT and record.payload),
        'can_review': bool(assigned and role in {'SECAD', 'AP', 'DIRCAB'} and record.owner_id != request.user.pk and record.status in STAGES),
        'can_edit': record.owner_id == request.user.pk and role == 'OPS' and record.status == Status.DRAFT,
        'can_reject': bool(assigned and role == 'DIRCAB'), 'can_print': bool(record.status == Status.APPROVED and record.issued_pdf),
        'decision_form': form if form is not None else DecisionForm(record=record, actor=request.user), 'conflict': conflict,
        'accesses': record.accesses.select_related('actor').order_by('-created_at')[:20]}, status=status)


@never_cache
@login_required
@require_safe
def detail(request, pk):
    return render_detail(request, get_object_or_404(visible_requests(request.user), pk=pk))


class Conflict(Exception):
    pass


@never_cache
@login_required
@require_POST
def transition(request, pk):
    record = get_object_or_404(visible_requests(request.user), pk=pk)
    form = DecisionForm(request.POST, record=record, actor=request.user)
    action = request.POST.get('action')
    role = role_for(request.user)
    task = task_for(record)
    if not task or task.assignee_id != request.user.pk or task.stage != role or role != STAGES.get(record.status):
        raise PermissionDenied('Cette tâche ne vous est pas attribuée.')
    if role != 'OPS' and record.owner_id == request.user.pk:
        raise PermissionDenied('Une personne ne peut pas valider son propre document.')
    if action not in ({'submit'} if role == 'OPS' else {'approve', 'return', 'reject'} if role == 'DIRCAB' else {'approve', 'return'}):
        raise Http404
    if not form.is_valid():
        return render_detail(request, record, form=form, status=400)
    data = form.cleaned_data
    if data['revision'] != record.revision or data['cycle'] != record.cycle:
        return render_detail(request, record, conflict=True, status=409)
    if action in {'return', 'reject'} and not data['note'].strip():
        form.add_error('note', 'Le motif est obligatoire pour un retour ou un refus.')
    if action in {'submit', 'approve'} and form.target_role and not data.get('assignee'):
        form.add_error('assignee', 'Choisissez la personne responsable de la prochaine étape.')
    if form.errors:
        return render_detail(request, record, form=form, status=400)
    if not record.payload or payload_digest(record.payload) != record.payload_hash or task.snapshot_hash != record.payload_hash or task.revision != record.revision:
        return render_detail(request, record, conflict=True, status=409)
    if action == 'submit' and policy()['expired']:
        form.add_error(None, 'La validité est échue. Une nouvelle soumission requiert le renouvellement par la maintenance.')
        return render_detail(request, record, form=form, status=403)
    before = record.status
    after = Status.DRAFT if action == 'return' else Status.REJECTED if action == 'reject' else NEXT[before][1] if before in NEXT else Status.APPROVED
    now = timezone.now()
    updates = {'status': after, 'updated_at': now}
    if action == 'submit':
        updates['cycle'] = record.cycle + 1
    if after == Status.APPROVED:
        approvals = record.tasks.filter(cycle=record.cycle, state=ValidationTask.State.APPROVED, stage__in=['SECAD', 'AP'], snapshot_hash=record.payload_hash, revision=record.revision)
        if set(approvals.values_list('stage', flat=True)) != {'SECAD', 'AP'}:
            return render_detail(request, record, conflict=True, status=409)
        from .composition import render_composed
        archived = render_composed(record.payload)
        updates.update(issued_pdf=archived, issued_hash=sha256(archived).hexdigest(), issued_at=now)
    try:
        with transaction.atomic():
            if not DocumentRequest.objects.filter(pk=record.pk, status=before, revision=record.revision, cycle=record.cycle).update(**updates):
                raise Conflict
            task.state = ValidationTask.State.RETURNED if action == 'return' else ValidationTask.State.REJECTED if action == 'reject' else ValidationTask.State.COMPLETED if action == 'submit' else ValidationTask.State.APPROVED
            task.note = data['note']; task.completed_at = now
            task.save(update_fields=['state', 'note', 'completed_at'])
            for key, value in updates.items():
                setattr(record, key, value)
            if action == 'return':
                new_task(record, 'OPS', record.owner, request.user)
            elif after not in {Status.APPROVED, Status.REJECTED}:
                new_task(record, STAGES[after], data['assignee'], request.user, data.get('due_at'))
            label = {'submit': 'Soumission à SECAD', 'approve': 'Validation finale' if role == 'DIRCAB' else f'Contrôle / visa {role}', 'return': f'Retour à OPS par {role}', 'reject': 'Refus final DIRCAB'}[action]
            RequestEvent.objects.create(request=record, actor=request.user, actor_role=role, event_type=action, status=after, note=f'{label}. {data["note"]}'.strip())
            from .usage import log_usage
            log_usage(request.user, action, record)
    except Conflict:
        record.refresh_from_db()
        return render_detail(request, record, conflict=True, status=409)
    request.session['sigda-feedback'] = 'Validation finale enregistrée : l’impression est autorisée.' if after == Status.APPROVED else 'Étape enregistrée et responsabilités actualisées.'
    return redirect('request_detail', pk=record.pk)


urlpatterns = [path('', queue, name='request_queue'), path('<uuid:pk>/', detail, name='request_detail'), path('<uuid:pk>/decision/', transition, name='request_transition')]
