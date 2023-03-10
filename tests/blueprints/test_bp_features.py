from unittest.mock import patch, MagicMock

import pytest

from tests.assertions import TestClient


@pytest.fixture(scope="module")
def client(module_test_client):
    return module_test_client


def test_bustimes(client: TestClient):
    # TODO test this properly: refactor external API access into service, test parsing
    with client.renders_template("bustimes.html"), patch(
        "sipa.blueprints.features.get_bustimes", mock := MagicMock()
    ):
        client.assert_ok("features.bustimes")
    assert mock.called


def test_meetingcal(client: TestClient):
    with client.renders_template("meetingcal.html"):
        resp = client.assert_ok("features.render_meetingcal")
    assert "Teamsitzung" in resp.data.decode()
