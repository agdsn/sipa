from flask import request as flask_request
from flask.sessions import SecureCookieSessionInterface


class SeparateLocaleCookieSessionInterface(SecureCookieSessionInterface):
    """
    Store a user's locale preference in a separate, unencrypted cookie.
    """
    def _copy_session(self, session, data):
        """
        Create a copy of a given session with different data.
        """
        new_session = self.session_class(data)
        new_session.new = session.new
        new_session.modified = session.modified
        return new_session

    def open_session(self, app, request):
        session = super().open_session(app, request)
        locale = request.cookies.get(app.config['LOCALE_COOKIE_NAME'])
        if not locale:
            return session

        data = dict(session, locale=locale)
        new_session = self._copy_session(session, data)
        return new_session

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        missing = object()
        locale = session.get('locale', missing)

        if locale is missing and 'locale' in flask_request.cookies:
            # Delete the cookie
            response.delete_cookie(app.config['LOCALE_COOKIE_NAME'],
                                   domain=domain, path=path)

        # Remove the locale from the session object, a new session object is
        # created to interfere with modification detection
        data = dict(session)
        data.pop('locale', None)
        new_session = self._copy_session(session, data)
        super().save_session(app, new_session, response)

        if locale is missing or not self.should_set_cookie(app, session):
            return

        expires = self.get_expiration_time(app, session)
        response.set_cookie(app.config['LOCALE_COOKIE_NAME'], locale,
                            expires=expires, httponly=False, secure=False,
                            max_age=app.config['LOCALE_COOKIE_MAX_AGE'],
                            domain=domain, path=path)
