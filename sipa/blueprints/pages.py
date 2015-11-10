# -*- coding: utf-8 -*-

"""
Blueprint for the flatpages
"""

import os.path
from logging import getLogger
import json

from flask import Blueprint, render_template, current_app

from sipa.flatpages import cf_pages
from sipa.model import registered_dormitories, preferred_dormitory_name

logger = getLogger(__name__)

bp_pages = Blueprint('pages', __name__, url_prefix='/pages')


@bp_pages.route('/<category_id>/<article_id>')
def show(category_id, article_id):
    """Display a flatpage and parse dynamic content if available

    If available, a `<name>.<locale>.json` json_file is parsed and used to
    display A section on the webpage where users can select their
    dormitory and see _specific_ information like financial data.
    """
    article = cf_pages.get_or_404(category_id, article_id)

    box_filename = os.path.join(
        os.path.abspath(current_app.config['FLATPAGES_ROOT']),
        "{}.json".format(article.localized_page.path)
    )

    dynamic_data = load_dynamic_json(box_filename)

    if not dynamic_data:
        return render_template('template.html', article=article,
                               dynamic=False)

    return render_template('template.html', article=article,
                           default_dormitory=preferred_dormitory_name(),
                           dynamic=True, **dynamic_data)


def load_dynamic_json(filename):
    try:
        with open(filename, encoding="utf-8") as f:
            json_string = f.read()
    except OSError:
        return

    try:
        dynamic_data = json.loads(json_string)
    except ValueError:
        logger.error("Corrupt json json_file: %s", filename, extra={'data': {
            'json_string': json_string,
        }}, exc_info=True)
        return

    try:
        keys = dynamic_data['keys']
        values = dynamic_data['values']
        mappings = dynamic_data['mappings']
        title = dynamic_data['title']
    except KeyError:
        logger.error("Corrupt json json_file: %s", filename, extra={
            'data': {'json_content': dynamic_data},
        }, exc_info=True)

    values = {
        dorm.name: values[mappings[dorm.name]]
        for dorm in registered_dormitories
        if dorm.name in mappings
    }
    dormitories = [(dorm.name, dorm.display_name)
                   for dorm in registered_dormitories
                   if dorm.name in mappings]

    return {'title': title,
            'keys': keys,
            'dormitories': dormitories,
            'values': values}
