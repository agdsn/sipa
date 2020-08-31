# -*- coding: utf-8 -*-
import logging
import os

from flask import render_template, request, redirect, \
    url_for, flash, session, abort, current_app, jsonify
from flask.blueprints import Blueprint
from flask_babel import gettext, format_date
from flask_login import current_user, login_user, logout_user, \
    login_required
from sqlalchemy.exc import DatabaseError

from sipa.backends.exceptions import BackendError
from sipa.forms import flash_formerrors, LoginForm, AnonymousContactForm, \
    OfficialContactForm
from sipa.mail import send_official_contact_mail, send_contact_mail
from sipa.backends.extension import backends
from sipa.units import dynamic_unit, format_money
from sipa.utils import get_user_name, redirect_url
from sipa.model.exceptions import UserNotFound, InvalidCredentials
from sipa.utils.git_utils import get_repo_active_branch, get_latest_commits

logger = logging.getLogger(__name__)

bp_generic = Blueprint('generic', __name__)


@bp_generic.before_app_request
def log_request():
    if 'sentry' in current_app.extensions:
        current_app.extensions['sentry'].client.extra_context({
            'current_user': get_user_name(current_user),
            'ip_user': get_user_name(backends.user_from_ip(request.remote_addr))
        })

    logging.getLogger(__name__ + '.http').debug(
        'Incoming request: %s %s', request.method, request.path,
        extra={'tags': {'user': get_user_name(current_user),
                        'ip': request.remote_addr}}
    )


@bp_generic.app_errorhandler(401)
@bp_generic.app_errorhandler(403)
@bp_generic.app_errorhandler(404)
def error_handler_redirection(e):
    """Handles errors by flashing an according message
    :param e: The error
    :return: A flask response with the according HTTP error code
    """
    if e.code == 401:
        message = gettext("Bitte melde Dich an, um die Seite zu sehen.")
    elif e.code == 403:
        message = gettext("Diese Funktion steht dir derzeit nicht zur Verfügung.")
    elif e.code == 404:
        message = gettext("Das von Dir angeforderte Dokument gibt es nicht.")
    else:
        message = gettext("Es ist ein Fehler aufgetreten!")
    return render_template(
        'error.html',
        errorcode=e.code,
        message=message
    ), e.code


@bp_generic.app_errorhandler(DatabaseError)
def exceptionhandler_sql(ex):
    """Handles global Database errors like:

    Server down, Lock wait timeout exceeded, …
    """
    flash(gettext("Es gab einen Fehler bei der Datenbankabfrage. "
                  "Bitte probiere es in ein paar Minuten noch mal."),
          "error")
    logger.critical('DatabaseError caught',
                    extra={'data': {'exception_args': ex.args}},
                    exc_info=True)
    return redirect(url_for('generic.index'))


@bp_generic.app_errorhandler(BackendError)
def exceptionhandler_backend(ex: BackendError):
    flash(gettext("Fehler bei der Kommunikation mit unserem Server"
                  " (Backend '%(name)s')", name=ex.backend_name),
          'error')
    logger.critical(
        'Backend error: %s', ex.backend_name,
        extra={'data': {'exception_args': ex.args}},
        exc_info=True,
    )
    return redirect(url_for('generic.index'), 302)


@bp_generic.route('/index.php')
@bp_generic.route('/')
def index():
    return redirect(url_for('news.show'))


@bp_generic.route("/login", methods=['GET', 'POST'])
def login():
    """Login page for users
    """
    form = LoginForm()

    if form.validate_on_submit():
        dormitory = backends.get_dormitory(form.dormitory.data)
        username = form.username.data
        password = form.password.data
        remember = form.remember.data
        User = dormitory.datasource.user_class

        valid_suffix = "@{}".format(dormitory.datasource.mail_server)

        if username.endswith(valid_suffix):
            username = username[:-len(valid_suffix)]

        try:
            user = User.authenticate(username, password)
        except InvalidCredentials as e:
            cause = "username" if isinstance(e, UserNotFound) else "password"
            logger.info("Authentication failed: Wrong %s", cause, extra={
                'tags': {'user': username, 'rate_critical': True}
            })
            flash(gettext("Anmeldedaten fehlerhaft!"), "error")
        else:
            if isinstance(user, User):
                session['dormitory'] = dormitory.name
                login_user(user, remember=remember)
                logger.info('Authentication successful',
                            extra={'tags': {'user': username}})
                flash(gettext("Anmeldung erfolgreich!"), "success")
    elif form.is_submitted():
        flash_formerrors(form)

    if current_user.is_authenticated:
        # `url_redirect` would not be bad here because this would allow for URL
        # injection using the `next` parameter
        return redirect(url_for('usersuite.index'))

    return render_template('login.html', form=form,
                           unsupported=backends.premature_dormitories)


@bp_generic.route("/logout")
@login_required
def logout():
    logger.info("Logging out",
                extra={'tags': {'user': current_user.uid}})
    logout_user()
    flash(gettext("Abmeldung erfolgreich!"), 'success')
    return redirect(url_for('.index'))


bp_generic.add_app_template_filter(dynamic_unit, name='unit')


@bp_generic.app_template_filter('gib')
def to_gigabytes(number):
    """Convert a number from KiB to GiB

    This is used mainly for the gauge, everything else uses the dynamic
    `unit` function.
    """
    return number / 1024 ** 2


@bp_generic.app_template_filter('date')
def jinja_format_date(date):
    return format_date(date)


bp_generic.add_app_template_filter(format_money, name='money')


@bp_generic.route("/usertraffic")
def usertraffic():
    """Show a user's traffic on a static site just as in the usersuite.

    If a user is logged but the ip corresponds to another user, a hint
    is flashed and the traffic of the `ip_user` is displayed.
    """
    ip_user = backends.user_from_ip(request.remote_addr)

    chosen_user = None

    if current_user.is_authenticated:
        chosen_user = current_user
        if not current_user.has_connection and not ip_user.is_authenticated:
            flash(gettext("Aufgrund deines Nutzerstatus kannst Du "
                          "keine Trafficdaten einsehen."), "info")
            return redirect(url_for('generic.index'))

    if ip_user.is_authenticated:
        chosen_user = ip_user

        if current_user.is_authenticated:
            if current_user != ip_user:
                flash(gettext("Ein anderer Nutzer als der für diesen "
                              "Anschluss Eingetragene ist angemeldet!"),
                      'warning')
                flash(gettext("Hier werden die Trafficdaten "
                              "dieses Anschlusses angezeigt."), "info")

    if chosen_user:
        user_id = chosen_user.id.value if chosen_user.id.supported else None
        return render_template("usertraffic.html",
                               user_id=user_id,
                               traffic_user=chosen_user)

    abort(401)


@bp_generic.route('/usertraffic/json')
def traffic_api():
    user = (current_user if current_user.is_authenticated
            else backends.user_from_ip(request.remote_addr))

    if not user.is_authenticated:
        return jsonify(version=0)

    traffic_history = ({
        'in': x['input'],
        'out': x['output'],
    } for x in reversed(user.traffic_history))

    trafficdata = {
        # `next` gets the first entry (“today”)
        'traffic': next(traffic_history),
        'history': list(traffic_history),
    }

    return jsonify(version=3, **trafficdata)


@bp_generic.route('/contact', methods=['GET', 'POST'])
def contact():
    form = AnonymousContactForm()

    if form.validate_on_submit():
        success = send_contact_mail(
            author=form.email.data,
            subject=form.subject.data,
            name=form.name.data,
            message=form.message.data,
            dormitory_name=form.dormitory.data,
        )

        if success:
            flash(gettext("Nachricht wurde versandt."), "success")
        else:
            flash(gettext("Es gab einen Fehler beim Versenden der Nachricht."),
                  'error')
        return redirect(url_for('.index'))
    elif form.is_submitted():
        flash_formerrors(form)
    elif current_user.is_authenticated:
        flash(gettext("Sicher, dass Du das anonyme Formular "
                      "benutzen möchtest? Dies ist nur erforderlich, wenn Du "
                      "Administratoren eines anderen Wohnheims "
                      "kontaktieren willst."), 'info')

    return render_template('anonymous_contact.html', form=form)


@bp_generic.route('/contact_official', methods=['GET', 'POST'])
def contact_official():
    form = OfficialContactForm()

    if form.validate_on_submit():
        success = send_official_contact_mail(
            author=form.email.data,
            subject=form.subject.data,
            name=form.name.data,
            message=form.message.data,
        )

        if success:
            flash(gettext("Nachricht wurde versandt."), "success")
        else:
            flash(gettext("Es gab einen Fehler beim Versenden der Nachricht."),
                  'error')
        return redirect(url_for('.index'))
    elif form.is_submitted():
        flash_formerrors(form)

    return render_template(
        'official_contact.html',
        form=form
    )


@bp_generic.route('/version')
def version():
    """ Display version information from local repo """
    sipa_dir = os.getcwd()
    return render_template(
        'version.html',
        active_branch=get_repo_active_branch(sipa_dir),
        commits=get_latest_commits(sipa_dir, 20),
    )
