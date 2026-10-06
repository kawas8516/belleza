import sys

from .base import *  # noqa: F403
from .base import env_bool, env_list

DEBUG = env_bool("DEBUG", default=True)

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", default="localhost,127.0.0.1")

# Dev-only fallback so a fresh clone runs without a .env; never used in prod.
SECRET_KEY = SECRET_KEY or "django-insecure-dev-only-key-change-me"  # noqa: F405

# Fast password hashing for `manage.py test` only; real hashers everywhere else.
if len(sys.argv) > 1 and sys.argv[1] == "test":
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
