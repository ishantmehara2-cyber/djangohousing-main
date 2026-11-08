from .base import *
from django.core.exceptions import ImproperlyConfigured

DEBUG = False

if SECRET_KEY == 'django-insecure-housing-clone-secret-key' or not SECRET_KEY:
    raise ImproperlyConfigured("PRODUCTION ERROR: SECRET_KEY must be set to a secure unique random string in production.")

if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['localhost', '127.0.0.1', '0.0.0.0']:
    raise ImproperlyConfigured("PRODUCTION ERROR: ALLOWED_HOSTS must be explicitly configured for production.")

CSRF_TRUSTED_ORIGINS = [
    "https://housing.ainextech.in",
]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() in ('true', '1', 't')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'

# Production Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
