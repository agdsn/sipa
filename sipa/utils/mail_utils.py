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
