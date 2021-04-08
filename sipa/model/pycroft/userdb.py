import logging
from ipaddress import IPv4Address, AddressValueError

from flask import current_app
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from sipa.model.user import BaseUserDB
from sipa.backends.exceptions import InvalidConfiguration

logger = logging.getLogger(__name__)


class UserDB(BaseUserDB):
    def __init__(self, user):
        super().__init__(user)

        mask = current_app.config.get('DB_HELIOS_IP_MASK')
        self.test_ipmask_validity(mask)
        self.ip_mask = mask

    @staticmethod
    def test_ipmask_validity(mask):
        """Test whether a valid ip mask (at max one consecutive '%') was given

        This is being done by replacing '%' with the maximum possible
        value ('255').  Thus, everything surrounding the '%' except
        for dots causes an invalid IPv4Address and thus a
        `ValueError`.
        """
        try:
            IPv4Address(mask.replace("%", "255"))
        except AddressValueError:
            raise ValueError("Mask {} is not a valid IP address or contains "
                             "more than one consecutive '%' sign".format(mask))

    @staticmethod
    def sql_query(query, args=()):
        """Prepare and execute a raw sql query.
        'args' is a tuple needed for string replacement.
        """
        database = current_app.extensions['db_helios']
        # Connection.__enter__ returns Cursor, Cursor.__enter__ returns itself
        # and we need both things for their `__exit__` commands
        with database.connect() as cursor, cursor:
            result = cursor.execute(query, args)
        return result

    @property
    def has_db(self):
        try:
            userdb = self.sql_query(
                "SELECT SCHEMA_NAME "
                "FROM INFORMATION_SCHEMA.SCHEMATA "
                "WHERE SCHEMA_NAME = %s",
                (self.db_name(),),
            ).fetchone()

            return userdb is not None
        except OperationalError:
            logger.critical("User db of user %s unreachable", self.db_name(),
                            exc_info=True)
            return None

    def create(self, password):
        self.sql_query(
            "CREATE DATABASE "
            "IF NOT EXISTS `%s`" % self.db_name(),
        )
        self.change_password(password)

    def drop(self):
        self.sql_query(
            "DROP DATABASE "
            "IF EXISTS `%s`" % self.db_name(),
        )

        self.sql_query(
            "DROP USER %s@%s",
            (self.db_name(), self.ip_mask),
        )

    def change_password(self, password):
        user = self.sql_query(
            "SELECT user "
            "FROM mysql.user "
            "WHERE user = %s",
            (self.db_name(),),
        ).fetchall()

        if not user:
            self.sql_query(
                "CREATE USER %s@%s "
                "IDENTIFIED BY %s",
                (self.db_name(), self.ip_mask, password,),
            )
        else:
            self.sql_query(
                "SET PASSWORD "
                "FOR %s@%s = PASSWORD(%s)",
                (self.db_name(), self.ip_mask, password,),
            )

        self.sql_query(
            "GRANT SELECT, INSERT, UPDATE, DELETE, "
            "ALTER, CREATE, DROP, INDEX, LOCK TABLES "
            "ON `{}`.* "
            "TO %s@%s".format(self.db_name()),
            (self.db_name(), self.ip_mask),
        )

    def db_name(self):
        return self.user.login.value


def register_userdb_extension(app):
    try:
        app.extensions['db_helios'] = create_engine(
            app.config['DB_HELIOS_URI'],
            echo=False, connect_args={'connect_timeout': app.config['SQL_TIMEOUT']}
        )
    except KeyError as exception:
        raise InvalidConfiguration(*exception.args)
