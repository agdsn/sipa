"""Blueprint for Usersuite components
"""
import logging
import math
import typing as t
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from io import BytesIO

from babel.numbers import format_currency
from fastapi import APIRouter, HTTPException, Response
from fastapi.datastructures import URL
from fastapi.responses import HTMLResponse
from fastapi_babel import _
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_babel import gettext
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from markupsafe import Markup
from starlette.requests import Request
from wtforms import IntegerField
from wtforms.validators import NumberRange
from wtforms_widgets.fields.core import TextAreaField

from sipa.forms import (
    ActivateNetworkAccessForm,
    ChangeMACForm,
    ChangeMailForm,
    ChangePasswordForm,
    ContactForm,
    ContinueMembershipForm,
    DeleteMPSKClientForm,
    HostingForm,
    MPSKClientForm,
    PaymentForm,
    StrippedStringField,
    TerminateMembershipConfirmForm,
    TerminateMembershipForm,
)
from sipa.mail import send_usersuite_contact_mail
from sipa.model.exceptions import (
    ContinuationNotPossible,
    MacAlreadyExists,
    MaximumNumberMPSKClients,
    NoWiFiPasswordGenerated,
    PasswordInvalid,
    SubnetFull,
    TerminationNotPossible,
    UnknownError,
    UserNotFound,
)
from sipa.model.misc import UserPaymentDetails
from sipa.model.mspk_client import MPSKClientEntry
from sipa.units import format_money
from sipa.utils import password_changeable, subscribe_to_status_page

from ..deps import Settings, Templates, User
from ..warnings import jinja_warn

logger = logging.getLogger(__name__)

bp_usersuite = Blueprint('usersuite', __name__, url_prefix='/usersuite')
router_usersuite = APIRouter(prefix='/usersuite', default_response_class=HTMLResponse)


def capability_or_403(active_property, capability):
    # prop: ActiveProperty = getattr(current_user, active_property)
    # if not getattr(prop.capabilities, capability):
    #     abort(403)
    return


def get_mpsk_client_or_404(mpsk_id: int) -> MPSKClientEntry:
    # for client in t.cast(User, current_user).mpsk_clients:
    #     if client.id == mpsk_id:
    #         return client
    abort(404)


@bp_usersuite.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Usersuite landing page with user account information
    and traffic overview.
    """
    rows = rows_from_user(current_user)
    payment_form = PaymentForm()
    if payment_form.validate_on_submit():
        months = payment_form.months.data
    else:
        months = payment_form.months.default

    months_field = t.cast(IntegerField, payment_form._fields["months"])
    validator = t.cast(NumberRange, months_field.validators[0])
    validator.max = math.floor(
        # Maximum value for EPC QR code, see https://de.wikipedia.org/wiki/EPC-QR-Code#EPC-QR-Code_Dateninhalt
        Decimal("999999999.99")
        / current_app.config["MEMBERSHIP_CONTRIBUTION"]
        * 100
    )

    datasource = current_user.datasource
    context = dict(rows=rows,
                   webmailer_url=datasource.webmailer_url,
                   terminate_membership_url=url_for('.terminate_membership'),
                   continue_membership_url=url_for('.continue_membership'),
                   payment_details=render_payment_details(current_user.payment_details(),
                                                          months),
                   girocode=generate_epc_qr_code(current_user.payment_details(), months))

    if current_user.has_connection:
        context.update(
            show_traffic_data=True,
            traffic_user=current_user,
        )

    if info and info.has_to_pay:
        context.update(
            show_transaction_log=True,
            last_update=info.last_update,
            balance=info.balance.raw_value,
            logs=info.history,
        )

    return render_template("usersuite/index.html", payment_form=payment_form, **context)


@dataclass(frozen=True)
class Row:
    desc: str
    value: str | None = None
    description_url: str | None = None
    subtext: str | None = None
    style: str | None = None
    copyable: bool = False
    add_url: URL | None = None
    edit_url: URL | None = None
    delete_url: URL | None = None


def rows_from_user(user: User, r: Request) -> t.Iterable[Row]:
    # TODO push most of that in the view itself!
    def format_date(date, format: t.Literal["long", "short"], **_kw) -> str:
        jinja_warn("used legacy flask_babel `dateformat` filter")
        return f"{date}"

    yield Row(_("Nutzer-ID"), user.id)
    yield Row(_("Voller Name"), user.realname)
    yield Row(_("Nutzername"), user.login)

    status, status_style = user.status
    yield Row(_("Mitgliedschaftsstatus"), status, style=status_style)
    yield Row(_("Aktuelles Zimmer"), user.address)
    yield Row(_("Aktuelle IP-Adresse"), ", ".join(user.ips))

    yield Row(
        _("Aktuelle MAC-Adresse"),
        ", ".join(user.macs),
        subtext=_("Die MAC Adresse des per Kabel verbundenen Gerätes"),
        edit_url=r.url_for("usersuite.change_mac") if user.can_edit_mac else None,
        add_url=r.url_for("usersuite.change_mac") if user.can_add_mac else None,
    )

    yield Row(
        _("E-Mail-Adresse"),
        user.mail or "",
        edit_url=r.url_for("usersuite.change_mail") if user.can_edit_mail else None,
    )
    yield Row(
        _("Status deiner E-Mail-Adresse"),
        gettext("Bestätigt") if user.mail_confirmed else gettext("Nicht bestätigt"),
        style="success" if user.mail_confirmed else "danger",
        edit_url=r.url_for("usersuite.resend_confirm_mail") if user.can_edit_mail else None,
    )
    yield Row(
        _("E-Mail-Weiterleitung"),
        gettext("Aktiviert") if user.mail_forwarded else gettext("Nicht aktiviert"),
        edit_url=r.url_for("usersuite.change_mail") if user.can_change_mail_forwarded else None,
    )

    yield Row(
        _("WLAN Passwort"),
        user.wifi_password,
        style="password" if user.wifi_password is not None else None,
        subtext=_("Clicken um Passwort zu Kopieren!"),
        description_url="../pages/service/wlan",
        copyable=True,
    )

    yield Row(
        _("WLAN MPSK Clients"),
        str(len(user.mpsk_clients)) if user.mpsk_clients else None,
        subtext=_("Für Geräte die kein WPA-Enterprise Unterstützen"),
        edit_url=r.url_for("usersuite.view_mpsk")
    )

    if (db := user.userdb) is not None:
        desc = _("MySQL Datenbank")
        match db.has_db:
            case None:
                yield Row(desc, _("Datenbank nicht erreichbar"), style="danger")
            case True:
                yield Row(desc, _("Aktiviert"), style="success",
                          delete_url=r.url_for("usersuite.hosting"))
            case False:
                yield Row(desc, _("Nicht aktiviert"), style="muted",
                          add_url=r.url_for("usersuite.hosting"))

    info = user.finance_information
    yield Row(
        _("Kontostand")
        + (
            " ({}: {})".format(_("Stand"), format_date(info.last_update, "short", rebase=False))
            if info.last_update
            else ""
        ),
        format_money(info.balance),
        subtext=_("Eingegangene Zahlung")
        + ": "
        + (
            # TODO use proper `format_date`
            format_date(info.last_received_update, "short", rebase=False)
            if info.last_received_update
            else ""
        ),
    )


@router_usersuite.get("/", name="usersuite.index")
@router_usersuite.post("/", name="usersuite.index")
def index_(r: Request, tp: Templates, s: Settings, user: User) -> HTMLResponse:
    class FakePaymentForm:
        csrf_token = ""

        def months(*a, **kw):
            return Markup("""<input type="number" class="form-control" value=6></input>""")

    return tp.TemplateResponse(
        r,
        "usersuite/index.html",
        context={
            "rows": rows_from_user(user, r),
            "payment_form": FakePaymentForm(),
            "payment_details": render_payment_details(
                user.payment_details, months=6, contribution=s.membership_contribution_cents
            ),
            "finance_information": user.finance_information,
            "traffic_history": user.traffic_history,
        },
    )


@bp_usersuite.route("/contact", methods=['GET', 'POST'])
@login_required
def contact():
    """Contact form for logged in users.
    Currently sends an e-mail to the support e-mail address
    '[Usersuite] Category: Subject' with userid and message.
    """
    form = ContactForm()

    if form.validate_on_submit():
        types = {
            'stoerung': "Störung",
            'finanzen': "Finanzen",
            'eigene-technik': "Eigene Technik"
        }
        subj = t.cast(StrippedStringField, form.subject).data
        assert subj is not None
        msg = t.cast(TextAreaField, form.message).data
        assert msg is not None
        success = send_usersuite_contact_mail(
            author=form.email.data,
            category=types.get(form.type.data, "Allgemein"),
            subject=subj,
            message=msg,
            user=t.cast(User, current_user),
        )

        if success:
            flash(gettext("Nachricht wurde versandt."), "success")
        else:
            flash(gettext("Es gab einen Fehler beim Versenden der Nachricht. "
                          "Bitte schicke uns direkt eine E-Mail an {}")
                          .format(current_user.datasource.support_mail),
                  'error')
        return redirect(url_for('.index'))

    form.email.default = current_user.mail.raw_value

    return render_template("usersuite/contact.html",
                           form_args={'form': form,
                                      'reset_button': True,
                                      'cancel_to': url_for('.index')})


@router_usersuite.get("/contact", name="usersuite.contact")
@router_usersuite.post("/contact", name="usersuite.contact")
def contact_(r: Request, tp: Templates, user: User) -> HTMLResponse:
    return HTMLResponse("STUB")


@bp_usersuite.route("/subscribe", methods=['GET'])
@login_required
def subscribe():
    """Route to subscribe to statuspage"""

    email = current_user.mail.raw_value
    if email == "":
        email = f"{current_user.login.raw_value}@agdsn.me"

    result = subscribe_to_status_page(
        current_app.config['STATUS_PAGE_API_SUBSCRIBE_ENDPOINT'],
        current_app.config['STATUS_PAGE_API_TOKEN'],
        current_app.config['STATUS_PAGE_REQUEST_TIMEOUT'],
        email,
    )
    if result is None:
        flash(gettext("Es ist ein Fehler aufgetreten!"), "error")
    elif result:
        flash(gettext("Deine E-Mail Adresse ({}) wurde zur Status-Page hinzugefügt. Du bekommst "
                      "eine E-Mail mit weiteren Details.").format(email), "success")
    else:
        flash(gettext("Du hast die Statuspage bereits abonniert."), "warning")

    return redirect(url_for('.index'))


@router_usersuite.get("/subscribe", name="usersuite.subscribe")
@router_usersuite.post("/subscribe", name="usersuite.subscribe")
def subscribe_(r: Request, tp: Templates, user: User) -> HTMLResponse:
    # TODO remove these `raw_value` shenanigans
    email = user.mail or f"{user.login}@agdsn.me"
    return HTMLResponse("STUB")


def render_payment_details(details: UserPaymentDetails, months, contribution: int | None = None):
    contrib = contribution or current_app.config["MEMBERSHIP_CONTRIBUTION"]
    return {
        gettext("Zahlungsempfänger"): details.recipient,
        gettext("Bank"): details.bank,
        gettext("IBAN"): details.iban,
        gettext("BIC"): details.bic,
        gettext("Verwendungszweck"): details.purpose,
        gettext("Betrag"): format_currency(
            Decimal(months) * contrib / 100,
            "EUR",
            locale="de_DE",
        ),
    }


def generate_epc_qr_code(details: UserPaymentDetails, months):
    # generate content for epc-qr-code (also known as giro-code)
    EPC_FORMAT = \
        "BCD\n001\n1\nSCT\n{bic}\n{recipient}\n{iban}\nEUR{amount}\n\n\n{purpose}\n\n"

    return EPC_FORMAT.format(
        bic=details.bic.replace(' ', ''),
        recipient=details.recipient,
        iban=details.iban.replace(' ', ''),
        amount=months * current_app.config['MEMBERSHIP_CONTRIBUTION'] / 100,
        purpose=details.purpose)


# TODO just remove this and hard-code
def get_attribute_endpoint(attribute, capability='edit'):
    """Try to determine the flask endpoint for the according property."""
    if capability == 'edit':
        attribute_mappings = {
            'mac': 'change_mac' if current_user.network_access_active.raw_value else 'activate_network_access',
            'userdb_status': 'hosting',
            'mail': 'change_mail',
            'mail_forwarded': 'change_mail',
            'mail_confirmed': 'resend_confirm_mail',
            'wifi_password': 'reset_wifi_password',
            'finance_balance': 'finance_logs',
            'mpsk_clients': "view_mpsk",
        }

        assert attribute in attribute_mappings.keys(), \
            f"No edit endpoint for attribute `{attribute}`"
    else:
        assert capability == 'delete', "capability must be 'delete' or 'edit'"

        attribute_mappings = {
            'userdb_status': 'hosting',
        }

        assert attribute in attribute_mappings.keys(), \
            f"No delete endpoint for attribute `{attribute}`"

    return f"{bp_usersuite.name}.{attribute_mappings[attribute]}"


@bp_usersuite.route("/change-password", methods=['GET', 'POST'])
@login_required
@password_changeable(current_user)
def change_password():
    """Frontend page to change the user's password"""
    form = ChangePasswordForm()

    if form.validate_on_submit():
        old = form.old.data
        new = form.new.data

        try:
            current_user.change_password(old, new)
        except PasswordInvalid:
            flash(gettext("Altes Passwort war inkorrekt!"), "error")
        else:
            flash(gettext("Passwort wurde geändert"), "success")
            return redirect(url_for('.index'))

    return render_template("generic_form.html", page_title=gettext("Passwort ändern"),
                           form_args={'form': form, 'reset_button': True, 'cancel_to': url_for('.index')})


@router_usersuite.get("/change_password", name="usersuite.change_password")
@router_usersuite.post("/change_password", name="usersuite.change_password")
def change_password_(r: Request, tp: Templates, user: User) -> HTMLResponse:
    return HTMLResponse("STUB")


@bp_usersuite.route("/change-mail", methods=['GET', 'POST'])
@login_required
def change_mail():
    """Frontend page to change the user's mail address"""

    capability_or_403('mail', 'edit')

    form = ChangeMailForm()

    if form.validate_on_submit():
        password = form.password.data
        email = form.email.data

        try:
            current_user.change_mail(
                password=password,
                new_mail=email,
                mail_forwarded=form.forwarded.data,
            )
        except UserNotFound:
            flash(gettext("Nutzer nicht gefunden!"), "error")
        except PasswordInvalid:
            flash(gettext("Passwort war inkorrekt!"), "error")
        else:
            flash(gettext("E-Mail-Adresse wurde geändert"), "success")
            return redirect(url_for('.index'))
    elif not form.is_submitted():
        form.email.data = current_user.mail.raw_value
        form.forwarded.data = current_user.mail_forwarded.raw_value

    return render_template('generic_form.html',
                           page_title=gettext("E-Mail-Adresse ändern"),
                           form_args={'form': form, 'cancel_to': url_for('.index')})


@router_usersuite.get("/change_mail", name="usersuite.change_mail")
@router_usersuite.post("/change_mail", name="usersuite.change_mail")
def change_mail_(r: Request, tp: Templates, user: User) -> HTMLResponse:
    return HTMLResponse("STUB")


@bp_usersuite.route("/resend-confirm-mail", methods=['GET', 'POST'])
@login_required
def resend_confirm_mail():
    """Frontend page to resend confirmation mail"""

    capability_or_403('mail', 'edit')

    form = FlaskForm()

    if form.validate_on_submit():
        if current_user.resend_confirm_mail():
            logger.info('Successfully resent confirmation mail',
                        extra={'tags': {'rate_critical': True}})
            flash(gettext('Wir haben dir eine E-Mail mit einem Bestätigungslink geschickt.'), 'success')
        else:
            flash(gettext('Versenden der Bestätigungs-E-Mail ist fehlgeschlagen!'), 'error')

        return redirect(url_for('.index'))

    form_args = {
        'form': form,
        'cancel_to': url_for('.index'),
        'submit_text': gettext('E-Mail mit Bestätigungslink erneut senden')
    }

    return render_template('generic_form.html',
                           page_title=gettext("Bestätigung deiner E-Mail-Adresse"),
                           form_args=form_args)


@router_usersuite.get("/resend_confirm_mail", name="usersuite.resend_confirm_mail")
@router_usersuite.post("/resend_confirm_mail", name="usersuite.resend_confirm_mail")
def resend_confirm_mail_(r: Request, tp: Templates, user: User) -> HTMLResponse:
    return HTMLResponse("STUB")


@bp_usersuite.route("/change-mac", methods=['GET', 'POST'])
@login_required
def change_mac():
    """As user, change the MAC address of your device.
    """

    capability_or_403('mac', 'edit')

    form = ChangeMACForm()

    if form.validate_on_submit():
        password = form.password.data
        mac = form.mac.data
        host_name = form.host_name.data

        try:
            current_user.change_mac_address(mac, host_name, password)
        except PasswordInvalid:
            flash(gettext("Passwort war inkorrekt!"), "error")
        except MacAlreadyExists:
            flash(gettext("MAC-Adresse ist bereits in Verwendung!"), "error")
        else:
            logger.info('Successfully changed MAC address',
                        extra={'data': {'mac': mac},
                               'tags': {'rate_critical': True}})

            flash(gettext("MAC-Adresse wurde geändert!"), 'success')
            flash(gettext("Es kann bis zu 15 Minuten dauern, "
                          "bis die Änderung wirksam ist."), 'info')

            return redirect(url_for('.index'))

    form.mac.default = current_user.mac.value

    return render_template('usersuite/change_mac.html',
                           form_args={'form': form, 'cancel_to': url_for('.index')})


@router_usersuite.get("/change_mac", name="usersuite.change_mac")
@router_usersuite.post("/change_mac", name="usersuite.change_mac")
def change_mac_(r: Request, tp: Templates, user: User) -> HTMLResponse:
    return HTMLResponse("STUB")


@bp_usersuite.route("/change-mpsk/<int:mpsk_id>", methods=['GET', 'POST'])
@login_required
def change_mpsk(mpsk_id: int):
    """Changes the WiFi MPSK MAC address of a device
    """
    capability_or_403('mpsk_clients', 'edit')

    form = MPSKClientForm()
    mpsk_client = get_mpsk_client_or_404(mpsk_id)
    if form.validate_on_submit():
        password = form.password.data
        mac = form.mac.data
        name = form.name.data
        try:
            current_user.change_mpsk_clients(
                mac=mac, name=name, mpsk_id=mpsk_id, password=password
            )
        except PasswordInvalid:
            flash(gettext("Passwort war inkorrekt!"), "error")
        except ValueError:
            flash(gettext("MPSK Gerät nicht gefunden!"), "error")
        except MacAlreadyExists:
            flash(gettext("MAC-Adresse ist bereits in Verwendung!"), "error")
        else:
            logger.info('Successfully changed MAC address',
                        extra={'data': {'mac': mac},
                               'tags': {'rate_critical': True}})

            flash(gettext("MAC-Adresse wurde geändert!"), "success")
            flash(
                gettext(
                    "Es kann bis zu 15 Minuten dauern, " "bis die Änderung wirksam ist."
                ),
                "info",
            )

            return redirect(url_for(".view_mpsk"))

    form.mac.data = mpsk_client.mac
    form.name.data = mpsk_client.name

    return render_template(
        "usersuite/change_mac.html",
        form_args={"form": form, "cancel_to": url_for(".view_mpsk")},
    )


@bp_usersuite.route("/add-mpsk", methods=['GET', 'POST'])
@login_required
def add_mpsk():
    """As user, adds a mpsk devices MAC address for WiFi
    """

    capability_or_403('mpsk_clients', 'edit')

    form = MPSKClientForm()

    if form.validate_on_submit():
        password = form.password.data
        mac = form.mac.data
        name = form.name.data

        try:
            device = current_user.add_mpsk_client(mac, name, password)
        except PasswordInvalid:
            flash(gettext("Passwort war inkorrekt!"), "error")
        except MacAlreadyExists:
            flash(gettext("MAC-Adresse ist bereits in Verwendung!"), "error")
        except ValueError:
            flash(gettext("Invalide Mac Adresse!"), "error")
        except MaximumNumberMPSKClients:
            flash(gettext("Maximale Anzahl an MPSK Clients bereits erstellt!"), "error")
        except NoWiFiPasswordGenerated:
            flash(gettext("Bevor MPSK Clients angelegt werden können muss ein WiFi Passwort erstellt werden!"), "error")

        else:
            logger.info('Successfully changed MAC address',
                        extra={'data': {'mac': mac},
                               'tags': {'rate_critical': True}})

            flash(gettext("MAC-Adresse wurde geändert!"), "success")
            flash(
                gettext(
                    "Es kann bis zu 15 Minuten dauern, " "bis die Änderung wirksam ist."
                ),
                "info",
            )
            current_user.mpsk_clients.value.append(device)
            return redirect(url_for(".view_mpsk"))

    return render_template(
        "usersuite/mpsk_client.html",
        form_args={"form": form, "cancel_to": url_for(".view_mpsk")},
    )


@bp_usersuite.route("/delete-mpsk/<int:mpsk_id>", methods=["GET", "POST"])
@login_required
def delete_mpsk(mpsk_id: int):

    capability_or_403('mpsk_clients', 'edit')
    get_mpsk_client_or_404(mpsk_id)
    form = DeleteMPSKClientForm()

    if form.validate_on_submit():
        password = form.password.data
        # mac = form.mac.data
        try:
            logging.warning(f"MPSK: {mpsk_id}")
            current_user.delete_mpsk_client(mpsk_id, password)
        except PasswordInvalid:
            flash(gettext("Passwort war inkorrekt!"), "error")
        except ValueError:
            flash(gettext("MPSK MAC wurde nicht gefunden!"), "error")
        else:
            flash(gettext("MPSK Client wurde gelöscht!"), 'success')

            return redirect(url_for('.view_mpsk'))

    # form.mac.data = request.args.get('mac')
    return render_template('usersuite/mpsk_client.html',
                           form_args={'form': form, 'cancel_to': url_for('.view_mpsk')})


@router_usersuite.get("/view-mpsk_clients", name="usersuite.view_mpsk")
@router_usersuite.post("/view-mpsk_clients")
def view_mpsk(r: Request, tp: Templates, user: User):
    return tp.TemplateResponse(r, "usersuite/mpsk_table.html", {"clients": user.mpsk_clients})


@bp_usersuite.route("/activate-network-access", methods=['GET', 'POST'])
@login_required
def activate_network_access():
    """As user, activate your network access
    """

    capability_or_403('network_access_active', 'edit')

    form = ActivateNetworkAccessForm(birthdate=current_user.birthdate)

    if form.validate_on_submit():
        password = form.password.data
        mac = form.mac.data
        birthdate = form.birthdate.data
        host_name = form.host_name.data

        try:
            current_user.activate_network_access(password, mac, birthdate, host_name)
        except PasswordInvalid:
            flash(gettext("Passwort war inkorrekt!"), "error")
        except MacAlreadyExists:
            flash(gettext("MAC-Adresse ist bereits in Verwendung!"), "error")
        except SubnetFull:
            flash(gettext("Es sind nicht mehr genug freie IPv4 Adressen verfügbar. Bitte kontaktiere den Support."), "error")
        else:
            logger.info('Successfully activated network access',
                        extra={'data': {'mac': mac, 'birthdate': birthdate, 'host_name': host_name},
                               'tags': {'rate_critical': True}})

            flash(gettext("Netzwerkzugang wurde aktiviert!"), 'success')
            flash(gettext("Es kann bis zu 10 Minuten dauern, "
                          "bis der Netzwerkzugang funktioniert."), 'info')

            return redirect(url_for('.index'))

    return render_template('generic_form.html', page_title=gettext("Netzwerkanschluss aktivieren"),
                           form_args={'form': form, 'cancel_to': url_for('.index')})


@router_usersuite.get("/activate_network_access", name="usersuite.activate_network_access")
@router_usersuite.post("/activate_network_access")
def activate_network_access_(r: Request, tp: Templates, user: User):
    if not user.can_activate_network_access:
        # TODO is there a better code for “this does not make sense in this situation”?
        raise HTTPException(status_code=403)

    current = user.mpsk_clients
    return tp.TemplateResponse(r, "usersuite/mpsk_table.html", dict(clients=current))


@bp_usersuite.route("/hosting", methods=['GET', 'POST'])
@bp_usersuite.route("/hosting/<string:action>", methods=['GET', 'POST'])
@login_required
def hosting(action=None):
    """Change various settings for Helios.
    """
    if not current_user.has_property("userdb"):
        abort(403)

    if action == "confirm":
        current_user.userdb.drop()
        flash(gettext("Deine Datenbank wurde gelöscht."), 'success')
        return redirect(url_for('.hosting'))

    form = HostingForm()

    if form.validate_on_submit():
        if form.action.data == "create":
            current_user.userdb.create(form.password.data)
            flash(gettext("Deine Datenbank wurde erstellt."), 'success')
        else:
            current_user.userdb.change_password(form.password.data)

    try:
        user_has_db = current_user.userdb.has_db
    except NotImplementedError:
        abort(403)

    return render_template('usersuite/hosting.html',
                           form=form, user_has_db=user_has_db, action=action)


# TODO remove unused variants, e.g., I'm not sure POST /hosting makes any sense
@router_usersuite.get("/hosting", name="usersuite.hosting")
@router_usersuite.post("/hosting")
@router_usersuite.get("/hosting/{action}")
@router_usersuite.post("/hosting/{action}")
def hosting_(r: Request, tp: Templates, user: User, action: str | None = None) -> Response:
    # TODO replace manual 403 by dependency
    if not user.has_property("userdb"):
        raise HTTPException(status_code=403)

    return HTMLResponse("STUB")


@bp_usersuite.route("/finance-logs")
@login_required
def finance_logs():
    return redirect(url_for('usersuite.index', _anchor='transaction-log'))


@bp_usersuite.route("/terminate-membership", methods=['GET', 'POST'])
@login_required
def terminate_membership():
    """
    As member, cancel your membership to a given date
    :return:
    """

    capability_or_403('membership_end_date', 'edit')

    if current_user.membership_end_date.raw_value is not None:
        abort(403)

    form = TerminateMembershipForm()

    if form.validate_on_submit():
        end_date = form.end_date.data

        return redirect(url_for('.terminate_membership_confirm',
                                end_date=end_date))

    form_args = {
        'form': form,
        'cancel_to': url_for('.index'),
        'submit_text': gettext('Weiter')
    }

    return render_template('generic_form.html',
                           page_title=gettext("Mitgliedschaft beenden"),
                           form_args=form_args)


@bp_usersuite.route("/terminate-membership/confirm", methods=['GET', 'POST'])
@login_required
def terminate_membership_confirm():
    """
    As member, cancel your membership to a given date
    :return:
    """

    capability_or_403('membership_end_date', 'edit')

    if current_user.membership_end_date.raw_value is not None:
        abort(403)

    end_date = request.args.get("end_date", None, lambda x: datetime.strptime(x, '%Y-%m-%d').date())

    form = TerminateMembershipConfirmForm()

    if end_date is not None:
        try:
            form.estimated_balance.data = str(current_user.estimate_balance(
                end_date))

        except UnknownError:
            flash(gettext("Unbekannter Fehler!"), "error")
        else:
            form.end_date.data = end_date
    else:
        return redirect(url_for('.terminate_membership'))

    if form.validate_on_submit():
        try:
            current_user.terminate_membership(form.end_date.data)
        except TerminationNotPossible:
            flash(gettext("Beendigung der Mitgliedschaft nicht möglich!"), "error")
        except MacAlreadyExists:
            flash(gettext("Unbekannter Fehler!"), "error")
        else:
            logger.info('Successfully scheduled membership termination',
                        extra={'data': {'end_date': form.end_date.data},
                               'tags': {'rate_critical': True}})

            flash(gettext("Deine Mitgliedschaft wird zum angegebenen Datum beendet."), 'success')

        return redirect(url_for('.index'))

    form_args = {
        'form': form,
        'cancel_to': url_for('.terminate_membership')
    }

    return render_template('generic_form.html',
                           page_title=gettext("Mitgliedschaft beenden - Bestätigen"),
                           form_args=form_args)


@bp_usersuite.route("/continue-membership", methods=['GET', 'POST'])
@login_required
def continue_membership():
    """
    Cancel termination of membership
    :return:
    """

    capability_or_403('membership_end_date', 'edit')

    if current_user.membership_end_date.raw_value is None:
        abort(403)

    form = ContinueMembershipForm()

    if form.validate_on_submit():
        try:
            current_user.continue_membership()
        except ContinuationNotPossible:
            flash(gettext("Fortsetzung der Mitgliedschaft nicht möglich!"), "error")
        except UnknownError:
            flash(gettext("Unbekannter Fehler!"), "error")
        else:
            logger.info('Successfully cancelled membership termination',
                        extra={'tags': {'rate_critical': True}})

            flash(gettext("Deine Mitgliedschaft wird fortgesetzt."), 'success')

        return redirect(url_for('.index'))

    form_args = {
        'form': form,
        'cancel_to': url_for('.index')
    }

    return render_template('generic_form.html',
                           page_title=gettext("Mitgliedschaft fortsetzen"),
                           form_args=form_args)


@router_usersuite.get("/continue_membership", name="usersuite.continue_membership")
@router_usersuite.post("/continue_membership")
def continue_membership_(r: Request, tp: Templates, user: User) -> HTMLResponse:
    return HTMLResponse("STUB")


@bp_usersuite.route("/reset-wifi-password", methods=['GET', 'POST'])
@login_required
def reset_wifi_password():
    """
    Reset the wifi password
    """

    form = FlaskForm()

    capability_or_403('wifi_password', 'edit')

    if form.validate_on_submit():
        try:
            new_password = current_user.reset_wifi_password()
        except UnknownError:
            flash(gettext("Unbekannter Fehler!"), "error")
        else:
            logger.info('Successfully reset wifi password',
                        extra={'tags': {'rate_critical': True}})

            flash(Markup("{}:<pre>{}</pre>".format(gettext("Es wurde ein neues WLAN Passwort generiert"), new_password)), 'success')

        return redirect(url_for('.index'))

    form_args = {
        'form': form,
        'cancel_to': url_for('.index'),
        'submit_text': gettext('Neues WLAN Passwort generieren')
    }

    return render_template('generic_form.html',
                           page_title=gettext("Neues WLAN Passwort"),
                           form_args=form_args)


@router_usersuite.get("/reset-wifi-password", name="usersuite.reset_wifi_password")
@router_usersuite.post("/reset-wifi-password")
def reset_wifi_password_(r: Request, tp: Templates, user: User) -> HTMLResponse:
    return HTMLResponse("STUB")


@bp_usersuite.route("/get-apple-wlan-mobileconfig", methods=["GET"])
@login_required
def get_apple_wlan_mobileconfig():
    """
    Get the mobileconfig for the agdsn WLAN for an Apple device.
    """

    login = current_user.login.raw_value
    wifi_password = current_user.wifi_password.raw_value

    if not wifi_password:
        abort(404)

    return send_file(
        BytesIO(
            bytes(
                render_template(
                    "apple-mobileconfig.xml.j2",
                    login=login,
                    wifi_password=wifi_password,
                ),
                encoding="utf-8",
            )
        ),
        as_attachment=True,
        download_name="agdsn.mobileconfig",
    )


@router_usersuite.get("/get_apple_wlan_mobileconfig", name="usersuite.get_apple_wlan_mobileconfig")
def get_apple_wlan_mobileconfig_(r: Request, tp: Templates, user: User) -> HTMLResponse:
    return HTMLResponse("STUB")


