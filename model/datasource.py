from ipaddress import IPv4Network
from sipa.utils import argstr


def empty_function(app):
    pass


class DataSource:
    """DataSource object Providing its name and the User object.

    """
    def __init__(self, name, display_name, user_class, mail_server,
                 support_mail=None,
                 init_context=empty_function,
                 debug_only=False):
        super(DataSource, self).__init__()
        self.name = name
        self.display_name = display_name
        self.user_class = user_class
        self.mail_server = mail_server
        self.support_mail = (support_mail if support_mail
                             else "support@{}".format(mail_server))
        self._init_context = init_context
        self.debug_only = debug_only

    def __eq__(self, other):
        return self.name == other.name

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            name=self.name,
            display_name=self.display_name,
            user_class=self.user_class,
            mail_server=self.mail_server,
            support_mail=self.support_mail,
            init_context=self._init_context,
            debug_only=self.debug_only,
        ))

    def init_context(self, app):
        return self._init_context(app)


class SubnetCollection:
    """A simple class for combining multiple IPv4Networks.

    Provides __contains__ functionality for IPv4Addresses.
    """

    def __init__(self, subnets):
        if type(subnets) == list:
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


class Dormitory:
    """A dormitory as selectable on the login page."""

    def __init__(self, name, display_name, datasource, subnets=[]):
        self.name = name
        self.display_name = display_name
        self.datasource = datasource
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


class PrematureDataSource:
    """A dormitory not yet supported by SIPA"""

    def __init__(self, name, display_name, website_url, support_mail):
        self.name = name
        self.display_name = display_name
        self.website_url = website_url
        self.support_mail = support_mail

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            name=self.name,
            display_name=self.display_name,
            website_url=self.website_url,
            support_mail=self.support_mail,
        ))
