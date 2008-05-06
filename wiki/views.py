# -*- coding: utf-8 -*-

import logging

from werkzeug import Response

from werkzeug.exceptions import NotFound

from werkzeug.utils import redirect

from utils import expose

from utils import render

from models import ResourceNotFound, WikiPage

@expose('/', defaults={'stub':'homepage'})
@expose('/<string:stub>')
@render('view')
def view(request, stub):
    try:
        page = WikiPage.by_id(stub)
    except ResourceNotFound:
        raise NotFound
    return dict(page=page)

@expose('/edit/', defaults={'stub':'homepage'})
@expose('/edit/<string:stub>')
@render('edit')
def edit(request, stub):
    # See if the page exists...
    try:
        page = WikiPage.by_id(stub)
    # If not, create a temporary page that doesn't get saved
    except ResourceNotFound:
        page = WikiPage(stub=stub)
    return dict(page=page)

@expose('/save/<string:stub>', ['POST'])
def save(request, stub=None):
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
    page = WikiPage(
        stub = request.path.strip('/').split('/', 1)[0],
        body = None
    )
    return dict(page=page)

@expose('/delete/<string:stub>', ['POST'])
def delete(request, stub=None):
    WikiPage.delete(stub)
    url = request.script_root + '/'
    return redirect(url)

@expose('/list/')
@render('list')
def list(request):
    """Lists all the pages, as links"""
    pages = WikiPage.get_all()
    return dict(pages=pages)


