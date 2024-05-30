from __future__ import annotations

import logging.config
import os
import platform
import sys
from decimal import Decimal
from pathlib import Path
from typing import NoReturn

error_text = "\033[1;91mError:\033[0m"
warning_text = "\033[1;33mWarning:\033[0m"


def error_exit(code: int, reason: str) -> NoReturn:
    print(f"{error_text} {reason}", flush=True)
    os._exit(code)


# --- General settings ---

# The directory where everything lives in.
user_set_working_dir = os.environ.get("SHILA_LAGER_WORKING_DIR")
working_dir_location = Path(user_set_working_dir).expanduser() if user_set_working_dir is not None else Path(os.path.expanduser("~"), "shila-lager")

manual_upload_dir = working_dir_location / "manual-uploads"
plot_output_dir = working_dir_location / "plots"

# A constant to detect if you are on Linux.
is_linux = platform.system() == "Linux"

# A constant to detect if you are on macOS.
is_macos = platform.system() == "Darwin"

# A constant to detect if you are on Windows.
is_windows = platform.system() == "Windows"

# -/- General settings ---


# --- Test Settings ---


# Yes, changing behaviour when testing is evil.
is_testing = "pytest" in sys.modules
if is_testing:
    pass


# -/- Test Settings ---


# --- Database Configuration ---

def _make_db_name(db_name: str) -> str:
    return "test_" + db_name if is_testing else db_name


def db_make_sqlite_url(db_name: str) -> str:
    return f"sqlite:///{os.path.join(working_dir_location, _make_db_name(db_name))}"


def db_make_mariadb_url(user: str, pw: str, db_name: str) -> str:
    return f"mariadb+mariadbconnector://{user}:{pw}@localhost:3306/{_make_db_name(db_name)}"


def db_make_postgres_url(user: str, pw: str, db_name: str) -> str:
    return f"postgresql+psycopg2://{user}:{pw}@localhost:5432/{_make_db_name(db_name)}"


# First, the database url is tried. If it doesn"t work, the `sqlite_database_name` together with the working dir is tried. If both error, the program is halted.
sqlite_database_name = "state.db"
database_url = db_make_sqlite_url(sqlite_database_name)

# If set to True all emitted SQL is echo"d back
database_verbose_sql = False

# -/- Database Configuration ---

# --- Django Configuration ---

# Build paths inside the project like this: BASE_DIR / "subdir".
BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DIR = BASE_DIR / "shila_lager"
FRONTEND_DIR = SOURCE_DIR / "frontend"
APP_DIR = FRONTEND_DIR / "apps"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!  TODO: Log an error if no secret key is provided
SECRET_KEY = os.environ.get("SHILA_LAGER_SECRET_KEY") or "django-insecure-w9n&-4vb#dkay9*856z6b$@k(f+j82-ayp^_xj5-qkt9cnfv7d"

# SECURITY WARNING: don"t run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = os.environ.get("SHILA_LAGER_SERVER_NAMES", "").split(" ")

# Application definition

INSTALLED_APPS = [
    "shila_lager.frontend.apps.bestellung.apps.LagerConfig",
    "shila_lager.frontend.apps.einzahlungen.apps.EinzahlungenConfig",
    "shila_lager.frontend.apps.rechnungen.apps.RechnungenConfig",
    "shila_lager.frontend.apps.stats.apps.StatsConfig",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "shila_lager.frontend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [FRONTEND_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "shila_lager.frontend.wsgi.application"

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": working_dir_location / "state.db",
    }
}

# Storage
# https://docs.djangoproject.com/en/5.0/ref/settings/#storages
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": working_dir_location / "uploads",
            "base_url": "/uploads/",
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATICFILES_DIRS = [FRONTEND_DIR / "static"]
STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -/- Django Configuration -/-

# --- Logging Configuration ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },

    "loggers": {
        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "shila-lager": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

logging.config.dictConfig(LOGGING)
logger = logging.getLogger("shila-lager")

# --- Grihed Options ---

empty_crate_price = Decimal(1.5)
