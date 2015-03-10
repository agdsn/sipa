#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, send_file, abort


bp_documents = Blueprint('documents', __name__, url_prefix='/documents')

@bp_documents.route('/<document>')
def show(document):
    #(TODO) check wether an document should be avaible<
    try:
        return send_file('cached_documents/' + document)
    except IOError:
        abort(404)