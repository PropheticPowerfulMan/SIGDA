"""Explicit HTTPS deployment profile; never silently use development credentials."""
from .settings import *
from django.core.exceptions import ImproperlyConfigured

SECRET_KEY=environ.get('SIGDA_SECRET_KEY','')
if len(SECRET_KEY)<50 or SECRET_KEY.startswith('django-insecure-'):
    raise ImproperlyConfigured('Une clé SIGDA_SECRET_KEY privée d’au moins 50 caractères est requise.')
ALLOWED_HOSTS=[value.strip() for value in environ.get('SIGDA_ALLOWED_HOSTS','').split(',') if value.strip()]
if not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS:
    raise ImproperlyConfigured('Définissez les noms d’hôte explicites dans SIGDA_ALLOWED_HOSTS.')
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
STATIC_ROOT=BASE_DIR/'static-collected'
if environ.get('SIGDA_TRUST_HTTPS_PROXY')=='1':
    SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO','https')
