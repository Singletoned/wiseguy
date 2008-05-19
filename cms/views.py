# -*- coding: utf-8 -*-

import logging

from werkzeug import Response
from werkzeug.exceptions import NotFound
from werkzeug.utils import redirect
from werkzeug.routing import Map

from picard.utils import create_expose, render, with_page_from

from models import ResourceNotFound

url_map = Map()

expose = create_expose(url_map)


@expose('/', defaults={'address':''})
@expose('/<path:address>')
@render('view')
@with_page_from('address')
def view(request, page):
    return dict(
        page=page
    )

@expose('/edit/', defaults={'address':''})
@expose('/edit/<path:address>')
@render('edit')
@with_page_from('address')
def edit(request, page):
    return dict(
        page=page
    )

@expose('/save/', ['POST'], defaults={'address':''})
@expose('/save/<path:address>', ['POST'])
@render('save')
@with_page_from('address')
def save(request, page):
    page.title = request.form['title']
    print page.contents
    if page.contents:
        content = page.contents[0]
        content.body = request.form['body']
        content.save()
    else:
        content = request.models.Content(body=request.form['body'])
        content.save()
        page.contents.append(content)
    # try:
    #     page.tags = request.form['tags'].replace(',', ' ').split()
    # except KeyError:
    #     pass
    page = page.save()
    print page
    url = request.script_root + '/' + page.address
    return redirect(url, 303)
    
