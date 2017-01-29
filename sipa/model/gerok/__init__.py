# -*- coding: utf-8 -*-

from ipaddress import IPv4Network

from ..datasource import DataSource, Dormitory
from . import user
from sipa.model.exceptions import InvalidConfiguration


def init_context(app):
    try:
        app.extensions['gerok_api'] = {
            'endpoint': app.config['GEROK_ENDPOINT'],
            'token': app.config['GEROK_API_TOKEN']
        }
    except KeyError as exception:
        raise InvalidConfiguration(*exception.args)


datasource = DataSource(
    name='gerok',
    user_class=user.User,
    mail_server="wh17.tu-dresden.de",
    webmailer_url="https://wh17.tu-dresden.de/webmail/",
    init_context=init_context
)

Dormitory(name='gerok', display_name="Gerokstraße",
          datasource=datasource, subnets=[IPv4Network('141.76.124.0/24')])


__all__ = ['datasource']
