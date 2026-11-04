"""Isolated local browser-test database. Never use these settings for deployment."""
from .settings import *  # noqa: F403

DEBUG = True
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "e2e.sqlite3"}}
FRONTEND_URL = "http://localhost:5174"
CSRF_TRUSTED_ORIGINS = ["http://localhost:5174", "http://127.0.0.1:5174"]
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
VISION_SERVICE_URL = "http://127.0.0.1:8003"
VISION_API_KEY = "e2e-internal-only"
MEDIA_ROOT = BASE_DIR.parent / "tmp" / "e2e-media"
