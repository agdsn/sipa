import re
import typing as t
from unittest.mock import patch

import pytest
from flask import url_for
from werkzeug import Response

from sipa.blueprints.usersuite import get_attribute_endpoint
from sipa.model.fancy_property import PropertyBase
from sipa.model.user import TableRow
from tests.assertions import TestClient, RenderedTemplate


pytestmark = pytest.mark.usefixtures("user_logged_in")


@pytest.fixture(scope="module")
def client(module_test_client) -> TestClient:
    return module_test_client


def test_usersuite_reachable(client):
    resp = client.get(url_for("usersuite.index"))
    assert resp.status_code == 200


@pytest.mark.parametrize(
    "endpoint",
    [
        f"usersuite.{x}"
        for x in "index contact change_mac activate_network_access".split()
    ],
)
def test_usersuite_endpoint_ok(client, endpoint):
    client.assert_ok(endpoint)


@pytest.fixture(scope="module")
def _usersuite_index(client) -> tuple[Response, RenderedTemplate]:
    with client.renders_template("usersuite/index.html") as recorded:
        resp = client.assert_ok("usersuite.index")
    return resp, recorded[0]


@pytest.fixture(scope="module")
def usersuite_response(_usersuite_index):
    return _usersuite_index[0]


@pytest.fixture(scope="module")
def usersuite_passed_rows(_usersuite_index) -> list[TableRow]:
    return t.cast(list[TableRow], _usersuite_index[1].context["rows"])


@pytest.mark.parametrize(
    "propname",
    (
        "address",
        "finance_balance",
        "id",
        "ips",
        "login",
        "mac",
        "mail",
        "mail_confirmed",
        "mail_forwarded",
        "realname",
        "status",
        "userdb_status",  # unsupported
        "wifi_password",
        "mpsk_clients",
    ),
)
def test_usersuite_passes_correct_rows(usersuite_passed_rows, propname):
    rows = usersuite_passed_rows
    relevant_row = next(row for row in rows if row.property.name == propname)
    assert (
        relevant_row is not None
    ), f"Property {propname} absent from usersuite rows!\n{rows=!r}"
    if propname != "userdb_status":
        assert t.cast(PropertyBase, relevant_row.property).supported


def test_usersuite_contains_urls(usersuite_response):
    """Test the usersuite contains the urls of `sample`s capabilities."""
    # We have to patch `current_user` since it is not defined due
    # to the wrong app context, but the code runs some asserts
    # against it checking capabilities.
    with patch("sipa.blueprints.usersuite.current_user"):
        urls = [
            *(url_for(get_attribute_endpoint(attr)) for attr in ["mail", "mac"]),
            *(
                url_for(get_attribute_endpoint(attr, capability="delete"))
                for attr in []
            ),
            url_for("usersuite.change_password"),
            url_for("generic.contact"),
        ]

    for url in urls:
        assert re.search(
            f'href="[^"]*{url}[^"]*"', usersuite_response.data.decode()
        ), f"Usersuite does not contain any reference to url {url!r}"


def test_usersuite_form_add_mpsk(client):
    client.assert_ok("usersuite.add_mpsk")


def test_usersuite_change_mpsk_not_found(client):
    resp = client.get(url_for("usersuite.change_mpsk", mpsk_id=1))
    assert resp.status_code == 404

def test_usersuite_delete_mpsk_not_found(client):
    resp = client.get(url_for("usersuite.delete_mpsk", mpsk_id=1))
    assert resp.status_code == 404


@pytest.mark.parametrize(
    "data", ({"password": "test", "name": "a", "mac": "88:88:88:88:87:88"},)
)
def test_add_mpsk_client(client, data):
    resp = client.post(url_for("usersuite.add_mpsk"), data=data)
    assert resp.status_code == 302

    assert resp.headers["location"] == url_for("usersuite.view_mpsk")


@pytest.mark.parametrize(
    "data",
    (
        {"password": "test"},
        {"name": "a"},
        {"mac": "88:88:88:88:87:88"},
        {"password": "test", "name": "", "mac": "88:88:88:88:87:88"},
        {"password": "test", "name": "", "mac": "FF:FF:FF:FF:FF:FF"},
    ),
)
def test_add_invalid_mpsk(client, data):
    resp = client.post(url_for("usersuite.add_mpsk"), data=data)
    assert resp.status_code == 200

@pytest.mark.parametrize(
    "data",
    (
        {"password": "test"},
        {"name": "a"},
        {"mac": "88:88:88:88:87:88"},
        {"password": "test", "name": "", "mac": "88:88:88:88:87:88"},
        {"password": "test", "name": "", "mac": "FF:FF:FF:FF:FF:FF"},
    ),
)
def test_change_invalid_mpsk(client, data):
    resp = client.post(url_for("usersuite.add_mpsk"), data={"password": "test", "name": "a", "mac": "88:88:88:88:87:88"})
    assert resp.status_code == 302

    resp = client.post(url_for("usersuite.change_mpsk", mpsk_id=0), data=data)
    assert resp.status_code == 200

@pytest.mark.parametrize(
    "data", ({"password": "test", "name": "a", "mac": "88:88:88:88:87:88"},)
)
def test_delete_mpsk(client, data):
    resp = client.post(url_for("usersuite.add_mpsk"), data=data)
    assert resp.status_code == 302

    assert resp.headers["location"] == url_for("usersuite.view_mpsk")
    resp = client.post(
        url_for("usersuite.delete_mpsk", mpsk_id=0), data={"password": "test"}
    )
    assert resp.status_code == 302

    assert resp.headers["location"] == url_for("usersuite.view_mpsk")


def test_usersuite_get_no_mpsks(client):
    client.assert_ok("usersuite.view_mpsk")
    resp = client.get("usersuite.view_mpsk")

    assert "delete-mpsk" not in str(resp)
