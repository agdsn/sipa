# -*- coding: utf-8 -*-
from typing import Any, List
from unittest import TestCase

from sipa.model.pycroft.unserialize import unserializer, MissingKeysError, ConversionError


class UnserializerTest(TestCase):
    def test_basic_unserializer(self):
        @unserializer
        class Foo:
            bar: str

        try:
            f = Foo({'bar': "value"})
        except TypeError:
            self.fail("TypeError raised")
        self.assertEqual(f.bar, "value")

        with self.assertRaises(MissingKeysError):
            Foo({'baz': "something"})

    def test_slash_stripping(self):
        @unserializer
        class Foo:
            type_: str

        with self.assertRaises(MissingKeysError):
            Foo({'type_': "value"})

        try:
            f = Foo({'type': "value"})
        except TypeError:
            self.fail("TypeError raised")
        self.assertEqual(f.type, "value")

    def test_type_conversion(self):
        @unserializer
        class Foo:
            count: int

        with self.assertRaises(ConversionError):
            Foo({'count': "not_an_int"})

    def test_list_cannot_convert(self):
        @unserializer
        class Foo:
            items: List[str]

        with self.assertRaises(ConversionError):
            Foo({'items': ["bar", "baz"]})

    def test_complex_unserializer(self):
        @unserializer
        class Foo:
            name: str
            id_: int
            items: Any

        f = Foo({'name': "Hans", 'id': "555", 'items': ["one", "two"]})
        self.assertEqual(f.name, "Hans")
        self.assertEqual(f.id, 555)
        self.assertEqual(f.items, ["one", "two"])
