from __future__ import annotations

import typing as t


class TableRow(t.NamedTuple):
    """Represents a Row in on the user pages Table"""

    property: str
    description: str
    subtext: str | None = None
