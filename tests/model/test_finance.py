from unittest import TestCase

from sipa.model.finance import BaseFinanceInformation


class EverythingMissingTestCase(TestCase):
    class InvalidInfo(BaseFinanceInformation):  # pylint: disable=abstract-method
        pass

    def test_cannot_inherit_base(self):
        with self.assertRaises(TypeError):
            self.InvalidInfo()  # pylint: disable=abstract-class-instantiated


class NoNeedToPayTestCase(TestCase):
    class DisabledFinanceInformation(BaseFinanceInformation):
        has_to_pay = False
        raw_balance = 0
        history = []
        last_update = None

    def test_instanciation_works(self):
        self.DisabledFinanceInformation()

    def test_has_correct_balance(self):
        balance = self.DisabledFinanceInformation().balance
        self.assertTrue(balance.empty)
        self.assertIn("inbegriffen", balance.value.lower())


class StaticBalanceTestCase(TestCase):
    class StaticFinanceInformation(BaseFinanceInformation):
        has_to_pay = True
        raw_balance = 30
        history = []
        last_update = None

    def setUp(self):
        super().setUp()
        self.balance = self.StaticFinanceInformation().balance

    def test_has_correct_balance(self):
        self.assertFalse(self.balance.empty)
        self.assertIn('30', self.balance.value)
        self.assertEqual(self.balance.raw_value, 30)

    def test_balance_editable(self):
        self.assertTrue(self.balance.capabilities.edit)

    def test_balance_not_deletable(self):
        self.assertFalse(self.balance.capabilities.delete)
