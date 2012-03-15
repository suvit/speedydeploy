SENTRY_SERVERS = ['{{sentry_server}}']
SENTRY_KEY = {% if sentry_key %}'{{ sentry_key }}'{% else %}None{% endif %}

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
