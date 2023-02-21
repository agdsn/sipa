import logging
from unittest.mock import patch

from tests.base import AppInitialized, disable_logs


GIT_HOOK_URL = '/hooks/update-content'

# OPTIONS is implicitly added by flask and always handled
# http://flask.pocoo.org/docs/0.10/api/#flask.Flask.add_url_rule → Parameters → options
_HTTP_METHODS = {'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE', 'OPTIONS', 'CONNECT'}
HTTP_METHODS = _HTTP_METHODS - {'OPTIONS'}


class GitHookTestBase(AppInitialized):
    def assert_hook_status(self, status, token=None):
        url = GIT_HOOK_URL
        if token is not None:
            url = f"{url}?token={token}"

        assert self.client.post(url).status_code == status


class GitHookNoToken(GitHookTestBase):
    def test_git_hook_wrong_method(self):
        """Test that using wrong methods will cause a HTTP 405 return"""
        for method in HTTP_METHODS - {'POST'}:
            with self.subTest(method=method):
                response = self.client.open(GIT_HOOK_URL, method=method)
                assert response.status_code == 405

    def test_git_hook_not_existent(self):
        """Test that HTTP 404 is returned if no token is configured"""
        self.assert_hook_status(404)


class GitHookExistent(GitHookTestBase):
    token = "SuperDUPERsecret!!1"

    @property
    def app_config(self):
        return {
            **super().app_config,
            'GIT_UPDATE_HOOK_TOKEN': self.token,
        }

    def test_no_token_auth_required(self):
        """Test that `PUT`ting the hook w/o giving a token returns HTTP 401"""
        self.assert_hook_status(401)

    def test_empty_token_auth_required(self):
        self.assert_hook_status(401, token="")

    def test_wrong_token_permission_denied(self):
        """Test that using a wrong token gets you a HTTP 403"""
        with disable_logs(logging.WARNING):
            self.assert_hook_status(403, token=self.token+"wrong")

    def test_correct_token_working(self):
        """Test that the hook returns HTTP 204 and calls `update_repo`"""

        # Patch out `update_repo` – we don't care about anything
        # git-related in this TestCase
        with patch('sipa.blueprints.hooks.update_repo') as mock:
            self.assert_hook_status(204, token=self.token)
            self.assertTrue(mock.called)
