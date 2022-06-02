from typing import Protocol


# noinspection PyPropertyDefinition
class UserLike(Protocol):
    @property
    def is_active(self) -> bool: ...

    @property
    def is_authenticated(self) -> bool: ...

    @property
    def is_anonymous(self) -> bool: ...
