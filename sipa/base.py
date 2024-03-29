"""
Basic utilities for the Flask app

These are basic utilities necessary for the Flask app which are
disjoint from any blueprint.
"""
import logging

from flask.globals import session
from werkzeug.routing import IntegerConverter as BaseIntegerConverter

from sipa.login_manager import SipaLoginManager
from sipa.backends import backends

logger = logging.getLogger(__name__)

login_manager = SipaLoginManager()
login_manager.login_view = "generic.login"


class IntegerConverter(BaseIntegerConverter):
    """IntegerConverter supporting negative values

    This is a Modification of the standard IntegerConverter which does
    not support negative values.  See the corresponding `werkzeug
    documentation
    <http://werkzeug.pocoo.org/docs/0.10/routing/#werkzeug.routing.IntegerConverter>`_.
    """
    regex = r'-?\d+'


@login_manager.user_loader
def load_user(username):
    """Loads a User object from/into the session at every request
    """
    logger.debug("User loader triggered (%r)", username)
    _cleanup_session(session)
    User = backends.datasource.user_class
    return User.get(username)


def _cleanup_session(session):
    session.pop("dormitory", None)
