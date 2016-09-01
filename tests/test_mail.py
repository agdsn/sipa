from unittest import TestCase
from unittest.mock import MagicMock, patch

from sipa.mail import send_contact_mail, send_complex_mail, \
    send_official_contact_mail, send_usersuite_contact_mail, \
    compose_subject, compose_body


class MailSendingTestBase(TestCase):
    def setUp(self):
        super().setUp()
        self.send_mail_mock = MagicMock(return_value=True)

        self.success = self._call_mail_function()

    def _call_mail_function(self):
        try:
            func = self.mail_function
        except AttributeError as exc:
            raise AttributeError("You must either provide `mail_function` "
                                 "or override `_call_mail_function`!") from exc

        with patch('sipa.mail.send_mail', self.send_mail_mock):
            return func(**self.args)

    @property
    def args(self):
        return {}

    def assert_arg_in_call_arg(self, arg, call_arg):
        self.assertIn(self.args[arg], self.send_mail_mock.call_args[1][call_arg])

    def assert_arg_equals_call_arg(self, arg, call_arg):
        self.assertEqual(self.args[arg], self.send_mail_mock.call_args[1][call_arg])


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


class ComplexMailContentTestCase(MailSendingTestBase):
    mail_function = staticmethod(send_complex_mail)

    @property
    def args(self):
        return {
            'sender': "foo@bar.baz",
            'subject': "test",
            'message': "Dies ist eine Testnachricht.",
            'tag': "Testtag",
            'category': 'Kategorie mit einer nichtleeren Menge an Morphismen',
            'header': {'foo': "Bar", 'alkohol': "Na Klar!"},
        }

    def test_success_passed(self):
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


class OfficialContactMailTestCase(MailSendingTestBase):
    mail_function = staticmethod(send_official_contact_mail)

    @property
    def args(self):
        return {
            'sender': "foo@bar.baz",
            'subject': "test",
            'message': "Suchen sie einen Partner?",
            'name': "Paul Dirac",
        }

    def test_success_passed(self):
        self.assertTrue(self.success)

    def test_sender_mail_passed(self):
        self.assert_arg_equals_call_arg('sender', 'sender')

    def test_subject_complete(self):
        self.assert_arg_in_call_arg('subject', 'subject')

    def test_message_body_complete(self):
        self.assert_arg_in_call_arg('message', 'message')
        self.assert_arg_in_call_arg('name', 'message')


class ContactMailTestCase(MailSendingTestBase):
    def setUp(self):
        self.backends_mock = MagicMock()
        self.dorm_display_name = "Testdormitory (nicht die Wu)"
        self.backends_mock.get_dormitory('test').display_name = self.dorm_display_name
        self.dorm_mail = "support@foo.bar"
        self.backends_mock.get_dormitory('test').datasource.support_mail = self.dorm_mail

        # the setup of the parent class comes later because this
        # prepares the `mail_function` call
        super().setUp()

    @property
    def args(self):
        return {
            'sender': "foo@bar.baz",
            'subject': "test",
            'name': "Paul Dirac",
            'message': "Nö",
            'dormitory_name': 'test',
        }

    def _call_mail_function(self):
        with patch('sipa.mail.send_mail', self.send_mail_mock), \
                patch('sipa.mail.backends', self.backends_mock):
            return send_contact_mail(**self.args)

    def test_success_passed(self):
        self.assertTrue(self.success)

    def test_message_complete(self):
        self.assert_arg_in_call_arg('message', 'message')
        self.assert_arg_in_call_arg('name', 'message')
        self.assertIn(self.dorm_display_name, self.send_mail_mock.call_args[1]['message'])

    def test_subject_complete(self):
        self.assert_arg_in_call_arg('subject', 'subject')

    def test_sender_mail_passed(self):
        self.assert_arg_equals_call_arg('sender', 'sender')

    def test_recipient_passed(self):
        recipient = self.send_mail_mock.call_args[1]['recipient']
        self.assertEqual(recipient, self.dorm_mail)


class UsersuiteContactMailTestCase(MailSendingTestBase):
    def setUp(self):
        mock = MagicMock()
        mock.uid = 'test_uid'
        mock.datasource.mail_server = "agdsn.de"
        mock.datasource.support_mail = "support@agd.sn"

        self.user_mock = mock

        # the setup of the parent class comes later because this
        # prepares the `mail_function` call
        super().setUp()

    mail_function = staticmethod(send_usersuite_contact_mail)

    @property
    def args(self):
        return {
            'subject': "test",
            'message': "Nö",
            'category': "Spaßkategorie",
            'user': self.user_mock,
        }

    def test_success_passed(self):
        self.assertTrue(self.success)

    def test_sender_composed_correctly(self):
        sender = self.send_mail_mock.call_args[1]['sender']
        self.assertTrue(sender.endswith(self.user_mock.datasource.mail_server),
                        msg="Sender does not end with mail_server")
        self.assertTrue(sender.startswith(self.user_mock.uid),
                        msg="Sender does not start with uid")

    def test_recipient_passed(self):
        expected_recipient = self.user_mock.datasource.support_mail
        self.assertEqual(expected_recipient,
                         self.send_mail_mock.call_args[1]['recipient'])

    def test_subject_completeg(self):
        self.assert_arg_in_call_arg('subject', 'subject')
        self.assert_arg_in_call_arg('category', 'subject')

    def test_message_complete(self):
        self.assert_arg_in_call_arg('message', 'message')
        self.assertIn(self.user_mock.uid, self.send_mail_mock.call_args[1]['message'])
