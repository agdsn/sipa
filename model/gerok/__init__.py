# -*- coding: utf-8 -*-

from flask.ext.babel import gettext
from ..division import Division
import user

division = Division(
    name='gerok',
    display_name=gettext(u"Gerokstraße"),
    user_class=user.User
)
