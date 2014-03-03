#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Drupalport auf Python im Zuge der Entwicklung von Pycroft.
Erstellt am 02.03.2014 von Dominik Pataky pataky@wh2.tu-dresden.de
"""

from flask import Flask, render_template
from flask.ext.ldap import LDAP

app = Flask(__name__)
app.secret_key = "q_T_a1C18aizPnA2yf-1Q8(2&,pd5n"

# LDAP config
app.config["LDAP_DOMAIN"] = "atlantis"
app.config["LDAP_SEARCH_BASE"] = "ou=buzz,o=AG DSN,c=de???(|(host=atlantis)(host=exorg))"
app.config["LDAP_PORT"] = 1389
ldap = LDAP(app)
app.add_url_rule("/login", "login", ldap.login, methods=["GET", "POST"])


@app.route('/')
def index():
    return render_template("index.html")

@app.route("/contacts")
def contacts():
    return render_template("content/ansprechpartner.html")

#@app.route("/login")
#def login():
#    pass

if __name__ == "__main__":
    app.run(debug=True, host="localhost")
