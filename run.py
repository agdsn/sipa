#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Drupalport auf Python im Zuge der Entwicklung von Pycroft.
Erstellt am 02.03.2014 von Dominik Pataky pataky@wh2.tu-dresden.de
"""

from flask import Flask, render_template

app = Flask(__name__)
app.secret_key = "q_T_a1C18aizPnA2yf-1Q8(2&,pd5n"


@app.route('/')
def index():
    return render_template('index.html')

@app.route("/contacts")
def contacts():
    return render_template("content/ansprechpartner.html")

if __name__ == "__main__":
    app.run(debug=True, host="localhost")
