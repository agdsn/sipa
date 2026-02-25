from __future__ import annotations
from jinja2.runtime import Context

import typing as t
from contextlib import asynccontextmanager
from functools import partial
from importlib.resources import files
from pathlib import Path

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from flask_login import AnonymousUserMixin
from flask_qrcode import QRcode
from jinja2 import Environment, pass_context
from markupsafe import Markup
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import _TemplateResponse

from sipa.blueprints.features import router_features
from sipa.blueprints.generic import router_generic
from sipa.blueprints.news import router_news
from sipa.blueprints.pages import router_pages
from sipa.blueprints.usersuite import router_usersuite
from sipa.initialization import init_jinja_env

from .deps import NotAuthenticated
from .units import dynamic_unit, format_money
from .utils.csp import generate_nonce, response_set_csp
from .utils.graph_utils import generate_traffic_chart
from .warnings import jinja_warn


def _get_package_path(suffix: str = "") -> str:
    fs_path = Path(__file__).resolve().parent
    if fs_path.is_dir():
        return str(fs_path / suffix)

    pkg_path = files("sipa")
    if pkg_path.is_dir():
        return str(pkg_path / suffix)

    raise AssertionError


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if (_get_package_path()) is None:
            raise RuntimeError("could not find package path for static files")
        app.mount("/static", StaticFiles(directory=_get_package_path("static")), name="static")
        yield

    app = FastAPI(lifespan=lifespan)

    app.state.templates = init_templates()

    app.include_router(router_generic)
    app.include_router(router_news)
    app.include_router(router_pages)
    app.include_router(router_usersuite)
    app.include_router(router_features)

    @app.middleware("http")
    async def add_csp_nonces(r: Request, call_next):
        r.state.nonce = (n := generate_nonce())
        return response_set_csp(await call_next(r), n)

    @app.exception_handler(NotAuthenticated)
    def redirect_to_login(request: Request, exc: NotAuthenticated) -> RedirectResponse:
        return RedirectResponse(request.url_for("generic.login"), status_code=303)

    return app


def init_templates() -> Templates:
    templates = Templates(
        _get_package_path("templates"),
        context_processors=[lambda request: {
            "current_user": getattr(request.state, "user", AnonymousUserMixin()),
            "nonce": request.state.nonce,
        }],
    )

    templates.env.globals["traffic_chart"] = _templates_traffic_chart

    # TODO magic mock? some stupid stubs?
    class CfPagesStub: ...

    class BackendsStub: ...

    init_jinja_env(
        templates.env,
        CfPagesStub(),  # type: ignore
        BackendsStub(),  # type: ignore
    )
    _init_babel_stubs(templates.env)
    templates.env.globals["qrcode"] = QRcode.qrcode
    templates.env.filters["qrcode"] = QRcode.qrcode
    templates.env.filters["money"] = format_money
    templates.env.filters["unit"] = dynamic_unit
    return templates


def _init_babel_stubs(env: Environment) -> None:
    # TODO replace by real thing
    def _i18n(msg: str, **kw: str | Markup):
        # stacklevel=4 is required due to jinja evaluation frames in the stack
        jinja_warn("i18n _() not yet implemented")
        return Markup(msg) % kw

    env.globals["_"] = _i18n

    def _datetimeformat(datetime, format: t.Literal["long", "short"], **_kw):
        jinja_warn("used unported flask_babel `datetimeformat` filter")
        return f"{datetime}"

    env.filters["datetimeformat"] = _datetimeformat

    def _dateformat(date, format: t.Literal["long", "medium", "short"], **_kw):
        jinja_warn("used legacy flask_babel `dateformat` filter")
        return f"{date}"

    env.filters["dateformat"] = _dateformat
    env.filters["date"] = partial(_dateformat, format="medium")

    def _timeformat(time, format: t.Literal["long", "short"], **_kw):
        jinja_warn("used legacy flask_babel `timeformat` filter")
        return f"{time}"

    env.filters["timeformat"] = _timeformat

    # these are our own but build on babel
    # TODO implement correctly; see utils
    # …all of these neet `@pass_context` to derive the current locale
    env.globals["get_weekday"] = lambda w: f"{w}"  # TODO should return locale.days["format"]["wide"][w]
    env.globals["get_locale"] = lambda: "en"  # TODO should return a locale
    env.globals["possible_locales"] = lambda: ["en", "de"]


@pass_context
def _templates_traffic_chart(ctx: Context, data) -> Markup:
    nonce = ctx.get("nonce")
    get_weekday = ctx["get_weekday"]
    _ = ctx["_"]

    svg_or_html = generate_traffic_chart(
        data,
        nonce=nonce,
        get_weekday=get_weekday,
        _=_,
    ).render()

    return Markup(svg_or_html)

class Templates(Jinja2Templates):
    def TemplateResponse(  # type: ignore[invalid-method-override]
        self,
        request: Request,
        name: str,
        context: dict[str, t.Any] | None = None,
        status_code: int = 200,
        headers: t.Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> _TemplateResponse:
        ctx = {} if context is None else dict(context)

        # TODO make context processor
        def url_self(**updates) -> str:
            return str(request.url.include_query_params(**updates))
        ctx.setdefault("url_self", url_self)
        ctx.setdefault("get_flashed_messages", lambda **kw: [])
        ctx["should_display_traffic_data"] = lambda: False  # TODO do without context locals

        return super().TemplateResponse(
            request=request,
            name=name,
            context=ctx,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )
