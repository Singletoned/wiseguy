# -*- coding: utf-8 -*-

import jinja2 as j2
import lxml.html
from lxml.html import builder as html


@j2.contextfunction
def prev_li(context):
    prev_classes = ['prev']
    if not context['offset'] > 0:
        prev_classes.append('disabled')
    prev = html.LI(
        html.A(
            u"← Previous",
            href="#"
        ),
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
