#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Drupalport auf Python im Zuge der Entwicklung von Pycroft.
Erstellt am 02.03.2014 von Dominik Pataky pataky@wh2.tu-dresden.de
"""

from __future__ import absolute_import

from flask import render_template, request, redirect, \
    url_for, flash, session
from flask.ext.babel import gettext
from flask.ext.login import current_user, login_user, logout_user
from sqlalchemy.exc import OperationalError
from ldap import SERVER_DOWN
from werkzeug.routing import IntegerConverter as BaseIntegerConverter

from sipa import app
from sipa.forms import flash_formerrors, LoginForm
from sipa.utils.database_utils import query_trafficdata, \
    user_id_from_ip
from sipa.utils.exceptions import UserNotFound, PasswordInvalid, \
    ForeignIPAccessError
from sipa.utils.ldap_utils import User, authenticate


class IntegerConverter(BaseIntegerConverter):
    """Modification of the standard IntegerConverter which does not support
    negative values. See
    http://werkzeug.pocoo.org/docs/0.10/routing/#werkzeug.routing.IntegerConverter
    """
    regex = r'-?\d+'


app.url_map.converters['int'] = IntegerConverter


def errorpage(e):
    if e.code in (404,):
        flash(gettext(u"Seite nicht gefunden!"), "warning")
    elif e.code in (401, 403):
        flash(gettext(
            u"Du hast nicht die notwendigen Rechte um die Seite zu sehen!"),
            "warning")
    else:
        flash(gettext(u"Es ist ein Fehler aufgetreten!"), "error")
    return redirect(url_for("index"))


app.register_error_handler(401, errorpage)
app.register_error_handler(403, errorpage)
app.register_error_handler(404, errorpage)


@app.errorhandler(OperationalError)
def exceptionhandler_sql(ex):
    """Handles global MySQL errors (server down).
    """
    flash(gettext("Verbindung zum SQL-Server konnte nicht hergestellt werden!"),
          "error")
    # todo check if infinite redirection might still occur
    # Proviously, requesting `/` w/o having a connection to the mysql database
    # would result in an infinite loop of redirects to `/` since
    # OperationalError is being handled globally.
    # In the latter case, the cause was the request of the traffic chart data.
    # A quick fix was catching it and returning an error status.
    return redirect(url_for('index'))


@app.errorhandler(SERVER_DOWN)
def exceptionhandler_ldap(ex):
    """Handles global LDAP SERVER_DOWN exceptions.
    The session must be reset, because if the user is logged in and the server
    fails during his session, it would cause a redirect loop.
    This also resets the language choice, btw.

    The alternative would be a try-except catch block in load_user, but login
    also needs a handler.
    """
    session.clear()
    flash(gettext(
        "Verbindung zum LDAP-Server konnte nicht hergestellt werden!"),
        "error"
    )
    return redirect(url_for('index'))


@app.route("/language/<string:lang>")
def set_language(lang='de'):
    """Set the session language via URL
    """
    session['locale'] = lang
    return redirect(request.referrer)


@app.route('/index.php')
@app.route('/')
def index():
    return redirect(url_for("news.display"))


@app.route("/login", methods=['GET', 'POST'])
def login():
    """Login page for users
    """
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        try:
            user = authenticate(username, password)
        except UserNotFound:
            flash(gettext(u"Nutzer nicht gefunden!"), "error")
        except PasswordInvalid:
            flash(gettext(u"Passwort war inkorrekt!"), "error")
        else:
            if isinstance(user, User):
                login_user(user)
    elif form.is_submitted():
        flash_formerrors(form)

    if current_user.is_authenticated():
        return redirect(url_for('usersuite.usersuite'))

    return render_template('login.html', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/usertraffic")
def usertraffic():
    """For anonymous users with a valid IP
    """
    try:
        ip = request.remote_addr
        trafficdata = query_trafficdata(ip)

        if current_user.is_authenticated():
            if current_user.userid is user_id_from_ip(ip):
                flash(gettext(u"Ein anderer Nutzer als der für diesen Anschluss"
                              u" Eingetragene ist angemeldet!"), "warning")
                flash(gettext("Hier werden die Trafficdaten "
                              "dieses Anschlusses angezeigt"), "info")
    except ForeignIPAccessError:
        flash(gettext(u"Deine IP gehört nicht zum Wohnheim!"), "error")

        if current_user.is_authenticated():
            flash(gettext(u"Da du angemeldet bist, kannst du deinen Traffic "
                          u"hier in der Usersuite einsehen."), "info")
            return redirect(url_for('usersuite.usersuite'))
        else:
            flash(gettext(u"Um deinen Traffic von außerhalb einsehen zu können,"
                          u" musst du dich anmelden."), "info")
            return redirect(url_for('login'))

    # todo test if the template works if called from this position
    return render_template("usertraffic.html", usertraffic=trafficdata)
