#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import flash
from flask.ext.wtf import Form
from wtforms import TextField, TextAreaField, SelectField, PasswordField
from wtforms.validators import Required, Email


class ContactForm(Form):
    email = TextField(u"E-Mail", validators=[Email(u"E-Mail ist nicht in gültigem Format!")])
    subject = TextField(u"Betreff", validators=[Required(u"Betreff muss angegeben werden!")])
    type = SelectField(u"Kategorie", choices=[
        (u"frage", u"Allgemeine Frage an die Admins"),
        (u"stoerung", u"Störungen im Wu-ZW-Netz"),
        (u"finanzen", u"Finanzen (Beiträge, Gebühren)"),
        (u"eigene-technik", u"Probleme mit eigener Technik")
    ])
    message = TextAreaField(u"Nachricht", validators=[Required(u"Nachricht fehlt!")])


class ChangePasswordForm(Form):
    old = PasswordField(validators=[Required(u"Altes Passwort muss angegeben werden!")])
    new = PasswordField(validators=[Required(u"Neues Passwort fehlt!")])
    new2 = PasswordField(validators=[Required(u"Bestätigung des neuen Passworts fehlt!")])


def flash_formerrors(form):
    """If a form is submitted, but could not be validated the routing passes the form
    and this method returns all form errors (form.errors) as flash messages.
    """
    for field, errors in form.errors.items():
            for e in errors:
                flash(e, "error")