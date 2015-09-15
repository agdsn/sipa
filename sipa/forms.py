#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import flash
from flask.ext.babel import gettext, lazy_gettext
from flask_wtf import Form

from model import list_all_dormitories, supported_dormitories, \
    preferred_dormitory_name

from werkzeug.local import LocalProxy

from wtforms import StringField, TextAreaField, SelectField, PasswordField, \
    HiddenField, BooleanField
from wtforms.validators import DataRequired, Email, MacAddress, \
    ValidationError, EqualTo, Regexp, AnyOf


password_required_charset_message = lazy_gettext(
    u"Passwort muss Buchstaben in Groß- und Kleinschreibung, Zahlen "
    u"und Sonderzeichen enthalten sowie mindestens acht Zeichen lang sein"
)

password_validators = [
    Regexp(
        u"("
        u"(?=.*\d)"                                     # ≥ 1 Digit
        u"(?=.*[a-z])(?=.*[A-Z])"                       # ≥ 1 Letter (up/low
        u"(?=.*[…_\[\]^!<>=&@:-?*}{/\#$|~`+%\"\';])"    # ≥ 1 Special char
        u".{8,}"                                        # ≥ 8 chars
        u")",
        message=password_required_charset_message
    ),
]


class ReadonlyStringField(StringField):
    def __init__(self, *args, **kwargs):
        super(ReadonlyStringField, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return super(ReadonlyStringField, self).__call__(
            *args, readonly=True, **kwargs)


class ContactForm(Form):
    email = ReadonlyStringField(
        label=lazy_gettext(u"Deine E-Mail-Adresse"),
        validators=[Email(gettext(u"E-Mail ist nicht in gültigem Format!"))],
    )
    type = SelectField(label=lazy_gettext(u"Kategorie"), choices=[
        (u"frage", lazy_gettext(u"Allgemeine Frage an die Administratoren")),
        (u"stoerung",
         lazy_gettext(u"Störungen im Netzwerk Wundtstraße/Zellescher Weg")),
        (u"finanzen", lazy_gettext(u"Finanzfragen (Beiträge, Gebühren)")),
        (u"eigene-technik", lazy_gettext(u"Probleme mit privater Technik"))
    ])
    subject = StringField(label=lazy_gettext(u"Betreff"), validators=[
        DataRequired(gettext(u"Betreff muss angegeben werden!"))])
    message = TextAreaField(label=lazy_gettext(u"Nachricht"), validators=[
        DataRequired(gettext(u"Nachricht fehlt!"))
    ])


class ChangePasswordForm(Form):
    old = PasswordField(label=lazy_gettext(u"Altes Passwort"), validators=[
        DataRequired(gettext(u"Altes Passwort muss angegeben werden!"))])
    new = PasswordField(label=lazy_gettext(u"Neues Passwort"), validators=[
        DataRequired(gettext(u"Neues Passwort fehlt!"))
    ] + password_validators)
    confirm = PasswordField(label=lazy_gettext(u"Bestätigung"), validators=[
        DataRequired(gettext(u"Bestätigung des neuen Passworts fehlt!")),
        EqualTo('new',
                message=gettext(u"Neue Passwörter stimmen nicht überein!"))
    ])


class ChangeMailForm(Form):
    password = PasswordField(
        label=lazy_gettext(u"Passwort"),
        validators=[DataRequired(gettext(u"Passwort nicht angegeben!"))])
    email = StringField(
        label=lazy_gettext(u"Neue Mail"),
        validators=[Email(gettext(u"E-Mail ist nicht in gültigem Format!"))])


class DeleteMailForm(Form):
    password = PasswordField(
        validators=[DataRequired(gettext(u"Passwort nicht angegeben!"))])


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
        validators=[DataRequired(gettext(u"Passwort nicht angegeben!"))])
    mac = StringField(
        label=lazy_gettext(u"Neue MAC"),
        validators=[DataRequired(u"MAC-Adresse nicht angegeben!"),
                    MacAddress(u"MAC ist nicht in gültigem Format!"),
                    require_unicast_mac])


class LoginForm(Form):
    dormitory = SelectField(
        lazy_gettext(u"Wohnheim"),
        choices=LocalProxy(list_all_dormitories),
        default=LocalProxy(lambda: preferred_dormitory_name()),
        validators=[AnyOf(supported_dormitories,
                          message=gettext(u"Kein gültiges Wohnheim!"))]
    )
    username = StringField(
        label=lazy_gettext(u"Nutzername"),
        validators=[DataRequired(gettext(u"Nutzername muss "
                                         "angegeben werden!"))]
    )
    password = PasswordField(
        label=lazy_gettext(u"Passwort"),
        validators=[DataRequired(gettext(u"Kein Passwort eingegeben!"))]
    )
    remember = BooleanField(default=lazy_gettext(u"Anmeldung merken"))


class HostingForm(Form):
    password = PasswordField(lazy_gettext(u"Passwort"), validators=[
        DataRequired(gettext(u"Kein Passwort eingegeben!"))
    ] + password_validators)
    confirm = PasswordField(lazy_gettext(u"Bestätigung"), validators=[
        DataRequired(gettext(u"Bestätigung des neuen Passworts fehlt!")),
        EqualTo('password',
                message=gettext(u"Neue Passwörter stimmen nicht überein!"))
    ])
    action = HiddenField()


def flash_formerrors(form):
    """If a form is submitted but could not be validated, the routing passes
    the form and this method returns all form errors (form.errors)
    as flash messages.
    """
    for field, errors in form.errors.items():
        for e in errors:
            flash(gettext(e), "error")
