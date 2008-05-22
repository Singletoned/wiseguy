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
    if page.contents:
        content = page.contents[0]
        content.body = request.form['body']
    else:
        content = dict(body=request.form['body'])
        page.contents.append(content)
    try:
        page.tags = request.form['tags'].replace(',', ' ').split()
    except KeyError:
        pass
    page = page.save()
    url = request.script_root + '/' + page.address
    return redirect(url, 303)
    

@expose('/create/', ['GET', 'POST'], defaults={'address':''})
@expose('/create/<path:address>', ['GET', 'POST'])
@render('create')
def create(request, address):
    if request.method == 'GET':
        return dict(address=address)
    
    if request.method == 'POST':
        page = request.models.Page()
        page.address = address + request.form['stub']
        page.title = request.form['title']
        content = {}
        content['body'] = request.form['body']
        page.contents.append(content)
        try:
            page.tags = request.form['tags'].replace(',', ' ').split()
        except KeyError:
            pass
        page = page.save()
        url = request.script_root + '/' + page.address
        return redirect(url, 303)
    

@expose('/delete/', ['GET', 'POST'], defaults={'address':''})
@expose('/delete/<path:address>', ['GET', 'POST'])
@render('delete')
@with_page_from('address')
def delete(request, page):
    if request.method == 'GET':
        return dict(page=page)
    
    if request.method == 'POST':
        url = '/' + '/'.join(page.address.split('/')[:-1])
        request.models.Page.delete(page.id)
        return redirect(url, 303)
    

@render('not_found')
def not_found(request, response):
    return dict(request=request)


@expose('/comment/', ['POST'], defaults={'address':''})
@expose('/comment/<path:address>', ['POST'])
@render('comment')
@with_page_from('address')
def comment(request, page):
    form = request.form
    comment = page.save_comment(form['name'], form['email'], form['body'])
    if request.is_xhr:
        # Return a fragment
        return dict(comment=comment)
    else:
        # Clientside javascript mustn't be working.  Redirect back to the page
        return redirect('/%s' % page.address)


@expose('/rating/', ['POST'], defaults={'address':''})
@expose('/rating/<path:address>', ['POST'])
@render('rating')
@with_page_from('address')
def rating(request, page):
    if request.is_xhr:
        rating = page.save_rating(request.form['rating'])
        print rating
        # Return a fragment
        return dict(page=page)
    else:
        rating = page.save_rating(request.args['rating'])
        # Clientside javascript mustn't be working.  Redirect back to the page
        return redirect('/%s' % stub)






