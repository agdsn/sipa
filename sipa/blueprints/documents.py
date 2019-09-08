# -*- coding: utf-8 -*-

import os

from flask import Blueprint, send_from_directory, current_app
from flask_login import current_user
from flask.views import View

from sipa.base import login_manager


bp_documents = Blueprint('documents', __name__)


class StaticFiles(View):
    def __init__(self, directory, login_required=False, member_required=False):
        self.directory = directory
        self.login_required = login_required
        self.member_required = member_required

    def dispatch_request(self, filename):
        if self.login_required and not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()

        if self.member_required and not current_user.is_member:
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
login_manager.ignore_endpoint('documents.show_image')

bp_documents.add_url_rule('/documents/<path:filename>',
                          view_func=StaticFiles.as_view('show_document',
                                                        '../content/documents'))
login_manager.ignore_endpoint('documents.show_document')


bp_documents.add_url_rule('/documents_restricted/<path:filename>',
                          view_func=StaticFiles.as_view('show_document_restricted',
                                                        '../content/documents_restricted',
                                                        login_required=True,
                                                        member_required=True))
