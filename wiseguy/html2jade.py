# -*- coding: utf-8 -*-

import wiseguy.html


def render_el(el):
    parts = []
    parts.append(el.tag)
    if el.attrib.has_key('id'):
        parts.append("#"+el.attrib['id'].strip())
    if el.attrib.has_key('class'):
        for cls in el.attrib['class'].split():
            parts.append("."+cls.strip())
    if el.text and el.text.strip():
        parts.append(" "+el.text)
    yield "".join(parts)
    for sub_el in el:
        for line in render_el(sub_el):
            yield "  " + line

def html2jade(text):
    html = wiseguy.html.Html(text)
    lines = render_el(html)
    return "\n".join(lines)
