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
    ),
    "notification": DocumentType(
        "Notification administrative",
        "Notifier une régularisation de situation administrative.",
        "NOT",
    ),
}

MONTHS = (
    "janvier", "février", "mars", "avril", "mai", "juin", "juillet",
    "août", "septembre", "octobre", "novembre", "décembre",
)


def format_date(value: date) -> str:
    return f"{value.day} {MONTHS[value.month - 1]} {value.year}"
