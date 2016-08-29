from unittest import TestCase
from unittest.mock import MagicMock, patch

from sipa.utils.mail_utils import send_contact_mail


class ContactMailTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.args = {
            'sender': "foo@bar.baz",
            'subject': "test",
            'name': "Paul Dirac",
            'message': "Nö",
            'dormitory_name': 'test',
        }
        self.backends_mock = MagicMock()
        self.dorm_display_name = "Testdormitory (nicht die Wu)"
        self.backends_mock.get_dormitory('test').display_name = self.dorm_display_name
        self.dorm_mail = "support@foo.bar"
        self.backends_mock.get_dormitory('test').datasource.support_mail = self.dorm_mail

        self.send_mail_mock = MagicMock(return_value=True)

        with patch('sipa.utils.mail_utils.send_mail', self.send_mail_mock), \
             patch('sipa.utils.mail_utils.backends', self.backends_mock):
            self.success = send_contact_mail(**self.args)


    def test_success_passed(self):
        self.assertTrue(self.success)

    def test_dormitory_name_in_mail_body(self):
        message = self.send_mail_mock.call_args[0][3]
        self.assertIn(self.dorm_display_name, message)

    def test_sender_name_in_mail_body(self):
        message = self.send_mail_mock.call_args[0][3]
        self.assertIn(self.args['name'], message)

    def test_subject_ends_with_subject(self):
        subject = self.send_mail_mock.call_args[0][2]
        self.assertIn(self.args['subject'], subject)
        self.assertRegex(subject, r"^\[.*?\]")
