# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, List
from unittest import TestCase

from sipa.model.pycroft.unserialize import unserializer, MissingKeysError, ConversionError, \
    UnserializationError


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

    def test_list_can_convert(self):
        @unserializer
        class Foo:
            items: List[str]

        try:
            f = Foo({'items': ["bar", "baz"]})
        except ConversionError:
            self.fail()
        else:
            self.assertEqual(f.items, ["bar", "baz"])

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


@unserializer
class Note:
    id_: int
    name: str


@unserializer
class Bar:  # We need to dofine this at module level so the lookup works
    description: str
    notes: List[Note]


@unserializer
class Baz:
    inner: Bar


class NestedUnserializationTest(TestCase):
    def setUp(self):
        self._bar_cls = Bar
        try:
            self.baz = Baz({'inner': {'description': "Beschreibung",
                                      'notes': [{'id': 1, 'name': "a"},
                                                {'id': 2, 'name': "b"}]}})
        except UnserializationError as e:
            self.fail(f"Unserialization failed: {e}")

    def test(self):
        self.assertIsInstance(self.baz.inner, self._bar_cls)
        self.assertEqual(self.baz.inner.description, "Beschreibung")
        notes = self.baz.inner.notes
        self.assertEqual(len(notes), 2)
        self.assertEqual(notes[0].name, "a")
        self.assertEqual(notes[0].id, 1)
        self.assertEqual(notes[1].name, "b")
        self.assertEqual(notes[1].id, 2)
