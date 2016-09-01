from unittest import TestCase
from unittest.mock import MagicMock, patch

from sipa.mail import send_contact_mail, send_complex_mail, \
    compose_subject, compose_body


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

        with patch('sipa.mail.send_mail', self.send_mail_mock), \
                patch('sipa.mail.backends', self.backends_mock):
            self.success = send_contact_mail(**self.args)

    def test_success_passed(self):
        self.assertTrue(self.success)

    def test_dormitory_name_in_mail_body(self):
        message = self.send_mail_mock.call_args[1]['message']
        self.assertIn(self.dorm_display_name, message)

    def test_sender_name_in_mail_body(self):
        message = self.send_mail_mock.call_args[1]['message']
        self.assertIn(self.args['name'], message)

    def test_subject_ends_with_subject(self):
        subject = self.send_mail_mock.call_args[1]['subject']
        self.assertIn(self.args['subject'], subject)
        self.assertRegex(subject, r"^\[.*?\]")


class ComplexMailContentTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.args = {
            'sender': "foo@bar.baz",
            'subject': "test",
            'message': "Dies ist eine Testnachricht.",
            'tag': "Testtag",
            'category': 'Kategorie mit einer nichtleeren Menge an Morphismen',
            'header': {'foo': "Bar", 'alkohol': "Na Klar!"},
        }
        self.send_mail_mock = MagicMock(return_value=True)

        with patch('sipa.mail.send_mail', self.send_mail_mock):
            self.success = send_complex_mail(**self.args)

    def test_success_pased(self):
        self.assertTrue(self.success)

    def test_keyword_args_used(self):
        self.assertFalse(self.send_mail_mock.call_args[0])

    def test_subject_complete_passed(self):
        subject_passed = self.send_mail_mock.call_args[1]['subject']

        self.assertIn(self.args['subject'], subject_passed)
        self.assertIn(self.args['tag'], subject_passed)
        self.assertIn(self.args['category'], subject_passed)

    def test_message_complete_passed(self):
        message_passed = self.send_mail_mock.call_args[1]['message']

        self.assertIn(self.args['message'], message_passed)

        for key, value in self.args['header'].items():
            self.assertIn(key, message_passed)
            self.assertIn(value, message_passed)


class ComplexMailArgumentsTestCase(TestCase):
    def test_fails_on_missing_argument(self):
        """Test send_complex_mail needs all of the required arguments"""
        required_args = ['sender', 'recipient', 'subject', 'message']

        for blacklist_arg in required_args:
            kwargs = {arg: MagicMock() for arg in required_args
                      if arg != blacklist_arg}
            with self.assertRaises(TypeError):
                send_complex_mail(**kwargs)


class ComposeSubjectTestCase(TestCase):
    def test_tag_and_category(self):
        composed = compose_subject("Subject!", tag="foo", category="bar")
        self.assertEqual(composed, "[foo] bar: Subject!")

    def test_tag_missing(self):
        composed = compose_subject("Subject!", category="bar")
        self.assertEqual(composed, "bar: Subject!")

    def test_category_missing(self):
        composed = compose_subject("Subject!", tag="foo")
        self.assertEqual(composed, "[foo] Subject!")

    def test_both_missing(self):
        composed = compose_subject("subject")
        self.assertEqual(composed, "subject")


class ComposeBodyTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.message = "Lorem ipsum Dolor sit amet.\ngaudeamus igitur!"

    def test_without_dict_is_identity(self):
        self.assertEqual(compose_body(self.message), self.message)

    def test_correct_header_with_full_dict(self):
        info = {'Name': "Foo Bar", 'Social status': "Knows Python"}
        composed = compose_body(self.message, header=info)

        for key, val in info.items():
            self.assertIn("{}: {}".format(key, val), composed)

        self.assertIn(self.message, composed)
