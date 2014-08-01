#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Drupalport auf Python im Zuge der Entwicklung von Pycroft.
Erstellt am 02.03.2014 von Dominik Pataky pataky@wh2.tu-dresden.de
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from flask.ext.login import LoginManager, current_user, login_user, logout_user, login_required

from authentication import User, authenticate, change_password
from database import query_userinfo
from forms import flash_formerrors, ContactForm, ChangePasswordForm
from mail import send_mail

app = Flask(__name__)
app.secret_key = "q_T_a1C18aizPnA2yf-1Q8(2&,pd5n"
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(username):
    return User.get(username)


@app.route('/')
def index():
    return render_template("index.html")


@app.route("/contacts")
def contacts():
    return render_template("content/ansprechpartner.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = authenticate(username, password)

        if user == -1:
            flash(u"Nutzer nicht gefunden!", "error")
        elif user == -2:
            flash(u"Passwort war inkorrekt!", "error")
        
        if isinstance(user, User):
            login_user(user)

    if current_user.is_authenticated():
        return redirect(url_for('usersuite'))

    return render_template('login.html')


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/usersuite")
@login_required
def usersuite():
    userinfo = query_userinfo(current_user.uid)
    if userinfo == -1:
        flash(u"Es gab einen Fehler bei der Datenbankanfrage!", "error")
        return redirect(url_for("index"))
    return render_template("usersuite/index.html", userinfo=userinfo)


@app.route("/usersuite/contact", methods=['GET', 'POST'])
@login_required
def usersuite_contact():
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

        if send_mail(form.email.data, "support@wh2.tu-dresden.de", subject, form.message.data):
            flash(u"Nachricht wurde versandt.")
        else:
            flash(u"Es gab einen Fehler beim Versenden der Nachricht. Bitte schicke uns direkt eine E-Mail an org@wh2.tu-dresden.de", "error")
        return redirect(url_for("usersuite"))
    elif form.is_submitted():
        flash_formerrors(form)

    return render_template("usersuite/contact.html", form=form)


@app.route("/usersuite/change-password", methods=['GET', 'POST'])
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
            flash(u"Neue Passwörter stimmen nicht überein!", "error")
        else:
            code = change_password(current_user.uid, old, new)
            if code == -1:
                flash(u"Altes Passwort war inkorrekt!", "error")
            elif code:
                flash(u"Passwort wurde geändert", "success")
                return redirect(url_for("usersuite"))
    elif form.is_submitted():
        flash_formerrors(form)

    return render_template("usersuite/change_password.html", form=form)


if __name__ == "__main__":
    app.run(debug=True, host="localhost")
