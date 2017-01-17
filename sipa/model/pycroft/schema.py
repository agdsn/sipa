from sqlalchemy import Column, String, Integer

from ..sqlalchemy import db


class User(db.Model):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    login = Column(String(40), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
