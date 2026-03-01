from __future__ import annotations

import typing as t
from contextlib import asynccontextmanager
from functools import partial

from babel import Locale
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi_babel import BabelMiddleware
from fastapi_babel.properties import RootConfigs
from flask_login import AnonymousUserMixin
from flask_qrcode import QRcode
from jinja2 import Environment, pass_context
from jinja2.runtime import Context
from markupsafe import Markup
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import _TemplateResponse

from sipa.babel import fastapi_locale_selector
from sipa.blueprints.features import router_features
from sipa.blueprints.generic import router_generic
from sipa.blueprints.news import router_news
from sipa.blueprints.pages import router_pages
from sipa.blueprints.usersuite import router_usersuite
from sipa.initialization import init_jinja_env

from ._pkg_path import get_package_path as get_package_path
from .deps import NotAuthenticated
from .fastapi_dev_reload import add_dev_websocket, lifespan_dev_watcher
from .units import dynamic_unit, format_money
from .utils.csp import generate_nonce, response_set_csp
from .utils.graph_utils import generate_traffic_chart
from .warnings import jinja_warn


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if (get_package_path()) is None:
            raise RuntimeError("could not find package path for static files")
        app.mount("/static", StaticFiles(directory=get_package_path("static")), name="static")
        async with lifespan_dev_watcher(app):
            yield

    app = FastAPI(lifespan=lifespan)
    add_dev_websocket(app=app)

    app.state.templates = init_templates()

    app.include_router(router_generic)
    app.include_router(router_news)
    app.include_router(router_pages)
    app.include_router(router_usersuite)
    app.include_router(router_features)

    app.add_middleware(
        BabelMiddleware,
        babel_configs=RootConfigs(
            ROOT_DIR=".",
            # HACK: fastapi_babel (incorrectly) does not translate anything if locale == default_locale.
            #   this circumvents that.
            BABEL_DEFAULT_LOCALE="",
            BABEL_TRANSLATION_DIRECTORY=get_package_path("translations"),
        ),
        jinja2_templates=app.state.templates,
        locale_selector=fastapi_locale_selector,
    )
    from fastapi_babel.helpers import _ as fabgettext
    app.state.templates.env.globals.update(gettext=fabgettext)

    @app.get("/set-lang/{lang}", name="set_language")
    def set_language(r: Request, lang: str):
        resp = RedirectResponse(url=r.headers.get("referer") or "/")
        resp.set_cookie("lang", lang, max_age=365 * 24 * 3600, httponly=True, samesite="lax")
        return resp

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
        get_package_path("templates"),
        context_processors=[lambda request: {
            "current_user": getattr(request.state, "user", AnonymousUserMixin()),
            "nonce": request.state.nonce,
            "current_locale": Locale(request.state.babel.locale),
            # TODO post: replace all `get_locale()` usages by `current_locale` ones
            "get_locale": lambda: Locale(request.state.babel.locale),
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
