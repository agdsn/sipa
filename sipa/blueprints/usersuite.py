#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Blueprint for Usersuite components
"""

from flask import Blueprint, render_template, url_for, redirect, flash
from flask.ext.babel import gettext
from flask.ext.login import current_user, login_required

from model import User
from sipa import logger
from sipa.forms import ContactForm, ChangeMACForm, ChangeMailForm, \
    ChangePasswordForm, flash_formerrors, HostingForm, DeleteMailForm
from model.wu.database_utils import drop_mysql_userdatabase, \
    create_mysql_userdatabase, change_mysql_userdatabase_password
from model.wu.ldap_utils import change_email
from sipa.utils.mail_utils import send_mail
from sipa.utils.exceptions import DBQueryEmpty, LDAPConnectionError, \
    PasswordInvalid, UserNotFound

bp_usersuite = Blueprint('usersuite', __name__, url_prefix='/usersuite')


@bp_usersuite.route("/")
@login_required
def usersuite():
    """Usersuite landing page with user account information
    and traffic overview.
    """
    try:
        # TODO all this should be done by the User() object
        user_info = current_user.get_information()
        traffic_data = current_user.get_traffic_data()
    except DBQueryEmpty as e:
        logger.error('Userinfo DB query could not be finished',
                     extra={'data': {'exception_args': e.args}, 'stack': True})
        flash(gettext(u"Es gab einen Fehler bei der Datenbankanfrage!"),
              "error")
        return redirect(url_for('generic.index'))

    return render_template("usersuite/index.html",
                           userinfo=user_info,
                           usertraffic=traffic_data)


@bp_usersuite.route("/contact", methods=['GET', 'POST'])
@login_required
def usersuite_contact():
    """Contact form for logged in users.
    Currently sends an e-mail to the support mailing list as
    '[Usersuite] Category: Subject' with userid and message.
    """
    form = ContactForm()

    if form.validate_on_submit():
        types = {
            'stoerung': u"Störung",
            'finanzen': u"Finanzen",
            'eigene-technik': u"Eigene Technik"
        }

        cat = types.get(form.type.data, u"Allgemein")

        subject = u"[Usersuite] {0}: {1}".format(cat, form.subject.data)

        message_text = u"Nutzerlogin: {0}\n\n".format(current_user.uid) \
                       + form.message.data

        if send_mail(form.email.data, "support@wh2.tu-dresden.de", subject,
                     message_text):
            flash(gettext(u"Nachricht wurde versandt."), "success")
        else:
            flash(gettext(
                u"Es gab einen Fehler beim Versenden der Nachricht. Bitte "
                u"schicke uns direkt eine E-Mail an support@wh2.tu-dresden.de"),
                "error")
        return redirect(url_for(".usersuite"))
    elif form.is_submitted():
        flash_formerrors(form)

    return render_template("usersuite/contact.html", form=form)


@bp_usersuite.route("/change-password", methods=['GET', 'POST'])
@login_required
def usersuite_change_password():
    """Lets the user change his password.
    Requests the old password once (in case someone forgot to logout for
    example) and the new password two times.

    If the new password was entered correctly twice, LDAP performs a bind
    with the old credentials at the users DN and submits the passwords to
    ldap.passwd_s(). This way every user can edit only his own data.

    Error code "-1" is an incorrect old or empty password.

    TODO: set a minimum character limit for new passwords.
    """
    form = ChangePasswordForm()

    if form.validate_on_submit():
        old = form.old.data
        new = form.new.data

        if new != form.new2.data:
            flash(gettext(u"Neue Passwörter stimmen nicht überein!"), "error")
        else:
            try:
                current_user.change_password(old, new)
            except PasswordInvalid:
                flash(gettext(u"Altes Passwort war inkorrekt!"), "error")
            else:
                flash(gettext(u"Passwort wurde geändert"), "success")
                return redirect(url_for(".usersuite"))
    elif form.is_submitted():
        flash_formerrors(form)

    return render_template("usersuite/change_password.html", form=form)


@bp_usersuite.route("/change-mail", methods=['GET', 'POST'])
@login_required
def usersuite_change_mail():
    """Changes the users forwarding mail attribute
    in his LDAP entry.

    TODO: LDAP schema forbids add/replace 'mail' attribute
    """
    form = ChangeMailForm()

    if form.validate_on_submit():
        password = form.password.data
        email = form.email.data

        try:
            current_user.re_authenticate(password)
            current_user.change_mail(current_user.uid, password, email)
        except UserNotFound:
            flash(gettext(u"Nutzer nicht gefunden!"), "error")
        except PasswordInvalid:
            flash(gettext(u"Passwort war inkorrekt!"), "error")
        except LDAPConnectionError:
            flash(gettext(u"Nicht genügend LDAP-Rechte!"), "error")
        else:
            flash(gettext(u"E-Mail-Adresse wurde geändert"), "success")
            return redirect(url_for('.usersuite'))
    elif form.is_submitted():
        flash_formerrors(form)

    return render_template('usersuite/change_mail.html', form=form)


@bp_usersuite.route("/delete-mail", methods=['GET', 'POST'])
@login_required
def usersuite_delete_mail():
    """Resets the users forwarding mail attribute
    in his LDAP entry.
    """
    form = DeleteMailForm()

    if form.validate_on_submit():
        password = form.password.data

        try:
            change_email(current_user.uid, password, "")
        except UserNotFound:
            flash(gettext(u"Nutzer nicht gefunden!"), "error")
        except PasswordInvalid:
            flash(gettext(u"Passwort war inkorrekt!"), "error")
        except LDAPConnectionError:
            flash(gettext(u"Nicht genügend LDAP-Rechte!"), "error")
        else:
            flash(gettext(u"E-Mail-Adresse wurde zurückgesetzt"), "success")
            return redirect(url_for('.usersuite'))
    elif form.is_submitted():
        flash_formerrors(form)

    return render_template('usersuite/delete_mail.html', form=form)


@bp_usersuite.route("/change-mac", methods=['GET', 'POST'])
@login_required
def usersuite_change_mac():
    """As user, change the MAC address of your device.
    """
    form = ChangeMACForm()
    userinfo = current_user.get_information()

    if form.validate_on_submit():
        password = form.password.data
        mac = form.mac.data

        try:
            # TODO do as told by Sebastian:
            # sowas ist hässlich
            # login_manager.anonymous_user auf eine Klasse setzen, die alle relevanten Sachen implementiert
            # AnonymousUserMixin erben
            if isinstance(current_user, User):
                current_user.re_authenticate(password)

        except PasswordInvalid:
            flash(gettext(u"Passwort war inkorrekt!"), "error")
        else:
            current_user.change_mac_address(userinfo['ip'],
                                            userinfo['mac'],
                                            mac)
            logger.info('Successfully changed MAC address to %s', mac)

            subject = u"[Usersuite] %s hat seine/ihre MAC-Adresse " \
                      u"geändert" % current_user.uid
            message = u"Nutzer %(name)s (%(uid)s) hat seine/ihre MAC-Adresse " \
                      u"geändert.\nAlte MAC: %(old_mac)s\nNeue MAC: %(new_mac)s" % \
                      {'name': current_user.name, 'uid': current_user.uid,
                       'old_mac': userinfo['mac'], 'new_mac': mac}

            if send_mail(current_user.uid + u"@wh2.tu-dresden.de",
                         "support@wh2.tu-dresden.de", subject, message):
                flash(gettext(u"MAC-Adresse wurde geändert!"), "success")
                return redirect(url_for('.usersuite'))
            else:
                flash(gettext(u"Es gab einen Fehler beim Versenden der "
                              u"Nachricht. Bitte schicke uns direkt eine E-Mail"
                              u" an support@wh2.tu-dresden.de"), "error")
                return redirect(url_for('.usersuite'))
    elif form.is_submitted():
        flash_formerrors(form)

    old_mac = userinfo['mac']
    return render_template('usersuite/change_mac.html',
                           form=form, old_mac=old_mac)


@bp_usersuite.route("/hosting", methods=['GET', 'POST'])
@bp_usersuite.route("/hosting/<string:action>", methods=['GET', 'POST'])
@login_required
def usersuite_hosting(action=None):
    """Change various settings for Helios.
    """
    if action == "confirm":
        drop_mysql_userdatabase(current_user.uid)
        flash(gettext(u"Deine Datenbank wurde gelöscht."), "message")
        return redirect(url_for('.usersuite_hosting'))

    form = HostingForm()

    if form.validate_on_submit():
        if form.password1.data != form.password2.data:
            flash(gettext(u"Neue Passwörter stimmen nicht überein!"), "error")
        else:
            if form.action.data == "create":
                create_mysql_userdatabase(current_user.uid, form.password1.data)
                flash(gettext(u"Deine Datenbank wurde erstellt."), "message")
            else:
                change_mysql_userdatabase_password(current_user.uid,
                                                   form.password1.data)
    elif form.is_submitted():
        flash_formerrors(form)

    user_has_db = current_user.has_user_db()

    return render_template('usersuite/hosting.html',
                           form=form, user_has_db=user_has_db, action=action)