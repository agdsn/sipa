# -*- coding: utf-8 -*-
import inspect
import sys
from typing import Callable, Optional, Any, List, Union


class UnserializationError(Exception):
    pass


class MissingKeysError(KeyError, UnserializationError):
    pass


class ConversionError(TypeError, UnserializationError):
    pass


def canonicalize_key(key: str) -> str:
    return key[:-1] if key.endswith('_') else key


def _maybe_setattr(cls, attrname, attr):
    if attrname in cls.__dict__:
        return
    setattr(cls, attrname, attr)


NoneType = type(None)


def _is_optional(t):
    return getattr(t, '__origin__', None) is Union and \
           len(t.__args__) == 2 and t.__args__[1] is NoneType


MAXDEPTH = 100


def constructor_from_generic(name: str, args: tuple, *a, **kw) -> Optional[Callable]:
    """
    :param name:  Something like 'List' (like from `List[int]._name`)
    :param args: Something like `(int,)` from (`List[int].__args__`)
    :return: A constructor callable or None
    """
    if name == Any._name:
        def constructor(val):
            return val

    elif name == List._name:
        if len(args) == 1:
            item_constructor = constructor_from_annotation(args[0], *a, **kw)

            def constructor(val):
                return [item_constructor(i) for i in val]
        else:
            raise UnserializationError("Cannot find constructor for List[A, ...]"
                                       " with more than one argument.")
    elif name == Optional._name:
        if len(args) >= 1:
            item_constructor = constructor_from_annotation(args[0], *a, **kw)

            def constructor(val):
                return item_constructor(val) if val is not None else None
        else:
            raise UnserializationError("Cannot find constructor for Optional[...]"
                                       " with less than one argument.")
    else:
        raise UnserializationError(f"Generic type '{name}' not supported")

    return constructor


def constructor_from_annotation(type_, module, maxdepth=MAXDEPTH) -> Callable:
    """Use the value of an annotation to return an appropriate constructor"""
    if maxdepth <= 0:
        raise UnserializationError(
            "Maxdepth exceeded when trying to lookup constructors."
            f" the default is {MAXDEPTH}."
        )

    # un-stringification by eval'ing in module scope
    if isinstance(type_, str):
        try:
            type_ = eval(type_, module.__dict__, None)
        except NameError:
            raise UnserializationError(f"Unable to look up type {type_!r}"
                                       f" in module {module.__name__!r}")

    constructor: Optional[Callable] = None

    # Case 1: known generic
    if hasattr(type_, '_name'):
        type_name = type_._name
        if _is_optional(type_):
            type_name = Optional._name
        constructor = constructor_from_generic(type_name, getattr(type_, '__args__', ()),
                                               module=module, maxdepth=maxdepth-1)

    # cases 2, 3: Is an unserializer or something builtin
    elif inspect.isclass(type_):
        constructor = type_

    if not constructor:
        raise UnserializationError(f"Could not find constructor for type {type_!r}")

    return constructor


def unserializer(cls: type) -> type:
    """A class decorator providing a magic __init__ method"""
    annotations = {canonicalize_key(key): val
                   for key, val in getattr(cls, '__annotations__', {}).items()}
    setattr(cls, '__annotations__', annotations)

    # noinspection Mypy
    @property
    def _json_keys(self):
        return self.__annotations__.keys()  # TODO we might exclude some things

    _maybe_setattr(cls, '_json_keys', _json_keys)

    def __init__(self, dict_like: dict = None):
        if not dict_like:
            dict_like = {}

        # TODO read `Optional` attributes
        module = sys.modules[type(self).__module__]
        constructor_map = {key: constructor_from_annotation(type_=val,
                                                            module=module)
                           for key, val in self.__annotations__.items()}

        missing_keys = set(constructor_map.keys()) - set(dict_like.keys())
        if missing_keys:
            raise MissingKeysError(
                f"Missing {len(missing_keys)} keys"
                f" to construct {type(self).__name__}:"
                f" {', '.join(missing_keys)}"
            )
        # TODO perhaps warn on superfluous keys

        for attrname, constructor in constructor_map.items():
            val = dict_like[attrname]
            if not constructor or val is None:
                converted = val
            else:
                try:
                    converted = constructor(val)
                except (TypeError, ValueError) as e:
                    typename = self.__annotations__[attrname]
                    raise ConversionError(f"Failed to convert {val!r}"
                                          f" to type {typename!r}") from e

            self.__dict__[attrname] = converted

    _maybe_setattr(cls, '__init__', __init__)

    return cls
