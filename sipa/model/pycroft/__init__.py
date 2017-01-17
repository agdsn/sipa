from ..datasource import DataSource
from .user import User


def _do_nothing(*app):
    pass


datasource = DataSource(
    name='pycroft',
    user_class=User,
    mail_server="",
    webmailer_url="",
    init_context=_do_nothing,
)
