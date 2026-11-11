import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_safe

from .catalog import DOCUMENT_TYPES
from .guidance import local_answer


class QuestionForm(forms.Form):
    question = forms.CharField(max_length=2000)
    mode = forms.ChoiceField(choices=[("local", "Local"), ("gpt", "GPT")])


def gpt_answer(question, instructions=None):
    catalogue = "\n".join(f"- {model.title} : {model.description}" for model in DOCUMENT_TYPES.values())
    default_instructions = (
        "Tu es l’assistant de SIGDA, atelier documentaire en français. Réponds de façon concise. "
        "Les documents sont des spécimens non valables. Les modèles disponibles sont fournis ci-dessous. "
        "Aide à choisir un modèle, préparer une demande, relire ou formuler un texte administratif. "
        "N’invente ni décision, ni habilitation, ni résultat d’une action dans SIGDA. "
        "N’affirme pas avoir accédé à des dossiers. Invite à vérifier les faits et faire valider les actes.\n"
        + catalogue
    )
    payload = json.dumps({
        "model": settings.SIGDA_OPENAI_MODEL,
        "instructions": default_instructions if instructions is None else instructions,
        "input": question,
        "store": False,
        "max_output_tokens": 1200,
    }).encode("utf-8")
    request = Request(
        "https://api.openai.com/v1/responses",
        data=payload,
        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=25) as response:
        data = response.read(1024 * 1024 + 1)
    if len(data) > 1024 * 1024:
        raise ValueError("Réponse trop volumineuse")
    body = json.loads(data)
    parts = [
        content["text"]
        for item in body.get("output", []) if item.get("type") == "message"
        for content in item.get("content", [])
        if content.get("type") == "output_text" and isinstance(content.get("text"), str)
    ]
    if not parts:
        raise ValueError("Réponse sans texte")
    return "\n".join(parts)


def gpt_limit_reached(user):
    key = f"sigda-gpt:{user.pk}:{int(time.time() // 60)}"
    cache.add(key, 0, 70)
    return cache.incr(key) > 10


@never_cache
@login_required
@require_safe
def page(request):
    return render(request, "assistant.html", {
        "current_view": "assistant",
        "current_label": "Assistant",
        "gpt_available": bool(settings.OPENAI_API_KEY),
    })


@never_cache
@login_required
@require_POST
def ask(request):
    form = QuestionForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"error": "Saisissez une question de 1 à 2 000 caractères et choisissez un mode."}, status=400)
    question = form.cleaned_data["question"]
    mode = form.cleaned_data["mode"]
    if mode == "local":
        return JsonResponse({**local_answer(question), "mode": "Guidage local"})
    if not settings.OPENAI_API_KEY:
        return JsonResponse({"error": "La connexion GPT doit être configurée dans le serveur."}, status=503)
    if gpt_limit_reached(request.user):
        return JsonResponse({"error": "Limite de 10 questions GPT par minute atteinte. Réessayez dans une minute."}, status=429)
    try:
        text = gpt_answer(question)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, KeyError, TypeError, AttributeError):
        return JsonResponse({"error": "GPT est momentanément indisponible. Vous pouvez utiliser le guidage local."}, status=502)
    return JsonResponse({"text": text, "links": [], "mode": "GPT"})
