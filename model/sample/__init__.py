# -*- coding: utf-8 -*-

from flask.ext.babel import gettext
from ..division import Division
import user

division = Division(
    name='sample',
    display_name=gettext("Beispielsektion"),
    user_class=user.User,
    mail_server=u"test.agdsn.de",
    init_context=user.init_context,
    debug_only=True
)
