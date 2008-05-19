# -*- coding: utf-8 -*-

from datetime import datetime

from couchdb.client import Server, ResourceNotFound

from picard.schema import PicardDocument, TextField, IntegerField, DateTimeField, DictField, ListField, FloatField, Schema

class ContentsList(object):
    """A fake list for page content items"""
    def __init__(self, parent, keys):
        self._keys = keys
        self._parent = parent
    
    def __getitem__(self, i):
        key = self._keys[i]
        return Content.by_id(key)
    
    def __len__(self):
        return len(self._keys)
    
    def append(self, item):
        self._parent.content_keys.append(item.id)
        self._parent.save()
    
    def __repr__(self):
        return str([Content.by_id(key) for key in self._keys])


class Page(PicardDocument):
    class meta:
        content_type = "page"
    
    address = TextField(keyable=True)
    title = TextField(keyable=True)
    content_keys = ListField(
        TextField(),
        default=[]
    )
    
    @property
    def contents(self):
        return ContentsList(self, self.content_keys)


class Content(PicardDocument):
    class meta:
        content_type = "cms_content"
    
    title = TextField()
    body = TextField()


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


