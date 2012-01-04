# -*- coding: utf-8 -*-

import jinja2 as j2
import lxml.html
from lxml.html import builder as html


@j2.contextfunction
def prev_li(context):
    prev_classes = ['prev']
    attrs = dict()
    if not context['offset'] > 0:
        prev_classes.append('disabled')
    else:
        attrs['href'] = "/"
    prev = html.LI(
        html.A(
            u"← Previous",
            attrs),
        {'class': " ".join(prev_classes)},
    )
    return prev

@j2.contextfunction
def next_li(context):
    next_classes = ['next']
    if not context['total'] > (context['offset'] + context['limit']):
        next_classes.append('disabled')
    next = html.LI(
        html.A(
            u"Next →",
            href="#"
        ),
        {'class': " ".join(next_classes)},
    )
    return next

def page_counter(context):
    total = context['total']
    offset = context['offset']
    limit = context['limit']
    current = 0
    page = 0
    while current < total:
        page = page + 1
        start = current + 1
        end = current + limit
        if current <= offset < end:
            active = True
        else:
            active = False
        yield dict(
            page=page,
            offset=current,
            limit=limit,
            start=start,
            end=end,
            active=active)
        current = current + limit


@j2.contextfunction
def pagination(context):
    prev = prev_li(context)
    next = next_li(context)
    total = context['total']
    offset = context['offset']
    limit = context['limit']
    elements = []
    elements.append(prev)
    for page in page_counter(context):
        if page['active']:
            li_class = {'class': (page['active'] and "active" or "")}
        else:
            li_class = {}
        el = html.LI(
            html.A(
                str(page['page']),
                href="#"),
            li_class)
        elements.append(el)
    elements.append(next)
    div = html.DIV(
        {'class': 'pagination'},
        html.UL(
            *elements))
    return lxml.html.tostring(div, pretty_print=True)
