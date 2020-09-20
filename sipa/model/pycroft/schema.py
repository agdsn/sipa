# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date
from decimal import Decimal
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
    mail_forwarded: bool
    mail_confirmed: bool
    properties: List[str]
    traffic_history: List[TrafficHistoryEntry]
    interfaces: List[Interface]
    finance_balance: Decimal
    finance_history: List[FinanceHistoryEntry]
    # TODO implement `cls.Meta.custom_constructors`, use `parse_date` for this
    last_finance_update: str

    # TODO introduce properties once they can be excluded

    membership_end_date: str
    membership_begin_date: str
    wifi_password: Optional[str]


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


@unserializer
class FinanceHistoryEntry:
    valid_on: str
    amount: Decimal
    description: str
