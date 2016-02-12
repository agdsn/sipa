# -*- coding: utf-8; -*-

DEFAULT_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': ("%(levelname)s %(asctime)s %(module)s "
                       "%(process)d %(thread)d %(message)s")
        },
        'medium': {
            'format': ("%(levelname)s %(asctime)s %(module)s "
                       "%(message)s")
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'stdout': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'verbose',
        },
        'sentry': {
            'class': 'raven.handlers.logging.SentryHandler',
            'level': 'NOTSET',
            'formatter': 'medium',
        },
    },
    'loggers': {
        'root': {
            'level': 'DEBUG',
            'handlers': ['stdout'],
        },
        'sipa': {
            'level': 'DEBUG',
            'handlers': ['stdout', 'sentry'],
            'propagate': True,  # Important for `sipa.*` loggers
        },
    }
}
