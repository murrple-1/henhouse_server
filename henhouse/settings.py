import datetime
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "APP_SECRET_KEY",
    "PLEASE_OVERRIDE_ME",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("APP_DEBUG", "false").lower() == "true"

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "ninja",
    "corsheaders",
    "silk",
    "app_admin.apps.AppAdminConfig",
    "art.apps.ArtConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",
    "silk.middleware.SilkyMiddleware",
]

ROOT_URLCONF = "henhouse.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "henhouse.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

REDIS_URL = os.getenv("APP_REDIS_URL", "redis://redis:6379")

if os.getenv("APP_IN_DOCKER", "false").lower() == "true":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("APP_DB_NAME", "postgres"),
            "USER": os.getenv("APP_DB_USER", "postgres"),
            "PASSWORD": os.getenv("APP_DB_PASSWORD", "password"),
            "HOST": os.getenv("APP_DB_HOST", "postgresql"),
            "PORT": int(os.getenv("APP_DB_PORT", "5432")),
        }
    }

    SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
    SESSION_CACHE_ALIAS = "default"
else:
    # Basically used in CI test phase or when running tests locally.
    # We don't load redis for that, so avoid setting the cache.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        }
    }

SESSION_COOKIE_SECURE = os.getenv("APP_SESSION_COOKIE_SECURE", "true") == "true"
SESSION_COOKIE_SAMESITE = "None"
SESSION_COOKIE_DOMAIN = os.getenv("APP_SESSION_COOKIE_DOMAIN", "localhost")
SESSION_SAVE_EVERY_REQUEST = True


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 6,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
    {
        "NAME": "app_admin.password_validation.HasLowercaseValidator",
    },
    {
        "NAME": "app_admin.password_validation.HasUppercaseValidator",
    },
    {
        "NAME": "app_admin.password_validation.HasDigitValidator",
    },
    {
        "NAME": "app_admin.password_validation.HasSpecialCharacterValidator",
    },
]

AUTH_USER_MODEL = "app_admin.User"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = os.getenv("TZ", "UTC")

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "_static")

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "app_console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        }
    },
    "loggers": {
        "django": {
            "level": os.getenv("APP_DJANGO_LOG_LEVEL", "INFO"),
        },
        "django.db.backends": {
            "level": os.getenv("APP_DJANGO_DB_BACKEND_LOG_LEVEL", "INFO"),
        },
        "henhouse": {
            "handlers": ["app_console"],
            "level": os.getenv("APP_LOG_LEVEL", "INFO"),
        },
    },
}

if os.getenv("APP_IN_DOCKER", "false").lower() == "true":
    CACHES = {
        "default": {
            "BACKEND": "redis_lock.django_cache.RedisCache",
            "LOCATION": f"{REDIS_URL}/1",
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
            "TIMEOUT": 60 * 5,  # 5 minutes
        },
        "stable_query": {
            "BACKEND": "redis_lock.django_cache.RedisCache",
            "LOCATION": f"{REDIS_URL}/2",
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
            "TIMEOUT": 60 * 60,  # 1 hour
        },
        "captcha": {
            "BACKEND": "redis_lock.django_cache.RedisCache",
            "LOCATION": f"{REDIS_URL}/3",
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
            "TIMEOUT": 60 * 5,  # 5 minutes
        },
        "throttle": {
            "BACKEND": "redis_lock.django_cache.RedisCache",
            "LOCATION": f"{REDIS_URL}/4",
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        },
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "default-cache",
            "TIMEOUT": 60 * 5,  # 5 minutes
        },
        "stable_query": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "stable-query-cache",
            "TIMEOUT": 60 * 60,  # 1 hour
        },
        "captcha": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "captcha-cache",
            "TIMEOUT": 60 * 5,  # 5 minutes
        },
        "throttle": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "throttle-cache",
        },
    }

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "app_admin.auth_backends.EmailBackend",
]

CSRF_TRUSTED_ORIGINS = (
    csrf_trusted_origins.split(",")
    if (csrf_trusted_origins := os.getenv("APP_CSRF_TRUSTED_ORIGINS"))
    else ["http://localhost:4200"]
)
CSRF_COOKIE_SECURE = os.getenv("APP_CSRF_COOKIE_SECURE", "true") == "true"
CSRF_COOKIE_SAMESITE = "None"
CSRF_COOKIE_DOMAIN = os.getenv("APP_CSRF_COOKIE_DOMAIN", "localhost")

if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.getenv("APP_EMAIL_HOST")
    EMAIL_PORT = int(os.getenv("APP_EMAIL_PORT", "587"))
    EMAIL_HOST_USER = os.getenv("APP_EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.getenv("APP_EMAIL_HOST_PASSWORD")
    EMAIL_USE_TLS = os.getenv("APP_EMAIL_USE_TLS", "false").lower() == "true"
    EMAIL_USE_SSL = os.getenv("APP_EMAIL_USE_SSL", "false").lower() == "true"
    EMAIL_TIMEOUT = (
        None if (timeout := os.getenv("APP_EMAIL_TIMEOUT")) is None else float(timeout)
    )

DEFAULT_FROM_EMAIL = os.getenv("APP_DEFAULT_FROM_EMAIL", "webmaster@localhost")

# corsheaders
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ["X-CSRFToken"]

# django-silk
SILKY_AUTHENTICATION = True
SILKY_AUTHORISATION = True
SILKY_MAX_RECORDED_REQUESTS = 10**4
SILKY_MAX_RECORDED_REQUESTS_CHECK_PERCENT = 10
SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_BINARY = True
SILKY_PYTHON_PROFILER_RESULT_PATH = os.path.join(BASE_DIR, "_silk_profiles")
SILKY_PYTHON_PROFILER_EXTENDED_FILE_NAME = True
SILKY_DELETE_PROFILES = True
SILKY_MAX_REQUEST_BODY_SIZE = int(
    os.getenv("APP_SILKY_MAX_REQUEST_BODY_SIZE", "8192")
)  # 8kb
SILKY_MAX_RESPONSE_BODY_SIZE = int(
    os.getenv("APP_SILKY_MAX_RESPONSE_BODY_SIZE", "8192")
)  # 8kb

# app
_test_runner_type = os.getenv("TEST_RUNNER_TYPE", "standard").lower()
if _test_runner_type == "standard":
    pass
elif _test_runner_type == "timed":
    TEST_RUNNER = "henhouse.testrunner.DjangoTimedTestRunner"
    TEST_SLOW_TEST_THRESHOLD = float(os.getenv("TEST_SLOW_TEST_THRESHOLD", "0.5"))
else:
    raise RuntimeError("unknown 'TEST_RUNNER_TYPE'")

TOKEN_EXPIRY_INTERVAL = datetime.timedelta(days=14)

try:
    from .local_settings import *
except ImportError:
    pass
