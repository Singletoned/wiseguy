# -*- coding: utf-8 -*-

from pprint import pprint

import couchdb
from couchdb.client import Server, ResourceNotFound

from couchdb.schema import Document, TextField, IntegerField, DateTimeField, ListField, DictField, Schema, Field, SchemaMeta

class Query(object):
    """A callable holder for a few attributes of a query"""
    def __init__(self, name, code, wrapper, db=None):
        self.name = name
        self.code = code
        self.wrapper = wrapper
        self.db = db
    
    def __call__(self, key, db=None):
        "Returns the first item from the query"
        db = db or self.db
        return list(db.query(self.code, wrapper=self.wrapper)[key])[0]


class SchemaMetaData(object):
    """A placeholder for bits of data about the schema"""
    def __init__(self, metadata):
        self.db = getattr(metadata, 'db', None)
        self.id_default_column = getattr(metadata, 'id_default_column', None)
        self.content_type = getattr(metadata, 'content_type', None)


class PicardDocumentMeta(SchemaMeta):

    def __new__(cls, name, bases, d):
        pprint('cls')
        pprint(cls)
        pprint('name')
        pprint(name)
        pprint('bases')
        pprint(bases)
        pprint('d')
        pprint(d)
        
        if d.has_key('meta'):
            pprint(d['meta'].__dict__)
        else:
            pprint("No meta available")
        
        meta = SchemaMetaData(d.get('meta', None))
        
        pd_class = SchemaMeta.__new__(cls, name, bases, d)
        pd_class.meta = meta
        queries = {}
        for attrname, field in pd_class._fields.items():
            if getattr(field, 'keyable', False):
                code = """
                function(doc) {
                  if (doc.content_type == "%s") {
                    map(doc.%s, doc);
                  }
                }
                """ % (pd_class.meta.content_type, attrname)
                query_name = "get_by_%s" % attrname
                query = Query(query_name, code, pd_class.init_from_row, db=meta.db)
                queries[query_name] = query
                setattr(pd_class, query_name, query)
        setattr(pd_class, '_queries', queries)
        return pd_class
    


class PicardDocument(Document):
    """A version of Couchdb document with some utility methods"""
    
    __metaclass__ = PicardDocumentMeta
        
    def __init__(self, *args, **kwargs):
        super(PicardDocument, self).__init__(**kwargs)
        self._data['content_type'] = self.meta.content_type
        for query_name, query in self._queries.items():
            query.db = self.meta.db
    
    @classmethod
    def by_id(cls, id):
        item = cls.load(id)
        if item is None:
            raise ResourceNotFound()
        return item
    
    def save(self):
        """Checks to see if `meta` defines a default column to use for an id"""
        if getattr(self._data, 'id', None) is None:
            if self._data.get('_id', None) is None:
                self._data['_id'] = getattr(self, self.meta.id_default_column)
        
        item = self.store(self.meta.db)
        return item
    
    @classmethod
    def load(cls, id, db=None):
        """Load a specific document from the given database."""
        db = db or cls.meta.db
        item = db.get(id)
        if item is None:
            raise ResourceNotFound()
        return cls.wrap(item)

    def store(self, db=None):
        """Store the document in the given database."""
        db = db or cls.meta.db
        if getattr(self._data, 'id', None) is None:
            if self._data.get('_id', None) is not None:
                db[self._data['_id']] = self._data
            else:
                docid = db.create(self._data)
                self._data = db.get(docid)
        else:
            db[self._data.id] = self._data
        return self
    
    @classmethod
    def delete(cls, id, db=None):
        db = db or cls.meta.db
        del db[id]
    
    @classmethod
    def init_from_row(cls, row):
        """initialises an item from a view result row"""
        return cls.wrap(row.value)

