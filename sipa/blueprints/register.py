# -*- coding: utf-8 -*-

"""Blueprint for the online registration.
"""

from functools import wraps

from sipa.model.pycroft.api import PycroftApi
from sipa.forms import flash_formerrors, RegisterIdentifyForm, RegisterRoomForm, RegisterFinishForm

from flask import Blueprint, session, url_for, redirect, render_template, flash, request
from flask.globals import current_app
from flask_babel import gettext
from werkzeug import parse_date
from werkzeug.local import LocalProxy

api: PycroftApi = LocalProxy(lambda: current_app.extensions['pycroft_api'])

bp_register = Blueprint('register', __name__, url_prefix='/register')


def register_redirect(func):
    @wraps(func)
    def wrapper_decorator(*args, **kwargs):
        endpoint = None
        if 'user_identity' in session:
            user_identity = session['user_identity']
            if user_identity.get('finished'):
                endpoint = '.finish'
            elif 'room_wrong' in user_identity or user_identity.get('skipped_verification'):
                endpoint = '.data'
            else:
                endpoint = '.room'
        else:
            endpoint = '.identify'

        if endpoint and f'register{endpoint}' != request.endpoint:
            return redirect(url_for(endpoint))

        return func(*args, **kwargs)

    return wrapper_decorator


@bp_register.route("/identify", methods=['GET', 'POST'])
@register_redirect
def identify():
    # Genau wie auf dem Mietvertrag
    form = RegisterIdentifyForm()

    suggest_skip = False
    if form.validate_on_submit():
        user_identity = {
            'first_name': form.first_name.data,
            'last_name': form.last_name.data,
            'birthdate': form.birthdate.data,
            'no_swdd_tenant': form.no_swdd_tenant.data,
        }

        if form.no_swdd_tenant.data or 'skip_verification' in request.form:
            user_identity['skipped_verification'] = True
            session['user_identity'] = user_identity
            return redirect(url_for('.data'))

        status, user_data = api.match_person(form.first_name.data, form.last_name.data,
                                             form.birthdate.data, form.tenant_number.data)
        if status == 200:
            user_identity.update(user_data)
            session['user_identity'] = user_identity
            return redirect(url_for('.room'))
        else:
            flash(gettext(
                'Die Verifizierung deiner Daten mit dem SWDD ist fehlgeschlagen. Bitte überprüfe, dass du die exakt selben Daten wie beim SWDD angegeben hast. Um die Verifizierung zu überspringen, kannst du den entsprechenden Button klicken, die Verifizierung wird dann später manuell durchgeführt.'),
                category='error')
            suggest_skip = True
    elif form.is_submitted():
        flash_formerrors(form)

    return render_template('register/identify.html', title=gettext('Identifizierung'), form=form,
                           skip_verification=suggest_skip)


@bp_register.route("/room", methods=['GET', 'POST'])
@register_redirect
def room():
    user_identity = session['user_identity']
    form = RegisterRoomForm()

    if form.validate_on_submit():
        user_identity['room_wrong'] = form.wrong_room.data
        return redirect(url_for('.data'))
    elif form.is_submitted():
        flash_formerrors(form)
    else:
        form.room.data = user_identity['room']
        form.move_in_date.data = parse_date(user_identity['move_in_date'])

    return render_template('register/form.html', title=gettext('Raumbestätigung'), form=form)


@bp_register.route("/data", methods=['GET', 'POST'])
@register_redirect
def data():
    form = RegisterFinishForm()
    if form.validate_on_submit():
        user_identity = session['user_identity']

        status, result = api.member_request(
            form.email.data, form.login.data, form.password.data, form.start_on_move_in_date.data,
            user_identity['first_name'], user_identity['last_name'],
            parse_date(user_identity['birthdate']),
            user_identity['no_swdd_tenant'], user_identity.get('tenant_number'),
            user_identity.get('skipped_verification', False))

        if status == 200:
            user_identity['finished'] = True
            session.modified = True
            return redirect(url_for('.finish'))
        else:
            flash(gettext('Abschluss der Registrierung fehlgeschlagen'), category='error')

    elif form.is_submitted():
        flash_formerrors(form)

    return render_template('register/form.html', title=gettext('Account erstellen'), form=form)


@bp_register.route("/finish")
@register_redirect
def finish():
    return render_template('register/finish.html', title=gettext("Bestätigung"))


@bp_register.route("/confirm/<token>")
def confirm(token: str):
    status, result = api.confirm_email(token)
    # TODO: Maybe just redirect to one of two sipa content pages...
    if status == 200:
        # Mark state as finished! -> Always redirect to successful content page.
        result = 'Bestätigung erfolgreich.'
    else:
        result = 'Bestätigung fehlgeschlagen.'

    return render_template('register/confirm.html', title=gettext("Bestätigung"), result=result)
