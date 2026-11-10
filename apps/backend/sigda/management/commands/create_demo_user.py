from getpass import getpass
from os import environ

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Crée le compte local « demo » avec les droits d’un utilisateur standard."

    def handle(self, *args, **options):
        user_model = get_user_model()
        username = "demo"
        if user_model.objects.filter(username=username).exists():
            self.stdout.write("Le compte « demo » existe déjà.")
            return

        password = environ.get("SIGDA_DEMO_PASSWORD")
        if password is None:
            try:
                password = getpass("Mot de passe du compte demo : ")
                confirmation = getpass("Confirmez le mot de passe : ")
            except EOFError as error:
                raise CommandError("Définissez SIGDA_DEMO_PASSWORD ou lancez la commande dans un terminal.") from error
            if password != confirmation:
                raise CommandError("Les mots de passe ne correspondent pas.")

        try:
            validate_password(password, user_model(username=username))
        except ValidationError as error:
            raise CommandError(" ".join(error.messages)) from error

        _, created = user_model.objects.get_or_create(
            username=username,
            defaults={"password": make_password(password)},
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Compte local « demo » créé."))
        else:
            self.stdout.write("Le compte « demo » existe déjà.")
