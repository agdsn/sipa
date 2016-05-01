import logging

from flask.ext.login import AnonymousUserMixin

from ..default import BaseUser
from sipa.model.property import active_prop, unsupported_prop
from sipa.model.sqlalchemy import db
from sipa.model.hss.ldap import HssLdapConnector
from sipa.model.hss.schema import Account, IP
from sipa.utils import argstr
from sipa.utils.exceptions import InvalidCredentials
logger = logging.getLogger(__name__)


class User(BaseUser):
    LdapConnector = HssLdapConnector

    def __init__(self, uid):
        """Initialize the User object.

        Note that init itself is not called directly, but mainly by the
        static methods.

        This method should be called by any subclass.  Therefore,
        prepend `super().__init__(uid)`.  After this, other
        variables like `mail`, `group` or `name` can be initialized
        similiarly.

        :param uid: A unique unicode identifier for the User
        :param name: The real name gotten from the LDAP
        """
        self.uid = uid

    def __eq__(self, other):
        return self.uid == other.uid and self.datasource == other.datasource

    datasource = 'hss'

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            uid=self.uid,
            name=self.realname,
        ))

    @classmethod
    def get(cls, username):
        """Used by user_loader. Return a User instance."""
        return cls(uid=username)

    @classmethod
    def from_ip(cls, ip):
        """Return a user based on an ip.

        If there is no user associated with this ip, return AnonymousUserMixin.
        """
        account_name = db.session.query(IP).filter_by(ip=ip).one().account
        if not account_name:
            return AnonymousUserMixin()

        return cls.get(account_name)

    def re_authenticate(self, password):
        self.authenticate(self.uid, password)

    @classmethod
    def authenticate(cls, username, password):
        """Return a User instance or raise PasswordInvalid"""
        try:
            with HssLdapConnector(username, password) as conn:
                print("conn:", conn)
                user_dict = HssLdapConnector.fetch_user(username,
                                                        connection=conn)
        except InvalidCredentials:  # Covers `UserNotFound`, `PasswordInvalid`
            return AnonymousUserMixin()
        else:
            return cls(uid=username, name=user_dict['name'])

    @property
    def _pg_account(self):
        """Return the corresponding ORM Account"""
        return db.session.query(Account).filter_by(
            account=self.uid
        ).one()

    @property
    def can_change_password(self):
        return False

    def change_password(self, old, new):
        """Change the user's password from old to new.

        Although the password has been checked using
        re_authenticate(), some data sources like those which have to
        perform an LDAP bind need it anyways.
        """
        # TODO: implement password change
        raise NotImplementedError

    @property
    def traffic_history(self):
        """Return the current credit and the traffic history as a dict.

        The history should cover one week. The assumed unit is KiB.

        The dict syntax is as follows:

        return {'credit': 0,
                'history': [(day, <in>, <out>, <credit>)
                            for day in range(7)]}

        """
        # TODO: return useful data
        return {'credit': 0,
                'history': []}

    @property
    def credit(self):
        """Return the current credit in KiB"""
        return self._pg_account.traffic_balance / 1024

    @active_prop
    def ips(self):
        return ", ".join(ip.ip for ip in self._pg_account.ips)

    @property
    def name(self):
        return self.uid

    @active_prop
    def realname(self):
        return self._pg_account.name

    @active_prop
    def login(self):
        return self._pg_account.account

    @active_prop
    def mac(self):
        return ", ".join(mac.mac.lower() for mac in self._pg_account.macs)

    @active_prop
    def mail(self):
        # TODO: implement
        return "foo@bar.baz"

    @active_prop
    def address(self):
        acc = self._pg_account.access
        return "{building} {floor}-{flat}{room}".format(
            floor=acc.floor,
            flat=acc.flat,
            room=acc.room,
            building=acc.building,
        )

    @active_prop
    def status(self):
        return 2

    @unsupported_prop
    def id(self):
        raise NotImplementedError

    @unsupported_prop
    def hostname(self):
        raise NotImplementedError

    @unsupported_prop
    def hostalias(self):
        raise NotImplementedError

    @unsupported_prop
    def userdb_status(self):
        raise NotImplementedError

    @property
    def userdb(self):
        raise NotImplementedError

    @property
    def has_connection(self):
        return False
