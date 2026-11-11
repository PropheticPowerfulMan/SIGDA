from unicodedata import combining, normalize

from django.conf import settings
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
from .assistant import ask as assistant_ask, page as assistant_page
from .drafting import draft
from .wording import STYLES, document_text
from .catalog import AGENTS, DOCUMENT_TYPES, format_date
from .pdf import render_pdf
from .preview import render_preview
from .pwa import manifest, offline, service_worker


@never_cache
@login_required
@require_safe
def overview(request):
    return render(request, "overview.html", {
        "current_view": "overview",
        "current_label": "Vue d’ensemble",
        "agents": AGENTS,
        "document_types": DOCUMENT_TYPES,
    })


def search_text(value):
    return "".join(character for character in normalize("NFD", value.casefold()) if not combining(character))


@never_cache
@login_required
@require_safe
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
    pdf = render_pdf(key, document, agent, reference, format_date(today), wording=wording)
    return pdf, reference


@never_cache
@login_required
@require_safe
@xframe_options_sameorigin
def specimen(request, key, agent_key):
    wording = request.GET.get("wording", "classique")
    if wording not in STYLES:
        raise Http404
    pdf, reference = build_specimen(key, agent_key, wording)
    disposition = "attachment" if request.GET.get("download") == "1" else "inline"
    return HttpResponse(pdf, content_type="application/pdf", headers={
        "Content-Disposition": f'{disposition}; filename="{reference}.pdf"',
    })


@never_cache
@login_required
@require_safe
def specimen_preview(request, key, agent_key):
    wording = request.GET.get("wording", "classique")
    if wording not in STYLES:
        raise Http404
    pdf, _ = build_specimen(key, agent_key, wording)
    return HttpResponse(render_preview(pdf), content_type="image/png")


urlpatterns = [
    path("", workspace, name="workspace"),
    path("accueil/", overview, name="overview"),
    path("dossiers/", directory, name="agent_directory"),
    path("demandes/", include("sigda.workflow")),
    path("activite/", dashboard, name="activity"),
    path("assistant/", assistant_page, name="assistant"),
    path("assistant/question/", assistant_ask, name="assistant_ask"),
    path("atelier/reformulation/", draft, name="document_draft"),
    path("connexion/", LoginView.as_view(), name="login"),
    path("deconnexion/", require_POST(LogoutView.as_view()), name="logout"),
    path("manifest.webmanifest", manifest, name="manifest"),
    path("sw.js", service_worker, name="service_worker"),
    path("offline.html", offline, name="offline"),
    path("specimens/<slug:key>/<slug:agent_key>.pdf", specimen, name="specimen"),
    path("specimens/<slug:key>/<slug:agent_key>.png", specimen_preview, name="specimen_preview"),
]
