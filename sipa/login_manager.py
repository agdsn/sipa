from functools import wraps

from flask import request, Blueprint
from flask_babel import gettext
from flask_login import LoginManager


class SipaLoginManager(LoginManager):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.localize_callback = gettext
        self.login_message = "Bitte melde Dich an, um die Seite zu sehen."
        self.ignored_endpoints = set()
        self._wrapped_user_callback = None

    def ignore_endpoint(self, endpoint_name):
        self.ignored_endpoints.add(endpoint_name)

    def disable_user_loading(self, bp=None):
        """The decorator version of :py:meth:`ignore_endpoint`

        Use as `@login_manager.disable_user_loading()` or
        `@login_manager.disable_user_loading(bp)`.
        """
        if bp is None:
            def endpoint_name(f):
                return f.__name__
        else:
            if not isinstance(bp, Blueprint):
                raise TypeError("Must call `disable_user_loading`"
                                " with instance of `Blueprint`")

            def endpoint_name(f):
                return f"{bp.name}.{f.__name__}"

        def decorate(f):
            self.ignore_endpoint(endpoint_name(f))
            return f
        return decorate

    @property
    def _user_callback(self):
        return self._wrapped_user_callback

    @_user_callback.setter
    def _user_callback(self, f):
        @wraps(f)
        def wrapped_user_callback(user_id):
            if request.endpoint in self.ignored_endpoints:
                return self.anonymous_user()
            return f(user_id)

        self._wrapped_user_callback = wrapped_user_callback
