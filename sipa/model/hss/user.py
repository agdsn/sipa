from ..default import BaseUser

from flask.ext.login import AnonymousUserMixin

from sipa.model.property import active_prop, unsupported_prop
from sipa.utils import argstr


class User(BaseUser):

    def __init__(self, uid):
        """Initialize the User object.

        Note that init itself is not called directly, but mainly by the
        static methods.

        This method should be called by any subclass.  Therefore,
        prepend `super().__init__(uid)`.  After this, other
        variables like `mail`, `group` or `name` can be initialized
        similiarly.

        :param uid:A unique unicode identifier for the User
        """
        self.uid = uid

    def __eq__(self, other):
        return self.uid == other.uid and self.datasource == other.datasource

    datasource = 'hss'

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            uid=self.uid,
            name=self.name,
            # mail=self._mail,
        ))

    @classmethod
    def get(cls, username):
        """Used by user_loader. Return a User instance."""
        # TODO: fetch user from ldap
        return cls(username)

    @classmethod
    def from_ip(cls, ip):
        """Return a user based on an ip.

        If there is no user associated with this ip, return AnonymousUserMixin.
        """
        # TODO: return correct user from IP
        return AnonymousUserMixin()

    def re_authenticate(self, password):
        self.authenticate(self.uid, password)

    @classmethod
    def authenticate(cls, username, password):
        """Return a User instance or raise PasswordInvalid"""
        # TODO: check password / user
        return cls(username)

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
        # TODO: return useful data
        return 42

    @active_prop
    def ips(self):
        return "141.30.228.39"

    @property
    def name(self):
        return self.uid

    @active_prop
    def realname(self):
        return "Foo bar"

    @active_prop
    def login(self):
        return self.name

    @active_prop
    def mac(self):
        return "AA:BB:CC:DD:EE:FF"

    @active_prop
    def mail(self):
        return "foo@bar.baz"

    @active_prop
    def address(self):
        return "Keller"

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
