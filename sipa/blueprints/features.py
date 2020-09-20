# -*- coding: utf-8 -*-

"""Blueprint for feature components such as bustimes etc.
Basically, this is everything that is to specific to appear in the generic.py
and does not fit into any other blueprint such as “documents”.
"""

from flask import Blueprint, current_app, render_template
from sipa.utils import get_bustimes

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
