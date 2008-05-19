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
    