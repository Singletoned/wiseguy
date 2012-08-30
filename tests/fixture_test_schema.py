# -*- coding: utf-8 -*-

import functools

from sqlalchemy import (Column, Table, String, Integer, ForeignKey, MetaData)
from sqlalchemy.orm import mapper, relation, backref

import sqlalchemy as sa

uri = "sqlite:///dev.sqlite"

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

class Article(object):
    pass

class Comment(object):
    pass

mapper(Article, article_table)

mapper(Comment, comment_table)

classes = [Article, Comment]
Session.classes = dict(
    Article=Article,
    Comment=Comment)


def with_empty_db():
    Session.close_all()
    engine.dispose()
    metadata.drop_all()
    metadata.create_all()

metadata.create_all()
