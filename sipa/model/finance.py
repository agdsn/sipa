from abc import ABCMeta, abstractmethod

from flask_babel import gettext

from sipa.model.fancy_property import ActiveProperty, Capabilities
from sipa.units import format_money


class BaseFinanceInformation(metaclass=ABCMeta):
    """A Class bundling the most important finance information.
    """
    @property
    def balance(self):
        if not self.has_to_pay:
            return ActiveProperty('balance', value=gettext("Muss nicht bezahlen"),
                                  raw_value=0, empty=True)
        return ActiveProperty('balance', value=format_money(self._balance),
                              raw_value=self._balance,
                              capabilities=Capabilities(edit=True, delete=False))

    @property
    @abstractmethod
    def _balance(self):
        pass

    @property
    @abstractmethod
    def has_to_pay(self):
        pass

    @property
    @abstractmethod
    def history(self):
        pass

    @property
    @abstractmethod
    def last_update(self):
        pass
