from abc import abstractmethod
from itertools import permutations

import pytest

from sipa import forms
from wtforms import Form, PasswordField, ValidationError, StringField


class FormTestBase(Form):
    password = PasswordField()


class TestPasswordComplexityValidation:
    __abstract__ = True

    @pytest.fixture(scope="class")
    def validate(self, validator):
        def validate_(password):
            form = FormTestBase(data={"password": password})
            field = form.password
            validator(form, field)

        return validate_

    @abstractmethod
    def validator(self):
        ...


class TestMinLength(TestPasswordComplexityValidation):
    MIN_LENGTH = 4

    @pytest.fixture(scope="class")
    def validator(self):
        return forms.PasswordComplexity(min_length=self.MIN_LENGTH, min_classes=1)

    @pytest.mark.parametrize("pw", ["a" * i for i in range(MIN_LENGTH)])
    def test_min_length_reject(self, pw, validate):
        with pytest.raises(ValidationError):
            validate(pw)

    @pytest.mark.parametrize("pw", ["a" * i for i in range(MIN_LENGTH, 2 * MIN_LENGTH)])
    def test_min_length_accept(self, pw, validate):
        try:
            validate(pw)
        except ValidationError:
            pytest.fail()


class TestMinClasses(TestPasswordComplexityValidation):
    REPRESENTATIVES = ("a", "A", "0", "~")

    @pytest.fixture(scope="class")
    def validator(self):
        return forms.PasswordComplexity(min_length=1, min_classes=2)

    @pytest.mark.parametrize("pw", REPRESENTATIVES)
    def test_min_classes_reject(self, pw, validate):
        with pytest.raises(ValidationError):
            validate(pw)

    @pytest.mark.parametrize(
        "pw", ["".join(p) for p in permutations(REPRESENTATIVES, 2)]
    )
    def test_min_classes_accept(self, pw, validate):
        try:
            validate(pw)
        except ValidationError:
            pytest.fail()


class MACTestForm(Form):
    mac = StringField()
    hostname = StringField()


class TestMacUnicastVadator:
    @pytest.fixture(scope="class")
    def validatemac(self):
        def validatemac_(mac):
            form = MACTestForm(data={"mac": mac, "hostname": "hostname"})
            filemac = form.mac
            forms.require_unicast_mac(form, filemac)

        return validatemac_

    @pytest.mark.parametrize(
        "mac",
        [
            "tt:tt:tt:tt:tt:tt",
            "0z:80:41:ae:fd:7e",
            "0+:80:41:ae:fd:7e",
            "awda ssfsfwa",
            "a",
            "ab",
            "0d-80-41-ae-fd-7e",
            "0f-80-41-ae-fd-7e"
        ],
    )
    def test_bad_macs(self, mac, validatemac):
        with pytest.raises(ValidationError):
            validatemac(mac)

    @pytest.mark.parametrize(
        "mac",
        ["00:80:41:ae:fd:7e", "00-80-41-ae-fd-7e", "008041-aefd7e", "0080.41ae.fd7e"],
    )
    def test_good_macs(self, mac, validatemac):
        try:
            validatemac(mac)
        except ValidationError:
            pytest.fail()
