# -*- coding: utf-8 -*-

from ipaddress import IPv4Network

from ..datasource import DataSource, Dormitory
from .database_utils import init_db
from .ldap_utils import init_ldap
from . import user


def init_context(app):
    init_db(app)
    init_ldap(app)


datasource = DataSource(
    name='wu',
    user_class=user.User,
    mail_server="wh2.tu-dresden.de",
    webmailer_url="https://www.wh2.tu-dresden.de/webmail/",
    init_context=init_context
)

[  # pylint: disable=expression-not-assigned
    Dormitory(name=dorm[0], display_name=dorm[1], datasource=datasource,
              subnets=dorm[2])
    for dorm in [
        ('wu', "Wundtstraße", [
            IPv4Network('141.30.216.0/24'),  # Wu11
            IPv4Network('141.30.222.0/24'),  # Wu1
            IPv4Network('141.30.223.0/24'),  # Wu3
            IPv4Network('141.30.228.0/24'),  # Wu5
            IPv4Network('141.30.224.0/24'),  # Wu7
            IPv4Network('141.30.202.0/24'),  # Wu9
        ]),
        ('zw', "Zellescher Weg", [
            IPv4Network('141.30.226.0/23'),  # ZW41*
        ]),
        ('borsi', "Borsbergstraße", [
            IPv4Network('141.76.121.0/24'),  # Borsi34
        ]),
        ('zeu', "Zeunerstraße", [
            IPv4Network('141.30.234.128/26'),  # Zeu1f
            IPv4Network('141.30.234.192/27'),  # Zeu1f
        ]),
    ]
]

__all__ = ['datasource']
