import logging

from flask import current_app, request, abort
from flask.blueprints import Blueprint

from sipa.utils.git_utils import update_repo


logger = logging.getLogger(__name__)

bp_hooks = Blueprint('hooks', __name__, url_prefix='/hooks')


@bp_hooks.route('/update-content', methods=['POST'])
def content_hook():
    auth_key = current_app.config.get('GIT_UPDATE_HOOK_TOKEN')

    if not auth_key:
        # no key configured (default) → feature not enabled
        abort(404)

    key = request.args.get('token')
    if not key:
        logger.debug("`update-content` called without Token",
                     extra={'data': {'request_args': request.args}})
        abort(401)

    if key != auth_key:
        logger.warning("`update-content` called with wrong Token",
                       extra={'data': {'request_args': request.args,
                                       'auth_key': auth_key}})
        abort(403)

    logger.info("Update hook triggered. Fetching content.")
    reload_necessary = update_repo(current_app.config['FLATPAGES_ROOT'])
    if reload_necessary:
        try:
            import uwsgi
        except ImportError:
            logger.debug("UWSGI not present, skipping reload")
            pass
        else:
            logger.debug("Reloading UWSGI…")
            uwsgi.reload()

    # 204: No content
    # https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#204
    return "", 204
