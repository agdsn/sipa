# -*- coding: utf-8 -*-

from flask.ext.babel import gettext
from ..division import Division
import user

division = Division(
    name='sample',
    display_name=gettext("Beispielsektion"),
    user_class=user.User,
    debug_only=True
)
