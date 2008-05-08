# -*- coding: utf-8 -*-

import logging

from werkzeug import Response

from werkzeug.exceptions import NotFound

from werkzeug.utils import redirect

from utils import expose, render

from models import ResourceNotFound

@expose('/', defaults={'stub':'homepage'})
@expose('/<string:stub>')
@render('view')
def view(request, stub):
    WikiPage = request.models.WikiPage
    if request.session.get('logged_in', False):
        user = User.get_by_username(request.session['username'])
    else:
        user = None
        
    try:
        page = WikiPage.by_id(stub)
    except ResourceNotFound:
        raise NotFound
    return dict(page=page, user=user)

@expose('/edit/', defaults={'stub':'homepage'})
@expose('/edit/<string:stub>')
@render('edit')
def edit(request, stub):
    WikiPage = request.models.WikiPage
    # See if the page exists...
    try:
        page = WikiPage.by_id(stub)
    # If not, create a temporary page that doesn't get saved
    except ResourceNotFound:
        page = WikiPage(stub=stub)
    return dict(page=page)

@expose('/save/<string:stub>', ['POST'])
def save(request, stub=None):
    WikiPage = request.models.WikiPage
    stub = stub or request.form['stub']
    try:
        page = WikiPage.by_id(stub)
    except ResourceNotFound:
        page = WikiPage()
        page.stub = stub
    
    page.body = request.form['body']
    try:
        page.tags = request.form['tags'].replace(',', ' ').split()
    except KeyError:
        pass
    page = page.save()
    url = request.script_root + '/' + stub
    return redirect(url, 303)
        
@render('not_found')
def not_found(request, response):
    "Displays an edit form and offers to let them create the page"
    WikiPage = request.models.WikiPage
    page = WikiPage(
        stub = request.path.strip('/').split('/', 1)[0],
        body = None
    )
    return dict(page=page)

@expose('/delete/<string:stub>', ['POST'])
def delete(request, stub=None):
    WikiPage = request.models.WikiPage
    WikiPage.delete(stub)
    url = request.script_root + '/'
    return redirect(url)

@expose('/list/')
@render('list')
def list(request):
    """Lists all the pages, as links"""
    WikiPage = request.models.WikiPage
    pages = WikiPage.get_all()
    return dict(pages=pages)

@expose('/register', ['GET', 'POST'])
@render('register')
def register(request):
    User = request.models.User
    if request.method == 'GET':
        return dict()
    else:
        form = request.form
        errors = {}
        for key in ['username', 'email', 'password']:
            if not form[key]:
                errors[key] = "Please enter the %s" % key
        if not errors:
            if len(User.get_by_username(form['username'])):
                errors['username'] = "That username is already taken"
            if len(User.get_by_email(form['email'])):
                errors['email'] = "That email address is already taken"
        if errors:
            return dict(form_data=form, errors=errors)
        else:
            user = User.create_from_form(form)
            user.save()
            session = request.session
            session['username'] = user.username
            session['logged_in'] = True
            session.save()
            return redirect('/')
    

@expose('/login', ['GET', 'POST'])
@render('login')
def login(request):
    User = request.models.User
    if request.method == 'GET':
        return dict()
    else:
        form = request.form
        errors = {}
        user = User.get_by_username(form['username'])
        if not user:
            errors['username'] = """That username is not in use.  Have you misplet it or would you like to <a href="/register">register</a>?"""
            errors['password'] = """That password would be incorrect if the user existed (which it doesn't)."""
        else:
            if not form['password'] == user.password:
                errors['password'] == """That password is incorrect.  Do you need a <a href="/reminder">reminder</a>?"""
            else:
                session = request.session
                session['username'] = user.username
                session['logged_in'] = True
                session.save()
                return redirect(form.get('from_page', False) or '/')
        return dict(form_data=form, errors=errors)


