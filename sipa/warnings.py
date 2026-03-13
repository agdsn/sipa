import warnings


def jinja_warn(msg: str) -> None:
    warnings.warn(msg, FastAPIIncompleteWarning, stacklevel=5)


class FastAPIIncompleteWarning(Warning): ...
