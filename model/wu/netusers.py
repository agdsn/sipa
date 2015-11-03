# -*- coding: utf-8; -*-
from sqlalchemy import (Column, Index, Integer, String,
                        text, ForeignKey, DECIMAL, BigInteger)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Nutzer(Base):
    __tablename__ = 'nutzer'
    __table_args__ = (
        Index(u'zimmer', u'etage', u'zimmernr'),
    )

    nutzer_id = Column(Integer, primary_key=True, server_default=text("'0'"))
    wheim_id = Column(Integer, nullable=False, index=True,
                      server_default=text("'0'"))
    etage = Column(Integer, nullable=False, server_default=text("'0'"))
    zimmernr = Column(String(10), nullable=False, server_default=text("''"))
    unix_account = Column(String(40), nullable=False, unique=True)
    status = Column(Integer, nullable=False, index=True,
                    server_default=text("'1'"))

    computer = relationship("Computer", backref="nutzer")


class Computer(Base):
    __tablename__ = 'computer'

    nutzer_id = Column(Integer, ForeignKey('nutzer.nutzer_id'), nullable=False)

    c_etheraddr = Column(String(20), primary_key=True)
    c_ip = Column(String(15), nullable=False, index=True, primary_key=True,
                  server_default=text("''"))
    c_hname = Column(String(20), nullable=False, server_default=text("''"))
    c_alias = Column(String(20))


class Credit(Base):
    __tablename__ = u'credit'

    user_id = Column(Integer, primary_key=True, nullable=False)
    amount = Column(Integer, nullable=False)
    timetag = Column(Integer, primary_key=True, nullable=False)


class Traffic(Base):
    __tablename__ = 'tuext'

    timetag = Column(BigInteger(), primary_key=True)
    ip = Column(String(15), nullable=False, index=True, primary_key=True)
    input = Column(DECIMAL(20, 0))
    output = Column(DECIMAL(20, 0))
