#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask.ext.wtf import Form
from wtforms import TextField, TextAreaField, SelectField
from wtforms.validators import Required, Email


class ContactForm(Form):
    email = TextField(u"E-Mail", validators=[Email()])
    type = SelectField(u"Kategorie", choices=[
        (u"frage", u"Allgemeine Frage an die Admins"),
        (u"stoerung", u"Störungen im Wu-ZW-Netz"),
        (u"finanzen", u"Finanzen (Beiträge, Gebühren)"),
        (u"probleme", u"Probleme mit eigener Technik")
    ])
    message = TextAreaField(u"Nachricht", validators=[Required()])
