"""Configuration réservée à la démonstration sur la boucle locale."""

from os import environ
from pathlib import Path
from secrets import token_urlsafe

BASE_DIR = Path(__file__).resolve().parents[1]
SECRET_KEY = environ.get("SIGDA_SECRET_KEY") or token_urlsafe(48)
OPENAI_API_KEY = environ.get("OPENAI_API_KEY", "")
SIGDA_OPENAI_MODEL = environ.get("SIGDA_OPENAI_MODEL", "gpt-5.4-mini")
DEBUG = False
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
ROOT_URLCONF = "sigda.urls"
LANGUAGE_CODE = "fr"
TIME_ZONE = "Africa/Kinshasa"
USE_TZ = True

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "sigda",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "overview"
LOGOUT_REDIRECT_URL = "login"
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
X_FRAME_OPTIONS = "DENY"
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR.parent / "demo"]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "OPTIONS": {
            "context_processors": ["django.contrib.auth.context_processors.auth", "sigda.roles.workspace_role"],
        },
    }
]
