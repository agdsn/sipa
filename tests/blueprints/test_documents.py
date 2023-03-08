import pytest

from tests.assertions import TestClient


@pytest.fixture(scope="module")
def client(module_test_client):
    return module_test_client


def test_restriced_area(client: TestClient):
    with client.renders_template("login.html"):
        resp = client.assert_url_ok(
            "/documents_restricted/fake-doc/", follow_redirects=True
        )
    assert len(resp.history) == 1
    assert resp.history[0].location.startswith("/login?")


@pytest.mark.usefixtures("user_logged_in")
def test_restricted_area_logged_in(client: TestClient):
    client.assert_url_response_code("/documents_restricted/fake-doc/", 404)


def test_unrestricted_area(client: TestClient):
    client.assert_url_response_code("/documents/fake-doc/", 404)
