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
from typing import Optional, Dict, Any

from flask import current_app
from flask_login import current_user

from sipa.backends.extension import backends
from sipa.model.user import BaseUser

logger = logging.getLogger(__name__)


def wrap_message(message: str, chars_in_line: int = 80) -> str:
    """Wrap a block of text to a certain amount of characters

    :param message:
    :param chars_in_line: The width to wrap against

    :returns: the wrapped message
    """
    return_text = []
    for paragraph in message.split('\n'):
        lines = textwrap.wrap(paragraph, chars_in_line)
        if not lines:
            return_text.append('')
        else:
            return_text.extend(lines)
    return '\n'.join(return_text)


def send_mail(author: str, recipient: str, subject: str, message: str) -> bool:
    """Send a MIME text mail

    Send a mail from ``author`` to ``receipient`` with ``subject`` and
    ``message``.  The message will be wrapped to 80 characters and
    encoded to UTF8.

    Returns False, if sending from localhost:25 fails.  Else returns
    True.

    :param author: The mail address of the author
    :param recipient: The mail address of the recipient
    :param subject:
    :param message:

    :returns: Whether the transmission succeeded
    """
    sender = current_app.config['CONTACT_SENDER_MAIL']
    message = wrap_message(message)
    mail = MIMEText(message, _charset='utf-8')

    mail['Message-Id'] = make_msgid()
    mail['From'] = sender
    mail['Reply-To'] = author
    mail['X-OTRS-CustomerId'] = author
    mail['To'] = recipient
    mail['Subject'] = subject
    mail['Date'] = formatdate(localtime=True)

    mailserver_host = current_app.config['MAILSERVER_HOST']
    mailserver_port = current_app.config['MAILSERVER_PORT']

    try:
        smtp = smtplib.SMTP()
        smtp.connect(host=mailserver_host,
                     port=mailserver_port)
        smtp.sendmail(from_addr=sender, to_addrs=recipient, msg=mail.as_string(0))
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
            'tags': {'from': author, 'to': recipient,
                     'mailserver': '{}:{}'.format(mailserver_host,
                                                  mailserver_port)},
            'data': {'subject': subject, 'message': message}
        })
        return True


def send_contact_mail(author: str, subject: str, message: str,
                      name: str, dormitory_name: str) -> bool:
    """Compose a mail for anonymous contacting.

    Call :py:func:`send_complex_mail` setting a tag plus name and
    dormitory in the header.

    :param author: The e-mail of the author
    :param subject:
    :param message:
    :param name: The author's real-life name
    :param dormitory_name: The string identifier of the chosen dormitory

    :returns: see :py:func:`send_complex_mail`
    """
    dormitory = backends.get_dormitory(dormitory_name)

    return send_complex_mail(
        author=author,
        recipient=dormitory.datasource.support_mail,
        subject=subject,
        message=message,
        tag="Kontakt",
        header={'Name': name, 'Dormitory': dormitory.display_name},
    )


def send_official_contact_mail(author: str, subject: str, message: str,
                               name: str) -> bool:
    """Compose a mail for official contacting.

    Call :py:func:`send_complex_mail` setting a tag.

    :param author: The e-mail address of the author
    :param subject:
    :param message:
    :param name: The author's real-life name

    :returns: see :py:func:`send_complex_mail`
    """
    return send_complex_mail(
        author=author,
        recipient="vorstand@lists.agdsn.de",
        subject=subject,
        message=message,
        tag="Kontakt",
        header={'Name': name},
    )


def send_usersuite_contact_mail(subject: str, message: str, category: str,
                                user: BaseUser = current_user) -> bool:
    """Compose a mail for contacting from the usersuite

    Call :py:func:`send_complex_mail` setting a tag and the category
    plus the user's login in the header.

    The author is chosen to be the user's mailaccount on the
    datasource's mail server.

    :param subject:
    :param message:
    :param category: The Category as to be included in the title
    :param user:

    :returns: see :py:func:`send_complex_mail`
    """
    return send_complex_mail(
        author="{login}@{server}".format(
            login=user.login.value,
            server=user.datasource.mail_server
        ),
        recipient=user.datasource.support_mail,
        subject=subject,
        message=message,
        tag="Usersuite",
        category=category,
        header={'Login': user.login.value},
    )


def send_complex_mail(subject: str, message: str, tag: str = "",
                      category: str = "", header: Optional[Dict[str, Any]] = None,
                      **kwargs) -> bool:
    """Send a mail with context information in subject and body.

    This function is just a modified call of :py:func:`send_mail`, to
    which all the other arguments are passed.

    :param subject:
    :param message:
    :param tag: See :py:func:`compose_subject`
    :param category: See :py:func:`compose_subject`
    :param header: See :py:func:`compose_body`

    :returns: see :py:func:`send_mail`
    """
    return send_mail(
        **kwargs,
        subject=compose_subject(subject, tag=tag, category=category),
        message=compose_body(message, header=header),
    )


def compose_subject(raw_subject: str, tag: str = "", category: str = "") -> str:
    """Compose a subject containing a tag and a category.

    If any of tag or category is missing, don't print the
    corresponding part (without whitespace issues).

    :param raw_subject: The original subject
    :param tag:
    :param category:

    :returns: The subject.  Form: "[{tag}] {category}: {raw_subject}"
    """
    subject = ""
    if tag:
        subject += "[{}] ".format(tag)

    if category:
        subject += "{}: ".format(category)

    subject += raw_subject

    return subject


def compose_body(message: str, header: Optional[Dict[str, Any]] = None):
    """Prepend additional information to a message.

    :param message:
    :param header: Dict of the additional "key: value"
        entries to be prepended to the mail.

    :returns: The composed body
    """
    if not header:
        return message

    serialized_header = "\n".join("{key}: {value}".format(key=key, value=value)
                                  for key, value in header.items())

    return "{header}\n\n{body}".format(header=serialized_header, body=message)
