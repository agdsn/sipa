import logging
from functools import partial
from urllib.parse import urljoin

import pytest
from flask import abort, url_for, Flask

from tests.assertions import TestClient


@pytest.fixture(scope="module")
def client(module_test_client: TestClient) -> TestClient:
    return module_test_client


@pytest.mark.parametrize("code", (401, 403, 404), scope="class")
class TestErrorHandlers:
    @pytest.fixture(scope="class", autouse=True)
    def modify_app(self, bare_app, code):
        # We monkey-patch a new route: this is way faster than always initializing a new app.
        endpoint = f"aborting-with-{code}"
        bare_app.add_url_rule(
            rule=f"/aborting-{code}",
            endpoint=endpoint,
            view_func=partial(abort, code=code),
        )
        yield
        bare_app.url_map._rules_by_endpoint.pop(endpoint)

    def test_error_handler_redirection(self, code, class_test_client: TestClient):
        with class_test_client.renders_template("error.html"):
            class_test_client.get(f"/aborting-{code}")


def test_index_redirects_correctly(client: TestClient):
    client.assert_url_redirects("/", "/news/")


def test_index_reachable(client: TestClient):
    client.assert_url_ok("/", follow_redirects=True)


def test_correct_backend(app: Flask):
    assert app.config["BACKEND"] == "sample"


@pytest.mark.usefixtures("user_logged_in")
def test_usertraffic_permitted(client: TestClient, app):
    client.assert_ok("generic.usertraffic")


def test_api_reachable(client: TestClient):
    client.assert_ok("generic.traffic_api")


def test_version_reachable(client: TestClient):
    with client.renders_template("version.html"):
        client.assert_ok("generic.version")


class TestForm:
    """Base class for form tests.

    You need to implement the `endpoint`, `template`, `valid_data`,
    and `invalid_data` fixtures.
    """

    __test__ = False

    def test_get(self, client: TestClient, endpoint, template):
        with client.renders_template(template):
            client.assert_ok(endpoint)

    def test_post_flashes(self, client: TestClient, endpoint, template):
        with client.renders_template(template), client.capture_flashes() as flashed:
            client.assert_ok(endpoint, method="POST")
        assert flashed
        assert all(m.category == "error" for m in flashed)

    def test_invalid_data_flashes(
        self, client: TestClient, endpoint, template, invalid_data
    ):
        with client.renders_template(template), client.flashes_message(
            ".*", category="error"
        ):
            client.assert_ok(endpoint, data=invalid_data, method="POST")

    @pytest.fixture()
    def silence_logs(self):
        logging.disable()
        yield
        logging.disable(logging.NOTSET)

    def test_valid_data_returns(
        self, client: TestClient, valid_data, endpoint, silence_logs
    ):
        # TODO: mock out mail sending and check for `success` instead
        with client.flashes_message(".*error sending.*", category="error"):
            client.assert_redirects(
                endpoint, data=valid_data, method="POST", expected_location="/"
            )


class TestAnonymousContactForm(TestForm):
    __test__ = True

    @pytest.fixture(scope="class")
    def endpoint(self):
        return "generic.contact"

    @pytest.fixture(scope="class")
    def template(self):
        return "anonymous_contact.html"

    @pytest.fixture(scope="class")
    def valid_data(self):
        return {
            "email": "foo@bar.baz",
            "name": "Darc net",
            "dormitory": "localhost",
            "subject": "Test",
            "message": "Test message!",
        }

    @pytest.fixture(
        scope="class",
        params=(
            {"email": ""},
            {"email": "foo@bar"},
            {"name": ""},
            {"dormitory": "not_localhost"},
            {"subject": ""},
            {"message": ""},
        ),
    )
    def invalid_data(self, request):
        return request.param


class TestOfficialContactForm(TestForm):
    __test__ = True

    @pytest.fixture(scope="class")
    def endpoint(self):
        return "generic.contact_official"

    @pytest.fixture(scope="class")
    def template(self):
        return "official_contact.html"

    @pytest.fixture(scope="class")
    def valid_data(self):
        return {
            "email": "foo@bar.baz",
            "name": "Darc net",
            "subject": "Test",
            "message": "Test message!",
        }

    @pytest.fixture(
        scope="class",
        params=(
            {"email": ""},
            {"email": "foo@bar"},
            {"name": ""},
            {"subject": ""},
            {"message": ""},
        ),
    )
    def invalid_data(self, request):
        return request.param


def test_nonexistent_url_404(client: TestClient):
    fake_url = urljoin(url_for("generic.index"), "nonexistent")
    resp = client.assert_url_response_code(fake_url, code=404)
    assert resp.location is None
