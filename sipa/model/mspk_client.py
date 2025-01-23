from dataclasses import dataclass


@dataclass(frozen=True)
class MPSKClientEntry:
    mac: str
    name: str
    id: int
