# -*- coding: utf-8 -*-

import wiseguy.html


def render_el(el):
    if el.text:
        yield " ".join([el.tag, el.text])
    else:
        yield el.tag

def html2jade(text):
    html = wiseguy.html.Html(text)
    lines = render_el(html)
    return "\n".join(lines)
