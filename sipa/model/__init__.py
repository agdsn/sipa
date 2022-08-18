import logging

from sipa.backends import Backends
from . import sample, pycroft
from .sqlalchemy import db


logger = logging.getLogger(__name__)


#: The implemented datasources available by default
AVAILABLE_DATASOURCES = [
    sample.datasource,
    pycroft.datasource
]


def prepare_sqlalchemy(app):
    app.config['SQLALCHEMY_BINDS'] = {}
    db.init_app(app)


def build_backends_ext() -> Backends:
    backends = Backends()
    for d in AVAILABLE_DATASOURCES:
        backends.register(d)

    # pre_init_hook is designed to be a decorator, so this may look weird.
    backends.pre_init_hook(prepare_sqlalchemy)
    return backends
