from functools import partial

from flask import abort
from tests.prepare import AppInitialized


class TestErrorhandlersCase(AppInitialized):
    used_codes = [401, 403, 404]

    def create_app(self):
        test_app = super().create_app()

        def failing(code):
            abort(code)

        for code in self.used_codes:
            test_app.add_url_rule(
                rule='/aborting-{}'.format(code),
                endpoint='aborting-with-{}'.format(code),
                view_func=partial(failing, code=code),
            )

        return test_app

    def test_error_handler_redirection(self):
        for code in self.used_codes:
            self.client.get('/aborting-{}'.format(code))
            self.assertTemplateUsed('error.html')


class TestCorrectRedirectCase(AppInitialized):
    def test_root_directory_redirect(self):
        response = self.client.get('/')
        self.assertRedirects(response, '/news/')
