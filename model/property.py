from collections import namedtuple
from flask.ext.babel import lazy_gettext


Capabilities = namedtuple('capabilities', ['edit', 'delete'])
no_capabilities = Capabilities(edit=None, delete=None)


class PropertyBase:
    # TODO: how's that “warning/mute/etc.” bootstrap stuff called? “context”?
    def __init__(self, name, value, capabilities=no_capabilities, style=None):
        self.name = name
        self.value = value
        # TODO: Where to store the links? perhaps a generic route?
        self.capabilities = capabilities
        # TODO: shall we include more (semantic) information in `style`?
        # e.g. to use `<em>` when unsupported etc.
        self.style = style


class UnsupportedProperty(PropertyBase):
    def __init__(self, name):
        super(UnsupportedProperty, self).__init__(
            # TODO: is lazy_gettext necessary?
            name=name,
            value=lazy_gettext("Nicht unterstützt"),
            style='muted',
        )


class ActiveProperty(PropertyBase):
    def __init__(self, name, value=None, capabilities=no_capabilities):
        super(ActiveProperty, self).__init__(
            name=name,
            value=(value if value else lazy_gettext("Nicht angegeben")),
            capabilities=capabilities,
            style=('muted' if not value else None),
        )


def unsupported_prop(func):
    def _unsupported_prop(*args, **kwargs):
        # TODO: is this the best way? shouldn't this be rather the
        # default in BaseUser?
        return UnsupportedProperty(name=func.__name__)

    return _unsupported_prop


class active_prop(property):
    """A property-like class wrapping the getter with class:`ActiveProperty`

    class:`active_prop` automatically adds `edit` and `delete`
    capabilities to the ActiveProperty object if `setter`/`deleter` is
    invoked.

    """

    # TODO: support (pass) custom things like color etc.
    def __init__(self, fget, fset=None, fdel=None, doc=None):
        """Return a property object and wrap fget with `ActiveProperty`.

        The first argument is the function given to `active_prop`
        (perhaps as a decorator).
        """

        # fget is supposed to be the non-wrapped function
        self.__raw_getter = fget

        def wrapped_getter(*args, **kwargs):
            return ActiveProperty(
                name=fget.__name__,
                value=fget(*args, **kwargs),
                capabilities=Capabilities(edit=(fset is not None),
                                          delete=(fdel is not None)),
            )

        # Let `property` handle the initialization of `__get__`, `__set__` etc.
        super(active_prop, self).__init__(wrapped_getter, fset, fdel, doc)

    def getter(self, func):
        return type(self)(func, self.fset, self.fdel, self.__doc__)

    def setter(self, func):
        return type(self)(self.__raw_getter, func, self.fdel, self.__doc__)

    def deleter(self, func):
        return type(self)(self.__raw_getter, self.fset, func, self.__doc__)
