from sqlalchemy import Column, String

from sipa.model.sqlalchemy import db


class Account(db.Model):
    __tablename__ = 'account'
    __bind_key__ = 'hss'

    account = Column(String(16), primary_key=True, nullable=False)
