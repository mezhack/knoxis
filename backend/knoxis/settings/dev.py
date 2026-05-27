import os

from dotenv import load_dotenv

from .base import *  # noqa: F403

load_dotenv()

DEBUG = True

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-not-for-production-use")

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "knoxis"),
        "USER": os.environ.get("POSTGRES_USER", "knoxis"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "knoxis"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

CPF_HMAC_KEY = os.environ.get("CPF_HMAC_KEY", "dev-hmac-key-not-for-production")

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 0.5
