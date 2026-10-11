"""
Django settings for the HolyCross Hospital Management project.

All secrets and deployment-specific values come from environment variables
(see .env.example). Sensible defaults keep local development zero-config.
"""
import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# Load a local .env file if present (development convenience, never committed).
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

ON_VERCEL = bool(os.environ.get("VERCEL"))

DEBUG = env_bool("DJANGO_DEBUG", default=not ON_VERCEL)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG and not ON_VERCEL:
        raise RuntimeError("DJANGO_SECRET_KEY must be set when DEBUG is off.")
    # Development / preview fallback only. Set DJANGO_SECRET_KEY in production.
    SECRET_KEY = "dev-insecure-holycross-change-me"

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,.vercel.app")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "https://*.vercel.app")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "Backend",
    "Frontend",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "HospitalManagement.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "Frontend.context_processors.hospital",
            ],
        },
    },
]

WSGI_APPLICATION = "HospitalManagement.wsgi.application"

# Database
# DATABASE_URL (e.g. Neon / Vercel Postgres) is used when set. Otherwise SQLite:
# the project file locally, or a self-seeding demo copy in /tmp on Vercel
# (Vercel's filesystem is read-only and resets between cold starts).
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
if DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=0, ssl_require=ON_VERCEL)}
elif ON_VERCEL:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "/tmp/holycross.sqlite3"}}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

DEMO_DATABASE = ON_VERCEL and not DATABASE_URL
if DEMO_DATABASE:
    # Each serverless instance has its own throwaway database, so keep sessions in signed cookies.
    SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "loginfr"
LOGIN_REDIRECT_URL = "index"

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ.get("DJANGO_TIME_ZONE", "Asia/Kolkata")
USE_I18N = True
USE_TZ = True

# Static files are served by WhiteNoise straight from the app static folders,
# so no collectstatic build step is needed on Vercel.
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG
WHITENOISE_MAX_AGE = 0 if DEBUG else 60 * 60 * 24

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
# Uploads on Vercel land in /tmp (ephemeral). Use object storage for production uploads.
UPLOAD_ROOT = Path("/tmp/media") if ON_VERCEL else MEDIA_ROOT

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": UPLOAD_ROOT, "base_url": MEDIA_URL},
    },
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024

# Email (optional). Without SMTP credentials, messages are only stored in the
# dashboard inbox and printed to the console.
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = True
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "noreply@holycross.example")
CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", EMAIL_HOST_USER)

# Video consultation (ZegoCloud UIKit). Leave unset to disable the feature.
ZEGO_APP_ID = os.environ.get("ZEGO_APP_ID", "")
ZEGO_SERVER_SECRET = os.environ.get("ZEGO_SERVER_SECRET", "")

# Public hospital details shown across the site.
HOSPITAL = {
    "name": os.environ.get("HOSPITAL_NAME", "HolyCross Hospital"),
    "phone": os.environ.get("HOSPITAL_PHONE", "+91 85905 69016"),
    "emergency": os.environ.get("HOSPITAL_EMERGENCY", "+91 85905 69016"),
    "email": os.environ.get("HOSPITAL_EMAIL", "care@holycross.example"),
    "address": os.environ.get("HOSPITAL_ADDRESS", "HolyCross Hospital, Kochi, Kerala, India"),
}

# Production hardening
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
