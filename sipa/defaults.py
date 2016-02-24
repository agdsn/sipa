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
            # None will be replaced by the locally defined callable.
            # (see sipa.initialization.init_logging)
            '()': None,
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

WARNINGS_ONLY_CONFIG = {
    'version': 1,
    'incremental': True,
    'loggers': {
        'sipa': {
            'level': 'WARNING',
        },

    }
}
