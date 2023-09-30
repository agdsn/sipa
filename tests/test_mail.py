from dataclasses import dataclass, field
from unittest import TestCase
from unittest.mock import MagicMock, patch

from sipa.mail import send_contact_mail, send_complex_mail, \
    send_official_contact_mail, send_usersuite_contact_mail, \
    compose_subject, compose_body, send_mail


class MailSendingTestBase(TestCase):
    """Test Base for functions using `send_mail`

    This test base provides a mock for :py:meth:`~sipa.mail.send_mail`
    so any tunction that builds up on it can be tested by watching
    what ``self.send_mail_mock`` got called with.

    This class provides its own setup routine, which either takes
    ``self.args`` and passes it as keyword arguments to
    ``self.mail_function`` (be careful to define it as a
    staticmethod).  If that is not enough (because something needs to
    be patched or similar), override ``self._call_mail_function``.
    """
    mail_function: staticmethod

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
        assert self.args[arg] in self.send_mail_mock.call_args[1][call_arg]

    def assert_arg_equals_call_arg(self, arg, call_arg):
        assert self.args[arg] == self.send_mail_mock.call_args[1][call_arg]


class ComposeSubjectTestCase(TestCase):
    def test_tag_and_category(self):
        composed = compose_subject("Subject!", tag="foo", category="bar")
        assert composed == "[foo] bar: Subject!"

    def test_tag_missing(self):
        composed = compose_subject("Subject!", category="bar")
        assert composed == "bar: Subject!"

    def test_category_missing(self):
        composed = compose_subject("Subject!", tag="foo")
        assert composed == "[foo] Subject!"

    def test_both_missing(self):
        composed = compose_subject("subject")
        assert composed == "subject"


class ComposeBodyTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.message = "Lorem ipsum Dolor sit amet.\ngaudeamus igitur!"

    def test_without_dict_is_identity(self):
        assert compose_body(self.message) == self.message

    def test_correct_header_with_full_dict(self):
        info = {'Name': "Foo Bar", 'Social status': "Knows Python"}
        composed = compose_body(self.message, header=info)

        for key, val in info.items():
            assert f"{key}: {val}" in composed

        assert self.message in composed


class SMTPTestBase(TestCase):
    """Base class providing mocks for current_app and SMTP().send_mail()"""
    def setUp(self):
        self.app_mock = MagicMock()
        self.smtp_mock = MagicMock()
        self.app_mock.config = self._get_app_config()

    def _get_app_config(self):
        return {
            'MAILSERVER_HOST': 'some-mailserver.agdsn.network',
            'MAILSERVER_PORT': 25,
            'MAILSERVER_SSL': None,
            'MAILSERVER_SSL_VERIFY': False,
            'MAILSERVER_SSL_CA_DATA': None,
            'MAILSERVER_SSL_CA_FILE': None,
            'MAILSERVER_USER': None,
            'MAILSERVER_PASSWORD': None,
            'CONTACT_SENDER_MAIL': 'noreply@agdsn.de',
        }

    def _patch_smtp(self):
        if self.app_mock.config['MAILSERVER_SSL'] == 'ssl':
            return patch('sipa.mail.smtplib.SMTP_SSL', self.smtp_mock)
        else:
            return patch('sipa.mail.smtplib.SMTP', self.smtp_mock)


class SendMailTestBase(SMTPTestBase):
    def setUp(self):
        super().setUp()

        def dont_wrap_message(msg):
            return msg
        self.wrap_mock = MagicMock(side_effect=dont_wrap_message)

        self.args = {
            'author': "foo@bar.baz",
            'recipient': "support@agd.sn",
            'subject': "Internet broken",
            'message': "Fix it!!!",
        }

        with self._patch_smtp(), \
                patch('sipa.mail.current_app', self.app_mock), \
                patch('sipa.mail.wrap_message', self.wrap_mock), \
                self.assertLogs('sipa.mail', level='INFO') as log:
            self.success = send_mail(**self.args)

        self.log = log

        @dataclass
        class SendmailSig:
            """Signature of SMTP().sendmail()"""
            from_addr: str
            to_addrs: list[str]
            msg: str
            mail_options: list = field(default_factory=lambda: [])
            rcpt_options: list = field(default_factory=lambda: [])

        call_args = self.smtp_mock().sendmail.call_args
        self.observed_call_args = SendmailSig(*call_args[0], **call_args[1])


class SendMailCommonTests:
    def test_wrap_message_called(self):
        assert self.wrap_mock.call_count == 1
        assert self.wrap_mock.call_args[0] == (self.args["message"],)

    def test_smtp_close_called(self):
        assert self.smtp_mock().close.called

    def test_sendmail_envelope_sender(self):
        assert (
            self.observed_call_args.from_addr
            == self.app_mock.config["CONTACT_SENDER_MAIL"]
        ), "Wrong envelope sender set!"

    def test_sendmail_from_header(self):
        self.assertIn(f"From: {self.args['author']}\n",
                      self.observed_call_args.msg,
                      "Wrong From: header!")

    def test_sendmail_otrs_header(self):
        assert (
            f"X-OTRS-CustomerId: {self.args['author']}\n" in self.observed_call_args.msg
        ), "X-OTRS-CustumerId incorrect!"

    def test_sendmail_reply_to(self):
        assert (
            f"Reply-To: {self.args['author']}\n" in self.observed_call_args.msg
        ), "Wrong Reply-To: header!"

    def test_sendmail_recipient_passed(self):
        recipient = self.observed_call_args.to_addrs
        assert recipient == self.args["recipient"]
        message = self.observed_call_args.msg
        assert f"To: {recipient}" in message

    def test_sendmail_subject_passed(self):
        message = self.observed_call_args.msg
        assert f"Subject: {self.args['subject']}" in message

    def test_returned_true(self):
        assert self.success

    def test_info_logged(self):
        log_message = self.log.output.pop()
        assert "Successfully sent mail" in log_message
        # nothing else there
        assert not self.log.output


class SendMailNoAuthTestCase(SendMailTestBase, SendMailCommonTests):
    def test_smtp_login_not_called(self):
        assert not self.smtp_mock().login.called


class SendMailAuthTestCase(SendMailTestBase, SendMailCommonTests):
    def test_smtp_login_called(self):
        assert self.smtp_mock().login.called

    def _get_app_config(self):
        return {
            **super(SendMailTestBase, self)._get_app_config(),
            'MAILSERVER_USER': 'test',
            'MAILSERVER_PASSWORD': 'secure',
        }


class SendMailTestSslCase(SendMailTestBase, SendMailCommonTests):
    def _get_app_config(self):
        return {
            **super(SendMailTestBase, self)._get_app_config(),
            'MAILSERVER_PORT': 465,
            'MAILSERVER_SSL': 'ssl',
        }


class SendMailTestStarttlsCase(SendMailTestBase, SendMailCommonTests):
    def test_smtp_starttls_called(self):
        assert self.smtp_mock().starttls.called

    def _get_app_config(self):
        return {
            **super(SendMailTestBase, self)._get_app_config(),
            'MAILSERVER_PORT': 587,
            'MAILSERVER_SSL': 'starttls',
        }


class SendMailFailingTestCase(SMTPTestBase):
    def setUp(self):
        super().setUp()

        def bad_sendmail(*_, **__):
            raise OSError()
        self.smtp_mock().sendmail.side_effect = bad_sendmail

        with self._patch_smtp(), patch(
            "sipa.mail.current_app", self.app_mock
        ), self.assertLogs("sipa.mail", level="ERROR") as log:
            self.success = send_mail("", "", "", "")

        self.log = log

    def test_send_mail_logs_on_success(self):

        log_message = self.log.output.pop()
        assert "Unable to connect" in log_message
        # nothing else there
        assert not self.log.output

    def test_failing_returns_false(self):
        assert not self.success


class ComplexMailContentTestCase(MailSendingTestBase):
    mail_function = staticmethod(send_complex_mail)

    @property
    def args(self):
        return {
            'author': "foo@bar.baz",
            'subject': "test",
            'message': "Dies ist eine Testnachricht.",
            'tag': "Testtag",
            'category': 'Kategorie mit einer nichtleeren Menge an Morphismen',
            'header': {'foo': "Bar", 'alkohol': "Na Klar!"},
        }

    def test_success_passed(self):
        assert self.success

    def test_keyword_args_used(self):
        assert not self.send_mail_mock.call_args[0]

    def test_subject_complete_passed(self):
        subject_passed = self.send_mail_mock.call_args[1]['subject']

        assert self.args["subject"] in subject_passed
        assert self.args["tag"] in subject_passed
        assert self.args["category"] in subject_passed

    def test_message_complete_passed(self):
        message_passed = self.send_mail_mock.call_args[1]['message']

        assert self.args["message"] in message_passed

        for key, value in self.args['header'].items():
            assert key in message_passed
            assert value in message_passed


class ComplexMailArgumentsTestCase(TestCase):
    def test_fails_on_missing_argument(self):
        """Test send_complex_mail needs all of the required arguments"""
        required_args = ['author', 'recipient', 'subject', 'message']

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
            'author': "foo@bar.baz",
            'subject': "test",
            'message': "Suchen sie einen Partner?",
            'name': "Paul Dirac",
        }

    def test_success_passed(self):
        assert self.success

    def test_sender_mail_passed(self):
        self.assert_arg_equals_call_arg('author', 'author')

    def test_subject_complete(self):
        self.assert_arg_in_call_arg('subject', 'subject')

    def test_message_body_complete(self):
        self.assert_arg_in_call_arg('message', 'message')
        self.assert_arg_in_call_arg('name', 'message')


class ContactMailTestCase(MailSendingTestBase):
    def setUp(self):
        self.backends_mock = MagicMock()
        self.dorm_display_name = "Testdormitory"
        self.backends_mock.get_dormitory('test').display_name = self.dorm_display_name
        self.dorm_mail = "support@foo.bar"
        self.backends_mock.datasource.support_mail = self.dorm_mail

        # the setup of the parent class comes later because this
        # prepares the `mail_function` call
        super().setUp()

    @property
    def args(self):
        return {
            'author': "foo@bar.baz",
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
        assert self.success

    def test_message_complete(self):
        self.assert_arg_in_call_arg("message", "message")
        self.assert_arg_in_call_arg("name", "message")
        assert self.dorm_display_name in self.send_mail_mock.call_args[1]["message"]

    def test_subject_complete(self):
        self.assert_arg_in_call_arg('subject', 'subject')

    def test_sender_mail_passed(self):
        self.assert_arg_equals_call_arg('author', 'author')

    def test_recipient_passed(self):
        recipient = self.send_mail_mock.call_args[1]['recipient']
        assert recipient == self.dorm_mail


class UsersuiteContactMailTestCase(MailSendingTestBase):
    def setUp(self):
        mock = MagicMock()
        mock.login.value = 'test_login'
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
        assert self.success

    def test_sender_composed_correctly(self):
        sender = self.send_mail_mock.call_args[1]["author"]
        assert sender.endswith(
            self.user_mock.datasource.mail_server
        ), "Sender does not end with mail_server"
        assert sender.startswith(
            self.user_mock.login.value
        ), "Sender does not start with login"

    def test_recipient_passed(self):
        expected_recipient = self.user_mock.datasource.support_mail
        assert expected_recipient == self.send_mail_mock.call_args[1]["recipient"]

    def test_subject_completeg(self):
        self.assert_arg_in_call_arg('subject', 'subject')
        self.assert_arg_in_call_arg('category', 'subject')

    def test_message_complete(self):
        self.assert_arg_in_call_arg("message", "message")
        assert self.user_mock.login.value in self.send_mail_mock.call_args[1]["message"]
