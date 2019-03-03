# -*- coding: utf-8 -*-
import logging
from ipaddress import IPv4Network

from sipa.backends import DataSource, Dormitory
from sipa.backends.exceptions import InvalidConfiguration
from . import user

logger = logging.getLogger(__name__)


def init_context(app):
    try:
        app.config['SQLALCHEMY_BINDS'].update({
            'hss': app.config['HSS_CONNECTION_STRING']
        })
    except KeyError as exception:
        raise InvalidConfiguration(*exception.args)


#: The HSS datasource
datasource = DataSource(
    name='hss',
    user_class=user.User,
    mail_server="agdsn.me",
    # to be included when it becomes a DataSource
    webmailer_url="https://mail.agdsn.de",
    init_context=init_context,
)

[Dormitory(  # pylint: disable=expression-not-assigned
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

__all__ = ['datasource']
