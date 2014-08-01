#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Drupalport auf Python im Zuge der Entwicklung von Pycroft.
Erstellt am 02.03.2014 von Dominik Pataky pataky@wh2.tu-dresden.de
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from flask.ext.login import LoginManager, current_user, login_user, logout_user, login_required

from authentication import User, authenticate
from forms import ContactForm
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
        return redirect(url_for('index'))

    return render_template('login.html')


@app.route("/usersuite")
@login_required
def usersuite():
    return render_template("usersuite/index.html")


@app.route("/usersuite/contact", methods=['GET', 'POST'])
@login_required
def usersuite_contact():
    form = ContactForm()

    if form.validate_on_submit():
        # Form was submitted _and_ successfully validated.
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
        # If the form was submitted, but could not be validated.
        for field, errors in form.errors.items():
            for e in errors:
                flash(e, "error")

    return render_template("usersuite/contact.html", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="localhost")
