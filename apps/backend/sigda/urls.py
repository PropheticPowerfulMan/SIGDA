from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.urls import path
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_safe

from .catalog import AGENTS, DOCUMENT_TYPES, format_date
from .pdf import render_pdf


@require_safe
@never_cache
def workspace(request):
    selected_agent = request.GET.get("agent", next(iter(AGENTS)))
    selected_type = request.GET.get("type", next(iter(DOCUMENT_TYPES)))
    if selected_agent not in AGENTS or selected_type not in DOCUMENT_TYPES:
        raise Http404("Agent ou modèle de démonstration inconnu.")

    return render(request, "workspace.html", {
        "agents": AGENTS,
        "document_types": DOCUMENT_TYPES,
        "selected_agent": selected_agent,
        "selected_type": selected_type,
        "agent": AGENTS[selected_agent],
        "document": DOCUMENT_TYPES[selected_type],
    })


@require_safe
@never_cache
@xframe_options_sameorigin
def specimen(request, key, agent_key):
    try:
        document = DOCUMENT_TYPES[key]
        agent = AGENTS[agent_key]
    except KeyError as error:
        raise Http404("Agent ou modèle de démonstration inconnu.") from error

    today = timezone.localdate()
    reference = f"SPEC-{document.prefix}-{agent.registration}-{today.year}"
    pdf = render_pdf(key, document, agent, reference, format_date(today))
    disposition = "attachment" if request.GET.get("download") == "1" else "inline"
    return HttpResponse(pdf, content_type="application/pdf", headers={
        "Content-Disposition": f'{disposition}; filename="{reference}.pdf"',
    })


urlpatterns = [
    path("", workspace, name="workspace"),
    path("specimens/<slug:key>/<slug:agent_key>.pdf", specimen, name="specimen"),
]
