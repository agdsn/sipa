from flask import url_for

from tests.assertions import TestClient


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
