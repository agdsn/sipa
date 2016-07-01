from datetime import datetime
from operator import itemgetter

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import String, Integer, BigInteger, Date, Boolean, Numeric, \
    TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import INET, MACADDR
from sqlalchemy.ext.hybrid import hybrid_property

from sipa.model.sqlalchemy import db
from sipa.model.misc import TransactionTuple


class Account(db.Model):
    __tablename__ = 'account'
    __bind_key__ = 'hss'

    account = Column(String(16), primary_key=True, nullable=False)
    name = Column(String(255), nullable=False)

    finance_balance = Column(Numeric(5, 2), nullable=False, default=0)

    traffic_balance = Column(BigInteger, nullable=False, default=10000000000)
    access_id = Column('access', Integer, ForeignKey('access.id'))

    ips = relationship('IP')
    macs = relationship('Mac')
    traffic_log = relationship('TrafficLog')
    traffic_quota_id = Column('traffic_quota', Integer, ForeignKey('traffic_quota.id'))
    # traffic_quota is available using a backref

    properties = relationship('AccountProperty', uselist=False)

    fees = relationship('AccountFeeRelation')
    transactions = relationship('AccountStatementLog')

    @property
    def combined_transactions(self):
        return sorted([
            *(TransactionTuple(value=-f.fee_object.amount, datum=f.fee_object.timestamp)
              for f in self.fees),
            *(TransactionTuple(value=t.amount, datum=t.timestamp)
              for t in self.transactions),
        ], key=itemgetter(1))


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
        return "<{cls} account='{obj.account}' date='{obj.date}'>".format(
            cls=type(self).__name__,
            obj=self,
        )


class AccountStatementLog(db.Model):
    __tablename__ = 'account_statement_log'
    __bind_key__ = 'hss'

    id = Column(Integer, primary_key=True, nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False)
    amount = Column(Numeric(5, 2), nullable=False)
    purpose = Column(String(255), nullable=False)
    account = Column(String(16), ForeignKey('account.account'))


class AccountFeeRelation(db.Model):
    __tablename__ = 'account_fee_relation'
    __bind_key__ = 'hss'

    account = Column(String(16), ForeignKey('account.account'), nullable=False)
    fee = Column(Integer, ForeignKey('fee_info.id'), nullable=False)
    fee_object = relationship('FeeInfo', uselist=False)

    __mapper_args__ = {'primary_key': (account, fee)}


class FeeInfo(db.Model):
    __tablename__ = 'fee_info'
    __bind_key__ = 'hss'

    id = Column(Integer, primary_key=True, nullable=False)
    amount = Column(Numeric(5, 2), nullable=False)
    description = Column(String(255), nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False)


class TrafficQuota(db.Model):
    __tablename__ = 'traffic_quota'
    __bind_key__ = 'hss'

    id = Column(Integer, primary_key=True)
    daily_credit = Column(BigInteger, nullable=False, default=0)
    max_credit = Column(BigInteger, nullable=False, default=0)
    description = Column(String(255), nullable=False)
    accounts = relationship('Account', backref='traffic_quota')

    def __repr__(self):
        return ("<{cls} #{obj.id} daily={obj.daily_credit} max={obj.max_credit} "
                "'{obj.description}'>".format(
                    cls=type(self).__name__,
                    obj=self,
                ))
