from jinja2 import Environment
from markupsafe import Markup
from sipa.blueprints.features import router_features
from starlette.background import BackgroundTask
from starlette.templating import _TemplateResponse
import typing as t
import warnings
from importlib.resources import files

from fastapi import FastAPI
from fastapi.datastructures import State
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from flask_login import AnonymousUserMixin
from starlette.requests import Request

from sipa.blueprints.generic import router_generic
from sipa.blueprints.news import router_news
from sipa.blueprints.pages import router_pages
from sipa.blueprints.usersuite import router_usersuite
from sipa.initialization import init_jinja_env


def create_app() -> FastAPI:
    app = FastAPI()

    init_templates(app.state)

    app.include_router(router_generic)
    app.include_router(router_news)
    app.include_router(router_pages)
    app.include_router(router_usersuite)
    app.include_router(router_features)
    app.mount("/static", StaticFiles(directory=str(files("sipa") / "static")), name="static")

    return app


def init_templates(state: State):
    def _get_current_user(request: Request) -> dict[str, t.Any]:
        return {"current_user": getattr(request.state, "user", AnonymousUserMixin())}

    templates = Templates(
        str(files("sipa") / "templates"),
        context_processors=[_get_current_user],
    )

    # TODO magic mock? some stupid stubs?
    class CfPagesStub: ...

    class BackendsStub: ...

    init_jinja_env(
        templates.env,
        CfPagesStub(),  # type: ignore
        BackendsStub(),  # type: ignore
    )
    _init_babel_stubs(templates.env)
    state.templates = templates


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

    def _dateformat(date, format: t.Literal["long", "short"], **_kw):
        jinja_warn("used legacy flask_babel `dateformat` filter")
        return f"{date}"

    env.filters["dateformat"] = _dateformat

    def _timeformat(time, format: t.Literal["long", "short"], **_kw):
        jinja_warn("used legacy flask_babel `timeformat` filter")
        return f"{time}"

    env.filters["timeformat"] = _timeformat


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


def jinja_warn(msg: str) -> None:
    warnings.warn(msg, FastAPIIncompleteWarning, stacklevel=5)


class FastAPIIncompleteWarning(Warning):
    ...
