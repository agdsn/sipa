# -*- coding: utf-8 -*-
import re
from operator import itemgetter

from flask_babel import gettext, lazy_gettext
from flask import flash
from flask_wtf import FlaskForm
from werkzeug.local import LocalProxy
from wtforms import (BooleanField, HiddenField, PasswordField, SelectField,
                     StringField, TextAreaField, RadioField, IntegerField)
from wtforms.validators import (AnyOf, DataRequired, Email, EqualTo,
                                MacAddress, Regexp, ValidationError, NumberRange)

from sipa.model import backends


class PasswordComplexity(object):
    character_classes = ((re.compile(r'[a-z]'), lazy_gettext("Kleinbuchstaben (a-z)")),
                         (re.compile(r'[A-Z]'), lazy_gettext("Großbuchstaben (A-Z)")),
                         (re.compile(r'[0-9]'), lazy_gettext("Ziffern (0-9)")),
                         (re.compile(r'[^a-zA-Z0-9]'), lazy_gettext("andere Zeichen")))
    default_message = lazy_gettext(
        "Dein Passwort muss mindestens {min_length} Zeichen lang sein und "
        "mindestens {min_classes} verschiedene Klassen von Zeichen "
        "enthalten. Zeichen von Klassen sind: {classes}."
    )

    def __init__(self, min_length=8, min_classes=3, message=None):
        self.min_length = min_length
        self.min_classes = min_classes
        self.message = message

    def __call__(self, form, field, message=None):
        password = field.data or ''

        if len(password) < self.min_length:
            self.raise_error(message)
        matched_classes = sum(1 for pattern, name in self.character_classes
                              if pattern.search(password))
        if matched_classes < self.min_classes:
            self.raise_error(message)

    def raise_error(self, message):
        if message is None:
            if self.message is None:
                message = self.default_message
            else:
                message = self.message
        classes_descriptions = map(itemgetter(1), self.character_classes)
        classes = ', '.join(map(str, classes_descriptions))
        raise ValidationError(message.format(min_length=self.min_length,
                                             min_classes=self.min_classes,
                                             classes=classes))


def strip_filter(string):
    return string.strip() if string else None


class StrippedStringField(StringField):
    def __init__(self, *args, **kwargs):
        kwargs['filters'] = kwargs.get('filters', []) + [strip_filter]
        super().__init__(*args, **kwargs)


class ReadonlyStringField(StrippedStringField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return super().__call__(
            *args, readonly=True, **kwargs)


class ContactForm(FlaskForm):
    email = ReadonlyStringField(
        label=lazy_gettext("Deine E-Mail-Adresse"),
        validators=[Email(lazy_gettext("E-Mail ist nicht in gültigem "
                                       "Format!"))],
    )
    type = SelectField(label=lazy_gettext("Kategorie"), choices=[
        ("frage", lazy_gettext("Allgemeine Frage an die Administratoren")),
        ("stoerung",
         lazy_gettext("Störungen im Netzwerk Wundtstraße/Zellescher Weg")),
        ("finanzen", lazy_gettext("Finanzfragen (Beiträge, Gebühren)")),
        ("eigene-technik", lazy_gettext("Probleme mit privater Technik"))
    ])
    subject = StrippedStringField(label=lazy_gettext("Betreff"), validators=[
        DataRequired(lazy_gettext("Betreff muss angegeben werden!"))])
    message = TextAreaField(label=lazy_gettext("Nachricht"), validators=[
        DataRequired(lazy_gettext("Nachricht fehlt!"))
    ])


class AnonymousContactForm(FlaskForm):
    email = StrippedStringField(
        label=lazy_gettext("Deine E-Mail-Adresse"),
        validators=[Email(lazy_gettext("E-Mail ist nicht "
                                       "in gültigem Format!"))],
    )
    name = StringField(
        label=lazy_gettext("Dein Name"),
        validators=[DataRequired(lazy_gettext("Bitte gib einen Namen an!"))],
    )
    dormitory = SelectField(
        label=lazy_gettext("Wohnheim"),
        choices=LocalProxy(lambda: backends.dormitories_short),
        default=LocalProxy(lambda: backends.preferred_dormitory_name()),
    )
    subject = StrippedStringField(label=lazy_gettext("Betreff"), validators=[
        DataRequired(lazy_gettext("Betreff muss angegeben werden!"))])
    message = TextAreaField(label=lazy_gettext("Nachricht"), validators=[
        DataRequired(lazy_gettext("Nachricht fehlt!"))
    ])


class OfficialContactForm(FlaskForm):
    email = StrippedStringField(
        label=lazy_gettext("E-Mail-Adresse"),
        validators=[Email(lazy_gettext("E-Mail ist nicht "
                                       "in gültigem Format!"))],
    )
    name = StringField(
        label=lazy_gettext("Name / Organisation"),
        validators=[DataRequired(lazy_gettext("Bitte gib einen Namen an!"))],
    )
    subject = StrippedStringField(label=lazy_gettext("Betreff"), validators=[
        DataRequired(lazy_gettext("Betreff muss angegeben werden!"))])
    message = TextAreaField(label=lazy_gettext("Nachricht"), validators=[
        DataRequired(lazy_gettext("Nachricht fehlt!"))
    ])


class ChangePasswordForm(FlaskForm):
    old = PasswordField(label=lazy_gettext("Altes Passwort"), validators=[
        DataRequired(lazy_gettext("Altes Passwort muss angegeben werden!"))])
    new = PasswordField(label=lazy_gettext("Neues Passwort"), validators=[
        DataRequired(lazy_gettext("Neues Passwort fehlt!")),
        PasswordComplexity(),
    ])
    confirm = PasswordField(label=lazy_gettext("Bestätigung"), validators=[
        DataRequired(lazy_gettext("Bestätigung des neuen Passworts fehlt!")),
        EqualTo('new',
                message=lazy_gettext("Neue Passwörter stimmen nicht überein!"))
    ])


class ChangeMailForm(FlaskForm):
    password = PasswordField(
        label=lazy_gettext("Passwort"),
        validators=[DataRequired(lazy_gettext("Passwort nicht angegeben!"))])
    email = StrippedStringField(
        label=lazy_gettext("Neue Mail"),
        validators=[Email(lazy_gettext("E-Mail ist nicht in gültigem Format!"))])


class DeleteMailForm(FlaskForm):
    password = PasswordField(
        validators=[DataRequired(lazy_gettext("Passwort nicht angegeben!"))])


def require_unicast_mac(form, field):
    """
    Validator for unicast mac adress.
    A MAC-adress is defined to be “broadcast” if the least significant bit
    of the first octet is 1. Therefore, it has to be 0 to be valid.
    """
    if int(field.data[1], 16) % 2:
        raise ValidationError(gettext("MAC muss unicast-Adresse sein!"))


class ChangeMACForm(FlaskForm):
    password = PasswordField(
        label=lazy_gettext("Passwort"),
        validators=[DataRequired(lazy_gettext("Passwort nicht angegeben!"))])
    mac = StrippedStringField(
        label=lazy_gettext("Neue MAC"),
        validators=[DataRequired("MAC-Adresse nicht angegeben!"),
                    MacAddress("MAC ist nicht in gültigem Format!"),
                    require_unicast_mac])


class ChangeUseCacheForm(FlaskForm):
    use_cache = RadioField(
        label=lazy_gettext("Cache-Nutzung"),
        coerce=int,
        choices=[(0, lazy_gettext('Deaktiviert')),
                 (1, lazy_gettext('Aktiviert')),
                 ]
    )


class LoginForm(FlaskForm):
    dormitory = SelectField(
        lazy_gettext("Wohnheim"),
        choices=LocalProxy(lambda: backends.dormitories_short),
        default=LocalProxy(lambda: backends.preferred_dormitory_name()),
        validators=[LocalProxy(
            lambda: AnyOf([dorm.name for dorm in backends.dormitories],
                          message=lazy_gettext("Kein gültiges Wohnheim!"))
        )]
    )
    username = StrippedStringField(
        label=lazy_gettext("Nutzername"),
        validators=[
            DataRequired(lazy_gettext("Nutzername muss angegeben werden!")),
            Regexp("^[^,+\"\\<>;#]+$", message=lazy_gettext(
                "Nutzername enthält ungültige Zeichen!")),
        ],
    )
    password = PasswordField(
        label=lazy_gettext("Passwort"),
        validators=[DataRequired(lazy_gettext("Kein Passwort eingegeben!"))]
    )
    remember = BooleanField(default=lazy_gettext("Anmeldung merken"))


class HostingForm(FlaskForm):
    password = PasswordField(lazy_gettext("Passwort"), validators=[
        DataRequired(lazy_gettext("Kein Passwort eingegeben!")),
        PasswordComplexity(),
    ])
    confirm = PasswordField(lazy_gettext("Bestätigung"), validators=[
        DataRequired(lazy_gettext("Bestätigung des neuen Passworts fehlt!")),
        EqualTo('password',
                message=lazy_gettext("Neue Passwörter stimmen nicht überein!"))
    ])
    action = HiddenField()


class PaymentForm(FlaskForm):
    months = IntegerField(default=1)


def flash_formerrors(form):
    """If a form is submitted but could not be validated, the routing passes
    the form and this method returns all form errors (form.errors)
    as flash messages.
    """
    for field, errors in list(form.errors.items()):
        for e in errors:
            flash(e, "error")
