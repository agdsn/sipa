from unittest import TestCase

from .base import TestWhenSubclassedMeta


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
