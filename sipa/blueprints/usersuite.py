# -*- coding: utf-8 -*-

"""Blueprint for Usersuite components
"""

from collections import OrderedDict
import logging

from flask import Blueprint, render_template, url_for, redirect, flash, abort
from flask_babel import format_date, gettext
from flask_login import current_user, login_required

from sipa.forms import ContactForm, ChangeMACForm, ChangeMailForm, \
    ChangePasswordForm, flash_formerrors, HostingForm, DeleteMailForm, \
    ChangeUseCacheForm
from sipa.mail import send_usersuite_contact_mail
from sipa.utils import password_changeable
from sipa.model.exceptions import DBQueryEmpty, LDAPConnectionError, \
    PasswordInvalid, UserNotFound
from sipa.model.misc import PaymentDetails

logger = logging.getLogger(__name__)

bp_usersuite = Blueprint('usersuite', __name__, url_prefix='/usersuite')


@bp_usersuite.route("/")
@login_required
def index():
    """Usersuite landing page with user account information
    and traffic overview.
    """
    info = current_user.finance_information
    last_update = info.last_update if info else None
    finance_update_string = (
        " ({}: {})".format(gettext("Stand"),
                           format_date(last_update, 'short', rebase=False))
        if last_update
        else ""
    )
    descriptions = OrderedDict([
        ('id', gettext("Nutzer-ID")),
        ('realname', gettext("Voller Name")),
        ('login', gettext("Accountname")),
        ('status', gettext("Mitgliedsschaftsstatus")),
        ('address', gettext("Aktuelles Zimmer")),
        ('ips', gettext("Aktuelle IP-Adresse")),
        ('mac', gettext("Aktuelle MAC-Adresse")),
        ('mail', gettext("E-Mail-Weiterleitung")),
        ('use_cache', gettext("Cache-Nutzung")),
        ('hostname', gettext("Hostname")),
        ('hostalias', gettext("Hostalias")),
        ('userdb_status', gettext("MySQL Datenbank")),
        ('finance_balance', gettext("Kontostand") + finance_update_string),
    ])

    try:
        rows = current_user.generate_rows(descriptions)
    except DBQueryEmpty as e:
        logger.error('Userinfo DB query could not be finished',
                     extra={'data': {'exception_args': e.args}, 'stack': True})
        flash(gettext("Es gab einen Fehler bei der Datenbankanfrage!"),
              "error")
        return redirect(url_for('generic.index'))

    datasource = current_user.datasource
    context = dict(rows=rows,
                   webmailer_url=datasource.webmailer_url,
                   payment_details=render_payment_details(current_user.payment_details()),
                   girocode=generate_epc_qr_code(current_user.payment_details()))

    if current_user.has_connection:
        context.update(
            show_traffic_data=True,
            traffic_user=current_user,
        )

    if info and info.has_to_pay:
        context.update(
            show_transaction_log=True,
            last_update=info.last_update,
            balance=info.balance.raw_value,
            logs=info.history,
        )

    return render_template("usersuite/index.html", **context)


@bp_usersuite.route("/contact", methods=['GET', 'POST'])
@login_required
def contact():
    """Contact form for logged in users.
    Currently sends an e-mail to the support mailing list as
    '[Usersuite] Category: Subject' with userid and message.
    """
    form = ContactForm()

    if form.validate_on_submit():
        types = {
            'stoerung': "Störung",
            'finanzen': "Finanzen",
            'eigene-technik': "Eigene Technik"
        }

        success = send_usersuite_contact_mail(
            category=types.get(form.type.data, "Allgemein"),
            subject=form.subject.data,
            message=form.message.data
        )

        if success:
            flash(gettext("Nachricht wurde versandt."), "success")
        else:
            flash(gettext("Es gab einen Fehler beim Versenden der Nachricht. "
                          "Bitte schicke uns direkt eine E-Mail an {}"
                          .format(current_user.datasource.support_mail)),
                  'error')
        return redirect(url_for('.index'))
    elif form.is_submitted():
        flash_formerrors(form)

    form.email.default = "{uid}@{server}".format(
        uid=current_user.uid,
        server=current_user.datasource.mail_server
    )

    return render_template("usersuite/contact.html", form=form)


def render_payment_details(details: PaymentDetails):
    return {
        gettext("Zahlungsempfänger"): details.recipient,
        gettext("Bank"): details.bank,
        gettext("IBAN"): details.iban,
        gettext("BIC"): details.bic,
        gettext("Verwendungszweck"): details.purpose,
    }


def generate_epc_qr_code(details: PaymentDetails):
    # generate content for epc-qr-code (also known as giro-code)
    return "BCD\n001\n1\nSCT\n{bic}\n{recipient}\n{iban}\nEUR{amount}\n\n\n{purpose}\n\n".format(
        bic=details.bic,
        recipient=details.recipient,
        iban=details.iban,
        amount=5.00,
        purpose=details.purpose)


def get_attribute_endpoint(attribute, capability='edit'):
    """Try to determine the flask endpoint for the according property."""
    if capability == 'edit':
        attribute_mappings = {
            'mac': 'change_mac',
            'userdb_status': 'hosting',
            'mail': 'change_mail',
            'use_cache': 'change_use_cache',
            'finance_balance': 'finance_logs',
        }

        assert attribute in attribute_mappings.keys(), \
            "No edit endpoint for attribute `{}`".format(attribute)
    else:
        assert capability == 'delete', "capability must be 'delete' or 'edit'"

        attribute_mappings = {
            'mail': 'delete_mail',
        }

        assert attribute in attribute_mappings.keys(), \
            "No delete endpoint for attribute `{}`".format(attribute)

    return "{}.{}".format(bp_usersuite.name, attribute_mappings[attribute])


@bp_usersuite.route("/change-password", methods=['GET', 'POST'])
@login_required
@password_changeable(current_user)
def change_password():
    """Frontend page to change the user's password"""
    form = ChangePasswordForm()

    if form.validate_on_submit():
        old = form.old.data
        new = form.new.data

        try:
            current_user.re_authenticate(old)
            current_user.change_password(old, new)
        except PasswordInvalid:
            flash(gettext("Altes Passwort war inkorrekt!"), "error")
        else:
            flash(gettext("Passwort wurde geändert"), "success")
            return redirect(url_for('.index'))
    elif form.is_submitted():
        flash_formerrors(form)

    return render_template("usersuite/change_password.html", form=form)


@bp_usersuite.route("/change-mail", methods=['GET', 'POST'])
@login_required
def change_mail():
    """Frontend page to change the user's mail address"""

    form = ChangeMailForm()

    if form.validate_on_submit():
        password = form.password.data
        email = form.email.data

        try:
            try:
                current_user.mail = email
            except AttributeError:
                with current_user.tmp_authentication(password):
                    current_user.mail = email
        except UserNotFound:
            flash(gettext("Nutzer nicht gefunden!"), "error")
        except PasswordInvalid:
            flash(gettext("Passwort war inkorrekt!"), "error")
        except LDAPConnectionError:
            flash(gettext("Nicht genügend LDAP-Rechte!"), "error")
        else:
            flash(gettext("E-Mail-Adresse wurde geändert"), "success")
            return redirect(url_for('.index'))
    elif form.is_submitted():
        flash_formerrors(form)

    return render_template('usersuite/change_mail.html', form=form)


@bp_usersuite.route("/delete-mail", methods=['GET', 'POST'])
@login_required
def delete_mail():
    """Resets the users forwarding mail attribute
    in his LDAP entry.
    """
    form = DeleteMailForm()

    if form.validate_on_submit():
        password = form.password.data

        try:
            try:
                del current_user.mail
            except AttributeError:
                with current_user.tmp_authentication(password):
                    del current_user.mail
        except UserNotFound:
            flash(gettext("Nutzer nicht gefunden!"), "error")
        except PasswordInvalid:
            flash(gettext("Passwort war inkorrekt!"), "error")
        except LDAPConnectionError:
            flash(gettext("Nicht genügend LDAP-Rechte!"), "error")
        else:
            flash(gettext("E-Mail-Adresse wurde zurückgesetzt"), "success")
            return redirect(url_for('.index'))
    elif form.is_submitted():
        flash_formerrors(form)

    return render_template('usersuite/delete_mail.html', form=form)


@bp_usersuite.route("/change-mac", methods=['GET', 'POST'])
@login_required
def change_mac():
    """As user, change the MAC address of your device.
    """
    form = ChangeMACForm()

    if form.validate_on_submit():
        password = form.password.data
        mac = form.mac.data

        try:
            current_user.re_authenticate(password)

        except PasswordInvalid:
            flash(gettext("Passwort war inkorrekt!"), "error")
        else:
            current_user.mac = mac
            logger.info('Successfully changed MAC address',
                        extra={'data': {'mac': mac},
                               'tags': {'rate_critical': True}})

            flash(gettext("MAC-Adresse wurde geändert!"), 'success')
            flash(gettext("Es kann bis zu 10 Minuten dauern, "
                          "bis die Änderung wirksam ist."), 'info')

            return redirect(url_for('.index'))
    elif form.is_submitted():
        flash_formerrors(form)

    form.mac.default = current_user.mac.value

    return render_template('usersuite/change_mac.html', form=form)


@bp_usersuite.route("/change_use_cache", methods=['GET', 'POST'])
@login_required
def change_use_cache():
    """As user, change your usage of the cache.
    """
    form = ChangeUseCacheForm()

    if form.validate_on_submit():
        use_cache = bool(form.use_cache.data)
        current_user.use_cache = use_cache
        if use_cache:
            flash(gettext("Cache-Nutzung wurde aktiviert!"), 'success')
        else:
            flash(gettext("Cache-Nutzung wurde deaktiviert!"), 'success')
        flash(gettext("Es kann bis zu 10 Minuten dauern, "
                      "bis die Änderung wirksam ist."), 'info')

        return redirect(url_for('.index'))
    elif form.is_submitted():
        flash_formerrors(form)

    return render_template('usersuite/change_use_cache.html', form=form)


@bp_usersuite.route("/hosting", methods=['GET', 'POST'])
@bp_usersuite.route("/hosting/<string:action>", methods=['GET', 'POST'])
@login_required
def hosting(action=None):
    """Change various settings for Helios.
    """
    if action == "confirm":
        current_user.userdb.drop()
        flash(gettext("Deine Datenbank wurde gelöscht."), 'success')
        return redirect(url_for('.hosting'))

    form = HostingForm()

    if form.validate_on_submit():
        if form.action.data == "create":
            current_user.userdb.create(form.password.data)
            flash(gettext("Deine Datenbank wurde erstellt."), 'success')
        else:
            current_user.userdb.change_password(form.password.data)
    elif form.is_submitted():
        flash_formerrors(form)

    try:
        user_has_db = current_user.userdb.has_db
    except NotImplementedError:
        abort(403)

    return render_template('usersuite/hosting.html',
                           form=form, user_has_db=user_has_db, action=action)


@bp_usersuite.route("/finance-logs")
@login_required
def finance_logs():
    return redirect(url_for('usersuite.index', _anchor='transaction-log'))
