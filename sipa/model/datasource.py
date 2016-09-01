import logging
from ipaddress import IPv4Network

from sipa.utils import argstr
from .misc import xor_hashes, compare_all_attributes

logger = logging.getLogger(__name__)


class DataSource:
    """DataSource object Providing its name and the User object.

    """
    def __init__(self, name, user_class, mail_server,
                 webmailer_url=None,
                 support_mail=None,
                 init_context=None):
        super().__init__()
        self.name = name

        class _user_class(user_class):
            datasource = self
        self.user_class = _user_class

        self.mail_server = mail_server
        self.webmailer_url = webmailer_url
        self.support_mail = (support_mail if support_mail
                             else "support@{}".format(mail_server))
        self._init_context = init_context
        self._dormitories = {}

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
        return xor_hashes(self.name, self.user_class, self.support_mail, self.mail_server)

    def register_dormitory(self, dormitory):
        name = dormitory.name
        if name in self._dormitories:
            raise ValueError("Dormitory {} already registered", name)
        self._dormitories[name] = dormitory

    @property
    def dormitories(self):
        """A list of all registered dormitories.

        :rtype: list of ``Dormitory`` instances
        :returns: the registered dormitories
        """
        return list(self._dormitories.values())

    def init_context(self, app):
        """Initialize this backend

            - Apply the custom configuration of
              :py:def:`app.config['BACKENDS_CONFIG'][self.name]`

            - Call :py:meth:`_init_context(app)` as given in the
              config

        The custom config supports the following keys:

            - ``support_mail``: Set ``self.support_mail``

        If an unknown key is given, a warning will be logged.

        :param Flask app: the app to initialize against
        """
        # copy the dict so we can freely ``pop`` things
        config = app.config.get('BACKENDS_CONFIG', {}).get(self.name, {}).copy()

        try:
            self.support_mail = config.pop('support_mail')
        except KeyError:
            pass

        for key in config.keys():
            logger.warning("Ignoring unknown key '%s'", key,
                           extra={'data': {'config': config}})

        if self._init_context:
            return self._init_context(app)


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
        return xor_hashes(*self.subnets)


class Dormitory:
    """A dormitory as selectable on the login page."""

    def __init__(self, name, display_name, datasource, subnets=None):
        self.name = name
        self.display_name = display_name
        self.datasource = datasource
        datasource.register_dormitory(self)
        self.subnets = SubnetCollection(subnets if subnets else [])

    def __repr__(self):
        return "{}.{}({})".format(__name__, type(self).__name__, argstr(
            name=self.name,
            display_name=self.display_name,
            datasource=self.datasource,
            subnets=self.subnets.subnets,
        ))

    def __eq__(self, other):
        return compare_all_attributes(self, other, ['name', 'datasource'])

    def __hash__(self):
        return xor_hashes(self.name, self.display_name, self.datasource, self.subnets)


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
