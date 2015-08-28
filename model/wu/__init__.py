# -*- coding: utf-8 -*-

from flask.ext.babel import gettext
from ..division import Division
import user

division = Division(
    name='wu',
    display_name=gettext(u"Wundtstraße & Zellescher Weg"),
    user_class=user.User,
    init_context=user.init_context
)
