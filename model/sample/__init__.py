# -*- coding: utf-8 -*-

from flask.ext.babel import gettext
from ..division import DataSource, Dormitory
from ipaddress import IPv4Network

import user

division = DataSource(
    name='sample',
    display_name=gettext("Beispielsektion"),
    user_class=user.User,
    mail_server=u"test.agdsn.de",
    init_context=user.init_context,
    debug_only=True
)

dormitories = [
    Dormitory(name='localhost', display_name=u"Lokalgastgeber",
              division=division,
              subnets=[
                  IPv4Network(u'127.0.0.0/8'),  # loopback
                  IPv4Network(u'172.17.0.0/16'),  # used by docker
              ]),
]
