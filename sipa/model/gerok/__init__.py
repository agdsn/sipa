# -*- coding: utf-8 -*-

from ipaddress import IPv4Network

from ..datasource import DataSource, Dormitory
from . import user


def init_context(app):
    app.extensions['gerok_api'] = {
        'endpoint': app.config['GEROK_ENDPOINT'],
        'token': app.config['GEROK_API_TOKEN']
    }


datasource = DataSource(
    name='gerok',
    user_class=user.User,
    mail_server="wh17.tu-dresden.de",
    support_mail="gerok@wh17.tu-dresden.de",
    init_context=init_context
)

dormitories = [
    Dormitory(name='gerok', display_name="Gerokstraße",
              datasource=datasource, subnets=[IPv4Network('141.76.124.0/24')])
]
