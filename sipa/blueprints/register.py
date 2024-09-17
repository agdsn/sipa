"""Blueprint for the online registration.
"""

import logging
from dataclasses import dataclass, asdict
from datetime import date
from functools import wraps

from flask import Blueprint, g, session, url_for, redirect, render_template, flash, request
from flask.globals import current_app
from flask_babel import gettext
from flask_login import current_user
from werkzeug.local import LocalProxy

from sipa.backends.extension import backends, _dorm_summary
from sipa.forms import RegisterIdentifyForm, RegisterRoomForm, RegisterFinishForm
from sipa.model.pycroft.api import PycroftApi, PycroftApiError
from sipa.model.pycroft.exc import PycroftBackendError
from sipa.utils import parse_date

logger = logging.getLogger(__name__)
api: PycroftApi = LocalProxy(lambda: current_app.extensions['pycroft_api'])

bp_register = Blueprint('register', __name__, url_prefix='/register')


@dataclass
class RegisterState:
    # Current step of the registration process
    step: str = 'identify'

    first_name: str = None
    last_name: str = None
    tenant_number: int | None = None
    birthdate: date = None
    no_swdd_tenant: bool = None
    previous_dorm: str | None = None

    move_in_date: date | None = None
    room_id: int | None = None
    building: str | None = None
    room: str | None = None

    skipped_verification: bool = False
    room_confirmed: bool = False

    result: str = None

    def __post_init__(self):
        if isinstance(self.birthdate, str):
            self.birthdate = parse_date(self.birthdate)
        if isinstance(self.move_in_date, str):
            self.move_in_date = parse_date(self.move_in_date)

    @property
    def confirmed_room_id(self):
        return self.room_id if self.room_confirmed else None

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, json: dict):
        return RegisterState(**json) if json is not None else None


@bp_register.before_request
def load_register_state():
    reg_state = session.get('reg_state')
    if reg_state is not None:
        g.reg_state = RegisterState.from_json(reg_state)


@bp_register.after_request
def save_register_state(response):
    if 'reg_state' in g:
        session['reg_state'] = g.reg_state.to_json()
    return response


def register_redirect(func):
    @wraps(func)
    def wrapper_decorator(*args, **kwargs):
        if 'reg_state' not in g:
            g.reg_state = RegisterState()

        endpoint = f'register.{g.reg_state.step}'
        if endpoint != request.endpoint:
            return redirect(url_for(endpoint))

        return func(g.reg_state, *args, **kwargs)

    return wrapper_decorator


def goto_step(step):
    g.reg_state.step = step
    return redirect(url_for(f'.{step}'))


def handle_backend_error(ex: PycroftBackendError):
    flash(gettext('Fehler bei der Kommunikation mit dem Backend-Server. Bitte versuche es erneut.'),
          'error')
    logger.critical(
        'Backend error: %s', ex.backend_name,
        extra={'data': {'exception_args': ex.args}},
        exc_info=True,
    )


@bp_register.route("/")
def landing():
    return redirect("../pages/membership/registration")


@bp_register.route("/identify", methods=['GET', 'POST'])
@register_redirect
def identify(reg_state: RegisterState):
    form = RegisterIdentifyForm()
    form.previous_dorm.choices = [_dorm_summary('', '')] + backends.dormitories_short

    suggest_skip = False
    if form.validate_on_submit():
        reg_state.first_name = form.first_name.data
        reg_state.last_name = form.last_name.data
        reg_state.birthdate = form.birthdate.data
        reg_state.no_swdd_tenant = form.no_swdd_tenant.data
        previous_dorm = backends.get_dormitory(form.previous_dorm.data)
        reg_state.previous_dorm = previous_dorm.display_name if previous_dorm else None

        if form.no_swdd_tenant.data or 'skip_verification' in request.form:
            reg_state.skipped_verification = True
            return goto_step('data')

        try:
            match = api.match_person(form.first_name.data, form.last_name.data,
                                     form.birthdate.data, form.tenant_number.data,
                                     reg_state.previous_dorm)
            reg_state.move_in_date = match.begin
            reg_state.room_id = match.room_id
            reg_state.building = match.building
            reg_state.room = match.room
            reg_state.tenant_number = form.tenant_number.data
            return goto_step('room')
        except PycroftApiError as e:
            if e.code == 'user_exists':
                flash(gettext(
                    'Zu den von dir angegebenen Daten existiert bereits eine Mitgliedschaft. '
                    'Bitte wähle aus, in welchem Wohnheim du vorher gewohnt hast.'), 'error')
            elif e.code == 'similar_user_exists':
                flash(gettext('Für den dir zugeordneten Raum gibt es bereits ein Konto. '
                              'Falls du denkst, dass es sich dabei um einen Fehler handelt, '
                              'kannst du den entsprechenden Button klicken. Die Verifizierung wird '
                              'dann später manuell durchgeführt.'), 'error')
                suggest_skip = True
            elif e.code == 'no_room_for_tenancies':
                reg_state.tenant_number = form.tenant_number.data
                return goto_step('data')
            else:
                flash(gettext(
                    'Die Verifizierung deiner Daten mit dem Studentenwerk Dresden ist fehlgeschlagen. '
                    'Bitte überprüfe, dass du die exakt selben Daten, wie beim Studentenwerk Dresden '
                    'bzw. wie auf deinem Mietvertrag, angegeben hast. '
                    'Um die Verifizierung zu überspringen, kannst du den entsprechenden Button '
                    'klicken. Die Verifizierung wird dann später manuell durchgeführt.'), 'error')
                suggest_skip = True
        except PycroftBackendError as e:
            handle_backend_error(e)

    return render_template('register/identify.html', title=gettext('Identifizierung'), form=form,
                           skip_verification=suggest_skip)


@bp_register.route("/room", methods=['GET', 'POST'])
@register_redirect
def room(reg_state: RegisterState):
    form = RegisterRoomForm()
    if form.validate_on_submit():
        reg_state.room_confirmed = 'wrong_room' not in request.form
        return goto_step('data')
    elif not form.is_submitted():
        form.building.data = reg_state.building
        form.room.data = reg_state.room
        form.move_in_date.data = reg_state.move_in_date

    return render_template('register/room.html', title=gettext('Raumbestätigung'), form=form)


@bp_register.route("/data", methods=['GET', 'POST'])
@register_redirect
def data(reg_state: RegisterState):
    form = RegisterFinishForm()
    form.member_begin_date.min = date.today()
    if form.validate_on_submit():
        try:
            api.member_request(
                email=form.email.data,
                login=form.login.data,
                password=form.password.data,
                first_name=reg_state.first_name,
                last_name=reg_state.last_name,
                birthdate=reg_state.birthdate,
                move_in_date=form.member_begin_date.data,
                tenant_number=reg_state.tenant_number,
                room_id=reg_state.confirmed_room_id,
                previous_dorm=reg_state.previous_dorm)

            return goto_step('finish')
        except PycroftApiError as e:
            if e.code == 'user_exists':
                flash(gettext(
                    'Zu den von dir angegebenen Daten existiert bereits eine Mitgliedschaft.'),
                      'error')
            elif e.code == 'similar_user_exists':
                flash(gettext('Für den dir zugeordneten Raum gibt es bereits eine Mitgliedschaft.'),
                      'error')
            elif e.code == 'email_taken':
                flash(gettext('E-Mail-Adresse ist bereits in Verwendung.'), 'error')
            elif e.code == 'login_taken':
                flash(gettext('Nutzername ist bereits vergeben.'), 'error')
            elif e.code == 'email_illegal':
                flash(gettext("E-Mail-Adresse hat ein ungültiges Format!"), 'error')
            elif e.code == 'login_illegal':
                flash(gettext("Nutzername hat ein ungültiges Format!"), 'error')
            elif e.code == 'move_in_date_invalid':
                flash(gettext("Das Einzugsdatum ist ungültig."), 'error')
            else:
                logger.exception(e)
                logger.error(f"Got unexpected error ({e.code}) from Pycroft: {e.message}")
                flash(gettext('Registrierung aus unbekanntem Grund fehlgeschlagen.'), 'error')
        except PycroftBackendError as e:
            handle_backend_error(e)

    elif not form.is_submitted():
        form.member_begin_date.data = max(reg_state.move_in_date, date.today()) \
            if reg_state.move_in_date is not None else date.today()

    skipped_verification = reg_state.skipped_verification or (reg_state.room_id is not None and not reg_state.room_confirmed)

    if skipped_verification:
        flash(gettext("Du hast die Verifikation übersprungen oder dein Zimmer nicht bestätigt. "
                      "Dadurch kann dein Antrag nicht automatisch bearbeitet werden. "
                      "Eine manuelle Bearbeitung kann mehrere Tage dauern."), 'warning')

    return render_template(
        "register/data.html", title=gettext("Konto erstellen"), form=form
    )


@bp_register.route("/finish")
@register_redirect
def finish(reg_state: RegisterState):
    return render_template('register/finish.html', title=gettext("Bestätigung"))


@bp_register.route("/confirm/<token>")
def confirm(token: str):
    try:
        api_result = api.confirm_email(token)
        if api_result['type'] == 'pre_member':
            # Email confirmation as part of the registration process
            reg_state = g.setdefault('reg_state', RegisterState())
            reg_state.result = api_result['reg_result']
            return goto_step('success')
        else:
            # Regular email confirmation
            flash(gettext('Bestätigung erfolgreich.'), 'success')
            if current_user.is_authenticated:
                return redirect(url_for('usersuite.index'))
            else:
                return redirect(url_for('generic.index'))
    except PycroftApiError:
        flash(gettext('Bestätigung fehlgeschlagen.'), 'error')
        result = gettext(
            'Der Bestätigungslink ist nicht gültig. '
            'Möglicherweise hast du dein Konto bereits bestätigt, '
            'oder der Bestätigungszeitraum ist verstrichen.')
    except PycroftBackendError as e:
        result = gettext('Bestätigung fehlgeschlagen.')
        handle_backend_error(e)

    return render_template('register/confirm.html', title=gettext("Bestätigung"), result=result)


@bp_register.route("/success")
@register_redirect
def success(reg_state: RegisterState):
    return redirect(f'../pages/membership/registration_{reg_state.result}')


@bp_register.route("/cancel")
def cancel():
    g.reg_state = RegisterState()
    return redirect(url_for('generic.index'))


@bp_register.route("/restart")
def restart():
    g.reg_state = RegisterState()
    return goto_step('identify')
