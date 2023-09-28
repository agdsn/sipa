import typing as t
from dataclasses import dataclass
from functools import wraps

from flask_babel import gettext
from abc import ABC, abstractmethod
from sipa.utils import argstr


class Capabilities(t.NamedTuple):
    edit: bool
    delete: bool

    @classmethod
    def edit_if(cls, condition: bool) -> t.Self:
        return cls(edit=condition, delete=False)

    @classmethod
    def edit_delete_if(cls, condition: bool) -> t.Self:
        return cls(edit=condition, delete=condition)


NO_CAPABILITIES = Capabilities(edit=False, delete=False)

TVal = t.TypeVar("TVal")
TRawVal = t.TypeVar("TRawVal")


STYLE = t.Literal[
    "muted",
    "primary",
    "success",
    "info",
    "warning",
    "danger",
    "password",
]


@dataclass
class PropertyBase(ABC, t.Generic[TVal, TRawVal]):
    name: str
    value: TVal
    raw_value: TRawVal = None
    capabilities: Capabilities = NO_CAPABILITIES
    style: STYLE | None = None
    # TODO actually is not None due to post_init. More elegantly solved with
    # separate `InitVar`
    empty: bool | None = None
    description_url: str | None = None

    def __post_init__(self):
        if self.empty is None:
            self.empty = not bool(self.value)

    @property
    @abstractmethod
    def supported(self) -> bool:
        pass

    def __eq__(self, other):
        """Check other for equality in each important attribute. If this is
        failing, compare against `self.raw_value`
        """
        try:
            return all((
                self.name == other.name,
                self.value == other.value,
                self.capabilities == other.capabilities,
                self.style == other.style,
                self.empty == other.empty,
            ))
        except AttributeError:
            return self.raw_value == other

    def __contains__(self, item):
        return self.raw_value.__contains__(item)

    def __bool__(self):
        """The boolean value represents whether the property is not empty"""
        return not self.empty


class UnsupportedProperty(PropertyBase[str, None]):
    supported = False

    def __init__(self, name):
        super().__init__(
            name=name,
            value=gettext("Nicht unterstützt"),
            raw_value=None,
            style='muted',
            empty=True,
        )

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            name=self.name
        ))

    def __eq__(self, other):
        try:
            return self.name == other.name
        except AttributeError:
            return False


class ActiveProperty(PropertyBase[TVal, TRawVal]):
    supported = True

    def __post_init__(self):
        if self.empty is None:
            self.empty = not bool(self.value)
        if self.raw_value is None:
            self.raw_value = self.value
        if self.value is None:
            self.value = gettext("Nicht angegeben")
        if self.style is None:
            self.style = "muted" if self.empty else None

    def __repr__(self):
        return "<{cls} {name}='{value}' [{empty}]>".format(
            cls=type(self).__name__,
            name=self.name,
            value=self.value,
            empty=('empty' if self.empty else 'nonempty'),
        )


def unsupported_prop(func):
    import warnings

    warnings.warn(
        "unsupported_prop is deprecated. directly return UnsupportedProperty instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return property(lambda self: UnsupportedProperty(name=func.__name__))


def connection_dependent_(func):
    """A decorator to “deactivate” the property if the user's not active."""

    @wraps(func)
    def _connection_dependent(self, *args, **kwargs) -> ActiveProperty:
        if not self.has_connection:
            return ActiveProperty(
                name=func.__name__,
                value=gettext("Nicht verfügbar"),
                empty=True,
                capabilities=NO_CAPABILITIES,
            )

        ret = func(self, *args, **kwargs)
        return ret

    return _connection_dependent
