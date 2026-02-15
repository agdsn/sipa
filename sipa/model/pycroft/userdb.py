import logging
import typing as t
from dataclasses import dataclass

from flask import current_app
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.exc import OperationalError

from sipa.backends.exceptions import InvalidConfiguration
from sipa.config.typed_config import Mask

logger = logging.getLogger(__name__)


@t.final
@dataclass(frozen=True)
class UserDB:
    dbname: str
    ip_mask: Mask
    database: Engine

    # TODO pass cursor explicitly or encapsulate in ctor
    @staticmethod
    def sql_query(query: str, args=()):
        """Prepare and execute a raw sql query.

        :param query: See :py:meth:`pymysql.cursors.Cursor.execute`.
        :param args: is a tuple needed for string replacement.
            See :py:meth:`pymysql.cursors.Cursor.execute`.
        """
        database: Engine = current_app.extensions["db_helios"]
        # Connection.__enter__ returns Cursor, Cursor.__enter__ returns itself
        # and we need both things for their `__exit__` commands
        with database.connect() as cursor, cursor:
            result = cursor.execute(query, args)
        return result

    @property
    def has_db(self):
        try:
            userdb = self.sql_query(
                "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s",
                (self.dbname,),
            ).fetchone()

            return userdb is not None
        except OperationalError:
            logger.critical("User db of user %s unreachable", self.dbname, exc_info=True)
            return None

    def create(self, password):
        self.sql_query(
            "CREATE DATABASE IF NOT EXISTS `%s`" % self.dbname,
        )
        self.change_password(password)

    def drop(self):
        self.sql_query(
            "DROP DATABASE IF EXISTS `%s`" % self.dbname,
        )
        self.sql_query(
            "DROP USER %s@%s",
            (self.dbname, self.ip_mask),
        )

    def change_password(self, password):
        user = self.sql_query(
            "SELECT user FROM mysql.user WHERE user = %s",
            (self.dbname,),
        ).fetchall()

        if not user:
            self.sql_query(
                "CREATE USER %s@%s IDENTIFIED BY %s",
                (
                    self.dbname,
                    self.ip_mask,
                    password,
                ),
            )
        else:
            self.sql_query(
                "SET PASSWORD FOR %s@%s = PASSWORD(%s)",
                (
                    self.dbname,
                    self.ip_mask,
                    password,
                ),
            )

        self.sql_query(
            "GRANT SELECT, INSERT, UPDATE, DELETE, "
            "ALTER, CREATE, DROP, INDEX, LOCK TABLES "
            f"ON `{self.dbname}`.* "
            "TO %s@%s",
            (self.dbname, self.ip_mask),
        )


def register_userdb_extension(app):
    # TODO replace by registering a helios_engine on `app.state`
    try:
        app.extensions['db_helios'] = create_engine(
            app.config['DB_HELIOS_URI'],
            echo=False, connect_args={'connect_timeout': app.config['SQL_TIMEOUT']},
            pool_recycle=app.config['SQL_CONNECTION_RECYCLE'],
        )
    except KeyError as exception:
        raise InvalidConfiguration(*exception.args) from None
