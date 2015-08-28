def empty_function(app):
    pass


class Division(object):
    """Division object Providing its name and the User object.

    """
    def __init__(self, name, display_name, user_class,
                 init_context=empty_function,
                 debug_only=False):
        super(Division, self).__init__()
        self.name = name
        self.display_name = display_name
        self.user_class = user_class
        self._init_context = init_context
        self.debug_only = debug_only

    def init_context(self, app):
        return self._init_context(app)
