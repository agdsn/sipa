#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask.ext.wtf import Form
from wtforms import TextField, TextAreaField, SelectField
from wtforms.validators import Required, Email


class ContactForm(Form):
    email = TextField(u"E-Mail", validators=[Email()])
    type = SelectField(u"Kategorie", choices=[
        (u"frage", u"Allgemeine Frage"),
        (u"stoerung", u"Störung"),
        (u"probleme", u"Probleme mit eigener Technik"),
        (u"finanzen", u"Finanzen")
    ])
    message = TextAreaField(u"Nachricht", validators=[Required()])
