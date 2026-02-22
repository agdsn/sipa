from __future__ import annotations

import typing as t
from datetime import date, datetime
from decimal import Decimal

from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.engine.create import create_engine
from starlette.responses import RedirectResponse

from .config.typed_config import Settings as SipaSettings
from .model.misc import PaymentDetails
from .model.pycroft.api import PycroftApi
from .model.pycroft.schema import UserData, UserStatus, Interface
from .model.pycroft.user import User as PycroftUser


# TODO define init method here as well to put state writing and state fetching closer together
def templates(request: Request) -> Jinja2Templates:
    return t.cast(Jinja2Templates, request.app.state.templates)


type Templates = t.Annotated[Jinja2Templates, Depends(templates)]


def get_settings() -> SipaSettings:
    return SipaSettings()


type Settings = t.Annotated[SipaSettings, Depends(get_settings)]


class NotAuthenticated(Exception):
    pass


def get_user(request: Request, settings: Settings) -> PycroftUser:
    """
        :raises NotAuthenticated:
    """
    # TODO put this thing next to the `login_get` and `login_post` endpoints
    #   – or at least next to a `set_user` function which sets a cookie.
    if not (username := request.cookies.get("username")):
        raise NotAuthenticated

    # TODO fetch user from pycroft API
    # TODO allow passing UserData model directly
    user = PycroftUser(
        user_data=UserData(
            id=10564,
            user_id="10564",
            login=username,
            name="Hans Franz",
            status=UserStatus(
                member=True,
                traffic_exceeded=False,
                network_access=True,
                account_balanced=True,
                violation=False,
            ),
            room="Wu3 3-43",
            mail="hans.franz@agdsn.de",
            mail_forwarded=False,
            mail_confirmed=True,
            properties=[
                "mail",
                "member",
                "network_access",
                "sipa_login",
                "userdb",
            ],
            traffic_history=[],
            interfaces=[
                Interface(id=1, mac="00:de:ad:be:ef:00", ips=["141.30.228.39"]),
            ],
            finance_balance=Decimal(200),
            finance_history=[],
            last_finance_update=date(2020, 1, 1),
            # TODO introduce properties once they can be excluded
            birthdate=date(2000, 1, 1),
            membership_end_date=None,
            membership_begin_date=None,
            wifi_password="YouShallNotPassword",
            mpsk_clients=[],
        ).model_dump(),
        api=PycroftApi(
            endpoint=str(settings.pycroft_endpoint), api_key=str(settings.pycroft_api_key)
        ),
        payment_details=PaymentDetails(
            recipient=settings.payment_recipient,
            bank=settings.payment_bank,
            iban=settings.payment_iban,
            bic=settings.payment_bic,
        ),
        ip_mask=settings.db_helios_ip_mask,
        engine=create_engine(str(settings.db_helios_uri)),
    )
    request.state.user = user
    return user


type User = t.Annotated[PycroftUser, Depends(get_user)]

