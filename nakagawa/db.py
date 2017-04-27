#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, Unicode
from sqlalchemy.pool import NullPool

Base = declarative_base()
session = None
engine = None


def init_db(db_file):
    global engine
    engine = create_engine('sqlite:///' + str(db_file), poolclass=NullPool)
    Session = sessionmaker(bind=engine)
    global session
    session = Session()
    Base.metadata.create_all(engine)


def get_session():
    return session


class ThreadTable(Base):
    __tablename__ = 'thread'
    id = Column(Integer, primary_key=True)
    board_id = Column(Unicode(512), nullable=False)
    thread_id = Column(Integer, nullable=False)
    err404 = Column(Integer, nullable=False)
    limit = Column(Integer, nullable=False)

    def __repr__(self):
        return "<Thread(board_id='%s', thread_id='%s', err404='%s')>" % (self.board_id, self.thread_id, self.err404)


class UrlsTable(Base):
    __tablename__ = 'urls'
    id = Column(Integer, primary_key=True)
    url = Column(Unicode(512), nullable=False)

    def __repr__(self):
        return "<Urls(id='%s', url='%s')>" % (self.id, self.url)
