from collections import namedtuple
from flask.ext.babel import gettext
from abc import ABCMeta, abstractmethod
from sipa.utils import argstr


Capabilities = namedtuple('capabilities', ['edit', 'delete'])
no_capabilities = Capabilities(edit=None, delete=None)


class PropertyBase(metaclass=ABCMeta):
    def __init__(self, name, value, raw_value, capabilities=no_capabilities,
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
        try:
            return all((
                self.name == other.name,
                self.value == other.value,
                self.capabilities == other.capabilities,
                self.style == other.style,
                self.empty == other.empty,
            ))
        except AttributeError:
            return False


class UnsupportedProperty(PropertyBase):
    supported = False

    def __init__(self, name):
        super(UnsupportedProperty, self).__init__(
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
        return self.name == other.name


class ActiveProperty(PropertyBase):
    supported = True

    def __init__(self, name, value=None, capabilities=no_capabilities,
                 style=None, empty=False):
        # Enforce bootstrap css classes: getbootstrap.com/css/#helper-classes
        assert style in {None, 'muted', 'primary', 'success',
                         'info', 'warning', 'danger'}, \
                         "Style must be a bootstrap class string"

        super(ActiveProperty, self).__init__(
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
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            name=self.name,
            value=self.value,
            capabilities=self.capabilities,
            style=self.style,
            empty=self.empty,
        ))


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

        def wrapped_getter(*args, **kwargs):
            result = fget(*args, **kwargs)
            try:
                value = result['value']
            except TypeError:
                # `KeyError` should not happen, since that means a
                # dict would have been returned not including `value`,
                # which would make no sense and likely is a mistake.
                value = result
                style = None
                empty = None
                tmp_readonly = False
            else:
                style = result.get('style', None)
                empty = result.get('empty', None)
                tmp_readonly = result.get('tmp_readonly', False)

            return ActiveProperty(
                name=fget.__name__,
                value=value,
                capabilities=Capabilities(
                    edit=(fset is not None or fake_setter),
                    delete=(fdel is not None),
                ) if not tmp_readonly else no_capabilities,
                style=style,
                empty=empty,
            )

        # Let `property` handle the initialization of `__get__`, `__set__` etc.
        super(active_prop, self).__init__(wrapped_getter, fset, fdel, doc)

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
