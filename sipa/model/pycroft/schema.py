from __future__ import annotations

from datetime import date
from decimal import Decimal

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
    properties: list[str]
    traffic_history: list[TrafficHistoryEntry]
    interfaces: list[Interface]
    finance_balance: Decimal
    finance_history: list[FinanceHistoryEntry]
    last_finance_update: date

    # TODO introduce properties once they can be excluded

    birthdate: date | None
    membership_end_date: date | None
    membership_begin_date: date | None
    wifi_password: str | None


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
    ips: list[str]


@unserializer
class TrafficHistoryEntry:
    timestamp: str
    ingress: int | None
    egress: int | None


@unserializer
class FinanceHistoryEntry:
    valid_on: str
    amount: Decimal
    description: str
