# -*- coding: utf-8 -*-

import wiseguy.html


def render_el(el):
    yield el.tag

def html2jade(text):
    html = wiseguy.html.Html(text)
    lines = render_el(html)
    return "\n".join(lines)
