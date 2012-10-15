# -*- coding: utf-8 -*-

import lxml.html

import wiseguy.html


handled_attributes = set(['class', 'id'])

def make_attribute_pairs(el, attributes):
    for attr in attributes:
        yield '%s="%s"' % (attr, el.attrib[attr])

def make_attributes(el):
    attributes = set(el.attrib) - handled_attributes
    if attributes:
        yield "("
        yield ", ".join(make_attribute_pairs(el, attributes))
        yield ")"

def render_tag(el):
    yield el.tag
    if el.attrib.has_key('id'):
        yield "#" + el.attrib['id'].strip()
    if el.attrib.has_key('class'):
        for cls in el.attrib['class'].split():
            yield "." + cls.strip()
    for item in make_attributes(el):
        yield item
    if el.text and el.text.strip():
        yield " " + el.text.strip()

def render_el(el):
    if isinstance(el, lxml.html.HtmlComment):
        for line in el.text.strip().split("\n"):
            yield "// " + line.strip()
    else:
        yield "".join(render_tag(el))
    for sub_el in el:
        for line in render_el(sub_el):
            yield "  " + line
    if el.tail and el.tail.strip():
        yield "  | %s" % el.tail.strip()

def html2jade(text):
    html = wiseguy.html.Html(text)
    lines = render_el(html)
    return "\n".join(lines)
