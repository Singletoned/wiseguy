# -*- coding: utf-8 -*-

import functools

from sqlalchemy import (Column, Table, String, Integer, ForeignKey, MetaData)
from sqlalchemy.orm import mapper, relation, backref

import sqlalchemy as sa

uri = "sqlite:///"

metadata = MetaData()
engine = sa.create_engine(uri)
metadata.bind = engine
Session = sa.orm.sessionmaker(bind=engine)

article_table = Table("Article", metadata,
    Column('stub', String(16), primary_key=True),
    Column('name', String(64)),
    Column('body', String),
    Column('score', Integer),
)

comment_table = Table("Comment", metadata,
    Column('id', Integer, primary_key=True),
    Column('article_stub', String(16), ForeignKey('Article.stub')),
    Column('email', String(128)),
    Column('name', String(128)),
    Column('body', String),
)

class BaseTable(object):
    @classmethod
    def create(cls, **kwargs):
        item = cls()
        item.from_dict(kwargs)
        return item

    @classmethod
    def add_or_update(cls, session, data):
        p_keys = cls._sa_class_manager.mapper.primary_key
        p_key_names = [key.name for key in p_keys]
        p_key = [data[key_name] for key_name in p_key_names]
        item = session.query(cls).get(p_key)
        if not item:
            item = cls()
        item.from_dict(data)
        session.add(item)
        return item

    def from_dict(self, d):
        for key, value in d.items():
            setattr(self, key, value)

    def to_dict(self):
        return dict(
            (k, getattr(self, k)) for k in self.__dict__.keys()
                if not k.startswith("_"))


class Article(BaseTable):
    pass

class Comment(BaseTable):
    pass

mapper(Article, article_table)

mapper(Comment, comment_table)

classes = [Article, Comment]

def with_empty_db(func):
    @functools.wraps(func)
    def decorated():
        Session.close_all()
        engine.dispose()
        metadata.create_all()
        func()
    return decorated

metadata.create_all()
