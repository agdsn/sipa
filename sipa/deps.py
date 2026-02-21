from __future__ import annotations
from sqlalchemy.engine.create import create_engine

import typing as t

from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates
from .model.misc import PaymentDetails
from .model.pycroft.api import PycroftApi
from .model.pycroft.user import User
from starlette.responses import RedirectResponse

from .config.typed_config import Settings as SipaSettings


# TODO define init method here as well to put state writing and state fetching closer together
def templates(request: Request) -> Jinja2Templates:
    return t.cast(Jinja2Templates, request.app.state.templates)


type Templates = t.Annotated[Jinja2Templates, Depends(templates)]


def get_settings() -> SipaSettings:
    return SipaSettings()


type Settings = t.Annotated[SipaSettings, Depends(get_settings)]


def get_user(request: Request, settings: Settings) -> User | RedirectResponse:
    # TODO put this thing next to the `login_get` and `login_post` endpoints
    #   – or at least next to a `set_user` function which sets a cookie.
    if not (username := request.cookies.get("username")):
        return RedirectResponse(url=request.url_for("generic.login"))

    # TODO fetch user from pycroft API
    # TODO allow passing UserData model directly
    return User(
        user_data={},
        api=PycroftApi(endpoint="", api_key=settings.pycroft_api_key),
        payment_details=PaymentDetails(
            recipient=settings.payment_recipient,
            bank=settings.payment_bank,
            iban=settings.payment_iban,
            bic=settings.payment_bic,
        ),
        ip_mask=settings.db_helios_ip_mask,
        engine=create_engine(settings.db_helios_uri),
    )
