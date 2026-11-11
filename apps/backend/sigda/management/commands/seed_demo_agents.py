from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from sigda.catalog import AGENTS
from sigda.models import AgentRecord


class Command(BaseCommand):
    help = "Ajoute les deux dossiers fictifs dans la base du compte de démonstration."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="demo")

    def handle(self, *args, **options):
        try:
            owner = get_user_model().objects.get(username=options["username"])
        except get_user_model().DoesNotExist as error:
            raise CommandError("Créez d’abord le compte de démonstration.") from error
        for agent in AGENTS.values():
            AgentRecord.objects.get_or_create(owner=owner, registration=agent.registration, defaults={
                "name": agent.name, "service": agent.service, "job": agent.job, "grade": agent.grade})
        self.stdout.write(self.style.SUCCESS("Dossiers fictifs disponibles dans la base agents."))
