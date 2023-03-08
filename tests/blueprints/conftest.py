# This file contains parts of the module `tests.frontend.conftest`
# (pycroft@ded11d489de02e8c670990abc46f07beaea064f7)
import typing as t

import pytest
from flask import Flask

from sipa import create_app
from sipa.defaults import WARNINGS_ONLY_CONFIG
from .assertions import TestClient
from .fixture_helpers import login_context, prepare_app_for_testing, _test_client


@pytest.fixture(scope="module")
def module_test_client(app: Flask) -> t.Iterator[TestClient]:
    with _test_client(app) as c:
        yield c


@pytest.fixture(scope="class")
def class_test_client(app: Flask) -> t.Iterator[TestClient]:
    with _test_client(app) as c:
        yield c


@pytest.fixture(scope="module")
def user_logged_in(module_test_client: TestClient) -> None:
    """A module-scoped convenience fixture to log in an admin"""
    with login_context(module_test_client, login="test", password="test"):
        yield


@pytest.fixture(scope="session")
def default_config() -> dict[str, t.Any]:
    return {
        "SECRET_KEY": "secret",
        "TESTING": True,
        "LOG_CONFIG": WARNINGS_ONLY_CONFIG,
        "WTF_CSRF_ENABLED": False,
        "PRESERVE_CONTEXT_ON_EXCEPTION": False,
        "CONTACT_SENDER_MAIL": "test@foo.de",
        "MEETINGS_ICAL_URL": "https://agdsn.de/cloud/remote.php/dav/public-calendars/bgiQmBstmfzRdMeH?export",
    }


@pytest.fixture(scope="session")
def bare_app(default_config) -> Flask:
    """app without backends"""
    test_app = Flask("sipa")
    return prepare_app_for_testing(create_app(app=test_app, config=default_config))


@pytest.fixture(scope="session")
def app(default_config) -> Flask:
    """App with `sample` backend"""
    test_app = Flask("sipa")
    return prepare_app_for_testing(
        create_app(app=test_app, config=default_config | {"BACKENDS": ["sample"]})
    )
