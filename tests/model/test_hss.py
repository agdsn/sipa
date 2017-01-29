import logging
from unittest import TestCase

from flask_login import AnonymousUserMixin

from sipa.model.hss.user import User
from tests.base import disable_logs


class HssUserGetTestCase(TestCase):
    def test_user_get_uses_database(self):
        # A warning about a RuntimeError is thrown due to the
        # missing app context
        with disable_logs(logging.WARNING):
            self.assertIsInstance(User.get('test'), AnonymousUserMixin)
