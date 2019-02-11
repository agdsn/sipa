# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Optional

from sipa.model.pycroft.unserialize import unserializer


@unserializer
class UserData:
    id: int
    user_id: str
    login: str
    name: str
    status: UserStatus
    room: str
    mail: str
    cache: bool
    traffic_balance: int
    traffic_history: List[TrafficHistoryEntry]
    interfaces: List[Interface]
    finance_balance: int
    finance_history: List[FinanceHistoryEntry]
    # TODO implement `cls.Meta.custom_constructors`, use `parse_date` for this
    last_finance_update: str

    # TODO introduce properties once they can be excluded


@unserializer
class UserStatus:
    member: bool
    traffic_exceeded: bool
    network_access: bool
    account_balanced: bool
    violation: bool


@unserializer
class Interface:
    id: int
    mac: str
    ips: List[str]


@unserializer
class TrafficHistoryEntry:
    timestamp: str
    ingress: Optional[int]
    egress: Optional[int]
    balance: Optional[int]


@unserializer
class FinanceHistoryEntry:
    valid_on: str
    amount: int
    description: str
