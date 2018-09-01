# -*- coding: utf-8 -*-

from ipaddress import IPv4Network

from sipa.backends import DataSource, Dormitory
from sipa.backends.exceptions import InvalidConfiguration
from . import user, api


def init_context(app):
    try:
        app.extensions['pycroft_api'] = api.PycroftApi(
            endpoint=app.config['PYCROFT_ENDPOINT'],
            api_key=app.config['PYCROFT_API_KEY'],
        )
    except KeyError as exception:
        raise InvalidConfiguration(*exception.args)


datasource = DataSource(
    name='pycroft',
    user_class=user.User,
    mail_server="wh2.tu-dresden.de",
    support_mail="support@agdsn.de",
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
        ('buda', "Budapester Straße", [
            IPv4Network('141.30.204.0/24'),  # Bu22
            IPv4Network('141.30.205.0/24'),  # Bu24
        ]),
        ('fl', "Fritz-Löffler-Straße", [
            IPv4Network('141.30.28.0/24'),  # FL16
        ]),
        ('gps', "Gret-Palucca-Straße", [
            IPv4Network('141.30.207.0/24'),  # GPS11
        ]),
        ('gerok', "Gerokstraße", [
            IPv4Network('141.76.124.0/24'),  # Ger
        ]),
        ('neu', "Neuberinstraße", [
            IPv4Network('141.30.203.0/26'),  # Neu15
        ]),
    ]
]

__all__ = ['datasource']
