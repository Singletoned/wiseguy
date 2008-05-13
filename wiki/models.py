# -*- coding: utf-8 -*-

from datetime import datetime

from couchdb.client import Server, ResourceNotFound

from picard.schema import PicardDocument, TextField, IntegerField, DateTimeField, DictField, ListField, Schema

server = Server('http://localhost:5984/')

# try:
#    db = server.create('picard_wiki')
#    print 'database created'
# except:
#    db = server['picard_wiki']
# 
# try:
#     user_db = server.create('picard_users')
# except:
#     user_db = server['picard_users']

class WikiPage(PicardDocument):
    class meta:        
        # db = db
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
            name=TextField(),
            email=TextField(),
            body=TextField(),
            date=DateTimeField(default=datetime.now)
        ))
    )
    
    def save_comment(self, name, email, body):
        comment = dict(name=name, email=email, body=body)
        self.comments.append(comment)
        self.save(save_revision=False)
        return self.comments[-1]
    

class User(PicardDocument):
    class meta:
        # db=user_db
        id_default_column = "username"
        content_type = "user"
    
    username = TextField(keyable=True)
    email = TextField(keyable=True)
    password = TextField()

    @classmethod
    def create_from_form(cls, form):
        """Ignores extra fields"""
        return cls(username=form['username'], email=form['email'], password=form['password'])


class ModelStore(object):
    WikiPage = WikiPage
    User = User

    