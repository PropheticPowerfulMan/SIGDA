from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.urls import include, path
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST, require_safe

from .activity import dashboard
from .catalog import AGENTS, DOCUMENT_TYPES, format_date
from .pdf import render_pdf
from .preview import render_preview
from .pwa import manifest, offline, service_worker


@never_cache
@login_required
@require_safe
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


def build_specimen(key, agent_key):
    try:
        document = DOCUMENT_TYPES[key]
        agent = AGENTS[agent_key]
    except KeyError as error:
        raise Http404("Agent ou modèle de démonstration inconnu.") from error

    today = timezone.localdate()
    reference = f"SPEC-{document.prefix}-{agent.registration}-{today.year}"
    pdf = render_pdf(key, document, agent, reference, format_date(today))
    return pdf, reference


@never_cache
@login_required
@require_safe
@xframe_options_sameorigin
def specimen(request, key, agent_key):
    pdf, reference = build_specimen(key, agent_key)
    disposition = "attachment" if request.GET.get("download") == "1" else "inline"
    return HttpResponse(pdf, content_type="application/pdf", headers={
        "Content-Disposition": f'{disposition}; filename="{reference}.pdf"',
    })


@never_cache
@login_required
@require_safe
def specimen_preview(request, key, agent_key):
    pdf, _ = build_specimen(key, agent_key)
    return HttpResponse(render_preview(pdf), content_type="image/png")


urlpatterns = [
    path("", workspace, name="workspace"),
    path("demandes/", include("sigda.workflow")),
    path("activite/", dashboard, name="activity"),
    path("connexion/", LoginView.as_view(), name="login"),
    path("deconnexion/", require_POST(LogoutView.as_view()), name="logout"),
    path("manifest.webmanifest", manifest, name="manifest"),
    path("sw.js", service_worker, name="service_worker"),
    path("offline.html", offline, name="offline"),
    path("specimens/<slug:key>/<slug:agent_key>.pdf", specimen, name="specimen"),
    path("specimens/<slug:key>/<slug:agent_key>.png", specimen_preview, name="specimen_preview"),
]
