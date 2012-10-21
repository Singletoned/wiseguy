# -*- coding: utf-8 -*-

import lxml.html

import wiseguy.html


handled_attributes = set(['class', 'id'])

def make_attribute_pairs(el, attributes):
    for attr in attributes:
        yield u'%s="%s"' % (attr, el.attrib[attr])

def make_attributes(el):
    attributes = set(el.attrib) - handled_attributes
    if attributes:
        yield u"("
        yield u", ".join(make_attribute_pairs(el, attributes))
        yield u")"

def render_tag(el):
    yield el.tag
    if el.attrib.has_key('id'):
        if el.attrib['id']:
            yield u"#" + el.attrib['id'].strip()
    if el.attrib.has_key('class'):
        for cls in el.attrib['class'].split():
            yield u"." + cls.strip()
    for item in make_attributes(el):
        yield item
    if el.text and el.text.strip():
        yield u" " + el.text.strip()

def render_el(el):
    if isinstance(el, lxml.html.HtmlComment):
        for line in el.text.strip().split(u"\n"):
            yield u"// " + line.strip()
    else:
        yield u"".join(render_tag(el))
    for sub_el in el:
        for line in render_el(sub_el):
            yield u"  " + line
    if el.tail and el.tail.strip():
        yield u"  | %s" % el.tail.strip()

def html2jade(text):
    html = wiseguy.html.Html(text)
    lines = render_el(html)
    return u"\n".join(lines)
