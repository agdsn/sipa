#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import flash, current_app
from flask.ext.babel import gettext, lazy_gettext
from flask_wtf import Form

from werkzeug.local import LocalProxy

from wtforms import TextField, TextAreaField, SelectField, PasswordField, \
    HiddenField, BooleanField
from wtforms.validators import Required, Email, MacAddress, ValidationError

from model import registered_divisions


class ContactForm(Form):
    email = TextField(label=lazy_gettext(u"Deine E-Mail-Adresse"), validators=[
        Email(gettext(u"E-Mail ist nicht in gültigem Format!"))])
    type = SelectField(label=lazy_gettext(u"Kategorie"), choices=[
        (u"frage", lazy_gettext(u"Allgemeine Frage an die Administratoren")),
        (u"stoerung",
         lazy_gettext(u"Störungen im Netzwerk Wundtstraße/Zellescher Weg")),
        (u"finanzen", lazy_gettext(u"Finanzfragen (Beiträge, Gebühren)")),
        (u"eigene-technik", lazy_gettext(u"Probleme mit privater Technik"))
    ])
    subject = TextField(label=lazy_gettext(u"Betreff"), validators=[
        Required(gettext(u"Betreff muss angegeben werden!"))])
    message = TextAreaField(label=lazy_gettext(u"Nachricht"), validators=[
        Required(gettext(u"Nachricht fehlt!"))
    ])


class ChangePasswordForm(Form):
    old = PasswordField(label=lazy_gettext(u"Altes Passwort"), validators=[
        Required(gettext(u"Altes Passwort muss angegeben werden!"))])
    new = PasswordField(label=lazy_gettext(u"Neues Passwort"), validators=[
        Required(gettext(u"Neues Passwort fehlt!"))])
    new2 = PasswordField(label=lazy_gettext(u"Bestätigung"), validators=[
        Required(gettext(u"Bestätigung des neuen Passworts fehlt!"))])


class ChangeMailForm(Form):
    password = PasswordField(
        label=lazy_gettext(u"Passwort"),
        validators=[Required(gettext(u"Passwort nicht angegeben!"))])
    email = TextField(
        label=lazy_gettext(u"Neue Mail"),
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
        label=lazy_gettext(u"Passwort"),
        validators=[Required(gettext(u"Passwort nicht angegeben!"))])
    mac = TextField(
        label=lazy_gettext(u"Neue MAC"),
        validators=[Required(u"MAC-Adresse nicht angegeben!"),
                    MacAddress(u"MAC ist nicht in gültigem Format!"),
                    require_unicast_mac])


class LoginForm(Form):
    division = SelectField(lazy_gettext(u"Sektion"), choices=LocalProxy(
        # TODO: sort by ip
        lambda: [(division.name, division.display_name)
                 for division in registered_divisions
                 if not division.debug_only or current_app.debug]
    ))
    username = TextField(
        label=lazy_gettext(u"Nutzername"),
        validators=[Required(gettext(u"Nutzername muss angegeben werden!"))]
    )
    password = PasswordField(
        label=lazy_gettext(u"Passwort"),
        validators=[Required(gettext(u"Kein Passwort eingegeben!"))]
    )
    remember = BooleanField(default=lazy_gettext(u"Anmeldung merken"))


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
