"""
Production settings for ocean project.
"""

import os

from ocean.settings.dev import *



SECRET_KEY = os.environ["OCEAN_SECRET_KEY"]

DEBUG = False

ALLOWED_HOSTS = os.environ["OCEAN_ALLOWED_HOSTS"].split(" ")
CORS_ORIGIN_WHITELIST = os.environ["OCEAN_CORS_OROGIN_WHITELIST"].split(" ")
CSRF_TRUSTED_ORIGINS = os.environ["OCEAN_CSRF_TRUSTED_ORIGINS"].split(" ")

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["OCEAN_DB_NAME"],
        "USER": os.environ["OCEAN_DB_USER"],
        "PASSWORD": os.environ["OCEAN_DB_PASSWORD"],
        "HOST": os.environ["OCEAN_DB_HOST"],
        "PORT": os.environ["OCEAN_DB_PORT"],
    }
}

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
