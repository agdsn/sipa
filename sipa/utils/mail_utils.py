# -*- coding: utf-8 -*-

"""
Utils for sending emails via SMTP on localhost.
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
    """Wraps an unformatted block of text to 80 characters
    """
    return_text = []
    for paragraph in message.split('\n'):
        lines = textwrap.wrap(paragraph, chars_in_line)
        if not lines:
            return_text.append('')
        else:
            return_text.extend(lines)
    return '\n'.join(return_text)


def send_mail(sender, receipient, subject, message):
    """Send a MIME text mail from sender to receipient with subject and message.
    The message will be wrapped to 80 characters and encoded to UTF8.

    Returns False, if sending from localhost:25 fails.
    Else returns True.
    """
    message = wrap_message(message)
    mail = MIMEText(message, _charset='utf-8')

    mail['Message-Id'] = make_msgid()
    mail['From'] = sender
    mail['To'] = receipient
    mail['Subject'] = subject
    mail['Date'] = formatdate(localtime=True)

    mailserver_host = current_app.config['MAILSERVER_HOST']
    mailserver_port = current_app.config['MAILSERVER_PORT']

    try:
        smtp = smtplib.SMTP()
        smtp.connect(host=mailserver_host,
                     port=mailserver_port)
        smtp.sendmail(sender, receipient, mail.as_string(0))
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
            'tags': {'from': sender, 'to': receipient,
                     'mailserver': '{}:{}'.format(mailserver_host,
                                                  mailserver_port)},
            'data': {'subject': subject, 'message': message}
        })
        return True


def send_contact_mail(sender, subject, name, message, dormitory_name):
    """Compose a mail for anonymous contacting.

    Additionally to sending the mail, it does:

        - Prepend the subject with [Kontakt]

        - Prepend the dormitory and name of the sender to the mail body

    :param str sender:
    :param str subject:
    :param str name: The sender's real-life name
    :param str message:
    :param str dormitory_name:
    """
    dormitory = backends.get_dormitory(dormitory_name)

    message = "Name: {name}\nDormitory: {dorm}\n{body}".format(
        name=name,
        dorm=dormitory.display_name,
        body=message,
    )
    subject = compose_subject(subject, tag="Kontakt")
    recipient = dormitory.datasource.support_mail

    return send_mail(sender, recipient, subject, message)


def send_official_contact_mail(sender, subject, name, message):
    """Compose a mail for official contacting.

    Additionally to sending the mail, it does:

        - Prepend the subject with [Kontakt]

    :param str sender:
    :param str subject:
    :param str name: The sender's real-life name
    :param str message:
    """
    subject = compose_subject(subject, tag="Kontakt")
    message = "Name: {name}\n\n{body}".format(
        name=name,
        body=message,
    )
    recipient = "vorstand@lists.agdsn.de"

    return send_mail(sender, recipient, subject, message)


def send_usersuite_contact_mail(category, subject, message, user=current_user):
    """Compose a mail for contacting from the usersuite

        - Prepend the subject with a tag and the category

        - Prepend the user's login to the body

    :param str category: The Category as to be included in the title
    :param str subject:
    :param str message:
    :param BaseUser user: The user object
    """
    sender = "{uid}@{server}".format(
        uid=user.uid,
        server=user.datasource.mail_server
    )
    recipient = user.datasource.support_mail

    subject = compose_subject(subject, tag="Usersuite", category=category)
    message = "Login: {uid}\n\n{body}".format(
        uid=user.login,
        body=message,
    )

    return send_mail(sender, recipient, subject, message)


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
