import logging
import typing as t
import re
from base64 import urlsafe_b64encode
from os import urandom
from typing import cast
from unittest import TestCase
from unittest.mock import MagicMock

from ipaddress import IPv4Network

import pytest
from flask import Flask

from sipa.backends import Backends, DataSource, Dormitory, InitContextCallable


class TestBackendInitializationCase(TestCase):
    def setUp(self):
        super().setUp()
        self.app = Flask("sipa")
        self.app.config["BACKEND"] = "foo"
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        dormitory = Dormitory(
            name="test", display_name="", subnets=[IPv4Network("127.0.0.0/8")]
        )
        datasource = DataSource(
            name='foo',
            user_class=object,
            mail_server="",
            webmailer_url="",
            support_mail="",
            init_context=lambda app: None,
            dormitories=[dormitory],
        )
        self.backends = Backends([datasource])
        self.backends.init_app(self.app)
        self.backends.init_backends()

    def test_extension_registrated(self):
        assert 'backends' in self.app.extensions

    def assert_dormitories_namelist(self, list, base):
        """Asserts whether the list consists of (str, str) tuples

        …and has the correct length
        """
        assert len(list) == len(base)
        for name, display_name in list:
            assert isinstance(name, str)
            assert isinstance(display_name, str)

    def test_get_dormitory(self):
        for dormitory in self.backends.dormitories:
            assert self.backends.get_dormitory(dormitory.name) == dormitory

        possible_names = [
            dorm.name for dorm in self.backends.dormitories
        ]

        for str_length in range(10):
            random_string = None
            while random_string in possible_names:
                random_string = urlsafe_b64encode(urandom(str_length))

            assert self.backends.get_dormitory(random_string) is None

    def test_dormitory_from_ip(self):
        for dorm in self.backends.dormitories:
            first_ip = next(dorm.subnets.subnets[0].hosts())

            assert self.backends.dormitory_from_ip(first_ip) == dorm

        # TODO: Find an ip not in any dormitory


class TestDataSource:
    @pytest.fixture(scope="class")
    def app(self):
        app = MagicMock()
        app.config = {}
        return app

    @pytest.fixture(scope="class")
    def default_args(self) -> dict[str, t.Any]:
        return {
            'name': 'test',
            'user_class': object,
            'mail_server': "",
            "dormitories": [],
        }

    def test_init_context_gets_called_correctly(self, default_args, app):
        init_mock = cast(InitContextCallable, MagicMock())
        datasource = DataSource(
            **default_args,
            init_context=init_mock,
        )

        datasource.init_context(app)
        assert init_mock.call_args[0] == (app,)

    @pytest.fixture(scope="function")
    def datasource(self, default_args) -> DataSource:
        return DataSource(**default_args)

    def test_init_context_reads_mail(self, datasource, app):
        config = {"support_mail": "bazingle.foo@shizzle.xxx"}
        app.config["BACKENDS_CONFIG"] = {datasource.name: config}

        datasource.init_context(app)

        assert datasource.support_mail == config["support_mail"]

    def test_init_context_warns_on_unknown_keys(
        self, datasource, app, caplog: pytest.LogCaptureFixture
    ):
        RE_UNKNOWN_KEY = re.compile("ignoring unknown key", flags=re.IGNORECASE)
        bad_keys = ['unknown', 'foo', 'bar', 'mail']
        bad_config = {key: None for key in bad_keys}
        app.config["BACKENDS_CONFIG"] = {datasource.name: bad_config}

        caplog.set_level(logging.WARNING, logger="sipa.backend")
        datasource.init_context(app)

        for record in caplog.records:
            assert re.match(RE_UNKNOWN_KEY, record.message)
            assert any(
                key in record.message for key in bad_keys
            ), "Log warning raised not containing any of the given invalid keys"
