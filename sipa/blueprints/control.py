
from collections import OrderedDict
import logging
from datetime import datetime
import ipaddress

from babel.numbers import format_currency
from flask import Blueprint, render_template, url_for, redirect, flash, abort, request, current_app
from flask_babel import format_date, gettext
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from markupsafe import Markup

bp_control = Blueprint('control', __name__, url_prefix='/control')
@bp_control.route("/port", methods=['GET', 'POST'])
def check_port():
    """
    returns json with all the port forwardings
    """
    if not request.form.get("port"):
        return 'port nicht in Textfeld'
    if not request.form["port"].isnumeric():
        return gettext('der Port muss eine Nummer sein')
    if int(request.form["port"]) < 1:
        return gettext('der Port muss größer als 0 sein')
    if int(request.form["port"]) > 65535:
        return gettext('der Port muss kleiner als 65536 sein')
    return ""

@bp_control.route("/ip", methods=['GET', 'POST'])
def checks_ip_address():
    """
    checks rather the given ip address is valid
    """

    if not request.form.get("source_ip"):
        return "das Feld muss eine ip addresse enthalten"
    try:
        ip = ipaddress.ip_address(request.form.get("source_ip"))
    except ValueError:
        return "die IP scheint keine valide IP Adresse zu sein"
    network = ipaddress.ip_network("192.168.10.0/24")
    if ip not in network:
        return "die angegebene IP gehört nicht zu deinem Subnetz"
    return ""