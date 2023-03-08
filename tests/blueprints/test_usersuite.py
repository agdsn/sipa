import re
import typing as t
from unittest.mock import patch

import pytest
from flask import url_for
from werkzeug import Response

from sipa.blueprints.usersuite import get_attribute_endpoint
from sipa.model.fancy_property import PropertyBase
from sipa.model.user import Row
from .assertions import TestClient, RenderedTemplate


def test_login_logout(module_test_client: TestClient):
    module_test_client.assert_redirects(
        "generic.login",
        data={
            "dormitory": "localhost",
            "username": "test",
            "password": "test",
        },
        method="POST",
        expected_location=url_for("usersuite.index"),
    )
    module_test_client.assert_redirects(
        "generic.logout", expected_location=url_for("generic.index")
    )


# TODO make this module_based and group by endpoints as classes
@pytest.mark.usefixtures("class_user_logged_in")
class TestUsersuite:
    @pytest.fixture(scope="class")
    def client(self, class_test_client) -> TestClient:
        return class_test_client

    def test_usersuite_reachable(self, client):
        resp = client.get(url_for("usersuite.index"))
        assert resp.status_code == 200

    @pytest.mark.parametrize(
        "endpoint",
        [
            f"usersuite.{x}"
            for x in "index contact change_mac activate_network_access".split()
        ],
    )
    def test_usersuite_endpoint_ok(self, client, endpoint):
        client.assert_ok(endpoint)

    @pytest.fixture(scope="class")
    def _usersuite_index(self, client) -> tuple[Response, RenderedTemplate]:
        with client.renders_template("usersuite/index.html") as recorded:
            resp = client.assert_ok("usersuite.index")
        return resp, recorded[0]

    @pytest.fixture(scope="class")
    def usersuite_response(self, _usersuite_index):
        return _usersuite_index[0]

    @pytest.fixture(scope="class")
    def usersuite_passed_rows(self, _usersuite_index) -> list[Row]:
        return t.cast(list[Row], _usersuite_index[1].context["rows"])

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
        ),
    )
    def test_usersuite_passes_correct_rows(self, usersuite_passed_rows, propname):
        rows = usersuite_passed_rows
        relevant_row = next(row for row in rows if row.property.name == propname)
        assert (
            relevant_row is not None
        ), f"Property {propname} absent from usersuite rows!\n{rows=!r}"
        if propname != "userdb_status":
            assert t.cast(PropertyBase, relevant_row.property).supported

    def test_usersuite_contains_urls(self, usersuite_response):
        """Test the usersuite contains the urls of `sample`s capabilities."""
        # We have to patch `current_user` since it is not defined due
        # to the wrong app context, but the code runs some asserts
        # against it checking capabilities.
        with patch('sipa.blueprints.usersuite.current_user'):
            urls = [
                *(url_for(get_attribute_endpoint(attr))
                  for attr in ['mail', 'mac']),
                *(url_for(get_attribute_endpoint(attr, capability='delete'))
                  for attr in []),
                url_for('usersuite.change_password'),
                url_for('generic.contact'),
            ]

        for url in urls:
            assert re.search(
                f'href="[^"]*{url}[^"]*"', usersuite_response.data.decode()
            ), f"Usersuite does not contain any reference to url {url!r}"
