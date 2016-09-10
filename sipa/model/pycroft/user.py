import logging

from flask_login import AnonymousUserMixin
from sqlalchemy.orm.exc import NoResultFound

from sipa.model.fancy_property import unsupported_prop, active_prop
from ..sqlalchemy import db
from ..user import BaseUser
from .schema import User as PGUser

logger = logging.getLogger(__name__)


class User(BaseUser):
    @classmethod
    def get(cls, username):
        return cls(uid=username)

    def _receive_pg_object(self):
        """Load the corresponding ORM object from the database

        :raises RuntimeError: when the user does not exist in the
            database.

        :returns: The ORM object

        :rtype: :py:obj:``~.schema.User``
        """
        try:
            pg_object = (db.session.query(PGUser)
                         .filter_by(login=self.uid).one())
        except NoResultFound:
            raise RuntimeError("User not available")
        except RuntimeError as e:
            logger.warning("RuntimeError caught when accessing pg_object",
                           extra={'data': {'user': self}})
            raise RuntimeError from e
        else:
            return pg_object

    @property
    def pg_object(self):
        """Cached wrapper for :py:meth:`_receive_pg_object`

        :returns: See :meth:`_receive_pg_object`

        :rtype: See :meth:`_receive_pg_object`
        """
        print("pg_object called")
        try:
            return self._pg_object
        except AttributeError:
            pg_object = self._receive_pg_object()
            self._pg_object = pg_object
            return pg_object

    @classmethod
    def from_ip(cls, ip):
        return AnonymousUserMixin()

    @classmethod
    def authenticate(cls, username, password):
        return AnonymousUserMixin()

    can_change_password = False

    def change_password(self, old, new):
        raise NotImplementedError

    @property
    def traffic_history(self):
        return []

    @property
    def credit(self):
        return 0

    @active_prop
    def realname(self):
        return "Pycroft"

    @active_prop
    def login(self):
        return self.pg_object.login

    @active_prop
    def mac(self):
        return "00:bb:ee:ff:cc:dd"

    @active_prop
    def address(self):
        return "Wundtstraße"

    @active_prop
    def status(self):
        return "Zukunftsfähig"

    @property
    def userdb_status(self):
        raise NotImplementedError

    @property
    def userdb(self):
        raise NotImplementedError

    @property
    def has_connection(self):
        raise NotImplementedError

    @property
    def last_finance_update(self):
        raise NotImplementedError

    @unsupported_prop
    def mail(self):
        raise NotImplementedError

    @unsupported_prop
    def id(self):
        raise NotImplementedError

    @unsupported_prop
    def hostname(self):
        return

    @unsupported_prop
    def hostalias(self):
        return

    @unsupported_prop
    def finance_balance(self):
        raise NotImplementedError
