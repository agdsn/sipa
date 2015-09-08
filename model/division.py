from ipaddress import IPv4Network


def empty_function(app):
    pass


class Division(object):
    """Division object Providing its name and the User object.

    """
    def __init__(self, name, display_name, user_class, mail_server,
                 subnets=[],
                 init_context=empty_function,
                 debug_only=False):
        super(Division, self).__init__()
        self.name = name
        self.display_name = display_name
        self.user_class = user_class
        self.mail_server = mail_server
        self.subnets = SubnetCollection(subnets)
        self._init_context = init_context
        self.debug_only = debug_only

    def init_context(self, app):
        return self._init_context(app)


class SubnetCollection(object):
    """A simple class providing `ip in division.subnets`-like functionality."""

    def __init__(self, subnets):
        if type(subnets) == list:
            for subnet in subnets:
                if not isinstance(subnet, IPv4Network):
                    raise TypeError(u"List of IPv4Network objects expected "
                                    "in SubnetCollection.__init__")
        else:
            raise TypeError(u"List expected in SubnetCollection.__init__")

        self.subnets = subnets

    def __contains__(self, address):
        for subnet in self.subnets:
            if address in subnet:
                return True
        return False


class Dormitory:
    """A dormitory as selectable on the login page."""

    def __init__(self, name, display_name, division):
        # TODO: add subnet functionality
        self.name = name
        self.display_name = display_name
        self.division = division
