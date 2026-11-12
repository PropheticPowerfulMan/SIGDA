from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

from .models import DocumentRequest, UsageEvent
from .roles import role_for, is_maintainer


def milliseconds(value):
    return round(value.timestamp() * 1000) if value else None


@never_cache
@login_required
@require_safe
def dashboard(request):
    if role_for(request.user) != 'DIRCAB' and not is_maintainer(request.user):
        raise PermissionDenied('Le pilotage global est réservé à DIRCAB et à la maintenance habilitée.')
    now = timezone.now()
    begin = now - timedelta(days=91)
    records = []
    for record in DocumentRequest.objects.only('id','status').prefetch_related('events', 'tasks'):
        records.append({'id': str(record.pk), 'status': record.status,
            'events': [{'at': milliseconds(e.created_at), 'type': e.event_type, 'status': e.status} for e in record.events.all()],
            'tasks': [{'stage': t.stage, 'state': t.state, 'createdAt': milliseconds(t.created_at),
                       'completedAt': milliseconds(t.completed_at), 'dueAt': milliseconds(t.due_at)} for t in record.tasks.all()]})
    usage = [{'at': milliseconds(e.created_at), 'actor': e.actor.get_username(), 'role': e.actor_role,
              'action': e.action, 'reference': str(e.document_id or '')}
             for e in UsageEvent.objects.filter(created_at__gte=begin).select_related('actor').order_by('created_at', 'id')]
    return render(request, 'workflow/activity.html', {'current_view': 'activity', 'current_label': 'Pilotage technique' if is_maintainer(request.user) else 'Pilotage DIRCAB',
        'statistics_data': {'now': milliseconds(now), 'records': records, 'usage': usage}})
