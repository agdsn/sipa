from abc import ABCMeta, abstractmethod
from datetime import timedelta

from flask_babel import gettext

from sipa.model.fancy_property import ActiveProperty
from sipa.units import format_money
from sipa.utils import compare_all_attributes


class BaseFinanceInformation(metaclass=ABCMeta):
    """A Class providing finance information about a user.

    This class bundles informations such as whether the current user
    is obliged to pay, the current balance, history, and the time of
    the last update.  The balance is being provided as a
    FancyProperty, so it can be used as a row.

    For subclassing, implement the respective abstract
    methods/properties.
    """

    @property
    def balance(self) -> ActiveProperty[str, float]:
        """The current balance as a
        :py:class:`~sipa.model.fancy_property.ActiveProperty`

        If :attr:`has_to_pay` is False, return an empty property with
        the note that the user doesn't have to pay.  Else, return the
        balance formatted and styled (red/green) as money and mark
        this property editable.
        """
        if not self.has_to_pay:
            return ActiveProperty('finance_balance',
                                  value=gettext("Beitrag in Miete inbegriffen"),
                                  raw_value=0, empty=True)
        return ActiveProperty('finance_balance',
                              value=format_money(self.raw_balance),
                              raw_value=self.raw_balance)

    @property
    @abstractmethod
    def raw_balance(self) -> float:
        """The current balance

        If :py:meth:`has_to_pay` is False, this method will not be
        used implicitly.
        """
        pass

    @property
    @abstractmethod
    def has_to_pay(self) -> bool:
        """Whether the user is obliged to pay."""
        pass

    @property
    @abstractmethod
    def history(self):
        """History of payments

        This method should return an iterable of a (datetime, int, description)
        tuple.
        """
        pass

    @property
    @abstractmethod
    def last_update(self):
        """The time of the last update."""
        pass

    @property
    def last_received_update(self):
        last_update = self.last_update
        weekday = last_update.toordinal() % 7
        match weekday:
            case 6:
                return last_update - timedelta(days=2)
            case 7:
                return last_update - timedelta(days=3)
            case 1:
                return last_update - timedelta(days=3)
            case _:
                return last_update - timedelta(days=1)

    def __eq__(self, other):
        return compare_all_attributes(self, other, ['raw_balance', 'has_to_pay',
                                                    'history', 'last_update'])
