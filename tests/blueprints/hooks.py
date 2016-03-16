# -*- coding: utf-8; -*-
from unittest.mock import MagicMock, patch

from tests.prepare import AppInitialized


GIT_HOOK_URL = '/hooks/update-content'

# OPTIONS is implicitly added by flask and always handled
# http://flask.pocoo.org/docs/0.10/api/#flask.Flask.add_url_rule → Parameters → options
_HTTP_METHODS = {'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE', 'OPTIONS', 'CONNECT'}
HTTP_METHODS = _HTTP_METHODS - {'OPTIONS'}


class GitHookNoToken(AppInitialized):
    def test_git_hook_wrong_method(self):
        """Test that using wrong methods will cause a HTTP 405 return"""
        for method in HTTP_METHODS - {'POST'}:
            with self.subTest(method=method):
                response = self.client.open(GIT_HOOK_URL, method=method)
                self.assertEqual(response.status_code, 405)

    def test_git_hook_not_existent(self):
        """Test that HTTP 404 is returned if no token is configured"""
        response = self.client.post(GIT_HOOK_URL)
        self.assertEqual(response.status_code, 404)


class GitHookExistent(AppInitialized):
    def create_app(self):
        self.token = "SuperDUPERsecret!!1"
        return super().create_app(
            additional_config={'GIT_UPDATE_HOOK_TOKEN': self.token}
        )

    def test_no_token_auth_required(self):
        """Test that `PUT`ting the hook w/o giving a token returns HTTP 401"""
        response = self.client.post(GIT_HOOK_URL)
        self.assertEqual(response.status_code, 401)

    def test_empty_token_auth_required(self):
        response = self.client.post("{}?token=".format(GIT_HOOK_URL))
        self.assertEqual(response.status_code, 401)

    def test_wrong_token_permission_denied(self):
        """Test that using a wrong token gets you a HTTP 403"""
        response = self.client.post("{}?token={}".format(
            GIT_HOOK_URL,
            self.token + "wrong",
        ))
        self.assertEqual(response.status_code, 403)

    def test_correct_token_working(self):
        """Test that the hook returns HTTP 204 and calls `update_repo`"""

        # Patch out `update_repo` – we don't care about anything
        # git-related in this TestCase
        mock = MagicMock()
        with patch('sipa.blueprints.hooks.update_repo', mock):
            response = self.client.post("{}?token={}".format(
                GIT_HOOK_URL,
                self.token,
            ))
        self.assertEqual(response.status_code, 204)
        self.assertTrue(mock.called)
