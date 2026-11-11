from base64 import b64encode
from collections import Counter
import re
from urllib.error import URLError

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .assistant import gpt_answer, gpt_limit_reached
from .catalog import AGENTS, DOCUMENT_TYPES, format_date
from .pdf import render_pdf
from .preview import render_preview
from .wording import STYLES, document_text


class DraftingForm(forms.Form):
    agent = forms.ChoiceField(choices=[(key, key) for key in AGENTS])
    kind = forms.ChoiceField(choices=[(key, key) for key in DOCUMENT_TYPES])
    wording = forms.ChoiceField(choices=list(STYLES.items()))
    action = forms.ChoiceField(choices=[("rewrite", "rewrite"), ("preview", "preview")])
    mode = forms.ChoiceField(choices=[("local", "local"), ("gpt", "gpt")])
    text = forms.CharField(max_length=1800)

    def clean_text(self):
        return self.cleaned_data["text"].replace("\r\n", "\n").replace("\r", "\n")


def validate_facts(text, original, agent):
    protected = [agent.name, agent.registration, agent.service, agent.job, agent.grade]
    if any(value in original and value not in text for value in protected):
        raise ValueError("Conservez les noms, le matricule, la fonction, le grade et le service du texte initial.")
    if Counter(re.findall(r"\d+", text)) != Counter(re.findall(r"\d+", original)):
        raise ValueError("Conservez les dates et les autres données chiffrées du texte initial.")


@never_cache
@login_required
@require_POST
def draft(request):
    form = DraftingForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"error": "Vérifiez le modèle, le style et le texte (1 à 1 800 caractères)."}, status=400)
    data = form.cleaned_data
    agent = AGENTS[data["agent"]]
    model = DOCUMENT_TYPES[data["kind"]]
    date = timezone.localdate()
    date_label = format_date(date)
    original = document_text(data["kind"], agent, date_label)
    text = data["text"]
    style = data["wording"]
    try:
        if data["action"] == "rewrite":
            if data["mode"] == "local":
                styles = list(STYLES)
                style = styles[(styles.index(style) + 1) % len(styles)]
                text = document_text(data["kind"], agent, date_label, style)
            else:
                if not settings.OPENAI_API_KEY:
                    return JsonResponse({"error": "Configurez la connexion GPT dans le serveur."}, status=503)
                if gpt_limit_reached(request.user):
                    return JsonResponse({"error": "Limite GPT atteinte. Réessayez dans une minute."}, status=429)
                validate_facts(text, original, agent)
                text = gpt_answer(text, instructions=(
                    "Reformule le français de ce corps de document administratif congolais. "
                    "Produis seulement le corps du texte, en paragraphes, sans titre ni markdown. "
                    "Préserve exactement les noms, matricules, fonctions, grades, services, dates, "
                    "nombres et faits. N’ajoute aucune décision ni aucun fait. "
                    "Varie la syntaxe et emploie un registre administratif sobre. "
                    "Le résultat doit rester inférieur à 1800 caractères."
                )).replace("\r\n", "\n").replace("\r", "\n")
            if len(text) > 1800:
                raise ValueError("La reformulation est trop longue. Raccourcissez-la avant de l’appliquer.")
            validate_facts(text, original, agent)
            return JsonResponse({"text": text, "wording": style})

        validate_facts(text, original, agent)
        reference = f"SPEC-{model.prefix}-{agent.registration}-{date.year}"
        pdf = render_pdf(data["kind"], model, agent, reference, date_label, body_text=text, preview_only=True)
        return JsonResponse({
            "preview": "data:image/png;base64," + b64encode(render_preview(pdf)).decode("ascii"),
            "filename": reference + ".pdf",
        })
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    except (URLError, OSError, TimeoutError, KeyError, TypeError, AttributeError):
        return JsonResponse({"error": "La reformulation GPT est indisponible. Le texte proposé reste à relire."}, status=502)
