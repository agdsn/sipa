"""Blueprint for feature components such as bustimes etc.
Basically, this is everything that is to specific to appear in the generic.py
and does not fit into any other blueprint such as “documents”.
"""
from typing import Iterable
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from flask import Blueprint, render_template_string

from sipa.deps import Templates, Settings
from sipa.utils import get_bustimes, meetingcal, support_cal, support_hotline_available, TimeTable

bp_features = Blueprint('features', __name__)
router_features = APIRouter(default_response_class=HTMLResponse)


@router_features.get("/bustimes")
@router_features.get("/bustimes/{stopname}")
def bustimes(
    t: Templates,
    r: Request,
    s: Settings,
    stopname: str | None = None,
):
    """Queries the VVO-Online widget for the given stop.
    If no specific stop is given in the URL, it will query all
    stops set up in the config.
    """
    stops: dict[str, Iterable[TimeTable]] = (
        {stopname: get_bustimes(stopname)}
        if stopname
        else {stop: get_bustimes(stop, 4) for stop in s.busstops}
    )
    return t.TemplateResponse(r, "bustimes.html", {"stops": stops})


@router_features.get("/meetingcal", name="features.render_meetingcal")
def render_meetingcal(t: Templates, r: Request, s: Settings):
    # TODO turn into proper component
    return t.TemplateResponse(
        request=r,
        name="meetingcal.html",
        context={"meetings": meetingcal(url=(s.meetings_ical_url))}
    )


@router_features.get("/meetings-fragment", name="features.meetings")
def meetings_fragment(t: Templates, r: Request, s: Settings):
    # TODO turn into proper component
    # TODO think about `FragmentResponse` or some other helper which
    # - when sent with `HX-Request: true`: only sends the fragment
    # - otherwise: embeds it in a default “fragment” presenter
    return t.TemplateResponse(
        request=r,
        name="meetingcal-fragment.html",
        context={"meetingcal": meetingcal(url=s.meetings_ical_url)},
    )


@router_features.get("/support-fragment", name="features.support_office")
def support_office(t: Templates, r: Request, s: Settings):
    return t.TemplateResponse(
        r,
        "support-fragment.html",
        context={"supports": support_cal(s)},
    )


@bp_features.route("/hotline-fragment")
def hotline():
    return render_template_string(
        """
        {%- from "macros/support-hotline.html" import hotline_description -%}
        {{- hotline_description(available=available) -}}
        """,
        available=support_hotline_available(),
    )


@router_features.get("/hotline-fragment", name="features.hotline")
def hotline_(t: Templates, request: Request, s: Settings):
    return t.TemplateResponse(
        request,
        "hotline-fragment.html",
        context={"available": support_hotline_available(uri=str(s.pbx_uri))},
    )
