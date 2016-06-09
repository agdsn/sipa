from unittest import TestCase

from flask.ext.login import AnonymousUserMixin

from sipa.model.hss.user import User


class HssUserGetTestCase(TestCase):
    def test_user_get_uses_database(self):
        self.assertIsInstance(User.get('test'), AnonymousUserMixin)
