# -*- coding: utf-8 -*-

from flask.ext.babel import gettext
from ..datasource import DataSource, Dormitory
from database_utils import init_db
from ldap_utils import init_ldap
from ipaddress import IPv4Network
import user


def init_context(app):
    init_db(app)
    init_ldap(app)


datasource = DataSource(
    name='hss',
    display_name=gettext(u"Hochschulstraße"),
    user_class=user.User,
    mail_server=u"wh12.tu-dresden.de",
    init_context=init_context,
    debug_only=True
)


dormitories = [
    Dormitory(name='hss', display_name=u"Hochschulstraße", datasource=datasource,
              subnets=[
                  IPv4Network(u'141.30.217.0/24'),  # HSS 46
                  IPv4Network(u'141.30.234.0/25'),  # HSS 46
                  IPv4Network(u'141.30.218.0/24'),  # HSS 48
                  IPv4Network(u'141.30.215.128/25'),  # HSS 48
                  IPv4Network(u'141.30.219.0/24'),  # HSS 50
              ])
]
