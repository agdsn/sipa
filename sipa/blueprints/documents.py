# -*- coding: utf-8 -*-

import os

from flask import Blueprint, send_from_directory, current_app
from flask_login import current_user
from flask.views import View

bp_documents = Blueprint('documents', __name__)


class StaticFiles(View):
    def __init__(self, directory, login_required=False):
        self.directory = directory
        self.login_required = login_required

    def dispatch_request(self, filename):
        if self.login_required and not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()

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


bp_documents.add_url_rule('/documents/restricted/<path:filename>',
                          view_func=StaticFiles.as_view('show_document_restricted',
                                                        '../content/documents/restricted',
                                                        True))
