from ipaddress import IPv4Network
from sipa.utils import argstr


class DataSource:
    """DataSource object Providing its name and the User object.

    """
    def __init__(self, name, user_class, mail_server,
                 webmailer_url=None,
                 support_mail=None,
                 init_context=None):
        super().__init__()
        self.name = name
        self.user_class = user_class
        self.mail_server = mail_server
        self.webmailer_url = webmailer_url
        self.support_mail = (support_mail if support_mail
                             else "support@{}".format(mail_server))
        self._init_context = init_context
        self.dormitories = {}

    def __eq__(self, other):
        return self.name == other.name

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            name=self.name,
            user_class=self.user_class,
            mail_server=self.mail_server,
            webmailer_url=self.webmailer_url,
            support_mail=self.support_mail,
            init_context=self._init_context,
        ))

    def __hash__(self):
        return (
            hash(self.name) ^
            hash(self.user_class) ^
            hash(self.support_mail) ^
            hash(self.mail_server)
        )

    def register_dormitory(self, dormitory):
        name = dormitory.name
        if name in self.dormitories:
            raise ValueError("Dormitory {} already registered", name)
        self.dormitories[name] = dormitory

    def init_context(self, app):
        if self._init_context:
            return self._init_context(app)

        return


class SubnetCollection:
    """A simple class for combining multiple IPv4Networks.

    Provides __contains__ functionality for IPv4Addresses.
    """

    def __init__(self, subnets):
        if isinstance(subnets, list):
            for subnet in subnets:
                if not isinstance(subnet, IPv4Network):
                    raise TypeError("List of IPv4Network objects expected "
                                    "in SubnetCollection.__init__")
        else:
            raise TypeError("List expected in SubnetCollection.__init__")

        self.subnets = subnets

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            subnets=self.subnets,
        ))

    def __contains__(self, address):
        for subnet in self.subnets:
            if address in subnet:
                return True
        return False

    def __eq__(self, other):
        return self.subnets == other.subnets

    def __hash__(self):
        _hash = 0
        for subnet in self.subnets:
            _hash ^= hash(subnet)

        return _hash


class Dormitory:
    """A dormitory as selectable on the login page."""

    def __init__(self, name, display_name, datasource, subnets=[]):
        self.name = name
        self.display_name = display_name
        self.datasource = datasource
        datasource.register_dormitory(self)
        self.subnets = SubnetCollection(subnets)

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            name=self.name,
            display_name=self.display_name,
            datasource=self.datasource,
            subnets=self.subnets.subnets,
        ))

    def __eq__(self, other):
        return self.name == other.name and self.datasource == other.datasource

    def __hash__(self):
        return (
            hash(self.name) ^
            hash(self.display_name) ^
            hash(self.datasource) ^
            hash(self.subnets)
        )


class PrematureDataSource:
    """A dormitory not yet supported by SIPA"""

    def __init__(self, name, website_url, support_mail):
        self.name = name
        self.website_url = website_url
        self.support_mail = support_mail

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            name=self.name,
            website_url=self.website_url,
            support_mail=self.support_mail,
        ))
