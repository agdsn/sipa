#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utils for sending emails via SMTP on localhost.
"""

from email.utils import formatdate
from email.mime.text import MIMEText
import smtplib
import textwrap

from sipa import app, logger


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

    mailserver_host = app.config['MAILSERVER_HOST']
    mailserver_port = app.config['MAILSERVER_PORT']
    try:
        smtp = smtplib.SMTP()
        smtp.connect(host=mailserver_host,
                     port=mailserver_port)
        smtp.sendmail(sender, receipient, mail.as_string(0))
        smtp.close()
    except IOError as e:
        # smtp.connect failed to connect
        logger.critical('Unable to connect to SMTP server {}:{}: {}'.format(
            mailserver_host,
            mailserver_port,
            e.args,
        ))
        return False
    else:
        logger.info('Successfully sent mail FROM {} TO {} VIA {}:{}. '
                    'Subject: {}'.format(sender, receipient, mailserver_host,
                                         mailserver_port, subject))
        return True
