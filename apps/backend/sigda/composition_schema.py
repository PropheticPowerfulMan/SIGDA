"""Shared field descriptions and factual templates for the guided composer."""
from datetime import date
import json
from pathlib import Path

SERVICES = json.loads((Path(__file__).resolve().parents[3] / "config/services.json").read_text(encoding="utf-8"))

from .catalog import Agent, format_date
from .wording import STYLES


def field(key, label, kind="text", example="", maximum=100):
    return {"key": key, "label": label, "type": kind, "example": example, "max": maximum}


IDENTITY_FIELDS = [
    field("name", "Nom complet de l’agent", example="Ex. Camille Exemple"),
    field("registration", "Matricule", example="Ex. DEMO-001", maximum=40),
    {**field("service", "Service d’affectation", "select"), "options": SERVICES},
    field("job", "Fonction exercée", example="Ex. Technicienne des réseaux"),
    field("grade", "Grade administratif", example="Ex. Agent d’administration de 1re classe"),
]
COMMON_FIELDS = [
    field("issuer_service", "Service qui établit le document", example="Ex. Service des ressources humaines", maximum=80),
    field("place", "Ville d’établissement", example="Ex. Kinshasa", maximum=50),
    field("issue_date", "Date du document", "date"),
    field("signatory", "Nom du signataire (facultatif)", maximum=80),
    field("signatory_role", "Qualité du signataire", example="Ex. Responsable du service", maximum=80),
]
MODELS = {
    "attestation-service": {"subject": "agent", "fields": [field("since", "En service depuis le", "date"), field("purpose", "Utilisation prévue de l’attestation", example="Ex. Complément du dossier administratif", maximum=160)],
        "facts": "{name}, matricule {registration}, exerce la fonction de {job} au {service}, au grade de {grade}. La prise de service date du {since}. Cette attestation est demandée pour {purpose}."},
    "attestation-nuit": {"subject": "agent", "fields": [field("since", "Début de l’affectation de nuit", "date"), field("schedule", "Horaire du service de nuit", example="Ex. De 20 h à 6 h", maximum=80)],
        "facts": "{name}, matricule {registration}, exerce la fonction de {job} au {service}, au grade de {grade}. L’agent assure le service de nuit depuis le {since}, selon l’horaire suivant : {schedule}."},
    "attestation-presence": {"subject": "agent", "fields": [field("presence_date", "Présence constatée le", "date"), field("presence_place", "Lieu de présence", example="Ex. Bureau du service", maximum=100)],
        "facts": "La présence de {name}, matricule {registration}, est constatée le {presence_date} à {presence_place}. L’agent exerce la fonction de {job} au {service}, au grade de {grade}."},
    "attestation-affectation": {"subject": "agent", "fields": [field("effective_date", "Date d’effet de l’affectation", "date")],
        "facts": "{name}, matricule {registration}, est affecté au {service} avec effet au {effective_date}, pour exercer la fonction de {job}, au grade de {grade}."},
    "notification": {"subject": "agent", "fields": [field("decision_ref", "Référence de la décision", example="Ex. Décision n° DEMO/2026/01"), field("decision_date", "Date de la décision", "date"), field("reason", "Objet de la notification", example="Ex. Mise à jour de la situation administrative", maximum=180)],
        "facts": "La décision {decision_ref}, datée du {decision_date}, concernant {reason}, est notifiée à {name}, matricule {registration}, exerçant la fonction de {job} au {service}, au grade de {grade}."},
    "convocation": {"subject": "agent", "fields": [field("meeting_date", "Date du rendez-vous", "date"), field("meeting_time", "Heure du rendez-vous", "time"), field("meeting_place", "Lieu du rendez-vous", example="Ex. Bureau des ressources humaines"), field("reason", "Motif de la convocation", example="Ex. Vérification des pièces du dossier", maximum=180)],
        "facts": "{name}, matricule {registration}, exerçant la fonction de {job} au {service}, au grade de {grade}, est invité à se présenter le {meeting_date} à {meeting_time}, à {meeting_place}, pour {reason}."},
    "bordereau-transmission": {"subject": "piece", "fields": [field("recipient", "Service destinataire", example="Ex. Direction des ressources humaines"), field("item", "Pièce ou dossier transmis", example="Ex. Dossier de mise à jour administrative", maximum=160), field("quantity", "Nombre de pièces", "number"), field("purpose", "Suite attendue", example="Ex. Vérification et classement", maximum=160)],
        "facts": "Le {issuer_service} transmet à {recipient} les pièces suivantes : {item}. Nombre de pièces : {quantity}. Suite attendue : {purpose}."},
    "lettre-transmission": {"subject": "piece", "fields": [field("recipient", "Service destinataire", example="Ex. Direction des ressources humaines"), field("item", "Pièce ou dossier transmis", example="Ex. Rapport d’activité", maximum=160), field("quantity", "Nombre de pièces", "number"), field("purpose", "Suite attendue", example="Ex. Examen et suite utile", maximum=160)],
        "facts": "Nous transmettons à {recipient}, au nom du {issuer_service}, les pièces suivantes : {item}, en quantité de {quantity}. Cet envoi appelle la suite suivante : {purpose}."},
    "note-service": {"subject": "service", "fields": [field("recipient", "Service ou personnel concerné", example="Ex. Tous les chefs de bureau"), field("subject", "Objet de la note", example="Ex. Actualisation des dossiers"), field("instructions", "Consigne à communiquer", "textarea", "Ex. Transmettre les fiches mises à jour au secrétariat.", 400)],
        "facts": "À l’attention de {recipient}. Objet : {subject}.\n\n{instructions}"},
    "autorisation-sortie": {"subject": "agent", "fields": [field("exit_date", "Date de la sortie", "date"), field("from_time", "Heure de départ", "time"), field("to_time", "Heure de retour prévue", "time"), field("destination", "Destination", example="Ex. Bureau administratif de Gombe"), field("reason", "Motif de la sortie", example="Ex. Dépôt de pièces administratives", maximum=160)],
        "facts": "Une autorisation de sortie est accordée à {name}, matricule {registration}, exerçant la fonction de {job} au {service}, au grade de {grade}. La sortie est prévue le {exit_date}, de {from_time} à {to_time}, à destination de {destination}, pour {reason}."},
    "ordre-mission": {"subject": "agent", "fields": [field("mission_start", "Début de la mission", "date"), field("mission_end", "Fin de la mission", "date"), field("destination", "Lieu de la mission", example="Ex. Kinshasa / Gombe"), field("objective", "Objet de la mission", "textarea", "Ex. Vérification et inventaire des pièces administratives.", 260)],
        "facts": "{name}, matricule {registration}, exerçant la fonction de {job} au {service}, au grade de {grade}, est désigné pour une mission à {destination}. La mission se déroule du {mission_start} au {mission_end}, soit {duration} jour(s) calendaires. Objet de la mission : {objective}."},
}
OPENINGS = {"classique": "Le service compétent établit le présent document sur la base des informations ci-après.", "formel": "Il est porté à la connaissance du destinataire les éléments administratifs suivants.", "direct": "Les informations administratives à prendre en compte sont les suivantes."}
CLOSINGS = {"classique": "Le présent document est établi pour les suites administratives utiles.", "formel": "La présente est soumise à la vérification et à la validation de l’autorité compétente.", "direct": "Ces informations sont à vérifier avant validation du document."}


def compose_text(data):
    schema = MODELS[data["kind"]]
    values = dict(data)
    for spec in COMMON_FIELDS + schema["fields"]:
        key = spec["key"]
        if spec["type"] == "date":
            values[key] = format_date(date.fromisoformat(str(values[key])))
        elif spec["type"] == "time":
            values[key] = str(values[key])[:5].replace(":", " h ")
    if data["kind"] == "ordre-mission":
        values["duration"] = (date.fromisoformat(data["mission_end"]) - date.fromisoformat(data["mission_start"])).days + 1
    style = data["wording"]
    return OPENINGS[style] + "\n\n" + schema["facts"].format_map(values) + "\n\n" + CLOSINGS[style]


def compose_agent(data):
    if MODELS[data["kind"]]["subject"] != "agent":
        return Agent(data.get("item") or data.get("subject") or data["issuer_service"], "", data["issuer_service"], "", "")
    return Agent(*(data[field] for field in ("name", "registration", "service", "job", "grade")))
