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
    },
    'loggers': {
        'root': {
            'level': 'DEBUG',
            'handlers': ['stdout'],
        },
        'sipa': {
            'level': 'DEBUG',
            'handlers': ['stdout'],
            'propagate': True,  # Important for `sipa.*` loggers
        },
    }
}

WARNINGS_ONLY_CONFIG = {
    'version': 1,
    'incremental': True,
    'loggers': {
        'sipa': {
            'level': 'WARNING',
        },
        'factory': {
            'level': 'WARNING',
        },
    }
}
