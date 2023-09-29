from ipaddress import IPv4Network

from sipa.backends import DataSource, Dormitory
from sipa.backends.exceptions import InvalidConfiguration
from sipa.backends.datasource import SubnetCollection
from . import user, api, userdb


def init_pycroft_api(app):
    try:
        app.extensions['pycroft_api'] = api.PycroftApi(
            endpoint=app.config['PYCROFT_ENDPOINT'],
            api_key=app.config['PYCROFT_API_KEY'],
        )
    except KeyError as exception:
        raise InvalidConfiguration(*exception.args) from exception


def init_userdb(app):
    userdb.register_userdb_extension(app)


def init_context(app):
    init_pycroft_api(app)
    init_userdb(app)


datasource = DataSource(
    name='pycroft',
    user_class=user.User,
    mail_server="agdsn.me",
    support_mail="support@agdsn.de",
    webmailer_url="https://mail.agdsn.de",
    init_context=init_context,
    dormitories=[
        Dormitory(
            name=name,
            display_name=display_name,
            subnets=SubnetCollection(subnets),
        )
        for name, display_name, subnets in [
            (
                "wu",
                "Wundtstraße",
                [
                    IPv4Network("141.30.216.0/24"),  # Wu11
                    IPv4Network("141.30.222.0/24"),  # Wu1
                    IPv4Network("141.30.223.0/24"),  # Wu3
                    IPv4Network("141.30.228.0/24"),  # Wu5
                    IPv4Network("141.30.224.0/24"),  # Wu7
                    IPv4Network("141.30.202.0/24"),  # Wu9
                ],
            ),
            (
                "zw",
                "Zellescher Weg",
                [
                    IPv4Network("141.30.226.0/23"),  # ZW41*
                ],
            ),
            (
                "borsi",
                "Borsbergstraße",
                [
                    IPv4Network("141.76.121.0/24"),  # Borsi34
                ],
            ),
            (
                "zeu",
                "Zeunerstraße",
                [
                    IPv4Network("141.30.234.128/26"),  # Zeu1f
                    IPv4Network("141.30.234.192/27"),  # Zeu1f
                ],
            ),
            (
                "buda",
                "Budapester Straße",
                [
                    IPv4Network("141.30.204.0/24"),  # Bu22
                    IPv4Network("141.30.205.0/24"),  # Bu24
                ],
            ),
            (
                "fl",
                "Fritz-Löffler-Straße",
                [
                    IPv4Network("141.30.28.0/24"),  # FL16
                    IPv4Network("141.30.220.0/24"),  # FL12
                    IPv4Network("141.30.229.0/24"),  # FL12
                    IPv4Network("141.30.230.0/24"),  # FL12
                ],
            ),
            (
                "gps",
                "Gret-Palucca-Straße",
                [
                    IPv4Network("141.30.207.0/24"),  # GPS11
                ],
            ),
            (
                "gerok",
                "Gerokstraße",
                [
                    IPv4Network("141.76.124.0/24"),  # Ger
                ],
            ),
            (
                "neu",
                "Neuberinstraße",
                [
                    IPv4Network("141.30.203.0/26"),  # Neu15
                ],
            ),
            (
                "rei",
                "Reichenbachstraße",
                [
                    IPv4Network("141.30.211.0/24"),  # Rei35
                ],
            ),
            (
                "gu",
                "Gutzkowstraße",
                [
                    IPv4Network("141.30.212.0/24"),  # Gu29a
                    IPv4Network("141.30.213.0/24"),  # Gu29b
                ],
            ),
            (
                "hoy",
                "Hoyerswerdaer Straße",
                [
                    IPv4Network("141.76.119.0/25"),  # Hoy10
                ],
            ),
            (
                "mar",
                "Marschnerstraße",
                [
                    IPv4Network("141.30.221.0/24"),  # Mar31
                ],
            ),
            (
                "gue",
                "Güntzstraße",
                [
                    IPv4Network("141.30.225.0/24"),  # Gue29
                ],
            ),
            (
                "hss",
                "Hochschulstraße",
                [
                    IPv4Network("141.30.217.0/24"),
                    IPv4Network("141.30.234.0/25"),
                    IPv4Network("141.30.218.0/24"),
                    IPv4Network("141.30.215.128/25"),
                    IPv4Network("141.30.219.0/24"),
                    IPv4Network("141.30.234.224/27"),
                ],
            ),
            (
                "bla",
                "Blasewitzer Straße",
                [
                    IPv4Network("141.30.29.0/24"),  # Bla84
                ],
            ),
            (
                "spb",
                "St.-Petersburger-Straße",
                [
                    IPv4Network("141.30.208.0/24"),
                    IPv4Network("141.30.210.0/24"),
                    IPv4Network("141.30.214.0/24"),
                ],
            ),
        ]
    ],
)

__all__ = ['datasource']
