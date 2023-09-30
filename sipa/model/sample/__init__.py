from ipaddress import IPv4Network

from sipa.backends import DataSource, Dormitory
from sipa.backends.datasource import SubnetCollection
from . import user

#: The sample datasource, used for frontend debugging.
datasource = DataSource(
    name='sample',
    user_class=user.User,
    mail_server="test.agdsn.de",
    init_app=user.init_app,
    dormitories=[
        Dormitory(
            name="localhost",
            display_name="Lokalgastgeber",
            subnets=SubnetCollection(
                [
                    IPv4Network("127.0.0.0/8"),  # loopback
                    IPv4Network("172.0.0.0/8"),  # used by docker
                ]
            ),
        )
    ],
)

__all__ = ['datasource']
