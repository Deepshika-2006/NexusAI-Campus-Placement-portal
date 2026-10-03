
import os
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# BASE CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env
load_dotenv(BASE_DIR / ".env")


# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "NexusAI-local-development-key-2026-9f3d7a1c5b8e2-RANDOM-CHANGE-ME",
)

DEBUG = os.getenv("DEBUG", "False").lower() == "true"


# ============================================================
# OPENAI / AI CONFIGURATION
# ============================================================

# Keep the real API key inside .env.
# Never hard-code your API key inside Python files.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


# ============================================================
# ALLOWED HOSTS
# ============================================================

allowed_hosts = os.getenv(
    "ALLOWED_HOSTS",
    "127.0.0.1,localhost",
).split(",")

ALLOWED_HOSTS = [
    host.strip()
    for host in allowed_hosts
    if host.strip()
]


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",

    "core",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]


# WhiteNoise for serving static files
try:
    import whitenoise  # noqa: F401

    MIDDLEWARE.insert(
        1,
        "whitenoise.middleware.WhiteNoiseMiddleware",
    )
except ImportError:
    pass


# ============================================================
# URL CONFIGURATION
# ============================================================

ROOT_URLCONF = "nexus.urls"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "templates",
        ],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ============================================================
# WSGI
# ============================================================

WSGI_APPLICATION = "nexus.wsgi.application"


# ============================================================
# DATABASE
# ============================================================

DB_ENGINE = os.getenv(
    "DB_ENGINE",
    "django.db.backends.mysql",
)


# ------------------------------------------------------------
# SQLite option
# ------------------------------------------------------------

if DB_ENGINE == "django.db.backends.sqlite3":

    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": BASE_DIR / os.getenv(
                "DB_NAME",
                "db.sqlite3",
            ),
        }
    }


# ------------------------------------------------------------
# MySQL option
# ------------------------------------------------------------

else:

    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,

            "NAME": os.getenv(
                "DB_NAME",
                "nexusai",
            ),

            "USER": os.getenv(
                "DB_USER",
                "root",
            ),

            "PASSWORD": os.getenv(
                "DB_PASSWORD",
                "",
            ),

            "HOST": os.getenv(
                "DB_HOST",
                "127.0.0.1",
            ),

            "PORT": os.getenv(
                "DB_PORT",
                "3306",
            ),

            "OPTIONS": {
                "charset": "utf8mb4",
            },
        }
    }


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },

    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
        "OPTIONS": {
            "min_length": 6,
        },
    },
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = "/css/"

STATICFILES_DIRS = [
    BASE_DIR / "static" / "css",
]

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)


# ============================================================
# MEDIA / UPLOADED FILES
# ============================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================================================
# LOGIN / LOGOUT
# ============================================================

LOGIN_URL = "/login/"

LOGIN_REDIRECT_URL = "/student-dashboard/"

LOGOUT_REDIRECT_URL = "/"


# ============================================================
# CSRF
# ============================================================

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CSRF_TRUSTED_ORIGINS",
        "",
    ).split(",")
    if origin.strip()
]


# ============================================================
# PROXY / HTTPS
# ============================================================

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# ============================================================
# PRODUCTION SECURITY
# ============================================================

if not DEBUG:

    SECURE_SSL_REDIRECT = True

    SECURE_HSTS_SECONDS = 31536000

    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

    SECURE_HSTS_PRELOAD = True

    SESSION_COOKIE_SECURE = True

    CSRF_COOKIE_SECURE = True

    SECURE_CONTENT_TYPE_NOSNIFF = True

    SECURE_REFERRER_POLICY = (
        "strict-origin-when-cross-origin"
    )
