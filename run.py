#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Drupalport auf Python im Zuge der Entwicklung von Pycroft.
Erstellt am 02.03.2014 von Dominik Pataky pataky@wh2.tu-dresden.de
"""

import io

from flask import Flask, render_template, request, redirect, \
    url_for, flash, send_file, session
from flask.ext.login import LoginManager, current_user, login_user, \
    logout_user
from flask.ext.babel import Babel, gettext
from sqlalchemy.exc import OperationalError
from ldap import SERVER_DOWN

from blueprints.usersuite import bp_usersuite
from config import languages, busstops
from forms import flash_formerrors, LoginForm
from utils import get_bustimes
from utils.database_utils import query_userinfo, query_trafficdata
from utils.exceptions import UserNotFound, PasswordInvalid, DBQueryEmpty
from utils.graph_utils import make_trafficgraph
from utils.ldap_utils import User, authenticate


app = Flask(__name__)
app.secret_key = "q_T_a1C18aizPnA2yf-1Q8(2&,pd5n"
login_manager = LoginManager()
login_manager.init_app(app)
babel = Babel(app)

# Blueprints
app.register_blueprint(bp_usersuite)


def errorpage(e):
    if e.code in (404,):
        flash(gettext(u"Seite nicht gefunden!"), "warning")
    elif e.code in (401, 403):
        flash(gettext(u"Sie haben nicht die notwendigen Rechte um die Seite zu sehen!"), "warning")
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
    flash(u"Connection to SQL server could not be established!", "error")
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
    flash(u"Connection to LDAP server could not be established!", "error")
    return redirect(url_for('index'))


@login_manager.user_loader
def load_user(username):
    """Loads a User object from/into the session at every request
    """
    return User.get(username)


@babel.localeselector
def babel_selector():
    """Tries to get the language setting from the current session cookie.
    If this fails (if it is not set) the best matching language out of the
    header accept-language is chosen and set.
    """
    lang = session.get('lang')
    if not lang:
        session['lang'] = request.accept_languages.best_match(languages.keys())

    return session.get('lang')


@app.route('/')
def index():
    return render_template("index.html")


@app.route("/contacts")
def contacts():
    return render_template("content/ansprechpartner.html")


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


@app.route("/language/<string:lang>")
def set_language(lang='de'):
    """Set the session language via URL
    """
    session['lang'] = lang
    return redirect(request.referrer)


@app.route("/usertraffic")
def usertraffic():
    """For anonymous users with a valid IP
    """
    try:
        trafficdata = query_trafficdata(request.remote_addr)
    except DBQueryEmpty:
        flash(gettext(u"Deine IP gehört nicht zum Wohnheim!"), "error")
        return redirect(url_for('index'))

    return render_template("usertraffic.html", usertraffic=trafficdata)


@app.route("/traffic.png")
def trafficpng():
    """Create a traffic chart as png binary file and return the binary
    object to the client.

    If the user is not logged in, try to create a graph for the remote IP.
    Fails, if the IP was not recognized.
    """
    if current_user.is_anonymous():
        ip = request.remote_addr
    else:
        userinfo = query_userinfo(current_user.uid)
        ip = userinfo['ip']

    try:
        trafficdata = query_trafficdata(ip)
    except DBQueryEmpty:
        flash(gettext(u"Es gab einen Fehler bei der Datenbankanfrage!"), "error")
        return redirect(url_for('index'))

    traffic_chart = make_trafficgraph(trafficdata)

    return send_file(io.BytesIO(traffic_chart.render_to_png()), "image/png")


@app.route("/bustimes")
@app.route("/bustimes/<string:stopname>")
def bustimes(stopname=None):
    """Queries the VVO-Online widget for the given stop.
    If no specific stop is given in the URL, it will query all
    stops set up in the config.
    """
    data = {}

    if stopname:
        # Only one stop requested
        data[stopname] = get_bustimes(stopname)
    else:
        # General output page
        for stop in busstops:
            data[stop] = get_bustimes(stop, 4)

    return render_template('bustimes.html', times=data, stopname=stopname)


if __name__ == "__main__":
    app.run(debug=True, host="localhost")
