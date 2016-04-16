# -*- coding: utf-8 -*-

from ipaddress import IPv4Network

from ..datasource import DataSource, Dormitory
from . import user


def init_context(self):
    pass


datasource = DataSource(
    name='hss',
    user_class=user.User,
    # website_url="https://wh12.tu-dresden.de",
    mail_server="wh2.tu-dresden.de",
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
