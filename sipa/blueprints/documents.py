# -*- coding: utf-8 -*-

from flask import Blueprint, send_file, abort, send_from_directory, current_app
from os.path import isfile, realpath, join
from flask.views import View
import os

bp_documents = Blueprint('documents', __name__)


class StaticFiles(View):
    def __init__(self, directory):
        self.directory = directory

    def dispatch_request(self, filename):
        if os.path.isabs(self.directory):
            directory = self.directory
        else:
            directory = os.path.join(current_app.root_path, self.directory)
        cache_timeout = current_app.get_send_file_max_age(filename)
        return send_from_directory(directory, filename,
                                   cache_timeout=cache_timeout)


bp_documents.add_url_rule('/images/<path:filename>',
                          view_func=StaticFiles.as_view('show_image',
                                                        '../content/images'))


bp_documents.add_url_rule('/documents/<path:filename>',
                          view_func=StaticFiles.as_view('show_document',
                                                        '../content/documents'))
