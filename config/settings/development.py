from .base import *

DEBUG = True

# Desabilitar cache em desenvolvimento
WHITENOISE_MAX_AGE = 0

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Em dev, desabilitar whitenoise manifest para evitar erros
STORAGES = {
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

CORS_ALLOW_ALL_ORIGINS = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging de queries SQL em dev (descomentar para debug)
# LOGGING = {
#     'version': 1,
#     'handlers': {'console': {'class': 'logging.StreamHandler'}},
#     'loggers': {
#         'django.db.backends': {'level': 'DEBUG', 'handlers': ['console']},
#     },
# }
