# -*- coding: utf-8 -*-

from datetime import datetime

from couchdb.client import Server, ResourceNotFound

from picard.schema import PicardDocument, TextField, IntegerField, \
DateTimeField, DictField, ListField, FloatField, Schema


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
        default=list
    )
    tags = ListField(TextField())
    comments = ListField(
        DictField(
            Schema.build(
                name=TextField(),
                email=TextField(),
                body=TextField(),
                date=DateTimeField(default=datetime.now)
            ),
        default=dict
        ),
        default=list
    )
    rating = DictField(
        Schema.build(
            score=FloatField(),
            votes=IntegerField(),
            total=IntegerField()
        ),
        default={
            'score':0,
            'votes':0,
            'total':0
        }
    )
    
    
    def save_comment(self, name, email, body):
        comment = dict(name=name, email=email, body=body)
        self.comments.append(comment)
        self.save()
        return self.comments[-1]
    
    def save_rating(self, rating):
        votes = self.rating['votes'] + 1
        total = self.rating['total'] + int(rating)
        score = float(total) / float(votes)
        self.rating = dict(
            votes=votes,
            total=total,
            score=score
        )
        self.save()
        return self.rating



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
        return cls(
            username=form['username'],
            email=form['email'],
            password=form['password']
        )


class Story(PicardDocument):
    class meta:
        content_type = "story"
    
    title = TextField(keyable=True)
    body = TextField()
    
    @classmethod
    def create_from_form(cls, **kwargs):
        item = cls()
        item.title = kwargs['title']
        item.body = kwargs['body']
        return item.save()

    def update_from_form(self, **kwargs):
        self.title = kwargs['title']
        self.body = kwargs['body']
        return self.save()



