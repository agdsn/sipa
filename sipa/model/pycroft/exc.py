from sipa.backends.exceptions import BackendError


class PycroftBackendError(BackendError):
    def __init__(self, *a, **kw):
        super().__init__('pycroft', *a, **kw)
