SENTRY_REMOTE_URL = 'http://errors.progway.ru/sentry/store/'
SENTRY_SERVERS = ['http://errors.progway.ru/sentry/store/']
SENTRY_KEY = None

LOGGING['handlers']['sentry'] = {
    'level': 'DEBUG',
    'class': 'raven.contrib.django.handlers.SentryHandler',
    'formatter': 'advanced'
}
LOGGING['loggers']['sentry.errors'] = {
    'level': 'DEBUG',
    'handlers': ['sentry', 'default'],
    'propagate': False,
}

#MIDDLEWARE_CLASSES = (
  # We recommend putting this as high in the chain as possible
#  'sentry.client.middleware.SentryResponseErrorIdMiddleware',
#) + MIDDLEWARE_CLASSES
