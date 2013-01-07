import os

LOG_DIRNAME = locals().get('LOG_DIRNAME', '{{remote_dir}}/log/')
LOG_FILENAME = locals().get('LOG_FILENAME', 'main.log')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'simple': {
            'format': '%(levelname)s - %(message)s'
        },
        'advanced':{
            'format': '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
        },
        'verbose': {
            'format': '%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(process)d - %(thread)d - %(message)s'
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
            'filename': os.path.join(LOG_DIRNAME, LOG_FILENAME),
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
