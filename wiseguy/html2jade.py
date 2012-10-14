# -*- coding: utf-8 -*-

import wiseguy.html


def render_tag(el):
    yield el.tag
    if el.attrib.has_key('id'):
        yield "#" + el.attrib['id'].strip()
    if el.attrib.has_key('class'):
        for cls in el.attrib['class'].split():
            yield "." + cls.strip()
    if el.text and el.text.strip():
        yield " " + el.text

def render_el(el):
    yield "".join(render_tag(el))
    for sub_el in el:
        for line in render_el(sub_el):
            yield "  " + line

def html2jade(text):
    html = wiseguy.html.Html(text)
    lines = render_el(html)
    return "\n".join(lines)
