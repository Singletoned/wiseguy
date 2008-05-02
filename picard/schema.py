# -*- coding: utf-8 -*-

from pprint import pprint
from datetime import datetime
from calendar import timegm

import couchdb
from couchdb.client import Server, ResourceNotFound

from couchdb.schema import Document, TextField, IntegerField, DateTimeField, ListField, DictField, Schema, Field, SchemaMeta

from utils import simple_decorator

@simple_decorator
def revisioned_save(save_func):
    """Adds the current data (except revisions) into revisions before saving"""
    def revisioned_func(*args, **kwargs):
        self = args[0]
        revisions = self._data.setdefault('revisions', [])
        data = {'date_revised':datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'}
        data.update(self._data)
        del data['revisions']
        revisions.append(data)
        return save_func(*args, **kwargs)
    return revisioned_func

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
        self.revisioned = getattr(metadata, 'revisioned', False)


class PicardDocumentMeta(SchemaMeta):
    def __new__(cls, name, bases, d):
        meta = SchemaMetaData(d.get('meta', None))
        if meta.revisioned:
            date_revised = DateTimeField(default=datetime.now)
            d['date_revised'] = date_revised
            def revisions(self):
                revisions = self._data.setdefault('revisions', [])
                return [self.wrap(rev) for rev in revisions]
            d['revisions'] = property(revisions)
            d['save'] = revisioned_save(bases[0].save)
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
    
    def save(self, db=None):
        """Save the document to the given or default database.  Use `id_default_column` if set"""
        db = db or self.meta.db
        id = self.id or getattr(self, self.meta.id_default_column) or None
        if id:
            db[id] = self._data
        else:
            docid = db.create(self._data)
            self._data = db[docid]
        return self
    
    @classmethod
    def load(cls, id, db=None):
        """Load a specific document from the given database."""
        db = db or cls.meta.db
        item = db.get(id)
        if item is None:
            raise ResourceNotFound()
        return cls.wrap(item)
    
    @classmethod
    def delete(cls, id, db=None):
        db = db or cls.meta.db
        del db[id]
    
    @classmethod
    def init_from_row(cls, row):
        """initialises an item from a view result row"""
        return cls.wrap(row.value)

    @classmethod
    def get_all(cls, db=None):
        db = db or cls.meta.db
        """Fetches all documents that match the classes content_type"""
        code = """
        function(doc) {
          if (doc.doc_type == "%s") {
            map(null, doc);
          }
        }
        """ % cls.meta.content_type
        return db.query(code, wrapper=cls.init_from_row)
    
    