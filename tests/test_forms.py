from itertools import permutations
from wtforms import ValidationError, Form, PasswordField
from sipa import forms
from unittest import TestCase


class PasswordComplexityValidatorTest(TestCase):
    class TestForm(Form):
        password = PasswordField()

    def validate(self, validator, password):
        form = self.TestForm(data={'password': password})
        field = form.password
        validator(form, field)

    def test_min_length(self):
        min_length = 4
        assert min_length > 1
        validator = forms.PasswordComplexity(min_length=min_length,
                                             min_classes=1)
        for length in range(min_length):
            with self.assertRaises(ValidationError):
                self.validate(validator, 'a' * length)
        for length in range(min_length, 2 * min_length):
            self.validate(validator, 'a' * length)

    def test_min_classes(self):
        validator = forms.PasswordComplexity(min_length=1, min_classes=2)
        class_representatives = ('a', 'A', '0', '~')
        for representative in class_representatives:
            with self.assertRaises(ValidationError):
                self.validate(validator, representative)
        for permutation in permutations(class_representatives, 2):
            self.validate(validator, ''.join(permutation))
