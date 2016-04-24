# -*- coding: utf-8 -*-
import logging
from ipaddress import IPv4Network

from ..datasource import DataSource, Dormitory
from . import user

logger = logging.getLogger(__name__)


def init_context(app):
    if 'HSS_CONNECTION_STRING' not in app.config:
        logger.debug('HSS_CONNECTION_STRING not set. Skipping.')
        return

    app.config['SQLALCHEMY_BINDS'].update({
        'hss': app.config['HSS_CONNECTION_STRING']
    })


datasource = DataSource(
    name='hss',
    user_class=user.User,
    mail_server="wh12.tu-dresden.de",
    # to be included when it becomes a DataSource
    webmailer_url="https://wh12.tu-dresden.de/roundcube/",
    init_context=init_context,
    # support_mail="support@wh12.tu-dresden.de",
)

dormitories = [Dormitory(
    name='hss',
    display_name="Hochschulstraße",
    datasource=datasource,
    subnets=[
        IPv4Network('141.30.217.0/24'),
        IPv4Network('141.30.234.0/25'),
        IPv4Network('141.30.218.0/24'),
        IPv4Network('141.30.215.128/25'),
        IPv4Network('141.30.219.0/24'),
        IPv4Network('141.30.234.224/27'),
    ]
)]
