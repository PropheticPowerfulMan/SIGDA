from getpass import getpass
from os import environ

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Permission
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Crée le compte local « demo » ou le compte distinct « demo-valideur »."

    def add_arguments(self, parser):
        parser.add_argument("--reviewer", action="store_true", help="Créer le compte valideur.")

    def handle(self, *args, **options):
        user_model = get_user_model()
        reviewer = options["reviewer"]
        username = "demo-valideur" if reviewer else "demo"
        password_env = "SIGDA_REVIEWER_PASSWORD" if reviewer else "SIGDA_DEMO_PASSWORD"
        if user_model.objects.filter(username=username).exists():
            self.stdout.write(f"Le compte « {username} » existe déjà.")
            return

        password = environ.get(password_env)
        if password is None:
            try:
                password = getpass(f"Mot de passe du compte {username} : ")
                confirmation = getpass("Confirmez le mot de passe : ")
            except EOFError as error:
                raise CommandError(f"Définissez {password_env} ou lancez la commande dans un terminal.") from error
            if password != confirmation:
                raise CommandError("Les mots de passe ne correspondent pas.")

        try:
            validate_password(password, user_model(username=username))
        except ValidationError as error:
            raise CommandError(" ".join(error.messages)) from error

        with transaction.atomic():
            user, created = user_model.objects.get_or_create(
                username=username,
                defaults={"password": make_password(password)},
            )
            if created and reviewer:
                permission = Permission.objects.get(
                    content_type__app_label="sigda", codename="review_documentrequest",
                )
                user.user_permissions.add(permission)
        if created:
            self.stdout.write(self.style.SUCCESS(f"Compte local « {username} » créé."))
        else:
            self.stdout.write(f"Le compte « {username} » existe déjà.")
