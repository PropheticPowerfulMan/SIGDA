from datetime import date, timedelta
from functools import wraps

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone

from .models import ServiceValidity


def annual_end(start):
    try:
        return start.replace(year=start.year + 1)
    except ValueError:
        return start.replace(year=start.year + 1, day=28)


def policy(today=None):
    today = today or timezone.localdate()
    window = ServiceValidity.objects.filter(pk=1).first()
    config = settings.SIGDA_DEPLOYMENT
    start = window.starts_on if window else date.fromisoformat(config['valid_from'])
    end = window.expires_on if window else date.fromisoformat(config['valid_until'])
    last_day = end - timedelta(days=1)
    days = (end - today).days
    state = 'expired' if today >= end else 'preparation' if today < start else 'reminder' if days <= config['reminder_days'] else 'active'
    return {'start': start, 'end': end, 'last_day': last_day, 'days': max(0, days), 'state': state,
            'expired': state == 'expired', 'institution': config['institution']}


def creation_allowed(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if policy()['expired']:
            return JsonResponse({'error': 'La période de validité est échue. Contactez la maintenance pour le renouvellement. Les documents validés restent accessibles.'}, status=403)
        return view(request, *args, **kwargs)
    return wrapped


def service_context(request):
    return {'service_policy': policy(), 'feedback_message': request.session.pop('sigda-feedback', '') if request.method == 'GET' else ''}
