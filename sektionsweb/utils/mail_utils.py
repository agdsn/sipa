#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utils for sending emails via SMTP on localhost.
"""

from email.utils import formatdate
from email.mime.text import MIMEText
import smtplib
import textwrap

from sektionsweb.config import MAILSERVER_HOST, MAILSERVER_PORT


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

    mail['From'] = sender
    mail['To'] = receipient
    mail['Subject'] = subject
    mail['Date'] = formatdate(localtime=True)

    try:
        smtp = smtplib.SMTP()
        smtp.connect(host=MAILSERVER_HOST, port=MAILSERVER_PORT)
        smtp.sendmail(sender, receipient, mail.as_string(0))
        smtp.close()
        return True
    except IOError:
        # smtp.connect failed to connect
        return False