import pytest

from sipa.model.fancy_property import ActiveProperty
from sipa.model.finance import BaseFinanceInformation


def test_baseinfo_abc_instantiation():
    # noinspection PyAbstractClass
    class InvalidInfo(BaseFinanceInformation):  # pylint: disable=abstract-method
        pass

    with pytest.raises(TypeError):
        InvalidInfo()  # pylint: disable=abstract-class-instantiated


class TestNoNeedToPay:
    class DisabledFinanceInformation(BaseFinanceInformation):
        has_to_pay = False
        raw_balance = 0
        history = []
        last_update = None
        last_received_update = None

    @pytest.fixture(scope="class")
    def finance_info(self) -> BaseFinanceInformation:
        return self.DisabledFinanceInformation()

    def test_has_correct_balance(self, finance_info):
        balance = finance_info.balance
        assert balance.empty
        assert "inbegriffen" in balance.value.lower()


class TestStaticBalance:
    class StaticFinanceInformation(BaseFinanceInformation):
        has_to_pay = True
        raw_balance = 30
        history = []
        last_update = None
        last_received_update = None

    @pytest.fixture(scope="class")
    def balance(self) -> ActiveProperty:
        return self.StaticFinanceInformation().balance

    def test_has_correct_balance(self, balance):
        assert not balance.empty
        assert "30" in balance.value
        assert balance.raw_value == 30

    def test_balance_not_editable(self, balance):
        assert not balance.capabilities.edit

    def test_balance_not_deletable(self, balance):
        assert not balance.capabilities.delete
