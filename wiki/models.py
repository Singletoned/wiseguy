# -*- coding: utf-8 -*-

from datetime import datetime

from couchdb.client import Server, ResourceNotFound

from picard.schema import PicardDocument, TextField, IntegerField, DateTimeField, DictField, ListField, Schema

server = Server('http://localhost:5984/')

try:
   db = server.create('picard_wiki')
   print 'database created'
except:
   db = server['picard_wiki']


class WikiPage(PicardDocument):
    class meta:        
        db = db
        id_default_column = "stub"
        content_type = "wiki_page"
        revisioned = True
    
    address = TextField()
    stub = TextField(keyable=True)
    body = TextField()
    date_created = DateTimeField(default=datetime.now)
    date_modified = DateTimeField(default=datetime.now)
    tags = ListField(TextField())
    comments = ListField(
        DictField(Schema.build(
            author_name=TextField(),
            author_email=TextField(),
            body=TextField(),
            date=DateTimeField(default=datetime.now)
        ))
    )
    
