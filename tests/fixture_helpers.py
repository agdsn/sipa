# This file contains parts of the module `tests.frontend.fixture_helpers`
# (pycroft@ded11d489de02e8c670990abc46f07beaea064f7)
#  Copyright (c) 2022. The Pycroft Authors. See the AUTHORS file.
#  This file is part of the Pycroft project and licensed under the terms of
#  the Apache License, Version 2.0. See the LICENSE file for details
import contextlib
import random
import string
import typing as t

from flask import url_for, Flask
from sipa import create_app
from sipa.defaults import WARNINGS_ONLY_CONFIG
from .blueprints.assertions import TestClient


@contextlib.contextmanager
def login_context(test_client: TestClient, login: str, password: str):
    test_client.post(
        url_for("generic.login"), data={"username": login, "password": password}
    )
    yield
    test_client.get("generic.logout")


def prepare_app_for_testing(app):
    """Set setting which are relevant for testing.

    * testing / debug mode
    * disable CSRF for WTForms
    * set a random secret key
    * set the server name to `localhost`
    """
    app.testing = True
    app.debug = True
    # Disable the CSRF in testing mode
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SECRET_KEY"] = "".join(
        random.choice(string.ascii_letters) for _ in range(20)
    )
    app.config["SERVER_NAME"] = "localhost.localdomain"
    return app


@contextlib.contextmanager
def _test_client(app: Flask) -> t.Iterator[TestClient]:
    app.test_client_class = TestClient
    with app.app_context(), app.test_client() as c:
        yield c


def make_testing_app(config: dict[str, t.Any] | None = None) -> Flask:
    """app without backends"""
    test_app = Flask("sipa")
    config = config or DEFAULT_TESTING_CONFIG
    return prepare_app_for_testing(create_app(app=test_app, config=config))


DEFAULT_TESTING_CONFIG = {
    "SECRET_KEY": "secret",
    "TESTING": True,
    "LOG_CONFIG": WARNINGS_ONLY_CONFIG,
    "WTF_CSRF_ENABLED": False,
    "PRESERVE_CONTEXT_ON_EXCEPTION": False,
    "CONTACT_SENDER_MAIL": "test@foo.de",
    "MEETINGS_ICAL_URL": "https://agdsn.de/cloud/remote.php/dav/public-calendars/bgiQmBstmfzRdMeH?export",
}
