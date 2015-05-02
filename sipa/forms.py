#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import flash
from flask.ext.babel import gettext, lazy_gettext
from flask_wtf import Form
from wtforms import TextField, TextAreaField, SelectField, PasswordField, \
    HiddenField
from wtforms.validators import Required, Email, MacAddress, ValidationError

class ContactForm(Form):
    email = TextField(u"E-Mail", validators=[
        Email(gettext(u"E-Mail ist nicht in gültigem Format!"))])
    subject = TextField(u"Betreff", validators=[
        Required(gettext(u"Betreff muss angegeben werden!"))])
    type = SelectField(u"Kategorie", choices=[
        (u"frage", lazy_gettext(u"Allgemeine Frage an die Administratoren")),
        (u"stoerung",
         lazy_gettext(u"Störungen im Netzwerk Wundtstraße/Zellescher Weg")),
        (u"finanzen", lazy_gettext(u"Finanzfragen (Beiträge, Gebühren)")),
        (u"eigene-technik", lazy_gettext(u"Probleme mit privater Technik"))
    ])
    message = TextAreaField(u"Nachricht",
                            validators=[Required(gettext(u"Nachricht fehlt!"))])


class ChangePasswordForm(Form):
    old = PasswordField(validators=[
        Required(gettext(u"Altes Passwort muss angegeben werden!"))])
    new = PasswordField(
        validators=[Required(gettext(u"Neues Passwort fehlt!"))])
    new2 = PasswordField(validators=[
        Required(gettext(u"Bestätigung des neuen Passworts fehlt!"))])


class ChangeMailForm(Form):
    password = PasswordField(
        validators=[Required(gettext(u"Passwort nicht angegeben!"))])
    email = TextField(
        validators=[Email(gettext(u"E-Mail ist nicht in gültigem Format!"))])


class DeleteMailForm(Form):
    password = PasswordField(
        validators=[Required(gettext(u"Passwort nicht angegeben!"))])


def require_unicast_mac(form, field):
    """
    Validator for unicast mac adress.
    A MAC-adress is defined to be “broadcast” if the least significant bit
    of the first octet is 1. Therefore, it has to be 0 to be valid.
    """
    if int(field.data[1], 16) % 2:
        raise ValidationError(gettext(u"MAC muss unicast-Adresse sein!"))


class ChangeMACForm(Form):
    password = PasswordField(
        validators=[Required(gettext(u"Passwort nicht angegeben!"))])
    mac = TextField(validators=[Required(u"MAC-Adresse nicht angegeben!"),
                                MacAddress(
                                    u"MAC ist nicht in gültigem Format!"),
                                require_unicast_mac])


class LoginForm(Form):
    username = TextField(u"Username", validators=[
        Required(gettext(u"Nutzername muss angegeben werden!"))])
    password = PasswordField(u"Password", validators=[
        Required(gettext(u"Kein Passwort eingegeben!"))])


class HostingForm(Form):
    password1 = PasswordField(u"Password", validators=[
        Required(gettext(u"Kein Passwort eingegeben!"))])
    password2 = PasswordField(validators=[
        Required(gettext(u"Bestätigung des neuen Passworts fehlt!"))])
    action = HiddenField()


def flash_formerrors(form):
    """If a form is submitted but could not be validated, the routing passes
    the form and this method returns all form errors (form.errors)
    as flash messages.
    """
    for field, errors in form.errors.items():
        for e in errors:
            flash(gettext(e), "error")