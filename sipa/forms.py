# -*- coding: utf-8 -*-
import re
from datetime import date
from operator import itemgetter

from flask_babel import gettext, lazy_gettext
from flask import flash
from flask_login import current_user
from flask_wtf import FlaskForm
from werkzeug.local import LocalProxy
from wtforms import (BooleanField, HiddenField, PasswordField, SelectField,
                     StringField, TextAreaField, RadioField, IntegerField, DateField, SubmitField)
from wtforms.validators import (AnyOf, DataRequired, Email, EqualTo, InputRequired,
                                MacAddress, Regexp, ValidationError, NumberRange, Optional, Length)

from sipa.backends.extension import backends, _dorm_summary


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


class OptionalIf(Optional):
    # makes a field optional if some other data is supplied or is not supplied
    def __init__(self, deciding_field, invert=False, *args, **kwargs):
        self.deciding_field = deciding_field
        self.invert = invert
        super(OptionalIf, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        deciding_field = form._fields.get(self.deciding_field)
        deciding_has_data = deciding_field is not None and bool(
            deciding_field.data) and deciding_field.data != 'None'
        if deciding_has_data ^ self.invert:
            super(OptionalIf, self).__call__(form, field)


def lower_filter(string):
    return string.lower() if string else None


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


class EmailField(StrippedStringField):
    def __init__(self, *args, **kwargs):
        validators = [
            DataRequired(lazy_gettext("E-Mail-Adresse hat ein ungültiges Format!")),
            Email(lazy_gettext("E-Mail-Adresse hat ein ungültiges Format!"))
        ]
        if 'validators' in kwargs:
            kwargs['validators'] = validators + kwargs['validators']
        else:
            kwargs['validators'] = validators
        super().__init__(*args, **kwargs)


class NativeDateField(DateField):
    min: date = None
    max: date = None

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('render_kw', {})['type'] = 'date'
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if self.min is not None:
            kwargs['min'] = self.min.strftime(self.format)
        if self.max is not None:
            kwargs['max'] = self.max.strftime(self.format)
        return super().__call__(*args, **kwargs)


class SpamCheckField(StringField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = u'%s %s' % ('honey', c)
        kwargs['autocomplete'] = 'off'
        return super().__call__(*args, **kwargs)


class SpamProtectedForm(FlaskForm):
    # Adds a honypot for bots to the form.
    # This field must not be filled out to submit the form.
    # We're using 'website' as the field-name since we won't give bots a hint.
    website = SpamCheckField(label="", validators=[Length(0, 0, "You seem to like honey.")])


class ContactForm(SpamProtectedForm):
    email = EmailField(label=lazy_gettext("Deine E-Mail-Adresse"))
    type = SelectField(label=lazy_gettext("Kategorie"), choices=[
        ("frage", lazy_gettext("Allgemeine Fragen")),
        ("stoerung", lazy_gettext("Störung im Netzwerk")),
        ("finanzen", lazy_gettext("Finanzfragen (Beiträge, Gebühren)")),
        ("eigene-technik", lazy_gettext("Probleme mit privater Technik"))
    ])
    subject = StrippedStringField(label=lazy_gettext("Betreff"), validators=[
        DataRequired(lazy_gettext("Betreff muss angegeben werden!"))])
    message = TextAreaField(label=lazy_gettext("Nachricht"), validators=[
        DataRequired(lazy_gettext("Nachricht fehlt!"))
    ])


class AnonymousContactForm(SpamProtectedForm):
    email = EmailField(label=lazy_gettext("Deine E-Mail-Adresse"))
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


class OfficialContactForm(SpamProtectedForm):
    email = EmailField(label=lazy_gettext("E-Mail-Adresse"))
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
    email = EmailField(label=lazy_gettext("E-Mail-Adresse"))
    forwarded = BooleanField(
        label=lazy_gettext(LocalProxy(lambda:
            "Mails für mein AG DSN E-Mail-Konto ({agdsn_email}) an private E-Mail-Adresse weiterleiten"
            .format(agdsn_email=f'{current_user.login.value}@agdsn.me'))))


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
        validators=[DataRequired(lazy_gettext("MAC-Adresse nicht angegeben!")),
                    MacAddress(lazy_gettext("MAC ist nicht in gültigem Format!")),
                    require_unicast_mac],
        description="XX:XX:XX:XX:XX:XX")
    host_name = StringField(
        label=lazy_gettext("Neuer Gerätename (Optional)"),
        validators=[Regexp(regex="^[a-zA-Z0-9 ]+",
                           message=lazy_gettext("Gerätename ist ungültig")),
                    Optional(),
                    Length(-1, 30, lazy_gettext("Gerätename zu lang"))],
        description=lazy_gettext("TL-WR841N, MacBook, FritzBox, PC, Laptop, o.Ä."),
    )


class ActivateNetworkAccessForm(FlaskForm):
    password = PasswordField(
        label=lazy_gettext("Passwort"),
        validators=[DataRequired(lazy_gettext("Passwort nicht angegeben!"))])
    mac = StrippedStringField(
        label=lazy_gettext("MAC-Adresse"),
        validators=[DataRequired(lazy_gettext("MAC-Adresse nicht angegeben!")),
                    MacAddress(lazy_gettext("MAC ist nicht in gültigem Format!")),
                    require_unicast_mac],
        description="XX:XX:XX:XX:XX:XX")
    birthdate = NativeDateField(label=lazy_gettext("Geburtsdatum"),
                          validators=[DataRequired(lazy_gettext("Geburtsdatum nicht angegeben!"))],
                          description=lazy_gettext("YYYY-MM-DD (z.B. 1995-10-23)"))
    host_name = StringField(
        label=lazy_gettext("Gerätename (Optional)"),
        validators=[Regexp(regex="^[a-zA-Z0-9 ]+",
                           message=lazy_gettext("Gerätename ist ungültig")),
                    Optional(),
                    Length(-1, 30, lazy_gettext("Gerätename zu lang"))],
        description=lazy_gettext("TL-WR841N, MacBook, FritzBox, PC, Laptop, o.Ä.")
    )


class TerminateMembershipForm(FlaskForm):
    end_date = NativeDateField(label=lazy_gettext("Austrittsdatum"),
                         validators=[DataRequired(lazy_gettext("Austrittsdatum nicht angegeben!"))],
                         description=lazy_gettext("YYYY-MM-DD (z.B. 2018-10-01)"))

    def validate_end_date(form, field):
        if field.data < date.today():
            raise ValidationError(lazy_gettext("Das Austrittsdatum darf nicht in der Vergangenheit "
                                               "liegen!"))


class TerminateMembershipConfirmForm(FlaskForm):
    end_date = NativeDateField(label=lazy_gettext("Austrittsdatum"),
                         render_kw={'readonly': True},
                         validators=[DataRequired("invalid end date")])

    estimated_balance = StringField(
        label=lazy_gettext("Geschätzter Kontostand (in EUR) zum Ende der Mitgliedschaft"),
        render_kw={'readonly': True},
        validators=[DataRequired("invalid balance")])

    confirm_termination = BooleanField(label=lazy_gettext(
        "Ich bestätige, dass ich meine Mitgliedschaft zum obenstehenden Datum beenden möchte"),
        validators=[
            DataRequired(lazy_gettext("Bitte bestätige die Beendigung der Mitgliedschaft"))])

    confirm_settlement = BooleanField(label=lazy_gettext(
        "Ich bestätige, dass ich ggf. ausstehende Beiträge baldmöglichst bezahle"),
        validators=[
            DataRequired(lazy_gettext(
                "Bitte bestätige die baldmöglichste Bezahlung von ausstehenden Beiträgen."))])

    confirm_donation = BooleanField(label=lazy_gettext(
        "Ich bestätige, dass ich zu viel gezahltes Guthaben spende, wenn ich nicht innerhalb "
        "von 31 Tagen nach Mitgliedschaftsende einen Rückerüberweisungsantrag stelle"),
        validators=[
            DataRequired(lazy_gettext("Bitte bestätige die Spendeneinwilligung."))])


class ContinueMembershipForm(FlaskForm):
    confirm_continuation = BooleanField(label=lazy_gettext(
        "Ich bestätige, dass ich die Kündigung meiner Mitgliedschaft zurückziehe"),
        validators=[
            DataRequired(lazy_gettext("Bitte bestätige die Aufhebung der Kündigung"))])


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
    remember = BooleanField(label=lazy_gettext("Anmeldung merken"))


class PasswordRequestResetForm(FlaskForm):
    ident = StrippedStringField(
        label=lazy_gettext("Nutzername oder Nutzer-ID"),
        description='XXXXX-YY',
        validators=[
            DataRequired(lazy_gettext("Nutzername muss angegeben werden!")),
            Regexp("^[^,+\"\\<>;#]+$", message=lazy_gettext(
                "Identifizierung enthält ungültige Zeichen!")),
        ],
    )

    email = EmailField(label=lazy_gettext("Hinterlegte E-Mail-Adresse"))


class PasswordResetForm(FlaskForm):
    password = PasswordField(
        label=lazy_gettext("Neues Passwort"),
        validators=[
            DataRequired(lazy_gettext("Passwort muss angegeben werden!")),
            PasswordComplexity(),
        ]
    )
    password_repeat = PasswordField(
        label=lazy_gettext("Passwort erneut eingeben"),
        validators=[
            DataRequired(lazy_gettext("Passwort muss angegeben werden!")),
            EqualTo("password", lazy_gettext("Passwörter stimmen nicht überein!")),
        ]
    )


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
    months = IntegerField(lazy_gettext("Monate"), default=1,
                          validators=[NumberRange(min=1, message=lazy_gettext(
                              "Muss mindestens 1 Monat sein."))])


class RegisterIdentifyForm(FlaskForm):
    first_name = StrippedStringField(
        label=lazy_gettext("Vorname"),
        validators=[DataRequired(lazy_gettext("Bitte gib deinen Vornamen ein."))]
    )

    last_name = StrippedStringField(
        label=lazy_gettext("Nachname"),
        validators=[DataRequired(lazy_gettext("Bitte gib deinen Nachnamen ein."))]
    )

    birthdate = NativeDateField(
        label=lazy_gettext("Geburtsdatum"),
        validators=[DataRequired(lazy_gettext("Bitte gib dein Geburtsdatum an."))],
        description=lazy_gettext("YYYY-MM-DD (z.B. 1995-10-23)")
    )

    no_swdd_tenant = BooleanField(
        label=lazy_gettext(
            "Ich bin Untermieter oder habe meinen Mietvertrag nicht direkt "
            "vom Studentenwerk Dresden."),
    )

    tenant_number = IntegerField(
        label=lazy_gettext("Debitorennummer (siehe Mietvertrag)"),
        validators=[
            OptionalIf("no_swdd_tenant"),
            OptionalIf("skip_verification"),
            InputRequired(lazy_gettext("Bitte gib deine Debitorennummer ein.")),
            NumberRange(min=0,
                        message=lazy_gettext("Debitorennummer muss eine positive Zahl sein.")),
        ]
    )

    agdsn_history = BooleanField(
        label=lazy_gettext(
            "Ich hatte schon einmal einen Internetanschluss durch die AG\u00a0DSN."),
    )

    previous_dorm = SelectField(
        label=lazy_gettext("Vorheriges Wohnheim"),
        choices=LocalProxy(lambda: [_dorm_summary('', '')] + backends.dormitories_short),
        validators=[
            OptionalIf("agdsn_history", invert=True),
            DataRequired("Bitte vorheriges Wohnheim auswählen."),
        ],
        default='',
    )


class RegisterRoomForm(FlaskForm):
    building = ReadonlyStringField(label=lazy_gettext("Wohnheim"))
    room = ReadonlyStringField(label=lazy_gettext("Raum"))

    move_in_date = NativeDateField(
        label=lazy_gettext("Einzugsdatum"),
        render_kw={'readonly': True, 'required': True}
    )


class RegisterFinishForm(FlaskForm):
    _LOGIN_REGEX = re.compile(r"""
            ^
            # Must begin with a lowercase character
            [a-z]
            # Can continue with lowercase characters, numbers and some punctuation
            # but between punctuation characters must be characters or numbers
            (?:[.-]?[a-z0-9])+$
            """, re.VERBOSE)

    login = StringField(
        label=lazy_gettext("Gewünschter Nutzername"),
        validators=[
            DataRequired(lazy_gettext("Nutzername muss angegeben werden!")),
            Regexp(regex=_LOGIN_REGEX, message=lazy_gettext(
                "Dein Nutzername muss mit einem Kleinbuchstaben beginnen und kann mit "
                "Kleinbuchstaben, Zahlen und Interpunktionszeichen (Punkt und Bindestrich) "
                "fortgesetzt werden, aber es müssen Kleinbuchstaben oder Zahlen zwischen "
                "den Interpunktionszeichen stehen.")),
        ],
        filters=[lower_filter]
    )

    password = PasswordField(
        label=lazy_gettext("Passwort"),
        validators=[
            DataRequired(lazy_gettext("Passwort muss angegeben werden!")),
            PasswordComplexity(),
        ]
    )
    password_repeat = PasswordField(
        label=lazy_gettext("Passwort erneut eingeben"),
        validators=[
            DataRequired(lazy_gettext("Passwort muss angegeben werden!")),
            EqualTo("password", lazy_gettext("Passwörter stimmen nicht überein!")),
        ]
    )
    email = EmailField(label=lazy_gettext("E-Mail-Adresse"))
    email_repeat = EmailField(
        label=lazy_gettext("E-Mail-Adresse erneut eingeben"),
        validators=[EqualTo("email", lazy_gettext("E-Mail-Adressen stimmen nicht überein!"))]
    )

    member_begin_date = NativeDateField(
        label=lazy_gettext("Gewünschter Mitgliedschaftsbeginn"),
        validators=[
            DataRequired(lazy_gettext("Mitgliedschaftsbeginn muss angegeben werden!")),
        ]
    )

    confirm_legal_1 = BooleanField(
        label=lazy_gettext("Ich bestätige, dass meine Angaben korrekt und vollständig sind und ich "
                           "die Vorraussetzungen für die Mitgliedschaft (Student oder Bewohner "
                           "eines Studentenwohnheimes) erfülle."),
        validators=[
            DataRequired(lazy_gettext(
                "Bitte bestätige, dass deine Angaben korrekt sind."))
        ]
    )

    confirm_legal_2 = BooleanField(
        label=lazy_gettext("Ich bestätige, dass ich die [Satzung](constitution) und Ordnungen "
                           "der AG DSN in ihrer jeweils aktuellen Fassung anerkenne, "
                           "insbesondere die [Netzordnungen](network_constitution) "
                           "und die [Beitragsordnung](fee_regulation)."),
        validators=[
            DataRequired(lazy_gettext(
                "Bitte bestätige deine Zustimmung zur Satzung und weiteren Ordnungen."))
        ]
    )

    confirm_legal_3 = BooleanField(
        label=lazy_gettext("Ich habe die [Datenschutzbestimmungen](privacy_policy) verstanden "
                           "und stimme diesen zu."),
        validators=[
            DataRequired(lazy_gettext(
                "Bitte bestätige deine Zustimmung zu der Datenschutzbelehrung."))
        ]
    )


def flash_formerrors(form):
    """If a form is submitted but could not be validated, the routing passes
    the form and this method returns all form errors (form.errors)
    as flash messages.
    """
    for field, errors in list(form.errors.items()):
        for e in errors:
            flash(e, "error")


_LINK_PLACEHOLDER = re.compile(r'\[(?P<text>[^\]]+)\]\((?P<link>[^)]+)\)')


def render_links(raw: str, links: dict):
    """
    Replace link placeholders in label of BooleanFields.

    :param raw: Text that contains the link placeholders.
    :param links: Link placeholder to url mapping.
    """
    def render_link(match: re.Match) -> str:
        link = match.group('link')
        if link in links:
            return f'<a target="_blank" href="{links[link]}">{match.group("text")}</a>'
        else:
            return match.group(0)

    return _LINK_PLACEHOLDER.sub(render_link, raw)
