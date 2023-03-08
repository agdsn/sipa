# This file contains parts of the module `tests.frontend.conftest`
# (pycroft@ded11d489de02e8c670990abc46f07beaea064f7)
import typing as t

import pytest
from flask import Flask

from .assertions import TestClient
from .fixture_helpers import (
    login_context,
    _test_client,
    make_testing_app,
    DEFAULT_TESTING_CONFIG,
)


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
def bare_app() -> Flask:
    """app without backends"""
    return make_testing_app(config=DEFAULT_TESTING_CONFIG)


@pytest.fixture(scope="session")
def app() -> Flask:
    """App with `sample` backend"""
    return make_testing_app(DEFAULT_TESTING_CONFIG | {"BACKENDS": ["sample"]})
