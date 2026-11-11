from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .models import UsageEvent
from .roles import role_for


def log_usage(user, action, document=None):
    if user and user.is_authenticated:
        UsageEvent.objects.create(actor=user, actor_role=role_for(user) or "", action=action, document=document)


@receiver(user_logged_in, dispatch_uid="sigda_login_usage")
def login_event(sender, request, user, **kwargs):
    log_usage(user, "login")
    if request is not None:
        request.session["sigda-feedback"] = "Connexion établie. Votre espace de travail est prêt."


@receiver(user_logged_out, dispatch_uid="sigda_logout_usage")
def logout_event(sender, request, user, **kwargs):
    log_usage(user, "logout")
