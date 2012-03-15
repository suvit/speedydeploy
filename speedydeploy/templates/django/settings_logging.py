import os

LOG_DIRNAME = locals().get('LOG_DIRNAME', '{{remote_dir}}/log/')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(process)d - %(thread)d - %(message)s'
        },
        'simple': {
            'format': '%(levelname)s - %(message)s'
        },
        'advanced':{
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },
        'default':{
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIRNAME, 'shop.log'),
            'formatter': 'advanced',
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'advanced'
        },
        'watch': {
            'level':'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIRNAME, 'watch.log'),
            'formatter': 'advanced',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True
        },
        'console': {
            'handlers':['console'],
            'level':'INFO',
            'propagate': True,
        },
        'root': {
            'handlers':['console'],
            'level':'INFO',
            'propagate': True,
        },
    },
}
