from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Agent:
    name: str
    registration: str
    service: str
    job: str
    grade: str


@dataclass(frozen=True)
class DocumentType:
    title: str
    description: str
    prefix: str
    category: str


AGENTS = {
    "alpha": Agent(
        "Camille Exemple", "DEMO-001", "Service des systèmes d’information",
        "technicienne des réseaux", "Agent d’administration de 1re classe",
    ),
    "beta": Agent(
        "Dominique Témoin", "DEMO-002", "Service de la gestion documentaire",
        "gestionnaire documentaire", "Agent d’administration de 2e classe",
    ),
}

DOCUMENT_TYPES = {
    "attestation-nuit": DocumentType(
        "Attestation de travail de nuit",
        "Certifier une affectation au service de nuit.",
        "ATN",
        "Attestations",
    ),
    "notification": DocumentType(
        "Notification administrative",
        "Notifier une régularisation de situation administrative.",
        "NOT",
        "Notifications",
    ),
    "attestation-service": DocumentType(
        "Attestation de service",
        "Présenter la fonction et l’affectation administrative d’un agent.",
        "ATS",
        "Attestations",
    ),
    "convocation": DocumentType(
        "Convocation administrative",
        "Inviter un agent à un entretien de mise à jour de son dossier.",
        "CON",
        "Notifications",
    ),
    "bordereau-transmission": DocumentType(
        "Bordereau de transmission",
        "Accompagner l’envoi d’une pièce administrative et en préciser la destination.",
        "BOR",
        "Transmission",
    ),
    "attestation-presence": DocumentType(
        "Attestation de présence", "Constater la présence d’un agent au service.",
        "APR", "Attestations",
    ),
    "attestation-affectation": DocumentType(
        "Attestation d’affectation", "Présenter le service d’affectation et la fonction exercée.",
        "AAF", "Attestations",
    ),
    "note-service": DocumentType(
        "Note de service", "Communiquer une consigne interne de gestion documentaire.",
        "NDS", "Correspondances",
    ),
    "lettre-transmission": DocumentType(
        "Lettre de transmission", "Adresser une pièce au service compétent.",
        "LTR", "Transmission",
    ),
    "autorisation-sortie": DocumentType(
        "Autorisation de sortie", "Préparer une autorisation pour une démarche administrative.",
        "ASO", "Autorisations",
    ),
    "ordre-mission": DocumentType(
        "Ordre de mission", "Préciser l’objet, le lieu et la durée d’une mission de démonstration.",
        "OM", "Missions",
    ),
}

MONTHS = (
    "janvier", "février", "mars", "avril", "mai", "juin", "juillet",
    "août", "septembre", "octobre", "novembre", "décembre",
)


def format_date(value: date) -> str:
    return f"{value.day} {MONTHS[value.month - 1]} {value.year}"
