# -*- coding: utf-8 -*-

import os

from flask import Blueprint, send_from_directory, current_app
from flask.blueprints import BlueprintSetupState
from flask_login import login_required


class StaticFilesBlueprint(Blueprint):
    def add_static_files(self, rule, endpoint, directory, decorators=()):
        def add(state: BlueprintSetupState):
            app = state.app
            nonlocal directory
            if not os.path.isabs(directory):
                directory = os.path.join(app.root_path, directory)

            def send_static_file(filename):
                cache_timeout = app.get_send_file_max_age(filename)
                return send_from_directory(directory, filename,
                                           cache_timeout=cache_timeout)

            for decorator in decorators:
                send_static_file = decorator(send_static_file)

            app.add_url_rule(rule, endpoint, send_static_file)

        self.record(add)


bp_documents = StaticFilesBlueprint('documents', __name__)
bp_documents.add_static_files('/images/<path:filename>', 'show_image',
                              '../content/images')
bp_documents.add_static_files('/documents/<path:filename>', 'show_document',
                              '../content/documents')
bp_documents.add_static_files('/documents_restricted/<path:filename>',
                              'show_document_restricted',
                              '../content/documents_restricted',
                              [login_required])
