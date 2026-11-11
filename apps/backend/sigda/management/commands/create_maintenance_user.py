from getpass import getpass
from os import environ

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = 'Crée un compte nominatif de maintenance. Aucun identifiant de maintenance n’est livré dans la démonstration publique.'

    def add_arguments(self, parser):
        parser.add_argument('username')

    def handle(self, *args, **options):
        username = options['username']
        users = get_user_model()
        if users.objects.filter(username=username).exists():
            raise CommandError('Ce compte existe déjà. Aucune habilitation ni aucun mot de passe n’a été modifié.')
        password = environ.get('SIGDA_MAINTENANCE_PASSWORD') or getpass('Mot de passe du compte de maintenance : ')
        try:
            validate_password(password, users(username=username))
        except ValidationError as error:
            raise CommandError(' '.join(error.messages)) from error
        with transaction.atomic():
            user = users.objects.create_user(username, password=password, is_staff=True)
            user.groups.add(Group.objects.get_or_create(name='SIGDA_MAINTENANCE')[0])
        self.stdout.write(self.style.SUCCESS('Compte de maintenance créé. Conservez ses identifiants dans votre gestionnaire de mots de passe.'))
