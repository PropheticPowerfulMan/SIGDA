from django.apps import AppConfig


class SigdaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sigda"

    def ready(self):
        from . import usage
