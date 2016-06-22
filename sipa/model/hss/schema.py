from datetime import datetime

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import String, Integer, BigInteger, Date, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import INET, MACADDR
from sqlalchemy.ext.hybrid import hybrid_property

from sipa.model.sqlalchemy import db


class Account(db.Model):
    __tablename__ = 'account'
    __bind_key__ = 'hss'

    account = Column(String(16), primary_key=True, nullable=False)
    name = Column(String(255), nullable=False)

    # Not needed now, staying in the code for https://git.io/vw1bH though.
    # finance_balance = Column(Numeric(5, 2), nullable=False, default=0)

    traffic_balance = Column(BigInteger, nullable=False, default=10000000000)
    access_id = Column('access', Integer, ForeignKey('access.id'))

    ips = relationship('IP')
    macs = relationship('Mac')
    traffic_log = relationship('TrafficLog')

    properties = relationship('AccountProperty', uselist=False)


class AccountProperty(db.Model):
    __tablename__ = 'account_property'
    __bind_key__ = 'hss'

    account = Column(String(16), ForeignKey('account.account'),
                     primary_key=True, nullable=False)
    active = Column(Boolean, nullable=False)


class Access(db.Model):
    __tablename__ = 'access'
    __bind_key__ = 'hss'

    id = Column(Integer, primary_key=True, nullable=False)
    building = Column(String(16))  # e.g. "HSS46"
    floor = Column(String(8))  # e.g. "0"
    flat = Column(String(8))  # e.g. "1"
    room = Column(String(8))  # e.g. "b"

    users = relationship('Account', backref='access')


class IP(db.Model):
    __tablename__ = 'ip'
    __bind_key__ = 'hss'

    ip = Column(INET, primary_key=True)
    account = Column(String(16), ForeignKey('account.account'))


class Mac(db.Model):
    __tablename__ = 'mac'
    __bind_key__ = 'hss'

    id = Column(Integer, primary_key=True)
    mac = Column(MACADDR, nullable=False)
    account = Column(String(16), ForeignKey('account.account'))


class TrafficLog(db.Model):
    __tablename__ = 'traffic_log'
    __bind_key__ = 'hss'

    id = Column(Integer, primary_key=True)
    account = Column(String(16), ForeignKey('account.account'))

    date = Column(Date, nullable=False)
    bytes_in = Column(BigInteger, nullable=False, default=0)
    bytes_out = Column(BigInteger, nullable=False, default=0)

    def __repr__(self):
        return "<{type} account='{obj.account}' date='{obj.date}'>".format(
            type=type(self),
            obj=self,
        )


class TrafficQuota(db.Model):
    __tablename__ = 'traffic_quota'
    __bind_key__ = 'hss'

    id = Column(Integer, primary_key=True)
    daily_credit = Column(BigInteger, nullable=False, default=0)
    max_credit = Column(BigInteger, nullable=False, default=0)
    description = Column(String(255), nullable=False)
