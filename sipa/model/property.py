from collections import namedtuple
from functools import wraps

from flask_babel import gettext
from abc import ABCMeta, abstractmethod
from sipa.utils import argstr


Capabilities = namedtuple('capabilities', ['edit', 'delete'])
NO_CAPABILITIES = Capabilities(edit=False, delete=False)


class PropertyBase(metaclass=ABCMeta):
    def __init__(self, name, value, raw_value, capabilities=NO_CAPABILITIES,
                 style=None, empty=False):
        self.name = name
        self.value = value
        self.raw_value = raw_value
        self.capabilities = capabilities
        self.style = style
        self.empty = empty or not value

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            name=self.name,
            value=self.value,
            raw_value=self.raw_value,
            capabilities=self.capabilities,
            style=self.style,
            empty=self.empty,
        ))

    @property
    @abstractmethod
    def supported(self):
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


class UnsupportedProperty(PropertyBase):
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


class ActiveProperty(PropertyBase):
    supported = True

    def __init__(self, name, value=None, capabilities=NO_CAPABILITIES,
                 style=None, empty=False):
        # Enforce bootstrap css classes: getbootstrap.com/css/#helper-classes
        assert style in {None, 'muted', 'primary', 'success',
                         'info', 'warning', 'danger'}, \
                         "Style must be a bootstrap class string"

        super().__init__(
            name=name,
            value=(value if value else gettext("Nicht angegeben")),
            raw_value=value,
            capabilities=capabilities,
            style=(style if style  # customly given style is most important
                   else 'muted' if empty or not value
                   else None),
            empty=empty or not value,
        )

    def __repr__(self):
        return "<{cls} {name}='{value}' [{empty}]>".format(
            cls=type(self).__name__,
            name=self.name,
            value=self.value,
            empty=('empty' if self.empty else 'nonempty'),
        )


def unsupported_prop(func):
    return property(lambda self: UnsupportedProperty(name=func.__name__))


class active_prop(property):
    """A property-like class wrapping the getter with class:`ActiveProperty`

    class:`active_prop` automatically adds `edit` and `delete`
    capabilities to the ActiveProperty object if `setter`/`deleter` is
    invoked.

    """

    def __init__(self, fget, fset=None, fdel=None, doc=None,
                 fake_setter=False):
        """Return a property object and wrap fget with `ActiveProperty`.

        The first argument is the function given to `active_prop`
        (perhaps as a decorator).

        `fget` is always wrapped by `ActiveProperty`in a way depending
        of the return value of `fget`.  If it returns

        - Something subscriptable to `'value'`: Pass `['value']` and
          `['style']` (defaults to `None`) to `ActiveProperty`s
          `__init__`, respectively.

        - Something else: Pass it as `value` to `ActiveProperty`s
          `__init__`.

        """
        self.__raw_getter = fget
        self.__fake_setter = fake_setter  # only for the __repr__

        @wraps(fget)
        def wrapped_getter(*args, **kwargs):
            result = fget(*args, **kwargs)
            try:
                value = result['value']
            except TypeError:
                # `KeyError` should not happen, since that means a
                # dict would have been returned not including `value`,
                # which would make no sense and likely is a mistake.
                name = fget.__name__
                value = result
                style = None
                empty = None
                tmp_readonly = False
            else:
                name = result.get('name', fget.__name__)
                style = result.get('style', None)
                empty = result.get('empty', None)
                tmp_readonly = result.get('tmp_readonly', False)

            return ActiveProperty(
                name=name,
                value=value,
                capabilities=Capabilities(
                    edit=(fset is not None or fake_setter),
                    delete=(fdel is not None),
                ) if not tmp_readonly else NO_CAPABILITIES,
                style=style,
                empty=empty,
            )

        # Let `property` handle the initialization of `__get__`, `__set__` etc.
        super().__init__(wrapped_getter, fset, fdel, doc)

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            fget=self.__raw_getter,
            fset=self.fset,
            fdel=self.fdel,
            doc=self.__doc__,
            fake_setter=self.__fake_setter,
        ))

    def getter(self, func):
        return type(self)(func, self.fset, self.fdel, self.__doc__)

    def setter(self, func):
        return type(self)(self.__raw_getter, func, self.fdel, self.__doc__)

    def deleter(self, func):
        return type(self)(self.__raw_getter, self.fset, func, self.__doc__)

    def fake_setter(self):
        return type(self)(self.__raw_getter, self.fset, self.fdel,
                          self.__doc__,
                          fake_setter=True)


def connection_dependent(func):
    """A decorator to “deactivate” the property if the user's not active.
    """

    def _connection_dependent(self, *args, **kwargs):
        if not self.has_connection:
            return {
                'name': func.__name__,
                'value': gettext("Nicht verfügbar"),
                'empty': True,
                'tmp_readonly': True,
            }

        ret = func(self, *args, **kwargs)
        try:
            ret.update({'name': func.__name__})
        except AttributeError:
            ret = {'value': ret, 'name': func.__name__}

        return ret

    return _connection_dependent
