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
    "Passwort muss Buchstaben in Groß- und Kleinschreibung, Zahlen "
    "und Sonderzeichen enthalten sowie mindestens acht Zeichen lang sein"
)

password_validator = Regexp(
    "("
    "(?=.*\d)"                                     # ≥ 1 Digit
    "(?=.*[a-z])(?=.*[A-Z])"                       # ≥ 1 Letter (up/low
    "(?=.*[…_\[\]^!<>=&@:-?*}{/\#$|~`+%\"\';])"    # ≥ 1 Special char
    ".{8,}"                                        # ≥ 8 chars
    ")",
    message=password_required_charset_message
)


class ReadonlyStringField(StringField):
    def __init__(self, *args, **kwargs):
        super(ReadonlyStringField, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return super(ReadonlyStringField, self).__call__(
            *args, readonly=True, **kwargs)


class ContactForm(Form):
    email = ReadonlyStringField(
        label=lazy_gettext("Deine E-Mail-Adresse"),
        validators=[Email(gettext("E-Mail ist nicht in gültigem Format!"))],
    )
    type = SelectField(label=lazy_gettext("Kategorie"), choices=[
        ("frage", lazy_gettext("Allgemeine Frage an die Administratoren")),
        ("stoerung",
         lazy_gettext("Störungen im Netzwerk Wundtstraße/Zellescher Weg")),
        ("finanzen", lazy_gettext("Finanzfragen (Beiträge, Gebühren)")),
        ("eigene-technik", lazy_gettext("Probleme mit privater Technik"))
    ])
    subject = StringField(label=lazy_gettext("Betreff"), validators=[
        DataRequired(gettext("Betreff muss angegeben werden!"))])
    message = TextAreaField(label=lazy_gettext("Nachricht"), validators=[
        DataRequired(gettext("Nachricht fehlt!"))
    ])


class ChangePasswordForm(Form):
    old = PasswordField(label=lazy_gettext("Altes Passwort"), validators=[
        DataRequired(gettext("Altes Passwort muss angegeben werden!"))])
    new = PasswordField(label=lazy_gettext("Neues Passwort"), validators=[
        DataRequired(gettext("Neues Passwort fehlt!")),
        password_validator
    ])
    confirm = PasswordField(label=lazy_gettext("Bestätigung"), validators=[
        DataRequired(gettext("Bestätigung des neuen Passworts fehlt!")),
        EqualTo('new',
                message=gettext("Neue Passwörter stimmen nicht überein!"))
    ])


class ChangeMailForm(Form):
    password = PasswordField(
        label=lazy_gettext("Passwort"),
        validators=[DataRequired(gettext("Passwort nicht angegeben!"))])
    email = StringField(
        label=lazy_gettext("Neue Mail"),
        validators=[Email(gettext("E-Mail ist nicht in gültigem Format!"))])


class DeleteMailForm(Form):
    password = PasswordField(
        validators=[DataRequired(gettext("Passwort nicht angegeben!"))])


def require_unicast_mac(form, field):
    """
    Validator for unicast mac adress.
    A MAC-adress is defined to be “broadcast” if the least significant bit
    of the first octet is 1. Therefore, it has to be 0 to be valid.
    """
    if int(field.data[1], 16) % 2:
        raise ValidationError(gettext("MAC muss unicast-Adresse sein!"))


class ChangeMACForm(Form):
    password = PasswordField(
        label=lazy_gettext("Passwort"),
        validators=[DataRequired(gettext("Passwort nicht angegeben!"))])
    mac = StringField(
        label=lazy_gettext("Neue MAC"),
        validators=[DataRequired("MAC-Adresse nicht angegeben!"),
                    MacAddress("MAC ist nicht in gültigem Format!"),
                    require_unicast_mac])


class LoginForm(Form):
    dormitory = SelectField(
        lazy_gettext("Wohnheim"),
        choices=LocalProxy(list_all_dormitories),
        default=LocalProxy(lambda: preferred_dormitory_name()),
        validators=[AnyOf(supported_dormitories,
                          message=gettext("Kein gültiges Wohnheim!"))]
    )
    username = StringField(
        label=lazy_gettext("Nutzername"),
        validators=[
            DataRequired(gettext("Nutzername muss angegeben werden!")),
            Regexp("^[^ ].*[^ ]$", message=gettext(
                "Nutzername darf nicht von Leerzeichen umgeben sein!")),
            Regexp("^[^,+\"\\<>;#]+$", message=gettext(
                "Nutzername enthält ungültige Zeichen!")),
        ]
    )
    password = PasswordField(
        label=lazy_gettext("Passwort"),
        validators=[DataRequired(gettext("Kein Passwort eingegeben!"))]
    )
    remember = BooleanField(default=lazy_gettext("Anmeldung merken"))


class HostingForm(Form):
    password = PasswordField(lazy_gettext("Passwort"), validators=[
        DataRequired(gettext("Kein Passwort eingegeben!")),
        password_validator
    ])
    confirm = PasswordField(lazy_gettext("Bestätigung"), validators=[
        DataRequired(gettext("Bestätigung des neuen Passworts fehlt!")),
        EqualTo('password',
                message=gettext("Neue Passwörter stimmen nicht überein!"))
    ])
    action = HiddenField()


def flash_formerrors(form):
    """If a form is submitted but could not be validated, the routing passes
    the form and this method returns all form errors (form.errors)
    as flash messages.
    """
    for field, errors in list(form.errors.items()):
        for e in errors:
            flash(e, "error")
