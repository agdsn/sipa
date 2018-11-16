class InvalidConfiguration(IndexError):
    pass


class BackendError(RuntimeError):
    def __init__(self, backend_name: str, *a, **kw):
        self.backend_name = backend_name
        super().__init__(*a, **kw)
