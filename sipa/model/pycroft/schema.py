# -*- coding: utf-8 -*-
from typing import Any

from sipa.model.pycroft.unserialize import unserializer


@unserializer
class UserData:
    id: int
    user_id: str
    login: str
    realname: str
    # TODO introduce UserStatus when nested unserialization
    status: Any
    room: str
    mail: str
    cache: bool  # TODO test that this works by a `json.loads(json.dumps(foo=True))` test
    traffic_balance: int  # TODO test what comes out there
    traffic_history: Any
    interfaces: Any
    finance_balance: str
    finance_history: Any
    last_finance_update: str  # TODO what type does parse_date expect?

    # TODO introduce properties once they can be excluded
