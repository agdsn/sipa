from abc import abstractmethod
from itertools import permutations

import pytest

from sipa import forms
from wtforms import Form, PasswordField, ValidationError


class TestForm(Form):
    password = PasswordField()


class TestPasswordComplexityValidation:
    __abstract__ = True

    @pytest.fixture(scope="class")
    def validate(self, validator):
        def validate_(password):
            form = TestForm(data={"password": password})
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
