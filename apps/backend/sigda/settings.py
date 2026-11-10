"""Configuration réservée à la démonstration sur la boucle locale."""

from pathlib import Path
from secrets import token_urlsafe

BASE_DIR = Path(__file__).resolve().parents[1]
SECRET_KEY = token_urlsafe(48)
DEBUG = False
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
ROOT_URLCONF = "sigda.urls"
LANGUAGE_CODE = "fr"
TIME_ZONE = "Africa/Kinshasa"
USE_TZ = True

INSTALLED_APPS = ["django.contrib.staticfiles", "sigda"]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
X_FRAME_OPTIONS = "DENY"
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR.parent / "demo"]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
    }
]
