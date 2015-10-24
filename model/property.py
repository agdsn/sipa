from collections import namedtuple
from flask.ext.babel import gettext


Capabilities = namedtuple('capabilities', ['edit', 'delete'])
no_capabilities = Capabilities(edit=None, delete=None)


class PropertyBase:
    def __init__(self, name, value, capabilities=no_capabilities,
                 style=None, empty=False):
        self.name = name
        self.value = value
        self.capabilities = capabilities
        self.style = style
        self.empty = empty or not value

    def __repr__(self):
        return ("{}.{}(name='{}', value='{}', capabilities={}, "
                "style='{}', empty={})"
                .format(__name__, type(self).__name__,
                        self.name, self.value, self.capabilities,
                        self.style, self.empty))


class UnsupportedProperty(PropertyBase):
    def __init__(self, name):
        super(UnsupportedProperty, self).__init__(
            name=name,
            value=gettext("Nicht unterstützt"),
            style='muted',
            empty=True,
        )

    def __repr__(self):
        return ("{}.{}(name='{}')"
                .format(__name__, type(self).__name__, self.name))


class ActiveProperty(PropertyBase):
    def __init__(self, name, value=None, capabilities=no_capabilities,
                 style=None, empty=False):
        # Enforce bootstrap css classes: getbootstrap.com/css/#helper-classes
        assert style in {None, 'muted', 'primary', 'success',
                         'info', 'warning', 'danger'}, \
                         "Style must be a bootstrap class string"

        super(ActiveProperty, self).__init__(
            name=name,
            value=(value if value else gettext("Nicht angegeben")),
            capabilities=capabilities,
            style=(style if style  # customly given style is most important
                   else 'muted' if empty or not value
                   else None),
            empty=empty or not value,
        )

    def __repr__(self):
        return ("{}.{}(name='{}', value='{}', capabilities={}, "
                "style='{}', empty={})"
                .format(__name__, type(self).__name__,
                        self.name, self.value, self.capabilities,
                        self.style, self.empty))


def unsupported_prop(name):
    return property(lambda self: UnsupportedProperty(name=name))


class active_prop(property):
    """A property-like class wrapping the getter with class:`ActiveProperty`

    class:`active_prop` automatically adds `edit` and `delete`
    capabilities to the ActiveProperty object if `setter`/`deleter` is
    invoked.

    """

    # TODO: support (pass) custom things like color etc.
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
            else:
                style = result.get('style', None)
                empty = result.get('empty', None)

            return ActiveProperty(
                name=fget.__name__,
                value=value,
                capabilities=Capabilities(
                    edit=(fset is not None or fake_setter),
                    delete=(fdel is not None),
                ),
                style=style,
                empty=empty,
            )

        # Let `property` handle the initialization of `__get__`, `__set__` etc.
        super(active_prop, self).__init__(wrapped_getter, fset, fdel, doc)

    def __repr__(self):
        return ("{}.{}(fget={}, fset={}, fdel={}, doc='{}', fake_setter={})"
                .format(__name__, type(self).__name__,
                        self.__raw_getter, self.fset, self.fdel, self.__doc__,
                        self.__fake_setter))

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
