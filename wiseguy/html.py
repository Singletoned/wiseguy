# -*- coding: utf-8 -*-

import re

import pyjade.ext.html
import lxml.html


whitespace_re = re.compile("\s+")

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
    "label",
    "strong",
    "title",
    "legend"
])

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

def _render_content(el):
    if el.text:
        yield el.text
    for sub_element in el:
        for line in _render_el_tidy(sub_element):
            yield line

def _render_el(el, indent_level=1):
    yield _render_open_tag(el)
    if el.text:
        yield el.text
    for sub_element in el:
        for line in _render_el(sub_element, indent_level=indent_level+1):
            yield line
    if not el.tag in lxml.html.defs.empty_tags:
        yield _render_close_tag(el)
    if el.tail:
        yield el.tail

def has_inline_content(el):
    for sub_element in el:
        if not sub_element.tag in inline_tags:
            return False
    else:
        return True

def is_empty(el):
    if (not el.text) and (not el.getchildren()):
        return True
    else:
        return False

def _render_inline_tag(el):
    lines = _render_el(el)
    lines = [line.replace('\n', '') for line in lines]
    yield whitespace_re.sub(' ', "".join(lines))

def _render_block_tag(el, indent_level=0):
    indent = "  " * (indent_level+1)
    if is_empty(el):
        if not el.tag in lxml.html.defs.empty_tags:
            yield _render_open_tag(el) + _render_close_tag(el)
        else:
            yield _render_open_tag(el)
    else:
        yield _render_open_tag(el)
        if has_inline_content(el):
            yield indent+"".join(_render_content(el)).strip()
        else:
            for line in _render_content(el):
                yield indent + line
        if not el.tag in lxml.html.defs.empty_tags:
            yield _render_close_tag(el)

def _render_el_tidy(el, indent_level=1):
    if el.tag in inline_tags:
        yield _render_inline_tag(el).next()
    else:
        for line in _render_block_tag(el):
            if line.strip():
                yield line

def normalise_html(el):
    return "\n".join([item.strip() for item in _render_el(el) if item.strip()])

def tidy_html(el):
    return "\n".join(_render_el_tidy(el))
