# -*- coding: utf-8 -*-
from typing import Any, Dict


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


def unserializer(cls: type) -> type:
    annotations = {canonicalize_key(key): val
                   for key, val in getattr(cls, '__annotations__', {}).items()}
    setattr(cls, '__annotations__', annotations)

    # noinspection Mypy
    @property
    def _json_keys(self):
        return self.__annotations__.keys()  # TODO we might exclude some things

    _maybe_setattr(cls, '_json_keys', _json_keys)

    def __init__(self, dict_like: dict):
        # TODO read `Optional` attributes
        missing_keys = self._json_keys - set(dict_like.keys())
        if missing_keys:
            raise MissingKeysError(f"Missing {len(missing_keys)} keys:"
                                   f" {', '.join(missing_keys)}")
        # TODO perhaps warn on superfluous keys

        for attrname in self._json_keys:
            val = dict_like[attrname]
            type_ = self.__annotations__[attrname]
            if type_ != Any:
                try:
                    converted = type_(val)
                except (TypeError, ValueError) as e:
                    raise ConversionError(f"Failed to convert {val!r}"
                                          f" to type {type_!r}") from e
            else:
                converted = val
            self.__dict__[attrname] = converted

    _maybe_setattr(cls, '__init__', __init__)

    return cls
