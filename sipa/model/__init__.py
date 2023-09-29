import logging

from sipa.backends import Backends
from . import sample, pycroft


logger = logging.getLogger(__name__)


#: The implemented datasources available by default
AVAILABLE_DATASOURCES = [
    sample.datasource,
    pycroft.datasource
]
