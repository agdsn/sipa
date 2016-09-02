from ..datasource import DataSource


def _do_nothing(*app):
    pass


datasource = DataSource(
    name='pycroft',
    user_class=object,
    mail_server="",
    webmailer_url="",
    init_context=_do_nothing,
)
