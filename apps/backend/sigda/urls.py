from unicodedata import combining, normalize

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.views import LoginView, LogoutView
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import include, path
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST, require_safe

from .activity import dashboard
from .assistant import ask as assistant_ask, page as assistant_page
from .drafting import draft
from .wording import STYLES, document_text
from .catalog import AGENTS, DOCUMENT_TYPES, format_date
from .pdf import render_pdf
from .preview import render_preview
from . import document_integrity
from .pwa import manifest, offline, service_worker
from . import composition, maintenance
from .models import AgentRecord
from .roles import require_ops, is_maintainer
from .dashboards import dashboard_data
from .security import ProtectedLoginView
from django.core.exceptions import PermissionDenied


@never_cache
@login_required
@require_safe
def overview(request):
    if is_maintainer(request.user):return redirect('maintenance')
    return render(request, "overview.html", {
        "current_view": "overview",
        "dashboard": dashboard_data(request.user),
        "current_label": "Vue d’ensemble",
        "agents": AGENTS,
        "document_types": DOCUMENT_TYPES,
        "saved_agent_count": AgentRecord.objects.filter(owner=request.user).count(),
    })


def search_text(value):
    return "".join(character for character in normalize("NFD", value.casefold()) if not combining(character))


@never_cache
@login_required
@require_safe
@require_ops
def directory(request):
    query = request.GET.get("q", "").strip()
    needle = search_text(query)
    agents = {
        key: agent for key, agent in AGENTS.items()
        if needle in search_text(f"{agent.name} {agent.registration} {agent.service}")
    }
    return render(request, "directory.html", {
        "current_view": "directory",
        "current_label": "Dossiers agents",
        "agents": agents,
        "saved_agents": [record for record in AgentRecord.objects.filter(owner=request.user)
                         if needle in search_text(f"{record.name} {record.registration} {record.service}")],
        "query": query,
    })


@never_cache
@login_required
@require_safe
def workspace(request):
    selected_agent = request.GET.get("agent", next(iter(AGENTS)))
    selected_type = request.GET.get("type", next(iter(DOCUMENT_TYPES)))
    if selected_agent not in AGENTS or selected_type not in DOCUMENT_TYPES:
        raise Http404("Agent ou modèle de démonstration inconnu.")

    families = tuple(dict.fromkeys(kind.category for kind in DOCUMENT_TYPES.values()))
    family = request.GET.get("family", "")
    if family not in families:
        family = ""
    wording = request.GET.get("wording", "classique")
    if wording not in STYLES:
        wording = "classique"
    return render(request, "workspace.html", {
        "current_view": "workspace",
        "current_label": "Atelier documentaire",
        "agents": AGENTS,
        "document_types": DOCUMENT_TYPES,
        "selected_agent": selected_agent,
        "selected_type": selected_type,
        "family": family,
        "wording": wording,
        "styles": STYLES,
        "body_text": document_text(selected_type, AGENTS[selected_agent], format_date(timezone.localdate()), wording),
        "gpt_available": bool(settings.OPENAI_API_KEY),
        "families": families,
        "catalogue_items": {
            key: kind for key, kind in DOCUMENT_TYPES.items()
            if not family or kind.category == family
        },
        "agent": AGENTS[selected_agent],
        "document": DOCUMENT_TYPES[selected_type],
    })


def build_specimen(key, agent_key, wording="classique"):
    try:
        document = DOCUMENT_TYPES[key]
        agent = AGENTS[agent_key]
    except KeyError as error:
        raise Http404("Agent ou modèle de démonstration inconnu.") from error

    today = timezone.localdate()
    reference = f"SPEC-{document.prefix}-{agent.registration}-{today.year}"
    pdf = render_pdf(key, document, agent, reference, format_date(today), wording=wording, preview_only=True)
    return pdf, reference


@never_cache
@login_required
@require_safe
@xframe_options_sameorigin
def specimen(request, key, agent_key):
    wording = request.GET.get("wording", "classique")
    if wording not in STYLES:
        raise Http404
    if key not in DOCUMENT_TYPES or agent_key not in AGENTS:
        raise Http404
    return HttpResponseForbidden('Les exemples ne sont pas imprimables. Préparez un document et faites-le valider par DIRCAB.')


@never_cache
@login_required
@require_safe
def specimen_preview(request, key, agent_key):
    wording = request.GET.get("wording", "classique")
    if wording not in STYLES:
        raise Http404
    pdf, _ = build_specimen(key, agent_key, wording)
    return HttpResponse(render_preview(pdf), content_type="image/png")


@never_cache
@require_POST
def exit_session(request):
    auth_logout(request)
    request.session['sigda-feedback'] = 'Déconnexion effectuée.'
    return redirect('login')


urlpatterns = [
    path('verification/<uuid:pk>/',document_integrity.verify,name='verify_document'),
    path('maintenance/etat/',maintenance.status,name='maintenance_status'),
    path("assistance/", maintenance.support, name="support"),
    path("maintenance/", maintenance.administration, name="maintenance"),
    path("composer/", composition.page, name="compose"),
    path("composer/apercu/", composition.preview, name="compose_preview"),
    path("composer/enregistrer/", composition.save, name="compose_save"),
    path("dossiers/enregistrer/", composition.save_agent, name="agent_save"),
    path("documents/<uuid:pk>.<str:extension>", composition.saved_document, name="saved_document"),
    path("", lambda request: redirect("login"), name="entry"),
    path("atelier/", workspace, name="workspace"),
    path("accueil/", overview, name="overview"),
    path("dossiers/", directory, name="agent_directory"),
    path("demandes/", include("sigda.workflow")),
    path("activite/", dashboard, name="activity"),
    path("assistant/", assistant_page, name="assistant"),
    path("assistant/question/", assistant_ask, name="assistant_ask"),
    path("atelier/reformulation/", draft, name="document_draft"),
    path("connexion/", ProtectedLoginView.as_view(), name="login"),
    path("deconnexion/", exit_session, name="logout"),
    path("manifest.webmanifest", manifest, name="manifest"),
    path("sw.js", service_worker, name="service_worker"),
    path("offline.html", offline, name="offline"),
    path("specimens/<slug:key>/<slug:agent_key>.pdf", specimen, name="specimen"),
    path("specimens/<slug:key>/<slug:agent_key>.png", specimen_preview, name="specimen_preview"),
]
