from os import environ

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from sigda.roles import ROLES


class Command(BaseCommand):
    help = "Prépare les quatre profils fictifs du circuit OPS → SECAD → AP → DIRCAB."

    def handle(self, *args, **options):
        password = environ.get("SIGDA_DEMO_PASSWORD")
        if not password:
            raise CommandError("Définissez SIGDA_DEMO_PASSWORD pour créer les comptes de démonstration.")
        users = get_user_model()
        for role in ROLES:
            group, _ = Group.objects.get_or_create(name="SIGDA_" + role)
            account, created = users.objects.get_or_create(username=role.lower())
            if created:
                account.set_password(password)
                account.save(update_fields=["password"])
            account.groups.remove(*account.groups.filter(name__startswith="SIGDA_"))
            account.groups.add(group)
            if role == "OPS":
                call_command("seed_demo_agents", username=account.username)
        demo = users.objects.filter(username="demo").first()
        if demo:
            demo.groups.remove(*demo.groups.filter(name__startswith="SIGDA_"))
            demo.groups.add(Group.objects.get(name="SIGDA_OPS"))
        self.stdout.write(self.style.SUCCESS("Comptes fictifs ops, secad, ap et dircab disponibles."))
