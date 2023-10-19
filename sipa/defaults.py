DEFAULT_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "medium": {"format": ("%(levelname)s %(asctime)s %(name)s " "%(message)s")},
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "medium",
        },
    },
    "loggers": {
        "sipa": {
            "level": "DEBUG",
            "handlers": ["stdout"],
            "propagate": True,  # Important for `sipa.*` loggers
        },
    },
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
