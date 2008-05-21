# -*- coding: utf-8 -*-

from datetime import datetime

from couchdb.client import Server, ResourceNotFound

from picard.schema import PicardDocument, TextField, IntegerField, DateTimeField, DictField, ListField, FloatField, Schema


class Page(PicardDocument):
    class meta:
        content_type = "page"
    
    address = TextField(keyable=True)
    title = TextField(keyable=True)
    contents = ListField(
        DictField(Schema.build(
            title = TextField(),
            body = TextField()
        )),
        default=[]
    )
    


class User(PicardDocument):
    class meta:
        id_default_column = "username"
        content_type = "user"
    
    username = TextField(keyable=True)
    email = TextField(keyable=True)
    password = TextField()
    
    @classmethod
    def create_from_form(cls, form):
        """Ignores extra fields"""
        return cls(username=form['username'], email=form['email'], password=form['password'])


