from dataclasses import dataclass


@dataclass(frozen=true)
class MPSKClientEntry:
    mac: str
    name: str
    id: int
