# -*- coding: utf-8 -*-

import string
import random

from nose import with_setup

from beaker.middleware import SessionMiddleware
from paste.fixture import TestApp, TestResponse
from couchdb.client import Server

from root import CMS

server = Server('http://localhost:5984/')

try:
    db = server.create('picard_cms_test')
    print 'database created'
except:
    del server['picard_cms_test']
    db = server.create('picard_cms_test')

try:
    user_db = server.create('picard_users_test')
except:
    del server['picard_users_test']
    user_db = server.create('picard_users_test')


app = CMS(db=db, user_db=user_db)
app = SessionMiddleware(app, type="memory")
app = TestApp(app)

def random_string(length=5):
    return ''.join([random.choice(string.letters) for i in range(length)])

random_stub = random_string(20)
random_tags = ' '.join([random_string() for j in range(5)])

def create_pages():
    response = app.get('/create/')
    form = response.forms['create-form']
    form['title'] = "Homepage"
    form['body'] = "This is the homepage"
    response = form.submit()
    response = response.follow()
    assert response.request.url == "/", "The address is '/'"
    assert "This is the homepage" in response.normal_body,\
        "The body contains 'This is the homepage'"
    response = app.get('/create/')
    form = response.forms['create-form']
    form['stub'] = "test"
    form['title'] = "Test Page"
    form['body'] = "This is a test page"
    response = form.submit()
    response = response.follow()
    assert response.request.url == "/test", "The address is '/test'"
    assert "This is a test page" in response.normal_body,\
        "The body contains 'This is a test page'"

def delete_pages():
    response = app.get('/delete/test')
    form = response.forms['delete-form']
    response = form.submit()
    response = response.follow()
    assert response.request.url == "/", "The address is '/'"
    response = app.get('/test')
    assert "Page Not Found" in response.normal_body
    response = app.get('/delete/')
    form = response.forms['delete-form']
    response = form.submit()
    response = response.follow()
    assert response.request.url == "/", "The address is '/'"
    assert "Page Not Found" in response.normal_body
    
    

def test_create_pages():
    create_pages()

def test_delete_pages():
    delete_pages()