"""Blueprint for feature components such as bustimes etc.
Basically, this is everything that is to specific to appear in the generic.py
and does not fit into any other blueprint such as “documents”.
"""
import typing as t
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
    tp: Templates,
    r: Request,
    s: Settings,
    stopname: str | None = None,
):
    """Queries the VVO-Online widget for the given stop.
    If no specific stop is given in the URL, it will query all
    stops set up in the config.
    """
    stops: dict[str, t.Iterable[TimeTable]] = (
        {stopname: get_bustimes(stopname)}
        if stopname
        else {stop: get_bustimes(stop, 4) for stop in s.busstops}
    )
    return tp.TemplateResponse(r, "bustimes.html", {"stops": stops})


@router_features.get("/meetingcal", name="features.render_meetingcal")
def render_meetingcal(tp: Templates, r: Request, s: Settings):
    # TODO turn into proper component
    return tp.TemplateResponse(
        request=r,
        name="meetingcal.html",
        context={"meetings": meetingcal(url=(s.meetings_ical_url))}
    )


@router_features.get("/meetings-fragment", name="features.meetings")
def meetings_fragment(tp: Templates, r: Request, s: Settings):
    # TODO turn into proper component
    # TODO think about `FragmentResponse` or some other helper which
    # - when sent with `HX-Request: true`: only sends the fragment
    # - otherwise: embeds it in a default “fragment” presenter
    return tp.TemplateResponse(
        request=r,
        name="meetingcal-fragment.html",
        context={"meetingcal": meetingcal(url=s.meetings_ical_url)},
    )


@router_features.get("/support-fragment", name="features.support_office")
def support_office(tp: Templates, r: Request, s: Settings):
    return tp.TemplateResponse(
        r,
        "support-fragment.html",
        context={"supports": support_cal(s)},
    )


@router_features.get("/hotline-fragment", name="features.hotline")
def hotline(tp: Templates, request: Request, s: Settings):
    return tp.TemplateResponse(
        request,
        "hotline-fragment.html",
        context={"available": support_hotline_available(uri=str(s.pbx_uri))},
    )
