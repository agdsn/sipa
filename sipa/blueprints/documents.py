#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, send_file, abort
from os.path import isfile

bp_documents = Blueprint('documents', __name__, url_prefix='/documents')


@bp_documents.route('/images/<image>')
def show_image(image):
    filename = '../content/images/{}'.format(image)
    if not isfile(filename):
        abort(404)

    try:
        return send_file(filename)
    except IOError:
        abort(404)


@bp_documents.route('/<document>')
def show_pdf(document):
    filename = '../cached_documents/{}'.format(document)
    if not isfile(filename):
        abort(404)

    try:
        return send_file(filename)
    except IOError:
        abort(404)
