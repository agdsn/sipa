# -*- coding: utf-8 -*-

from flask.ext.babel import gettext
from ..division import Division
from database_utils import init_db
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
    init_context=init_context
)
