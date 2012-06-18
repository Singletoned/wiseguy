# -*- coding: utf-8 -*-

import pyjade.ext.html

import lxml.html

inline_tags = set([
    "a",
    "abbr",
    "address",
    "br",
    "cite",
    "code",
    "del",
    "details",
    "command",
    "em",
    "i",
    "img",
    "ins",
    "strong"])

class HtmlElement(lxml.html.HtmlElement):
    def to_string(self, pretty=True):
        return lxml.html.tostring(self, pretty_print=pretty)

    def insert(self, path, text_or_el):
        elements = self.cssselect(path)
        if isinstance(text_or_el, (str, unicode)):
            for el in elements:
                el.text = text_or_el
        else:
            for el in elements:
                el.append(text_or_el)

class HtmlElementLookup(lxml.html.HtmlElementClassLookup):
    def lookup(self, node_type, document, namespace, name):
        return HtmlElement

parser = lxml.html.HTMLParser()
parser.set_element_class_lookup(HtmlElementLookup())

def Html(src):
    return lxml.html.fromstring(src, parser=parser)

class HTMLCompiler(pyjade.compiler.Compiler):
    def attributes(self, attrs):
        return " ".join(['''%s="%s"''' % (k,v) for (k,v) in attrs.items()])

    def visitAttributes(self, attrs):
        classes = []
        params = dict()
        for attr in attrs:
            if attr['name'] == 'class':
                classes.append(attr['val'].strip("'"))
            else:
                params[attr['name']] = attr['val'].strip("'")
        if classes:
            params['class'] = " ".join(classes)
        self.buf.append("".join([''' %s="%s"''' % (k,v) for (k,v) in params.items()]))


def jade(src):
    text = process_jade(src)
    el = lxml.html.fromstring(text, parser=parser)
    return el

def process_jade(src):
    parser = pyjade.parser.Parser(src)
    block = parser.parse()
    compiler = pyjade.ext.html.HTMLCompiler(block, pretty=False)
    return compiler.compile()

def _render_open_tag(el):
    return "<%s%s>" % (el.tag, _render_attrs(el))

def _render_close_tag(el):
    return "</%s>" % (el.tag)

def _render_attrs(el):
    return "".join([' %s="%s"'%(k, el.attrib[k]) for k in sorted(el.keys())])

def _render_tag_contents(el):
    if el.text:
        yield el.text
    for sub_element in el:
        for line in _render_el(sub_element):
            yield line
    if el.tail:
        yield el.tail

def _render_el(el):
    yield _render_open_tag(el)
    for line in _render_tag_contents(el):
        yield line
    if not el.tag in lxml.html.defs.empty_tags:
        yield _render_close_tag(el)

def _inline_content(el):
    for sub_element in el:
        if not sub_element.tag in inline_tags:
            return False
    else:
        return True

def _render_el_tidy(el):
    if not _inline_content(el):
        for line in _render_el(el):
            yield line
    else:
        yield _render_open_tag(el)
        yield "  "+"".join(_render_tag_contents(el)).strip()
        if not el.tag in lxml.html.defs.empty_tags:
            yield _render_close_tag(el)

def normalise_html(el):
    return "\n".join([item.strip() for item in _render_el(el) if item.strip()])

def tidy_html(el):
    return "\n".join(_render_el_tidy(el))
