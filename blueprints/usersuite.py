#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Blueprint for Usersuite components
"""

from flask import Blueprint, render_template, url_for, redirect, flash, request
from flask.ext.babel import gettext
from flask.ext.login import login_required, current_user

from forms import ContactForm, ChangeMACForm, ChangeMailForm, \
    ChangePasswordForm, flash_formerrors, HostingForm
from utils import calculate_userid_checksum
from utils.database_utils import query_trafficdata, query_userinfo, \
    update_macaddress, drop_mysql_userdatabase, create_mysql_userdatabase, change_mysql_userdatabase_password, user_has_mysql_db
from utils.ldap_utils import change_password, change_email, authenticate
from utils.mail_utils import send_mail
from utils.exceptions import DBQueryEmpty, LDAPConnectionError, \
    PasswordInvalid, UserNotFound


bp_usersuite = Blueprint('usersuite', __name__, url_prefix='/usersuite')


@bp_usersuite.route("/")
@login_required
def usersuite():
    """Usersuite landing page with user account information
    and traffic overview.
    """
    try:
        userinfo = query_userinfo(current_user.uid)
        userinfo['checksum'] = calculate_userid_checksum(userinfo['id'])
        trafficdata = query_trafficdata(userinfo['ip'])
    except DBQueryEmpty:
        flash(gettext(u"Es gab einen Fehler bei der Datenbankanfrage!"),
              "error")
        return redirect(url_for("index"))

    return render_template("usersuite/index.html",
                           userinfo=userinfo,
                           usertraffic=trafficdata)


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

        cat = form.type.data
        if cat in types.keys():
            cat = types[cat]
        else:
            cat = u"Allgemein"

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
                change_password(current_user.uid, old, new)
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
            change_email(current_user.uid, password, email)
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


@bp_usersuite.route("/change-mac", methods=['GET', 'POST'])
@login_required
def usersuite_change_mac():
    """As user, change the MAC address of your device.
    """
    form = ChangeMACForm()
    userinfo = query_userinfo(current_user.uid)

    if form.validate_on_submit():
        password = form.password.data
        mac = form.mac.data

        try:
            authenticate(current_user.uid, password)
        except PasswordInvalid:
            flash(gettext(u"Passwort war inkorrekt!"), "error")
        else:
            update_macaddress(userinfo['ip'], userinfo['mac'], mac)

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
                              u"Nachricht. Bitte schicke uns direkt eine E-Mail "
                              u"an support@wh2.tu-dresden.de"), "error")
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

    user_has_db = user_has_mysql_db(current_user.uid)

    return render_template('usersuite/hosting.html',
                           form=form, user_has_db=user_has_db, action=action)