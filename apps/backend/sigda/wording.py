STYLES = {"classique": "Classique", "formel": "Formel", "direct": "Direct"}


def document_text(key, agent, date_label, style="classique"):
    identity = f"{agent.name}, matricule {agent.registration}"
    role = f"{agent.job} au {agent.service}"
    facts = {
        "attestation-nuit": f"{identity} exerce en qualité de {role} et assure le service de nuit.",
        "attestation-service": f"{identity} exerce en qualité de {role}. Son grade est {agent.grade}.",
        "attestation-presence": f"La présence au service de {identity}, exerçant en qualité de {role}, est constatée le {date_label}.",
        "attestation-affectation": f"{identity} est affecté au {agent.service} et exerce la fonction de {agent.job}.",
        "notification": f"La situation administrative de {identity} est mise à jour au grade de {agent.grade}.",
        "convocation": f"{identity} est invité à un entretien de mise à jour de son dossier au service des ressources humaines, à Kinshasa. La date et l’heure de rendez-vous seront communiquées par le service.",
        "bordereau-transmission": f"Le {agent.service} transmet au service des ressources humaines une fiche de situation administrative concernant {identity}, pour vérification.",
        "lettre-transmission": f"Nous vous transmettons, pour examen et suite utile, une fiche de situation administrative relative à {identity}, exerçant en qualité de {role}.",
        "note-service": f"Dans le cadre de la mise à jour du dossier de {identity}, le {agent.service} est invité à transmettre les pièces justificatives disponibles au service des ressources humaines.",
        "autorisation-sortie": f"{identity}, exerçant en qualité de {role}, est autorisé dans ce scénario fictif à se rendre au service des ressources humaines à Kinshasa, le {date_label}, de 10 h à 12 h.",
        "ordre-mission": f"{identity}, exerçant en qualité de {role}, est désigné dans ce scénario fictif pour une mission de vérification documentaire à Kinshasa. La mission se déroule le {date_label}, pour une durée de 1 jour. Un compte rendu sera adressé au service des ressources humaines.",
    }
    if key not in facts or style not in STYLES:
        raise ValueError("Modèle ou style inconnu.")
    openings = {
        "classique": "Le présent document est établi pour les besoins de la démonstration SIGDA.",
        "formel": "Pour les besoins de la démonstration SIGDA, il est porté à la connaissance du destinataire les indications suivantes.",
        "direct": "Ce spécimen SIGDA présente les informations administratives ci-dessous.",
    }
    closings = {
        "classique": "Ce spécimen est soumis à la vérification du service compétent.",
        "formel": "Les présentes indications appellent la vérification et la validation du service compétent.",
        "direct": "Le service compétent est invité à vérifier ces informations avant validation.",
    }
    if key.startswith("attestation-"):
        openings = {
            "classique": "L’autorité habilitée du service des ressources humaines atteste ce qui suit.",
            "formel": "Il est attesté par le service des ressources humaines les faits ci-après.",
            "direct": "Le service des ressources humaines certifie les informations suivantes.",
        }
        closings = {
            "classique": "La présente attestation est établie pour servir et faire valoir ce que de droit.",
            "formel": "La présente est délivrée à l’intéressé pour les suites administratives utiles.",
            "direct": "Cette attestation est remise à l’intéressé pour les besoins de son dossier administratif.",
        }
    elif key in {"notification", "convocation", "lettre-transmission"}:
        openings = {"classique": "Madame, Monsieur,", "formel": "Madame, Monsieur,", "direct": "Madame, Monsieur,"}
        closings = {
            "classique": "Veuillez agréer, Madame, Monsieur, l’expression de notre considération distinguée.",
            "formel": "Nous vous prions d’agréer, Madame, Monsieur, l’assurance de notre considération distinguée.",
            "direct": "Nous vous remercions de l’attention portée à la présente correspondance.",
        }
    return f"{openings[style]}\n\n{facts[key]}\n\n{closings[style]}"
