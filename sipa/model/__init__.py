import logging

from sipa.backends import Backends
from . import pycroft


logger = logging.getLogger(__name__)


#: The implemented datasources available by default
AVAILABLE_DATASOURCES = [
    pycroft.datasource
]
