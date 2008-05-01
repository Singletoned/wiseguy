# -*- coding: utf-8 -*-
from couchdb.schema import Document, TextField, IntegerField, DateTimeField, ListField, DictField, Schema, Field
from pprint import pprint


class SchemaMeta(type):
    """For every attribute the class has, if it is a `Field`, assign it to `_fields` attribute

    >>> class MySchema(SchemaMeta):
    ...     __metaclass__ = SchemaMeta
    ...     foo = TextField()
    ...     bar = IntegerField()
    ... 
    >>> MySchema._fields
    {'foo': <couchdb.schema.TextField object at 0x654bd0>, 'bar': <couchdb.schema.IntegerField object at 0x654c10>}
    """
    def __new__(cls, name, bases, d):
        pprint(cls)
        pprint(name)
        pprint(bases)
        pprint(d)
        if d.has_key('meta'):
            pprint(d['meta'].__dict__)
        else:
            print "No meta available"
        fields = {}
        for base in bases:
            if hasattr(base, '_fields'):
                fields.update(base._fields)
        for attrname, attrval in d.items():
            if isinstance(attrval, Field):
                if not attrval.name:
                    attrval.name = attrname
                fields[attrname] = attrval
        d['_fields'] = fields
        # print "d: ", d
        # print d['meta']
        return type.__new__(cls, name, bases, d)


class Schema(object):
    __metaclass__ = SchemaMeta
    
    def __init__(self, **values):
        self._data = {}
        for attrname, field in self._fields.items():
            if attrname in values:
                setattr(self, attrname, values.pop(attrname))
            else:
                setattr(self, attrname, getattr(self, attrname))


class Doc(Schema):
    class meta:
        foo = "flibble"
    foo = TextField()
    bar = IntegerField()

doc = Doc(foo="hello")


