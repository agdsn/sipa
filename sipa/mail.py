# -*- coding: utf-8 -*-

"""
Functions concerned with mail composition and transmission

This module ultimately provides functions to be used by a blueprint in
order to compose and send a mail, for instance
:py:func:`send_contact_mail`.

On the layer below, some intermediate functions are introduced which
are needed to compose and send the mails.  The core is
:py:func:`send_complex_mail`, which calls :py:func:`send_mail`
prepending optional information to the title and body
"""

import logging
import smtplib
import textwrap

from email.utils import formatdate, make_msgid
from email.mime.text import MIMEText

from flask import current_app
from flask_login import current_user

from sipa.model import backends


logger = logging.getLogger(__name__)


def wrap_message(message, chars_in_line=80):
    """Wrap a block of text to a certain amount of characters

    :param str message: The message
    :param int chars_in_line: The width to wrap against

    :returns: the wrapped message

    :rtype: str
    """
    return_text = []
    for paragraph in message.split('\n'):
        lines = textwrap.wrap(paragraph, chars_in_line)
        if not lines:
            return_text.append('')
        else:
            return_text.extend(lines)
    return '\n'.join(return_text)


def send_mail(sender, recipient, subject, message):
    """Send a MIME text mail

    Send a mail from ``sender`` to ``receipient`` with ``subject`` and
    ``message``.  The message will be wrapped to 80 characters and
    encoded to UTF8.

    Returns False, if sending from localhost:25 fails.  Else returns
    True.

    :param str sender: The mail address of the sender
    :param str recipient: The mail address of the recipient
    :param str subject:
    :param str message:

    :returns: Whether the transmission succeeded

    :rtype: bool
    """
    message = wrap_message(message)
    mail = MIMEText(message, _charset='utf-8')

    mail['Message-Id'] = make_msgid()
    mail['From'] = sender
    mail['To'] = recipient
    mail['Subject'] = subject
    mail['Date'] = formatdate(localtime=True)

    mailserver_host = current_app.config['MAILSERVER_HOST']
    mailserver_port = current_app.config['MAILSERVER_PORT']

    try:
        smtp = smtplib.SMTP()
        smtp.connect(host=mailserver_host,
                     port=mailserver_port)
        smtp.sendmail(sender, recipient, mail.as_string(0))
        smtp.close()
    except IOError as e:
        # smtp.connect failed to connect
        logger.critical('Unable to connect to SMTP server', extra={
            'trace': True,
            'tags': {'mailserver': '{}:{}'.format(mailserver_host,
                                                  mailserver_port)},
            'data': {'exception_arguments': e.args}
        })
        return False
    else:
        logger.info('Successfully sent mail from usersuite', extra={
            'tags': {'from': sender, 'to': recipient,
                     'mailserver': '{}:{}'.format(mailserver_host,
                                                  mailserver_port)},
            'data': {'subject': subject, 'message': message}
        })
        return True


def send_contact_mail(sender, subject, message, name, dormitory_name):
    """Compose a mail for anonymous contacting.

    Call :py:func:`send_complex_mail` setting a tag plus name and
    dormitory in the header.

    :param str sender: The e-mail of the sender
    :param str subject:
    :param str message:
    :param str name: The sender's real-life name
    :param str dormitory_name: The string identifier of the chosen
        dormitory

    :returns: see :py:func:`send_complex_mail`
    """
    dormitory = backends.get_dormitory(dormitory_name)

    return send_complex_mail(
        sender=sender,
        recipient=dormitory.datasource.support_mail,
        subject=subject,
        message=message,
        tag="Kontakt",
        header={'Name': name, 'Dormitory': dormitory.display_name},
    )


def send_official_contact_mail(sender, subject, message, name):
    """Compose a mail for official contacting.

    Call :py:func:`send_complex_mail` setting a tag.

    :param str sender: The e-mail address of the sender
    :param str subject:
    :param str message:
    :param str name: The sender's real-life name

    :returns: see :py:func:`send_complex_mail`
    """
    return send_complex_mail(
        sender=sender,
        recipient="vorstand@lists.agdsn.de",
        subject=subject,
        message=message,
        tag="Kontakt",
        header={'Name': name},
    )


def send_usersuite_contact_mail(subject, message, category, user=current_user):
    """Compose a mail for contacting from the usersuite

    Call :py:func:`send_complex_mail` setting a tag and the category
    plus the user's login in the header.

    The sender is chosen to be the user's mailaccount on the
    datasource's mail server.

    :param str subject:
    :param str message:
    :param str category: The Category as to be included in the title
    :param BaseUser user: The user object

    :returns: see :py:func:`send_complex_mail`
    """
    return send_complex_mail(
        sender="{uid}@{server}".format(
            uid=user.uid,
            server=user.datasource.mail_server
        ),
        recipient=user.datasource.support_mail,
        subject=subject,
        message=message,
        tag="Usersuite",
        category=category,
        header={'Login': user.uid},
    )


def send_complex_mail(subject, message, tag="", category="", header=None, **kwargs):
    """Send a mail with context information in subject and body.

    This function is just a modified call of :py:func:`send_mail`, to
    which all the other arguments are passed.

    :param str subject:
    :param str message:
    :param str tag: See :py:func:`compose_subject`
    :param str category: See :py:func:`compose_subject`
    :param dict header: See :py:func:`compose_body`

    :returns: see :py:func:`send_mail`
    """
    return send_mail(
        **kwargs,
        subject=compose_subject(subject, tag=tag, category=category),
        message=compose_body(message, header=header),
    )


def compose_subject(raw_subject, tag="", category=""):
    """Compose a subject containing a tag and a category.

    If any of tag or category is missing, don't print the
    corresponding part (without whitespace issues).

    :param str raw_subject: The original subject
    :param str tag:
    :param str category:

    :returns: The subject.  Form: "[{tag}] {category}: {raw_subject}"

    :rtype: str
    """
    subject = ""
    if tag:
        subject += "[{}] ".format(tag)

    if category:
        subject += "{}: ".format(category)

    subject += raw_subject

    return subject


def compose_body(message, header=None):
    """Prepend additional information to a message.

    :param str message:
    :param dict header: Dict of the additional "key: value"
        entries to be prepended to the mail.

    :returns: The composed body

    :rtype: str
    """
    if not header:
        return message

    header = "\n".join("{key}: {value}".format(key=key, value=value)
                       for key, value in header.items())

    return "{header}\n\n{body}".format(header=header, body=message)
