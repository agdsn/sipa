# -*- coding: utf-8 -*-

"""
Utils for sending emails via SMTP on localhost.
"""

from email.utils import formatdate, make_msgid
from email.mime.text import MIMEText
from flask import current_app

import smtplib
import textwrap


import logging
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


def base36encode(number, alphabet="0123456789abcdefghijklmnopqrstuvwxyz"):
    """Convert an integer to a base36 string.

    Taken from [Stackoverflow](http://stackoverflow.com/a/1181922/2443886).

    Slightly modified: `base36` is now reversed because appending the
    higher digits is easier than prepending, and reversing in the end
    is done easily using `[::-1]`.
    """
    if not isinstance(number, int):
        raise TypeError("Number must be an integer")

    base36 = ""
    sign = ""

    if number < 0:
        sign = "-"
        number = -number

    if 0 <= number < len(alphabet):
        return sign + alphabet[number]

    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 += alphabet[i]

    return sign + base36[::-1]
