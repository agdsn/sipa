#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, send_file, abort
from os.path import isfile, realpath

bp_documents = Blueprint('documents', __name__)


@bp_documents.route('/images/<image>')
def show_image(image):
    print("Trying to show image {}".format(image))
    filename = realpath("content/images/{}".format(image))
    print("filename: {}".format(filename))
    if not isfile(filename):
        print("aborting")
        abort(404)

    try:
        return send_file(filename)
    except IOError:
        abort(404)


@bp_documents.route('/documents/<document>')
def show_pdf(document):
    filename = realpath("content/documents/{}".format(document))
    if not isfile(filename):
        abort(404)

    try:
        return send_file(filename)
    except IOError:
        abort(404)
