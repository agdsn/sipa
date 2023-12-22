
import ipaddress

from flask_login import current_user, login_required
from flask import Blueprint, request
from flask_babel import gettext

bp_control = Blueprint('control', __name__, url_prefix='/control')
@bp_control.route("/port", methods=['POST'])
@login_required
def check_port():
    """
    returns json with all the port forwardings
    """
    for i in request.form:
        if not request.form.get(i):
            return 'port nicht in Textfeld'
        if not request.form[i].isnumeric():
            return gettext('der Port muss eine Nummer sein')
        if int(request.form[i]) < 1:
            return gettext('der Port muss größer als 0 sein')
        if int(request.form[i]) > 65535:
            return gettext('der Port muss kleiner als 65536 sein')
    return ""

@bp_control.route("/ip", methods=['POST'])
@login_required
def checks_ip_address():
    """
    checks rather the given ip address is valid
    """

    if not request.form.get("ip_address"):
        return gettext("das Feld muss eine ip addresse enthalten")
    try:
        ip = ipaddress.ip_address(request.form.get("ip_address"))
    except ValueError:
        return gettext("die IP scheint keine valide IP Adresse zu sein")
    network = ipaddress.ip_network("192.168.10.0/24")
    #network = ipaddress.ip_network(f"{getattr(current_user, 'ips').value}/24")
    if ip not in network:
        return gettext("die angegebene IP gehört nicht zu deinem Subnetz")
    return ""

@bp_control.route('/delete', methods=['DELETE'])
def delete():
    """
    returns emtpy string for simple deleting things
    """
    return ""
