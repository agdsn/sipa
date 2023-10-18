"""Blueprint for feature components such as bustimes etc.
Basically, this is everything that is to specific to appear in the generic.py
and does not fit into any other blueprint such as “documents”.
"""

from flask import Blueprint, current_app, render_template, render_template_string

from sipa.utils import get_bustimes, meetingcal

bp_features = Blueprint('features', __name__)


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


@bp_features.route("/meetingcal")
def render_meetingcal():
    meetings = meetingcal()
    return render_template('meetingcal.html', meetings=meetings)


@bp_features.route("/meetings-fragment")
def meetings():
    return render_template_string(
        """
            {%- from "macros/meetingcal.html" import render_meetingcal -%}
            {{- render_meetingcal(meetingcal) -}}
        """,
        meetingcal=meetingcal(),
    )


@bp_features.route("/hotline-fragment")
def hotline():
    return render_template_string(
        """
        {%- from "macros/support-hotline.html" import hotline_description -%}
        {{- hotline_description(available=available) -}}
        """,
        available=True,
    )
