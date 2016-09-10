import logging
from unittest import TestCase, expectedFailure
from unittest.mock import patch, MagicMock

from flask import Flask
from flask_testing import TestCase as FlaskTestCase
from sqlalchemy.exc import OperationalError

from sipa.model import Backends
from sipa.model.fancy_property import PropertyBase
from sipa.model.pycroft import datasource
from sipa.model.pycroft.schema import User
from sipa.model.sqlalchemy import db
from sipa.model.user import BaseUser
from ..base import TestWhenSubclassedMeta


class PycroftBackendTestCase(TestCase):
    def setUp(self):
        super().setUp()

        app = Flask('test')
        self.backends = Backends()
        app.config['BACKENDS'] = ['pycroft']
        self.backends.init_app(app)
        self.backends.init_backends()

    def test_pycroft_backend_available(self):
        dsrc = self.backends.get_datasource('pycroft')
        self.assertEqual(dsrc, datasource)

    def test_pycroft_only_backend(self):
        self.assertEqual(len(self.backends.datasources), 1)


class PycroftUserClassInheritanceTestCase(TestCase):
    """Ckheck whether the pycroft user class complies with our API.

    This should be refactored so that any arbitrary user class can be
    tested in the same way.
    """
    def setUp(self):
        super().setUp()
        self.User = datasource.user_class

    def test_user_instanciable(self):
        self.User(uid=0)

    def test_user_inherits_from_baseuser(self):
        self.assertTrue(issubclass(self.User, BaseUser))

    def test_user_datasource_is_pycroft(self):
        self.assertEqual(self.User.datasource, datasource)


class PropertyTestMixin(TestCase):
    def assert_is_fancy_property(self, prop):
        self.assertIsInstance(prop, PropertyBase)

    def assert_property_empty(self, prop):
        if not prop.empty:
            self.fail("Property {!r} is not empty".format(prop))

    def assert_property_not_empty(self, prop):
        if prop.empty:
            self.fail("Property {!r} unexpectedly empty".format(prop))

    def assert_property_supported(self, prop):
        if not prop.supported:
            self.fail("Property {!r} unexpectedly not supported".format(prop))

    def assert_property_unsupported(self, prop):
        if prop.supported:
            self.fail("Property {!r} unexpectedly supported".format(prop))


# pylint: disable=no-member
class PropertyAvailableTestCase(PropertyTestMixin, metaclass=TestWhenSubclassedMeta):
    """Generic Tests concerning fancy_property implementations

    The subclass must provide:

        - ``self._user``: The ``BaseUser`` object

        - ``self.supported``, ``self.unsupported``: A list of
          attribute names to be supported / unsupported
          fancy_properties.
    """
    __test__ = False

    @property
    def user(self):
        try:
            return self._user
        except AttributeError as e:
            raise AttributeError("`_user` not provided by subclass") from e

    def test_things_are_fancy_properties(self):
        for prop in self.supported + self.unsupported:
            with self.subTest(prop=prop):
                self.assert_is_fancy_property(getattr(self.user, prop))

    def test_supported_properties(self):
        for prop in self.supported:
            with self.subTest(prop=prop):
                self.assert_property_supported(getattr(self.user, prop))

    def test_unsupported_properties(self):
        for prop in self.unsupported:
            with self.subTest(prop=prop):
                self.assert_property_unsupported(getattr(self.user, prop))


class PycroftUserClassTestCase(PropertyAvailableTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self._user = self.create_user()
        self.supported = ['status', 'login', 'mac', 'address', 'realname']
        self.unsupported = ['id', 'mail', 'finance_balance', 'hostname', 'hostalias']

    @staticmethod
    def create_user():
        return datasource.user_class(uid=0)

    def test_user_cannot_change_password(self):
        self.assertFalse(self.user.can_change_password)

    def test_user_password_change_raises(self):
        with self.assertRaises(NotImplementedError):
            self.user.change_password(None, None)


class PycroftPgTestBase(FlaskTestCase):
    """A TestBase providing the pycroft backend with postgres

    This TestCase sets up the database and fills it by calling
    :py:meth:`fill_db`.
    """
    def create_app(self):
        app = Flask('sipa')
        backends = Backends()
        app.config['BACKENDS'] = ['pycroft']

        backends.init_app(app)
        backends.init_backends()

        #: The :py:obj:`backends` registered to the app.
        self.backends = backends

        return app

    def setUp(self):
        super().setUp()

        #: The :py:obj:`User` class of the ``'pycroft'`` datasource.
        self.User = self.backends.get_datasource('pycroft').user_class

        #: The :py:obj:`FlaskSQLAlchemy` db object
        self.db = db
        #: The session of :attr:`db`
        self.session = self.db.session

        self.db.create_all()
        self.fill_db()

    @property
    def pycroft_fixtures(self):
        """Dict providing the initial sqlalchemy fixtures

        The keys are classes ``cls`` of the model and values being a
        list of dicts to be passed as keyword arguments to
        ``cls.__init__``.  Naturally, you can pass any callable
        instead of ``cls`` as long as it returns a sqlalchemy object.
        """
        raise NotImplementedError("`pycroft_fixtures` not defined")

    def fill_db(self, orm_objects=None):
        """Fill the database with elements of
        :py:attr:`pycroft_fixtures`.
        """
        for cls, datasets in self.pycroft_fixtures.items():
            for data_dict in datasets:
                obj = cls(**data_dict)
                self.session.add(obj)

        if orm_objects is not None:
            for obj in orm_objects:
                self.session.add(obj)

        self.session.commit()


class PycroftNoFixturesTestBase(PycroftPgTestBase):
    """Subclass of `PycroftPgTestBase` without fixtures."""
    @property
    def pycroft_fixtures(self):
        return {}


class PycroftUserGetTestCase(PycroftPgTestBase, TestCase):
    @property
    def pycroft_fixtures(self):
        return {User: [{
            'login': 'sipa',
            'name': "March mellow",
        }]}

    def setUp(self):
        super().setUp()
        self.user_data = self.pycroft_fixtures[User].pop()
        self.user = self.User.get(self.user_data['login'])

    def test_user_get_returns_user(self):
        self.assertIsInstance(self.user, self.User)

    def test_user_got_correct_uid(self):
        self.assertEqual(self.user.uid, self.user_data['login'])

    def test_user_got_correct_login(self):
        self.assertEqual(self.user.login, self.user_data['login'])


class PycroftUserFetchFailedTestCase(PycroftNoFixturesTestBase, TestCase):
    def setUp(self):
        super().setUp()

        def _raise_runtimeerror(*_):
            """Function to mock the db object"""
            raise RuntimeError()

        self.db_mock = MagicMock()
        self.db_mock.session.query.side_effect = _raise_runtimeerror

    def test_runtimeerror_passed_and_logged(self):
        with patch('sipa.model.pycroft.user.db', self.db_mock), \
                self.assertRaises(RuntimeError), \
                self.assertLogs(logging.getLogger('sipa.model.pycroft.user'),
                                level="WARNING") as cm:
            user = self.User.get('sipa')
            # pylint: disable=pointless-statement
            user.pg_object

        self.assertTrue(self.db_mock.session.query.called)

        self.assertEqual(len(cm.output), 1)
        last_log = cm.output.pop()
        self.assertIn("RuntimeError caught", last_log)


class PycroftUserORMFetchTestCase(PycroftNoFixturesTestBase, TestCase):
    def setUp(self):
        super().setUp()
        self.prepared_pg_user = User(login="sipa", name="test")
        #: The user obtained by ``User.get``
        self.user_gotten = self.User.get('sipa')

    def test_empty_db_has_no_user(self):
        with self.assertRaises(RuntimeError):
            # pylint: disable=pointless-statement
            self.user_gotten.pg_object

    def test_db_returns_correct_user(self):
        self.fill_db(orm_objects=[self.prepared_pg_user])
        self.assertEqual(self.user_gotten.pg_object, self.prepared_pg_user)

    def test_does_not_access_db_a_second_time(self):
        self.fill_db(orm_objects=[self.prepared_pg_user])
        # initial call to init caching
        # pylint: disable=pointless-statement
        self.user_gotten.pg_object
        db.drop_all()

        try:
            self.assertTrue(self.user_gotten.pg_object)
        except (RuntimeError, OperationalError) as e:
            self.fail("`{}` raised instead of loading cached object"
                      .format(type(e).__name__))
