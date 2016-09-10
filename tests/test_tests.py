from operator import itemgetter
from unittest import TestCase
from unittest.mock import MagicMock

from .base import TestWhenSubclassedMeta, subtests_over


class SubclassesTestCase(TestCase):
    def test_subclass_resetted(self):
        class Base(metaclass=TestWhenSubclassedMeta):
            __test__ = False

        class C(Base):
            pass

        self.assertTrue(C.__test__)
        self.assertIn('__test__', C.__dict__)

    def test_subclass_not_resetted(self):
        class Base(metaclass=TestWhenSubclassedMeta):
            __test__ = True

        class C(Base):
            pass

        self.assertTrue(C.__test__)
        self.assertNotIn('__test__', C.__dict__)

    def test_subclass_attr_not_set(self):
        class Base(metaclass=TestWhenSubclassedMeta):
            pass

        class C(Base):
            pass

        with self.assertRaises(AttributeError):
            getattr(C, '__test__')


class SubTestForAllTestCase(TestCase):
    subtest_mock = MagicMock()

    class Foo:
        subTest = MagicMock()

        def __init__(self):
            self.result = []

        @property
        def params(self, ):
            return {'key': ['foo', 'bar', 'baz']}

        @subtests_over('params', getter=itemgetter('key'))
        def to_be_repeated(self, param):
            self.result = [param] + self.result

    def test_subtests_called(self):
        mock = self.Foo.subTest

        obj = self.Foo()
        # pylint: disable=no-value-for-parameter
        obj.to_be_repeated()

        self.assertTrue(mock.called)
        self.assertEqual(len(mock.call_args_list), len(obj.params['key']))
        self.assertEqual(obj.result, list(reversed(obj.params['key'])))
