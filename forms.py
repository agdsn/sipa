#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask.ext.wtf import Form
from wtforms import TextField, TextAreaField, SelectField
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
