# -*- coding: utf-8 -*-

from flask.ext.babel import gettext
from ..division import Division
from ipaddress import IPv4Network

import user


def init_context(app):
    app.extensions['gerok_api'] = {
        'endpoint': app.config['GEROK_ENDPOINT'],
        'token': app.config['GEROK_API_TOKEN']
    }


division = Division(
    name='gerok',
    display_name=gettext(u"Gerokstraße"),
    user_class=user.User,
    mail_server=u"wh17.tu-dresden.de",
    subnets=[
        IPv4Network(u'141.76.124.0/24'),  # Gerok38
    ],
    init_context=init_context
)
