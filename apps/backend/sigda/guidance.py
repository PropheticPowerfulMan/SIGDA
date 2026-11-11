from unicodedata import combining, normalize

from .catalog import DOCUMENT_TYPES


GUIDES = [
    {
        "title": "Imprimer un document A4",
        "terms": ["imprimer", "impression", "papier", "a4", "zoom", "pdf"],
        "text": "Dans l’atelier, choisissez l’agent et le modèle, puis utilisez Imprimer. "
                "Le dialogue du navigateur permet de choisir l’imprimante et le format A4. "
                "Le PDF peut aussi être ouvert dans votre lecteur pour l’impression.",
        "target": "documents",
    },
    {
        "title": "Soumettre et suivre une demande",
        "terms": ["demande", "soumettre", "brouillon", "validation", "approbation", "refus"],
        "text": "Créez un brouillon dans Demandes, puis soumettez-le. Dans Django, "
                "un compte distinct habilité peut approuver ou refuser. Un refus exige un motif. "
                "L’historique conserve les étapes et leurs auteurs.",
        "target": "requests",
    },
    {
        "title": "Comprendre les indicateurs",
        "terms": ["activite", "statistique", "statistiques", "delai", "mediane", "p90", "tracabilite"],
        "text": "Activité présente le journal et les indicateurs. Le taux d’approbation rapporte "
                "les approbations à toutes les décisions. Dans Django, la médiane et le P90 "
                "mesurent les délais entre soumission et décision sur la période choisie.",
        "target": "activity",
    },
]

ALIASES = {"attestation-service": ["emploi", "fonction", "affectation"],
           "convocation": ["entretien", "convoquer"],
           "bordereau-transmission": ["transmettre", "envoi", "piece"]}
STOPWORDS = {"de", "du", "des", "la", "le", "les", "un", "une", "pour", "comment", "quel", "quelle", "document", "je"}


def tokens(text):
    plain = "".join(char for char in normalize("NFD", text.casefold()) if not combining(char))
    return {word for word in "".join(char if char.isalnum() else " " for char in plain).split()
            if len(word) > 1 and word not in STOPWORDS}


def local_answer(question):
    words = tokens(question)
    scored = []
    for guide in GUIDES:
        score = len(words & set(guide["terms"]))
        if score:
            scored.append((score, guide["text"], guide["title"], guide["target"], None))
    for key, model in DOCUMENT_TYPES.items():
        score = len(words & (tokens(model.title) | set(ALIASES.get(key, ()))))
        if score:
            scored.append((score, model.description, model.title, "documents", key))
    scored.sort(key=lambda row: row[0], reverse=True)
    selected = scored[:3]
    if not selected:
        return {
            "text": "Je peux vous guider dans le catalogue, l’impression A4, les demandes et les statistiques. "
                    "Précisez le document recherché ou l’étape qui vous pose une difficulté.",
            "links": [],
        }
    return {
        "text": "\n\n".join(f"{title}\n{text}" for _, text, title, _, _ in selected),
        "links": [{"label": title, "target": target, "model": model}
                  for _, _, title, target, model in selected],
    }
