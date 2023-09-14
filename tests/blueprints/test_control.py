import pytest

from tests.assertions import TestClient

pytestmark = pytest.mark.usefixtures("user_logged_in")


@pytest.fixture(scope="module")
def client(module_test_client) -> TestClient:
    return module_test_client


@pytest.mark.parametrize(
        "ip_responses",
        [
            ("1.1", "die IP scheint keine valide IP Adresse zu sein"),
            ("0z:80:41:ae:fd:7e", "die IP scheint keine valide IP Adresse zu sein"),
            ("0+:80:41:ae:fd:7e", "die IP scheint keine valide IP Adresse zu sein"),
            ("awda ssfsfwa", "die IP scheint keine valide IP Adresse zu sein"),
            ("a", "die IP scheint keine valide IP Adresse zu sein"),
            ("ab", "die IP scheint keine valide IP Adresse zu sein"),
            ("1000", "die IP scheint keine valide IP Adresse zu sein"),
            ("1.6.7.","die IP scheint keine valide IP Adresse zu sein"),
            ("192.169.10.1", "die angegebene IP gehört nicht zu deinem Subnetz")
        ],
    )
def test_invalid_ip(client, ip_responses):
        resp = client.post("/control/ip", data={"ip_address": ip_responses[0]})
        assert resp.status_code == 200
        assert ip_responses[1] in resp.data.decode("UTF-8")


def test_valid_ip(client):
    for i in range(1, 254):
        ip = "192.168.10." + str(i)
        resp = client.post("/control/ip", data={"ip_address": ip})
        assert resp.status_code == 200
        assert "" == resp.data.decode("UTF-8")


@pytest.mark.parametrize(
        "port",
        [
            ("1.99", "der Port muss eine Nummer sein"),
            ("0z:80:41:ae:fd:7e", "der Port muss eine Nummer sein"),
            ("awda ssfsfwa", "der Port muss eine Nummer sein"),
            ("a", "der Port muss eine Nummer sein"),
            ("ab", "der Port muss eine Nummer sein"),
            ("0", "der Port muss größer als 0 sein"),
            ("-10", "der Port muss eine Nummer sein"),
            ("65536", "der Port muss kleiner als 65536 sein"),
            ("65735", "der Port muss kleiner als 65536 sein")
        ],
    )
def test_invalid_port(client, port):
    resp = client.post("/control/port", data={"port": port[0]})
    assert resp.status_code == 200
    assert port[1] in resp.data.decode("UTF-8")


def test_valid_port(client):
    for i in range(1, 65536):
        resp = client.post("/control/port", data={"port": i})
        assert resp.status_code == 200
        assert "" == resp.data.decode("UTF-8")
