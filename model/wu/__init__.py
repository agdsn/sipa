# -*- coding: utf-8 -*-

from flask.ext.babel import gettext
from ..division import Division, Dormitory
from database_utils import init_db
from ipaddress import IPv4Network

from ldap_utils import init_ldap
import user


def init_context(app):
    init_db(app)
    init_ldap(app)


division = Division(
    name='wu',
    display_name=gettext(u"Wundtstraße & Zellescher Weg"),
    user_class=user.User,
    mail_server=u"wh2.tu-dresden.de",
    subnets=[
        IPv4Network(u'141.30.216.0/24'),  # Wu11
        IPv4Network(u'141.30.222.0/24'),  # Wu1
        IPv4Network(u'141.30.223.0/24'),  # Wu3
        IPv4Network(u'141.30.228.0/24'),  # Wu5
        IPv4Network(u'141.30.224.0/24'),  # Wu7
        IPv4Network(u'141.30.202.0/24'),  # Wu9
        IPv4Network(u'141.30.226.0/23'),  # ZW41*
        IPv4Network(u'141.76.121.0/24'),  # Borsi34
    ],
    init_context=init_context
)

dormitories = [
    Dormitory(name=dorm[0], display_name=dorm[1], division=division)
    for dorm in [
            ('wu', u"Wundtstraße"),
            ('zw', u"Zellescher Weg"),
            ('borsi', u"Borsbergstraße"),
    ]
]
