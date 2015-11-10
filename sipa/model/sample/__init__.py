# -*- coding: utf-8 -*-

from ipaddress import IPv4Network

from flask.ext.babel import lazy_gettext

from ..datasource import DataSource, Dormitory
from . import user

datasource = DataSource(
    name='sample',
    display_name=lazy_gettext("Beispielsektion"),
    user_class=user.User,
    mail_server="test.agdsn.de",
    init_context=user.init_context,
    debug_only=True
)

dormitories = [
    Dormitory(name='localhost', display_name="Lokalgastgeber",
              datasource=datasource,
              subnets=[
                  IPv4Network('127.0.0.0/8'),  # loopback
                  IPv4Network('172.17.0.0/16'),  # used by docker
              ]),
]
