from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from sipa.model.mspk_client import MPSKClientEntry


class UserData(BaseModel):
    id: int
    user_id: str
    login: str
    name: str
    status: UserStatus
    room: str | None
    mail: str | None
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
    mpsk_clients: list[MPSKClientEntry]


class UserStatus(BaseModel):
    member: bool
    traffic_exceeded: bool
    network_access: bool
    account_balanced: bool
    violation: bool


class Interface(BaseModel):
    id: int
    mac: str
    ips: list[str]


class TrafficHistoryEntry(BaseModel):
    timestamp: str
    ingress: int | None
    egress: int | None


class FinanceHistoryEntry(BaseModel):
    valid_on: str
    amount: Decimal
    description: str


