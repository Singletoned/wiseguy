# -*- coding: utf-8 -*-

import jinja2 as j2
import lxml.html
from lxml.html import builder as html


def _make_href_kwargs(context, kwargs_filter, offset, limit):
    if kwargs_filter:
        href_kwargs = kwargs_filter(context, offset=offset, limit=limit)
    else:
        href_kwargs = dict(offset=offset, limit=limit)
    return href_kwargs

@j2.contextfunction
def prev_li(context, item_url, kwargs_filter=None):
    prev_classes = ['prev']
    attrs = dict()
    if not context['offset'] > 0:
        prev_classes.append('disabled')
    else:
        new_offset = max(0, context['offset']-context['limit'])
        href_kwargs = _make_href_kwargs(context, kwargs_filter, new_offset, context['limit'])
        attrs['href'] = item_url(**href_kwargs)
    prev = html.LI(
        html.A(
            u"← Previous",
            attrs),
        {'class': " ".join(prev_classes)},
    )
    return prev

@j2.contextfunction
def next_li(context, item_url, kwargs_filter=None):
    next_classes = ['next']
    attrs = dict()
    if not context['total'] > (context['offset'] + context['limit']):
        next_classes.append('disabled')
    else:
        new_offset = context['offset'] + context['limit']
        href_kwargs = _make_href_kwargs(context, kwargs_filter, new_offset, context['limit'])
        attrs['href'] = item_url(**href_kwargs)
    next = html.LI(
        html.A(
            u"Next →",
            attrs),
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
def pagination(context, item_url, kwargs_filter=None, class_=None):
    prev = prev_li(context, item_url, kwargs_filter)
    next = next_li(context, item_url, kwargs_filter)
    total = context['total']
    offset = context['offset']
    limit = context['limit']
    elements = []
    elements.append(prev)
    for page in page_counter(context):
        href_kwargs = _make_href_kwargs(context, kwargs_filter, page['offset'], page['limit'])
        href = item_url(**href_kwargs)
        if page['active']:
            li_class = {'class': (page['active'] and "active" or "")}
        else:
            li_class = {}
        el = html.LI(
            html.A(
                str(page['page']),
                href=href),
            li_class)
        elements.append(el)
    elements.append(next)
    classes = ['pagination']
    if class_:
        classes.append(class_)
    classes = " ".join(classes)
    div = html.DIV(
        {'class': classes},
        html.UL(
            *elements))
    return lxml.html.tostring(div, pretty_print=True)


def breadcrumbs(pages):
    items = []
    last_page_num = len(pages) - 1
    for page_num, page in enumerate(pages):
        if not page_num == last_page_num:
            el = html.LI(
                html.A(
                    page[1],
                    href=page[0]),
                " ",
                html.SPAN(
                    {'class': 'divider'},
                    "/"))
        else:
            el = html.LI(
                {'class': 'active'},
                html.A(
                    page[1],
                    href=page[0]))
        items.append(el)
    bc = html.UL(
        {'class': "breadcrumb"},
        *items)
    return lxml.html.tostring(bc, pretty_print=True)
