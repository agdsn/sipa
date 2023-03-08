import logging
from unittest.mock import patch

import pytest

from .assertions import TestClient
from .conftest import make_bare_app
from ..base import disable_logs

GIT_HOOK_URL = '/hooks/update-content'

# OPTIONS is implicitly added by flask and always handled
# http://flask.pocoo.org/docs/0.10/api/#flask.Flask.add_url_rule → Parameters → options
_HTTP_METHODS = {'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE', 'OPTIONS', 'CONNECT'}
HTTP_METHODS = _HTTP_METHODS - {'OPTIONS'}


def assert_hook_status(client: TestClient, status, token=None):
    url = GIT_HOOK_URL
    if token is not None:
        url = f"{url}?token={token}"
    client.assert_url_response_code(url=url, method="POST", code=status)


@pytest.fixture(scope="module")
def client(module_test_client: TestClient) -> TestClient:
    return module_test_client


@pytest.fixture
def update_repo_mock():
    with patch("sipa.blueprints.hooks.update_repo") as mock:
        yield mock


class TestAppWithoutGitHook:
    @pytest.mark.parametrize("method", HTTP_METHODS - {"POST"})
    def test_git_hook_wrong_method(self, client, method):
        client.assert_url_response_code(GIT_HOOK_URL, method=method, code=405)

    def test_git_hook_not_existent(self, client):
        assert_hook_status(client, status=404)


class TestAppWithGitHook:
    @pytest.fixture(scope="class")
    def token(self) -> str:
        return "SuperDUPERsecret!!1"

    @pytest.fixture(scope="class")
    def app(self, default_config, token):
        return make_bare_app(config=(default_config | {"GIT_UPDATE_HOOK_TOKEN": token}))

    @pytest.fixture(scope="class")
    def client(self, class_test_client) -> TestClient:
        return class_test_client

    def test_no_token_auth_required(self, client):
        """Test that `PUT`ting the hook w/o giving a token returns HTTP 401"""
        assert_hook_status(client, status=401)

    def test_empty_token_auth_required(self, client):
        assert_hook_status(client, status=401, token="")

    def test_wrong_token_permission_denied(self, client, token):
        """Test that using a wrong token gets you a HTTP 403"""
        with disable_logs(logging.WARNING):
            assert_hook_status(client, status=403, token=f"{token}wrong")

    def test_correct_token_working(self, client, token, update_repo_mock):
        """Test that the hook returns HTTP 204 and calls `update_repo`"""
        assert_hook_status(client, status=204, token=token)
        assert update_repo_mock.called
