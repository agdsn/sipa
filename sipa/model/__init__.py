import logging

from sipa.backends import Backends
from . import sample, pycroft


logger = logging.getLogger(__name__)


#: The implemented datasources available by default
AVAILABLE_DATASOURCES = [
    sample.datasource,
    pycroft.datasource
]


def build_backends_ext() -> Backends:
    backends = Backends()
    for d in AVAILABLE_DATASOURCES:
        backends.register(d)

    # pre_init_hook is designed to be a decorator, so this may look weird.
    return backends
