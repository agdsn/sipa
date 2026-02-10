"""Blueprint for feature components such as bustimes etc.
Basically, this is everything that is to specific to appear in the generic.py
and does not fit into any other blueprint such as “documents”.
"""
from jinja2 import Template
from starlette.templating import _TemplateResponse
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from flask import Blueprint, current_app, render_template, render_template_string

from sipa.deps import Templates, Settings
from sipa.utils import get_bustimes, meetingcal, support_cal, support_hotline_available

bp_features = Blueprint('features', __name__)
router_features = APIRouter(default_response_class=HTMLResponse)


@bp_features.route("/bustimes")
@bp_features.route("/bustimes/<string:stopname>")
def bustimes(stopname=None):
    """Queries the VVO-Online widget for the given stop.
    If no specific stop is given in the URL, it will query all
    stops set up in the config.
    """
    data = {}

    if stopname:
        # Only one stop requested
        data[stopname] = get_bustimes(stopname)
    else:
        # General output page
        for stop in current_app.config['BUSSTOPS']:
            data[stop] = get_bustimes(stop, 4)

    return render_template('bustimes.html', stops=data, stopname=stopname)


@router_features.get("/bustimes")
@router_features.get("/bustimes/{stopname}")
def bustimes_(
    t: Templates,
    r: Request,
    s: Settings,
    stopname: str | None = None,
):
    """Queries the VVO-Online widget for the given stop.
    If no specific stop is given in the URL, it will query all
    stops set up in the config.
    """
    stops: dict[str, str] = (
        {stopname: get_bustimes(stopname)}
        if stopname
        else {stop: get_bustimes(stop, 4) for stop in s.busstops}
    )
    return t.TemplateResponse(r, "bustimes.html", {"stops": stops})


@bp_features.route("/meetingcal")
def render_meetingcal():
    meetings = meetingcal()
    return render_template('meetingcal.html', meetings=meetings)


@router_features.get("/meetingcal", name="features.render_meetingcal")
def render_meetingcal_(t: Templates, r: Request, s: Settings):
    # TODO turn into proper component
    return t.TemplateResponse(
        request=r,
        name="meetingcal.html",
        context={"meetings": meetingcal(url=(s.meetings_ical_url))}
    )


@bp_features.route("/meetings-fragment")
def meetings():
    return render_template_string(
        """
            {%- from "macros/ical.html" import render_meetingcal -%}
            {{- render_meetingcal(meetingcal) -}}
        """,
        meetingcal=meetingcal(),
    )


@router_features.get("/meetings-fragment", name="features.meetings")
def meetings_(t: Templates, r: Request, s: Settings):
    # TODO turn into proper component
    return t.TemplateResponse(
        request=r,
        name="meetingcal-fragment.html",
        context={"meetingcal": meetingcal(url=s.meetings_ical_url)},
    )


@bp_features.route("/support-fragment")
def support_office():
    return render_template_string(
        """
        {%- from "macros/ical.html" import render_support -%}
        {{- render_support(supports) -}}
        """,
        supports=support_cal(),
    )


@router_features.get("/support-fragment", name="features.support_office")
def support_office_(t: Templates, request: Request, s: Settings):
    return t.TemplateResponse(
        r,
        "support-fragment.html",
        context={"supports": {addr.name: addr.model_dump() for addr in s.contact_addresses}},
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
