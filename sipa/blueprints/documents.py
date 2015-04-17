#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, send_file, abort


bp_documents = Blueprint('documents', __name__, url_prefix='/documents')


@bp_documents.route('/images/<image>')
def show_image(image):
    try:
        return send_file('../content/images/{}'.format(image))
    except IOError:
        raise IOError


@bp_documents.route('/<document>')
def show_pdf(document):
    # TODO check whether an document should be available
    try:
        return send_file('../cached_documents/{}'.format(document))
    except IOError:
        abort(404)
